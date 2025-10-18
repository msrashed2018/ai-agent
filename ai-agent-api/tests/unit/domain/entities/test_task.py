"""Unit tests for Task domain entity."""

import pytest
from uuid import uuid4
from app.domain.entities.task import Task
from app.domain.exceptions import ValidationError


class TestTaskEntity:
    """Test cases for Task entity."""

    def test_task_creation(self):
        """Test task initialization."""
        task_id = uuid4()
        user_id = uuid4()
        allowed_tools = ["read", "write"]
        sdk_options = {"model": "claude-sonnet-4-5"}

        task = Task(
            id=task_id,
            user_id=user_id,
            name="Test Task",
            prompt_template="Process {{ input }}",
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
        )

        assert task.id == task_id
        assert task.user_id == user_id
        assert task.name == "Test Task"
        assert task.prompt_template == "Process {{ input }}"
        assert task.allowed_tools == allowed_tools
        assert task.sdk_options == sdk_options
        assert task.is_active is True
        assert task.is_deleted is False

    def test_render_prompt_with_variables(self):
        """Test rendering prompt template with variables."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="Analyze {{ filename }} in {{ language }}",
            allowed_tools=[],
            sdk_options={},
        )

        rendered = task.render_prompt({"filename": "test.py", "language": "Python"})
        assert rendered == "Analyze test.py in Python"

    def test_validate_schedule_without_cron_raises_error(self):
        """Test validating schedule without cron expression raises error."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        task.is_scheduled = True
        with pytest.raises(ValidationError):
            task.validate_schedule()

    def test_validate_schedule_with_valid_cron(self):
        """Test validating schedule with valid cron expression."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        task.is_scheduled = True
        task.schedule_cron = "0 0 * * *"  # Daily at midnight
        task.validate_schedule()  # Should not raise

    def test_validate_schedule_with_invalid_cron_raises_error(self):
        """Test validating schedule with invalid cron raises error."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        task.is_scheduled = True
        task.schedule_cron = "invalid cron"
        with pytest.raises(ValidationError):
            task.validate_schedule()

    def test_validate_report_format_valid_formats(self):
        """Test validating report format with valid formats."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        for format in ["json", "markdown", "html", "pdf"]:
            task.generate_report = True
            task.report_format = format
            task.validate_report_format()  # Should not raise

    def test_validate_report_format_invalid_format_raises_error(self):
        """Test validating report format with invalid format raises error."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        task.generate_report = True
        task.report_format = "invalid_format"
        with pytest.raises(ValidationError):
            task.validate_report_format()

    def test_soft_delete(self):
        """Test soft deleting a task."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        assert task.is_deleted is False
        assert task.deleted_at is None

        task.soft_delete()

        assert task.is_deleted is True
        assert task.deleted_at is not None

    def test_activate_task(self):
        """Test activating a task."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        task.is_active = False
        task.activate()
        assert task.is_active is True

    def test_deactivate_task(self):
        """Test deactivating a task."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        assert task.is_active is True
        task.deactivate()
        assert task.is_active is False

    def test_task_default_values(self):
        """Test task default values."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=[],
            sdk_options={},
        )

        assert task.description is None
        assert task.is_scheduled is False
        assert task.schedule_cron is None
        assert task.schedule_enabled is False
        assert task.generate_report is False
        assert task.report_format is None
        assert task.notification_config is None
        assert task.tags == []
        assert task.is_public is False

    def test_task_disallowed_tools(self):
        """Test task disallowed tools."""
        task = Task(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            prompt_template="",
            allowed_tools=["read", "write"],
            sdk_options={},
        )

        assert task.disallowed_tools == []
        task.disallowed_tools = ["delete", "execute"]
        assert "delete" in task.disallowed_tools
