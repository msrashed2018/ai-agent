"""Archive metadata domain entity."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.domain.enums import ArchiveStatus


@dataclass(frozen=True)
class ArchiveMetadata:
    """Immutable archive metadata entity.

    Represents metadata for a working directory archive stored in S3
    or file storage.
    """
    id: UUID
    session_id: UUID
    archive_path: str
    storage_backend: str  # e.g., 's3', 'filesystem'
    compression_type: str  # e.g., 'zip', 'tar.gz'
    size_bytes: int
    status: ArchiveStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    archive_metadata: Optional[dict] = None

    def __post_init__(self) -> None:
        """Validate the archive metadata."""
        if self.size_bytes < 0:
            raise ValueError("Archive size cannot be negative")
        if not self.archive_path.strip():
            raise ValueError("Archive path cannot be empty")
        if not self.storage_backend.strip():
            raise ValueError("Storage backend cannot be empty")
        if not self.compression_type.strip():
            raise ValueError("Compression type cannot be empty")
        
        # Validate status transitions
        if self.status == ArchiveStatus.COMPLETED and self.completed_at is None:
            raise ValueError("Completed archive must have completed_at timestamp")
        if self.status == ArchiveStatus.FAILED and not self.error_message:
            raise ValueError("Failed archive must have error message")

    def is_completed(self) -> bool:
        """Check if archive was successfully completed."""
        return self.status == ArchiveStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if archive failed."""
        return self.status == ArchiveStatus.FAILED

    def is_pending(self) -> bool:
        """Check if archive is pending."""
        return self.status == ArchiveStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if archive is in progress."""
        return self.status == ArchiveStatus.IN_PROGRESS

    def is_terminal_status(self) -> bool:
        """Check if archive is in a terminal status (completed or failed)."""
        return self.status in [ArchiveStatus.COMPLETED, ArchiveStatus.FAILED]

    def is_active_status(self) -> bool:
        """Check if archive is actively being processed."""
        return self.status in [ArchiveStatus.PENDING, ArchiveStatus.IN_PROGRESS]

    def get_size_mb(self) -> float:
        """Get archive size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    def get_size_gb(self) -> float:
        """Get archive size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    def get_size_kb(self) -> float:
        """Get archive size in kilobytes."""
        return self.size_bytes / 1024

    def get_human_readable_size(self) -> str:
        """Get human-readable size string."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.get_size_kb():.1f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.get_size_mb():.1f} MB"
        else:
            return f"{self.get_size_gb():.1f} GB"

    def get_duration_seconds(self) -> Optional[float]:
        """Get archive processing duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.created_at).total_seconds()

    def get_duration_minutes(self) -> Optional[float]:
        """Get archive processing duration in minutes."""
        duration_seconds = self.get_duration_seconds()
        return duration_seconds / 60.0 if duration_seconds is not None else None

    def is_cloud_storage(self) -> bool:
        """Check if archive uses cloud storage."""
        cloud_backends = ['s3', 'gcs', 'azure', 'cloudflare']
        return self.storage_backend.lower() in cloud_backends

    def is_local_storage(self) -> bool:
        """Check if archive uses local filesystem storage."""
        return self.storage_backend.lower() in ['filesystem', 'local', 'disk']

    def is_compressed(self) -> bool:
        """Check if archive uses compression."""
        return self.compression_type.lower() != 'none'

    def get_file_extension(self) -> str:
        """Get expected file extension based on compression type."""
        extension_map = {
            'zip': '.zip',
            'tar': '.tar',
            'tar.gz': '.tar.gz',
            'tar.bz2': '.tar.bz2',
            'gzip': '.gz',
            'none': '',
        }
        return extension_map.get(self.compression_type.lower(), f'.{self.compression_type}')

    def has_metadata(self) -> bool:
        """Check if archive has additional metadata."""
        return self.archive_metadata is not None and bool(self.archive_metadata)
