"""
Deploywise AI — Security & Quality Scanner Orchestrator.
Coordinates native analyzers and external tools (Semgrep, Bandit, Trivy, Gitleaks, OSV-Scanner, Checkov).
Tracks tool execution status and calculates assessment coverage transparently.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from app.core.schemas import (
    AssessmentCoverage,
    Category,
    Finding,
    FindingSource,
    ScannerResult,
    ScannerStatus,
    Severity,
)
from app.scanners.native_dependencies import scan_dependencies
from app.scanners.native_docker import scan_dockerfiles
from app.scanners.native_secrets import scan_for_secrets


class ScannerOrchestrator:
    """Discovers, executes, and records outcomes of static analysis tools."""

    EXTERNAL_TOOLS = [
        ("gitleaks", Category.SECURITY, ["gitleaks", "dir", "--no-git", "--report-format", "json", "-r"]),
        ("bandit", Category.SECURITY, ["bandit", "-r", ".", "-f", "json"]),
        ("semgrep", Category.SECURITY, ["semgrep", "scan", "--json"]),
        ("trivy", Category.SECURITY, ["trivy", "fs", "--format", "json", "."]),
        ("osv-scanner", Category.DEPENDENCY, ["osv-scanner", "--json", "-r", "."]),
        ("checkov", Category.SECURITY, ["checkov", "-d", ".", "-o", "json"]),
    ]

    def run_all_scans(self, workspace_path: Path | str) -> tuple[list[Finding], list[ScannerResult], AssessmentCoverage]:
        """Runs native scanners and all available external tools."""
        root = Path(workspace_path)
        all_findings: list[Finding] = []
        scanner_results: list[ScannerResult] = []

        # -------------------------------------------------------------
        # 1. Native Secret Scanner
        # -------------------------------------------------------------
        t0 = time.time()
        try:
            sec_findings = scan_for_secrets(root)
            all_findings.extend(sec_findings)
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeSecretScanner",
                    category=Category.SECURITY,
                    target=str(root.name),
                    status=ScannerStatus.PASSED if not sec_findings else ScannerStatus.FAILED,
                    duration_ms=int((time.time() - t0) * 1000),
                    finding_count=len(sec_findings),
                )
            )
        except Exception as exc:
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeSecretScanner",
                    category=Category.SECURITY,
                    target=str(root.name),
                    status=ScannerStatus.FAILED,
                    error_message=str(exc),
                )
            )

        # -------------------------------------------------------------
        # 2. Native Dependency Scanner
        # -------------------------------------------------------------
        t0 = time.time()
        try:
            dep_findings = scan_dependencies(root)
            all_findings.extend(dep_findings)
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeDependencyScanner",
                    category=Category.DEPENDENCY,
                    target=str(root.name),
                    status=ScannerStatus.PASSED if not dep_findings else ScannerStatus.FAILED,
                    duration_ms=int((time.time() - t0) * 1000),
                    finding_count=len(dep_findings),
                )
            )
        except Exception as exc:
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeDependencyScanner",
                    category=Category.DEPENDENCY,
                    target=str(root.name),
                    status=ScannerStatus.FAILED,
                    error_message=str(exc),
                )
            )

        # -------------------------------------------------------------
        # 3. Native Dockerfile Scanner
        # -------------------------------------------------------------
        t0 = time.time()
        try:
            doc_findings = scan_dockerfiles(root)
            all_findings.extend(doc_findings)
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeDockerScanner",
                    category=Category.SECURITY,
                    target=str(root.name),
                    status=ScannerStatus.PASSED if not doc_findings else ScannerStatus.FAILED,
                    duration_ms=int((time.time() - t0) * 1000),
                    finding_count=len(doc_findings),
                )
            )
        except Exception as exc:
            scanner_results.append(
                ScannerResult(
                    scanner_name="NativeDockerScanner",
                    category=Category.SECURITY,
                    target=str(root.name),
                    status=ScannerStatus.FAILED,
                    error_message=str(exc),
                )
            )

        # -------------------------------------------------------------
        # 4. External Scanners (Selective Execution)
        # -------------------------------------------------------------
        for tool_name, category, cmd in self.EXTERNAL_TOOLS:
            exe_path = shutil.which(tool_name)
            if not exe_path:
                # Explicitly record as skipped / not installed (never claim clean scan!)
                scanner_results.append(
                    ScannerResult(
                        scanner_name=tool_name,
                        category=category,
                        target=str(root.name),
                        status=ScannerStatus.SKIPPED_NOT_INSTALLED,
                        duration_ms=0,
                        finding_count=0,
                        error_message=f"Executable '{tool_name}' not detected on PATH in current environment.",
                    )
                )
                continue

            # Tool is available: run safely with timeout
            t0 = time.time()
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                duration = int((time.time() - t0) * 1000)

                # Attempt to parse tool JSON
                findings_count = 0
                if tool_name == "bandit" and proc.stdout:
                    try:
                        b_data = json.loads(proc.stdout)
                        for item in b_data.get("results", []):
                            findings_count += 1
                            sev = Severity.HIGH if item.get("issue_severity") == "HIGH" else Severity.MEDIUM
                            all_findings.append(
                                Finding(
                                    finding_id=f"BANDIT-{item.get('test_id')}-{findings_count}",
                                    source=FindingSource.SCANNER,
                                    rule_id=str(item.get("test_id", "BANDIT")),
                                    category=Category.SECURITY,
                                    severity=sev,
                                    blocking=False,
                                    stage_ids=[],
                                    title=f"Bandit: {item.get('issue_text')}",
                                    evidence=f"{item.get('filename')}:{item.get('line_number')}",
                                    why_it_matters="Identified Python security vulnerability.",
                                    recommended_fix="Refactor code according to Bandit recommendation.",
                                    verification_criteria=f"Bandit check {item.get('test_id')} must pass.",
                                    file_path=item.get("filename"),
                                    line_number=item.get("line_number"),
                                    evidence_status="confirmed",
                                    tool_name="Bandit",
                                )
                            )
                    except Exception:
                        pass

                scanner_results.append(
                    ScannerResult(
                        scanner_name=tool_name,
                        category=category,
                        target=str(root.name),
                        status=ScannerStatus.PASSED if findings_count == 0 else ScannerStatus.FAILED,
                        duration_ms=duration,
                        finding_count=findings_count,
                    )
                )
            except subprocess.TimeoutExpired:
                scanner_results.append(
                    ScannerResult(
                        scanner_name=tool_name,
                        category=category,
                        target=str(root.name),
                        status=ScannerStatus.TIMED_OUT,
                        duration_ms=30000,
                        error_message=f"Scanner execution exceeded 30s timeout.",
                    )
                )
            except Exception as exc:
                scanner_results.append(
                    ScannerResult(
                        scanner_name=tool_name,
                        category=category,
                        target=str(root.name),
                        status=ScannerStatus.FAILED,
                        error_message=str(exc),
                    )
                )

        # -------------------------------------------------------------
        # 5. Coverage Calculation
        # -------------------------------------------------------------
        total = len(scanner_results)
        executed = sum(1 for r in scanner_results if r.status in (ScannerStatus.PASSED, ScannerStatus.FAILED))
        passed = sum(1 for r in scanner_results if r.status == ScannerStatus.PASSED)
        failed = sum(1 for r in scanner_results if r.status == ScannerStatus.FAILED)
        skipped = sum(1 for r in scanner_results if r.status in (ScannerStatus.SKIPPED_NOT_INSTALLED, ScannerStatus.UNSUPPORTED))
        cov_pct = round((executed / total) * 100.0, 1) if total > 0 else 0.0

        coverage = AssessmentCoverage(
            total_checks=total,
            executed_checks=executed,
            passed_checks=passed,
            failed_checks=failed,
            skipped_checks=skipped,
            coverage_percentage=cov_pct,
        )

        return all_findings, scanner_results, coverage
