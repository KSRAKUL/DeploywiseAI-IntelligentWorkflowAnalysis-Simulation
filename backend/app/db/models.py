"""SQLAlchemy database models for Deploywise AI."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base for all ORM models."""
    pass


class WorkflowModel(Base):
    """Workflow metadata record."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    versions: Mapped[list[WorkflowVersionModel]] = relationship(
        "WorkflowVersionModel", back_populates="workflow", cascade="all, delete-orphan"
    )
    analyses: Mapped[list[AnalysisModel]] = relationship(
        "AnalysisModel", back_populates="workflow"
    )


class WorkflowVersionModel(Base):
    """Immutable snapshot of a workflow version."""

    __tablename__ = "workflow_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # Full immutable JSON
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow: Mapped[WorkflowModel] = relationship("WorkflowModel", back_populates="versions")
    analyses: Mapped[list[AnalysisModel]] = relationship(
        "AnalysisModel", back_populates="workflow_version"
    )

    __table_args__ = (
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version"),
    )


class PolicyModel(Base):
    """Stored policy versions."""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    rule_set_version: Mapped[str] = mapped_column(String(20), nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    thresholds: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisModel(Base):
    """Analysis run record."""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id"), nullable=False
    )
    workflow_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow_versions.id"), nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    verdict: Mapped[str] = mapped_column(String(20), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=True)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    workflow: Mapped[WorkflowModel] = relationship("WorkflowModel", back_populates="analyses")
    workflow_version: Mapped[WorkflowVersionModel] = relationship(
        "WorkflowVersionModel", back_populates="analyses"
    )
    findings: Mapped[list[FindingModel]] = relationship(
        "FindingModel", back_populates="analysis", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list[AgentRunModel]] = relationship(
        "AgentRunModel", back_populates="analysis", cascade="all, delete-orphan"
    )


class FindingModel(Base):
    """Individual finding record."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    finding_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(10), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False)
    advisory: Mapped[bool] = mapped_column(Boolean, default=False)
    stage_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_fix: Mapped[str] = mapped_column(Text, nullable=False)
    verification_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="high")

    analysis: Mapped[AnalysisModel] = relationship("AnalysisModel", back_populates="findings")


class AgentRunModel(Base):
    """Agent execution record."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # ok, timeout, invalid_output, unavailable
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0)
    output_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped[AnalysisModel] = relationship("AnalysisModel", back_populates="agent_runs")


class WhatIfRunModel(Base):
    """What-if simulation record — never mutates workflow."""

    __tablename__ = "what_if_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False)
    workflow_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    operations: Mapped[list] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    score_delta: Mapped[int] = mapped_column(Integer, nullable=True)
    verdict_change: Mapped[bool] = mapped_column(Boolean, nullable=True)
    result_snapshot: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DecisionModel(Base):
    """Reviewer decision record — does NOT trigger deployment."""

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_id: Mapped[str] = mapped_column(String(36), nullable=False)
    analysis_id: Mapped[str] = mapped_column(String(36), nullable=False)
    choice: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEventModel(Base):
    """Append-only audit log — never includes secrets or full payloads."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    # NOTE: Never include secrets or full workflow payloads in details
