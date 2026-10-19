"""Audit Log API Router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEventModel
from app.db.session import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_events(
    db: Annotated[AsyncSession, Depends(get_session)],
    workflow_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    """Paginated append-only audit log. Never exposes secrets."""
    stmt = select(AuditEventModel).order_by(AuditEventModel.timestamp.desc())
    if workflow_id:
        stmt = stmt.where(
            AuditEventModel.entity_id == workflow_id,
            AuditEventModel.entity_type == "workflow",
        )
    if action:
        stmt = stmt.where(AuditEventModel.action == action)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    events = result.scalars().all()

    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "details": e.details,
            }
            for e in events
        ],
    }
