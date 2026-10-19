"""
Deploywise AI — Contextual Developer Encouragement Engine.
Provides engineering-honest, professional motivational guidance for developers
without obscuring risks or altering readiness verdicts.
"""
from __future__ import annotations

from app.core.schemas import DeveloperEncouragement, Verdict


class DeveloperEncouragementService:
    """Generates outcome-aligned developer motivation and actionable guidance."""

    @staticmethod
    def generate(
        verdict: Verdict,
        is_blocked: bool,
        blocking_count: int,
        findings_count: int,
        coverage_pct: float,
        is_diagram_only: bool = False,
        is_verified_rerun: bool = False,
    ) -> DeveloperEncouragement:
        """
        Produce a motivational message that directly reflects the assessment state.
        
        Rules:
        - Never show an "all clear" message when blockers exist.
        - Encourage progress without minimizing risks.
        - Clearly signal unverified or partial evidence.
        """
        # Scenario 1: Post-remediation rerun where checks passed
        if is_verified_rerun and not is_blocked and blocking_count == 0:
            return DeveloperEncouragement(
                headline="Verification Confirmed",
                message="Nice work! The selected fixes have passed all rerun safety gates. Step by step, your delivery pipeline is becoming more reliable and maintainable.",
                status_level="verified",
                call_to_action="Proceed to staging deployment validation or final release review.",
                action_items_count=findings_count,
            )

        # Scenario 2: Active blockers detected (Critical risk)
        if is_blocked or blocking_count > 0:
            plural = "blocker" if blocking_count == 1 else "blockers"
            return DeveloperEncouragement(
                headline="Clear Path to Production Readiness",
                message=(
                    f"Good progress starts with visibility. {blocking_count} mandatory release {plural} "
                    f"were identified. Every issue resolved here prevents a high-severity production incident. "
                    f"Follow the prioritized remediation plan below to eliminate blockers systematically."
                ),
                status_level="blocked",
                call_to_action=f"Address the {blocking_count} highest-priority blockers first, then re-verify.",
                action_items_count=blocking_count,
            )

        # Scenario 3: Needs Review / Non-blocking warnings
        if verdict in (Verdict.NEEDS_REVIEW, Verdict.HIGH_RISK) or findings_count > 0:
            return DeveloperEncouragement(
                headline="Opportunity to Strengthen Your Delivery Pipeline",
                message=(
                    f"Your workflow has solid momentum with {findings_count} advisory improvement opportunities. "
                    "Addressing these security and quality gaps now will dramatically reduce tech debt and increase delivery velocity."
                ),
                status_level="needs_attention",
                call_to_action="Review recommended architectural improvements and schedule non-blocking enhancements.",
                action_items_count=findings_count,
            )

        # Scenario 4: Partial evidence / Diagram or document only
        if is_diagram_only or coverage_pct < 50.0:
            return DeveloperEncouragement(
                headline="Promising Baseline — Complete Evidence Needed",
                message=(
                    "You have established a valuable architectural baseline from your uploaded design. "
                    "Because static diagrams cannot execute code or verify runtime secrets, connect your repository or CI/CD pipeline to complete full assurance."
                ),
                status_level="partial_evidence",
                call_to_action="Run automated scanners against source code and CI/CD YAML to confirm production readiness.",
                action_items_count=0,
            )

        # Scenario 5: Healthy / Pass with high coverage
        return DeveloperEncouragement(
            headline="Strong Delivery Foundation",
            message=(
                "Great work! The verification checks completed so far show a well-governed, resilient delivery workflow. "
                "Keep maintaining your automated quality gates, security scans, and post-deployment monitoring as your codebase evolves."
            ),
            status_level="healthy",
            call_to_action="Maintain automated compliance checks on every pull request.",
            action_items_count=0,
        )
