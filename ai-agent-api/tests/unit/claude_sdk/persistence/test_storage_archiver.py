"""Unit tests for StorageArchiver."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

from app.claude_sdk.persistence.storage_archiver import StorageArchiver
from app.domain.entities.archive_metadata import ArchiveStatus


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_archive_repo():
    """Create mock archive repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def temp_working_dir(tmp_path):
    """Create temporary working directory with files."""
    working_dir = tmp_path / "working_dir"
    working_dir.mkdir()

    # Create some test files
    (working_dir / "file1.txt").write_text("Content 1")
    (working_dir / "file2.txt").write_text("Content 2")

    subdir = working_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Content 3")

    return working_dir


class TestStorageArchiverInitialization:
    """Tests for StorageArchiver initialization."""

    def test_initialization_local_storage(self, mock_db_session, mock_archive_repo):
        """Test initialization with local storage."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path="/tmp/archives"
        )

        assert archiver.storage_provider == "local"
        assert archiver.local_archive_path == Path("/tmp/archives")

    def test_initialization_creates_local_directory(self, mock_db_session, mock_archive_repo, tmp_path):
        """Test initialization creates local archive directory."""
        archive_path = tmp_path / "archives"

        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(archive_path)
        )

        assert archive_path.exists()
        assert archive_path.is_dir()

    def test_initialization_s3_requires_bucket_and_region(self, mock_db_session, mock_archive_repo):
        """Test S3 initialization requires bucket and region."""
        with pytest.raises(ValueError, match="S3 bucket and region required"):
            StorageArchiver(
                db=mock_db_session,
                archive_repo=mock_archive_repo,
                storage_provider="s3"
            )

    @patch('app.claude_sdk.persistence.storage_archiver.boto3')
    def test_initialization_s3_creates_client(self, mock_boto3, mock_db_session, mock_archive_repo):
        """Test S3 initialization creates boto3 client."""
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="s3",
            s3_bucket="test-bucket",
            s3_region="us-east-1"
        )

        mock_boto3.client.assert_called_once_with("s3", region_name="us-east-1")
        assert archiver.s3_client == mock_s3_client

    def test_initialization_unknown_provider_raises_error(self, mock_db_session, mock_archive_repo):
        """Test unknown storage provider raises error."""
        with pytest.raises(ValueError, match="Unknown storage provider"):
            StorageArchiver(
                db=mock_db_session,
                archive_repo=mock_archive_repo,
                storage_provider="azure"
            )


class TestArchiveWorkingDirectory:
    """Tests for archiving working directories."""

    @pytest.mark.asyncio
    async def test_archive_nonexistent_directory_raises_error(self, mock_db_session, mock_archive_repo):
        """Test archiving nonexistent directory raises error."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path="/tmp/archives"
        )

        with pytest.raises(ValueError, match="does not exist"):
            await archiver.archive_working_directory(
                session_id=uuid4(),
                working_dir=Path("/nonexistent/path")
            )

    @pytest.mark.asyncio
    async def test_archive_creates_initial_pending_record(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test archive creates initial pending record."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path="/tmp/archives"
        )

        session_id = uuid4()

        # Mock repo to return the created archive
        mock_archive_repo.create.return_value = MagicMock(id=uuid4())
        mock_archive_repo.get_by_id.return_value = MagicMock(
            archive_path="/tmp/test.tar.gz",
            status=ArchiveStatus.COMPLETED.value
        )

        await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=temp_working_dir
        )

        # Should create pending record
        create_call = mock_archive_repo.create.call_args[0][0]
        assert create_call.session_id == session_id
        assert create_call.status == ArchiveStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_archive_updates_to_completed_on_success(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test archive updates status to completed on success."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(temp_working_dir.parent / "archives")
        )

        session_id = uuid4()
        archive_id = uuid4()

        # Mock repo
        mock_archive_repo.create.return_value = MagicMock(id=archive_id)
        mock_archive_repo.get_by_id.return_value = MagicMock(
            id=archive_id,
            archive_path="test.tar.gz",
            status=ArchiveStatus.COMPLETED.value
        )

        await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=temp_working_dir
        )

        # Should update to completed
        update_call = mock_archive_repo.update.call_args
        assert update_call[0][0] == archive_id
        assert update_call[1]["status"] == ArchiveStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_archive_includes_manifest(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test archive includes file manifest."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(temp_working_dir.parent / "archives")
        )

        session_id = uuid4()
        archive_id = uuid4()

        mock_archive_repo.create.return_value = MagicMock(id=archive_id)
        mock_archive_repo.get_by_id.return_value = MagicMock(
            archive_path="test.tar.gz",
            status=ArchiveStatus.COMPLETED.value
        )

        await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=temp_working_dir
        )

        # Should include manifest
        update_call = mock_archive_repo.update.call_args
        manifest = update_call[1]["manifest"]

        assert "files" in manifest
        assert "file_count" in manifest
        assert "total_size" in manifest
        assert manifest["file_count"] == 3  # 3 files created in fixture

    @pytest.mark.asyncio
    async def test_archive_calculates_size(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test archive calculates and stores size."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(temp_working_dir.parent / "archives")
        )

        session_id = uuid4()
        archive_id = uuid4()

        mock_archive_repo.create.return_value = MagicMock(id=archive_id)
        mock_archive_repo.get_by_id.return_value = MagicMock(
            archive_path="test.tar.gz",
            status=ArchiveStatus.COMPLETED.value
        )

        await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=temp_working_dir
        )

        # Should include size
        update_call = mock_archive_repo.update.call_args
        size_bytes = update_call[1]["size_bytes"]

        assert size_bytes > 0

    @pytest.mark.asyncio
    async def test_archive_failure_updates_status_to_failed(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test archive failure updates status to failed."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(temp_working_dir.parent / "archives")
        )

        session_id = uuid4()
        archive_id = uuid4()

        # Make create succeed but get_by_id fail
        mock_archive_repo.create.return_value = MagicMock(id=archive_id)
        mock_archive_repo.get_by_id.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await archiver.archive_working_directory(
                session_id=session_id,
                working_dir=temp_working_dir
            )

        # Should update to failed
        update_calls = [call for call in mock_archive_repo.update.call_args_list
                       if call[1].get("status") == ArchiveStatus.FAILED.value]

        assert len(update_calls) > 0

    @pytest.mark.asyncio
    async def test_archive_local_storage(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir,
        tmp_path
    ):
        """Test archiving to local storage."""
        archive_path = tmp_path / "archives"

        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local",
            local_archive_path=str(archive_path)
        )

        session_id = uuid4()
        archive_id = uuid4()

        mock_archive_repo.create.return_value = MagicMock(id=archive_id)
        mock_archive_repo.get_by_id.return_value = MagicMock(
            id=archive_id,
            archive_path=str(archive_path / str(session_id) / f"{archive_id}.tar.gz"),
            status=ArchiveStatus.COMPLETED.value
        )

        result = await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=temp_working_dir
        )

        # Should store locally
        update_call = mock_archive_repo.update.call_args
        stored_path = update_call[1]["archive_path"]

        assert str(archive_path) in stored_path
        assert str(session_id) in stored_path


class TestGenerateManifest:
    """Tests for manifest generation."""

    @pytest.mark.asyncio
    async def test_generate_manifest_lists_all_files(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test manifest lists all files."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        manifest = await archiver._generate_manifest(temp_working_dir)

        assert len(manifest["files"]) == 3
        assert manifest["file_count"] == 3

    @pytest.mark.asyncio
    async def test_generate_manifest_includes_file_details(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test manifest includes file details."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        manifest = await archiver._generate_manifest(temp_working_dir)

        for file_info in manifest["files"]:
            assert "path" in file_info
            assert "size" in file_info
            assert "modified" in file_info

    @pytest.mark.asyncio
    async def test_generate_manifest_calculates_total_size(
        self,
        mock_db_session,
        mock_archive_repo,
        temp_working_dir
    ):
        """Test manifest calculates total size."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        manifest = await archiver._generate_manifest(temp_working_dir)

        # Total size should be sum of all files
        expected_size = sum(f["size"] for f in manifest["files"])
        assert manifest["total_size"] == expected_size

    @pytest.mark.asyncio
    async def test_generate_manifest_empty_directory(
        self,
        mock_db_session,
        mock_archive_repo,
        tmp_path
    ):
        """Test manifest for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        manifest = await archiver._generate_manifest(empty_dir)

        assert manifest["file_count"] == 0
        assert manifest["total_size"] == 0
        assert manifest["files"] == []


class TestRetrieveArchive:
    """Tests for retrieving archives."""

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_archive_raises_error(
        self,
        mock_db_session,
        mock_archive_repo,
        tmp_path
    ):
        """Test retrieving nonexistent archive raises error."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        archive_id = uuid4()
        mock_archive_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Archive not found"):
            await archiver.retrieve_archive(archive_id, tmp_path)

    @pytest.mark.asyncio
    async def test_retrieve_incomplete_archive_raises_error(
        self,
        mock_db_session,
        mock_archive_repo,
        tmp_path
    ):
        """Test retrieving incomplete archive raises error."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        archive_id = uuid4()
        mock_archive_repo.get_by_id.return_value = MagicMock(
            id=archive_id,
            status=ArchiveStatus.PENDING.value
        )

        with pytest.raises(ValueError, match="not completed"):
            await archiver.retrieve_archive(archive_id, tmp_path)


class TestCompressionMethods:
    """Tests for tar.gz compression."""

    def test_create_tar_gz(self, mock_db_session, mock_archive_repo, temp_working_dir, tmp_path):
        """Test creating tar.gz archive."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        archive_path = tmp_path / "test.tar.gz"

        archiver._create_tar_gz(temp_working_dir, archive_path)

        # Archive should exist
        assert archive_path.exists()
        assert archive_path.stat().st_size > 0

    def test_extract_tar_gz(self, mock_db_session, mock_archive_repo, temp_working_dir, tmp_path):
        """Test extracting tar.gz archive."""
        archiver = StorageArchiver(
            db=mock_db_session,
            archive_repo=mock_archive_repo,
            storage_provider="local"
        )

        # Create archive
        archive_path = tmp_path / "test.tar.gz"
        archiver._create_tar_gz(temp_working_dir, archive_path)

        # Extract to new location
        extract_path = tmp_path / "extracted"
        archiver._extract_tar_gz(archive_path, extract_path)

        # Extracted directory should contain files
        assert extract_path.exists()
        assert len(list(extract_path.rglob("*"))) > 0
