"""
Deploywise AI — Unified Project Assessment Orchestration Service.
End-to-end pipeline: Ingest -> Discover -> Scan -> Topology Graph -> Rules -> Scoring -> AI Advisory -> Report.
"""
from __future__ import annotations

import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.graph import WorkflowGraph
from app.core.policy import get_default_policy
from app.core.schemas import (
    AssessmentCoverage,
    AssessmentInputType,
    Category,
    CategoryScore,
    Finding,
    FindingSource,
    ProjectAssessmentResponse,
    ProjectStructure,
    RemediationItem,
    ScannerResult,
    ScannerStatus,
    Severity,
    Verdict,
    WorkflowInput,
)
from app.core.scoring import compute_score, run_all_rules
from app.db.models import AnalysisModel, AuditEventModel, FindingModel, WorkflowModel, WorkflowVersionModel
from app.ingestion.cicd_parser import parse_cicd_content
from app.ingestion.diagram_parser import DiagramWorkflowParser
from app.ingestion.git_repo import GitRepoIngestor
from app.ingestion.project_discovery import ProjectDiscoveryEngine
from app.ingestion.zip_archive import SafeZipExtractor
from app.scanners.orchestrator import ScannerOrchestrator
from app.services.ai_summary import generate_ai_summary
from app.services.diagram_generator import WorkflowDiagramGenerator
from app.services.encouragement import DeveloperEncouragementService


class ProjectAssessmentService:
    """Orchestrates comprehensive multi-source project workflow and code assurance assessments."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.discovery_engine = ProjectDiscoveryEngine()
        self.scanner_orchestrator = ScannerOrchestrator()
        self.diagram_parser = DiagramWorkflowParser()
        self.policy = get_default_policy()

    async def assess_github_repo(self, repo_url: str, branch: str | None = None) -> ProjectAssessmentResponse:
        """Clones, discovers, scans, and assesses a public or authorized Git repository."""
        ingestor = GitRepoIngestor()
        local_path, commit_sha, resolved_branch = ingestor.clone_and_pin(repo_url, branch_or_tag=branch)
        try:
            return await self._assess_workspace(
                workspace_path=local_path,
                project_name=Path(repo_url.rstrip("/")).stem,
                input_type=AssessmentInputType.GITHUB,
                input_source=repo_url,
                commit_sha=commit_sha,
                branch=resolved_branch,
            )
        finally:
            ingestor.cleanup(local_path)

    async def assess_zip_archive(self, zip_bytes: bytes, filename: str) -> ProjectAssessmentResponse:
        """Safely extracts, discovers, scans, and assesses a ZIP source archive."""
        extractor = SafeZipExtractor()
        local_path = extractor.extract(zip_bytes)
        try:
            return await self._assess_workspace(
                workspace_path=local_path,
                project_name=Path(filename).stem,
                input_type=AssessmentInputType.ZIP,
                input_source=filename,
            )
        finally:
            extractor.cleanup(local_path)

    async def assess_cicd_content(self, content: str, filename_hint: str = "workflow.yml") -> ProjectAssessmentResponse:
        """Directly parses and assesses a raw CI/CD workflow YAML or JSON file."""
        wf_input = parse_cicd_content(content, filename_hint=filename_hint)
        # Create lightweight temporary directory for scanning
        with tempfile.TemporaryDirectory(prefix="deploywise_cicd_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            target_file = tmp_path / filename_hint
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content, encoding="utf-8")

            return await self._assess_workspace(
                workspace_path=tmp_path,
                project_name=wf_input.name,
                input_type=AssessmentInputType.CICD,
                input_source=filename_hint,
                override_workflow=wf_input,
            )

    async def assess_diagram(self, file_bytes: bytes, filename: str) -> ProjectAssessmentResponse:
        """Infers workflow from diagram image, SVG, or PDF report and runs full assessment."""
        (
            wf_input,
            observed_facts,
            inferred_relationships,
            unknown_details,
            evidence_boundaries,
        ) = self.diagram_parser.parse_image_or_document(file_bytes, filename=filename)

        with tempfile.TemporaryDirectory(prefix="deploywise_diag_") as tmp_dir:
            return await self._assess_workspace(
                workspace_path=Path(tmp_dir),
                project_name=wf_input.name,
                input_type=AssessmentInputType.DIAGRAM,
                input_source=filename,
                override_workflow=wf_input,
                observed_facts=observed_facts,
                inferred_relationships=inferred_relationships,
                unknown_details=unknown_details,
                evidence_boundaries=evidence_boundaries,
            )

    async def _assess_workspace(
        self,
        workspace_path: Path,
        project_name: str,
        input_type: AssessmentInputType,
        input_source: str,
        commit_sha: str | None = None,
        branch: str | None = None,
        override_workflow: WorkflowInput | None = None,
        extra_notes: list[str] | None = None,
        observed_facts: list[str] | None = None,
        inferred_relationships: list[str] | None = None,
        unknown_details: list[str] | None = None,
        evidence_boundaries: list[str] | None = None,
    ) -> ProjectAssessmentResponse:
        """Core unified assessment pipeline."""
        now = datetime.now(timezone.utc)
        assessment_id = str(uuid.uuid4())

        # 1. Project Structure Discovery
        if override_workflow is not None:
            structure = ProjectStructure(
                languages=["CI/CD Configuration"],
                frameworks=[],
                package_managers=[],
                ci_workflows=[input_source],
                dockerfiles=[],
                total_files=1,
                commit_sha=commit_sha,
                branch=branch,
            )
            wf_input = override_workflow
        else:
            structure, detected_wf = self.discovery_engine.inspect_workspace(
                workspace_path, commit_sha=commit_sha, branch=branch
            )
            wf_input = detected_wf or self.discovery_engine._generate_baseline_workflow(structure, project_name)

        # 2. Run Scanner Orchestrator (native secrets, deps, Docker + external tools)
        scanner_findings, scanner_results, coverage = self.scanner_orchestrator.run_all_scans(workspace_path)

        # Generate IDs
        workflow_id = str(uuid.uuid4())
        workflow_version_id = str(uuid.uuid4())

        # 3. Build Graph & Evaluate Deterministic Workflow Rules (R01 - R10)
        graph = WorkflowGraph(wf_input)
        rule_findings = run_all_rules(graph, self.policy)

        # Combine verified findings
        all_findings: list[Finding] = rule_findings + scanner_findings

        # 4. Compute Weighted Score & Policy Verdict
        scoring_result = compute_score(
            findings=all_findings,
            workflow_id=workflow_id,
            workflow_version_id=workflow_version_id,
            policy=self.policy,
        )
        risk_score = scoring_result.score
        verdict = scoring_result.verdict
        is_blocked = scoring_result.is_blocked
        category_scores = scoring_result.category_scores

        # Coverage impact on verdict: if coverage is very low (< 30%), flag as INSUFFICIENT_EVIDENCE
        if coverage.coverage_percentage < 30.0 and verdict == Verdict.PASS:
            verdict = Verdict.INSUFFICIENT_EVIDENCE

        # 5. Build Prioritized Remediation Roadmap
        roadmap: list[RemediationItem] = []
        for f in all_findings:
            if f.blocking:
                p = 1
                plabel = "Priority 1 (Mandatory Blocker)"
                effort = "Immediate fix required; blocks production promotion."
            elif f.severity in (Severity.CRITICAL, Severity.HIGH):
                p = 2
                plabel = "Priority 2 (High Risk)"
                effort = "Resolve in current release cycle to prevent security or stability failure."
            elif f.severity == Severity.MEDIUM:
                p = 3
                plabel = "Priority 3 (Operational Improvement)"
                effort = "Schedule for next operational maintenance sprint."
            else:
                p = 4
                plabel = "Priority 4 (Maintainability)"
                effort = "Low effort hygiene improvement."

            roadmap.append(
                RemediationItem(
                    priority=p,
                    priority_label=plabel,
                    finding_id=f.finding_id,
                    title=f.title,
                    severity=f.severity,
                    category=f.category,
                    location=f.file_path or (f.stage_ids[0] if f.stage_ids else "Pipeline DAG"),
                    recommended_fix=f.recommended_fix,
                    suggested_patch=f.suggested_patch,
                    verification_criteria=f.verification_criteria,
                    effort_rationale=effort,
                )
            )

        roadmap.sort(key=lambda item: item.priority)

        # 5b. Generate AI Advisory Summary (never blocks or alters deterministic results)
        ai_summary = await generate_ai_summary(
            project_name=project_name,
            structure=structure,
            findings=all_findings,
            scanner_results=scanner_results,
            remediation_roadmap=roadmap,
            verdict=verdict,
            risk_score=risk_score,
            coverage_pct=coverage.coverage_percentage,
            commit_sha=commit_sha,
        )

        # 5c. Workflow Visual Intelligence: Generate Existing and Recommended Corrected Diagrams
        existing_diagram, recommended_diagram, diagram_comparison = WorkflowDiagramGenerator.generate_both(
            workflow=wf_input,
            findings=all_findings,
            is_diagram_inferred=(input_type == AssessmentInputType.DIAGRAM),
        )

        # 5d. Developer Motivation & Guidance
        blocking_count = sum(1 for f in all_findings if f.blocking)
        developer_encouragement = DeveloperEncouragementService.generate(
            verdict=verdict,
            is_blocked=is_blocked,
            blocking_count=blocking_count,
            findings_count=len(all_findings),
            coverage_pct=coverage.coverage_percentage,
            is_diagram_only=(input_type == AssessmentInputType.DIAGRAM),
        )

        # Compile evidence boundaries if not provided
        if not evidence_boundaries:
            evidence_boundaries = [
                "Inspection Scope: Verified files and pipelines parsed within input workspace.",
                "Static Verification: Deterministic safety rules and scanners run on detected manifests.",
                "Runtime Verification: Actual environment secrets and live probe results require production telemetry.",
            ]

        # 6. Persist to Database for Historical Traceability
        workflow_model = WorkflowModel(
            id=workflow_id,
            name=wf_input.name,
            environment=wf_input.environment.value,
            change_type=wf_input.change_type.value,
            created_at=now,
            updated_at=now,
        )
        self.db.add(workflow_model)

        version_model = WorkflowVersionModel(
            id=workflow_version_id,
            workflow_id=workflow_id,
            version_number=1,
            payload=wf_input.model_dump(),
            schema_version="1.0",
            created_at=now,
        )
        self.db.add(version_model)

        analysis_model = AnalysisModel(
            id=assessment_id,
            workflow_id=workflow_id,
            workflow_version_id=workflow_version_id,
            policy_version=self.policy.policy_version,
            rule_set_version=self.policy.rule_set_version,
            score=risk_score,
            verdict=verdict.value,
            is_blocked=is_blocked,
            category_scores=[cs.model_dump() for cs in category_scores],
            status="complete",
            created_at=now,
            completed_at=now,
        )
        self.db.add(analysis_model)

        for f in all_findings:
            f_model = FindingModel(
                id=str(uuid.uuid4()),
                analysis_id=assessment_id,
                finding_id=f.finding_id,
                source=f.source.value,
                rule_id=f.rule_id,
                rule_version=f.rule_version,
                category=f.category.value,
                severity=f.severity.value,
                blocking=f.blocking,
                advisory=f.advisory,
                stage_ids=f.stage_ids,
                title=f.title,
                evidence=f.evidence,
                why_it_matters=f.why_it_matters,
                recommended_fix=f.recommended_fix,
                verification_criteria=f.verification_criteria,
                confidence=f.confidence,
            )
            self.db.add(f_model)

        # Audit Event
        audit_event = AuditEventModel(
            id=str(uuid.uuid4()),
            timestamp=now,
            actor="system",
            action="project_assessment_completed",
            entity_type="assessment",
            entity_id=assessment_id,
            details={
                "project_name": project_name,
                "input_type": input_type.value,
                "input_source": input_source,
                "risk_score": risk_score,
                "verdict": verdict.value,
                "is_blocked": is_blocked,
                "findings_count": len(all_findings),
                "ai_summary_available": ai_summary is not None,
                "diagram_generated": existing_diagram is not None,
            },
        )
        self.db.add(audit_event)

        await self.db.commit()

        # Build response
        return ProjectAssessmentResponse(
            assessment_id=assessment_id,
            project_name=project_name,
            input_type=input_type,
            input_source=input_source,
            created_at=now,
            commit_sha=commit_sha,
            workflow_id=workflow_id,
            risk_score=risk_score,
            assurance_score=max(0.0, 100.0 - risk_score),
            coverage=coverage,
            verdict=verdict,
            is_blocked=is_blocked,
            structure=structure,
            scanner_results=scanner_results,
            findings=all_findings,
            category_scores=category_scores,
            remediation_roadmap=roadmap,
            ai_summary=ai_summary,
            existing_workflow_diagram=existing_diagram,
            recommended_workflow_diagram=recommended_diagram,
            diagram_comparison=diagram_comparison,
            observed_facts=observed_facts or [f"Workflow '{wf_input.name}' analyzed with {len(wf_input.stages)} stages."],
            inferred_relationships=inferred_relationships or [],
            unknown_details=unknown_details or [],
            evidence_boundaries=evidence_boundaries,
            developer_encouragement=developer_encouragement,
        )
