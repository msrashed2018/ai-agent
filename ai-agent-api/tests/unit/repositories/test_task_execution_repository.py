"""Unit tests for TaskExecutionRepository."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.repositories.task_execution_repository import TaskExecutionRepository
from app.models.task_execution import TaskExecutionModel
from app.models.task import TaskModel


class TestTaskExecutionRepository:
    """Test cases for TaskExecutionRepository."""

    @pytest_asyncio.fixture
    async def task_execution_repository(self, db_session):
        """Create TaskExecutionRepository instance."""
        return TaskExecutionRepository(db_session)

    @pytest_asyncio.fixture
    async def test_task(self, db_session, test_user):
        """Create a test task for executions."""
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Task",
            prompt_template="Execute {{ command }}",
            allowed_tools=["bash"],
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        return task

    @pytest_asyncio.fixture
    async def test_execution(self, db_session, test_task, test_session_model):
        """Create a test task execution."""
        execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            session_id=test_session_model.id,
            trigger_type="manual",
            trigger_metadata={"user": "test@example.com"},
            prompt_variables={"command": "ls -la"},
            status="pending",
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        return execution

    @pytest_asyncio.fixture
    async def completed_execution(self, db_session, test_task, test_session_model):
        """Create a completed execution."""
        execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            session_id=test_session_model.id,
            trigger_type="scheduled",
            status="completed",
            result_data={"output": "success"},
            total_messages=5,
            total_tool_calls=2,
            duration_seconds=120,
            started_at=datetime.utcnow() - timedelta(minutes=2),
            completed_at=datetime.utcnow(),
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        return execution

    @pytest_asyncio.fixture
    async def failed_execution(self, db_session, test_task):
        """Create a failed execution."""
        execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="api",
            status="failed",
            error_message="Task execution failed",
            started_at=datetime.utcnow() - timedelta(minutes=1),
            completed_at=datetime.utcnow(),
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        return execution

    # Test: create (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_create_execution(self, db_session, task_execution_repository, test_task, test_session_model):
        """Test creating a new task execution."""
        # Arrange
        execution_id = uuid4()
        execution_data = {
            "id": execution_id,
            "task_id": test_task.id,
            "session_id": test_session_model.id,
            "trigger_type": "webhook",
            "trigger_metadata": {"source": "github"},
            "prompt_variables": {"repo": "my-repo"},
            "status": "pending",
        }

        # Act
        created = await task_execution_repository.create(**execution_data)

        # Assert
        assert created is not None
        assert created.id == execution_id
        assert created.task_id == test_task.id
        assert created.trigger_type == "webhook"
        assert created.status == "pending"
        assert created.created_at is not None

    # Test: get_by_id (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session, task_execution_repository, test_execution):
        """Test getting execution by ID when it exists."""
        # Act
        result = await task_execution_repository.get_by_id(test_execution.id)

        # Assert
        assert result is not None
        assert result.id == test_execution.id
        assert result.task_id == test_execution.task_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session, task_execution_repository):
        """Test getting execution by non-existent ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await task_execution_repository.get_by_id(non_existent_id)

        # Assert
        assert result is None

    # Test: get_by_task
    @pytest.mark.asyncio
    async def test_get_by_task(self, db_session, task_execution_repository, test_task, test_execution, completed_execution):
        """Test getting all executions for a task."""
        # Act
        result = await task_execution_repository.get_by_task(test_task.id)

        # Assert
        assert len(result) >= 2
        execution_ids = [e.id for e in result]
        assert test_execution.id in execution_ids
        assert completed_execution.id in execution_ids
        assert all(e.task_id == test_task.id for e in result)

    @pytest.mark.asyncio
    async def test_get_by_task_ordered_by_created_desc(self, db_session, task_execution_repository, test_task):
        """Test executions are ordered by creation time descending."""
        # Arrange: Create executions with different timestamps
        old_execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="completed",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="pending",
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_execution, new_execution])
        await db_session.commit()

        # Act
        result = await task_execution_repository.get_by_task(test_task.id)

        # Assert
        assert len(result) >= 2
        new_idx = next(i for i, e in enumerate(result) if e.id == new_execution.id)
        old_idx = next(i for i, e in enumerate(result) if e.id == old_execution.id)
        assert new_idx < old_idx  # Newer should come first

    @pytest.mark.asyncio
    async def test_get_by_task_with_pagination(self, db_session, task_execution_repository, test_task):
        """Test pagination with skip and limit."""
        # Arrange: Create multiple executions
        for i in range(5):
            execution = TaskExecutionModel(
                id=uuid4(),
                task_id=test_task.id,
                trigger_type="manual",
                status="pending",
            )
            db_session.add(execution)
        await db_session.commit()

        # Act
        page1 = await task_execution_repository.get_by_task(test_task.id, skip=0, limit=2)
        page2 = await task_execution_repository.get_by_task(test_task.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_by_task_empty(self, db_session, task_execution_repository):
        """Test getting executions for task with no executions."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        result = await task_execution_repository.get_by_task(non_existent_task_id)

        # Assert
        assert result == []

    # Test: get_by_session
    @pytest.mark.asyncio
    async def test_get_by_session_exists(self, db_session, task_execution_repository, test_execution):
        """Test getting execution by session ID when it exists."""
        # Act
        result = await task_execution_repository.get_by_session(test_execution.session_id)

        # Assert
        assert result is not None
        assert result.id == test_execution.id
        assert result.session_id == test_execution.session_id

    @pytest.mark.asyncio
    async def test_get_by_session_not_found(self, db_session, task_execution_repository):
        """Test getting execution by non-existent session ID."""
        # Arrange
        non_existent_session_id = uuid4()

        # Act
        result = await task_execution_repository.get_by_session(non_existent_session_id)

        # Assert
        assert result is None

    # Test: get_by_status
    @pytest.mark.asyncio
    async def test_get_by_status(self, db_session, task_execution_repository, test_execution, completed_execution):
        """Test getting executions by status."""
        # Act
        pending = await task_execution_repository.get_by_status("pending")
        completed = await task_execution_repository.get_by_status("completed")

        # Assert
        assert len(pending) >= 1
        assert any(e.id == test_execution.id for e in pending)
        assert len(completed) >= 1
        assert any(e.id == completed_execution.id for e in completed)

    @pytest.mark.asyncio
    async def test_get_by_status_with_task_filter(self, db_session, task_execution_repository, test_task, test_execution):
        """Test getting executions by status filtered by task."""
        # Act
        result = await task_execution_repository.get_by_status("pending", task_id=test_task.id)

        # Assert
        assert len(result) >= 1
        assert all(e.task_id == test_task.id for e in result)
        assert all(e.status == "pending" for e in result)

    @pytest.mark.asyncio
    async def test_get_by_status_not_found(self, db_session, task_execution_repository):
        """Test getting executions with status that doesn't exist."""
        # Act
        result = await task_execution_repository.get_by_status("nonexistent_status")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_status_with_pagination(self, db_session, task_execution_repository, test_task):
        """Test status filtering with pagination."""
        # Arrange: Create multiple pending executions
        for i in range(5):
            execution = TaskExecutionModel(
                id=uuid4(),
                task_id=test_task.id,
                trigger_type="manual",
                status="pending",
            )
            db_session.add(execution)
        await db_session.commit()

        # Act
        page1 = await task_execution_repository.get_by_status("pending", skip=0, limit=2)
        page2 = await task_execution_repository.get_by_status("pending", skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert all(e.status == "pending" for e in page1)

    # Test: get_by_trigger_type
    @pytest.mark.asyncio
    async def test_get_by_trigger_type(self, db_session, task_execution_repository, test_execution):
        """Test getting executions by trigger type."""
        # Act
        result = await task_execution_repository.get_by_trigger_type("manual")

        # Assert
        assert len(result) >= 1
        assert any(e.id == test_execution.id for e in result)
        assert all(e.trigger_type == "manual" for e in result)

    @pytest.mark.asyncio
    async def test_get_by_trigger_type_not_found(self, db_session, task_execution_repository):
        """Test getting executions with trigger type that doesn't exist."""
        # Act
        result = await task_execution_repository.get_by_trigger_type("nonexistent_trigger")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_trigger_type_with_pagination(self, db_session, task_execution_repository, test_task):
        """Test trigger type filtering with pagination."""
        # Arrange: Create multiple webhook executions
        for i in range(5):
            execution = TaskExecutionModel(
                id=uuid4(),
                task_id=test_task.id,
                trigger_type="webhook",
                status="pending",
            )
            db_session.add(execution)
        await db_session.commit()

        # Act
        page1 = await task_execution_repository.get_by_trigger_type("webhook", skip=0, limit=2)
        page2 = await task_execution_repository.get_by_trigger_type("webhook", skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert all(e.trigger_type == "webhook" for e in page1)

    # Test: get_latest_execution
    @pytest.mark.asyncio
    async def test_get_latest_execution(self, db_session, task_execution_repository, test_task):
        """Test getting the latest execution for a task."""
        # Arrange: Create executions with different timestamps
        old_execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="completed",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        latest_execution = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="running",
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_execution, latest_execution])
        await db_session.commit()

        # Act
        result = await task_execution_repository.get_latest_execution(test_task.id)

        # Assert
        assert result is not None
        assert result.id == latest_execution.id

    @pytest.mark.asyncio
    async def test_get_latest_execution_not_found(self, db_session, task_execution_repository):
        """Test getting latest execution for task with no executions."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        result = await task_execution_repository.get_latest_execution(non_existent_task_id)

        # Assert
        assert result is None

    # Test: get_successful_executions
    @pytest.mark.asyncio
    async def test_get_successful_executions(self, db_session, task_execution_repository, test_task, completed_execution):
        """Test getting successful executions for a task."""
        # Act
        result = await task_execution_repository.get_successful_executions(test_task.id)

        # Assert
        assert len(result) >= 1
        assert any(e.id == completed_execution.id for e in result)
        assert all(e.status == "completed" for e in result)

    @pytest.mark.asyncio
    async def test_get_successful_executions_ordered_by_completed_desc(self, db_session, task_execution_repository, test_task):
        """Test successful executions are ordered by completed_at descending."""
        # Arrange: Create completed executions with different completion times
        old_completed = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="completed",
            completed_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_completed = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="completed",
            completed_at=datetime.utcnow(),
        )
        db_session.add_all([old_completed, new_completed])
        await db_session.commit()

        # Act
        result = await task_execution_repository.get_successful_executions(test_task.id)

        # Assert
        assert len(result) >= 2
        new_idx = next(i for i, e in enumerate(result) if e.id == new_completed.id)
        old_idx = next(i for i, e in enumerate(result) if e.id == old_completed.id)
        assert new_idx < old_idx

    @pytest.mark.asyncio
    async def test_get_successful_executions_with_limit(self, db_session, task_execution_repository, test_task):
        """Test getting successful executions with limit."""
        # Arrange: Create multiple completed executions
        for i in range(5):
            execution = TaskExecutionModel(
                id=uuid4(),
                task_id=test_task.id,
                trigger_type="manual",
                status="completed",
                completed_at=datetime.utcnow() - timedelta(minutes=i),
            )
            db_session.add(execution)
        await db_session.commit()

        # Act
        result = await task_execution_repository.get_successful_executions(test_task.id, limit=2)

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_successful_executions_empty(self, db_session, task_execution_repository):
        """Test getting successful executions for task with none."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        result = await task_execution_repository.get_successful_executions(non_existent_task_id)

        # Assert
        assert result == []

    # Test: get_failed_executions
    @pytest.mark.asyncio
    async def test_get_failed_executions(self, db_session, task_execution_repository, test_task, failed_execution):
        """Test getting failed executions for a task."""
        # Act
        result = await task_execution_repository.get_failed_executions(test_task.id)

        # Assert
        assert len(result) >= 1
        assert any(e.id == failed_execution.id for e in result)
        assert all(e.status == "failed" for e in result)

    @pytest.mark.asyncio
    async def test_get_failed_executions_with_limit(self, db_session, task_execution_repository, test_task):
        """Test getting failed executions with limit."""
        # Arrange: Create multiple failed executions
        for i in range(5):
            execution = TaskExecutionModel(
                id=uuid4(),
                task_id=test_task.id,
                trigger_type="manual",
                status="failed",
                error_message=f"Error {i}",
            )
            db_session.add(execution)
        await db_session.commit()

        # Act
        result = await task_execution_repository.get_failed_executions(test_task.id, limit=2)

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_failed_executions_empty(self, db_session, task_execution_repository):
        """Test getting failed executions for task with none."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        result = await task_execution_repository.get_failed_executions(non_existent_task_id)

        # Assert
        assert result == []

    # Test: update_status
    @pytest.mark.asyncio
    async def test_update_status_to_running(self, db_session, task_execution_repository, test_execution):
        """Test updating execution status to running."""
        # Act
        success = await task_execution_repository.update_status(test_execution.id, "running")
        await db_session.refresh(test_execution)

        # Assert
        assert success is True
        assert test_execution.status == "running"
        assert test_execution.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_completed(self, db_session, task_execution_repository, test_execution):
        """Test updating execution status to completed."""
        # Arrange
        result_data = {"output": "Task completed successfully"}

        # Act
        success = await task_execution_repository.update_status(
            test_execution.id,
            "completed",
            result_data=result_data
        )
        await db_session.refresh(test_execution)

        # Assert
        assert success is True
        assert test_execution.status == "completed"
        assert test_execution.completed_at is not None
        assert test_execution.result_data == result_data

    @pytest.mark.asyncio
    async def test_update_status_to_failed_with_error(self, db_session, task_execution_repository, test_execution):
        """Test updating execution status to failed with error message."""
        # Act
        success = await task_execution_repository.update_status(
            test_execution.id,
            "failed",
            error_message="Task execution failed"
        )
        await db_session.refresh(test_execution)

        # Assert
        assert success is True
        assert test_execution.status == "failed"
        assert test_execution.error_message == "Task execution failed"
        assert test_execution.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_cancelled(self, db_session, task_execution_repository, test_execution):
        """Test updating execution status to cancelled."""
        # Act
        success = await task_execution_repository.update_status(test_execution.id, "cancelled")
        await db_session.refresh(test_execution)

        # Assert
        assert success is True
        assert test_execution.status == "cancelled"
        assert test_execution.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, db_session, task_execution_repository):
        """Test updating status of non-existent execution."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await task_execution_repository.update_status(non_existent_id, "completed")

        # Assert
        assert success is False

    # Test: set_report
    @pytest.mark.asyncio
    async def test_set_report(self, db_session, task_execution_repository, test_execution):
        """Test linking a report to an execution."""
        # Arrange
        report_id = uuid4()

        # Act
        success = await task_execution_repository.set_report(test_execution.id, report_id)
        await db_session.refresh(test_execution)

        # Assert
        assert success is True
        assert test_execution.report_id == report_id

    @pytest.mark.asyncio
    async def test_set_report_not_found(self, db_session, task_execution_repository):
        """Test linking report to non-existent execution."""
        # Arrange
        non_existent_id = uuid4()
        report_id = uuid4()

        # Act
        success = await task_execution_repository.set_report(non_existent_id, report_id)

        # Assert
        assert success is False

    # Test: count_by_task
    @pytest.mark.asyncio
    async def test_count_by_task(self, db_session, task_execution_repository, test_task, test_execution, completed_execution):
        """Test counting executions for a task."""
        # Act
        count = await task_execution_repository.count_by_task(test_task.id)

        # Assert
        assert count >= 2

    @pytest.mark.asyncio
    async def test_count_by_task_empty(self, db_session, task_execution_repository):
        """Test counting executions for task with none."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        count = await task_execution_repository.count_by_task(non_existent_task_id)

        # Assert
        assert count == 0

    # Test: get_execution_stats
    @pytest.mark.asyncio
    async def test_get_execution_stats(self, db_session, task_execution_repository, test_task):
        """Test getting execution statistics for a task."""
        # Arrange: Create executions with different statuses
        completed_exec = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="completed",
            duration_seconds=100,
        )
        failed_exec = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="failed",
            duration_seconds=50,
        )
        cancelled_exec = TaskExecutionModel(
            id=uuid4(),
            task_id=test_task.id,
            trigger_type="manual",
            status="cancelled",
        )
        db_session.add_all([completed_exec, failed_exec, cancelled_exec])
        await db_session.commit()

        # Act
        stats = await task_execution_repository.get_execution_stats(test_task.id)

        # Assert
        assert stats["total"] >= 3
        assert stats["completed"] >= 1
        assert stats["failed"] >= 1
        assert stats["cancelled"] >= 1
        assert stats["avg_duration_seconds"] is not None

    @pytest.mark.asyncio
    async def test_get_execution_stats_empty(self, db_session, task_execution_repository):
        """Test getting execution statistics for task with no executions."""
        # Arrange
        non_existent_task_id = uuid4()

        # Act
        stats = await task_execution_repository.get_execution_stats(non_existent_task_id)

        # Assert
        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["cancelled"] == 0
        assert stats["avg_duration_seconds"] is None

    # Test: update (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_update_execution(self, db_session, task_execution_repository, test_execution):
        """Test updating an execution."""
        # Act
        updated = await task_execution_repository.update(
            test_execution.id,
            total_messages=10,
            total_tool_calls=5
        )

        # Assert
        assert updated is not None
        assert updated.total_messages == 10
        assert updated.total_tool_calls == 5

    # Test: delete (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_delete_execution(self, db_session, task_execution_repository, test_execution):
        """Test deleting an execution."""
        # Arrange
        execution_id = test_execution.id

        # Act
        success = await task_execution_repository.delete(execution_id)

        # Assert
        assert success is True
        deleted = await task_execution_repository.get_by_id(execution_id)
        assert deleted is None
