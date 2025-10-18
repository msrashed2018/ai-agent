"""Unit tests for ArchiveMetadata domain entity."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.domain.entities.archive_metadata import ArchiveMetadata
from app.domain.enums import ArchiveStatus


class TestArchiveMetadataEntity:
    """Test cases for ArchiveMetadata entity."""

    def test_archive_metadata_creation_pending(self):
        """Test archive metadata initialization with PENDING status."""
        archive_id = uuid4()
        session_id = uuid4()
        created_at = datetime.utcnow()
        
        metadata = {"files_count": 15, "original_size": 1024000}

        archive_metadata = ArchiveMetadata(
            id=archive_id,
            session_id=session_id,
            archive_path="/archives/session_123.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=512000,
            status=ArchiveStatus.PENDING,
            created_at=created_at,
            archive_metadata=metadata,
        )

        assert archive_metadata.id == archive_id
        assert archive_metadata.session_id == session_id
        assert archive_metadata.archive_path == "/archives/session_123.zip"
        assert archive_metadata.storage_backend == "s3"
        assert archive_metadata.compression_type == "zip"
        assert archive_metadata.size_bytes == 512000
        assert archive_metadata.status == ArchiveStatus.PENDING
        assert archive_metadata.created_at == created_at
        assert archive_metadata.completed_at is None
        assert archive_metadata.error_message is None
        assert archive_metadata.archive_metadata == metadata

    def test_archive_metadata_creation_completed(self):
        """Test archive metadata initialization with COMPLETED status."""
        created_at = datetime.utcnow()
        completed_at = created_at + timedelta(minutes=5)

        archive_metadata = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/local/archives/session_456.tar.gz",
            storage_backend="filesystem",
            compression_type="tar.gz",
            size_bytes=2048000,
            status=ArchiveStatus.COMPLETED,
            created_at=created_at,
            completed_at=completed_at,
        )

        assert archive_metadata.status == ArchiveStatus.COMPLETED
        assert archive_metadata.completed_at == completed_at

    def test_archive_metadata_creation_failed(self):
        """Test archive metadata initialization with FAILED status."""
        archive_metadata = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/tmp/failed_archive.zip",
            storage_backend="local",
            compression_type="zip",
            size_bytes=0,
            status=ArchiveStatus.FAILED,
            created_at=datetime.utcnow(),
            error_message="Compression failed: insufficient disk space",
        )

        assert archive_metadata.status == ArchiveStatus.FAILED
        assert archive_metadata.error_message == "Compression failed: insufficient disk space"

    def test_archive_metadata_validation_negative_size(self):
        """Test validation fails for negative size."""
        with pytest.raises(ValueError, match="Archive size cannot be negative"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="/test/archive.zip",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=-100,
                status=ArchiveStatus.PENDING,
                created_at=datetime.utcnow(),
            )

    def test_archive_metadata_validation_empty_path(self):
        """Test validation fails for empty archive path."""
        with pytest.raises(ValueError, match="Archive path cannot be empty"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="   ",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=1000,
                status=ArchiveStatus.PENDING,
                created_at=datetime.utcnow(),
            )

    def test_archive_metadata_validation_empty_storage_backend(self):
        """Test validation fails for empty storage backend."""
        with pytest.raises(ValueError, match="Storage backend cannot be empty"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="/test/archive.zip",
                storage_backend="",
                compression_type="zip",
                size_bytes=1000,
                status=ArchiveStatus.PENDING,
                created_at=datetime.utcnow(),
            )

    def test_archive_metadata_validation_empty_compression_type(self):
        """Test validation fails for empty compression type."""
        with pytest.raises(ValueError, match="Compression type cannot be empty"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="/test/archive.zip",
                storage_backend="s3",
                compression_type="   ",
                size_bytes=1000,
                status=ArchiveStatus.PENDING,
                created_at=datetime.utcnow(),
            )

    def test_archive_metadata_validation_completed_without_timestamp(self):
        """Test validation fails for completed status without completed_at."""
        with pytest.raises(ValueError, match="Completed archive must have completed_at timestamp"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="/test/archive.zip",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=1000,
                status=ArchiveStatus.COMPLETED,
                created_at=datetime.utcnow(),
                completed_at=None,
            )

    def test_archive_metadata_validation_failed_without_error(self):
        """Test validation fails for failed status without error message."""
        with pytest.raises(ValueError, match="Failed archive must have error message"):
            ArchiveMetadata(
                id=uuid4(),
                session_id=uuid4(),
                archive_path="/test/archive.zip",
                storage_backend="s3",
                compression_type="zip",
                size_bytes=1000,
                status=ArchiveStatus.FAILED,
                created_at=datetime.utcnow(),
                error_message=None,
            )

    def test_status_check_methods(self):
        """Test all status check methods."""
        pending_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/pending.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        in_progress_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/progress.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.IN_PROGRESS,
            created_at=datetime.utcnow(),
        )

        completed_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/completed.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.COMPLETED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        failed_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/failed.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.FAILED,
            created_at=datetime.utcnow(),
            error_message="Test error",
        )

        # Test individual status checks
        assert pending_archive.is_pending() is True
        assert pending_archive.is_in_progress() is False
        assert pending_archive.is_completed() is False
        assert pending_archive.is_failed() is False

        assert in_progress_archive.is_pending() is False
        assert in_progress_archive.is_in_progress() is True
        assert in_progress_archive.is_completed() is False
        assert in_progress_archive.is_failed() is False

        assert completed_archive.is_pending() is False
        assert completed_archive.is_in_progress() is False
        assert completed_archive.is_completed() is True
        assert completed_archive.is_failed() is False

        assert failed_archive.is_pending() is False
        assert failed_archive.is_in_progress() is False
        assert failed_archive.is_completed() is False
        assert failed_archive.is_failed() is True

    def test_terminal_and_active_status_methods(self):
        """Test terminal and active status methods."""
        pending_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/pending.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        completed_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/completed.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.COMPLETED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        failed_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/failed.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.FAILED,
            created_at=datetime.utcnow(),
            error_message="Test error",
        )

        assert pending_archive.is_terminal_status() is False
        assert pending_archive.is_active_status() is True

        assert completed_archive.is_terminal_status() is True
        assert completed_archive.is_active_status() is False

        assert failed_archive.is_terminal_status() is True
        assert failed_archive.is_active_status() is False

    def test_size_conversion_methods(self):
        """Test size conversion methods."""
        # 2.5 MB archive
        archive_metadata = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/archive.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=2621440,  # 2.5 * 1024 * 1024
            status=ArchiveStatus.COMPLETED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        assert archive_metadata.get_size_kb() == 2560.0
        assert archive_metadata.get_size_mb() == 2.5
        assert abs(archive_metadata.get_size_gb() - 0.00244140625) < 0.0001

    def test_human_readable_size(self):
        """Test human readable size formatting."""
        # Test bytes
        small_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="local", compression_type="zip", size_bytes=512,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        assert small_archive.get_human_readable_size() == "512 B"

        # Test KB
        kb_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="local", compression_type="zip", size_bytes=5120,  # 5 KB
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        assert kb_archive.get_human_readable_size() == "5.0 KB"

        # Test MB
        mb_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="local", compression_type="zip", size_bytes=5242880,  # 5 MB
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        assert mb_archive.get_human_readable_size() == "5.0 MB"

        # Test GB
        gb_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="local", compression_type="zip", size_bytes=5368709120,  # 5 GB
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        assert gb_archive.get_human_readable_size() == "5.0 GB"

    def test_duration_calculation(self):
        """Test duration calculation methods."""
        created_at = datetime.utcnow()
        completed_at = created_at + timedelta(minutes=3, seconds=30)  # 3.5 minutes

        completed_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/archive.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.COMPLETED,
            created_at=created_at,
            completed_at=completed_at,
        )

        pending_archive = ArchiveMetadata(
            id=uuid4(),
            session_id=uuid4(),
            archive_path="/test/pending.zip",
            storage_backend="s3",
            compression_type="zip",
            size_bytes=1000,
            status=ArchiveStatus.PENDING,
            created_at=created_at,
        )

        assert completed_archive.get_duration_seconds() == 210.0  # 3.5 * 60
        assert completed_archive.get_duration_minutes() == 3.5

        assert pending_archive.get_duration_seconds() is None
        assert pending_archive.get_duration_minutes() is None

    def test_storage_type_methods(self):
        """Test storage type identification methods."""
        cloud_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        gcs_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="gcs", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        local_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="filesystem", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        disk_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="local", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert cloud_archive.is_cloud_storage() is True
        assert cloud_archive.is_local_storage() is False

        assert gcs_archive.is_cloud_storage() is True
        assert gcs_archive.is_local_storage() is False

        assert local_archive.is_cloud_storage() is False
        assert local_archive.is_local_storage() is True

        assert disk_archive.is_cloud_storage() is False
        assert disk_archive.is_local_storage() is True

    def test_compression_methods(self):
        """Test compression-related methods."""
        compressed_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        uncompressed_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.tar",
            storage_backend="s3", compression_type="none", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert compressed_archive.is_compressed() is True
        assert uncompressed_archive.is_compressed() is False

    def test_file_extension_methods(self):
        """Test file extension determination."""
        zip_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        tar_gz_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test",
            storage_backend="s3", compression_type="tar.gz", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        no_compression_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test",
            storage_backend="s3", compression_type="none", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        custom_archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test",
            storage_backend="s3", compression_type="custom", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        assert zip_archive.get_file_extension() == ".zip"
        assert tar_gz_archive.get_file_extension() == ".tar.gz"
        assert no_compression_archive.get_file_extension() == ""
        assert custom_archive.get_file_extension() == ".custom"

    def test_has_metadata_method(self):
        """Test has_metadata method."""
        with_metadata = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(), archive_metadata={"files": 10}
        )

        with_empty_metadata = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(), archive_metadata={}
        )

        without_metadata = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(), archive_metadata=None
        )

        assert with_metadata.has_metadata() is True
        assert with_empty_metadata.has_metadata() is False
        assert without_metadata.has_metadata() is False

    def test_archive_metadata_immutability(self):
        """Test that ArchiveMetadata is immutable (frozen dataclass)."""
        archive = ArchiveMetadata(
            id=uuid4(), session_id=uuid4(), archive_path="/test.zip",
            storage_backend="s3", compression_type="zip", size_bytes=1000,
            status=ArchiveStatus.COMPLETED, created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            archive.status = ArchiveStatus.FAILED

        with pytest.raises(AttributeError):
            archive.size_bytes = 2000