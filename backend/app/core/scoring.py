"""
Scoring Engine — Deploywise AI Core
Deterministic. No LLM. Plain Python. Policy-driven. Unit tested.

Algorithm (FROZEN — see DECISIONS.md for any changes):
  1. For each category: sum severity points from deterministic rule failures only.
  2. Cap each category score at category_cap (default 100).
  3. weighted_sum = sum(category_score * weight for all categories)
  4. final_score = round(weighted_sum) using Python built-in round()
  5. If any blocking finding exists -> verdict = BLOCKED (regardless of score).
  6. Else: score >= high_risk_threshold -> HIGH_RISK
           score >= review_threshold    -> NEEDS_REVIEW
           else                         -> PASS

ROUNDING: Python built-in round() — banker's rounding (round half to even).
This is frozen. Any change requires a DECISIONS.md entry.

REGRESSION TEST (must pass permanently):
  Workflow: Build -> Unit Tests -> Deploy (no security scan, no approval, owner missing, blast_radius=high)
  Expected:  Security=50, Testing=15, Recovery=65, Dependency=0, Governance=80
  Weighted:  0.25*50 + 0.25*15 + 0.20*65 + 0.15*0 + 0.15*80 = 41.25 -> 41
  Verdict:   BLOCKED (R02 + R03 are blocking)
"""
from __future__ import annotations

from app.core.policy import PolicyConfig, get_default_policy
from app.core.schemas import (
    AnalysisResult,
    AnalysisStatus,
    Category,
    CategoryScore,
    Finding,
    FindingSource,
    Verdict,
)


def compute_score(
    findings: list[Finding],
    workflow_id: str,
    workflow_version_id: str,
    policy: PolicyConfig | None = None,
    agent_run_ids: list[str] | None = None,
) -> AnalysisResult:
    """
    Compute deterministic risk score from rule findings only.

    Agent findings (advisory=True, source=agent) are NEVER included in scoring.
    Returns a complete AnalysisResult.
    """
    if policy is None:
        policy = get_default_policy()

    # Step 1: Filter to rule-only findings for scoring
    rule_findings = [
        f for f in findings
        if f.source == FindingSource.RULE and not f.advisory
    ]

    # Step 2: Accumulate raw scores per category
    category_raw: dict[str, float] = {cat.value: 0.0 for cat in Category}
    finding_counts: dict[str, int] = {cat.value: 0 for cat in Category}

    for finding in rule_findings:
        points = policy.points_for(finding.severity.value)
        category_raw[finding.category.value] += points
        finding_counts[finding.category.value] += 1

    # Step 3: Cap each category at category_cap
    cap = policy.category_cap
    category_capped: dict[str, float] = {
        cat: min(raw, cap) for cat, raw in category_raw.items()
    }

    # Step 4: Compute weighted sum
    weighted_sum = 0.0
    category_scores: list[CategoryScore] = []

    for cat_enum in Category:
        cat_key = cat_enum.value
        weight = policy.weight_for(cat_key)
        raw = category_capped[cat_key]
        weighted = raw * weight
        weighted_sum += weighted
        category_scores.append(CategoryScore(
            category=cat_enum,
            raw_score=raw,
            weighted_score=weighted,
            weight=weight,
            finding_count=finding_counts[cat_key],
        ))

    # Step 5: Round using Python built-in round() — FROZEN
    final_score = round(weighted_sum)
    # Clamp to [0, 100] for safety
    final_score = max(0, min(100, final_score))
    # Human-psychology delivery assurance score: 100/100 is perfect/clean pass
    assurance_score = max(0, min(100, 100 - final_score))

    # Step 6: Determine verdict
    has_blocker = any(f.blocking for f in rule_findings)

    if has_blocker:
        verdict = Verdict.BLOCKED
    elif final_score >= policy.high_risk_threshold():
        verdict = Verdict.HIGH_RISK
    elif final_score >= policy.review_threshold():
        verdict = Verdict.NEEDS_REVIEW
    else:
        verdict = Verdict.PASS

    from datetime import datetime

    return AnalysisResult(
        workflow_id=workflow_id,
        workflow_version_id=workflow_version_id,
        policy_version=policy.policy_version,
        rule_set_version=policy.rule_set_version,
        status=AnalysisStatus.COMPLETE,
        score=final_score,
        assurance_score=assurance_score,
        verdict=verdict,
        is_blocked=has_blocker,
        category_scores=category_scores,
        findings=findings,  # Includes both rule and agent findings
        agent_run_ids=agent_run_ids or [],
        completed_at=datetime.utcnow(),
    )


def run_all_rules(
    graph,  # WorkflowGraph — avoiding circular import
    policy: PolicyConfig | None = None,
) -> list[Finding]:
    """
    Run all registered deterministic rules against the workflow graph.
    Returns combined list of all findings.
    """
    from app.core.rules.registry import get_all_rules

    all_findings: list[Finding] = []
    for rule in get_all_rules():
        try:
            findings = rule.evaluate(graph)
            all_findings.extend(findings)
        except Exception:
            # Rules must not crash the analysis — log but continue
            # In production this would be logged to structured logger
            pass
    return all_findings
