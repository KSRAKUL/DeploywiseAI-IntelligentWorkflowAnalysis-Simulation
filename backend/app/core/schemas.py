"""
Frozen Data Contracts — Deploywise AI
WARNING: Do NOT modify these schemas without creating a DECISIONS.md entry.
Tag: contracts-v1
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class StageType(str, Enum):
    BUILD = "build"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    SECURITY_SCAN = "security_scan"
    SECRETS_SCAN = "secrets_scan"
    DEPENDENCY_CHECK = "dependency_check"
    STAGING_DEPLOY = "staging_deploy"
    STAGING_VALIDATION = "staging_validation"
    APPROVAL = "approval"
    ROLLBACK_PLAN = "rollback_plan"
    DEPLOY_PRODUCTION = "deploy_production"
    MONITORING_CHECK = "monitoring_check"
    NOTIFY = "notify"
    CUSTOM = "custom"


class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class ChangeType(str, Enum):
    STANDARD = "standard"
    EMERGENCY = "emergency"
    PATCH = "patch"
    MAJOR = "major"
    MINOR = "minor"


class BlastRadius(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(str, Enum):
    SECURITY = "security"
    TESTING = "testing"
    RECOVERY = "recovery"
    DEPENDENCY = "dependency"
    GOVERNANCE = "governance"
    MAINTAINABILITY = "maintainability"
    OBSERVABILITY = "observability"


class FindingSource(str, Enum):
    RULE = "rule"
    AGENT = "agent"
    SCANNER = "scanner"


class Verdict(str, Enum):
    BLOCKED = "BLOCKED"
    HIGH_RISK = "HIGH_RISK"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PASS = "PASS"
    INCOMPLETE = "INCOMPLETE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ERROR = "ERROR"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Workflow Schemas (Frozen)
# ---------------------------------------------------------------------------

STAGE_ID_PATTERN = r"^[a-z0-9_-]{1,40}$"
MAX_STAGES = 100


class WorkflowMetadata(BaseModel):
    """Workflow-level metadata."""
    model_config = {"extra": "forbid"}

    blast_radius: BlastRadius = BlastRadius.MEDIUM
    dependencies_changed: bool = False


class Stage(BaseModel):
    """A single stage in the workflow graph."""
    model_config = {"extra": "forbid"}

    id: str = Field(..., pattern=STAGE_ID_PATTERN)
    name: str = Field(..., min_length=1, max_length=200)
    type: StageType
    owner: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    continue_on_failure: bool = False
    skippable: bool = False
    exception_expiry: datetime | None = None

    @field_validator("depends_on")
    @classmethod
    def depends_on_ids_format(cls, v: list[str]) -> list[str]:
        """Validate all dependency IDs match the stage ID pattern."""
        import re
        pattern = re.compile(STAGE_ID_PATTERN)
        for dep_id in v:
            if not pattern.match(dep_id):
                raise ValueError(f"Dependency ID '{dep_id}' does not match pattern {STAGE_ID_PATTERN}")
        return v


class WorkflowInput(BaseModel):
    """Incoming workflow JSON — frozen contract."""
    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, max_length=200)
    schema_version: str = Field(default="1.0")
    environment: Environment = Environment.PRODUCTION
    change_type: ChangeType = ChangeType.STANDARD
    stages: list[Stage] = Field(..., min_length=1)
    metadata: WorkflowMetadata = Field(default_factory=WorkflowMetadata)

    @field_validator("stages")
    @classmethod
    def validate_stage_count(cls, v: list[Stage]) -> list[Stage]:
        """Enforce max stage limit."""
        if len(v) > MAX_STAGES:
            raise ValueError(f"Workflow exceeds maximum stage count of {MAX_STAGES}")
        return v

    @model_validator(mode="after")
    def validate_stage_ids_unique_and_deps_exist(self) -> "WorkflowInput":
        """Ensure stage IDs are unique and all depends_on references exist."""
        ids = [s.id for s in self.stages]
        if len(ids) != len(set(ids)):
            duplicates = [i for i in ids if ids.count(i) > 1]
            raise ValueError(f"Duplicate stage IDs found: {set(duplicates)}")
        id_set = set(ids)
        for stage in self.stages:
            for dep in stage.depends_on:
                if dep not in id_set:
                    raise ValueError(
                        f"Stage '{stage.id}' depends_on unknown stage ID '{dep}'"
                    )
        return self


# ---------------------------------------------------------------------------
# Finding Schema (Frozen)
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """A single risk finding produced by a rule or agent."""
    model_config = {"extra": "forbid"}

    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: FindingSource
    rule_id: str = Field(..., min_length=1, max_length=10)
    rule_version: str = Field(default="1.0.0")
    category: Category
    severity: Severity
    blocking: bool
    stage_ids: list[str]
    title: str = Field(..., min_length=1, max_length=300)
    evidence: str = Field(..., min_length=1)
    why_it_matters: str = Field(..., min_length=1)
    recommended_fix: str = Field(..., min_length=1)
    verification_criteria: str = Field(..., min_length=1)
    confidence: str = Field(default="high")
    advisory: bool = False
    file_path: str | None = None
    line_number: int | None = None
    evidence_status: str = Field(default="confirmed")
    impact: str | None = None
    suggested_patch: str | None = None
    tool_name: str | None = None
    remediation_status: str = Field(default="unresolved")

    @model_validator(mode="after")
    def agents_cannot_block(self) -> "Finding":
        """Agent findings must never be blocking."""
        if self.source == FindingSource.AGENT and self.blocking:
            raise ValueError("Agent findings cannot set blocking=True")
        if self.source == FindingSource.AGENT and not self.advisory:
            raise ValueError("Agent findings must have advisory=True")
        return self


# ---------------------------------------------------------------------------
# Category Score
# ---------------------------------------------------------------------------

class CategoryScore(BaseModel):
    """Weighted score for a single category."""
    model_config = {"extra": "forbid"}

    category: Category
    raw_score: float = Field(..., ge=0.0, le=100.0)
    weighted_score: float = Field(..., ge=0.0)
    weight: float = Field(..., ge=0.0)
    finding_count: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Analysis Result Schema (Frozen)
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """Complete analysis result — includes deterministic results + advisory agent context."""
    model_config = {"extra": "forbid"}

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_version_id: str
    policy_version: str
    rule_set_version: str
    status: AnalysisStatus = AnalysisStatus.COMPLETE
    score: int = Field(..., ge=0, le=100)
    assurance_score: int = Field(default=100, ge=0, le=100)
    verdict: Verdict
    is_blocked: bool
    category_scores: list[CategoryScore]
    findings: list[Finding]
    agent_run_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# What-If Schemas
# ---------------------------------------------------------------------------

class WhatIfOperation(BaseModel):
    """A single operation to apply in a what-if simulation."""
    model_config = {"extra": "forbid"}

    operation: str = Field(..., pattern=r"^(add_stage|remove_stage|add_dependency|remove_dependency|update_stage)$")
    stage_id: str | None = None
    stage: Stage | None = None
    from_id: str | None = None
    to_id: str | None = None
    updates: dict[str, Any] | None = None


class WhatIfRequest(BaseModel):
    """Request body for what-if simulation."""
    model_config = {"extra": "forbid"}

    operations: list[WhatIfOperation] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=500)


class WhatIfResult(BaseModel):
    """Result of a what-if simulation — never mutates the original workflow."""
    model_config = {"extra": "forbid"}

    original_analysis: AnalysisResult
    proposed_analysis: AnalysisResult
    score_delta: int
    assurance_score_delta: int = 0
    verdict_change: bool
    resolved_findings: list[str]    # finding_ids resolved
    still_present_findings: list[str]  # finding_ids still present
    new_findings: list[str]         # finding_ids newly introduced
    graph_valid: bool
    graph_errors: list[str] = Field(default_factory=list)
    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_diagram: WorkflowDiagramModel | None = None
    proposed_diagram: WorkflowDiagramModel | None = None


# ---------------------------------------------------------------------------
# Decision Schema
# ---------------------------------------------------------------------------

class DecisionChoice(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class Decision(BaseModel):
    """Reviewer decision — does NOT trigger deployment."""
    model_config = {"extra": "forbid"}

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    analysis_id: str
    choice: DecisionChoice
    notes: str | None = Field(default=None, max_length=2000)
    actor: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API Error Response
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Single error detail item."""
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Structured error response — never includes stack traces."""
    model_config = {"extra": "forbid"}

    error: dict[str, Any]

    @classmethod
    def make(
        cls,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> "ErrorResponse":
        """Create a standard error response."""
        return cls(
            error={
                "code": code,
                "message": message,
                "details": [d.model_dump() for d in (details or [])],
            }
        )


# ---------------------------------------------------------------------------
# Audit Event
# ---------------------------------------------------------------------------

class AuditEvent(BaseModel):
    """Append-only audit log entry."""
    model_config = {"extra": "forbid"}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    # NOTE: Never include secrets or full workflow payloads in details


# ---------------------------------------------------------------------------
# Project Ingestion & Assessment Schemas
# ---------------------------------------------------------------------------

class AssessmentInputType(str, Enum):
    GITHUB = "github"
    ZIP = "zip"
    CICD = "cicd"
    DIAGRAM = "diagram"
    JSON = "json"


class ProjectStructure(BaseModel):
    """Metadata regarding inspected repository/archive structure."""
    model_config = {"extra": "forbid"}

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    ci_workflows: list[str] = Field(default_factory=list)
    dockerfiles: list[str] = Field(default_factory=list)
    total_files: int = 0
    inspected_files: list[str] = Field(default_factory=list)
    commit_sha: str | None = None
    branch: str | None = None


class ScannerStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED_NOT_INSTALLED = "skipped_not_installed"
    UNSUPPORTED = "unsupported"
    TIMED_OUT = "timed_out"


class ScannerResult(BaseModel):
    """Result of a security, dependency, or static analysis tool execution."""
    model_config = {"extra": "forbid"}

    scanner_name: str
    category: Category
    target: str
    status: ScannerStatus
    duration_ms: int = 0
    finding_count: int = 0
    error_message: str | None = None


class AssessmentCoverage(BaseModel):
    """Assessment coverage metrics."""
    model_config = {"extra": "forbid"}

    total_checks: int
    executed_checks: int
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)


class RemediationItem(BaseModel):
    """Actionable remediation item grouped by priority."""
    model_config = {"extra": "forbid"}

    priority: int = Field(..., ge=1, le=4)
    priority_label: str
    finding_id: str
    title: str
    severity: Severity
    category: Category
    location: str | None = None
    recommended_fix: str
    suggested_patch: str | None = None
    verification_criteria: str
    effort_rationale: str


class DiagramNode(BaseModel):
    """A node inside a workflow diagram."""
    model_config = {"extra": "forbid"}

    id: str
    label: str
    stage_type: str
    status: str = "confirmed"  # "confirmed" | "issue_identified" | "proposed_correction" | "unverified"
    environment: str | None = None
    owner: str | None = None
    issues: list[str] = Field(default_factory=list)


class DiagramEdge(BaseModel):
    """A directional dependency between workflow stages."""
    model_config = {"extra": "forbid"}

    source: str
    target: str
    label: str | None = None
    is_inferred: bool = False


class DiagramDiffItem(BaseModel):
    """A specific change between existing and recommended architectures."""
    model_config = {"extra": "forbid"}

    action: str  # "added" | "modified" | "reordered" | "removed"
    stage_id: str
    title: str
    description: str
    rationale: str


class WorkflowDiagramModel(BaseModel):
    """Structured graph and renderable Mermaid code for workflow diagrams."""
    model_config = {"extra": "forbid"}

    mermaid_code: str
    nodes: list[DiagramNode] = Field(default_factory=list)
    edges: list[DiagramEdge] = Field(default_factory=list)
    total_stages: int = 0
    missing_gates: list[str] = Field(default_factory=list)


class DeveloperEncouragement(BaseModel):
    """Contextual, engineering-honest motivational guidance for developers."""
    model_config = {"extra": "forbid"}

    headline: str
    message: str
    status_level: str  # "healthy" | "needs_attention" | "blocked" | "partial_evidence" | "verified"
    call_to_action: str
    action_items_count: int = 0


class ProjectAssessmentResponse(BaseModel):
    """Complete project workflow & code assurance assessment."""
    model_config = {"extra": "forbid"}

    assessment_id: str
    project_name: str
    input_type: AssessmentInputType
    input_source: str
    created_at: datetime
    commit_sha: str | None = None
    workflow_id: str | None = None
    risk_score: float = Field(..., ge=0.0, le=100.0)
    assurance_score: float = Field(default=100.0, ge=0.0, le=100.0)
    coverage: AssessmentCoverage
    verdict: Verdict
    is_blocked: bool
    structure: ProjectStructure
    scanner_results: list[ScannerResult]
    findings: list[Finding]
    category_scores: list[CategoryScore]
    remediation_roadmap: list[RemediationItem]
    ai_summary: str | None = None

    # Workflow Visual Intelligence & Corrected Architecture
    existing_workflow_diagram: WorkflowDiagramModel | None = None
    recommended_workflow_diagram: WorkflowDiagramModel | None = None
    diagram_comparison: list[DiagramDiffItem] = Field(default_factory=list)

    # Evidence Boundaries & Facts
    observed_facts: list[str] = Field(default_factory=list)
    inferred_relationships: list[str] = Field(default_factory=list)
    unknown_details: list[str] = Field(default_factory=list)
    evidence_boundaries: list[str] = Field(default_factory=list)

    # Developer Motivation & Confidence Building
    developer_encouragement: DeveloperEncouragement | None = None


