"""Background task execution via Celery.

Handles asynchronous execution of user-defined tasks using Claude Code CLI.
Integrates with existing TaskService and SDKIntegratedSessionService.

Flow:
1. API queues task to Celery (returns immediately)
2. Celery worker picks up task
3. Worker executes via TaskService (reuses existing logic)
4. Updates database with results
5. Handles errors and retries
"""

import asyncio
from typing import Optional, Dict
from celery import Task
from celery.utils.log import get_task_logger
from datetime import datetime

from app.celery_app import celery_app
from app.core.logging import get_logger

# Celery's task logger
task_logger = get_task_logger(__name__)
# Our structured application logger
app_logger = get_logger(__name__)


class TaskExecutionTask(Task):
    """Custom Task class with error handling and lifecycle management.

    Features:
    - Automatic retry on failure
    - Exponential backoff with jitter
    - Comprehensive error logging
    - Database status updates on failure
    """

    autoretry_for = (Exception,)  # Retry on any exception
    retry_kwargs = {"max_retries": 3, "countdown": 60}  # Wait 60s between retries
    retry_backoff = True  # Exponential backoff: 60s, 120s, 240s
    retry_jitter = True  # Add randomness to prevent thundering herd

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries exhausted."""
        execution_id = kwargs.get("execution_id") or (args[0] if args else None)

        app_logger.error(
            "Task execution failed after all retries",
            extra={
                "celery_task_id": task_id,
                "execution_id": execution_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "retry_count": self.request.retries,
                "max_retries": self.max_retries,
                "event": "task_execution_failed",
            },
            exc_info=einfo,
        )

        # Update execution status in database
        if execution_id:
            try:
                asyncio.run(self._mark_execution_failed(execution_id, str(exc)))
            except Exception as e:
                app_logger.error(
                    f"Failed to update execution status: {e}",
                    extra={"execution_id": execution_id}
                )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is being retried."""
        execution_id = kwargs.get("execution_id") or (args[0] if args else None)

        app_logger.warning(
            "Task execution retry scheduled",
            extra={
                "celery_task_id": task_id,
                "execution_id": execution_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "retry_count": self.request.retries + 1,
                "max_retries": self.max_retries,
                "event": "task_execution_retry",
            }
        )

    async def _mark_execution_failed(self, execution_id: str, error_message: str):
        """Mark execution as failed in database."""
        from app.database.session import get_async_session_context
        from app.repositories.task_execution_repository import TaskExecutionRepository

        async with get_async_session_context() as db:
            repo = TaskExecutionRepository(db)
            await repo.update(
                execution_id,
                status="failed",
                error_message=error_message[:1000],  # Truncate long errors
                completed_at=datetime.utcnow(),
            )
            await db.commit()


@celery_app.task(
    bind=True,
    base=TaskExecutionTask,
    name="app.celery_tasks.task_execution.execute_task_async",
    queue="task_execution",
    track_started=True,
)
def execute_task_async(
    self,
    execution_id: str,
    task_id: str,
    user_id: str,
    variables: Optional[Dict] = None,
):
    """Execute a task asynchronously in background.

    This Celery task wraps the synchronous task execution logic,
    providing retry, error handling, and monitoring capabilities.

    Args:
        execution_id: TaskExecution UUID
        task_id: Task UUID
        user_id: User UUID
        variables: Variables for prompt template substitution

    Returns:
        Dict with execution results:
        {
            "status": "completed" | "failed",
            "execution_id": str,
            "session_id": str | None,
            "duration_seconds": int,
            "error": str | None,
        }

    Raises:
        Exception: Any error during execution (will trigger retry mechanism)
    """
    app_logger.info(
        "Starting background task execution",
        extra={
            "celery_task_id": self.request.id,
            "execution_id": execution_id,
            "task_id": task_id,
            "user_id": user_id,
            "worker_hostname": self.request.hostname,
            "retry_count": self.request.retries,
            "event": "task_execution_start",
        }
    )

    # Run async implementation
    result = asyncio.run(
        _execute_task_impl(
            execution_id=execution_id,
            task_id=task_id,
            user_id=user_id,
            variables=variables or {},
            celery_task_id=self.request.id,
            worker_hostname=self.request.hostname,
        )
    )

    app_logger.info(
        "Background task execution completed",
        extra={
            "celery_task_id": self.request.id,
            "execution_id": execution_id,
            "task_id": task_id,
            "status": result.get("status"),
            "duration_seconds": result.get("duration_seconds"),
            "event": "task_execution_complete",
        }
    )

    return result


async def _execute_task_impl(
    execution_id: str,
    task_id: str,
    user_id: str,
    variables: Dict,
    celery_task_id: str,
    worker_hostname: str,
) -> Dict:
    """Internal async implementation of task execution.

    Separated from Celery task wrapper for testability.
    Reuses existing service layer logic.

    Returns:
        Dict with execution results
    """
    from app.database.session import get_async_session_context
    from app.repositories.task_repository import TaskRepository
    from app.repositories.task_execution_repository import TaskExecutionRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.session_repository import SessionRepository
    from app.repositories.message_repository import MessageRepository
    from app.repositories.tool_call_repository import ToolCallRepository
    from app.repositories.mcp_server_repository import MCPServerRepository
    from app.services.sdk_session_service import SDKIntegratedSessionService
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService
    from app.services.report_service import ReportService
    from app.repositories.report_repository import ReportRepository
    from app.claude_sdk import ClaudeSDKClientManager, PermissionService
    from app.infrastructure.redis_client import RedisClient
    from app.claude_sdk.monitoring.event_broadcaster import EventBroadcaster

    start_time = datetime.utcnow()

    async with get_async_session_context() as db:
        # Initialize repositories
        task_repo = TaskRepository(db)
        task_execution_repo = TaskExecutionRepository(db)
        user_repo = UserRepository(db)
        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        tool_call_repo = ToolCallRepository(db)
        mcp_server_repo = MCPServerRepository(db)
        report_repo = ReportRepository(db)

        # Initialize services
        audit_service = AuditService(db)
        storage_manager = StorageManager()

        # SDK components
        sdk_client_manager = ClaudeSDKClientManager()
        permission_service = PermissionService(
            db=db,
            user_repo=user_repo,
            session_repo=session_repo,
            mcp_server_repo=mcp_server_repo,
            audit_service=audit_service,
        )
        redis_client = RedisClient()
        event_broadcaster = EventBroadcaster(redis_client)

        # Session service (reuses existing logic!)
        session_service = SDKIntegratedSessionService(
            db=db,
            session_repo=session_repo,
            message_repo=message_repo,
            tool_call_repo=tool_call_repo,
            user_repo=user_repo,
            mcp_server_repo=mcp_server_repo,
            storage_manager=storage_manager,
            audit_service=audit_service,
            sdk_client_manager=sdk_client_manager,
            permission_service=permission_service,
            event_broadcaster=event_broadcaster,
        )

        try:
            # 1. Get task
            task = await task_repo.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            app_logger.info(
                "Task loaded",
                extra={
                    "execution_id": execution_id,
                    "task_name": task.name,
                }
            )

            # 2. Update execution status to RUNNING
            await task_execution_repo.update(
                execution_id,
                status="running",
                celery_task_id=celery_task_id,
                worker_hostname=worker_hostname,
                started_at=start_time,
            )
            await db.commit()

            app_logger.info(
                "Execution status updated to RUNNING",
                extra={"execution_id": execution_id}
            )

            # 3. Create session for task execution
            session_name = f"Task: {task.name} (manual)"
            session = await session_service.create_session(
                user_id=user_id,
                name=session_name,
                description=f"Automated execution of task '{task.name}'",
                sdk_options=task.sdk_options,
            )

            app_logger.info(
                "Session created for task execution",
                extra={
                    "execution_id": execution_id,
                    "session_id": str(session.id),
                    "working_directory": session.working_directory_path,
                }
            )

            # 4. Update execution with session ID
            await task_execution_repo.update(
                execution_id,
                session_id=session.id,
            )
            await db.commit()

            # 5. Render prompt template with variables
            rendered_prompt = _render_prompt_template(
                task.prompt_template,
                variables,
            )

            app_logger.info(
                "Prompt template rendered",
                extra={
                    "execution_id": execution_id,
                    "prompt_length": len(rendered_prompt),
                }
            )

            # 6. Send message through session (REUSES EXISTING LOGIC!)
            app_logger.info(
                "Sending message to Claude Code",
                extra={
                    "execution_id": execution_id,
                    "session_id": str(session.id),
                }
            )

            last_message = None
            async for message in session_service.send_message(
                session_id=session.id,
                user_id=user_id,
                message_text=rendered_prompt,
            ):
                last_message = message
                # Messages are persisted by session service

            app_logger.info(
                "Claude Code execution completed",
                extra={
                    "execution_id": execution_id,
                    "session_id": str(session.id),
                }
            )

            # 7. Mark execution as completed
            end_time = datetime.utcnow()
            duration_seconds = int((end_time - start_time).total_seconds())

            # Store last message ID in result_data
            result_data = {}
            if last_message:
                result_data["last_message_id"] = str(last_message.id)
                result_data["message_content"] = last_message.content[:500] if last_message.content else None  # Truncate for storage

            await task_execution_repo.update(
                execution_id,
                status="completed",
                completed_at=end_time,
                duration_seconds=duration_seconds,
                result_data=result_data if result_data else None,
            )
            await db.commit()

            app_logger.info(
                "Execution marked as completed",
                extra={
                    "execution_id": execution_id,
                    "duration_seconds": duration_seconds,
                }
            )

            # 8. Generate report if requested
            report_id = None
            if task.generate_report:
                app_logger.info(
                    "Generating report",
                    extra={
                        "execution_id": execution_id,
                        "report_format": task.report_format,
                    }
                )

                report_service = ReportService(
                    db=db,
                    report_repo=report_repo,
                    session_repo=session_repo,
                    storage_manager=storage_manager,
                )

                report = await report_service.generate_from_session(
                    session_id=session.id,
                    user_id=user_id,
                    title=f"Task Execution Report: {task.name}",
                    format=task.report_format or "html",
                    auto_generated=True,
                )

                report_id = report.id
                await task_execution_repo.update(
                    execution_id,
                    report_id=report.id,
                )
                await db.commit()

                app_logger.info(
                    "Report generated successfully",
                    extra={
                        "execution_id": execution_id,
                        "report_id": str(report.id),
                    }
                )

            # 9. Audit log
            await audit_service.log_action(
                user_id=user_id,
                action_type="task.executed",
                resource_type="task_execution",
                resource_id=execution_id,
                action_details={
                    "task_id": task_id,
                    "task_name": task.name,
                    "trigger_type": "manual",
                    "status": "completed",
                    "duration_seconds": duration_seconds,
                    "session_id": str(session.id),
                    "report_id": str(report_id) if report_id else None,
                }
            )
            await db.commit()

            return {
                "status": "completed",
                "execution_id": execution_id,
                "session_id": str(session.id),
                "report_id": str(report_id) if report_id else None,
                "duration_seconds": duration_seconds,
                "error": None,
            }

        except Exception as e:
            # Mark as failed
            end_time = datetime.utcnow()
            duration_seconds = int((end_time - start_time).total_seconds())

            error_message = str(e)[:1000]  # Truncate long errors

            await task_execution_repo.update(
                execution_id,
                status="failed",
                error_message=error_message,
                completed_at=end_time,
                duration_seconds=duration_seconds,
            )
            await db.commit()

            app_logger.error(
                "Task execution failed",
                extra={
                    "execution_id": execution_id,
                    "error": error_message,
                    "error_type": type(e).__name__,
                    "duration_seconds": duration_seconds,
                    "event": "task_execution_error",
                },
                exc_info=True,
            )

            # Audit log failure
            await audit_service.log_action(
                user_id=user_id,
                action_type="task.failed",
                resource_type="task_execution",
                resource_id=execution_id,
                action_details={
                    "task_id": task_id,
                    "error": error_message,
                    "error_type": type(e).__name__,
                    "duration_seconds": duration_seconds,
                }
            )
            await db.commit()

            # Re-raise for Celery retry mechanism
            raise


def _render_prompt_template(template: str, variables: dict) -> str:
    """Render prompt template with variables.

    Simple variable substitution using {variable_name} syntax.

    Args:
        template: Prompt template string
        variables: Variables to substitute

    Returns:
        Rendered prompt string

    Example:
        >>> template = "Analyze {environment} deployment"
        >>> variables = {"environment": "production"}
        >>> result = "Analyze production deployment"
    """
    import re

    def replace_var(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    # Replace {variable_name} with values
    rendered = re.sub(r'\{(\w+)\}', replace_var, template)
    return rendered
