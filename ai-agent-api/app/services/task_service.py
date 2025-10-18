"""Task service for business logic."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.task import Task
from app.domain.exceptions import TaskNotFoundError, PermissionDeniedError, ValidationError
from app.repositories.task_repository import TaskRepository
from app.repositories.task_execution_repository import TaskExecutionRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class TaskService:
    """Business logic for task management and execution."""

    def __init__(
        self,
        db: AsyncSession,
        task_repo: TaskRepository,
        task_execution_repo: TaskExecutionRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.task_repo = task_repo
        self.task_execution_repo = task_execution_repo
        self.user_repo = user_repo
        self.audit_service = audit_service

    async def create_task(
        self,
        user_id: UUID,
        name: str,
        prompt_template: str,
        allowed_tools: list[str],
        sdk_options: dict,
        description: Optional[str] = None,
        disallowed_tools: Optional[list[str]] = None,
        is_scheduled: bool = False,
        schedule_cron: Optional[str] = None,
        generate_report: bool = False,
        report_format: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task."""
        # Create task entity
        task = Task(
            id=uuid4(),
            user_id=user_id,
            name=name,
            prompt_template=prompt_template,
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
        )
        
        task.description = description
        task.disallowed_tools = disallowed_tools or []
        task.is_scheduled = is_scheduled
        task.schedule_cron = schedule_cron
        task.generate_report = generate_report
        task.report_format = report_format
        task.tags = tags or []
        
        # Validate
        if is_scheduled:
            task.validate_schedule()
        if generate_report:
            task.validate_report_format()
        
        # Persist
        from app.models.task import TaskModel
        task_model = TaskModel(
            id=task.id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            prompt_template=task.prompt_template,
            default_variables=None,
            allowed_tools=task.allowed_tools,
            disallowed_tools=task.disallowed_tools,
            sdk_options=task.sdk_options,
            working_directory_path=task.working_directory_path,
            is_scheduled=task.is_scheduled,
            schedule_cron=task.schedule_cron,
            schedule_enabled=False,
            generate_report=task.generate_report,
            report_format=task.report_format,
            notification_config=task.notification_config,
            tags=task.tags,
            is_public=task.is_public,
            is_active=task.is_active,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        
        self.db.add(task_model)
        await self.db.flush()
        await self.db.commit()
        
        # Audit log
        await self.audit_service.log_task_created(
            task_id=task.id,
            user_id=user_id,
            name=name,
            prompt_template=prompt_template,
        )
        
        return task

    async def execute_task(
        self,
        task_id: str,
        trigger_type: str = "manual",
        variables: Optional[dict] = None,
    ):
        """Execute a task by creating a session and running the prompt template.
        
        Args:
            task_id: Task UUID
            trigger_type: "manual", "scheduled", or "webhook"
            variables: Variables to substitute in prompt template
            
        Returns:
            TaskExecution entity
            
        Raises:
            TaskNotFoundError: Task doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Task not ready for execution
        """
        from app.domain.entities.task_execution import TaskExecution, TaskExecutionStatus
        from app.services.sdk_session_service import SDKIntegratedSessionService
        from app.services.storage_manager import StorageManager
        from app.repositories.session_repository import SessionRepository
        from app.repositories.message_repository import MessageRepository
        from app.repositories.tool_call_repository import ToolCallRepository
        from uuid import uuid4
        
        # 1. Get and validate task
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        if not task.is_active:
            raise ValidationError("Task is not active")
        
        # 2. Create task execution record
        execution = TaskExecution(
            id=uuid4(),
            task_id=task.id,
            user_id=task.user_id,
            trigger_type=trigger_type,
            variables=variables or {},
            status=TaskExecutionStatus.PENDING,
        )
        
        # Persist execution record
        from app.models.task_execution import TaskExecutionModel
        execution_model = TaskExecutionModel(
            id=execution.id,
            task_id=execution.task_id,
            user_id=execution.user_id,
            trigger_type=execution.trigger_type,
            variables=execution.variables,
            status=execution.status.value,
            started_at=execution.started_at,
        )
        self.db.add(execution_model)
        await self.db.flush()
        await self.db.commit()
        
        try:
            # 3. Create session for task execution
            session_service = SDKIntegratedSessionService(
                db=self.db,
                session_repo=SessionRepository(self.db),
                message_repo=MessageRepository(self.db),
                tool_call_repo=ToolCallRepository(self.db),
                user_repo=self.user_repo,
                storage_manager=StorageManager(),
                audit_service=self.audit_service,
            )
            
            # Build session name
            session_name = f"Task: {task.name} ({trigger_type})"
            
            # Use task's SDK options (already includes MCP config when session created)
            session = await session_service.create_session(
                user_id=task.user_id,
                name=session_name,
                description=f"Automated execution of task '{task.name}'",
                sdk_options=task.sdk_options,
            )
            
            # Update execution with session ID
            execution.session_id = session.id
            execution.status = TaskExecutionStatus.RUNNING
            await self.task_execution_repo.update(
                str(execution.id),
                session_id=session.id,
                status=TaskExecutionStatus.RUNNING.value,
            )
            await self.db.commit()
            
            # 4. Render prompt template with variables
            rendered_prompt = self._render_prompt_template(
                task.prompt_template,
                variables or {},
            )
            
            # 5. Send message through session
            # This will create the SDK client, send to Claude, and process responses
            message = await session_service.send_message(
                session_id=str(session.id),
                message_content=rendered_prompt,
            )
            
            # 6. Mark execution as completed
            execution.status = TaskExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.result_message_id = message.id
            
            await self.task_execution_repo.update(
                str(execution.id),
                status=TaskExecutionStatus.COMPLETED.value,
                completed_at=execution.completed_at,
                result_message_id=message.id,
            )
            
            # 7. Generate report if requested
            if task.generate_report:
                from app.services.report_service import ReportService
                from app.repositories.report_repository import ReportRepository
                
                report_service = ReportService(
                    db=self.db,
                    report_repo=ReportRepository(self.db),
                    session_repo=SessionRepository(self.db),
                    storage_manager=StorageManager(),
                )
                
                report = await report_service.generate_from_session(
                    session_id=session.id,
                    user_id=task.user_id,
                    title=f"Task Execution Report: {task.name}",
                    format=task.report_format or "html",
                    auto_generated=True,
                )
                
                execution.report_id = report.id
                await self.task_execution_repo.update(
                    str(execution.id),
                    report_id=report.id,
                )
            
            await self.db.commit()
            
            # 8. Audit log
            await self.audit_service.log_task_executed(
                task_id=task.id,
                execution_id=execution.id,
                user_id=task.user_id,
                trigger_type=trigger_type,
                status="completed",
            )
            
            return execution
            
        except Exception as e:
            # Mark execution as failed
            execution.status = TaskExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)
            
            await self.task_execution_repo.update(
                str(execution.id),
                status=TaskExecutionStatus.FAILED.value,
                completed_at=execution.completed_at,
                error_message=str(e),
            )
            await self.db.commit()
            
            # Audit log error
            await self.audit_service.log_task_executed(
                task_id=task.id,
                execution_id=execution.id,
                user_id=task.user_id,
                trigger_type=trigger_type,
                status="failed",
                error=str(e),
            )
            
            raise
    
    def _render_prompt_template(self, template: str, variables: dict) -> str:
        """Render prompt template with variables.
        
        Simple variable substitution using {variable_name} syntax.
        
        Args:
            template: Prompt template string
            variables: Variables to substitute
            
        Returns:
            Rendered prompt string
            
        Example:
            >>> template = "Analyze the {environment} deployment status"
            >>> variables = {"environment": "production"}
            >>> result = "Analyze the production deployment status"
        """
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        # Replace {variable_name} with values
        rendered = re.sub(r'\{(\w+)\}', replace_var, template)
        return rendered

    async def get_task(self, task_id: UUID, user_id: UUID) -> Task:
        """Get task by ID with authorization check."""
        task_model = await self.task_repo.get_by_id(task_id)
        if not task_model:
            raise TaskNotFoundError(f"Task {task_id} not found")
        
        # Check authorization
        if task_model.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin() and not task_model.is_public:
                raise PermissionDeniedError("Not authorized to access this task")
        
        return self._model_to_entity(task_model)

    async def list_tasks(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_public: bool = True,
    ) -> list[Task]:
        """List tasks for a user."""
        task_models = await self.task_repo.get_by_user(user_id, skip, limit)
        tasks = [self._model_to_entity(model) for model in task_models]
        
        # Optionally include public tasks
        if include_public:
            public_models = await self.task_repo.get_public_tasks(0, limit)
            public_tasks = [
                self._model_to_entity(model) 
                for model in public_models 
                if model.user_id != user_id
            ]
            tasks.extend(public_tasks)
        
        return tasks

    async def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        **updates,
    ) -> Task:
        """Update a task."""
        task = await self.get_task(task_id, user_id)
        
        # Only owner can update
        if task.user_id != user_id:
            raise PermissionDeniedError("Only task owner can update")
        
        # Update entity
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.utcnow()
        
        # Validate if needed
        if task.is_scheduled:
            task.validate_schedule()
        if task.generate_report:
            task.validate_report_format()
        
        # Update in database
        await self.task_repo.update(task_id, updated_at=task.updated_at, **updates)
        await self.db.commit()
        
        return task

    async def delete_task(self, task_id: UUID, user_id: UUID) -> bool:
        """Soft delete a task."""
        task = await self.get_task(task_id, user_id)
        
        # Only owner can delete
        if task.user_id != user_id:
            raise PermissionDeniedError("Only task owner can delete")
        
        success = await self.task_repo.soft_delete(task_id)
        await self.db.commit()
        return success

    async def enable_schedule(self, task_id: UUID, user_id: UUID) -> Task:
        """Enable task schedule."""
        task = await self.get_task(task_id, user_id)
        
        if not task.is_scheduled:
            raise ValidationError("Task is not configured for scheduling")
        
        task.validate_schedule()
        
        await self.task_repo.enable_schedule(task_id)
        await self.db.commit()
        
        task.schedule_enabled = True
        return task

    async def disable_schedule(self, task_id: UUID, user_id: UUID) -> Task:
        """Disable task schedule."""
        task = await self.get_task(task_id, user_id)
        
        await self.task_repo.disable_schedule(task_id)
        await self.db.commit()
        
        task.schedule_enabled = False
        return task

    async def get_scheduled_tasks(self) -> list[Task]:
        """Get all enabled scheduled tasks."""
        task_models = await self.task_repo.get_scheduled_tasks(enabled_only=True)
        return [self._model_to_entity(model) for model in task_models]

    async def get_task_executions(
        self,
        task_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """Get execution history for a task."""
        # Verify access
        await self.get_task(task_id, user_id)
        
        executions = await self.task_execution_repo.get_by_task(task_id, skip, limit)
        return executions

    async def get_task_statistics(self, task_id: UUID, user_id: UUID) -> dict:
        """Get execution statistics for a task."""
        # Verify access
        await self.get_task(task_id, user_id)
        
        stats = await self.task_execution_repo.get_execution_stats(task_id)
        return stats

    def _model_to_entity(self, model) -> Task:
        """Convert database model to domain entity."""
        task = Task(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            prompt_template=model.prompt_template,
            allowed_tools=model.allowed_tools,
            sdk_options=model.sdk_options,
        )
        
        task.description = model.description
        task.disallowed_tools = model.disallowed_tools or []
        task.working_directory_path = model.working_directory_path
        task.is_scheduled = model.is_scheduled
        task.schedule_cron = model.schedule_cron
        task.schedule_enabled = model.schedule_enabled
        task.generate_report = model.generate_report
        task.report_format = model.report_format
        task.notification_config = model.notification_config
        task.tags = model.tags or []
        task.is_public = model.is_public
        task.is_active = model.is_active
        task.is_deleted = model.is_deleted
        task.created_at = model.created_at
        task.updated_at = model.updated_at
        task.deleted_at = model.deleted_at
        
        return task
