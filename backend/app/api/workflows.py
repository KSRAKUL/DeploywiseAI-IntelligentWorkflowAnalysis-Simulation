"""Workflow API Router — transport only, no business logic."""
from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.schemas import (
    Decision,
    ErrorResponse,
    WhatIfRequest,
    WorkflowInput,
)
from app.db.session import get_session
from app.services.analysis import analyze_workflow, simulate_what_if

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowInput,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Create a new workflow from validated JSON."""
    from app.db.models import WorkflowModel, WorkflowVersionModel
    import uuid

    wf_id = str(uuid.uuid4())
    wf = WorkflowModel(
        id=wf_id,
        name=payload.name,
        environment=payload.environment.value,
        change_type=payload.change_type.value,
    )
    db.add(wf)
    await db.flush()

    version = WorkflowVersionModel(
        workflow_id=wf_id,
        version_number=1,
        payload=payload.model_dump(mode="json"),
        schema_version=payload.schema_version,
        is_draft=False,
    )
    db.add(version)
    await db.flush()

    return {
        "workflow_id": wf_id,
        "version_id": version.id,
        "version_number": 1,
        "name": payload.name,
        "environment": payload.environment.value,
    }


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_workflow(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Import a workflow from a JSON file with size and schema validation."""
    # Enforce file size limit
    content = await file.read(settings.max_import_size_bytes + 1)
    if len(content) > settings.max_import_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ErrorResponse.make(
                "FILE_TOO_LARGE",
                f"File exceeds maximum size of {settings.max_import_size_bytes} bytes",
            ).model_dump(),
        )

    try:
        raw = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse.make("INVALID_JSON", f"Invalid JSON: {e}").model_dump(),
        )

    try:
        payload = WorkflowInput(**raw)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse.make("VALIDATION_ERROR", str(e)).model_dump(),
        )

    # Delegate to create
    return await create_workflow(payload, db)


@router.get("")
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_session)],
    verdict: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    """List workflows with pagination and filters."""
    from sqlalchemy import select
    from app.db.models import WorkflowModel

    stmt = select(WorkflowModel)
    if environment:
        stmt = stmt.where(WorkflowModel.environment == environment)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    workflows = result.scalars().all()

    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "workflow_id": wf.id,
                "name": wf.name,
                "environment": wf.environment,
                "change_type": wf.change_type,
                "created_at": wf.created_at.isoformat(),
            }
            for wf in workflows
        ],
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Get a workflow by ID including version history."""
    from sqlalchemy import select
    from app.db.models import WorkflowModel, WorkflowVersionModel

    wf = await db.get(WorkflowModel, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=ErrorResponse.make(
            "NOT_FOUND", f"Workflow '{workflow_id}' not found"
        ).model_dump())

    stmt = select(WorkflowVersionModel).where(
        WorkflowVersionModel.workflow_id == workflow_id
    ).order_by(WorkflowVersionModel.version_number)
    result = await db.execute(stmt)
    versions = result.scalars().all()

    return {
        "workflow_id": wf.id,
        "name": wf.name,
        "environment": wf.environment,
        "created_at": wf.created_at.isoformat(),
        "versions": [
            {
                "version_id": v.id,
                "version_number": v.version_number,
                "is_draft": v.is_draft,
                "payload": v.payload,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
    }


@router.post("/{workflow_id}/analyze")
async def trigger_analysis(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Run deterministic rules + agents; bind to exact workflow version."""
    from sqlalchemy import select
    from app.db.models import (
        WorkflowModel, WorkflowVersionModel,
        AnalysisModel, FindingModel, AgentRunModel,
    )
    import uuid

    # Get latest version
    stmt = select(WorkflowVersionModel).where(
        WorkflowVersionModel.workflow_id == workflow_id
    ).order_by(WorkflowVersionModel.version_number.desc()).limit(1)
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail=ErrorResponse.make(
            "NOT_FOUND", f"No versions found for workflow '{workflow_id}'"
        ).model_dump())

    try:
        workflow = WorkflowInput(**version.payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=ErrorResponse.make(
            "VALIDATION_ERROR", str(e)
        ).model_dump())

    # Run analysis
    try:
        analysis_result = await analyze_workflow(
            workflow=workflow,
            workflow_id=workflow_id,
            workflow_version_id=version.id,
        )
    except Exception as e:
        logger.error(f"Analysis failed for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=ErrorResponse.make(
            "ANALYSIS_FAILED", "Analysis failed — see logs"
        ).model_dump())

    # Persist analysis
    analysis_model = AnalysisModel(
        id=analysis_result.analysis_id,
        workflow_id=workflow_id,
        workflow_version_id=version.id,
        policy_version=analysis_result.policy_version,
        rule_set_version=analysis_result.rule_set_version,
        status=analysis_result.status.value,
        score=analysis_result.score,
        verdict=analysis_result.verdict.value,
        is_blocked=analysis_result.is_blocked,
        category_scores=[cs.model_dump(mode="json") for cs in analysis_result.category_scores],
        completed_at=analysis_result.completed_at,
    )
    db.add(analysis_model)
    await db.flush()

    for finding in analysis_result.findings:
        finding_model = FindingModel(
            analysis_id=analysis_result.analysis_id,
            finding_id=finding.finding_id,
            source=finding.source.value,
            rule_id=finding.rule_id,
            rule_version=finding.rule_version,
            category=finding.category.value,
            severity=finding.severity.value,
            blocking=finding.blocking,
            advisory=finding.advisory,
            stage_ids=finding.stage_ids,
            title=finding.title,
            evidence=finding.evidence,
            why_it_matters=finding.why_it_matters,
            recommended_fix=finding.recommended_fix,
            verification_criteria=finding.verification_criteria,
            confidence=finding.confidence,
        )
        db.add(finding_model)

    return analysis_result.model_dump(mode="json")


@router.get("/{workflow_id}/analysis")
async def get_latest_analysis(
    workflow_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Fetch the latest analysis for a workflow."""
    from sqlalchemy import select
    from app.db.models import AnalysisModel, FindingModel

    stmt = select(AnalysisModel).where(
        AnalysisModel.workflow_id == workflow_id
    ).order_by(AnalysisModel.created_at.desc()).limit(1)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail=ErrorResponse.make(
            "NOT_FOUND", f"No analysis found for workflow '{workflow_id}'"
        ).model_dump())

    findings_stmt = select(FindingModel).where(FindingModel.analysis_id == analysis.id)
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    return {
        "analysis_id": analysis.id,
        "workflow_id": analysis.workflow_id,
        "score": analysis.score,
        "verdict": analysis.verdict,
        "is_blocked": analysis.is_blocked,
        "policy_version": analysis.policy_version,
        "rule_set_version": analysis.rule_set_version,
        "status": analysis.status,
        "category_scores": analysis.category_scores,
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
            }
            for f in findings
        ],
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
    }


@router.post("/{workflow_id}/what-if")
async def what_if_simulation(
    workflow_id: str,
    request: WhatIfRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Run a what-if simulation — NEVER mutates the saved workflow."""
    from sqlalchemy import select
    from app.db.models import WorkflowVersionModel, AnalysisModel, FindingModel

    # Load latest version
    stmt = select(WorkflowVersionModel).where(
        WorkflowVersionModel.workflow_id == workflow_id
    ).order_by(WorkflowVersionModel.version_number.desc()).limit(1)
    result = await db.execute(stmt)
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail=ErrorResponse.make(
            "NOT_FOUND", f"Workflow '{workflow_id}' not found"
        ).model_dump())

    # Load latest analysis for baseline
    analysis_stmt = select(AnalysisModel).where(
        AnalysisModel.workflow_id == workflow_id
    ).order_by(AnalysisModel.created_at.desc()).limit(1)
    analysis_result = await db.execute(analysis_stmt)
    existing_analysis = analysis_result.scalar_one_or_none()

    workflow = WorkflowInput(**version.payload)

    if existing_analysis:
        # Reconstruct AnalysisResult from DB for baseline
        from app.core.schemas import (
            AnalysisResult, AnalysisStatus, Category, CategoryScore,
            Finding, FindingSource, Severity, Verdict,
        )
        findings_stmt = select(FindingModel).where(FindingModel.analysis_id == existing_analysis.id)
        fr = await db.execute(findings_stmt)
        db_findings = fr.scalars().all()

        findings_list = [
            Finding(
                finding_id=f.finding_id,
                source=FindingSource(f.source),
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
            for f in db_findings
        ]

        cat_scores = [
            CategoryScore(**cs) for cs in (existing_analysis.category_scores or [])
        ]

        baseline = AnalysisResult(
            analysis_id=existing_analysis.id,
            workflow_id=workflow_id,
            workflow_version_id=version.id,
            policy_version=existing_analysis.policy_version,
            rule_set_version=existing_analysis.rule_set_version,
            status=AnalysisStatus(existing_analysis.status),
            score=existing_analysis.score,
            verdict=Verdict(existing_analysis.verdict),
            is_blocked=existing_analysis.is_blocked,
            category_scores=cat_scores,
            findings=findings_list,
        )
    else:
        # Run analysis fresh as baseline
        baseline = await analyze_workflow(
            workflow=workflow,
            workflow_id=workflow_id,
            workflow_version_id=version.id,
            run_agents=False,
        )

    result = await simulate_what_if(
        original_workflow=workflow,
        operations=[op.model_dump(mode="json") for op in request.operations],
        original_analysis=baseline,
        workflow_id=workflow_id,
        workflow_version_id=version.id,
    )

    return result


@router.post("/{workflow_id}/decision", status_code=status.HTTP_201_CREATED)
async def record_decision(
    workflow_id: str,
    decision: Decision,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Record a reviewer decision — does NOT deploy."""
    from app.db.models import DecisionModel

    model = DecisionModel(
        id=decision.decision_id,
        workflow_id=workflow_id,
        analysis_id=decision.analysis_id,
        choice=decision.choice.value,
        notes=decision.notes,
        actor=decision.actor,
    )
    db.add(model)

    return {"decision_id": decision.decision_id, "choice": decision.choice.value}
