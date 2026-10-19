"""
Policy Loader — Deploywise AI
Loads and validates the scoring policy from YAML.
Policy weights are FROZEN — do not change without DECISIONS.md entry.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PolicyConfig(BaseModel):
    """Validated scoring policy configuration."""

    policy_version: str = "1.0.0"
    rule_set_version: str = "1.0.0"
    category_weights: dict[str, float]
    severity_points: dict[str, int]
    category_cap: int = Field(default=100, ge=1)
    verdict_thresholds: dict[str, int]

    def weight_for(self, category: str) -> float:
        """Return the weight for a category (0.0 if not found)."""
        return self.category_weights.get(category, 0.0)

    def points_for(self, severity: str) -> int:
        """Return the severity points (0 if not found)."""
        return self.severity_points.get(severity, 0)

    def high_risk_threshold(self) -> int:
        """Score threshold for HIGH_RISK verdict."""
        return self.verdict_thresholds.get("high_risk", 60)

    def review_threshold(self) -> int:
        """Score threshold for NEEDS_REVIEW verdict."""
        return self.verdict_thresholds.get("review", 30)


_DEFAULT_POLICY: PolicyConfig | None = None


def load_policy(policy_path: Path | None = None) -> PolicyConfig:
    """
    Load policy from YAML file.
    Defaults to data/policies/default_policy_v1.yaml relative to project root.
    """
    global _DEFAULT_POLICY

    if policy_path is None:
        here = Path(__file__).resolve().parent
        candidates = [
            here.parents[2] / "data" / "policies" / "default_policy_v1.yaml",
            here.parents[1] / "data" / "policies" / "default_policy_v1.yaml",
            Path.cwd() / "data" / "policies" / "default_policy_v1.yaml",
            Path.cwd().parent / "data" / "policies" / "default_policy_v1.yaml",
        ]
        for cand in candidates:
            if cand.exists():
                policy_path = cand
                break
        else:
            policy_path = candidates[0]

    with policy_path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    return PolicyConfig(**raw)


def get_default_policy() -> PolicyConfig:
    """Return the singleton default policy, loading it on first call."""
    global _DEFAULT_POLICY
    if _DEFAULT_POLICY is None:
        _DEFAULT_POLICY = load_policy()
    return _DEFAULT_POLICY
