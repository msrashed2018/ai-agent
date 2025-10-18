"""Storage archiver for archiving working directories to S3 or filesystem."""
import logging
import tarfile
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.working_directory_archive_repository import WorkingDirectoryArchiveRepository
from app.models.working_directory_archive import WorkingDirectoryArchiveModel
from app.domain.entities.archive_metadata import ArchiveStatus

logger = logging.getLogger(__name__)


class StorageArchiver:
    """Archive working directories to S3 or local filesystem storage.

    Compresses working directories into tar.gz archives and uploads to
    configured storage backend (S3 or local filesystem).
    """

    def __init__(
        self,
        db: AsyncSession,
        archive_repo: WorkingDirectoryArchiveRepository,
        storage_provider: str = "local",
        s3_bucket: Optional[str] = None,
        s3_region: Optional[str] = None,
        local_archive_path: Optional[str] = None
    ):
        """Initialize storage archiver.

        Args:
            db: Database session
            archive_repo: Archive repository
            storage_provider: "s3" or "local"
            s3_bucket: S3 bucket name (required if provider=s3)
            s3_region: S3 region (required if provider=s3)
            local_archive_path: Local storage path (required if provider=local)
        """
        self.db = db
        self.archive_repo = archive_repo
        self.storage_provider = storage_provider
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region
        self.local_archive_path = local_archive_path

        # Initialize S3 client if needed
        if storage_provider == "s3":
            if not s3_bucket or not s3_region:
                raise ValueError("S3 bucket and region required for S3 storage")

            try:
                import boto3
                self.s3_client = boto3.client("s3", region_name=s3_region)
            except ImportError:
                raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")

        elif storage_provider == "local":
            if not local_archive_path:
                local_archive_path = "/tmp/archives"

            self.local_archive_path = Path(local_archive_path)
            self.local_archive_path.mkdir(parents=True, exist_ok=True)

        else:
            raise ValueError(f"Unknown storage provider: {storage_provider}")

        logger.info(f"StorageArchiver initialized with provider: {storage_provider}")

    async def archive_working_directory(
        self,
        session_id: UUID,
        working_dir: Path
    ) -> WorkingDirectoryArchiveModel:
        """Archive a working directory to storage.

        Args:
            session_id: Session ID
            working_dir: Path to working directory

        Returns:
            Archive metadata model

        Raises:
            ValueError: If working directory doesn't exist
            Exception: If archival fails
        """
        if not working_dir.exists():
            raise ValueError(f"Working directory does not exist: {working_dir}")

        archive_id = uuid4()

        try:
            # Create initial archive record
            archive = WorkingDirectoryArchiveModel(
                id=archive_id,
                session_id=session_id,
                archive_path="",  # Will be updated
                size_bytes=0,  # Will be updated
                compression="gzip",
                manifest={},  # Will be updated
                status=ArchiveStatus.PENDING.value,
                error_message=None,
                archived_at=None
            )

            created_archive = await self.archive_repo.create(archive)

            # Create compressed archive
            archive_file_path = await self._create_archive(working_dir, archive_id)

            # Generate manifest
            manifest = await self._generate_manifest(working_dir)

            # Upload to storage
            storage_path = await self._upload_archive(archive_file_path, archive_id, session_id)

            # Get file size
            size_bytes = archive_file_path.stat().st_size

            # Update archive record
            await self.archive_repo.update(
                archive_id,
                archive_path=storage_path,
                size_bytes=size_bytes,
                manifest=manifest,
                status=ArchiveStatus.COMPLETED.value,
                archived_at=datetime.utcnow()
            )

            # Clean up temporary file
            try:
                archive_file_path.unlink()
            except Exception:
                pass

            logger.info(
                f"Archived working directory: {storage_path} ({size_bytes} bytes)",
                extra={"session_id": str(session_id), "archive_id": str(archive_id)}
            )

            # Get updated archive
            updated_archive = await self.archive_repo.get_by_id(archive_id)
            return updated_archive

        except Exception as e:
            logger.error(
                f"Failed to archive working directory: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )

            # Update archive record with error
            try:
                await self.archive_repo.update(
                    archive_id,
                    status=ArchiveStatus.FAILED.value,
                    error_message=f"{type(e).__name__}: {str(e)}"
                )
            except Exception:
                pass

            raise

    async def _create_archive(
        self,
        source_dir: Path,
        archive_id: UUID
    ) -> Path:
        """Create compressed tar.gz archive.

        Args:
            source_dir: Source directory to archive
            archive_id: Archive ID

        Returns:
            Path to created archive file
        """
        # Create archive in temp directory
        temp_dir = Path(tempfile.gettempdir())
        archive_path = temp_dir / f"{archive_id}.tar.gz"

        logger.debug(f"Creating archive: {archive_path}")

        # Run tar compression in thread pool (blocking operation)
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._create_tar_gz,
            source_dir,
            archive_path
        )

        return archive_path

    def _create_tar_gz(self, source_dir: Path, archive_path: Path) -> None:
        """Create tar.gz archive (blocking operation).

        Args:
            source_dir: Source directory
            archive_path: Destination archive path
        """
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)

    async def _generate_manifest(self, source_dir: Path) -> Dict[str, Any]:
        """Generate manifest of archived files.

        Args:
            source_dir: Source directory

        Returns:
            Manifest dictionary with file list and metadata
        """
        files = []
        total_size = 0

        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_dir)
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime

                files.append({
                    "path": str(relative_path),
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_mtime).isoformat()
                })

                total_size += file_size

        return {
            "files": files,
            "file_count": len(files),
            "total_size": total_size,
            "created_at": datetime.utcnow().isoformat()
        }

    async def _upload_archive(
        self,
        archive_path: Path,
        archive_id: UUID,
        session_id: UUID
    ) -> str:
        """Upload archive to storage backend.

        Args:
            archive_path: Path to archive file
            archive_id: Archive ID
            session_id: Session ID

        Returns:
            Storage path/URI
        """
        if self.storage_provider == "s3":
            return await self._upload_to_s3(archive_path, archive_id, session_id)
        elif self.storage_provider == "local":
            return await self._upload_to_local(archive_path, archive_id, session_id)
        else:
            raise ValueError(f"Unknown storage provider: {self.storage_provider}")

    async def _upload_to_s3(
        self,
        archive_path: Path,
        archive_id: UUID,
        session_id: UUID
    ) -> str:
        """Upload archive to S3.

        Args:
            archive_path: Local archive path
            archive_id: Archive ID
            session_id: Session ID

        Returns:
            S3 URI
        """
        s3_key = f"archives/{session_id}/{archive_id}.tar.gz"

        # Upload in thread pool (blocking operation)
        await asyncio.get_event_loop().run_in_executor(
            None,
            self.s3_client.upload_file,
            str(archive_path),
            self.s3_bucket,
            s3_key
        )

        s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
        logger.info(f"Uploaded to S3: {s3_uri}")

        return s3_uri

    async def _upload_to_local(
        self,
        archive_path: Path,
        archive_id: UUID,
        session_id: UUID
    ) -> str:
        """Copy archive to local storage.

        Args:
            archive_path: Source archive path
            archive_id: Archive ID
            session_id: Session ID

        Returns:
            Local file path
        """
        # Create session directory
        session_dir = self.local_archive_path / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Copy to local storage
        dest_path = session_dir / f"{archive_id}.tar.gz"

        await asyncio.get_event_loop().run_in_executor(
            None,
            archive_path.rename,
            dest_path
        )

        logger.info(f"Copied to local storage: {dest_path}")

        return str(dest_path)

    async def retrieve_archive(
        self,
        archive_id: UUID,
        extract_to: Path
    ) -> Path:
        """Retrieve and extract an archive.

        Args:
            archive_id: Archive ID
            extract_to: Path to extract archive to

        Returns:
            Path to extracted directory
        """
        # Get archive metadata
        archive = await self.archive_repo.get_by_id(archive_id)
        if not archive:
            raise ValueError(f"Archive not found: {archive_id}")

        if archive.status != ArchiveStatus.COMPLETED.value:
            raise ValueError(f"Archive not completed: {archive.status}")

        # Download archive
        temp_archive = await self._download_archive(archive.archive_path, archive_id)

        # Extract archive
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._extract_tar_gz,
            temp_archive,
            extract_to
        )

        # Clean up temp file
        try:
            temp_archive.unlink()
        except Exception:
            pass

        logger.info(f"Extracted archive to: {extract_to}")

        return extract_to

    async def _download_archive(self, storage_path: str, archive_id: UUID) -> Path:
        """Download archive from storage.

        Args:
            storage_path: Storage path/URI
            archive_id: Archive ID

        Returns:
            Path to downloaded file
        """
        temp_path = Path(tempfile.gettempdir()) / f"{archive_id}_retrieved.tar.gz"

        if storage_path.startswith("s3://"):
            # Download from S3
            s3_bucket, s3_key = storage_path.replace("s3://", "").split("/", 1)

            await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.download_file,
                s3_bucket,
                s3_key,
                str(temp_path)
            )
        else:
            # Copy from local storage
            source_path = Path(storage_path)
            await asyncio.get_event_loop().run_in_executor(
                None,
                source_path.rename,
                temp_path
            )

        return temp_path

    def _extract_tar_gz(self, archive_path: Path, extract_to: Path) -> None:
        """Extract tar.gz archive (blocking operation).

        Args:
            archive_path: Archive file path
            extract_to: Destination path
        """
        extract_to.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_to)
