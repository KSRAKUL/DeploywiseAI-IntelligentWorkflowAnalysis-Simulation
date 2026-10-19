"""Unit tests for deterministic rules R01-R10 (25+ tests)."""
from __future__ import annotations

import pytest

from app.core.graph import build_graph
from app.core.rules.registry import get_all_rules, get_rule_by_id
from app.core.rules.rules import (
    R01MissingTests,
    R02MissingSecurityScan,
    R03MissingApproval,
    R04NoRollbackPlan,
    R05UnownedStage,
    R06InvalidStageOrder,
    R07MissingMonitoring,
    R08UnverifiedDependencyChange,
    R09TestsBypassable,
    R10NoStagingValidation,
)
from app.core.schemas import (
    BlastRadius,
    Severity,
    Stage,
    StageType,
    WorkflowInput,
    WorkflowMetadata,
)


def _make_wf(stages: list[dict], blast_radius: str = "medium", deps_changed: bool = False) -> WorkflowInput:
    return WorkflowInput(
        name="Test Workflow",
        schema_version="1.0",
        metadata=WorkflowMetadata(
            blast_radius=BlastRadius(blast_radius),
            dependencies_changed=deps_changed,
        ),
        stages=[Stage(**s) for s in stages],
    )


# ---------------------------------------------------------------------------
# Registry Tests
# ---------------------------------------------------------------------------

def test_registry_has_10_rules():
    rules = get_all_rules()
    assert len(rules) == 10
    rule_ids = {r.rule_id for r in rules}
    expected = {f"R{i:02d}" for i in range(1, 11)}
    assert rule_ids == expected


def test_registry_get_by_id():
    r1 = get_rule_by_id("R01")
    assert r1 is not None
    assert r1.rule_id == "R01"
    assert get_rule_by_id("NONEXISTENT") is None


# ---------------------------------------------------------------------------
# R01 — Missing Tests
# ---------------------------------------------------------------------------

def test_r01_triggers_when_no_tests():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["build"]},
    ])
    findings = R01MissingTests().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R01"
    assert findings[0].severity == Severity.HIGH
    assert not findings[0].blocking


def test_r01_passes_with_unit_test():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "ut", "name": "Unit Test", "type": StageType.UNIT_TEST, "owner": "team-a", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["ut"]},
    ])
    findings = R01MissingTests().evaluate(build_graph(wf))
    assert len(findings) == 0


def test_r01_passes_with_integration_test():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "it", "name": "Integ Test", "type": StageType.INTEGRATION_TEST, "owner": "team-a", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["it"]},
    ])
    findings = R01MissingTests().evaluate(build_graph(wf))
    assert len(findings) == 0


def test_r01_no_production_stage_returns_empty():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "stg", "name": "Staging", "type": StageType.STAGING_DEPLOY, "owner": "team-a", "depends_on": ["build"]},
    ])
    findings = R01MissingTests().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R02 — Missing Security Scan
# ---------------------------------------------------------------------------

def test_r02_triggers_and_is_blocking():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["build"]},
    ])
    findings = R02MissingSecurityScan().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R02"
    assert findings[0].blocking is True
    assert findings[0].severity == Severity.CRITICAL


def test_r02_passes_with_security_scan():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "sec", "name": "Security Scan", "type": StageType.SECURITY_SCAN, "owner": "team-a", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["sec"]},
    ])
    findings = R02MissingSecurityScan().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R03 — Missing Approval
# ---------------------------------------------------------------------------

def test_r03_triggers_and_is_blocking():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["build"]},
    ])
    findings = R03MissingApproval().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R03"
    assert findings[0].blocking is True
    assert findings[0].severity == Severity.CRITICAL


def test_r03_passes_with_approval():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "appr", "name": "Approve", "type": StageType.APPROVAL, "owner": "team-a", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["appr"]},
    ])
    findings = R03MissingApproval().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R04 — No Rollback Plan
# ---------------------------------------------------------------------------

def test_r04_triggers_with_high_severity():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["build"]},
    ], blast_radius="medium")
    findings = R04NoRollbackPlan().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R04"
    assert findings[0].severity == Severity.HIGH


def test_r04_escalates_to_critical_on_high_blast_radius():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["build"]},
    ], blast_radius="high")
    findings = R04NoRollbackPlan().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].severity == Severity.CRITICAL


def test_r04_passes_with_rollback_plan():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "team-a", "depends_on": []},
        {"id": "rb", "name": "Rollback", "type": StageType.ROLLBACK_PLAN, "owner": "team-a", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "team-a", "depends_on": ["rb"]},
    ])
    findings = R04NoRollbackPlan().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R05 — Unowned Stage
# ---------------------------------------------------------------------------

def test_r05_triggers_on_none_owner():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": None, "depends_on": []},
    ])
    findings = R05UnownedStage().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R05"
    assert findings[0].severity == Severity.MEDIUM


def test_r05_escalates_severity_on_unowned_deploy():
    wf = _make_wf([
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "", "depends_on": []},
    ])
    findings = R05UnownedStage().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].severity == Severity.HIGH


def test_r05_passes_when_all_owned():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
    ])
    findings = R05UnownedStage().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R06 — Invalid Stage Order
# ---------------------------------------------------------------------------

def test_r06_triggers_when_approval_is_after_production_deploy():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
        {"id": "appr", "name": "Approve", "type": StageType.APPROVAL, "owner": "lead", "depends_on": ["prod"]},
    ])
    findings = R06InvalidStageOrder().evaluate(build_graph(wf))
    assert any(f.rule_id == "R06" for f in findings)


def test_r06_passes_when_order_is_correct():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "appr", "name": "Approve", "type": StageType.APPROVAL, "owner": "lead", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["appr"]},
    ])
    findings = R06InvalidStageOrder().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R07 — Missing Monitoring
# ---------------------------------------------------------------------------

def test_r07_triggers_when_no_monitoring_after_prod():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
    ])
    findings = R07MissingMonitoring().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R07"
    assert findings[0].severity == Severity.MEDIUM


def test_r07_passes_with_monitoring_check():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
        {"id": "mon", "name": "Monitor", "type": StageType.MONITORING_CHECK, "owner": "sre", "depends_on": ["prod"]},
    ])
    findings = R07MissingMonitoring().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R08 — Unverified Dependency Change
# ---------------------------------------------------------------------------

def test_r08_triggers_when_deps_changed_and_no_check():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
    ], deps_changed=True)
    findings = R08UnverifiedDependencyChange().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R08"
    assert findings[0].severity == Severity.HIGH


def test_r08_passes_when_deps_not_changed():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["build"]},
    ], deps_changed=False)
    findings = R08UnverifiedDependencyChange().evaluate(build_graph(wf))
    assert len(findings) == 0


def test_r08_passes_with_dependency_check():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "dep", "name": "Dep Check", "type": StageType.DEPENDENCY_CHECK, "owner": "sec", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["dep"]},
    ], deps_changed=True)
    findings = R08UnverifiedDependencyChange().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R09 — Tests Bypassable
# ---------------------------------------------------------------------------

def test_r09_triggers_on_continue_on_failure():
    wf = _make_wf([
        {
            "id": "ut",
            "name": "Unit Test",
            "type": StageType.UNIT_TEST,
            "owner": "dev",
            "depends_on": [],
            "continue_on_failure": True,
        },
    ])
    findings = R09TestsBypassable().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R09"


def test_r09_triggers_on_skippable():
    wf = _make_wf([
        {
            "id": "ut",
            "name": "Unit Test",
            "type": StageType.UNIT_TEST,
            "owner": "dev",
            "depends_on": [],
            "skippable": True,
        },
    ])
    findings = R09TestsBypassable().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R09"


def test_r09_passes_when_tests_strict():
    wf = _make_wf([
        {
            "id": "ut",
            "name": "Unit Test",
            "type": StageType.UNIT_TEST,
            "owner": "dev",
            "depends_on": [],
            "continue_on_failure": False,
            "skippable": False,
        },
    ])
    findings = R09TestsBypassable().evaluate(build_graph(wf))
    assert len(findings) == 0


# ---------------------------------------------------------------------------
# R10 — No Staging Validation
# ---------------------------------------------------------------------------

def test_r10_triggers_when_staging_deploy_missing():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "sv", "name": "Stg Val", "type": StageType.STAGING_VALIDATION, "owner": "qa", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["sv"]},
    ])
    findings = R10NoStagingValidation().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R10"


def test_r10_triggers_when_staging_validation_missing():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "sd", "name": "Stg Deploy", "type": StageType.STAGING_DEPLOY, "owner": "dev", "depends_on": ["build"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["sd"]},
    ])
    findings = R10NoStagingValidation().evaluate(build_graph(wf))
    assert len(findings) == 1
    assert findings[0].rule_id == "R10"


def test_r10_passes_with_ordered_staging_deploy_and_validation():
    wf = _make_wf([
        {"id": "build", "name": "Build", "type": StageType.BUILD, "owner": "dev", "depends_on": []},
        {"id": "sd", "name": "Stg Deploy", "type": StageType.STAGING_DEPLOY, "owner": "dev", "depends_on": ["build"]},
        {"id": "sv", "name": "Stg Val", "type": StageType.STAGING_VALIDATION, "owner": "qa", "depends_on": ["sd"]},
        {"id": "prod", "name": "Prod", "type": StageType.DEPLOY_PRODUCTION, "owner": "sre", "depends_on": ["sv"]},
    ])
    findings = R10NoStagingValidation().evaluate(build_graph(wf))
    assert len(findings) == 0
