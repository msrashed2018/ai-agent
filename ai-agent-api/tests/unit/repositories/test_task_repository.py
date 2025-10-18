"""Unit tests for TaskRepository."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.repositories.task_repository import TaskRepository
from app.models.task import TaskModel


class TestTaskRepository:
    """Test cases for TaskRepository."""

    @pytest_asyncio.fixture
    async def task_repository(self, db_session):
        """Create TaskRepository instance."""
        return TaskRepository(db_session)

    @pytest_asyncio.fixture
    async def test_task(self, db_session, test_user):
        """Create a test task."""
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Task",
            description="A test task",
            prompt_template="Execute {{ command }}",
            default_variables={"command": "ls -la"},
            allowed_tools=["bash", "read"],
            disallowed_tools=["delete"],
            sdk_options={"model": "claude-3-sonnet-20240229"},
            is_scheduled=False,
            is_active=True,
            is_deleted=False,
            is_public=False,
            tags=["test", "automation"],
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    @pytest_asyncio.fixture
    async def scheduled_task(self, db_session, test_user):
        """Create a scheduled task."""
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Scheduled Task",
            description="A scheduled task",
            prompt_template="Run daily backup",
            allowed_tools=["bash"],
            is_scheduled=True,
            schedule_cron="0 0 * * *",
            schedule_enabled=True,
            is_active=True,
            is_deleted=False,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    @pytest_asyncio.fixture
    async def public_task(self, db_session, test_user):
        """Create a public task."""
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Public Task",
            description="A public task visible to all",
            prompt_template="Public template",
            allowed_tools=["bash"],
            is_public=True,
            is_deleted=False,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    @pytest_asyncio.fixture
    async def deleted_task(self, db_session, test_user):
        """Create a soft-deleted task."""
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Deleted Task",
            prompt_template="Template",
            allowed_tools=["bash"],
            is_deleted=True,
            deleted_at=datetime.utcnow(),
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    # Test: create (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_create_task(self, db_session, task_repository, test_user):
        """Test creating a new task."""
        # Arrange
        task_id = uuid4()
        task_data = {
            "id": task_id,
            "user_id": test_user.id,
            "name": "New Task",
            "description": "New task description",
            "prompt_template": "Execute {{ action }}",
            "default_variables": {"action": "test"},
            "allowed_tools": ["bash", "grep"],
            "sdk_options": {"model": "claude-3-sonnet-20240229"},
        }

        # Act
        created = await task_repository.create(**task_data)

        # Assert
        assert created is not None
        assert created.id == task_id
        assert created.name == "New Task"
        assert created.prompt_template == "Execute {{ action }}"
        assert created.allowed_tools == ["bash", "grep"]
        assert created.is_deleted is False
        assert created.created_at is not None

    # Test: get_by_id
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session, task_repository, test_task):
        """Test getting task by ID when it exists."""
        # Act
        result = await task_repository.get_by_id(test_task.id)

        # Assert
        assert result is not None
        assert result.id == test_task.id
        assert result.name == test_task.name

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session, task_repository):
        """Test getting task by non-existent ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await task_repository.get_by_id(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_deleted(self, db_session, task_repository, deleted_task):
        """Test that get_by_id excludes soft-deleted tasks."""
        # Act
        result = await task_repository.get_by_id(deleted_task.id)

        # Assert
        assert result is None

    # Test: get_by_user
    @pytest.mark.asyncio
    async def test_get_by_user(self, db_session, task_repository, test_user, test_task):
        """Test getting all tasks for a user."""
        # Act
        result = await task_repository.get_by_user(test_user.id)

        # Assert
        assert len(result) >= 1
        assert any(t.id == test_task.id for t in result)
        assert all(t.user_id == test_user.id for t in result)

    @pytest.mark.asyncio
    async def test_get_by_user_excludes_deleted_by_default(self, db_session, task_repository, test_user, test_task, deleted_task):
        """Test that get_by_user excludes deleted tasks by default."""
        # Act
        result = await task_repository.get_by_user(test_user.id)

        # Assert
        assert any(t.id == test_task.id for t in result)
        assert not any(t.id == deleted_task.id for t in result)

    @pytest.mark.asyncio
    async def test_get_by_user_includes_deleted_when_requested(self, db_session, task_repository, test_user, test_task, deleted_task):
        """Test that get_by_user includes deleted tasks when requested."""
        # Act
        result = await task_repository.get_by_user(test_user.id, include_deleted=True)

        # Assert
        assert any(t.id == test_task.id for t in result)
        assert any(t.id == deleted_task.id for t in result)

    @pytest.mark.asyncio
    async def test_get_by_user_ordered_by_created_desc(self, db_session, task_repository, test_user):
        """Test tasks are ordered by creation time descending."""
        # Arrange: Create tasks with different timestamps
        old_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Old Task",
            prompt_template="Template",
            allowed_tools=["bash"],
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="New Task",
            prompt_template="Template",
            allowed_tools=["bash"],
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_task, new_task])
        await db_session.commit()

        # Act
        result = await task_repository.get_by_user(test_user.id)

        # Assert
        assert len(result) >= 2
        new_idx = next(i for i, t in enumerate(result) if t.id == new_task.id)
        old_idx = next(i for i, t in enumerate(result) if t.id == old_task.id)
        assert new_idx < old_idx  # Newer should come first

    @pytest.mark.asyncio
    async def test_get_by_user_with_pagination(self, db_session, task_repository, test_user):
        """Test pagination with skip and limit."""
        # Arrange: Create multiple tasks
        for i in range(5):
            task = TaskModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Task {i}",
                prompt_template="Template",
                allowed_tools=["bash"],
            )
            db_session.add(task)
        await db_session.commit()

        # Act
        page1 = await task_repository.get_by_user(test_user.id, skip=0, limit=2)
        page2 = await task_repository.get_by_user(test_user.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_by_user_empty(self, db_session, task_repository):
        """Test getting tasks for user with no tasks."""
        # Arrange
        non_existent_user_id = uuid4()

        # Act
        result = await task_repository.get_by_user(non_existent_user_id)

        # Assert
        assert result == []

    # Test: get_by_name
    @pytest.mark.asyncio
    async def test_get_by_name_exists(self, db_session, task_repository, test_user, test_task):
        """Test getting task by name when it exists."""
        # Act
        result = await task_repository.get_by_name(test_task.name, test_user.id)

        # Assert
        assert result is not None
        assert result.id == test_task.id
        assert result.name == test_task.name

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, db_session, task_repository, test_user):
        """Test getting task by non-existent name."""
        # Act
        result = await task_repository.get_by_name("Nonexistent Task", test_user.id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_excludes_deleted(self, db_session, task_repository, test_user, deleted_task):
        """Test that get_by_name excludes deleted tasks."""
        # Act
        result = await task_repository.get_by_name(deleted_task.name, test_user.id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_user_specific(self, db_session, task_repository, test_user, admin_user):
        """Test that get_by_name is user-specific."""
        # Arrange: Create task for admin user with same name
        admin_task = TaskModel(
            id=uuid4(),
            user_id=admin_user.id,
            name="Shared Name",
            prompt_template="Template",
            allowed_tools=["bash"],
        )
        user_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Shared Name",
            prompt_template="Template",
            allowed_tools=["bash"],
        )
        db_session.add_all([admin_task, user_task])
        await db_session.commit()

        # Act
        result = await task_repository.get_by_name("Shared Name", test_user.id)

        # Assert
        assert result is not None
        assert result.id == user_task.id
        assert result.user_id == test_user.id

    # Test: get_scheduled_tasks
    @pytest.mark.asyncio
    async def test_get_scheduled_tasks(self, db_session, task_repository, scheduled_task):
        """Test getting scheduled tasks."""
        # Act
        result = await task_repository.get_scheduled_tasks()

        # Assert
        assert len(result) >= 1
        assert any(t.id == scheduled_task.id for t in result)
        assert all(t.is_scheduled is True for t in result)
        assert all(t.schedule_enabled is True for t in result)

    @pytest.mark.asyncio
    async def test_get_scheduled_tasks_enabled_only(self, db_session, task_repository, test_user):
        """Test getting only enabled scheduled tasks."""
        # Arrange: Create disabled scheduled task
        disabled_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Disabled Scheduled",
            prompt_template="Template",
            allowed_tools=["bash"],
            is_scheduled=True,
            schedule_cron="0 0 * * *",
            schedule_enabled=False,
        )
        db_session.add(disabled_task)
        await db_session.commit()

        # Act
        result = await task_repository.get_scheduled_tasks(enabled_only=True)

        # Assert
        assert not any(t.id == disabled_task.id for t in result)

    @pytest.mark.asyncio
    async def test_get_scheduled_tasks_includes_disabled(self, db_session, task_repository, test_user, scheduled_task):
        """Test getting scheduled tasks including disabled ones."""
        # Arrange: Create disabled scheduled task
        disabled_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Disabled Scheduled",
            prompt_template="Template",
            allowed_tools=["bash"],
            is_scheduled=True,
            schedule_cron="0 0 * * *",
            schedule_enabled=False,
        )
        db_session.add(disabled_task)
        await db_session.commit()

        # Act
        result = await task_repository.get_scheduled_tasks(enabled_only=False)

        # Assert
        assert any(t.id == scheduled_task.id for t in result)
        assert any(t.id == disabled_task.id for t in result)

    @pytest.mark.asyncio
    async def test_get_scheduled_tasks_excludes_deleted(self, db_session, task_repository, test_user):
        """Test that scheduled tasks excludes deleted tasks."""
        # Arrange: Create deleted scheduled task
        deleted_scheduled = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Deleted Scheduled",
            prompt_template="Template",
            allowed_tools=["bash"],
            is_scheduled=True,
            schedule_enabled=True,
            is_deleted=True,
            deleted_at=datetime.utcnow(),
        )
        db_session.add(deleted_scheduled)
        await db_session.commit()

        # Act
        result = await task_repository.get_scheduled_tasks()

        # Assert
        assert not any(t.id == deleted_scheduled.id for t in result)

    # Test: get_by_tags
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags(self, db_session, task_repository, test_task):
        """Test getting tasks by tags."""
        # Act
        result = await task_repository.get_by_tags(["test"])

        # Assert
        assert len(result) >= 1
        assert any(t.id == test_task.id for t in result)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_multiple_tags(self, db_session, task_repository, test_task):
        """Test getting tasks matching any of multiple tags."""
        # Act
        result = await task_repository.get_by_tags(["test", "automation"])

        # Assert
        assert len(result) >= 1
        assert any(t.id == test_task.id for t in result)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_with_user_filter(self, db_session, task_repository, test_user, test_task):
        """Test getting tasks by tags filtered by user."""
        # Act
        result = await task_repository.get_by_tags(["test"], user_id=test_user.id)

        # Assert
        assert len(result) >= 1
        assert all(t.user_id == test_user.id for t in result)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_not_found(self, db_session, task_repository):
        """Test getting tasks with non-existent tags."""
        # Act
        result = await task_repository.get_by_tags(["nonexistent_tag"])

        # Assert
        assert result == []

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_excludes_deleted(self, db_session, task_repository, test_user):
        """Test that get_by_tags excludes deleted tasks."""
        # Arrange: Create deleted task with tags
        deleted_tagged = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Deleted Tagged",
            prompt_template="Template",
            allowed_tools=["bash"],
            tags=["deleted_tag"],
            is_deleted=True,
            deleted_at=datetime.utcnow(),
        )
        db_session.add(deleted_tagged)
        await db_session.commit()

        # Act
        result = await task_repository.get_by_tags(["deleted_tag"])

        # Assert
        assert not any(t.id == deleted_tagged.id for t in result)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="ARRAY overlap operator requires PostgreSQL, SQLite uses emulation")
    async def test_get_by_tags_with_pagination(self, db_session, task_repository, test_user):
        """Test getting tasks by tags with pagination."""
        # Arrange: Create multiple tasks with same tag
        for i in range(5):
            task = TaskModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Tagged Task {i}",
                prompt_template="Template",
                allowed_tools=["bash"],
                tags=["common_tag"],
            )
            db_session.add(task)
        await db_session.commit()

        # Act
        page1 = await task_repository.get_by_tags(["common_tag"], skip=0, limit=2)
        page2 = await task_repository.get_by_tags(["common_tag"], skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    # Test: get_public_tasks
    @pytest.mark.asyncio
    async def test_get_public_tasks(self, db_session, task_repository, public_task):
        """Test getting public tasks."""
        # Act
        result = await task_repository.get_public_tasks()

        # Assert
        assert len(result) >= 1
        assert any(t.id == public_task.id for t in result)
        assert all(t.is_public is True for t in result)

    @pytest.mark.asyncio
    async def test_get_public_tasks_excludes_private(self, db_session, task_repository, test_task):
        """Test that get_public_tasks excludes private tasks."""
        # Act
        result = await task_repository.get_public_tasks()

        # Assert
        assert not any(t.id == test_task.id for t in result)

    @pytest.mark.asyncio
    async def test_get_public_tasks_excludes_deleted(self, db_session, task_repository, test_user):
        """Test that get_public_tasks excludes deleted tasks."""
        # Arrange: Create deleted public task
        deleted_public = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Deleted Public",
            prompt_template="Template",
            allowed_tools=["bash"],
            is_public=True,
            is_deleted=True,
            deleted_at=datetime.utcnow(),
        )
        db_session.add(deleted_public)
        await db_session.commit()

        # Act
        result = await task_repository.get_public_tasks()

        # Assert
        assert not any(t.id == deleted_public.id for t in result)

    @pytest.mark.asyncio
    async def test_get_public_tasks_with_pagination(self, db_session, task_repository, test_user):
        """Test getting public tasks with pagination."""
        # Arrange: Create multiple public tasks
        for i in range(5):
            task = TaskModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Public Task {i}",
                prompt_template="Template",
                allowed_tools=["bash"],
                is_public=True,
            )
            db_session.add(task)
        await db_session.commit()

        # Act
        page1 = await task_repository.get_public_tasks(skip=0, limit=2)
        page2 = await task_repository.get_public_tasks(skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    # Test: soft_delete
    @pytest.mark.asyncio
    async def test_soft_delete_task(self, db_session, task_repository, test_task):
        """Test soft deleting a task."""
        # Act
        success = await task_repository.soft_delete(test_task.id)
        await db_session.refresh(test_task)

        # Assert
        assert success is True
        assert test_task.is_deleted is True
        assert test_task.deleted_at is not None

    @pytest.mark.asyncio
    async def test_soft_delete_not_found(self, db_session, task_repository):
        """Test soft deleting non-existent task."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_repository.soft_delete(non_existent_id)

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_soft_delete_updates_updated_at(self, db_session, task_repository, test_task):
        """Test that soft delete updates the updated_at timestamp."""
        # Arrange
        original_updated_at = test_task.updated_at

        # Act
        await task_repository.soft_delete(test_task.id)
        await db_session.refresh(test_task)

        # Assert
        assert test_task.updated_at > original_updated_at

    # Test: activate
    @pytest.mark.asyncio
    async def test_activate_task(self, db_session, task_repository, test_task):
        """Test activating a task."""
        # Arrange: First deactivate the task
        test_task.is_active = False
        await db_session.commit()

        # Act
        success = await task_repository.activate(test_task.id)
        await db_session.refresh(test_task)

        # Assert
        assert success is True
        assert test_task.is_active is True

    @pytest.mark.asyncio
    async def test_activate_not_found(self, db_session, task_repository):
        """Test activating non-existent task."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_repository.activate(non_existent_id)

        # Assert
        assert success is False

    # Test: deactivate
    @pytest.mark.asyncio
    async def test_deactivate_task(self, db_session, task_repository, test_task):
        """Test deactivating a task."""
        # Act
        success = await task_repository.deactivate(test_task.id)
        await db_session.refresh(test_task)

        # Assert
        assert success is True
        assert test_task.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self, db_session, task_repository):
        """Test deactivating non-existent task."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_repository.deactivate(non_existent_id)

        # Assert
        assert success is False

    # Test: enable_schedule
    @pytest.mark.asyncio
    async def test_enable_schedule(self, db_session, task_repository, test_task):
        """Test enabling task schedule."""
        # Arrange: Ensure schedule is disabled
        test_task.schedule_enabled = False
        await db_session.commit()

        # Act
        success = await task_repository.enable_schedule(test_task.id)
        await db_session.refresh(test_task)

        # Assert
        assert success is True
        assert test_task.schedule_enabled is True

    @pytest.mark.asyncio
    async def test_enable_schedule_not_found(self, db_session, task_repository):
        """Test enabling schedule for non-existent task."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_repository.enable_schedule(non_existent_id)

        # Assert
        assert success is False

    # Test: disable_schedule
    @pytest.mark.asyncio
    async def test_disable_schedule(self, db_session, task_repository, scheduled_task):
        """Test disabling task schedule."""
        # Act
        success = await task_repository.disable_schedule(scheduled_task.id)
        await db_session.refresh(scheduled_task)

        # Assert
        assert success is True
        assert scheduled_task.schedule_enabled is False

    @pytest.mark.asyncio
    async def test_disable_schedule_not_found(self, db_session, task_repository):
        """Test disabling schedule for non-existent task."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_repository.disable_schedule(non_existent_id)

        # Assert
        assert success is False

    # Test: count_by_user
    @pytest.mark.asyncio
    async def test_count_by_user(self, db_session, task_repository, test_user, test_task):
        """Test counting tasks for a user."""
        # Act
        count = await task_repository.count_by_user(test_user.id)

        # Assert
        assert count >= 1

    @pytest.mark.asyncio
    async def test_count_by_user_excludes_deleted_by_default(self, db_session, task_repository, test_user, test_task, deleted_task):
        """Test that count excludes deleted tasks by default."""
        # Act
        count = await task_repository.count_by_user(test_user.id)
        count_with_deleted = await task_repository.count_by_user(test_user.id, include_deleted=True)

        # Assert
        assert count_with_deleted > count

    @pytest.mark.asyncio
    async def test_count_by_user_empty(self, db_session, task_repository):
        """Test counting tasks for user with no tasks."""
        # Arrange
        non_existent_user_id = uuid4()

        # Act
        count = await task_repository.count_by_user(non_existent_user_id)

        # Assert
        assert count == 0

    # Test: update (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_update_task(self, db_session, task_repository, test_task):
        """Test updating a task."""
        # Act
        updated = await task_repository.update(
            test_task.id,
            description="Updated description",
            tags=["updated", "test"]
        )

        # Assert
        assert updated is not None
        assert updated.description == "Updated description"
        assert "updated" in updated.tags

    # Test: delete (inherited from BaseRepository, hard delete)
    @pytest.mark.asyncio
    async def test_delete_task_hard(self, db_session, task_repository, test_task):
        """Test hard deleting a task."""
        # Arrange
        task_id = test_task.id

        # Act
        success = await task_repository.delete(task_id)

        # Assert
        assert success is True
        # Hard delete removes the record entirely, even from get_by_id with include_deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        deleted = result.scalar_one_or_none()
        assert deleted is None
