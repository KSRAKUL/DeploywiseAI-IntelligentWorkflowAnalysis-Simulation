"""
FakeLLM — Controlled JSON responses for testing.
Returns deterministic, schema-valid agent responses for unit/integration tests.
"""
from __future__ import annotations

import json

from app.llm.provider import LLMProvider


FAKE_RESPONSES: dict[str, list[dict]] = {
    "security": [
        {
            "finding_id": "fake-security-001",
            "source": "agent",
            "rule_id": "A-SEC-01",
            "rule_version": "1.0.0",
            "category": "security",
            "severity": "medium",
            "blocking": False,
            "stage_ids": [],
            "title": "Advisory: Consider secrets scanning",
            "evidence": "No secrets_scan stage detected. Recommend adding secrets scanning.",
            "why_it_matters": "Secrets accidentally committed can be exploited if deployed.",
            "recommended_fix": "Add a secrets_scan stage alongside or after security_scan.",
            "verification_criteria": "A secrets_scan stage runs before production.",
            "confidence": "medium",
            "advisory": True,
        }
    ],
    "qa": [
        {
            "finding_id": "fake-qa-001",
            "source": "agent",
            "rule_id": "A-QA-01",
            "rule_version": "1.0.0",
            "category": "testing",
            "severity": "low",
            "blocking": False,
            "stage_ids": [],
            "title": "Advisory: Consider adding integration tests",
            "evidence": "No integration_test stage detected in this workflow.",
            "why_it_matters": "Integration tests catch issues that unit tests miss.",
            "recommended_fix": "Add integration_test stage after unit_test.",
            "verification_criteria": "An integration_test stage exists in the workflow.",
            "confidence": "medium",
            "advisory": True,
        }
    ],
    "dependency": [],
    "operations": [],
    "recommendation": [],
}


class FakeLLM(LLMProvider):
    """
    Fake LLM for testing — returns controlled JSON without any network calls.
    Never use in production.
    """

    def __init__(self, role: str = "security") -> None:
        self._role = role

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return a controlled fake response based on the role."""
        response = FAKE_RESPONSES.get(self._role, [])
        return json.dumps(response)

    async def health_check(self) -> bool:
        """FakeLLM is always available."""
        return True

    @property
    def provider_name(self) -> str:
        return "fake"
