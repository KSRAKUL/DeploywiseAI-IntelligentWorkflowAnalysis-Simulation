"""Unit tests for workflow schemas, graph validation, and agent finding validators."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.base import BaseAgent
from app.core.graph import build_graph
from app.core.schemas import (
    Finding,
    FindingSource,
    Stage,
    StageType,
    WorkflowInput,
    WorkflowMetadata,
)
from app.llm.fake import FakeLLM


def test_stage_id_pattern_valid():
    s = Stage(id="valid-stage_1", name="Test", type=StageType.BUILD, depends_on=[])
    assert s.id == "valid-stage_1"


def test_stage_id_pattern_invalid():
    with pytest.raises(ValidationError):
        Stage(id="INVALID-UPPERCASE", name="Test", type=StageType.BUILD, depends_on=[])

    with pytest.raises(ValidationError):
        Stage(id="invalid stage with spaces", name="Test", type=StageType.BUILD, depends_on=[])

    with pytest.raises(ValidationError):
        Stage(id="invalid@chars!", name="Test", type=StageType.BUILD, depends_on=[])


def test_extra_top_level_fields_rejected():
    with pytest.raises(ValidationError):
        WorkflowInput(
            name="Test",
            schema_version="1.0",
            stages=[Stage(id="s1", name="S1", type=StageType.BUILD, depends_on=[])],
            malicious_field="injection",  # extra field
        )


def test_max_stages_limit_enforced():
    stages = [
        Stage(id=f"stage-{i}", name=f"Stage {i}", type=StageType.BUILD, depends_on=[])
        for i in range(101)
    ]
    with pytest.raises(ValidationError) as exc:
        WorkflowInput(name="Big Workflow", schema_version="1.0", stages=stages)
    assert "exceeds maximum stage count" in str(exc.value)


def test_duplicate_stage_ids_rejected():
    with pytest.raises(ValidationError) as exc:
        WorkflowInput(
            name="Duplicates",
            schema_version="1.0",
            stages=[
                Stage(id="build", name="Build 1", type=StageType.BUILD, depends_on=[]),
                Stage(id="build", name="Build 2", type=StageType.UNIT_TEST, depends_on=[]),
            ],
        )
    assert "Duplicate stage IDs" in str(exc.value)


def test_unknown_depends_on_rejected():
    with pytest.raises(ValidationError) as exc:
        WorkflowInput(
            name="Bad Dep",
            schema_version="1.0",
            stages=[
                Stage(id="prod", name="Prod", type=StageType.DEPLOY_PRODUCTION, depends_on=["ghost_stage"]),
            ],
        )
    assert "depends_on unknown stage ID" in str(exc.value)


def test_graph_detects_cyclic_dependency():
    wf = WorkflowInput(
        name="Cyclic Workflow",
        schema_version="1.0",
        stages=[
            Stage(id="stage-a", name="A", type=StageType.BUILD, depends_on=["stage-b"]),
            Stage(id="stage-b", name="B", type=StageType.UNIT_TEST, depends_on=["stage-a"]),
        ],
    )
    graph = build_graph(wf)
    assert any(e.code == "CYCLIC_DEPENDENCY" for e in graph.errors)


def test_finding_validator_rejects_agent_blocking_attempt():
    with pytest.raises(ValidationError) as exc:
        Finding(
            source=FindingSource.AGENT,
            rule_id="A-01",
            category="security",
            severity="critical",
            blocking=True,  # VIOLATION
            stage_ids=["s1"],
            title="Attempted block",
            evidence="Evidence",
            why_it_matters="Matters",
            recommended_fix="Fix",
            verification_criteria="Verify",
            advisory=True,
        )
    assert "Agent findings cannot set blocking=True" in str(exc.value)


def test_finding_validator_rejects_agent_non_advisory():
    with pytest.raises(ValidationError) as exc:
        Finding(
            source=FindingSource.AGENT,
            rule_id="A-01",
            category="security",
            severity="critical",
            blocking=False,
            stage_ids=["s1"],
            title="Non-advisory agent finding",
            evidence="Evidence",
            why_it_matters="Matters",
            recommended_fix="Fix",
            verification_criteria="Verify",
            advisory=False,  # VIOLATION
        )
    assert "Agent findings must have advisory=True" in str(exc.value)


def test_agent_validator_rejects_unknown_stage_id():
    agent = BaseAgent(FakeLLM())
    agent.role = "security"
    raw_findings = [
        {
            "finding_id": "test-1",
            "rule_id": "A-SEC-01",
            "category": "security",
            "severity": "medium",
            "stage_ids": ["non_existent_stage"],
            "title": "Advisory note",
            "evidence": "Evidence present",
            "why_it_matters": "Matters",
            "recommended_fix": "Fix",
            "verification_criteria": "Verify",
        }
    ]
    valid, rejected = agent._validate_findings(raw_findings, valid_stage_ids={"stage-1", "stage-2"})
    assert len(valid) == 0
    assert rejected == 1


def test_agent_validator_rejects_empty_evidence():
    agent = BaseAgent(FakeLLM())
    agent.role = "qa"
    raw_findings = [
        {
            "finding_id": "test-2",
            "rule_id": "A-QA-01",
            "category": "testing",
            "severity": "low",
            "stage_ids": ["stage-1"],
            "title": "Advisory note",
            "evidence": "   ",  # whitespace only
            "why_it_matters": "Matters",
            "recommended_fix": "Fix",
            "verification_criteria": "Verify",
        }
    ]
    valid, rejected = agent._validate_findings(raw_findings, valid_stage_ids={"stage-1"})
    assert len(valid) == 0
    assert rejected == 1
