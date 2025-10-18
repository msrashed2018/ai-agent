"""Storage manager for working directories and file operations."""
import os
import shutil
import tarfile
from pathlib import Path
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.core.config import settings


class StorageManager:
    """Manages working directories and file storage for sessions."""

    def __init__(self):
        self.base_workdir = Path(settings.agent_workdir_base)
        self.archive_dir = Path(settings.agent_workdir_archive)
        self.reports_dir = Path(settings.reports_dir)

    async def create_working_directory(self, session_id: UUID) -> Path:
        """Create a working directory for a session."""
        workdir = self.base_workdir / str(session_id)
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    async def get_working_directory(self, session_id: UUID) -> Optional[Path]:
        """Get the working directory path for a session."""
        workdir = self.base_workdir / str(session_id)
        if workdir.exists():
            return workdir
        return None

    async def delete_working_directory(self, session_id: UUID) -> bool:
        """Delete a session's working directory."""
        workdir = self.base_workdir / str(session_id)
        if workdir.exists():
            shutil.rmtree(workdir)
            return True
        return False

    async def archive_working_directory(self, session_id: UUID) -> Optional[Path]:
        """Archive a session's working directory to tar.gz."""
        workdir = self.base_workdir / str(session_id)
        if not workdir.exists():
            return None

        # Create archive directory if it doesn't exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Create tar.gz archive
        archive_name = f"{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        archive_path = self.archive_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(workdir, arcname=str(session_id))

        # Delete original directory
        shutil.rmtree(workdir)

        return archive_path

    async def get_directory_size(self, session_id: UUID) -> int:
        """Get total size of working directory in bytes."""
        workdir = self.base_workdir / str(session_id)
        if not workdir.exists():
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(workdir):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                total_size += filepath.stat().st_size

        return total_size

    async def get_file_count(self, session_id: UUID) -> int:
        """Get total number of files in working directory."""
        workdir = self.base_workdir / str(session_id)
        if not workdir.exists():
            return 0

        file_count = 0
        for dirpath, dirnames, filenames in os.walk(workdir):
            file_count += len(filenames)

        return file_count

    async def get_file_manifest(self, session_id: UUID) -> list:
        """Get list of all files in working directory with metadata."""
        workdir = self.base_workdir / str(session_id)
        if not workdir.exists():
            return []

        manifest = []
        for dirpath, dirnames, filenames in os.walk(workdir):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                relative_path = filepath.relative_to(workdir)
                stat = filepath.stat()

                manifest.append({
                    "path": str(relative_path),
                    "size": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

        return manifest

    async def save_report(
        self,
        report_id: UUID,
        content: str,
        format: str = "html",
    ) -> Path:
        """Save a report file to disk."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        extension_map = {
            "html": ".html",
            "markdown": ".md",
            "json": ".json",
            "pdf": ".pdf",
        }

        extension = extension_map.get(format, ".txt")
        filename = f"{report_id}{extension}"
        filepath = self.reports_dir / filename

        # Write content to file
        if format == "pdf":
            # For PDF, content should be bytes
            with open(filepath, "wb") as f:
                f.write(content)
        else:
            # For text formats
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return filepath

    async def get_report_path(self, report_id: UUID) -> Optional[Path]:
        """Get the path to a report file."""
        # Check all possible extensions
        for ext in [".html", ".md", ".json", ".pdf"]:
            filepath = self.reports_dir / f"{report_id}{ext}"
            if filepath.exists():
                return filepath
        return None

    async def delete_report(self, report_id: UUID) -> bool:
        """Delete a report file."""
        filepath = await self.get_report_path(report_id)
        if filepath and filepath.exists():
            filepath.unlink()
            return True
        return False

    async def get_total_storage_usage(self, user_id: Optional[UUID] = None) -> int:
        """Get total storage usage in bytes, optionally for a specific user."""
        # This is a simplified implementation
        # In production, you'd query the database to filter by user
        total_size = 0

        # Working directories
        if self.base_workdir.exists():
            for workdir in self.base_workdir.iterdir():
                if workdir.is_dir():
                    for dirpath, dirnames, filenames in os.walk(workdir):
                        for filename in filenames:
                            filepath = Path(dirpath) / filename
                            total_size += filepath.stat().st_size

        # Reports
        if self.reports_dir.exists():
            for filepath in self.reports_dir.iterdir():
                if filepath.is_file():
                    total_size += filepath.stat().st_size

        return total_size

    async def cleanup_old_archives(self, days: int = 180) -> int:
        """Delete archives older than specified days. Returns count of deleted archives."""
        if not self.archive_dir.exists():
            return 0

        cutoff_time = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for archive_file in self.archive_dir.glob("*.tar.gz"):
            if archive_file.stat().st_mtime < cutoff_time:
                archive_file.unlink()
                deleted_count += 1

        return deleted_count
