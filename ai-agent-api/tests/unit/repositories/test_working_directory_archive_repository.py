"""Unit tests for WorkingDirectoryArchiveRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.working_directory_archive_repository import WorkingDirectoryArchiveRepository
from app.models.working_directory_archive import WorkingDirectoryArchiveModel


class TestWorkingDirectoryArchiveRepository:
    """Test cases for WorkingDirectoryArchiveRepository."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repository(self, mock_db):
        """Working directory archive repository instance."""
        return WorkingDirectoryArchiveRepository(mock_db)

    @pytest.fixture
    def sample_archive(self):
        """Sample working directory archive model."""
        return WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/archives/session_123.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1024000,
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    async def test_repository_inheritance(self, repository):
        """Test that repository inherits from BaseRepository."""
        from app.repositories.base import BaseRepository
        assert isinstance(repository, BaseRepository)

    async def test_get_by_session(self, repository, mock_db, sample_archive):
        """Test getting archive by session ID (one-to-one relationship)."""
        session_id = sample_archive.session_id
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_archive
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert result == sample_archive
        assert result.session_id == session_id
        mock_db.execute.assert_called_once()

    async def test_get_by_session_not_found(self, repository, mock_db):
        """Test getting archive by session ID when not found."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert result is None
        mock_db.execute.assert_called_once()

    async def test_get_by_status_completed(self, repository, mock_db, sample_archive):
        """Test getting archives by completed status."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_status("completed")

        assert len(result) == 1
        assert result[0] == sample_archive
        assert result[0].status == "completed"
        mock_db.execute.assert_called_once()

    async def test_get_by_status_pending(self, repository, mock_db):
        """Test getting archives by pending status."""
        pending_archive = WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/archives/pending.zip",
            storage_backend="filesystem",
            compression_type="zip",
            size_bytes=512000,
            status="pending",
            created_at=datetime.utcnow(),
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pending_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_status("pending")

        assert len(result) == 1
        assert result[0] == pending_archive
        assert result[0].status == "pending"
        mock_db.execute.assert_called_once()

    async def test_get_by_status_with_pagination(self, repository, mock_db):
        """Test getting archives by status with pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_status("in_progress", skip=10, limit=5)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_by_storage_backend_s3(self, repository, mock_db, sample_archive):
        """Test getting archives by S3 storage backend."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_storage_backend("s3")

        assert len(result) == 1
        assert result[0] == sample_archive
        assert result[0].storage_backend == "s3"
        mock_db.execute.assert_called_once()

    async def test_get_by_storage_backend_filesystem(self, repository, mock_db):
        """Test getting archives by filesystem storage backend."""
        filesystem_archive = WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/local/archives/session_456.tar.gz",
            storage_backend="filesystem",
            compression_type="tar.gz",
            size_bytes=2048000,
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [filesystem_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_storage_backend("filesystem")

        assert len(result) == 1
        assert result[0] == filesystem_archive
        assert result[0].storage_backend == "filesystem"
        assert result[0].compression_type == "tar.gz"
        mock_db.execute.assert_called_once()

    async def test_get_by_storage_backend_with_pagination(self, repository, mock_db):
        """Test getting archives by storage backend with pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_storage_backend("gcs", skip=5, limit=20)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_pending_archives(self, repository, mock_db):
        """Test getting pending archives for processing."""
        pending_archives = [
            WorkingDirectoryArchiveModel(
                id=uuid4(),
                session_id=uuid4(),
                archive_path=f"/archives/pending_{i}.zip",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=1000000 + i * 100000,
                status="pending",
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = pending_archives
        mock_db.execute.return_value = mock_result

        result = await repository.get_pending_archives()

        assert len(result) == 3
        for archive in result:
            assert archive.status == "pending"
        mock_db.execute.assert_called_once()

    async def test_get_pending_archives_with_limit(self, repository, mock_db):
        """Test getting pending archives with custom limit."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_pending_archives(limit=50)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_failed_archives(self, repository, mock_db):
        """Test getting failed archives."""
        failed_archive = WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/archives/failed.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=0,  # Failed archives might have 0 size
            status="failed",
            created_at=datetime.utcnow(),
            error_message="Compression failed: insufficient disk space",
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [failed_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_failed_archives()

        assert len(result) == 1
        assert result[0] == failed_archive
        assert result[0].status == "failed"
        assert result[0].error_message == "Compression failed: insufficient disk space"
        mock_db.execute.assert_called_once()

    async def test_get_failed_archives_with_pagination(self, repository, mock_db):
        """Test getting failed archives with pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_failed_archives(skip=10, limit=25)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_multiple_archives_different_statuses(self, repository, mock_db):
        """Test getting archives with different statuses."""
        archives = [
            WorkingDirectoryArchiveModel(
                id=uuid4(),
                session_id=uuid4(),
                archive_path=f"/archives/archive_{i}.zip",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=1000000 + i * 100000,
                status=status,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if status == "completed" else None,
                error_message="Test error" if status == "failed" else None,
            )
            for i, status in enumerate(["pending", "in_progress", "completed", "failed"])
        ]
        
        # Test get_by_status for each status
        for status in ["pending", "in_progress", "completed", "failed"]:
            expected_archives = [a for a in archives if a.status == status]
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = expected_archives
            mock_db.execute.return_value = mock_result

            result = await repository.get_by_status(status)

            assert len(result) == 1
            assert result[0].status == status

    async def test_empty_results(self, repository, mock_db):
        """Test all methods with empty results."""
        session_id = uuid4()
        
        # Mock for scalar_one_or_none (get_by_session)
        mock_result_single = MagicMock()
        mock_result_single.scalar_one_or_none.return_value = None
        
        # Mock for scalars().all() (list methods)
        mock_result_list = MagicMock()
        mock_result_list.scalars.return_value.all.return_value = []

        # Test get_by_session returns None
        mock_db.execute.return_value = mock_result_single
        session_result = await repository.get_by_session(session_id)
        assert session_result is None

        # Test all list methods return empty lists
        mock_db.execute.return_value = mock_result_list
        
        status_result = await repository.get_by_status("nonexistent_status")
        assert len(status_result) == 0

        backend_result = await repository.get_by_storage_backend("nonexistent_backend")
        assert len(backend_result) == 0

        pending_result = await repository.get_pending_archives()
        assert len(pending_result) == 0

        failed_result = await repository.get_failed_archives()
        assert len(failed_result) == 0

    async def test_archive_with_metadata(self, repository, mock_db):
        """Test archive with additional metadata."""
        archive_with_metadata = WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/archives/complex.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=5242880,  # 5 MB
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            archive_metadata={
                "files_count": 150,
                "original_size": 10485760,  # 10 MB
                "compression_ratio": 0.5,
                "processing_time_seconds": 30,
            }
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = archive_with_metadata
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(archive_with_metadata.session_id)

        assert result == archive_with_metadata
        assert result.archive_metadata is not None
        assert result.archive_metadata["files_count"] == 150
        assert result.archive_metadata["compression_ratio"] == 0.5

    async def test_repository_model_type(self, repository):
        """Test that repository has correct model type."""
        assert repository.model == WorkingDirectoryArchiveModel

    async def test_repository_db_session(self, repository, mock_db):
        """Test that repository stores database session."""
        assert repository.db == mock_db

    async def test_large_archives_filtering(self, repository, mock_db):
        """Test handling of large archives."""
        large_archive = WorkingDirectoryArchiveModel(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/archives/large_project.tar.gz",
            storage_backend="s3",
            compression_type="tar.gz",
            size_bytes=1073741824,  # 1 GB
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            archive_metadata={
                "files_count": 50000,
                "original_size": 5368709120,  # 5 GB
                "compression_ratio": 0.2,
            }
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [large_archive]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_storage_backend("s3")

        assert len(result) == 1
        assert result[0].size_bytes == 1073741824
        assert result[0].archive_metadata["files_count"] == 50000