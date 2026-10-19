"""
Deploywise AI — Project Ingestion & Assessment API Endpoints.
Supports GitHub repository URL, ZIP archive upload, CI/CD YAML, and diagram inputs.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import ProjectAssessmentResponse
from app.db.models import AnalysisModel, FindingModel, WorkflowModel, WorkflowVersionModel
from app.db.session import get_session
from app.services.project_assessment import ProjectAssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


class GitHubAssessmentRequest(BaseModel):
    repo_url: str
    branch: str | None = None


class CICDAssessmentRequest(BaseModel):
    content: str
    filename_hint: str = "workflow.yml"


@router.post("/github", response_model=ProjectAssessmentResponse)
async def assess_github(
    payload: GitHubAssessmentRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectAssessmentResponse:
    """Assess a GitHub repository by URL."""
    service = ProjectAssessmentService(db)
    try:
        return await service.assess_github_repo(payload.repo_url, branch=payload.branch)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INGESTION_ERROR", "message": str(exc)}})


@router.post("/zip", response_model=ProjectAssessmentResponse)
async def assess_zip(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
) -> ProjectAssessmentResponse:
    """Assess an uploaded ZIP archive containing project source code."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_FILE_TYPE", "message": "Only .zip files are supported."}})

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "ZIP archive exceeds 50 MB limit."}})

    service = ProjectAssessmentService(db)
    try:
        return await service.assess_zip_archive(content, filename=file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INGESTION_ERROR", "message": str(exc)}})


@router.post("/cicd", response_model=ProjectAssessmentResponse)
async def assess_cicd(
    payload: CICDAssessmentRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectAssessmentResponse:
    """Assess raw CI/CD workflow YAML or JSON content."""
    service = ProjectAssessmentService(db)
    try:
        return await service.assess_cicd_content(payload.content, filename_hint=payload.filename_hint)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INGESTION_ERROR", "message": str(exc)}})


@router.post("/diagram", response_model=ProjectAssessmentResponse)
async def assess_diagram(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
) -> ProjectAssessmentResponse:
    """Assess a workflow diagram or architecture document image."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Diagram image exceeds 10 MB limit."}})

    service = ProjectAssessmentService(db)
    try:
        return await service.assess_diagram(content, filename=file.filename or "diagram.png")
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INGESTION_ERROR", "message": str(exc)}})


@router.get("", response_model=list[dict])
async def list_assessments(
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 20,
) -> list[dict]:
    """List recent completed project assessments with finding counts."""
    stmt = select(AnalysisModel).order_by(AnalysisModel.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()

    items = []
    for r in records:
        wf = await db.get(WorkflowModel, r.workflow_id)
        findings_stmt = select(FindingModel).where(FindingModel.analysis_id == r.id)
        findings_res = await db.execute(findings_stmt)
        findings = findings_res.scalars().all()
        blocking_count = sum(1 for f in findings if f.blocking)
        items.append({
            "assessment_id": r.id,
            "project_name": wf.name if wf else "Workflow",
            "workflow_id": r.workflow_id,
            "score": r.score,
            "verdict": r.verdict,
            "is_blocked": r.is_blocked,
            "findings_count": len(findings),
            "blocking_count": blocking_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return items


@router.get("/by-workflow/{workflow_id}", response_model=dict)
async def get_latest_assessment_for_workflow(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Get the most recent assessment for a given workflow_id."""
    stmt = (
        select(AnalysisModel)
        .where(AnalysisModel.workflow_id == workflow_id)
        .order_by(AnalysisModel.created_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"No assessment found for workflow '{workflow_id}'."}},
        )

    return await _serialize_assessment(analysis.id, db)


@router.get("/{assessment_id}", response_model=dict)
async def get_assessment(
    assessment_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """
    Retrieve a complete project assessment by assessment ID.
    Returns full assessment data including findings, scanner results,
    category scores, and remediation roadmap from the persisted record.
    """
    analysis = await db.get(AnalysisModel, assessment_id)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Assessment '{assessment_id}' not found."}},
        )

    return await _serialize_assessment(assessment_id, db)


async def _serialize_assessment(assessment_id: str, db: AsyncSession) -> dict:
    """Shared serialization logic for assessment endpoints."""
    analysis = await db.get(AnalysisModel, assessment_id)
    if not analysis:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Assessment not found."}})

    wf = await db.get(WorkflowModel, analysis.workflow_id)
    project_name = wf.name if wf else "Unknown Project"

    findings_stmt = select(FindingModel).where(FindingModel.analysis_id == assessment_id)
    findings_res = await db.execute(findings_stmt)
    findings = findings_res.scalars().all()

    serialized_findings = [
        {
            "finding_id": f.finding_id,
            "source": f.source,
            "rule_id": f.rule_id,
            "rule_version": f.rule_version,
            "category": f.category,
            "severity": f.severity,
            "blocking": f.blocking,
            "advisory": f.advisory,
            "stage_ids": f.stage_ids,
            "title": f.title,
            "evidence": f.evidence,
            "why_it_matters": f.why_it_matters,
            "recommended_fix": f.recommended_fix,
            "verification_criteria": f.verification_criteria,
            "confidence": f.confidence,
        }
        for f in findings
    ]

    # Reconstruct workflow input to regenerate diagram models if version payload exists
    version_stmt = (
        select(WorkflowVersionModel)
        .where(WorkflowVersionModel.workflow_id == analysis.workflow_id)
        .order_by(WorkflowVersionModel.version_number.desc())
        .limit(1)
    )
    version_res = await db.execute(version_stmt)
    version = version_res.scalar_one_or_none()

    existing_diag_dict = None
    rec_diag_dict = None
    diag_diff_list = []

    if version and version.payload:
        from app.core.schemas import Finding as FindingSchema, FindingSource, WorkflowInput
        from app.services.diagram_generator import WorkflowDiagramGenerator

        try:
            wf_obj = WorkflowInput.model_validate(version.payload)
            typed_findings = [
                FindingSchema(
                    finding_id=f.finding_id,
                    source=FindingSource(f.source) if f.source in FindingSource._value2member_map_ else FindingSource.RULE,
                    rule_id=f.rule_id,
                    rule_version=f.rule_version,
                    category=f.category,
                    severity=f.severity,
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
                for f in findings
            ]
            ext_d, rec_d, diff_items = WorkflowDiagramGenerator.generate_both(wf_obj, typed_findings)
            existing_diag_dict = ext_d.model_dump()
            rec_diag_dict = rec_d.model_dump()
            diag_diff_list = [d.model_dump() for d in diff_items]
        except Exception:
            pass

    from app.core.schemas import Verdict
    from app.services.encouragement import DeveloperEncouragementService

    verdict_enum = Verdict(analysis.verdict) if analysis.verdict in Verdict._value2member_map_ else Verdict.NEEDS_REVIEW
    encouragement = DeveloperEncouragementService.generate(
        verdict=verdict_enum,
        is_blocked=analysis.is_blocked,
        blocking_count=sum(1 for f in findings if f.blocking),
        findings_count=len(findings),
        coverage_pct=85.0,
    )

    return {
        "assessment_id": analysis.id,
        "project_name": project_name,
        "workflow_id": analysis.workflow_id,
        "policy_version": analysis.policy_version,
        "rule_set_version": analysis.rule_set_version,
        "risk_score": analysis.score,
        "verdict": analysis.verdict,
        "is_blocked": analysis.is_blocked,
        "category_scores": analysis.category_scores or [],
        "findings": serialized_findings,
        "findings_count": len(serialized_findings),
        "blocking_count": sum(1 for f in findings if f.blocking),
        "status": analysis.status,
        "existing_workflow_diagram": existing_diag_dict,
        "recommended_workflow_diagram": rec_diag_dict,
        "diagram_comparison": diag_diff_list,
        "developer_encouragement": encouragement.model_dump(),
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
    }
