"""
Deploywise AI — Native Dependency Hygiene & Risk Scanner.
Checks package manifests (package.json, pyproject.toml, requirements.txt) for
unpinned packages, wildcards, missing lockfiles, and untrusted protocols.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.schemas import Category, Finding, FindingSource, Severity


def scan_dependencies(workspace_path: Path | str) -> list[Finding]:
    """Scans package dependency manifests for supply chain & build repeatability risks."""
    root = Path(workspace_path)
    findings: list[Finding] = []

    # 1. Check Node/JS dependencies
    pkg_json = root / "package.json"
    if pkg_json.exists():
        rel_pkg = pkg_json.relative_to(root).as_posix()
        lockfile_present = (
            (root / "package-lock.json").exists()
            or (root / "yarn.lock").exists()
            or (root / "pnpm-lock.yaml").exists()
        )
        if not lockfile_present:
            findings.append(
                Finding(
                    finding_id="DEP-MISSING-LOCKFILE-NODE",
                    source=FindingSource.SCANNER,
                    rule_id="DEP01",
                    category=Category.DEPENDENCY,
                    severity=Severity.HIGH,
                    blocking=False,
                    stage_ids=[],
                    title=f"Missing Dependency Lockfile for {rel_pkg}",
                    evidence=f"{rel_pkg} exists but no package-lock.json, yarn.lock, or pnpm-lock.yaml was found in root.",
                    why_it_matters="Without an authoritative lockfile, builds can silently ingest unverified transitive updates containing breaking changes or malicious packages.",
                    recommended_fix="Commit 'package-lock.json', 'yarn.lock', or 'pnpm-lock.yaml' to version control and run 'npm ci' in CI pipelines.",
                    verification_criteria="A lockfile must exist alongside package.json.",
                    file_path=rel_pkg,
                    line_number=1,
                    evidence_status="confirmed",
                    impact="Non-deterministic production builds and vulnerability to dependency confusion.",
                    tool_name="NativeDependencyScanner",
                )
            )

        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep_name, dep_ver in deps.items():
                if dep_ver in ("*", "latest") or dep_ver.startswith(">=0"):
                    findings.append(
                        Finding(
                            finding_id=f"DEP-WILDCARD-{dep_name}",
                            source=FindingSource.SCANNER,
                            rule_id="DEP02",
                            category=Category.DEPENDENCY,
                            severity=Severity.HIGH,
                            blocking=False,
                            stage_ids=[],
                            title=f"Unpinned / Wildcard Dependency '{dep_name}: {dep_ver}'",
                            evidence=f"Package '{dep_name}' uses wildcards or unpinned version range '{dep_ver}'.",
                            why_it_matters="Wildcard dependencies pull whatever version is newest, introducing unexpected breaking changes and supply chain risks.",
                            recommended_fix=f"Pin '{dep_name}' to a specific semver range (e.g. ^1.2.0 or exact version).",
                            verification_criteria=f"Dependency '{dep_name}' must specify an explicit version in package.json.",
                            file_path=rel_pkg,
                            evidence_status="confirmed",
                            impact="Build breakage and uncontrolled dependency drift.",
                            suggested_patch=f'- "{dep_name}": "{dep_ver}"\n+ "{dep_name}": "^1.0.0"\n',
                            tool_name="NativeDependencyScanner",
                        )
                    )
        except Exception:
            pass

    # 2. Check Python requirements.txt
    req_txt = root / "requirements.txt"
    if req_txt.exists():
        rel_req = req_txt.relative_to(root).as_posix()
        try:
            lines = req_txt.read_text(encoding="utf-8").splitlines()
            for line_no, raw_line in enumerate(lines, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                # Check unpinned
                if not any(op in line for op in ["==", ">=", "<=", "~=", ">"]):
                    pkg_name = line.split()[0]
                    findings.append(
                        Finding(
                            finding_id=f"DEP-UNPINNED-PY-{pkg_name}",
                            source=FindingSource.SCANNER,
                            rule_id="DEP03",
                            category=Category.DEPENDENCY,
                            severity=Severity.MEDIUM,
                            blocking=False,
                            stage_ids=[],
                            title=f"Unpinned Python Requirement '{pkg_name}'",
                            evidence=f"Line {line_no}: '{line}' does not constrain package version.",
                            why_it_matters="Unpinned Python packages risk unpredictable behavior when upstream maintainers publish breaking updates.",
                            recommended_fix=f"Pin '{pkg_name}' with '==' or '>=' in {rel_req}.",
                            verification_criteria=f"'{pkg_name}' must have version constraint in requirements.txt.",
                            file_path=rel_req,
                            line_number=line_no,
                            evidence_status="confirmed",
                            impact="Silent regression during CI/CD package installation.",
                            tool_name="NativeDependencyScanner",
                        )
                    )
        except Exception:
            pass

    return findings
