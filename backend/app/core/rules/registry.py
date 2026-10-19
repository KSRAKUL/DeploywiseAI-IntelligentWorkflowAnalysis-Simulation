"""Rule registry — returns all active rules in evaluation order."""
from __future__ import annotations

from app.core.rules.base import BaseRule
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

RULE_REGISTRY: list[BaseRule] = [
    R01MissingTests(),
    R02MissingSecurityScan(),
    R03MissingApproval(),
    R04NoRollbackPlan(),
    R05UnownedStage(),
    R06InvalidStageOrder(),
    R07MissingMonitoring(),
    R08UnverifiedDependencyChange(),
    R09TestsBypassable(),
    R10NoStagingValidation(),
]

RULE_SET_VERSION = "1.0.0"


def get_all_rules() -> list[BaseRule]:
    """Return all registered deterministic rules."""
    return RULE_REGISTRY


def get_rule_by_id(rule_id: str) -> BaseRule | None:
    """Return a rule by its ID, or None if not found."""
    for rule in RULE_REGISTRY:
        if rule.rule_id == rule_id:
            return rule
    return None
