"""
Deploywise AI — Safe ZIP Archive Extraction Service.
Enforces Zip-Slip protection, archive bomb size caps, file count limits, and symlink defenses.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

MAX_UNCOMPRESSED_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_ARCHIVE_FILE_COUNT = 5000


class SafeZipExtractor:
    """Safely extracts ZIP archives into isolated workspaces without security vulnerabilities."""

    def __init__(
        self,
        max_size_bytes: int = MAX_UNCOMPRESSED_SIZE_BYTES,
        max_files: int = MAX_ARCHIVE_FILE_COUNT,
    ) -> None:
        self.max_size_bytes = max_size_bytes
        self.max_files = max_files

    def extract(self, zip_path_or_bytes: str | Path | bytes, base_dir: str | None = None) -> Path:
        """
        Safely unpack a ZIP file into an isolated temporary directory.
        Raises ValueError on path traversal attempts or resource limits.
        """
        target_dir = Path(tempfile.mkdtemp(prefix="deploywise_zip_", dir=base_dir))
        target_resolved = target_dir.resolve()

        try:
            if isinstance(zip_path_or_bytes, bytes):
                import io
                zfile = zipfile.ZipFile(io.BytesIO(zip_path_or_bytes))
            else:
                zfile = zipfile.ZipFile(zip_path_or_bytes)

            with zfile:
                infolist = zfile.infolist()
                if len(infolist) > self.max_files:
                    raise ValueError(
                        f"Archive exceeds maximum file limit of {self.max_files} (contains {len(infolist)} entries)."
                    )

                total_uncompressed = 0
                for info in infolist:
                    total_uncompressed += info.file_size
                    if total_uncompressed > self.max_size_bytes:
                        raise ValueError(
                            f"Archive exceeds uncompressed size limit of {self.max_size_bytes / (1024*1024):.0f} MB."
                        )

                    # Normalize destination path
                    dest_path = (target_resolved / info.filename).resolve()

                    # Zip-Slip check: must be strictly inside target_resolved
                    if not str(dest_path).startswith(str(target_resolved)):
                        raise ValueError(f"Illegal path traversal detected in archive: {info.filename}")

                    # Reject symlinks targeting outside
                    is_symlink = (info.external_attr >> 16) & 0o120000 == 0o120000
                    if is_symlink:
                        # Skip or disallow symlinks
                        continue

                    # Safe extract
                    if info.is_dir():
                        dest_path.mkdir(parents=True, exist_ok=True)
                    else:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        with zfile.open(info) as src, open(dest_path, "wb") as dst:
                            shutil.copyfileobj(src, dst)

            return target_resolved
        except Exception:
            # Clean up on failure
            if target_resolved.exists():
                shutil.rmtree(target_resolved, ignore_errors=True)
            raise

    @staticmethod
    def cleanup(dir_path: Path | str) -> None:
        """Safely delete an extracted workspace."""
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
