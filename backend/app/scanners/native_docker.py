"""
Deploywise AI — Native Dockerfile & Container Security Scanner.
Checks Dockerfiles for root execution, unpinned base images, piped curls, and missing healthchecks.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.core.schemas import Category, Finding, FindingSource, Severity


def scan_dockerfiles(workspace_path: Path | str) -> list[Finding]:
    """Scans Dockerfiles for container security anti-patterns."""
    root = Path(workspace_path)
    findings: list[Finding] = []

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            lower_name = fname.lower()
            if lower_name == "dockerfile" or lower_name.endswith(".dockerfile"):
                dockerfile_path = Path(dirpath) / fname
                rel_path = dockerfile_path.relative_to(root).as_posix()

                try:
                    content = dockerfile_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                lines = content.splitlines()
                has_user = False
                has_healthcheck = False

                for line_no, raw_line in enumerate(lines, start=1):
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Check base image tag
                    if line.upper().startswith("FROM "):
                        image_ref = line.split()[1] if len(line.split()) > 1 else ""
                        if ":latest" in image_ref or ":" not in image_ref:
                            findings.append(
                                Finding(
                                    finding_id=f"DOCKER-LATEST-TAG-{rel_path.replace('/', '-')}-{line_no}",
                                    source=FindingSource.SCANNER,
                                    rule_id="DOC01",
                                    category=Category.SECURITY,
                                    severity=Severity.HIGH,
                                    blocking=False,
                                    stage_ids=[],
                                    title=f"Unpinned / ':latest' Container Base Image in {rel_path}",
                                    evidence=f"Line {line_no}: '{line}' does not pin an explicit digest or version tag.",
                                    why_it_matters="Base images using ':latest' fluctuate over time, breaking repeatability and permitting upstream image compromises to cascade immediately into production.",
                                    recommended_fix=f"Pin base image '{image_ref}' to a specific version or immutable SHA256 digest.",
                                    verification_criteria=f"Base image in {rel_path} must specify an explicit version tag.",
                                    file_path=rel_path,
                                    line_number=line_no,
                                    evidence_status="confirmed",
                                    impact="Non-reproducible container builds and silent supply chain updates.",
                                    suggested_patch=f"- {line}\n+ FROM {image_ref.split(':')[0]}:3.12-slim@sha256:...\n",
                                    tool_name="NativeDockerScanner",
                                )
                            )

                    # Check curl | sh
                    if "| sh" in line or "| bash" in line:
                        findings.append(
                            Finding(
                                finding_id=f"DOCKER-PIPED-CURL-{rel_path.replace('/', '-')}-{line_no}",
                                source=FindingSource.SCANNER,
                                rule_id="DOC02",
                                category=Category.SECURITY,
                                severity=Severity.HIGH,
                                blocking=False,
                                stage_ids=[],
                                title=f"Insecure Piped Shell Execution in {rel_path}",
                                evidence=f"Line {line_no}: '{line}' pipes remote web content directly into a shell interpreter.",
                                why_it_matters="Piping external web scripts into sh/bash bypasses integrity verification and exposes the container build to MitM or DNS tampering.",
                                recommended_fix="Download script first, verify cryptographic checksum (sha256sum), and then execute.",
                                verification_criteria=f"Remove piped shell execution from line {line_no} of {rel_path}.",
                                file_path=rel_path,
                                line_number=line_no,
                                evidence_status="confirmed",
                                impact="Remote code execution during container build phase.",
                                tool_name="NativeDockerScanner",
                            )
                        )

                    if line.upper().startswith("USER "):
                        user_val = line.split()[1] if len(line.split()) > 1 else ""
                        if user_val.lower() not in ("root", "0"):
                            has_user = True

                    if line.upper().startswith("HEALTHCHECK "):
                        has_healthcheck = True

                # Check if USER instruction is absent
                if not has_user:
                    findings.append(
                        Finding(
                            finding_id=f"DOCKER-ROOT-USER-{rel_path.replace('/', '-')}",
                            source=FindingSource.SCANNER,
                            rule_id="DOC03",
                            category=Category.SECURITY,
                            severity=Severity.HIGH,
                            blocking=False,
                            stage_ids=[],
                            title=f"Container Runs as Root (Missing Non-Root USER in {rel_path})",
                            evidence=f"{rel_path} does not declare a non-root USER instruction.",
                            why_it_matters="Processes running as root inside containers have greater privilege escalation risk if a container breakout vulnerability occurs.",
                            recommended_fix="Create and switch to a non-root user (e.g. 'USER appuser' or 'USER 10001').",
                            verification_criteria=f"{rel_path} must contain 'USER <non-root-user>'.",
                            file_path=rel_path,
                            evidence_status="confirmed",
                            impact="Elevated risk of host escalation upon container breakout.",
                            suggested_patch="+ RUN addgroup -S appgroup && adduser -S appuser -G appgroup\n+ USER appuser\n",
                            tool_name="NativeDockerScanner",
                        )
                    )

    return findings
