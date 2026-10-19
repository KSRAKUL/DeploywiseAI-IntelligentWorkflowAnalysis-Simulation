"""
Deploywise AI — Safe Git & GitHub Repository Ingestion Service.
Clones public/authorized repositories with commit SHA pinning, depth=1, timeouts, and resource limits.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_SAFE_GIT_URL = re.compile(r"^(https?://|git@)[a-zA-Z0-9_\-\./:\+]+$")
MAX_REPO_CLONE_TIMEOUT_SECONDS = 45


class GitRepoIngestor:
    """Safe Git repository ingestion with commit pinning and shallow cloning."""

    def __init__(self, timeout_seconds: int = MAX_REPO_CLONE_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds

    def clone_and_pin(
        self,
        repo_url: str,
        branch_or_tag: str | None = None,
        base_dir: str | None = None,
    ) -> tuple[Path, str, str]:
        """
        Clones a git repository into an isolated directory and resolves its commit SHA.
        Returns: (local_path, commit_sha, resolved_branch)
        """
        clean_url = repo_url.strip()
        if not _SAFE_GIT_URL.match(clean_url):
            raise ValueError(f"Invalid or unsafe Git repository URL: '{repo_url}'")

        target_dir = Path(tempfile.mkdtemp(prefix="deploywise_git_", dir=base_dir))

        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
        ]
        if branch_or_tag:
            cmd.extend(["--branch", branch_or_tag])
        cmd.extend([clean_url, str(target_dir)])

        try:
            # Run git clone with timeout
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"Git clone failed: {proc.stderr.strip() or proc.stdout.strip()}")

            # Resolve HEAD commit SHA
            sha_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            commit_sha = sha_proc.stdout.strip()

            # Resolve branch name
            branch_proc = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else "HEAD"

            return target_dir, commit_sha, branch

        except subprocess.TimeoutExpired:
            self.cleanup(target_dir)
            raise TimeoutError(f"Git clone timed out after {self.timeout_seconds}s for {clean_url}")
        except Exception:
            self.cleanup(target_dir)
            raise

    @staticmethod
    def cleanup(dir_path: Path | str) -> None:
        """Safely delete cloned workspace."""
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
