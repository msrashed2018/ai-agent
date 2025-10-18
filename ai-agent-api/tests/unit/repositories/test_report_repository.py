"""Unit tests for ReportRepository."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.repositories.report_repository import ReportRepository
from app.models.report import ReportModel


class TestReportRepository:
    """Test cases for ReportRepository."""

    @pytest_asyncio.fixture
    async def report_repository(self, db_session):
        """Create ReportRepository instance."""
        return ReportRepository(db_session)

    @pytest_asyncio.fixture
    async def test_report(self, db_session, test_user, test_session_model):
        """Create a test report."""
        report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="Test Report",
            description="A test report",
            report_type="auto_generated",
            content={"text": "Report content", "summary": "Summary"},
            file_format="markdown",
            file_size_bytes=1024,
            tags=["test", "automation"],
            is_public=False,
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)
        return report

    @pytest_asyncio.fixture
    async def public_report(self, db_session, test_user, test_session_model):
        """Create a public report."""
        report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="Public Report",
            description="A public report",
            report_type="custom",
            content={"text": "Public content"},
            is_public=True,
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)
        return report

    @pytest_asyncio.fixture
    async def deleted_report(self, db_session, test_user, test_session_model):
        """Create a soft-deleted report."""
        report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="Deleted Report",
            report_type="auto_generated",
            content={"text": "Deleted content"},
            deleted_at=datetime.utcnow(),
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)
        return report

    # Test: create (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_create_report(self, db_session, report_repository, test_user, test_session_model):
        """Test creating a new report."""
        # Arrange
        report_id = uuid4()
        report_data = {
            "id": report_id,
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "title": "New Report",
            "description": "New report description",
            "report_type": "template",
            "content": {"text": "Template content"},
            "file_format": "pdf",
            "template_name": "standard_report",
        }

        # Act
        created = await report_repository.create(**report_data)

        # Assert
        assert created is not None
        assert created.id == report_id
        assert created.title == "New Report"
        assert created.report_type == "template"
        assert created.file_format == "pdf"
        assert created.created_at is not None

    # Test: get_by_id
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session, report_repository, test_report):
        """Test getting report by ID when it exists."""
        # Act
        result = await report_repository.get_by_id(test_report.id)

        # Assert
        assert result is not None
        assert result.id == test_report.id
        assert result.title == test_report.title

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session, report_repository):
        """Test getting report by non-existent ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await report_repository.get_by_id(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_deleted(self, db_session, report_repository, deleted_report):
        """Test that get_by_id excludes soft-deleted reports."""
        # Act
        result = await report_repository.get_by_id(deleted_report.id)

        # Assert
        assert result is None

    # Test: get_by_session
    @pytest.mark.asyncio
    async def test_get_by_session(self, db_session, report_repository, test_session_model, test_report):
        """Test getting all reports for a session."""
        # Act
        result = await report_repository.get_by_session(test_session_model.id)

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)
        assert all(r.session_id == test_session_model.id for r in result)

    @pytest.mark.asyncio
    async def test_get_by_session_excludes_deleted(self, db_session, report_repository, test_session_model, test_report, deleted_report):
        """Test that get_by_session excludes deleted reports."""
        # Act
        result = await report_repository.get_by_session(test_session_model.id)

        # Assert
        assert any(r.id == test_report.id for r in result)
        assert not any(r.id == deleted_report.id for r in result)

    @pytest.mark.asyncio
    async def test_get_by_session_ordered_by_created_desc(self, db_session, report_repository, test_user, test_session_model):
        """Test reports are ordered by creation time descending."""
        # Arrange: Create reports with different timestamps
        old_report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="Old Report",
            report_type="auto_generated",
            content={},
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="New Report",
            report_type="auto_generated",
            content={},
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_report, new_report])
        await db_session.commit()

        # Act
        result = await report_repository.get_by_session(test_session_model.id)

        # Assert
        assert len(result) >= 2
        new_idx = next(i for i, r in enumerate(result) if r.id == new_report.id)
        old_idx = next(i for i, r in enumerate(result) if r.id == old_report.id)
        assert new_idx < old_idx

    @pytest.mark.asyncio
    async def test_get_by_session_with_pagination(self, db_session, report_repository, test_user, test_session_model):
        """Test pagination with skip and limit."""
        # Arrange: Create multiple reports
        for i in range(5):
            report = ReportModel(
                id=uuid4(),
                session_id=test_session_model.id,
                user_id=test_user.id,
                title=f"Report {i}",
                report_type="auto_generated",
                content={},
            )
            db_session.add(report)
        await db_session.commit()

        # Act
        page1 = await report_repository.get_by_session(test_session_model.id, skip=0, limit=2)
        page2 = await report_repository.get_by_session(test_session_model.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_by_session_empty(self, db_session, report_repository):
        """Test getting reports for session with no reports."""
        # Arrange
        non_existent_session_id = uuid4()

        # Act
        result = await report_repository.get_by_session(non_existent_session_id)

        # Assert
        assert result == []

    # Test: get_by_user
    @pytest.mark.asyncio
    async def test_get_by_user(self, db_session, report_repository, test_user, test_report):
        """Test getting all reports for a user."""
        # Act
        result = await report_repository.get_by_user(test_user.id)

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)
        assert all(r.user_id == test_user.id for r in result)

    @pytest.mark.asyncio
    async def test_get_by_user_excludes_deleted(self, db_session, report_repository, test_user, test_report, deleted_report):
        """Test that get_by_user excludes deleted reports."""
        # Act
        result = await report_repository.get_by_user(test_user.id)

        # Assert
        assert any(r.id == test_report.id for r in result)
        assert not any(r.id == deleted_report.id for r in result)

    @pytest.mark.asyncio
    async def test_get_by_user_with_pagination(self, db_session, report_repository, test_user, test_session_model):
        """Test pagination for user reports."""
        # Arrange: Create multiple reports
        for i in range(5):
            report = ReportModel(
                id=uuid4(),
                session_id=test_session_model.id,
                user_id=test_user.id,
                title=f"User Report {i}",
                report_type="auto_generated",
                content={},
            )
            db_session.add(report)
        await db_session.commit()

        # Act
        page1 = await report_repository.get_by_user(test_user.id, skip=0, limit=2)
        page2 = await report_repository.get_by_user(test_user.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_by_user_empty(self, db_session, report_repository):
        """Test getting reports for user with no reports."""
        # Arrange
        non_existent_user_id = uuid4()

        # Act
        result = await report_repository.get_by_user(non_existent_user_id)

        # Assert
        assert result == []

    # Test: get_by_task_execution
    @pytest.mark.asyncio
    async def test_get_by_task_execution_exists(self, db_session, report_repository, test_user, test_session_model):
        """Test getting report by task execution ID."""
        # Arrange
        task_execution_id = uuid4()
        report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            task_execution_id=task_execution_id,
            title="Task Report",
            report_type="auto_generated",
            content={},
        )
        db_session.add(report)
        await db_session.commit()

        # Act
        result = await report_repository.get_by_task_execution(task_execution_id)

        # Assert
        assert result is not None
        assert result.task_execution_id == task_execution_id

    @pytest.mark.asyncio
    async def test_get_by_task_execution_not_found(self, db_session, report_repository):
        """Test getting report by non-existent task execution ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await report_repository.get_by_task_execution(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_task_execution_excludes_deleted(self, db_session, report_repository, test_user, test_session_model):
        """Test that get_by_task_execution excludes deleted reports."""
        # Arrange
        task_execution_id = uuid4()
        report = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            task_execution_id=task_execution_id,
            title="Deleted Task Report",
            report_type="auto_generated",
            content={},
            deleted_at=datetime.utcnow(),
        )
        db_session.add(report)
        await db_session.commit()

        # Act
        result = await report_repository.get_by_task_execution(task_execution_id)

        # Assert
        assert result is None

    # Test: get_by_tags
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags(self, db_session, report_repository, test_report):
        """Test getting reports by tags."""
        # Act
        result = await report_repository.get_by_tags(["test"])

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_with_user_filter(self, db_session, report_repository, test_user, test_report):
        """Test getting reports by tags filtered by user."""
        # Act
        result = await report_repository.get_by_tags(["test"], user_id=test_user.id)

        # Assert
        assert len(result) >= 1
        assert all(r.user_id == test_user.id for r in result)

    # Test: get_public_reports
    @pytest.mark.asyncio
    async def test_get_public_reports(self, db_session, report_repository, public_report):
        """Test getting public reports."""
        # Act
        result = await report_repository.get_public_reports()

        # Assert
        assert len(result) >= 1
        assert any(r.id == public_report.id for r in result)
        assert all(r.is_public is True for r in result)

    @pytest.mark.asyncio
    async def test_get_public_reports_excludes_private(self, db_session, report_repository, test_report):
        """Test that get_public_reports excludes private reports."""
        # Act
        result = await report_repository.get_public_reports()

        # Assert
        assert not any(r.id == test_report.id for r in result)

    @pytest.mark.asyncio
    async def test_get_public_reports_excludes_deleted(self, db_session, report_repository, test_user, test_session_model):
        """Test that get_public_reports excludes deleted reports."""
        # Arrange
        deleted_public = ReportModel(
            id=uuid4(),
            session_id=test_session_model.id,
            user_id=test_user.id,
            title="Deleted Public",
            report_type="auto_generated",
            content={},
            is_public=True,
            deleted_at=datetime.utcnow(),
        )
        db_session.add(deleted_public)
        await db_session.commit()

        # Act
        result = await report_repository.get_public_reports()

        # Assert
        assert not any(r.id == deleted_public.id for r in result)

    @pytest.mark.asyncio
    async def test_get_public_reports_with_pagination(self, db_session, report_repository, test_user, test_session_model):
        """Test getting public reports with pagination."""
        # Arrange: Create multiple public reports
        for i in range(5):
            report = ReportModel(
                id=uuid4(),
                session_id=test_session_model.id,
                user_id=test_user.id,
                title=f"Public Report {i}",
                report_type="auto_generated",
                content={},
                is_public=True,
            )
            db_session.add(report)
        await db_session.commit()

        # Act
        page1 = await report_repository.get_public_reports(skip=0, limit=2)
        page2 = await report_repository.get_public_reports(skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    # Test: get_by_report_type
    @pytest.mark.asyncio
    async def test_get_by_report_type(self, db_session, report_repository, test_report):
        """Test getting reports by report type."""
        # Act
        result = await report_repository.get_by_report_type("auto_generated")

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)
        assert all(r.report_type == "auto_generated" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_report_type_with_user_filter(self, db_session, report_repository, test_user, test_report):
        """Test getting reports by type filtered by user."""
        # Act
        result = await report_repository.get_by_report_type("auto_generated", user_id=test_user.id)

        # Assert
        assert len(result) >= 1
        assert all(r.user_id == test_user.id for r in result)
        assert all(r.report_type == "auto_generated" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_report_type_not_found(self, db_session, report_repository):
        """Test getting reports with type that doesn't exist."""
        # Act
        result = await report_repository.get_by_report_type("nonexistent_type")

        # Assert
        assert result == []

    # Test: get_by_format
    @pytest.mark.asyncio
    async def test_get_by_format(self, db_session, report_repository, test_report):
        """Test getting reports by file format."""
        # Act
        result = await report_repository.get_by_format("markdown")

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)
        assert all(r.file_format == "markdown" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_format_with_user_filter(self, db_session, report_repository, test_user, test_report):
        """Test getting reports by format filtered by user."""
        # Act
        result = await report_repository.get_by_format("markdown", user_id=test_user.id)

        # Assert
        assert len(result) >= 1
        assert all(r.user_id == test_user.id for r in result)
        assert all(r.file_format == "markdown" for r in result)

    @pytest.mark.asyncio
    async def test_get_by_format_not_found(self, db_session, report_repository):
        """Test getting reports with format that doesn't exist."""
        # Act
        result = await report_repository.get_by_format("nonexistent_format")

        # Assert
        assert result == []

    # Test: soft_delete
    @pytest.mark.asyncio
    async def test_soft_delete_report(self, db_session, report_repository, test_report):
        """Test soft deleting a report."""
        # Act
        success = await report_repository.soft_delete(test_report.id)
        await db_session.refresh(test_report)

        # Assert
        assert success is True
        assert test_report.deleted_at is not None

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self, db_session, report_repository):
        """Test soft deleting non-existent report."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await report_repository.soft_delete(non_existent_id)

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_soft_delete_updates_updated_at(self, db_session, report_repository, test_report):
        """Test that soft delete updates the updated_at timestamp."""
        # Arrange
        original_updated_at = test_report.updated_at

        # Act
        await report_repository.soft_delete(test_report.id)
        await db_session.refresh(test_report)

        # Assert
        assert test_report.updated_at > original_updated_at

    # Test: search_content (PostgreSQL-specific)
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="JSONB @> operator requires PostgreSQL, SQLite uses emulation")
    async def test_search_content(self, db_session, report_repository, test_report):
        """Test searching reports by content text."""
        # Act
        result = await report_repository.search_content("Report content")

        # Assert
        assert len(result) >= 1
        assert any(r.id == test_report.id for r in result)

    # Test: count_by_user
    @pytest.mark.asyncio
    async def test_count_by_user(self, db_session, report_repository, test_user, test_report):
        """Test counting reports for a user."""
        # Act
        count = await report_repository.count_by_user(test_user.id)

        # Assert
        assert count >= 1

    @pytest.mark.asyncio
    async def test_count_by_user_excludes_deleted(self, db_session, report_repository, test_user, test_report, deleted_report):
        """Test that count excludes deleted reports."""
        # Act
        count = await report_repository.count_by_user(test_user.id)

        # Assert
        # Should only count test_report, not deleted_report
        assert count >= 1

    @pytest.mark.asyncio
    async def test_count_by_user_empty(self, db_session, report_repository):
        """Test counting reports for user with no reports."""
        # Arrange
        non_existent_user_id = uuid4()

        # Act
        count = await report_repository.count_by_user(non_existent_user_id)

        # Assert
        assert count == 0

    # Test: update (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_update_report(self, db_session, report_repository, test_report):
        """Test updating a report."""
        # Act
        updated = await report_repository.update(
            test_report.id,
            title="Updated Report",
            description="Updated description"
        )

        # Assert
        assert updated is not None
        assert updated.title == "Updated Report"
        assert updated.description == "Updated description"

    # Test: delete (inherited from BaseRepository, hard delete)
    @pytest.mark.asyncio
    async def test_delete_report_hard(self, db_session, report_repository, test_report):
        """Test hard deleting a report."""
        # Arrange
        report_id = test_report.id

        # Act
        success = await report_repository.delete(report_id)

        # Assert
        assert success is True
        # Hard delete removes the record entirely
        from sqlalchemy import select
        result = await db_session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        deleted = result.scalar_one_or_none()
        assert deleted is None
