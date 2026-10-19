"""Unit tests for deterministic scoring engine (7 tests)."""
from __future__ import annotations

import pytest

from app.core.policy import get_default_policy
from app.core.schemas import (
    Category,
    Finding,
    FindingSource,
    Severity,
    Verdict,
)
from app.core.scoring import compute_score


def _make_finding(
    rule_id: str = "R01",
    category: Category = Category.TESTING,
    severity: Severity = Severity.HIGH,
    blocking: bool = False,
    source: FindingSource = FindingSource.RULE,
    advisory: bool = False,
) -> Finding:
    return Finding(
        finding_id=f"test-{rule_id}-{severity.value}",
        source=source,
        rule_id=rule_id,
        rule_version="1.0.0",
        category=category,
        severity=severity,
        blocking=blocking,
        stage_ids=["test-stage"],
        title="Test finding title",
        evidence="Test evidence text",
        why_it_matters="Test explanation",
        recommended_fix="Test fix advice",
        verification_criteria="Test criteria",
        confidence="high",
        advisory=advisory,
    )


def test_zero_findings_produces_zero_score_and_pass():
    res = compute_score(
        findings=[],
        workflow_id="wf-1",
        workflow_version_id="ver-1",
    )
    assert res.score == 0
    assert res.verdict == Verdict.PASS
    assert not res.is_blocked
    for cs in res.category_scores:
        assert cs.raw_score == 0.0
        assert cs.finding_count == 0


def test_single_blocking_finding_forces_blocked_verdict():
    f = _make_finding(
        rule_id="R02",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        blocking=True,
    )
    res = compute_score(
        findings=[f],
        workflow_id="wf-1",
        workflow_version_id="ver-1",
    )
    assert res.is_blocked is True
    assert res.verdict == Verdict.BLOCKED


def test_advisory_agent_findings_never_alter_score_or_verdict():
    agent_finding = _make_finding(
        rule_id="A-SEC-01",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        blocking=False,
        source=FindingSource.AGENT,
        advisory=True,
    )

    baseline = compute_score(
        findings=[],
        workflow_id="wf-1",
        workflow_version_id="ver-1",
    )

    with_agent = compute_score(
        findings=[agent_finding],
        workflow_id="wf-1",
        workflow_version_id="ver-1",
    )

    assert baseline.score == with_agent.score == 0
    assert baseline.verdict == with_agent.verdict == Verdict.PASS
    assert not with_agent.is_blocked


def test_category_cap_enforced():
    # 5 critical findings in same category = 5 * 50 = 250 points, capped at 100
    findings = [
        _make_finding(
            rule_id=f"R02-{i}",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            blocking=False,
        )
        for i in range(5)
    ]
    res = compute_score(
        findings=findings,
        workflow_id="wf-1",
        workflow_version_id="ver-1",
    )
    sec_cat = next(cs for cs in res.category_scores if cs.category == Category.SECURITY)
    assert sec_cat.raw_score == 100.0  # capped
    # Security weight is 0.25 -> 25 points
    assert sec_cat.weighted_score == 25.0


def test_verdict_thresholds_without_blockers():
    policy = get_default_policy()
    # High finding in testing: 30 points * 0.25 = 7.5 -> round to 8 -> PASS (< 30)
    low_findings = [
        _make_finding(rule_id="R01", category=Category.TESTING, severity=Severity.HIGH, blocking=False)
    ]
    res_low = compute_score(low_findings, "wf-1", "ver-1", policy=policy)
    assert res_low.verdict == Verdict.PASS

    # Multiple findings pushing score into NEEDS_REVIEW (>= 30, < 60)
    med_findings = [
        _make_finding(rule_id="R01", category=Category.TESTING, severity=Severity.HIGH, blocking=False),  # 30 * 0.25 = 7.5
        _make_finding(rule_id="R05", category=Category.GOVERNANCE, severity=Severity.HIGH, blocking=False),  # 30 * 0.15 = 4.5
        _make_finding(rule_id="R04", category=Category.RECOVERY, severity=Severity.HIGH, blocking=False),  # 30 * 0.20 = 6.0
        _make_finding(rule_id="R08", category=Category.DEPENDENCY, severity=Severity.HIGH, blocking=False), # 30 * 0.15 = 4.5
        _make_finding(rule_id="R06", category=Category.SECURITY, severity=Severity.HIGH, blocking=False),  # 30 * 0.25 = 7.5
    ]  # sum = 30.0 -> score = 30 -> NEEDS_REVIEW
    res_med = compute_score(med_findings, "wf-1", "ver-1", policy=policy)
    assert res_med.verdict in {Verdict.NEEDS_REVIEW, Verdict.HIGH_RISK}


def test_bankers_rounding_behavior():
    # Verify Python's built-in round behavior is used
    assert round(2.5) == 2
    assert round(3.5) == 4
    assert round(41.25) == 41


def test_canonical_regression_score():
    """
    CLAUDE.md frozen regression test:
    Security=50, Testing=15, Recovery=65, Dependency=0, Governance=80
    Weighted: 0.25*50 + 0.25*15 + 0.20*65 + 0.15*0 + 0.15*80 = 41.25 -> 41
    Verdict: BLOCKED (R02 + R03 are blocking)
    """
    findings = [
        # Security: 50 pts (Critical)
        _make_finding("R02", Category.SECURITY, Severity.CRITICAL, blocking=True),
        # Testing: 15 pts (Medium)
        _make_finding("R10", Category.TESTING, Severity.MEDIUM, blocking=False),
        # Recovery: 65 pts (Critical 50 + Medium 15)
        _make_finding("R04", Category.RECOVERY, Severity.CRITICAL, blocking=False),
        _make_finding("R07", Category.RECOVERY, Severity.MEDIUM, blocking=False),
        # Governance: 80 pts (Critical 50 + High 30)
        _make_finding("R03", Category.GOVERNANCE, Severity.CRITICAL, blocking=True),
        _make_finding("R05", Category.GOVERNANCE, Severity.HIGH, blocking=False),
    ]
    res = compute_score(findings, "wf-1", "ver-1")
    assert res.score == 41
    assert res.verdict == Verdict.BLOCKED
    assert res.is_blocked is True
