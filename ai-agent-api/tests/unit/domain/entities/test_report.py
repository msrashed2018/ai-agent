"""Unit tests for Report domain entity."""

import pytest
from uuid import uuid4
from app.domain.entities.report import Report, ReportType, ReportFormat


class TestReportEntity:
    """Test cases for Report entity."""

    def test_report_creation(self):
        """Test report initialization."""
        report_id = uuid4()
        session_id = uuid4()
        user_id = uuid4()
        content = {"data": "test"}

        report = Report(
            id=report_id,
            session_id=session_id,
            user_id=user_id,
            title="Test Report",
            content=content,
        )

        assert report.id == report_id
        assert report.session_id == session_id
        assert report.user_id == user_id
        assert report.title == "Test Report"
        assert report.content == content
        assert report.description is None
        assert report.report_type == ReportType.AUTO_GENERATED
        assert report.is_deleted is False
        assert report.is_public is False

    def test_report_timestamps(self):
        """Test report timestamps."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        assert report.created_at is not None
        assert report.updated_at is not None
        assert report.deleted_at is None

    def test_set_file_output(self):
        """Test setting file output information."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        report.set_file_output("/path/to/report.pdf", "pdf", 1024000)

        assert report.file_path == "/path/to/report.pdf"
        assert report.file_format == "pdf"
        assert report.file_size_bytes == 1024000

    def test_add_tag(self):
        """Test adding a tag."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        assert report.tags == []

        report.add_tag("important")
        assert "important" in report.tags

        # Adding same tag again should not duplicate
        report.add_tag("important")
        assert report.tags.count("important") == 1

    def test_remove_tag(self):
        """Test removing a tag."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        report.add_tag("important")
        report.add_tag("archived")

        assert "important" in report.tags
        assert "archived" in report.tags

        report.remove_tag("important")
        assert "important" not in report.tags
        assert "archived" in report.tags

    def test_remove_nonexistent_tag(self):
        """Test removing a tag that doesn't exist."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        # Should not raise error
        report.remove_tag("nonexistent")
        assert len(report.tags) == 0

    def test_soft_delete(self):
        """Test soft deleting a report."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        assert report.is_deleted is False
        assert report.deleted_at is None

        report.soft_delete()

        assert report.is_deleted is True
        assert report.deleted_at is not None

    def test_make_public(self):
        """Test making report public."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        assert report.is_public is False

        report.make_public()
        assert report.is_public is True

    def test_make_private(self):
        """Test making report private."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        report.is_public = True
        report.make_private()
        assert report.is_public is False

    def test_report_type_constants(self):
        """Test report type constants."""
        assert ReportType.AUTO_GENERATED == "auto_generated"
        assert ReportType.CUSTOM == "custom"
        assert ReportType.TEMPLATE == "template"

    def test_report_format_constants(self):
        """Test report format constants."""
        assert ReportFormat.JSON == "json"
        assert ReportFormat.MARKDOWN == "markdown"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.PDF == "pdf"

    def test_file_output_initially_none(self):
        """Test file output fields are initially None."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        assert report.file_path is None
        assert report.file_format is None
        assert report.file_size_bytes is None

    def test_template_name_assignment(self):
        """Test assigning template name."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        report.template_name = "standard_report"
        assert report.template_name == "standard_report"

    def test_task_execution_id_assignment(self):
        """Test assigning task execution ID."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        task_exec_id = uuid4()
        report.task_execution_id = task_exec_id
        assert report.task_execution_id == task_exec_id

    def test_report_with_large_content(self):
        """Test report with large content."""
        large_content = {
            "data": "x" * 10000,  # 10k characters
            "nested": {"deep": {"structure": [1, 2, 3]}},
        }

        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Large Report",
            content=large_content,
        )

        assert report.content == large_content
        assert len(report.content["data"]) == 10000

    def test_multiple_tags_operations(self):
        """Test multiple tag operations."""
        report = Report(
            id=uuid4(),
            session_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content={},
        )

        tags = ["tag1", "tag2", "tag3", "tag4"]
        for tag in tags:
            report.add_tag(tag)

        assert len(report.tags) == 4

        report.remove_tag("tag2")
        assert len(report.tags) == 3
        assert "tag2" not in report.tags

        report.add_tag("tag5")
        assert len(report.tags) == 4
