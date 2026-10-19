"""
Deploywise AI — Project Structure & Technology Discovery Engine.
Inspects an ingested repository or directory to detect languages, frameworks,
package managers, Dockerfiles, and CI/CD workflow configurations.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.core.schemas import (
    BlastRadius,
    ChangeType,
    Environment,
    ProjectStructure,
    Stage,
    StageType,
    WorkflowInput,
    WorkflowMetadata,
)
from app.ingestion.cicd_parser import parse_cicd_content


class ProjectDiscoveryEngine:
    """Discovers project structure, technologies, and workflow files in a workspace."""

    EXT_LANG_MAP = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".go": "Go",
        ".java": "Java",
        ".rs": "Rust",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".sh": "Shell",
        ".tf": "Terraform",
    }

    IGNORE_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        "dist",
        "build",
        ".next",
        "target",
        ".idea",
        ".vscode",
    }

    def inspect_workspace(self, workspace_path: Path | str, commit_sha: str | None = None, branch: str | None = None) -> tuple[ProjectStructure, WorkflowInput | None]:
        """
        Inspects the workspace directory.
        Returns a ProjectStructure and the primary detected WorkflowInput (if found or synthesizable).
        """
        root = Path(workspace_path)
        if not root.exists():
            raise FileNotFoundError(f"Workspace path does not exist: {workspace_path}")

        lang_counts: dict[str, int] = {}
        package_managers: set[str] = set()
        frameworks: set[str] = set()
        ci_workflows: list[str] = []
        dockerfiles: list[str] = []
        all_inspected_files: list[str] = []

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories
            dirnames[:] = [d for d in dirnames if d not in self.IGNORE_DIRS]

            for fname in filenames:
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root).replace("\\", "/")
                all_inspected_files.append(rel_path)

                lower_name = fname.lower()
                ext = os.path.splitext(fname)[1].lower()

                # Language detection
                if ext in self.EXT_LANG_MAP:
                    lang = self.EXT_LANG_MAP[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1

                # Package manager & framework detection
                if lower_name == "package.json":
                    package_managers.add("npm/yarn/pnpm")
                elif lower_name in ("package-lock.json",):
                    package_managers.add("npm")
                elif lower_name in ("yarn.lock",):
                    package_managers.add("yarn")
                elif lower_name in ("pnpm-lock.yaml",):
                    package_managers.add("pnpm")
                elif lower_name in ("pyproject.toml",):
                    package_managers.add("pip/poetry/hatch")
                elif lower_name in ("requirements.txt",):
                    package_managers.add("pip")
                elif lower_name in ("pipfile", "pipfile.lock"):
                    package_managers.add("pipenv")
                elif lower_name in ("go.mod",):
                    package_managers.add("go modules")
                elif lower_name in ("pom.xml",):
                    package_managers.add("maven")
                elif lower_name in ("build.gradle", "build.gradle.kts"):
                    package_managers.add("gradle")
                elif lower_name in ("cargo.toml",):
                    package_managers.add("cargo")

                # Docker & IaC
                if lower_name.startswith("dockerfile") or lower_name.endswith(".dockerfile"):
                    dockerfiles.append(rel_path)
                elif lower_name in ("docker-compose.yml", "docker-compose.yaml"):
                    frameworks.add("Docker Compose")

                # CI/CD Workflows
                if (
                    rel_path.startswith(".github/workflows/")
                    and lower_name.endswith((".yml", ".yaml"))
                ) or lower_name in (".gitlab-ci.yml", "jenkinsfile", "azure-pipelines.yml"):
                    ci_workflows.append(rel_path)

        sorted_languages = [
            lang for lang, _ in sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)
        ]

        structure = ProjectStructure(
            languages=sorted_languages[:5],
            frameworks=sorted(list(frameworks)),
            package_managers=sorted(list(package_managers)),
            ci_workflows=ci_workflows,
            dockerfiles=dockerfiles,
            total_files=len(all_inspected_files),
            inspected_files=all_inspected_files[:100],  # Cap sample
            commit_sha=commit_sha,
            branch=branch,
        )

        # Parse primary CI/CD workflow if available
        workflow_input: WorkflowInput | None = None
        if ci_workflows:
            primary_wf_rel = ci_workflows[0]
            primary_path = root / primary_wf_rel
            try:
                content = primary_path.read_text(encoding="utf-8", errors="replace")
                workflow_input = parse_cicd_content(content, filename_hint=primary_wf_rel)
            except Exception:
                workflow_input = None

        # Fallback: if no CI/CD workflow exists in the repository, generate a synthetic baseline
        # workflow reflecting what a project with these detected languages needs
        if workflow_input is None:
            workflow_input = self._generate_baseline_workflow(structure, root.name)

        return structure, workflow_input

    def _generate_baseline_workflow(self, structure: ProjectStructure, project_name: str) -> WorkflowInput:
        """Synthesizes a minimal pipeline reflecting the discovered repository assets."""
        stages: list[Stage] = []

        stages.append(
            Stage(
                id="build",
                name=f"Build & Compile ({structure.languages[0] if structure.languages else 'Application'})",
                type=StageType.BUILD,
                owner="engineering",
                depends_on=[],
            )
        )

        stages.append(
            Stage(
                id="unit-tests",
                name="Automated Unit Tests",
                type=StageType.UNIT_TEST,
                owner="engineering",
                depends_on=["build"],
            )
        )

        stages.append(
            Stage(
                id="deploy-prod",
                name="Production Deployment",
                type=StageType.DEPLOY_PRODUCTION,
                owner="devops",
                depends_on=["unit-tests"],
            )
        )

        return WorkflowInput(
            name=f"{project_name} Delivery Pipeline",
            schema_version="1.0",
            environment=Environment.PRODUCTION,
            change_type=ChangeType.STANDARD,
            stages=stages,
            metadata=WorkflowMetadata(
                blast_radius=BlastRadius.HIGH,
                dependencies_changed=bool(structure.package_managers),
            ),
        )
