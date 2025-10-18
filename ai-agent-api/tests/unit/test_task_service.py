"""Unit tests for TaskService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.task_service import TaskService
from app.domain.exceptions import TaskNotFoundError, ValidationError
from app.models.task import TaskModel


class TestTaskService:
    """Test cases for TaskService."""

    @pytest.fixture
    def task_service(self, db_session, mock_audit_service):
        """Create TaskService with mocked dependencies."""
        from app.repositories.task_repository import TaskRepository
        from app.repositories.task_execution_repository import TaskExecutionRepository
        from app.repositories.user_repository import UserRepository
        
        return TaskService(
            db=db_session,
            task_repo=TaskRepository(db_session),
            task_execution_repo=TaskExecutionRepository(db_session),
            user_repo=UserRepository(db_session),
            audit_service=mock_audit_service,
        )

    @pytest.mark.asyncio
    async def test_create_task_success(
        self,
        task_service,
        test_user,
        mock_audit_service,
    ):
        """Test successful task creation."""
        # Arrange
        user_id = test_user.id
        name = "Test Automation Task"
        prompt_template = "Analyze the {environment} system status"
        allowed_tools = ["Bash", "mcp__kubernetes_readonly__list_pods"]
        sdk_options = {
            "model": "claude-sonnet-4-5",
            "max_turns": 5,
            "permission_mode": "default",
        }
        
        # Act
        task = await task_service.create_task(
            user_id=user_id,
            name=name,
            prompt_template=prompt_template,
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
            description="Test task for automation",
            is_scheduled=False,
            generate_report=True,
            report_format="html",
        )
        
        # Assert
        assert task is not None
        assert task.user_id == user_id
        assert task.name == name
        assert task.prompt_template == prompt_template
        assert task.allowed_tools == allowed_tools
        assert task.generate_report is True
        assert task.report_format == "html"
        
        # Verify audit logging
        mock_audit_service.log_task_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_scheduled_task_with_cron(
        self,
        task_service,
        test_user,
    ):
        """Test creating scheduled task with cron expression."""
        # Arrange
        user_id = test_user.id
        name = "Daily Health Check"
        prompt_template = "Check system health and report any issues"
        allowed_tools = ["Bash", "mcp__monitoring__get_system_metrics"]
        sdk_options = {"model": "claude-sonnet-4-5"}
        
        # Act
        task = await task_service.create_task(
            user_id=user_id,
            name=name,
            prompt_template=prompt_template,
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
            is_scheduled=True,
            schedule_cron="0 9 * * *",  # Daily at 9 AM
        )
        
        # Assert
        assert task.is_scheduled is True
        assert task.schedule_cron == "0 9 * * *"

    @pytest.mark.asyncio
    async def test_execute_task_success(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test successful task execution."""
        # Arrange - Create a task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Execution Task",
            prompt_template="List files in the current directory",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        # Mock the SDKIntegratedSessionService and related components
        with patch('app.services.task_service.SDKIntegratedSessionService') as mock_service_class:
            mock_session_service = AsyncMock()
            mock_service_class.return_value = mock_session_service
            
            # Mock session creation
            mock_session = AsyncMock()
            mock_session.id = uuid4()
            mock_session_service.create_session.return_value = mock_session
            
            # Mock message sending
            mock_message = AsyncMock()
            mock_message.id = uuid4()
            mock_session_service.send_message.return_value = mock_message
            
            # Act
            execution = await task_service.execute_task(
                task_id=str(task.id),
                trigger_type="manual",
                variables={},
            )
            
            # Assert
            assert execution is not None
            assert execution.task_id == task.id
            assert execution.user_id == test_user.id
            assert execution.trigger_type == "manual"
            assert execution.session_id == mock_session.id
            assert execution.result_message_id == mock_message.id
            
            # Verify session was created
            mock_session_service.create_session.assert_called_once()
            
            # Verify message was sent
            mock_session_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_with_variables(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test task execution with template variables."""
        # Arrange - Create task with template
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Parameterized Task",
            prompt_template="Check the status of {service} in {environment}",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        variables = {
            "service": "nginx",
            "environment": "production",
        }
        
        with patch('app.services.task_service.SDKIntegratedSessionService') as mock_service_class:
            mock_session_service = AsyncMock()
            mock_service_class.return_value = mock_session_service
            
            mock_session = AsyncMock()
            mock_session.id = uuid4()
            mock_session_service.create_session.return_value = mock_session
            
            mock_message = AsyncMock()
            mock_message.id = uuid4()
            mock_session_service.send_message.return_value = mock_message
            
            # Act
            execution = await task_service.execute_task(
                task_id=str(task.id),
                trigger_type="scheduled",
                variables=variables,
            )
            
            # Assert
            assert execution.variables == variables
            
            # Verify rendered prompt was sent
            expected_prompt = "Check the status of nginx in production"
            mock_session_service.send_message.assert_called_once()
            call_args = mock_session_service.send_message.call_args
            assert call_args[1]["message_content"] == expected_prompt

    @pytest.mark.asyncio
    async def test_execute_task_with_report_generation(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test task execution with report generation."""
        # Arrange - Create task with report generation enabled
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Task with Report",
            prompt_template="Generate system report",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
            generate_report=True,
            report_format="html",
        )
        db_session.add(task)
        await db_session.commit()
        
        with patch('app.services.task_service.SDKIntegratedSessionService') as mock_service_class:
            with patch('app.services.task_service.ReportService') as mock_report_service_class:
                mock_session_service = AsyncMock()
                mock_service_class.return_value = mock_session_service
                
                mock_session = AsyncMock()
                mock_session.id = uuid4()
                mock_session_service.create_session.return_value = mock_session
                
                mock_message = AsyncMock()
                mock_message.id = uuid4()
                mock_session_service.send_message.return_value = mock_message
                
                # Mock report service
                mock_report_service = AsyncMock()
                mock_report_service_class.return_value = mock_report_service
                
                mock_report = AsyncMock()
                mock_report.id = uuid4()
                mock_report_service.generate_from_session.return_value = mock_report
                
                # Act
                execution = await task_service.execute_task(
                    task_id=str(task.id),
                    trigger_type="manual",
                )
                
                # Assert
                assert execution.report_id == mock_report.id
                
                # Verify report was generated
                mock_report_service.generate_from_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_not_found(
        self,
        task_service,
    ):
        """Test task execution with non-existent task."""
        # Act & Assert
        with pytest.raises(TaskNotFoundError):
            await task_service.execute_task(
                task_id=str(uuid4()),
                trigger_type="manual",
            )

    @pytest.mark.asyncio
    async def test_execute_task_inactive(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test task execution with inactive task."""
        # Arrange - Create inactive task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Inactive Task",
            prompt_template="Test prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=False,  # Inactive
        )
        db_session.add(task)
        await db_session.commit()
        
        # Act & Assert
        with pytest.raises(ValidationError, match="not active"):
            await task_service.execute_task(
                task_id=str(task.id),
                trigger_type="manual",
            )

    @pytest.mark.asyncio
    async def test_execute_task_handles_error(
        self,
        task_service,
        test_user,
        db_session,
        mock_audit_service,
    ):
        """Test task execution error handling."""
        # Arrange - Create task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Failing Task",
            prompt_template="This will fail",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        # Mock service to raise exception
        with patch('app.services.task_service.SDKIntegratedSessionService') as mock_service_class:
            mock_session_service = AsyncMock()
            mock_service_class.return_value = mock_session_service
            
            mock_session = AsyncMock()
            mock_session.id = uuid4()
            mock_session_service.create_session.return_value = mock_session
            
            # Make send_message raise exception
            mock_session_service.send_message.side_effect = Exception("SDK Error")
            
            # Act & Assert
            with pytest.raises(Exception, match="SDK Error"):
                await task_service.execute_task(
                    task_id=str(task.id),
                    trigger_type="manual",
                )
            
            # Verify error audit logging
            mock_audit_service.log_task_executed.assert_called()
            call_args = mock_audit_service.log_task_executed.call_args
            assert call_args[1]["status"] == "failed"

    def test_render_prompt_template(self, task_service):
        """Test prompt template rendering with variables."""
        # Test basic substitution
        template = "Check {service} status in {environment}"
        variables = {"service": "nginx", "environment": "production"}
        
        result = task_service._render_prompt_template(template, variables)
        assert result == "Check nginx status in production"
        
        # Test missing variable (should leave placeholder)
        template = "Check {service} and {missing_var}"
        variables = {"service": "apache"}
        
        result = task_service._render_prompt_template(template, variables)
        assert result == "Check apache and {missing_var}"
        
        # Test no variables
        template = "Simple template without variables"
        variables = {}
        
        result = task_service._render_prompt_template(template, variables)
        assert result == "Simple template without variables"

    @pytest.mark.asyncio
    async def test_get_task_success(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test successful task retrieval."""
        # Arrange - Create task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Task",
            prompt_template="Test prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        # Act
        retrieved_task = await task_service.get_task(task.id, test_user.id)
        
        # Assert
        assert retrieved_task.id == task.id
        assert retrieved_task.name == task.name

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test successful task update."""
        # Arrange - Create task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Original Name",
            prompt_template="Original prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        # Act
        updates = {
            "name": "Updated Name",
            "description": "Updated description",
        }
        
        updated_task = await task_service.update_task(task.id, test_user.id, updates)
        
        # Assert
        assert updated_task.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test successful task deletion."""
        # Arrange - Create task
        task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Task to Delete",
            prompt_template="Test prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_active=True,
        )
        db_session.add(task)
        await db_session.commit()
        
        # Act
        result = await task_service.delete_task(task.id, test_user.id)
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_get_scheduled_tasks(
        self,
        task_service,
        test_user,
        db_session,
    ):
        """Test getting scheduled tasks."""
        # Arrange - Create scheduled and unscheduled tasks
        scheduled_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Scheduled Task",
            prompt_template="Scheduled prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_scheduled=True,
            schedule_enabled=True,
            schedule_cron="0 * * * *",
        )
        
        unscheduled_task = TaskModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Manual Task",
            prompt_template="Manual prompt",
            allowed_tools=["Bash"],
            sdk_options={"model": "claude-sonnet-4-5"},
            is_scheduled=False,
        )
        
        db_session.add_all([scheduled_task, unscheduled_task])
        await db_session.commit()
        
        # Act
        scheduled_tasks = await task_service.get_scheduled_tasks()
        
        # Assert
        assert len(scheduled_tasks) == 1
        assert scheduled_tasks[0].name == "Scheduled Task"