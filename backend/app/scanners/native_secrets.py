"""
Deploywise AI — Native Secret & Credential Detection Scanner.
Scans source files for leaked API keys, tokens, private keys, and credentials without external dependencies.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from app.core.schemas import Category, Finding, FindingSource, Severity

SECRET_PATTERNS: list[tuple[str, str, re.Pattern, Severity]] = [
    (
        "SEC-01-AWS",
        "AWS Access Key ID Detected",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        Severity.CRITICAL,
    ),
    (
        "SEC-02-GH",
        "GitHub Personal Access / OAuth Token Detected",
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b"),
        Severity.CRITICAL,
    ),
    (
        "SEC-03-KEY",
        "Unencrypted Private Key Block Detected",
        re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----"),
        Severity.CRITICAL,
    ),
    (
        "SEC-04-SLACK",
        "Slack Webhook URL Detected",
        re.compile(r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+"),
        Severity.HIGH,
    ),
    (
        "SEC-05-PWD",
        "Hardcoded Password or Secret Assignment",
        re.compile(
            r"""(?i)(?:password|secret|api_key|access_token|auth_token)\s*[:=]\s*["']([^"'\s]{8,})["']"""
        ),
        Severity.HIGH,
    ),
]

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "dist",
    "build",
}

IGNORE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".woff",
    ".woff2",
    ".sqlite",
    ".db",
}


def _redact(val: str) -> str:
    """Mask confidential tokens for safe evidence display."""
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"


def scan_for_secrets(workspace_path: Path | str) -> list[Finding]:
    """Scans workspace files for leaked secrets and credentials."""
    root = Path(workspace_path)
    findings: list[Finding] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in IGNORE_EXTS:
                continue

            # Don't scan .env.example
            if fname.lower().endswith(".example"):
                continue

            file_path = Path(dirpath) / fname
            rel_path = file_path.relative_to(root).as_posix()

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            for line_no, line in enumerate(lines, start=1):
                # Ignore comment-only example values
                if "placeholder" in line.lower() or "your_" in line.lower() or "example" in line.lower():
                    continue

                for rule_code, title, pattern, severity in SECRET_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        matched_str = match.group(0)
                        redacted = _redact(matched_str)
                        findings.append(
                            Finding(
                                finding_id=f"SECRET-{rel_path.replace('/', '-')}-{line_no}",
                                source=FindingSource.SCANNER,
                                rule_id="SEC01",
                                category=Category.SECURITY,
                                severity=severity,
                                blocking=True,
                                stage_ids=[],
                                title=f"{title} in {rel_path}",
                                evidence=f"Line {line_no}: Match found ({redacted})",
                                why_it_matters="Committed secrets can be harvested by attackers to breach production environments or compromise cloud resources.",
                                recommended_fix="Revoke the exposed credential immediately and replace with an environment secret manager (e.g. GitHub Secrets, AWS Secrets Manager).",
                                verification_criteria=f"Ensure no matches for credential pattern exist in {rel_path} on line {line_no}.",
                                file_path=rel_path,
                                line_number=line_no,
                                evidence_status="confirmed",
                                impact="Full credential compromise and potential unauthorized access.",
                                suggested_patch=f"- {line.strip()}\n+ # Loaded securely from environment\n",
                                tool_name="NativeSecretScanner",
                            )
                        )
    return findings
