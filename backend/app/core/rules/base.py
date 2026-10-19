"""Base class for all Deploywise AI deterministic rules."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.graph import WorkflowGraph
from app.core.schemas import Category, Finding, FindingSource, Severity


class BaseRule(ABC):
    """
    Abstract base for all deterministic rules.

    Rules are pure functions: no LLM, no network, no randomness, no hidden state.
    Each rule returns a list of Findings (empty = no issue found).
    """

    rule_id: str
    rule_version: str = "1.0.0"
    category: Category
    severity: Severity
    blocking: bool = False

    @abstractmethod
    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """
        Evaluate the rule against the workflow graph.

        Returns:
            List of Finding objects. Empty list means the rule passed.
        """
        ...

    def _make_finding(
        self,
        stage_ids: list[str],
        title: str,
        evidence: str,
        why_it_matters: str,
        recommended_fix: str,
        verification_criteria: str,
        severity: Severity | None = None,
        blocking: bool | None = None,
    ) -> Finding:
        """Helper to construct a deterministic Finding."""
        return Finding(
            source=FindingSource.RULE,
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            category=self.category,
            severity=severity or self.severity,
            blocking=blocking if blocking is not None else self.blocking,
            stage_ids=stage_ids,
            title=title,
            evidence=evidence,
            why_it_matters=why_it_matters,
            recommended_fix=recommended_fix,
            verification_criteria=verification_criteria,
            confidence="high",
            advisory=False,
        )
