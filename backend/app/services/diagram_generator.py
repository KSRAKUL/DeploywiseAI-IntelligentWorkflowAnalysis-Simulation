"""
Deploywise AI — Corrected Workflow Diagram Generator.
Generates structured graph models and renderable Mermaid code for both
the Existing Reconstructed Workflow and the Recommended Improved Architecture.
"""
from __future__ import annotations

import re
from typing import Sequence

from app.core.schemas import (
    DiagramDiffItem,
    DiagramEdge,
    DiagramNode,
    Finding,
    Stage,
    StageType,
    WorkflowDiagramModel,
    WorkflowInput,
)


class WorkflowDiagramGenerator:
    """Generates visual and structured graphs for delivery workflows and architecture corrections."""

    @classmethod
    def generate_both(
        cls,
        workflow: WorkflowInput,
        findings: Sequence[Finding],
        is_diagram_inferred: bool = False,
    ) -> tuple[WorkflowDiagramModel, WorkflowDiagramModel, list[DiagramDiffItem]]:
        """
        Generate (existing_diagram, recommended_diagram, comparison_diff).
        """
        existing = cls.generate_existing_diagram(workflow, findings, is_diagram_inferred)
        recommended, diff = cls.generate_recommended_diagram(workflow, findings, existing)
        return existing, recommended, diff

    @classmethod
    def generate_existing_diagram(
        cls,
        workflow: WorkflowInput,
        findings: Sequence[Finding],
        is_diagram_inferred: bool = False,
        title: str = "Existing Delivery Pipeline",
        highlight_new_nodes_from: set[str] | None = None,
    ) -> WorkflowDiagramModel:
        """Constructs the delivery pipeline diagram with custom title and node styling."""
        nodes: list[DiagramNode] = []
        edges: list[DiagramEdge] = []
        missing_gates: list[str] = []

        # Map stage IDs to findings affecting them
        stage_issues: dict[str, list[str]] = {}
        for f in findings:
            for sid in f.stage_ids:
                stage_issues.setdefault(sid, []).append(f"{f.rule_id}: {f.title}")

        for s in workflow.stages:
            issues = stage_issues.get(s.id, [])
            if highlight_new_nodes_from is not None and s.id not in highlight_new_nodes_from:
                status = "proposed_correction"
            elif issues:
                status = "issue_identified"
            elif is_diagram_inferred:
                status = "unverified"
            else:
                status = "confirmed"

            nodes.append(
                DiagramNode(
                    id=s.id,
                    label=s.name or s.id,
                    stage_type=s.type.value if hasattr(s.type, "value") else str(s.type),
                    status=status,
                    environment="production" if s.type == StageType.DEPLOY_PRODUCTION else (
                        "staging" if s.type == StageType.STAGING_DEPLOY else None
                    ),
                    owner=s.owner,
                    issues=issues,
                )
            )

            for dep in s.depends_on:
                edges.append(
                    DiagramEdge(
                        source=dep,
                        target=s.id,
                        label=None,
                        is_inferred=is_diagram_inferred,
                    )
                )

        # Build Mermaid code
        mermaid_lines = [
            "graph LR",
            "  %% Styling Definitions",
            "  classDef confirmed fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#14532D;",
            "  classDef issue fill:#FFE4E6,stroke:#E11D48,stroke-width:2.5px,color:#881337;",
            "  classDef unverified fill:#F8FAFC,stroke:#94A3B8,stroke-width:1.5px,stroke-dasharray:4 4,color:#334155;",
            "  classDef proposed fill:#EFF6FF,stroke:#2563EB,stroke-width:2.5px,color:#1E3A8A;",
            "",
            f"  subgraph {title}",
        ]

        for n in nodes:
            style = "proposed" if n.status == "proposed_correction" else ("issue" if n.status == "issue_identified" else ("unverified" if n.status == "unverified" else "confirmed"))
            mermaid_lines.append(cls._format_mermaid_node(n.id, n.label, n.stage_type, style))

        for e in edges:
            mermaid_lines.append(cls._format_mermaid_edge(e.source, e.target))

        mermaid_lines.append("  end")

        return WorkflowDiagramModel(
            mermaid_code="\n".join(mermaid_lines),
            nodes=nodes,
            edges=edges,
            total_stages=len(nodes),
            missing_gates=missing_gates,
        )

    @classmethod
    def generate_recommended_diagram(
        cls,
        workflow: WorkflowInput,
        findings: Sequence[Finding],
        existing_diagram: WorkflowDiagramModel,
    ) -> tuple[WorkflowDiagramModel, list[DiagramDiffItem]]:
        """
        Synthesizes a proposed improved workflow architecture that incorporates all
        necessary safety gates, security checks, and deployment verifications.
        """
        existing_types = {s.type for s in workflow.stages}
        diff: list[DiagramDiffItem] = []

        # Baseline stages from existing
        rec_stages: list[dict] = []
        for s in workflow.stages:
            rec_stages.append({
                "id": s.id,
                "label": s.name or s.id,
                "type": s.type,
                "status": "confirmed",
                "depends_on": list(s.depends_on),
                "is_new": False,
            })

        # Identify required safety gates according to rule findings
        rule_ids = {f.rule_id for f in findings}

        # 1. Missing Automated Tests (R01 / R09)
        if StageType.UNIT_TEST not in existing_types or "R01" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-automated-tests",
                    title="Automated Unit & Integration Test Suite",
                    description="Added mandatory automated test execution gate with continue_on_failure=false.",
                    rationale="Eliminates R01/R09 risk of deploying untested or broken regression code to production.",
                )
            )

        # 2. Missing Security Scan (R02)
        if StageType.SECURITY_SCAN not in existing_types or "R02" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-security-scan",
                    title="Security & Vulnerability Scan (DevSecOps)",
                    description="Added automated dependency, secret, and container static analysis gate.",
                    rationale="Eliminates R02/R08 vulnerability windows before deploying artifacts.",
                )
            )

        # 3. Missing Staging Validation (R10)
        if StageType.STAGING_DEPLOY not in existing_types or "R10" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-staging-deploy",
                    title="Staging Pre-Production Deployment & Smoke Test",
                    description="Deploys artifact to pre-production staging environment and runs automated health checks.",
                    rationale="Validates configuration and environmental parity before exposing changes to customers.",
                )
            )

        # 4. Missing Approval Gate (R03)
        if StageType.APPROVAL not in existing_types or "R03" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-approval-gate",
                    title="Release Governance & Change Approval",
                    description="Mandatory sign-off gate by designated release manager or authorized lead.",
                    rationale="Ensures change verification and compliance audit trail before production activation.",
                )
            )

        # 5. Missing Rollback Plan (R04)
        if StageType.ROLLBACK_PLAN not in existing_types or "R04" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-rollback-plan",
                    title="Automated Canary Rollback Plan",
                    description="Pre-computed canary traffic split and automated instant rollback mechanism.",
                    rationale="Guarantees mean-time-to-recovery (MTTR) under 60 seconds if canary error rate spikes.",
                )
            )

        # 6. Missing Post-Deployment Monitoring (R07)
        if StageType.MONITORING_CHECK not in existing_types or "R07" in rule_ids:
            diff.append(
                DiagramDiffItem(
                    action="added",
                    stage_id="rec-monitoring-probe",
                    title="Post-Deploy Health Probe & SLO Verification",
                    description="Continuous telemetry check probing latency, error rates, and system metrics.",
                    rationale="Detects stealth deployment failures immediately post-rollout.",
                )
            )

        # Reconstruct optimal pipeline DAG
        ideal_sequence = [
            ("build", "Build & Package Artifact", StageType.BUILD),
            ("rec-automated-tests", "Automated Unit & Integration Tests", StageType.UNIT_TEST),
            ("rec-security-scan", "Security Scan (SAST, Secrets, Deps)", StageType.SECURITY_SCAN),
            ("rec-staging-deploy", "Staging Deploy & Smoke Validation", StageType.STAGING_DEPLOY),
            ("rec-approval-gate", "Release Governance Approval", StageType.APPROVAL),
            ("rec-rollback-plan", "Canary Rollback Mechanism", StageType.ROLLBACK_PLAN),
            ("deploy_production", "Production Rollout", StageType.DEPLOY_PRODUCTION),
            ("rec-monitoring-probe", "Post-Deploy Health Probe", StageType.MONITORING_CHECK),
        ]

        rec_nodes: list[DiagramNode] = []
        rec_edges: list[DiagramEdge] = []
        prev_node_id: str | None = None

        for stage_id, label, stype in ideal_sequence:
            is_new = any(d.stage_id == stage_id for d in diff)
            status = "proposed_correction" if is_new else "confirmed"

            rec_nodes.append(
                DiagramNode(
                    id=stage_id,
                    label=label,
                    stage_type=stype.value if hasattr(stype, "value") else str(stype),
                    status=status,
                    environment="production" if stype in (StageType.DEPLOY_PRODUCTION, StageType.MONITORING_CHECK) else (
                        "staging" if stype == StageType.STAGING_DEPLOY else None
                    ),
                    owner="platform-team" if is_new else None,
                    issues=[],
                )
            )

            if prev_node_id:
                rec_edges.append(
                    DiagramEdge(
                        source=prev_node_id,
                        target=stage_id,
                        label=None,
                        is_inferred=False,
                    )
                )
            prev_node_id = stage_id

        # Generate Mermaid
        rec_mermaid = [
            "graph LR",
            "  %% Styling Definitions",
            "  classDef confirmed fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#14532D;",
            "  classDef proposed fill:#EFF6FF,stroke:#2563EB,stroke-width:2.5px,color:#1E3A8A;",
            "",
            "  subgraph Future Delivery Pipeline",
        ]

        for n in rec_nodes:
            style = "proposed" if n.status == "proposed_correction" else "confirmed"
            rec_mermaid.append(cls._format_mermaid_node(n.id, n.label, n.stage_type, style))

        for e in rec_edges:
            rec_mermaid.append(cls._format_mermaid_edge(e.source, e.target))

        rec_mermaid.append("  end")

        diagram_model = WorkflowDiagramModel(
            mermaid_code="\n".join(rec_mermaid),
            nodes=rec_nodes,
            edges=rec_edges,
            total_stages=len(rec_nodes),
            missing_gates=[d.title for d in diff],
        )

        return diagram_model, diff

    @classmethod
    def _format_mermaid_node(cls, node_id: str, label: str, stage_type: str, style_class: str) -> str:
        """Constructs a valid, safe Mermaid node definition."""
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", node_id)
        # Escape characters that break Mermaid string escaping
        clean_label = label.replace('"', "'").replace("[", "(").replace("]", ")").replace("\n", " ").strip()
        clean_type = stage_type.replace('"', "'").replace("[", "(").replace("]", ")").replace("\n", " ").strip()
        return f'    {safe_id}["{clean_label}<br/>({clean_type})"]:::{style_class}'

    @classmethod
    def _format_mermaid_edge(cls, source_id: str, target_id: str) -> str:
        """Constructs a valid, safe Mermaid edge definition."""
        safe_src = re.sub(r"[^a-zA-Z0-9_-]", "_", source_id)
        safe_tgt = re.sub(r"[^a-zA-Z0-9_-]", "_", target_id)
        return f"    {safe_src} --> {safe_tgt}"
