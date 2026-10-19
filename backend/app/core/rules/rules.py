"""
Rules R01–R10 — All 10 Deterministic Deploywise AI Rules.
Pure Python. No LLM, no network, no randomness.
"""
from __future__ import annotations

from app.core.graph import WorkflowGraph
from app.core.rules.base import BaseRule
from app.core.schemas import (
    BlastRadius,
    Category,
    Finding,
    Severity,
    StageType,
)


# ---------------------------------------------------------------------------
# R01 — Missing Tests
# ---------------------------------------------------------------------------

class R01MissingTests(BaseRule):
    """
    R01: Any path to production bypasses all unit/integration test stages.
    Severity: High | Blocking: No
    """

    rule_id = "R01"
    category = Category.TESTING
    severity = Severity.HIGH
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check that every production node has at least one test ancestor."""
        if not graph.get_production_nodes():
            return []  # No production node — not applicable, graph error reported separately

        test_types = {StageType.UNIT_TEST, StageType.INTEGRATION_TEST}
        findings: list[Finding] = []

        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types = {
                graph.graph.nodes[a].get("stage_type") for a in ancestors
            }
            test_type_values = {t.value for t in test_types}
            if not ancestor_types.intersection(test_type_values):
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="Missing test stages before production deploy",
                    evidence=(
                        f"Production stage '{prod}' has no unit_test or "
                        f"integration_test stage in its ancestor chain."
                    ),
                    why_it_matters=(
                        "Untested code reaching production increases defect rate "
                        "and can cause customer-facing outages."
                    ),
                    recommended_fix=(
                        "Add a unit_test or integration_test stage on every path "
                        "leading to production deployment."
                    ),
                    verification_criteria=(
                        "Every path to every production deploy passes through "
                        "at least one test stage (unit_test or integration_test)."
                    ),
                ))

        return findings


# ---------------------------------------------------------------------------
# R02 — Missing Security Scan
# ---------------------------------------------------------------------------

class R02MissingSecurityScan(BaseRule):
    """
    R02: Any path to production bypasses security_scan.
    Severity: Critical | Blocking: Yes
    """

    rule_id = "R02"
    category = Category.SECURITY
    severity = Severity.CRITICAL
    blocking = True

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check each production node has a security_scan ancestor."""
        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []
        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types = {graph.graph.nodes[a].get("stage_type") for a in ancestors}
            if StageType.SECURITY_SCAN.value not in ancestor_types:
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="No security scan before production deploy",
                    evidence=(
                        f"Production stage '{prod}' has no security_scan stage "
                        f"in its ancestor chain."
                    ),
                    why_it_matters=(
                        "Vulnerable code can reach production unnoticed, "
                        "exposing systems to known CVEs and security breaches."
                    ),
                    recommended_fix=(
                        "Add a security_scan stage on every path to production."
                    ),
                    verification_criteria=(
                        "Every path to every production deploy passes through "
                        "a successful security_scan."
                    ),
                ))
        return findings


# ---------------------------------------------------------------------------
# R03 — Missing Approval
# ---------------------------------------------------------------------------

class R03MissingApproval(BaseRule):
    """
    R03: Any path to production has no approval stage before deploy.
    Severity: Critical | Blocking: Yes
    """

    rule_id = "R03"
    category = Category.GOVERNANCE
    severity = Severity.CRITICAL
    blocking = True

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check each production node has an approval ancestor."""
        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []
        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types = {graph.graph.nodes[a].get("stage_type") for a in ancestors}
            if StageType.APPROVAL.value not in ancestor_types:
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="No approval gate before production deploy",
                    evidence=(
                        f"Production stage '{prod}' has no approval stage "
                        f"in its ancestor chain."
                    ),
                    why_it_matters=(
                        "Without human approval, unreviewed changes can reach "
                        "production, bypassing change management controls."
                    ),
                    recommended_fix=(
                        "Add an approval stage before every production deployment."
                    ),
                    verification_criteria=(
                        "Every path to every production deploy passes through "
                        "an approval stage."
                    ),
                ))
        return findings


# ---------------------------------------------------------------------------
# R04 — No Rollback Plan
# ---------------------------------------------------------------------------

class R04NoRollbackPlan(BaseRule):
    """
    R04: No valid rollback_plan reachable and applicable to production.
    Severity: High (Critical if blast_radius=high) | Blocking: No
    """

    rule_id = "R04"
    category = Category.RECOVERY
    severity = Severity.HIGH
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check rollback_plan exists in ancestor chain of production stages."""
        if not graph.get_production_nodes():
            return []

        blast_radius = graph.workflow.metadata.blast_radius
        effective_severity = (
            Severity.CRITICAL
            if blast_radius == BlastRadius.HIGH
            else Severity.HIGH
        )

        findings: list[Finding] = []
        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types = {graph.graph.nodes[a].get("stage_type") for a in ancestors}
            if StageType.ROLLBACK_PLAN.value not in ancestor_types:
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="No rollback plan before production deploy",
                    evidence=(
                        f"Production stage '{prod}' has no rollback_plan stage "
                        f"in its ancestor chain. blast_radius={blast_radius.value}."
                    ),
                    why_it_matters=(
                        "Without a rollback plan, failed deployments cannot be "
                        "quickly reversed, extending production downtime."
                    ),
                    recommended_fix=(
                        "Add a rollback_plan stage before every production deployment."
                    ),
                    verification_criteria=(
                        "A rollback_plan stage exists and is reachable before "
                        "every production deploy."
                    ),
                    severity=effective_severity,
                ))
        return findings


# ---------------------------------------------------------------------------
# R05 — Unowned Stage
# ---------------------------------------------------------------------------

class R05UnownedStage(BaseRule):
    """
    R05: Any stage has owner=null/blank.
    Severity: Medium (High if deploy stage) | Blocking: No
    """

    rule_id = "R05"
    category = Category.GOVERNANCE
    severity = Severity.MEDIUM
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check every stage has a non-null, non-blank owner."""
        findings: list[Finding] = []
        for stage in graph.workflow.stages:
            if not stage.owner or not stage.owner.strip():
                is_deploy = stage.type == StageType.DEPLOY_PRODUCTION
                effective_severity = Severity.HIGH if is_deploy else Severity.MEDIUM
                findings.append(self._make_finding(
                    stage_ids=[stage.id],
                    title=f"Unowned stage: '{stage.name}'",
                    evidence=(
                        f"Stage '{stage.id}' (type={stage.type.value}) "
                        f"has no owner assigned (owner={stage.owner!r})."
                    ),
                    why_it_matters=(
                        "Unowned stages have no responsible party for failures, "
                        "delays, or incidents. Deploy stages without owners are "
                        "especially dangerous."
                    ),
                    recommended_fix=(
                        f"Assign a team or individual as owner of stage '{stage.id}'."
                    ),
                    verification_criteria=(
                        f"Stage '{stage.id}' has a non-empty owner field."
                    ),
                    severity=effective_severity,
                ))
        return findings


# ---------------------------------------------------------------------------
# R06 — Invalid Stage Order
# ---------------------------------------------------------------------------

class R06InvalidStageOrder(BaseRule):
    """
    R06: Production deploy is not downstream of required tests/security,
         or approval comes after deploy.
    Severity: High | Blocking: No
    """

    rule_id = "R06"
    category = Category.DEPENDENCY
    severity = Severity.HIGH
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Verify required stages appear before production in graph order."""
        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []
        required_before_prod = [
            StageType.UNIT_TEST,
            StageType.SECURITY_SCAN,
            StageType.APPROVAL,
        ]

        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            prod_descendants = graph.reachable_from(prod)
            ancestor_types = {graph.graph.nodes[a].get("stage_type") for a in ancestors}

            # Check approval doesn't come AFTER deploy
            for desc in prod_descendants:
                desc_type = graph.graph.nodes[desc].get("stage_type")
                if desc_type == StageType.APPROVAL.value:
                    findings.append(self._make_finding(
                        stage_ids=[prod, desc],
                        title="Approval stage appears after production deploy",
                        evidence=(
                            f"Stage '{desc}' (approval) is a descendant of "
                            f"production stage '{prod}' — it runs after deployment."
                        ),
                        why_it_matters=(
                            "Approval after deployment does not prevent risky code "
                            "from reaching production."
                        ),
                        recommended_fix=(
                            "Move the approval stage to be an ancestor of the production deploy."
                        ),
                        verification_criteria=(
                            "All approval stages appear before production deploy in the DAG."
                        ),
                    ))

            # Check required types exist in ancestors
            for required in required_before_prod:
                if required.value not in ancestor_types:
                    # Already caught by R01/R02/R03 — skip duplicates
                    pass

        return findings


# ---------------------------------------------------------------------------
# R07 — Missing Monitoring
# ---------------------------------------------------------------------------

class R07MissingMonitoring(BaseRule):
    """
    R07: No monitoring_check connected after production deployment.
    Severity: Medium | Blocking: No
    """

    rule_id = "R07"
    category = Category.RECOVERY
    severity = Severity.MEDIUM
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check that monitoring_check appears after each production stage."""
        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []
        for prod in graph.get_production_nodes():
            descendants = graph.reachable_from(prod)
            desc_types = {graph.graph.nodes[d].get("stage_type") for d in descendants}
            if StageType.MONITORING_CHECK.value not in desc_types:
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="No post-deployment monitoring check",
                    evidence=(
                        f"Production stage '{prod}' has no monitoring_check "
                        f"stage in its descendant chain."
                    ),
                    why_it_matters=(
                        "Without post-deployment monitoring, production incidents "
                        "may go undetected until customers report failures."
                    ),
                    recommended_fix=(
                        "Add a monitoring_check stage immediately after every "
                        "production deployment."
                    ),
                    verification_criteria=(
                        "A monitoring_check stage is reachable from every "
                        "production deploy stage."
                    ),
                ))
        return findings


# ---------------------------------------------------------------------------
# R08 — Unverified Dependency Change
# ---------------------------------------------------------------------------

class R08UnverifiedDependencyChange(BaseRule):
    """
    R08: metadata.dependencies_changed=true but no dependency_check gate before production.
    Severity: High | Blocking: No
    """

    rule_id = "R08"
    category = Category.DEPENDENCY
    severity = Severity.HIGH
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check dependency_check exists when dependencies_changed=true."""
        if not graph.workflow.metadata.dependencies_changed:
            return []  # Not applicable

        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []
        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types = {graph.graph.nodes[a].get("stage_type") for a in ancestors}
            if StageType.DEPENDENCY_CHECK.value not in ancestor_types:
                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="Dependency changes not verified before production",
                    evidence=(
                        f"Workflow metadata declares dependencies_changed=true, "
                        f"but production stage '{prod}' has no dependency_check "
                        f"stage in its ancestor chain."
                    ),
                    why_it_matters=(
                        "Unverified dependency changes can introduce incompatible "
                        "versions, license violations, or supply-chain vulnerabilities."
                    ),
                    recommended_fix=(
                        "Add a dependency_check stage before every production "
                        "deploy when dependencies_changed=true."
                    ),
                    verification_criteria=(
                        "A dependency_check stage exists on every production path "
                        "when dependencies_changed=true."
                    ),
                ))
        return findings


# ---------------------------------------------------------------------------
# R09 — Tests Can Be Bypassed
# ---------------------------------------------------------------------------

class R09TestsBypassable(BaseRule):
    """
    R09: A test stage has continue_on_failure=true or skippable=true.
    Severity: High | Blocking: No
    """

    rule_id = "R09"
    category = Category.TESTING
    severity = Severity.HIGH
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check all test stages for bypass flags."""
        test_types = {StageType.UNIT_TEST, StageType.INTEGRATION_TEST}
        findings: list[Finding] = []

        for stage in graph.workflow.stages:
            if stage.type not in test_types:
                continue
            if stage.continue_on_failure or stage.skippable:
                flags = []
                if stage.continue_on_failure:
                    flags.append("continue_on_failure=true")
                if stage.skippable:
                    flags.append("skippable=true")
                findings.append(self._make_finding(
                    stage_ids=[stage.id],
                    title=f"Test stage '{stage.name}' can be bypassed",
                    evidence=(
                        f"Stage '{stage.id}' (type={stage.type.value}) has "
                        f"bypass flags set: {', '.join(flags)}."
                    ),
                    why_it_matters=(
                        "Test stages that can be bypassed provide no safety guarantee — "
                        "failures will be silently ignored or skipped."
                    ),
                    recommended_fix=(
                        f"Remove {' and '.join(flags)} from stage '{stage.id}'. "
                        f"Tests must block the pipeline on failure."
                    ),
                    verification_criteria=(
                        f"Stage '{stage.id}' has continue_on_failure=false "
                        f"and skippable=false."
                    ),
                ))
        return findings


# ---------------------------------------------------------------------------
# R10 — No Staging Validation
# ---------------------------------------------------------------------------

class R10NoStagingValidation(BaseRule):
    """
    R10: Both staging_deploy + staging_validation do not appear in order
         before every production path.
    Severity: Medium | Blocking: No
    """

    rule_id = "R10"
    category = Category.TESTING
    severity = Severity.MEDIUM
    blocking = False

    def evaluate(self, graph: WorkflowGraph) -> list[Finding]:
        """Check staging_deploy then staging_validation appear before each prod node."""
        if not graph.get_production_nodes():
            return []

        findings: list[Finding] = []

        for prod in graph.get_production_nodes():
            ancestors = graph.ancestors(prod)
            ancestor_types_set = {graph.graph.nodes[a].get("stage_type") for a in ancestors}

            has_staging_deploy = StageType.STAGING_DEPLOY.value in ancestor_types_set
            has_staging_validation = StageType.STAGING_VALIDATION.value in ancestor_types_set

            if not has_staging_deploy or not has_staging_validation:
                missing = []
                if not has_staging_deploy:
                    missing.append("staging_deploy")
                if not has_staging_validation:
                    missing.append("staging_validation")

                findings.append(self._make_finding(
                    stage_ids=[prod],
                    title="Missing staging validation before production deploy",
                    evidence=(
                        f"Production stage '{prod}' is missing the following "
                        f"staging stages in its ancestor chain: {', '.join(missing)}."
                    ),
                    why_it_matters=(
                        "Without staging validation, behaviour in production is "
                        "unverified — reducing confidence and increasing incident risk."
                    ),
                    recommended_fix=(
                        "Add both staging_deploy and staging_validation stages, "
                        "in that order, before every production deployment."
                    ),
                    verification_criteria=(
                        "Both staging_deploy and staging_validation stages appear "
                        "in order before every production deploy."
                    ),
                ))
            else:
                # Verify ORDER: staging_deploy must be ancestor of staging_validation
                staging_val_nodes = [
                    a for a in ancestors
                    if graph.graph.nodes[a].get("stage_type") == StageType.STAGING_VALIDATION.value
                ]
                staging_dep_nodes = [
                    a for a in ancestors
                    if graph.graph.nodes[a].get("stage_type") == StageType.STAGING_DEPLOY.value
                ]
                for sv_node in staging_val_nodes:
                    sv_ancestors = graph.ancestors(sv_node)
                    if not any(sd in sv_ancestors for sd in staging_dep_nodes):
                        findings.append(self._make_finding(
                            stage_ids=[sv_node],
                            title="Staging validation runs before staging deploy",
                            evidence=(
                                f"staging_validation stage '{sv_node}' does not "
                                f"have a staging_deploy in its ancestor chain."
                            ),
                            why_it_matters=(
                                "Validation before deployment is meaningless — "
                                "there is nothing to validate yet."
                            ),
                            recommended_fix=(
                                "Ensure staging_deploy runs before staging_validation."
                            ),
                            verification_criteria=(
                                "staging_deploy is an ancestor of staging_validation."
                            ),
                        ))

        return findings
