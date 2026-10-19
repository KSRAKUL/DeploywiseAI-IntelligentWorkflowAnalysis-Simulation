"""
Deploywise AI — CI/CD Workflow & Manifest Ingestion Parser.
Converts GitHub Actions YAML, GitLab CI, and deployment manifests into normalized WorkflowGraph models.
"""
from __future__ import annotations

import re
from typing import Any
import yaml

from app.core.schemas import (
    BlastRadius,
    ChangeType,
    Environment,
    Stage,
    StageType,
    WorkflowInput,
    WorkflowMetadata,
    STAGE_ID_PATTERN,
)

_SANITIZE_RE = re.compile(r"[^a-z0-9_-]")


def _sanitize_stage_id(raw_id: str) -> str:
    """Sanitize any arbitrary string into a valid stage ID (lowercase, alphanumeric, dash/underscore, <=40 chars)."""
    cleaned = _SANITIZE_RE.sub("-", raw_id.lower().strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "stage"
    return cleaned[:40]


def parse_github_actions_yaml(content: str, workflow_name: str | None = None) -> WorkflowInput:
    """Parse a GitHub Actions workflow YAML file into a Deploywise WorkflowInput."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML format in GitHub Actions workflow: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("GitHub Actions workflow YAML must define a root object.")

    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        raise ValueError("GitHub Actions workflow does not contain any valid 'jobs' definitions.")

    wf_name = workflow_name or data.get("name") or "GitHub Actions Workflow"

    # Map raw job keys to sanitized unique IDs
    id_map: dict[str, str] = {}
    used_ids: set[str] = set()

    for raw_id in jobs.keys():
        cand = _sanitize_stage_id(raw_id)
        suffix = 1
        final_id = cand
        while final_id in used_ids:
            final_id = f"{cand[:35]}-{suffix}"
            suffix += 1
        id_map[raw_id] = final_id
        used_ids.add(final_id)

    stages: list[Stage] = []
    has_prod = False

    for raw_job_id, job_data in jobs.items():
        if not isinstance(job_data, dict):
            continue

        stage_id = id_map[raw_job_id]
        job_name = str(job_data.get("name") or raw_job_id)

        # Resolve dependencies
        raw_needs = job_data.get("needs", [])
        if isinstance(raw_needs, str):
            raw_needs = [raw_needs]
        elif not isinstance(raw_needs, list):
            raw_needs = []

        depends_on = [id_map[n] for n in raw_needs if n in id_map]

        # Inspect steps and environment to classify StageType
        env_field = str(job_data.get("environment") or "").lower()
        steps = job_data.get("steps") or []
        step_text = ""
        has_continue_on_error = bool(job_data.get("continue-on-error", False))

        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict):
                    if step.get("continue-on-error"):
                        has_continue_on_error = True
                    step_text += f" {step.get('name', '')} {step.get('uses', '')} {step.get('run', '')}".lower()

        full_context = f"{job_name.lower()} {raw_job_id.lower()} {env_field} {step_text}"

        # Classification heuristic
        stage_type = StageType.CUSTOM
        if any(w in full_context for w in ["security", "semgrep", "trivy", "snyk", "bandit", "codeql", "gitleaks", "audit"]):
            stage_type = StageType.SECURITY_SCAN
        elif any(w in full_context for w in ["secret", "credential"]):
            stage_type = StageType.SECRETS_SCAN
        elif any(w in full_context for w in ["dependency", "osv", "dependabot", "npm audit"]):
            stage_type = StageType.DEPENDENCY_CHECK
        elif any(w in full_context for w in ["approval", "gate", "promote", "manual"]):
            stage_type = StageType.APPROVAL
        elif any(w in full_context for w in ["rollback", "revert"]):
            stage_type = StageType.ROLLBACK_PLAN
        elif any(w in full_context for w in ["monitor", "health", "ping", "smoke"]):
            stage_type = StageType.MONITORING_CHECK
        elif any(w in full_context for w in ["unit_test", "pytest", "unit", "jest"]):
            stage_type = StageType.UNIT_TEST
        elif any(w in full_context for w in ["integration", "e2e", "cypress", "playwright"]):
            stage_type = StageType.INTEGRATION_TEST
        elif any(w in full_context for w in ["staging"]):
            stage_type = StageType.STAGING_DEPLOY
        elif any(w in full_context for w in ["deploy", "release", "prod", "publish"]):
            stage_type = StageType.DEPLOY_PRODUCTION
            has_prod = True
        elif any(w in full_context for w in ["build", "compile", "package", "docker"]):
            stage_type = StageType.BUILD

        stages.append(
            Stage(
                id=stage_id,
                name=job_name[:200],
                type=stage_type,
                owner="devops" if stage_type in (StageType.DEPLOY_PRODUCTION, StageType.APPROVAL) else None,
                depends_on=depends_on,
                continue_on_failure=has_continue_on_error,
                skippable=has_continue_on_error,
            )
        )

    if not stages:
        raise ValueError("Could not extract any stages from GitHub Actions workflow.")

    return WorkflowInput(
        name=wf_name[:200],
        schema_version="1.0",
        environment=Environment.PRODUCTION if has_prod else Environment.DEVELOPMENT,
        change_type=ChangeType.STANDARD,
        stages=stages,
        metadata=WorkflowMetadata(
            blast_radius=BlastRadius.HIGH if has_prod else BlastRadius.MEDIUM,
            dependencies_changed=False,
        ),
    )


def parse_gitlab_ci_yaml(content: str, workflow_name: str | None = None) -> WorkflowInput:
    """Parse a GitLab CI YAML file into a Deploywise WorkflowInput."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid GitLab CI YAML format: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("GitLab CI YAML must define a root dictionary.")

    wf_name = workflow_name or "GitLab CI Workflow"
    job_entries = {k: v for k, v in data.items() if isinstance(v, dict) and not k.startswith(".")}

    if not job_entries:
        raise ValueError("No jobs found in GitLab CI configuration.")

    id_map: dict[str, str] = {}
    used_ids: set[str] = set()
    for raw_id in job_entries.keys():
        cand = _sanitize_stage_id(raw_id)
        suffix = 1
        final_id = cand
        while final_id in used_ids:
            final_id = f"{cand[:35]}-{suffix}"
            suffix += 1
        id_map[raw_id] = final_id
        used_ids.add(final_id)

    stages: list[Stage] = []
    has_prod = False

    for raw_id, job_data in job_entries.items():
        stage_id = id_map[raw_id]
        stage_category = str(job_data.get("stage", "custom")).lower()
        script = " ".join(job_data.get("script", [])) if isinstance(job_data.get("script"), list) else str(job_data.get("script", ""))
        full_text = f"{raw_id} {stage_category} {script}".lower()

        stage_type = StageType.CUSTOM
        if "test" in full_text:
            stage_type = StageType.UNIT_TEST
        elif any(w in full_text for w in ["security", "semgrep", "snyk", "trivy"]):
            stage_type = StageType.SECURITY_SCAN
        elif "deploy" in full_text or "production" in full_text:
            stage_type = StageType.DEPLOY_PRODUCTION
            has_prod = True
        elif "build" in full_text:
            stage_type = StageType.BUILD

        needs = job_data.get("needs", [])
        dep_ids: list[str] = []
        if isinstance(needs, list):
            for n in needs:
                target = n.get("job") if isinstance(n, dict) else n
                if target in id_map:
                    dep_ids.append(id_map[target])

        stages.append(
            Stage(
                id=stage_id,
                name=raw_id[:200],
                type=stage_type,
                depends_on=dep_ids,
                continue_on_failure=bool(job_data.get("allow_failure", False)),
                skippable=bool(job_data.get("allow_failure", False)),
            )
        )

    return WorkflowInput(
        name=wf_name[:200],
        schema_version="1.0",
        environment=Environment.PRODUCTION if has_prod else Environment.DEVELOPMENT,
        change_type=ChangeType.STANDARD,
        stages=stages,
        metadata=WorkflowMetadata(
            blast_radius=BlastRadius.HIGH if has_prod else BlastRadius.MEDIUM,
            dependencies_changed=False,
        ),
    )


def parse_cicd_content(content: str, filename_hint: str = "workflow.yml") -> WorkflowInput:
    """Auto-detect format and parse into Deploywise WorkflowInput."""
    lower_hint = filename_hint.lower()
    if lower_hint.endswith(".json"):
        import json
        data = json.loads(content)
        return WorkflowInput.model_validate(data)

    if ".gitlab-ci" in lower_hint:
        return parse_gitlab_ci_yaml(content)

    return parse_github_actions_yaml(content)
