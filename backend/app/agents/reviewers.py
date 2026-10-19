"""Four specialist agents + Recommendation agent."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.llm.provider import LLMProvider


class SecurityAgent(BaseAgent):
    """Reviews scan placement, secrets, approval considerations."""
    role = "Security Reviewer"
    category = "security"


class QAAgent(BaseAgent):
    """Reviews test stage order, coverage gaps, failure handling."""
    role = "QA Assurance Reviewer"
    category = "testing"


class DependencyAgent(BaseAgent):
    """Reviews dependency changes, compatibility, validation order."""
    role = "Dependency Reviewer"
    category = "dependency"


class OperationsAgent(BaseAgent):
    """Reviews rollback ownership, monitoring, recovery readiness."""
    role = "Operations Resilience Reviewer"
    category = "recovery"


class RecommendationAgent(BaseAgent):
    """Produces prioritized action plan with trade-offs after reading all findings."""
    role = "Recommendation Summarizer"
    category = "governance"


def build_agents(llm: LLMProvider) -> list[BaseAgent]:
    """Return all active agents in evaluation order."""
    return [
        SecurityAgent(llm),
        QAAgent(llm),
        DependencyAgent(llm),
        OperationsAgent(llm),
        RecommendationAgent(llm),
    ]
