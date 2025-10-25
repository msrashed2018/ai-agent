"""
Tasks API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.domain.entities import User
from app.repositories.task_repository import TaskRepository
from app.repositories.task_execution_repository import TaskExecutionRepository
from app.services.task_service import TaskService
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskExecuteRequest,
    TaskExecutionResponse,
    TaskListResponse,
    TaskExecutionListResponse,
    TaskDetailedResponse,
    ExecutionSummaryData,
    WorkingDirectoryInfo,
    MCPToolInfo,
    PermissionPolicyInfo,
    AuditSummaryData,
    ReportSummaryData,
    ToolCallResponse,
    ToolCallListResponse,
    ExecutionCancelRequest,
    WorkingDirectoryManifest,
    WorkingDirectoryFileInfo,
    ArchiveResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse, Links


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """
    Create a new task definition (template).
    
    Tasks can be executed manually or scheduled to run automatically.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    
    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)
    
    # Create task
    task = await service.create_task(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        prompt_template=request.prompt_template,
        allowed_tools=request.allowed_tools,
        sdk_options=request.sdk_options,
        tool_group_id=request.tool_group_id,
        is_scheduled=request.is_scheduled,
        schedule_cron=request.schedule_cron,
        generate_report=request.generate_report,
        report_format=request.report_format,
        tags=request.tags,
    )
    
    # Build HATEOAS links
    response = TaskResponse.model_validate(task)
    response._links = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
        executions=f"/api/v1/tasks/{task.id}/executions",
    )
    
    return response


@router.get("/{task_id}", response_model=TaskDetailedResponse)
async def get_task(
    task_id: UUID,
    detailed: bool = Query(
        True,
        description="Include detailed information (executions, working dirs, audit logs, etc.)"
    ),
    include_executions: bool = Query(True, description="Include execution summary and recent executions"),
    include_working_dirs: bool = Query(True, description="Include working directory information"),
    include_audit: bool = Query(True, description="Include audit trail summary"),
    include_reports: bool = Query(True, description="Include reports summary"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskDetailedResponse:
    """
    Get task details by ID with optional aggregated child data.

    By default, returns comprehensive task details including:
    - Execution statistics (total, success rate, avg duration)
    - Recent executions (last 5)
    - Working directories (active and archived)
    - MCP tools configuration
    - Permission policies
    - Audit trail summary
    - Reports summary

    Use query parameters to control what additional data is included.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    if not detailed:
        # Simple response - just basic task info
        task = await service.get_task(task_id, current_user.id)

        response = TaskDetailedResponse.model_validate(task)
        response._links = Links(
            self=f"/api/v1/tasks/{task.id}",
            execute=f"/api/v1/tasks/{task.id}/execute",
            executions=f"/api/v1/tasks/{task.id}/executions",
        )

        return response

    # Get detailed task information
    details = await service.get_task_with_details(
        task_id=task_id,
        user_id=current_user.id,
        include_executions=include_executions,
        include_working_dirs=include_working_dirs,
        include_audit=include_audit,
        include_reports=include_reports,
    )

    task = details["task"]

    # Build response with all aggregated data
    response_data = {
        # Core task fields
        "id": task.id,
        "user_id": task.user_id,
        "name": task.name,
        "description": task.description,
        "prompt_template": task.prompt_template,
        "allowed_tools": task.allowed_tools,
        "disallowed_tools": task.disallowed_tools,
        "sdk_options": task.sdk_options,
        "working_directory_path": task.working_directory_path,
        "is_scheduled": task.is_scheduled,
        "schedule_cron": task.schedule_cron,
        "schedule_enabled": task.schedule_enabled,
        "generate_report": task.generate_report,
        "report_format": task.report_format,
        "notification_config": task.notification_config,
        "tags": task.tags,
        "is_public": task.is_public,
        "is_active": task.is_active,
        "is_deleted": task.is_deleted,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "deleted_at": task.deleted_at,
    }

    # Add aggregated data
    if details.get("execution_summary"):
        exec_summary = details["execution_summary"]

        # Convert last_execution model to response
        last_exec_response = None
        if exec_summary.get("last_execution"):
            last_exec_model = exec_summary["last_execution"]
            last_exec_response = TaskExecutionResponse(
                id=last_exec_model.id,
                task_id=last_exec_model.task_id,
                session_id=last_exec_model.session_id,
                status=last_exec_model.status,
                trigger_type=last_exec_model.trigger_type,
                prompt_variables=last_exec_model.prompt_variables or {},
                result_data=last_exec_model.result_data,
                report_id=last_exec_model.report_id,
                error_message=last_exec_model.error_message,
                duration_ms=last_exec_model.duration_seconds * 1000 if last_exec_model.duration_seconds else None,
                created_at=last_exec_model.created_at,
                started_at=last_exec_model.started_at,
                completed_at=last_exec_model.completed_at,
                links=Links(
                    self=f"/api/v1/task-executions/{last_exec_model.id}",
                    task=f"/api/v1/tasks/{last_exec_model.task_id}",
                )
            )

        response_data["execution_summary"] = ExecutionSummaryData(
            total_executions=exec_summary["total_executions"],
            successful=exec_summary["successful"],
            failed=exec_summary["failed"],
            cancelled=exec_summary["cancelled"],
            avg_duration_seconds=exec_summary["avg_duration_seconds"],
            success_rate=exec_summary["success_rate"],
            last_execution=last_exec_response,
        )

    # Add recent executions
    if details.get("recent_executions"):
        recent_execs = []
        for exec_model in details["recent_executions"]:
            exec_response = TaskExecutionResponse(
                id=exec_model.id,
                task_id=exec_model.task_id,
                session_id=exec_model.session_id,
                status=exec_model.status,
                trigger_type=exec_model.trigger_type,
                prompt_variables=exec_model.prompt_variables or {},
                result_data=exec_model.result_data,
                report_id=exec_model.report_id,
                error_message=exec_model.error_message,
                duration_ms=exec_model.duration_seconds * 1000 if exec_model.duration_seconds else None,
                created_at=exec_model.created_at,
                started_at=exec_model.started_at,
                completed_at=exec_model.completed_at,
                links=Links(
                    self=f"/api/v1/task-executions/{exec_model.id}",
                    task=f"/api/v1/tasks/{exec_model.task_id}",
                )
            )
            recent_execs.append(exec_response)
        response_data["recent_executions"] = recent_execs

    # Add working directories
    if details.get("working_directories"):
        wd_data = details["working_directories"]

        active_dirs = []
        for wd in wd_data.get("active", []):
            active_dirs.append(WorkingDirectoryInfo(
                execution_id=wd["execution_id"],
                session_id=wd.get("session_id"),
                path=wd["path"],
                size_bytes=wd.get("size_bytes"),
                created_at=wd["created_at"],
                is_archived=wd.get("is_archived", False),
                archive_id=wd.get("archive_id"),
                links=Links(
                    execution=f"/api/v1/task-executions/{wd['execution_id']}",
                ) if wd.get("session_id") else None
            ))

        archived_dirs = []
        for wd in wd_data.get("archived", []):
            archived_dirs.append(WorkingDirectoryInfo(
                execution_id=wd["execution_id"],
                session_id=wd.get("session_id"),
                path=wd["path"],
                size_bytes=wd.get("size_bytes"),
                created_at=wd["created_at"],
                is_archived=True,
                archive_id=wd.get("archive_id"),
                links=Links(
                    execution=f"/api/v1/task-executions/{wd['execution_id']}",
                ) if wd.get("archive_id") else None
            ))

        response_data["working_directories"] = {
            "active": active_dirs,
            "archived": archived_dirs,
        }

    # Add MCP tools
    if details.get("mcp_tools"):
        mcp_tools = []
        for tool_info in details["mcp_tools"]:
            mcp_tools.append(MCPToolInfo(
                server_name=tool_info["server_name"],
                tools=tool_info.get("tools", []),
                enabled=tool_info.get("enabled", True),
                config=tool_info.get("config"),
            ))
        response_data["mcp_tools"] = mcp_tools

    # Add permission policies
    if details.get("permission_policies"):
        response_data["permission_policies"] = PermissionPolicyInfo(
            allowed_tools=details["permission_policies"]["allowed_tools"],
            disallowed_tools=details["permission_policies"]["disallowed_tools"],
        )

    # Add audit summary
    if details.get("audit_summary"):
        response_data["audit_summary"] = AuditSummaryData(
            total_audit_logs=details["audit_summary"]["total_audit_logs"],
            recent_actions=details["audit_summary"]["recent_actions"],
            links=Links(
                audit_logs=f"/api/v1/audit-logs?resource_type=task&resource_id={task.id}",
            )
        )

    # Add reports summary
    if details.get("reports_summary"):
        response_data["reports_summary"] = ReportSummaryData(
            total=details["reports_summary"]["total"],
            recent=details["reports_summary"]["recent"],
            links=Links(
                reports=f"/api/v1/reports?task_id={task.id}",
            )
        )

    # Build comprehensive HATEOAS links
    response_data["_links"] = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
        executions=f"/api/v1/tasks/{task.id}/executions",
        audit_logs=f"/api/v1/audit-logs?resource_type=task&resource_id={task.id}",
        reports=f"/api/v1/reports?task_id={task.id}",
    )

    return TaskDetailedResponse(**response_data)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_scheduled: Optional[bool] = Query(None, description="Filter by scheduled status"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskListResponse:
    """
    List user's tasks with pagination and filtering.
    """
    repo = TaskRepository(db)
    
    # Get tasks
    tasks = await repo.get_by_user(
        user_id=current_user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    
    # Apply filters
    if is_scheduled is not None:
        tasks = [t for t in tasks if t.is_scheduled == is_scheduled]
    if tags:
        tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
    
    # Get total count
    total = len(tasks)
    
    # Convert to response models
    items = []
    for task in tasks:
        response = TaskResponse.model_validate(task)
        response._links = Links(
            self=f"/api/v1/tasks/{task.id}",
            execute=f"/api/v1/tasks/{task.id}/execute",
        )
        items.append(response)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """
    Update task configuration.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    
    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)
    
    # Get task
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Check ownership
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task",
        )
    
    # Update task
    task = await service.update_task(
        task_id=task_id,
        user_id=current_user.id,
        **request.model_dump(exclude_unset=True),
    )
    
    # Build HATEOAS links
    response = TaskResponse.model_validate(task)
    response._links = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
    )
    
    return response


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a task.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    
    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)
    
    # Get task
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    # Check ownership
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task",
        )
    
    # Delete task
    await service.delete_task(str(task_id))


@router.post("/{task_id}/execute", response_model=TaskExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_task(
    task_id: UUID,
    request: TaskExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionResponse:
    """
    Manually execute a task.

    Starts task execution asynchronously. Use the execution ID to check status.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    logger.info(
        "API: Task execution request received",
        extra={
            "task_id": str(task_id),
            "user_id": str(current_user.id),
            "username": current_user.username,
            "variables_count": len(request.variables) if request.variables else 0,
            "event": "api_execute_task_request",
        }
    )

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    # Get task
    repo = TaskRepository(db)
    task = await repo.get_by_id(str(task_id))

    if task is None:
        logger.warning(
            "API: Task not found",
            extra={
                "task_id": str(task_id),
                "user_id": str(current_user.id),
                "event": "task_not_found",
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    logger.info(
        "API: Task loaded successfully",
        extra={
            "task_id": str(task_id),
            "task_name": task.name,
            "event": "task_loaded",
        }
    )

    # Check ownership
    if task.user_id != current_user.id and current_user.role != "admin":
        logger.warning(
            "API: Unauthorized task execution attempt",
            extra={
                "task_id": str(task_id),
                "task_owner_id": str(task.user_id),
                "requester_id": str(current_user.id),
                "requester_role": current_user.role,
                "event": "unauthorized_task_execution",
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to execute this task",
        )

    logger.info(
        "API: Calling TaskService.execute_task()",
        extra={
            "task_id": str(task_id),
            "task_name": task.name,
            "user_id": str(current_user.id),
            "trigger_type": "manual",
            "event": "calling_task_service",
        }
    )

    # Execute task
    execution = await service.execute_task(
        task_id=str(task_id),
        trigger_type="manual",
        variables=request.variables,
    )

    logger.info(
        "API: Task execution initiated successfully",
        extra={
            "task_id": str(task_id),
            "execution_id": str(execution.id),
            "status": execution.status.value,
            "celery_task_id": execution.celery_task_id if hasattr(execution, 'celery_task_id') else None,
            "event": "task_execution_initiated",
        }
    )
    
    # Build HATEOAS links
    response = TaskExecutionResponse.model_validate(execution)
    response._links = Links(
        self=f"/api/v1/task-executions/{execution.id}",
        task=f"/api/v1/tasks/{task.id}",
    )
    if execution.session_id:
        response._links.session = f"/api/v1/sessions/{execution.session_id}"
    
    return response


@router.get("/{task_id}/executions", response_model=TaskExecutionListResponse)
async def list_task_executions(
    task_id: UUID,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionListResponse:
    """
    List executions for a specific task.
    """
    # Get task (check ownership)
    task_repo = TaskRepository(db)
    task = await task_repo.get_by_id(str(task_id))
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )
    
    # Get executions
    exec_repo = TaskExecutionRepository(db)
    executions = await exec_repo.get_by_task(
        task_id=task_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    # Get total count using the repository's count method if available
    # For now, just use the length of executions returned
    total = len(executions)
    
    # Convert to response models
    items = []
    for execution in executions:
        response = TaskExecutionResponse.model_validate(execution)
        response._links = Links(
            self=f"/api/v1/task-executions/{execution.id}",
            task=f"/api/v1/tasks/{task.id}",
        )
        if execution.session_id:
            response._links.session = f"/api/v1/sessions/{execution.session_id}"
        if execution.report_id:
            response._links.report = f"/api/v1/reports/{execution.report_id}"
        items.append(response)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/executions/{execution_id}/retry", response_model=TaskExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_task_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionResponse:
    """
    Retry a failed task execution.

    Schedules a failed or pending execution for background re-execution.
    The task will be executed asynchronously.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.core.logging import get_logger

    logger = get_logger(__name__)

    logger.info(
        "API: Retry execution request received",
        extra={
            "execution_id": str(execution_id),
            "user_id": str(current_user.id),
            "event": "api_retry_execution_request",
        }
    )

    # Get execution
    exec_repo = TaskExecutionRepository(db)
    execution = await exec_repo.get_by_id(str(execution_id))

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found",
        )

    # Check ownership via task
    task_repo = TaskRepository(db)
    task = await task_repo.get_by_id(str(execution.task_id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {execution.task_id} not found",
        )

    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to retry this execution",
        )

    # Check status - only allow retry for queued or failed
    if execution.status not in ["queued", "pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry execution with status '{execution.status}'. Only queued, pending, or failed executions can be retried.",
        )

    logger.info(
        "API: Retrying execution via TaskService",
        extra={
            "execution_id": str(execution_id),
            "task_id": str(task.id),
            "current_status": execution.status,
            "event": "retrying_execution",
        }
    )

    # Use TaskService to re-queue the task
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, exec_repo, user_repo, audit_service)

    try:
        # Reset execution to pending and re-execute
        await exec_repo.update(
            str(execution_id),
            status="pending",
            celery_task_id=None,
            error_message=None,
            started_at=None,
            completed_at=None,
        )
        await db.commit()

        # Re-execute with async mode
        retried_execution = await service._execute_task_async(
            execution=execution,
            task=task,
            variables=execution.prompt_variables or {},
        )

        logger.info(
            "API: Execution retried successfully",
            extra={
                "execution_id": str(execution_id),
                "new_status": retried_execution.status,
                "celery_task_id": retried_execution.celery_task_id if hasattr(retried_execution, 'celery_task_id') else None,
                "event": "execution_retried",
            }
        )

        # Build response
        response = TaskExecutionResponse.model_validate(retried_execution)
        response._links = Links(
            self=f"/api/v1/task-executions/{retried_execution.id}",
            task=f"/api/v1/tasks/{task.id}",
        )
        if retried_execution.session_id:
            response._links.session = f"/api/v1/sessions/{retried_execution.session_id}"

        return response

    except Exception as e:
        logger.error(
            "API: Failed to retry execution",
            extra={
                "execution_id": str(execution_id),
                "error": str(e),
                "error_type": type(e).__name__,
                "event": "retry_failed",
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry execution: {str(e)}",
        )


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
async def get_task_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionResponse:
    """
    Get task execution status and details.
    """
    exec_repo = TaskExecutionRepository(db)
    execution = await exec_repo.get_by_id(str(execution_id))
    
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task execution {execution_id} not found",
        )
    
    # Check ownership via task
    task_repo = TaskRepository(db)
    task = await task_repo.get_by_id(str(execution.task_id))
    
    if task and task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this execution",
        )
    
    # Build HATEOAS links
    response = TaskExecutionResponse.model_validate(execution)
    response._links = Links(
        self=f"/api/v1/task-executions/{execution.id}",
        task=f"/api/v1/tasks/{execution.task_id}",
    )
    if execution.session_id:
        response._links.session = f"/api/v1/sessions/{execution.session_id}"
    if execution.report_id:
        response._links.report = f"/api/v1/reports/{execution.report_id}"

    return response


# ===== NEW ENDPOINTS: Tool Calls, Cancellation, Working Directory Management =====


@router.get("/executions/{execution_id}/tool-calls", response_model=ToolCallListResponse)
async def get_execution_tool_calls(
    execution_id: UUID,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolCallListResponse:
    """
    Get tool calls for a task execution.

    **Note**: Tool calls are only available for sync mode executions (with sessions).
    Async mode executions don't store individual tool call records.

    Returns detailed information about each tool that was executed during the task run,
    including inputs, outputs, timing, and permission decisions.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    try:
        # Get tool calls
        tool_calls = await service.get_execution_tool_calls(
            execution_id=execution_id,
            user_id=current_user.id,
            skip=pagination.offset,
            limit=pagination.limit,
        )

        # Get total count
        total = len(tool_calls)

        # Convert to response models
        items = []
        for tool_call in tool_calls:
            response = ToolCallResponse.model_validate(tool_call)
            response._links = Links(
                self=f"/api/v1/tool-calls/{tool_call.id}",
                execution=f"/api/v1/task-executions/{execution_id}",
            )
            if tool_call.session_id:
                response._links.session = f"/api/v1/sessions/{tool_call.session_id}"
            items.append(response)

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    except Exception as e:
        if "async mode" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        raise


@router.post("/executions/{execution_id}/cancel", response_model=TaskExecutionResponse)
async def cancel_execution(
    execution_id: UUID,
    request: ExecutionCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionResponse:
    """
    Cancel a running task execution.

    **Cancellation behavior**:
    - `PENDING` or `QUEUED`: Cancelled immediately
    - `RUNNING` (async mode): Cancellation flag set, background task will stop
    - `RUNNING` (sync mode): Not supported (requires killing subprocess)
    - `COMPLETED`, `FAILED`, or `CANCELLED`: Cannot cancel (already finished)

    Returns the updated execution with `status=cancelled`.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.domain.exceptions import ValidationError

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    try:
        # Cancel execution
        execution = await service.cancel_execution(
            execution_id=execution_id,
            user_id=current_user.id,
            reason=request.reason,
        )

        # Build response
        response = TaskExecutionResponse.model_validate(execution)
        response._links = Links(
            self=f"/api/v1/task-executions/{execution.id}",
            task=f"/api/v1/tasks/{execution.task_id}",
        )
        if execution.session_id:
            response._links.session = f"/api/v1/sessions/{execution.session_id}"

        return response

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/executions/{execution_id}/files", response_model=WorkingDirectoryManifest)
async def get_execution_files(
    execution_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> WorkingDirectoryManifest:
    """
    Get file manifest for task execution's working directory.

    Returns a list of all files in the execution's working directory with metadata
    (path, size, modified timestamp).

    **Note**: Working directory must still exist (not yet archived or cleaned up).
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.domain.exceptions import ValidationError

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    try:
        # Get file manifest
        manifest_data = await service.get_execution_files(
            execution_id=execution_id,
            user_id=current_user.id,
        )

        # Convert file list to response models
        file_infos = [
            WorkingDirectoryFileInfo(**file_data)
            for file_data in manifest_data["files"]
        ]

        # Build response
        response = WorkingDirectoryManifest(
            execution_id=manifest_data["execution_id"],
            total_files=manifest_data["total_files"],
            total_size=manifest_data["total_size"],
            files=file_infos,
            _links=Links(
                self=f"/api/v1/task-executions/{execution_id}/files",
                execution=f"/api/v1/task-executions/{execution_id}",
                download=f"/api/v1/task-executions/{execution_id}/files/download",
                archive=f"/api/v1/task-executions/{execution_id}/archive",
            )
        )

        return response

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/executions/{execution_id}/files/download")
async def download_execution_files(
    execution_id: UUID,
    file_path: str = Query(..., description="Relative file path within working directory"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Download a specific file from task execution's working directory.

    Specify the relative file path (as returned by the `/files` endpoint) to download.
    """
    from fastapi.responses import FileResponse
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.domain.exceptions import ValidationError
    from pathlib import Path

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    try:
        # Get execution and authorize
        execution = await task_execution_repo.get_by_id(str(execution_id))
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task execution {execution_id} not found",
            )

        task = await task_repo.get_by_id(str(execution.task_id))
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {execution.task_id} not found",
            )

        # Check authorization
        if task.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this execution",
            )

        # Get working directory path
        working_dir = None
        if execution.session_id:
            from app.repositories.session_repository import SessionRepository
            session_repo = SessionRepository(db)
            session = await session_repo.get_by_id(str(execution.session_id))
            if session and session.working_directory_path:
                working_dir = Path(session.working_directory_path)
        elif execution.result_data and execution.result_data.get("working_dir"):
            working_dir = Path(execution.result_data["working_dir"])

        if not working_dir or not working_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Working directory not found. It may have been archived or cleaned up.",
            )

        # Resolve file path (prevent directory traversal)
        requested_file = working_dir / file_path
        if not requested_file.resolve().is_relative_to(working_dir.resolve()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path (directory traversal detected)",
            )

        if not requested_file.exists() or not requested_file.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}",
            )

        # Return file
        return FileResponse(
            path=str(requested_file),
            filename=requested_file.name,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}",
        )


@router.post("/executions/{execution_id}/archive", response_model=ArchiveResponse)
async def archive_execution_directory(
    execution_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveResponse:
    """
    Archive task execution's working directory to tar.gz.

    Creates a compressed archive of all files in the working directory and
    deletes the original directory to save space.

    **Note**: This operation is irreversible. The archived directory can be downloaded
    but cannot be extracted back to its original location.
    """
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    from app.domain.exceptions import ValidationError

    task_repo = TaskRepository(db)
    task_execution_repo = TaskExecutionRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = TaskService(db, task_repo, task_execution_repo, user_repo, audit_service)

    try:
        # Archive directory
        archive_data = await service.archive_execution_directory(
            execution_id=execution_id,
            user_id=current_user.id,
        )

        # Build response
        response = ArchiveResponse(
            execution_id=archive_data["execution_id"],
            archive_path=archive_data["archive_path"],
            archive_size=archive_data["archive_size"],
            created_at=archive_data["created_at"],
            _links=Links(
                self=f"/api/v1/task-executions/{execution_id}/archive",
                execution=f"/api/v1/task-executions/{execution_id}",
                download=f"/api/v1/archives/{archive_data['execution_id']}/download",
            )
        )

        return response

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/archives/{archive_id}/download")
async def download_archive(
    archive_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Download archived working directory as tar.gz.

    The archive_id is the same as the execution_id for which the directory was archived.
    """
    from fastapi.responses import FileResponse
    from app.services.storage_manager import StorageManager
    from pathlib import Path

    task_execution_repo = TaskExecutionRepository(db)
    task_repo = TaskRepository(db)

    # Get execution and authorize
    execution = await task_execution_repo.get_by_id(str(archive_id))
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archive {archive_id} not found",
        )

    task = await task_repo.get_by_id(str(execution.task_id))
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {execution.task_id} not found",
        )

    # Check authorization
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this archive",
        )

    # Find archive file
    storage_mgr = StorageManager()
    archive_dir = storage_mgr.archive_dir

    # Look for archive files matching this execution/session ID
    session_id_for_archive = execution.session_id if execution.session_id else execution.task_id
    matching_archives = list(archive_dir.glob(f"{session_id_for_archive}_*.tar.gz"))

    if not matching_archives:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Archive file not found for execution {archive_id}",
        )

    # Return most recent archive if multiple exist
    archive_path = sorted(matching_archives, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    return FileResponse(
        path=str(archive_path),
        filename=archive_path.name,
        media_type="application/gzip",
    )
