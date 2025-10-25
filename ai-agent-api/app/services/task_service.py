"""Task service for business logic."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.task import Task
from app.domain.entities.task_execution import TaskExecution, TaskExecutionStatus, TriggerType
from app.domain.exceptions import TaskNotFoundError, PermissionDeniedError, ValidationError
from app.repositories.task_repository import TaskRepository
from app.repositories.task_execution_repository import TaskExecutionRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)


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
        tool_group_id: Optional[UUID] = None,
        is_scheduled: bool = False,
        schedule_cron: Optional[str] = None,
        generate_report: bool = False,
        report_format: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task."""
        logger.info(
            "Creating new task",
            extra={
                "user_id": str(user_id),
                "task_name": name,
                "is_scheduled": is_scheduled,
                "generate_report": generate_report,
                "allowed_tools_count": len(allowed_tools) if allowed_tools else 0
            }
        )

        # === TOOL GROUP RESOLUTION ===
        # If tool_group_id is provided, load tools from tool group
        final_allowed_tools = allowed_tools or []
        final_disallowed_tools = disallowed_tools or []

        if tool_group_id:
            from app.repositories.tool_group_repository import ToolGroupRepository
            tool_group_repo = ToolGroupRepository(self.db)
            tool_group = await tool_group_repo.get_by_id(str(tool_group_id))

            if not tool_group:
                raise ValidationError(f"Tool group {tool_group_id} not found")

            # Use tool group's tools if not provided directly
            if not allowed_tools:
                final_allowed_tools = tool_group.allowed_tools or []
            if not disallowed_tools:
                final_disallowed_tools = tool_group.disallowed_tools or []

        # === VALIDATION LAYER ===
        # Validate task definition before creating entity
        await self._validate_task_definition(
            prompt_template=prompt_template,
            allowed_tools=final_allowed_tools,
            sdk_options=sdk_options,
            is_scheduled=is_scheduled,
            schedule_cron=schedule_cron,
            generate_report=generate_report,
            report_format=report_format,
        )

        # Create task entity
        task = Task(
            id=uuid4(),
            user_id=user_id,
            name=name,
            prompt_template=prompt_template,
            allowed_tools=final_allowed_tools,
            sdk_options=sdk_options or {},
            tool_group_id=tool_group_id,
        )

        task.description = description
        task.disallowed_tools = final_disallowed_tools
        task.is_scheduled = is_scheduled
        task.schedule_cron = schedule_cron
        task.generate_report = generate_report
        task.report_format = report_format
        task.tags = tags or []

        # Validate schedules and reports (entity-level validation)
        if is_scheduled:
            task.validate_schedule()
        if generate_report:
            task.validate_report_format()
        
        # Persist
        from app.models.task import TaskModel
        task_model = TaskModel(
            id=task.id,
            user_id=task.user_id,
            tool_group_id=task.tool_group_id,
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
        
        logger.info(
            "Task created successfully",
            extra={
                "user_id": str(user_id),
                "task_id": str(task.id),
                "task_name": name,
                "is_scheduled": is_scheduled,
                "generate_report": generate_report
            }
        )
        
        # Audit log
        await self.audit_service.log_action(
            user_id=user_id,
            action_type="task.created",
            resource_type="task",
            resource_id=task.id,
            action_details={"name": name, "is_scheduled": is_scheduled}
        )
        
        return task

    async def execute_task(
        self,
        task_id: str,
        trigger_type: str = "manual",
        variables: Optional[dict] = None,
        execution_mode: str = "async",
    ):
        """Execute a task by creating a session and running the prompt template.

        Supports both asynchronous (via Celery) and synchronous execution modes.
        
        Args:
            task_id: Task UUID
            trigger_type: "manual", "scheduled", or "webhook"
            variables: Variables to substitute in prompt template
            execution_mode: "async" (queue to Celery) or "sync" (block and wait)

        Returns:
            TaskExecution entity

        Raises:
            TaskNotFoundError: Task doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Task not ready for execution
        """
        
        logger.info(
            "Starting task execution",
            extra={
                "task_id": task_id,
                "trigger_type": trigger_type,
                "execution_mode": execution_mode,
                "variables_provided": bool(variables)
            }
        )

        # 1. Get and validate task
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            logger.warning(
                "Task execution failed - task not found",
                extra={"task_id": task_id}
            )
            raise TaskNotFoundError(f"Task {task_id} not found")

        if not task.is_active:
            raise ValidationError("Task is not active")

        # 2. Create task execution record
        execution = TaskExecution(
            id=uuid4(),
            task_id=task.id,
            trigger_type=TriggerType(trigger_type),
            status=TaskExecutionStatus.PENDING,
        )
        execution.prompt_variables = variables or {}

        # Persist execution record
        from app.models.task_execution import TaskExecutionModel
        execution_model = TaskExecutionModel(
            id=execution.id,
            task_id=execution.task_id,
            trigger_type=execution.trigger_type.value,
            prompt_variables=execution.prompt_variables,
            status=execution.status.value,
        )
        self.db.add(execution_model)
        await self.db.flush()
        await self.db.commit()

        logger.info(
            "Task execution record created",
            extra={
                "execution_id": str(execution.id),
                "task_id": task_id,
                "status": execution.status.value,
            }
        )

        # 3. Execute based on mode
        if execution_mode == "async":
            return await self._execute_task_async(execution, task, variables or {})
        else:
            return await self._execute_task_sync(execution, task, variables or {})

    async def _execute_task_async(
        self,
        execution: TaskExecution,
        task,
        variables: dict,
    ) -> TaskExecution:
        """Schedule task for background execution using asyncio.

        Uses asyncio.create_task to run the actual execution in the background
        without blocking the API response.

        Args:
            execution: TaskExecution entity
            task: Task entity
            variables: Prompt template variables

        Returns:
            TaskExecution entity with status=RUNNING
        """
        import asyncio
        from app.database.session import AsyncSessionLocal

        logger.info(
            "Scheduling task for background execution",
            extra={
                "execution_id": str(execution.id),
                "task_id": str(task.id),
                "task_name": task.name,
                "user_id": str(task.user_id),
                "event": "scheduling_async_task",
            }
        )

        # Update execution status to RUNNING immediately
        await self.task_execution_repo.update(
            str(execution.id),
            status=TaskExecutionStatus.RUNNING.value,
            started_at=datetime.utcnow(),
        )
        await self.db.commit()

        logger.info(
            "Task status updated to RUNNING",
            extra={
                "execution_id": str(execution.id),
                "status": "running",
            }
        )

        # Schedule the actual execution in the background
        async def run_task_in_background():
            """Run the task execution in the background without blocking."""
            db_session = AsyncSessionLocal()
            try:
                await self._execute_task_impl(execution, task, variables, db_session)
            except Exception as e:
                logger.error(
                    "Background task execution failed",
                    extra={
                        "execution_id": str(execution.id),
                        "task_id": str(task.id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "event": "task_execution_failed",
                    },
                    exc_info=True,
                )
            finally:
                await db_session.close()

        # Create a background task
        asyncio.create_task(run_task_in_background())

        logger.info(
            "Background task scheduled successfully",
            extra={
                "execution_id": str(execution.id),
                "event": "background_task_scheduled",
            }
        )

        return execution

    async def _execute_with_claude_sdk(
        self,
        prompt: str,
        task,
        execution_id: str,
    ) -> dict:
        """Execute prompt using Claude SDK directly (following POC patterns).

        This is the clean, direct approach for background task execution:
        - Use claude_agent_sdk.query() for one-shot execution
        - No session service complexity needed
        - Simple message collection and result extraction

        Based on claude-code-sdk-usage-poc/01_basic_hello_world.py pattern.

        Args:
            prompt: Rendered prompt to send to Claude
            task: Task entity with SDK options
            execution_id: Execution ID for logging

        Returns:
            Dictionary with execution results (messages, metadata, etc.)
        """
        from claude_agent_sdk import query, ClaudeAgentOptions
        from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ResultMessage
        from pathlib import Path
        import uuid

        logger.info(
            "[BG_TASK] Executing with Claude SDK directly",
            extra={
                "execution_id": execution_id,
                "task_id": str(task.id),
                "task_name": task.name,
                "prompt_length": len(prompt),
                "event": "claude_sdk_execution_start",
            }
        )

        # Log the full prompt being sent to Claude
        logger.info(
            "[BG_TASK] Full prompt being sent to Claude",
            extra={
                "execution_id": execution_id,
                "task_id": str(task.id),
                "prompt_preview": prompt[:500] if len(prompt) > 500 else prompt,
                "prompt_full_length": len(prompt),
                "event": "prompt_logged",
            }
        )

        # Create working directory for this task execution
        working_dir = Path(f"/tmp/agent-workdirs/active/{task.id}")
        working_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "[BG_TASK] Working directory created",
            extra={
                "execution_id": execution_id,
                "working_dir": str(working_dir),
                "event": "working_dir_created",
            }
        )

        # Build SDK options from task configuration
        sdk_options = task.sdk_options or {}

        # IMPORTANT: Always use 'acceptEdits' for task executions (system-controlled)
        # Tasks must auto-approve tools without manual intervention
        # User-provided permission_mode is ignored for security and automation
        options = ClaudeAgentOptions(
            allowed_tools=task.allowed_tools if task.allowed_tools else None,
            disallowed_tools=task.disallowed_tools if task.disallowed_tools else None,
            permission_mode="acceptEdits",  # System-controlled: always auto-approve
            model=sdk_options.get("model"),
            max_turns=sdk_options.get("max_turns", 10),
            cwd=str(working_dir),
        )

        logger.info(
            "[BG_TASK] Claude SDK options configured",
            extra={
                "execution_id": execution_id,
                "model": options.model,
                "permission_mode": options.permission_mode,
                "max_turns": options.max_turns,
                "working_dir": str(working_dir),
                "event": "sdk_options_configured",
            }
        )

        # Collect all messages from query
        all_messages = []
        final_result = None
        message_count = 0
        tool_use_count = 0
        tools_used = {}  # Track which tools were used and how many times

        try:
            # Execute query - returns AsyncIterator[AssistantMessage | ResultMessage]
            async for message in query(prompt=prompt, options=options):
                message_count += 1
                all_messages.append(message)

                if isinstance(message, AssistantMessage):
                    # Extract and log text content
                    text_blocks = []
                    tool_blocks = []

                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_blocks.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            tool_use_count += 1
                            tool_name = block.name
                            tools_used[tool_name] = tools_used.get(tool_name, 0) + 1
                            tool_blocks.append({
                                "id": block.id,
                                "name": tool_name,
                                "input_keys": list(block.input.keys()) if isinstance(block.input, dict) else [],
                            })

                    # Log Claude's text response
                    if text_blocks:
                        logger.info(
                            "[BG_TASK] Claude response message",
                            extra={
                                "execution_id": execution_id,
                                "message_number": message_count,
                                "message_type": "AssistantMessage",
                                "text_content": text_blocks[0][:300] if text_blocks[0] else "",
                                "text_length": len(text_blocks[0]) if text_blocks[0] else 0,
                                "event": "claude_message_received",
                            }
                        )

                    # Log tool uses
                    if tool_blocks:
                        logger.info(
                            "[BG_TASK] Claude requested tool execution",
                            extra={
                                "execution_id": execution_id,
                                "message_number": message_count,
                                "tools_requested": [t["name"] for t in tool_blocks],
                                "tool_count": len(tool_blocks),
                                "tool_details": tool_blocks,
                                "event": "tool_use_requested",
                            }
                        )

                    logger.debug(
                        "[BG_TASK] Received AssistantMessage from Claude",
                        extra={
                            "execution_id": execution_id,
                            "message_number": message_count,
                            "message_type": type(message).__name__,
                            "has_text": len(text_blocks) > 0,
                            "has_tools": len(tool_blocks) > 0,
                            "event": "message_received",
                        }
                    )

                elif isinstance(message, ResultMessage):
                    # Final result with metadata
                    final_result = message
                    logger.info(
                        "[BG_TASK] Received final result from Claude",
                        extra={
                            "execution_id": execution_id,
                            "duration_ms": message.duration_ms,
                            "num_turns": message.num_turns,
                            "is_error": message.is_error,
                            "total_cost_usd": message.total_cost_usd,
                            "input_tokens": getattr(message, 'input_tokens', None),
                            "output_tokens": getattr(message, 'output_tokens', None),
                            "event": "final_result_received",
                        }
                    )

            # Extract final text response from last AssistantMessage
            final_text = ""
            for message in reversed(all_messages):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            final_text = block.text
                            break
                    if final_text:
                        break

            logger.info(
                "[BG_TASK] Claude SDK execution completed successfully",
                extra={
                    "execution_id": execution_id,
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "total_messages": message_count,
                    "total_tool_uses": tool_use_count,
                    "tools_used_summary": tools_used,
                    "response_length": len(final_text),
                    "response_preview": final_text[:300] if len(final_text) > 300 else final_text,
                    "duration_ms": final_result.duration_ms if final_result else None,
                    "num_turns": final_result.num_turns if final_result else None,
                    "total_cost_usd": final_result.total_cost_usd if final_result else None,
                    "event": "claude_sdk_execution_complete",
                }
            )

            return {
                "success": True,
                "final_text": final_text,
                "total_messages": message_count,
                "total_tool_uses": tool_use_count,
                "duration_ms": final_result.duration_ms if final_result else None,
                "cost_usd": final_result.total_cost_usd if final_result else None,
                "num_turns": final_result.num_turns if final_result else None,
                "working_dir": str(working_dir),
            }

        except Exception as e:
            logger.error(
                "[BG_TASK] Claude SDK execution failed",
                extra={
                    "execution_id": execution_id,
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "messages_received": message_count,
                    "tool_uses_executed": tool_use_count,
                    "tools_used_before_failure": tools_used,
                    "event": "claude_sdk_execution_failed",
                },
                exc_info=True,
            )
            raise

    async def _execute_task_impl(
        self,
        execution: TaskExecution,
        task,
        variables: dict,
        db_session: AsyncSession,
    ) -> None:
        """Implementation of task execution logic that runs in background.

        Simple, direct approach using Claude SDK (based on POC examples):
        1. Render prompt template
        2. Execute with Claude SDK directly (query function)
        3. Update execution status with results
        4. Create audit trail

        Follows SDK best practices from claude-code-sdk-usage-poc examples.

        Args:
            execution: TaskExecution entity
            task: Task entity containing prompt and configuration
            variables: Template variables for prompt rendering
            db_session: Dedicated database session for this background task
        """
        from app.repositories.task_execution_repository import TaskExecutionRepository as ExecRepo
        from app.services.audit_service import AuditService

        logger.info(
            "[BG_TASK] Starting background task execution",
            extra={
                "execution_id": str(execution.id),
                "task_id": str(task.id),
                "task_name": task.name,
                "user_id": str(task.user_id),
                "trigger_type": execution.trigger_type.value,
                "variables_count": len(variables) if variables else 0,
                "event": "bg_task_started",
            }
        )

        exec_repo = ExecRepo(db_session)

        try:
            # Step 1: Render prompt template
            logger.info(
                "[BG_TASK] Rendering prompt template",
                extra={
                    "execution_id": str(execution.id),
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "template_length": len(task.prompt_template),
                    "template_preview": task.prompt_template[:200] if len(task.prompt_template) > 200 else task.prompt_template,
                    "variables_count": len(variables) if variables else 0,
                    "variables_keys": list(variables.keys()) if variables else [],
                    "event": "rendering_prompt",
                }
            )

            rendered_prompt = self._render_prompt_template(
                task.prompt_template,
                variables or {},
            )

            logger.info(
                "[BG_TASK] Prompt rendered successfully",
                extra={
                    "execution_id": str(execution.id),
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "template_length": len(task.prompt_template),
                    "rendered_length": len(rendered_prompt),
                    "rendered_preview": rendered_prompt[:300] if len(rendered_prompt) > 300 else rendered_prompt,
                    "event": "prompt_rendered",
                }
            )

            # Step 2: Execute with Claude SDK directly
            result = await self._execute_with_claude_sdk(
                prompt=rendered_prompt,
                task=task,
                execution_id=str(execution.id),
            )

            # Step 3: Update execution as completed
            logger.info(
                "[BG_TASK] Execution completed successfully",
                extra={
                    "execution_id": str(execution.id),
                    "total_messages": result.get("total_messages"),
                    "total_tool_uses": result.get("total_tool_uses"),
                    "duration_ms": result.get("duration_ms"),
                    "cost_usd": result.get("cost_usd"),
                    "num_turns": result.get("num_turns"),
                    "event": "execution_complete",
                }
            )

            # Update execution with result data
            await exec_repo.update(
                str(execution.id),
                status=TaskExecutionStatus.COMPLETED.value,
                completed_at=datetime.utcnow(),
                result_data={
                    "final_text": result.get("final_text", "")[:500],  # Truncate for storage
                    "total_messages": result.get("total_messages"),
                    "total_tool_uses": result.get("total_tool_uses"),
                    "duration_ms": result.get("duration_ms"),
                    "cost_usd": result.get("cost_usd"),
                    "num_turns": result.get("num_turns"),
                    "working_dir": result.get("working_dir"),
                },
            )

            logger.info(
                "[BG_TASK] Execution updated with completion status",
                extra={
                    "execution_id": str(execution.id),
                    "event": "execution_updated",
                }
            )

            # Commit database changes
            await db_session.commit()

            logger.info(
                "[BG_TASK] Database changes committed",
                extra={
                    "execution_id": str(execution.id),
                    "event": "changes_committed",
                }
            )

            # Create audit log
            audit_svc = AuditService(db_session)
            await audit_svc.log_task_executed(
                task_id=task.id,
                execution_id=execution.id,
                user_id=task.user_id,
                trigger_type=execution.trigger_type.value,
                status="success",  # Audit status must be 'success', 'failure', or 'denied'
            )

            logger.info(
                "[BG_TASK] ✅ Task execution completed successfully",
                extra={
                    "execution_id": str(execution.id),
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "duration_seconds": (datetime.utcnow() - execution.created_at).total_seconds(),
                    "event": "task_execution_success",
                }
            )

        except Exception as e:
            logger.error(
                "[BG_TASK] ❌ Background task execution failed with exception",
                extra={
                    "execution_id": str(execution.id),
                    "task_id": str(task.id),
                    "task_name": task.name if 'task' in locals() else 'unknown',
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "error_module": type(e).__module__,
                    "event": "task_execution_exception",
                },
                exc_info=True,
            )

            try:
                # Mark execution as failed
                logger.info(
                    "[BG_TASK] Marking execution as failed in database",
                    extra={
                        "execution_id": str(execution.id),
                        "status": "failed",
                        "error": str(e)[:200],  # Truncate error message
                        "event": "marking_failed",
                    }
                )

                await exec_repo.update(
                    str(execution.id),
                    status=TaskExecutionStatus.FAILED.value,
                    completed_at=datetime.utcnow(),
                    error_message=str(e),
                )

                logger.info(
                    "[BG_TASK] Execution marked as failed",
                    extra={
                        "execution_id": str(execution.id),
                        "event": "marked_failed",
                    }
                )

                # Audit log error
                logger.info(
                    "[BG_TASK] Creating audit log for failed execution",
                    extra={
                        "execution_id": str(execution.id),
                        "task_id": str(task.id),
                        "event": "logging_failure_audit",
                    }
                )

                audit_svc = AuditService(db_session)
                await audit_svc.log_task_executed(
                    task_id=task.id,
                    execution_id=execution.id,
                    user_id=task.user_id,
                    trigger_type=execution.trigger_type.value,
                    status="failed",
                    error_message=str(e),
                )

                logger.info(
                    "[BG_TASK] Failure audit log created",
                    extra={
                        "execution_id": str(execution.id),
                        "event": "failure_audit_logged",
                    }
                )

                await db_session.commit()

                logger.info(
                    "[BG_TASK] Database changes committed after failure handling",
                    extra={
                        "execution_id": str(execution.id),
                        "event": "failure_committed",
                    }
                )

            except Exception as error_handling_error:
                logger.error(
                    "[BG_TASK] Failed to handle error properly - database update failed",
                    extra={
                        "execution_id": str(execution.id),
                        "original_error": str(e)[:200],
                        "handler_error": str(error_handling_error),
                        "handler_error_type": type(error_handling_error).__name__,
                        "event": "error_handler_failed",
                    },
                    exc_info=True,
                )

    async def _execute_task_sync(
        self,
        execution: TaskExecution,
        task,
        variables: dict,
    ) -> TaskExecution:
        """Execute task synchronously (blocking).

        This is the original synchronous implementation.
        Used for backward compatibility and testing.

        Args:
            execution: TaskExecution entity
            task: Task entity
            variables: Prompt template variables

        Returns:
            TaskExecution entity with status=COMPLETED or FAILED
        """
        from app.services.sdk_session_service import SDKIntegratedSessionService
        from app.services.storage_manager import StorageManager
        from app.repositories.session_repository import SessionRepository
        from app.repositories.message_repository import MessageRepository
        from app.repositories.tool_call_repository import ToolCallRepository
        from uuid import uuid4

        logger.info(
            "Executing task synchronously",
            extra={
                "execution_id": str(execution.id),
                "task_id": str(task.id),
            }
        )

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
            session_name = f"Task: {task.name} ({execution.trigger_type.value})"

            # Prepare SDK options with forced permission_mode
            # IMPORTANT: Always use 'acceptEdits' for task executions (system-controlled)
            # Tasks must auto-approve tools without manual intervention
            task_sdk_options = (task.sdk_options or {}).copy()
            task_sdk_options["permission_mode"] = "acceptEdits"  # System-controlled: always auto-approve

            session = await session_service.create_session(
                user_id=task.user_id,
                name=session_name,
                description=f"Automated execution of task '{task.name}'",
                sdk_options=task_sdk_options,
                permission_mode="acceptEdits",  # Explicitly set for session
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
            execution.result_data = {
                "last_message_id": str(message.id),
                "message_content": message.content[:500] if message.content else None,
            }

            await self.task_execution_repo.update(
                str(execution.id),
                status=TaskExecutionStatus.COMPLETED.value,
                completed_at=execution.completed_at,
                result_data=execution.result_data,
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
                trigger_type=execution.trigger_type.value,
                status="success",  # Audit status must be 'success', 'failure', or 'denied'
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
                trigger_type=execution.trigger_type.value,
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
        logger.debug(
            "Getting task by ID",
            extra={
                "task_id": str(task_id),
                "user_id": str(user_id)
            }
        )
        
        task_model = await self.task_repo.get_by_id(task_id)
        if not task_model:
            logger.warning(
                "Task not found",
                extra={
                    "task_id": str(task_id),
                    "user_id": str(user_id)
                }
            )
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
        logger.info(
            "Deleting task",
            extra={
                "task_id": str(task_id),
                "user_id": str(user_id)
            }
        )
        
        task = await self.get_task(task_id, user_id)
        
        # Only owner can delete
        if task.user_id != user_id:
            logger.warning(
                "Task deletion denied - not owner",
                extra={
                    "task_id": str(task_id),
                    "user_id": str(user_id),
                    "task_owner_id": str(task.user_id)
                }
            )
            raise PermissionDeniedError("Only task owner can delete")
        
        success = await self.task_repo.soft_delete(task_id)
        await self.db.commit()
        
        if success:
            logger.info(
                "Task deleted successfully",
                extra={
                    "task_id": str(task_id),
                    "user_id": str(user_id)
                }
            )
        
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
            tool_group_id=model.tool_group_id,
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

    async def get_task_with_details(
        self,
        task_id: UUID,
        user_id: UUID,
        include_executions: bool = True,
        include_working_dirs: bool = True,
        include_audit: bool = True,
        include_reports: bool = True,
    ) -> dict:
        """Get task with all aggregated child objects and references.

        Returns a comprehensive view of the task including:
        - Execution statistics
        - Recent executions
        - Working directories (active and archived)
        - MCP tools configuration
        - Permission policies
        - Audit summary
        - Reports summary

        Args:
            task_id: Task UUID
            user_id: User UUID for authorization
            include_executions: Include execution summary and recent executions
            include_working_dirs: Include working directory information
            include_audit: Include audit trail summary
            include_reports: Include reports summary

        Returns:
            Dictionary with task and all aggregated data
        """
        logger.info(
            "Getting task with details",
            extra={
                "task_id": str(task_id),
                "user_id": str(user_id),
                "include_executions": include_executions,
                "include_working_dirs": include_working_dirs,
            }
        )

        # Get base task
        task = await self.get_task(task_id, user_id)

        result = {
            "task": task,
            "execution_summary": None,
            "recent_executions": [],
            "working_directories": None,
            "mcp_tools": [],
            "permission_policies": None,
            "audit_summary": None,
            "reports_summary": None,
        }

        # Get execution statistics and recent executions
        if include_executions:
            exec_stats = await self.task_execution_repo.get_execution_stats(task_id)

            # Get latest execution
            latest_execution = await self.task_execution_repo.get_latest_execution(task_id)

            # Calculate success rate
            total = exec_stats.get("total", 0)
            successful = exec_stats.get("completed", 0)
            success_rate = (successful / total) if total > 0 else 0.0

            result["execution_summary"] = {
                "total_executions": total,
                "successful": successful,
                "failed": exec_stats.get("failed", 0),
                "cancelled": exec_stats.get("cancelled", 0),
                "avg_duration_seconds": exec_stats.get("avg_duration_seconds"),
                "success_rate": success_rate,
                "last_execution": latest_execution,
            }

            # Get recent executions (last 5)
            result["recent_executions"] = await self.task_execution_repo.get_by_task(
                task_id=task_id,
                skip=0,
                limit=5
            )

        # Get working directories from sessions
        if include_working_dirs:
            result["working_directories"] = await self._get_working_directories(task_id)

        # Extract MCP tools from sdk_options
        result["mcp_tools"] = self._extract_mcp_tools(task.sdk_options)

        # Build permission policies info
        # Note: permission_mode is system-controlled (always 'acceptEdits' for tasks)
        result["permission_policies"] = {
            "allowed_tools": task.allowed_tools,
            "disallowed_tools": task.disallowed_tools,
        }

        # Get audit summary
        if include_audit:
            result["audit_summary"] = await self._get_audit_summary(task_id, user_id)

        # Get reports summary
        if include_reports:
            result["reports_summary"] = await self._get_reports_summary(task_id)

        return result

    async def _get_working_directories(self, task_id: UUID) -> dict:
        """Get working directories for task executions.

        Returns both active and archived directories.
        """
        from sqlalchemy import select
        from app.models.task_execution import TaskExecutionModel
        import os

        # Get executions
        stmt = (
            select(TaskExecutionModel)
            .where(TaskExecutionModel.task_id == task_id)
            .order_by(TaskExecutionModel.created_at.desc())
        )

        result = await self.db.execute(stmt)
        executions = result.scalars().all()

        active_dirs = []
        archived_dirs = []

        for execution_model in executions:
            if execution_model.result_data and execution_model.result_data.get("working_dir"):
                # Async mode - working dir in result_data
                dir_info = {
                    "execution_id": execution_model.id,
                    "path": execution_model.result_data.get("working_dir"),
                    "created_at": execution_model.created_at,
                    "is_archived": execution_model.status == "completed",
                    "size_bytes": None,
                }

                # Try to get directory size if it exists
                try:
                    working_dir = execution_model.result_data.get("working_dir")
                    if working_dir and os.path.exists(working_dir):
                        total_size = 0
                        for dirpath, dirnames, filenames in os.walk(working_dir):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                total_size += os.path.getsize(filepath)
                        dir_info["size_bytes"] = total_size
                except Exception as e:
                    logger.warning(f"Could not get directory size: {e}")
                    dir_info["size_bytes"] = None

                if execution_model.status == "completed":
                    archived_dirs.append(dir_info)
                else:
                    active_dirs.append(dir_info)

        return {
            "active": active_dirs,
            "archived": archived_dirs,
        }

    def _extract_mcp_tools(self, sdk_options: dict) -> list:
        """Extract MCP server and tools information from sdk_options.

        Args:
            sdk_options: SDK configuration dictionary

        Returns:
            List of MCP tool information
        """
        mcp_tools = []

        mcp_servers = sdk_options.get("mcp_servers", {})

        for server_name, server_config in mcp_servers.items():
            tool_info = {
                "server_name": server_name,
                "tools": server_config.get("tools", []),
                "enabled": server_config.get("enabled", True),
                "config": {
                    "command": server_config.get("command"),
                    "args": server_config.get("args", []),
                }
            }
            mcp_tools.append(tool_info)

        return mcp_tools

    async def _get_audit_summary(self, task_id: UUID, user_id: UUID) -> dict:
        """Get audit trail summary for task.

        Args:
            task_id: Task UUID
            user_id: User UUID

        Returns:
            Audit summary with total count and recent actions
        """
        from sqlalchemy import select, func
        from app.models.audit_log import AuditLogModel

        # Get total count of audit logs for this task
        count_stmt = (
            select(func.count(AuditLogModel.id))
            .where(
                (AuditLogModel.resource_type == "task") &
                (AuditLogModel.resource_id == task_id)
            )
        )
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar_one()

        # Get recent audit logs (last 5)
        recent_stmt = (
            select(AuditLogModel)
            .where(
                (AuditLogModel.resource_type == "task") &
                (AuditLogModel.resource_id == task_id)
            )
            .order_by(AuditLogModel.created_at.desc())
            .limit(5)
        )
        recent_result = await self.db.execute(recent_stmt)
        recent_logs = recent_result.scalars().all()

        recent_actions = []
        for log in recent_logs:
            recent_actions.append({
                "action_type": log.action_type,
                "status": log.status,
                "created_at": log.created_at,
                "details": log.action_details,
            })

        return {
            "total_audit_logs": total_count,
            "recent_actions": recent_actions,
        }

    async def _get_reports_summary(self, task_id: UUID) -> dict:
        """Get reports summary for task.

        Args:
            task_id: Task UUID

        Returns:
            Reports summary with total count and recent reports
        """
        from sqlalchemy import select, func
        from app.models.report import ReportModel
        from app.models.task_execution import TaskExecutionModel

        # Get total count of reports for this task's executions
        count_stmt = (
            select(func.count(ReportModel.id))
            .join(TaskExecutionModel, ReportModel.task_execution_id == TaskExecutionModel.id)
            .where(TaskExecutionModel.task_id == task_id)
        )
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar_one()

        # Get recent reports (last 5)
        recent_stmt = (
            select(ReportModel)
            .join(TaskExecutionModel, ReportModel.task_execution_id == TaskExecutionModel.id)
            .where(TaskExecutionModel.task_id == task_id)
            .order_by(ReportModel.created_at.desc())
            .limit(5)
        )
        recent_result = await self.db.execute(recent_stmt)
        recent_reports = recent_result.scalars().all()

        recent = []
        for report in recent_reports:
            recent.append({
                "id": report.id,
                "title": report.title,
                "format": report.file_format,
                "created_at": report.created_at,
                "file_path": report.file_path,
            })

        return {
            "total": total_count,
            "recent": recent,
        }

    async def _validate_task_definition(
        self,
        prompt_template: str,
        allowed_tools: list[str],
        sdk_options: dict,
        is_scheduled: bool,
        schedule_cron: Optional[str],
        generate_report: bool,
        report_format: Optional[str],
    ) -> None:
        """Validate task definition to ensure it will execute successfully.

        Checks:
        - Prompt template is valid and renderable
        - Allowed tools are valid patterns
        - SDK options are properly structured
        - No forbidden permission_mode overrides
        - Schedule cron is valid if scheduled
        - Report format is valid if reports enabled

        Raises:
            ValidationError: If validation fails with detailed error message
        """
        from app.domain.exceptions import ValidationError
        from jinja2 import Template, TemplateSyntaxError
        import re

        logger.debug("Validating task definition")

        # 1. Validate prompt template
        if not prompt_template or not prompt_template.strip():
            raise ValidationError("prompt_template cannot be empty")

        # Test Jinja2 template rendering
        try:
            template = Template(prompt_template)
            # Try rendering with empty variables to check syntax
            template.render()
        except TemplateSyntaxError as e:
            raise ValidationError(f"Invalid prompt template syntax: {str(e)}")
        except Exception as e:
            logger.warning(f"Template validation warning: {e}")
            # Allow other template errors (missing variables are OK)

        # 2. Validate allowed_tools patterns
        if not allowed_tools:
            raise ValidationError("allowed_tools must contain at least one tool pattern")

        valid_tool_patterns = [
            r"^Bash$",
            r"^Read$",
            r"^Write$",
            r"^Edit$",
            r"^Glob$",
            r"^Grep$",
            r"^Task$",
            r"^WebFetch$",
            r"^WebSearch$",
            r"^AskUserQuestion$",
            r"^Skill$",
            r"^SlashCommand$",
            r"^NotebookEdit$",
            r"^mcp__[\w\-]+__[\w\-]+$",  # MCP tools: mcp__server__tool
            r"^\*$",  # Allow all
        ]

        for tool in allowed_tools:
            is_valid = any(re.match(pattern, tool) for pattern in valid_tool_patterns)
            if not is_valid:
                raise ValidationError(
                    f"Invalid tool pattern '{tool}'. Must be a valid Claude Code tool "
                    f"(Bash, Read, Write, etc.) or MCP tool (mcp__server__tool) or wildcard (*)"
                )

        # 3. Validate sdk_options
        if sdk_options:
            # Check for forbidden permission_mode override
            if "permission_mode" in sdk_options:
                logger.warning(
                    "User attempted to set permission_mode in sdk_options. "
                    "This is system-controlled and will be ignored."
                )
                # Remove it to prevent confusion
                sdk_options.pop("permission_mode", None)

            # Validate model if provided
            if "model" in sdk_options:
                valid_models = [
                    "claude-sonnet-4-5",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-sonnet-20240620",
                    "claude-3-opus-20240229",
                    "claude-3-haiku-20240307",
                    "claude-haiku-4-5",
                ]
                if sdk_options["model"] not in valid_models:
                    raise ValidationError(
                        f"Invalid model '{sdk_options['model']}'. "
                        f"Must be one of: {', '.join(valid_models)}"
                    )

            # Validate max_turns if provided
            if "max_turns" in sdk_options:
                max_turns = sdk_options["max_turns"]
                if not isinstance(max_turns, int) or max_turns < 1 or max_turns > 50:
                    raise ValidationError("max_turns must be an integer between 1 and 50")

        # 4. Validate schedule if scheduled
        if is_scheduled:
            if not schedule_cron:
                raise ValidationError("schedule_cron is required when is_scheduled=True")

            from croniter import croniter
            if not croniter.is_valid(schedule_cron):
                raise ValidationError(f"Invalid cron expression: {schedule_cron}")

        # 5. Validate report format if reports enabled
        if generate_report:
            valid_formats = ["json", "markdown", "html", "pdf"]
            if not report_format or report_format not in valid_formats:
                raise ValidationError(
                    f"Invalid report_format: {report_format}. "
                    f"Must be one of: {', '.join(valid_formats)}"
                )

        logger.info(
            "Task definition validated successfully",
            extra={
                "prompt_template_length": len(prompt_template),
                "allowed_tools_count": len(allowed_tools),
                "has_sdk_options": bool(sdk_options),
                "is_scheduled": is_scheduled,
                "generate_report": generate_report,
            }
        )

    # ===== NEW FEATURES: Tool Calls, Cancellation, Working Directory Management =====

    async def get_execution_tool_calls(
        self,
        execution_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """Get tool calls for a task execution.

        Tool calls are only available for sync mode executions (with sessions).
        Async mode executions don't store individual tool calls.

        Args:
            execution_id: Task execution UUID
            user_id: User UUID for authorization
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of tool call models

        Raises:
            TaskNotFoundError: Execution doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Execution has no session (async mode)
        """
        from app.repositories.tool_call_repository import ToolCallRepository
        from app.domain.exceptions import ValidationError

        logger.info(
            "Getting tool calls for execution",
            extra={
                "execution_id": str(execution_id),
                "user_id": str(user_id),
                "skip": skip,
                "limit": limit,
            }
        )

        # Get execution
        execution = await self.task_execution_repo.get_by_id(str(execution_id))
        if not execution:
            raise TaskNotFoundError(f"Task execution {execution_id} not found")

        # Get task for authorization
        task = await self.task_repo.get_by_id(str(execution.task_id))
        if not task:
            raise TaskNotFoundError(f"Task {execution.task_id} not found")

        # Check authorization
        if task.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to access this execution")

        # Check if execution has a session (sync mode only)
        if not execution.session_id:
            raise ValidationError(
                "This execution was run in async mode and does not have detailed tool call records. "
                "Tool calls are only available for sync mode executions."
            )

        # Get tool calls from session
        tool_call_repo = ToolCallRepository(self.db)
        tool_calls = await tool_call_repo.get_by_session(
            session_id=execution.session_id,
            skip=skip,
            limit=limit,
        )

        logger.info(
            "Retrieved tool calls for execution",
            extra={
                "execution_id": str(execution_id),
                "tool_calls_count": len(tool_calls),
            }
        )

        return tool_calls

    async def cancel_execution(
        self,
        execution_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ):
        """Cancel a running task execution.

        Cancellation behavior:
        - PENDING/QUEUED: Mark as cancelled immediately
        - RUNNING (async mode): Set cancellation flag, background task will check and stop
        - RUNNING (sync mode): Not supported (would require killing subprocess)
        - COMPLETED/FAILED/CANCELLED: Cannot cancel (already finished)

        Args:
            execution_id: Task execution UUID
            user_id: User UUID for authorization
            reason: Optional cancellation reason

        Returns:
            Updated TaskExecution entity

        Raises:
            TaskNotFoundError: Execution doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Execution cannot be cancelled
        """
        from app.domain.exceptions import ValidationError

        logger.info(
            "Cancelling task execution",
            extra={
                "execution_id": str(execution_id),
                "user_id": str(user_id),
                "reason": reason,
            }
        )

        # Get execution
        execution = await self.task_execution_repo.get_by_id(str(execution_id))
        if not execution:
            raise TaskNotFoundError(f"Task execution {execution_id} not found")

        # Get task for authorization
        task = await self.task_repo.get_by_id(str(execution.task_id))
        if not task:
            raise TaskNotFoundError(f"Task {execution.task_id} not found")

        # Check authorization
        if task.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to cancel this execution")

        # Check if execution can be cancelled
        if execution.status in ["completed", "failed", "cancelled"]:
            raise ValidationError(
                f"Cannot cancel execution with status '{execution.status}'. "
                "Only pending, queued, or running executions can be cancelled."
            )

        # For RUNNING status in sync mode (with session), we cannot safely kill the subprocess
        if execution.status == "running" and execution.session_id:
            raise ValidationError(
                "Cannot cancel running sync mode execution. "
                "Sync mode executions run in a subprocess and cannot be safely interrupted. "
                "Only async mode running executions can be cancelled."
            )

        # Cancel the execution
        await self.task_execution_repo.update(
            str(execution_id),
            status=TaskExecutionStatus.CANCELLED.value,
            completed_at=datetime.utcnow(),
            error_message=reason or "Cancelled by user",
        )
        await self.db.commit()

        # Create audit log
        await self.audit_service.log_action(
            user_id=user_id,
            action_type="task_execution.cancelled",
            resource_type="task_execution",
            resource_id=execution_id,
            action_details={
                "task_id": str(task.id),
                "reason": reason,
            }
        )

        # Refresh execution from DB
        execution = await self.task_execution_repo.get_by_id(str(execution_id))

        logger.info(
            "Task execution cancelled successfully",
            extra={
                "execution_id": str(execution_id),
                "task_id": str(task.id),
                "reason": reason,
            }
        )

        return execution

    async def get_execution_files(
        self,
        execution_id: UUID,
        user_id: UUID,
    ) -> dict:
        """Get file manifest for task execution's working directory.

        Args:
            execution_id: Task execution UUID
            user_id: User UUID for authorization

        Returns:
            Dictionary with file manifest and metadata

        Raises:
            TaskNotFoundError: Execution doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Working directory not found
        """
        from app.services.storage_manager import StorageManager
        from app.domain.exceptions import ValidationError
        from pathlib import Path

        logger.info(
            "Getting files for execution",
            extra={
                "execution_id": str(execution_id),
                "user_id": str(user_id),
            }
        )

        # Get execution
        execution = await self.task_execution_repo.get_by_id(str(execution_id))
        if not execution:
            raise TaskNotFoundError(f"Task execution {execution_id} not found")

        # Get task for authorization
        task = await self.task_repo.get_by_id(str(execution.task_id))
        if not task:
            raise TaskNotFoundError(f"Task {execution.task_id} not found")

        # Check authorization
        if task.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to access this execution")

        # Get working directory path
        working_dir = None
        if execution.session_id:
            # Sync mode - get from session
            from app.repositories.session_repository import SessionRepository
            session_repo = SessionRepository(self.db)
            session = await session_repo.get_by_id(str(execution.session_id))
            if session and session.working_directory_path:
                working_dir = Path(session.working_directory_path)
        elif execution.result_data and execution.result_data.get("working_dir"):
            # Async mode - get from result_data
            working_dir = Path(execution.result_data["working_dir"])

        if not working_dir or not working_dir.exists():
            raise ValidationError(
                f"Working directory not found for execution {execution_id}. "
                "It may have been archived or cleaned up."
            )

        # Get file manifest
        storage_mgr = StorageManager()

        # Calculate session_id for storage manager (uses session_id or task_id)
        session_id_for_storage = execution.session_id if execution.session_id else execution.task_id

        files = await storage_mgr.get_file_manifest(session_id_for_storage)
        total_size = await storage_mgr.get_directory_size(session_id_for_storage)
        total_files = len(files)

        logger.info(
            "Retrieved file manifest for execution",
            extra={
                "execution_id": str(execution_id),
                "total_files": total_files,
                "total_size": total_size,
            }
        )

        return {
            "execution_id": execution_id,
            "total_files": total_files,
            "total_size": total_size,
            "files": files,
        }

    async def archive_execution_directory(
        self,
        execution_id: UUID,
        user_id: UUID,
    ) -> dict:
        """Archive task execution's working directory to tar.gz.

        Args:
            execution_id: Task execution UUID
            user_id: User UUID for authorization

        Returns:
            Dictionary with archive info

        Raises:
            TaskNotFoundError: Execution doesn't exist
            PermissionDeniedError: User doesn't have access
            ValidationError: Working directory not found or already archived
        """
        from app.services.storage_manager import StorageManager
        from app.domain.exceptions import ValidationError
        from pathlib import Path

        logger.info(
            "Archiving working directory for execution",
            extra={
                "execution_id": str(execution_id),
                "user_id": str(user_id),
            }
        )

        # Get execution
        execution = await self.task_execution_repo.get_by_id(str(execution_id))
        if not execution:
            raise TaskNotFoundError(f"Task execution {execution_id} not found")

        # Get task for authorization
        task = await self.task_repo.get_by_id(str(execution.task_id))
        if not task:
            raise TaskNotFoundError(f"Task {execution.task_id} not found")

        # Check authorization
        if task.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to access this execution")

        # Get working directory path
        working_dir = None
        session_id_for_storage = None

        if execution.session_id:
            # Sync mode - get from session
            from app.repositories.session_repository import SessionRepository
            session_repo = SessionRepository(self.db)
            session = await session_repo.get_by_id(str(execution.session_id))
            if session and session.working_directory_path:
                working_dir = Path(session.working_directory_path)
                session_id_for_storage = execution.session_id
        elif execution.result_data and execution.result_data.get("working_dir"):
            # Async mode - get from result_data
            working_dir = Path(execution.result_data["working_dir"])
            session_id_for_storage = execution.task_id

        if not working_dir or not working_dir.exists():
            raise ValidationError(
                f"Working directory not found for execution {execution_id}. "
                "It may have already been archived or cleaned up."
            )

        # Create archive
        storage_mgr = StorageManager()
        archive_path = await storage_mgr.archive_working_directory(session_id_for_storage)

        if not archive_path:
            raise ValidationError(f"Failed to archive working directory for execution {execution_id}")

        # Get archive size
        archive_size = archive_path.stat().st_size

        # Create audit log
        await self.audit_service.log_action(
            user_id=user_id,
            action_type="task_execution.directory_archived",
            resource_type="task_execution",
            resource_id=execution_id,
            action_details={
                "task_id": str(task.id),
                "archive_path": str(archive_path),
                "archive_size": archive_size,
            }
        )

        logger.info(
            "Working directory archived successfully",
            extra={
                "execution_id": str(execution_id),
                "archive_path": str(archive_path),
                "archive_size": archive_size,
            }
        )

        return {
            "execution_id": execution_id,
            "archive_path": str(archive_path),
            "archive_size": archive_size,
            "created_at": datetime.utcnow(),
        }
