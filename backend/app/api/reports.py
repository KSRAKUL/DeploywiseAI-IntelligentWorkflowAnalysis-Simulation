"""Reports & Policy API Routers — Deploywise AI."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.policy import get_default_policy
from app.db.models import AnalysisModel, FindingModel, WorkflowModel
from app.db.session import get_session
from app.reporting.pdf_generator import generate_assessment_pdf

reports_router = APIRouter(prefix="/reports", tags=["reports"])
policy_router = APIRouter(prefix="/policy", tags=["policy"])


@reports_router.get("/{analysis_id}")
async def get_report(
    analysis_id: str,
    format: str = Query(default="json", pattern="^(json|md)$"),
    db: AsyncSession = Depends(get_session),
):
    """Export analysis report in JSON or Markdown format."""
    analysis = await db.get(AnalysisModel, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Analysis '{analysis_id}' not found"}})

    findings_stmt = select(FindingModel).where(FindingModel.analysis_id == analysis_id)
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    wf = await db.get(WorkflowModel, analysis.workflow_id)
    project_name = wf.name if wf else "Software Delivery Workflow"

    rule_findings = [f for f in findings if f.source == "rule"]
    scanner_findings = [f for f in findings if f.source == "scanner"]
    agent_findings = [f for f in findings if f.source == "agent"]

    if format == "json":
        return {
            "report_version": "2.0",
            "analysis_id": analysis.id,
            "project_name": project_name,
            "workflow_id": analysis.workflow_id,
            "policy_version": analysis.policy_version,
            "rule_set_version": analysis.rule_set_version,
            "risk_score": analysis.score,
            "verdict": analysis.verdict,
            "is_blocked": analysis.is_blocked,
            "status": analysis.status,
            "category_scores": analysis.category_scores,
            "findings_summary": {
                "total": len(findings),
                "rule_based": len(rule_findings),
                "scanner_based": len(scanner_findings),
                "advisory": len(agent_findings),
                "blocking": sum(1 for f in findings if f.blocking),
            },
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "source": f.source,
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "blocking": f.blocking,
                    "advisory": f.advisory,
                    "category": f.category,
                    "stage_ids": f.stage_ids,
                    "title": f.title,
                    "evidence": f.evidence,
                    "why_it_matters": f.why_it_matters,
                    "recommended_fix": f.recommended_fix,
                    "verification_criteria": f.verification_criteria,
                    "confidence": f.confidence,
                }
                for f in findings
            ],
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }

    # Markdown report
    verdict_emoji = {
        "BLOCKED": "🔴",
        "HIGH_RISK": "🟠",
        "NEEDS_REVIEW": "🟡",
        "PASS": "🟢",
        "INSUFFICIENT_EVIDENCE": "⚪",
    }.get(analysis.verdict, "⚪")

    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

    lines = [
        f"# Deploywise AI — Project Assessment Report",
        f"",
        f"> **Assessment ID:** `{analysis.id}`",
        f"> **Project:** {project_name}",
        f"> **Completed:** {analysis.completed_at.isoformat() if analysis.completed_at else 'N/A'}",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **Risk Score** | {analysis.score} / 100 |",
        f"| **Verdict** | {verdict_emoji} {analysis.verdict} |",
        f"| **Release Blocked** | {'⛔ Yes' if analysis.is_blocked else '✅ No'} |",
        f"| **Policy Version** | `{analysis.policy_version}` |",
        f"| **Rule Set Version** | `{analysis.rule_set_version}` |",
        f"| **Total Findings** | {len(findings)} ({len(rule_findings)} rule, {len(scanner_findings)} scanner, {len(agent_findings)} advisory) |",
        f"| **Blocking Findings** | {sum(1 for f in findings if f.blocking)} |",
        f"",
        f"> ### 💡 Developer Guidance",
        f"> **Progress starts with visibility.** Resolve mandatory release blockers first to guarantee safe deployment.",
        f"> Focus on verified security controls, automated test coverage, and continuous monitoring.",
        f"",
        f"## Risk Category Breakdown",
        f"",
        f"| Category | Raw Score | Weight | Weighted Score | Violations |",
        f"|----------|-----------|--------|----------------|------------|",
    ]

    for cs in (analysis.category_scores or []):
        lines.append(
            f"| {cs.get('category', '').title()} | {cs.get('raw_score', 0):.1f} | "
            f"{cs.get('weight', 0) * 100:.0f}% | {cs.get('weighted_score', 0):.2f} pts | "
            f"{cs.get('finding_count', 0)} |"
        )

    lines += [
        f"",
        f"> ⚠️ Advisory agent observations never contribute to raw category points or the final numeric score.",
        f"",
        f"---",
        f"",
        f"## Deterministic Rule Findings ({len(rule_findings)})",
        f"",
    ]

    if not rule_findings:
        lines.append("*No deterministic rule violations identified.*")
    else:
        for f in rule_findings:
            emoji = severity_emoji.get(f.severity, "⚪")
            blocking_label = " **[BLOCKING]**" if f.blocking else ""
            lines += [
                f"### {emoji} [{f.rule_id}]{blocking_label} {f.title}",
                f"",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| **Severity** | {f.severity.upper()} |",
                f"| **Category** | {f.category.title()} |",
                f"| **Blocking** | {'Yes ⛔' if f.blocking else 'No'} |",
                f"| **Affected Stages** | `{', '.join(f.stage_ids) if f.stage_ids else 'N/A'}` |",
                f"| **Confidence** | {f.confidence} |",
                f"",
                f"**Evidence:** {f.evidence}",
                f"",
                f"**Why it matters:** {f.why_it_matters}",
                f"",
                f"**Recommended fix:** {f.recommended_fix}",
                f"",
                f"**Verification:** {f.verification_criteria}",
                f"",
                f"---",
                f"",
            ]

    if scanner_findings:
        lines += [
            f"## Scanner Findings ({len(scanner_findings)})",
            f"",
        ]
        for f in scanner_findings:
            emoji = severity_emoji.get(f.severity, "⚪")
            lines += [
                f"### {emoji} [{f.rule_id}] {f.title}",
                f"",
                f"- **Severity:** {f.severity.upper()}",
                f"- **Category:** {f.category.title()}",
                f"- **Evidence:** {f.evidence}",
                f"- **Recommended fix:** {f.recommended_fix}",
                f"",
            ]

    if agent_findings:
        lines += [
            f"## Advisory Agent Observations ({len(agent_findings)})",
            f"",
            f"> These observations are advisory only and do **not** affect the risk score or verdict.",
            f"",
        ]
        for f in agent_findings:
            lines += [
                f"### 💡 [{f.rule_id}] {f.title}",
                f"",
                f"**Evidence:** {f.evidence}",
                f"",
                f"**Recommended fix:** {f.recommended_fix}",
                f"",
            ]

    lines += [
        f"---",
        f"",
        f"## Reproducibility",
        f"",
        f"- **Engine:** Deploywise AI v0.1.0",
        f"- **Policy Version:** `{analysis.policy_version}`",
        f"- **Rule Set Version:** `{analysis.rule_set_version}`",
        f"- **Workflow ID:** `{analysis.workflow_id}`",
        f"",
        f"*This report was generated by Deploywise AI deterministic rule engine. "
        f"AI advisory content (if any) is clearly labeled and does not affect scores.*",
    ]

    return PlainTextResponse("\n".join(lines), media_type="text/markdown")


@reports_router.get("/{analysis_id}/pdf")
async def download_pdf_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Generate and download publication-grade PDF assessment report."""
    analysis = await db.get(AnalysisModel, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Analysis '{analysis_id}' not found"}})

    findings_stmt = select(FindingModel).where(FindingModel.analysis_id == analysis_id)
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    wf = await db.get(WorkflowModel, analysis.workflow_id)
    project_name = wf.name if wf else "Software Delivery Workflow"

    scanner_finding_count = sum(1 for f in findings if f.source == "scanner")
    total_checks = 10 + len([f for f in findings if f.source == "scanner"])

    # Generate encouragement and diagram comparison if available
    from app.core.schemas import Verdict
    from app.services.encouragement import DeveloperEncouragementService

    v_enum = Verdict(analysis.verdict) if analysis.verdict in Verdict._value2member_map_ else Verdict.NEEDS_REVIEW
    encouragement = DeveloperEncouragementService.generate(
        verdict=v_enum,
        is_blocked=analysis.is_blocked,
        blocking_count=sum(1 for f in findings if f.blocking),
        findings_count=len(findings),
        coverage_pct=90.0,
    )

    diff_items = []
    from app.db.models import WorkflowVersionModel
    version_stmt = select(WorkflowVersionModel).where(WorkflowVersionModel.workflow_id == analysis.workflow_id).order_by(WorkflowVersionModel.version_number.desc()).limit(1)
    version_res = await db.execute(version_stmt)
    version = version_res.scalar_one_or_none()
    if version and version.payload:
        from app.core.schemas import WorkflowInput
        from app.services.diagram_generator import WorkflowDiagramGenerator
        try:
            wf_obj = WorkflowInput.model_validate(version.payload)
            _, _, diff_items_obj = WorkflowDiagramGenerator.generate_both(wf_obj, [])
            diff_items = [d.model_dump() for d in diff_items_obj]
        except Exception:
            pass

    payload = {
        "assessment_id": analysis.id,
        "project_name": project_name,
        "workflow_id": analysis.workflow_id,
        "policy_version": analysis.policy_version,
        "rule_set_version": analysis.rule_set_version,
        "risk_score": analysis.score,
        "verdict": analysis.verdict,
        "is_blocked": analysis.is_blocked,
        "category_scores": analysis.category_scores,
        "developer_encouragement": encouragement.model_dump(),
        "diagram_comparison": diff_items,
        "evidence_boundaries": [
            "Inspection Scope: Verified files and pipelines parsed within input workspace.",
            "Static Verification: Deterministic safety rules and scanners run on detected manifests.",
            "Runtime Verification: Actual environment secrets and live probe results require production telemetry.",
        ],
        "coverage": {
            "coverage_percentage": 100.0 if not findings else round(
                (sum(1 for f in findings if f.source != "scanner") / max(total_checks, 1)) * 100, 1
            ),
            "executed_checks": total_checks,
            "total_checks": total_checks,
        },
        "findings": [
            {
                "finding_id": f.finding_id,
                "source": f.source,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "blocking": f.blocking,
                "advisory": f.advisory,
                "category": f.category,
                "stage_ids": f.stage_ids,
                "title": f.title,
                "evidence": f.evidence,
                "why_it_matters": f.why_it_matters,
                "recommended_fix": f.recommended_fix,
                "verification_criteria": f.verification_criteria,
            }
            for f in findings
        ],
    }

    try:
        pdf_bytes = generate_assessment_pdf(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": {"code": "PDF_GENERATION_FAILED", "message": str(exc)}})

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Deploywise_Assessment_{analysis_id[:8]}.pdf"',
        },
    )


@policy_router.get("")
async def get_policy() -> dict:
    """Return current policy weights, thresholds, and rule versions."""
    policy = get_default_policy()
    return {
        "policy_version": policy.policy_version,
        "rule_set_version": policy.rule_set_version,
        "category_weights": policy.category_weights,
        "severity_points": policy.severity_points,
        "category_cap": policy.category_cap,
        "verdict_thresholds": policy.verdict_thresholds,
    }
