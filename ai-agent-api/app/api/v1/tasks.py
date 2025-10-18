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
    service = TaskService(db)
    
    # Create task
    task = await service.create_task(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        prompt_template=request.prompt_template,
        allowed_tools=request.allowed_tools,
        sdk_options=request.sdk_options,
        is_scheduled=request.is_scheduled,
        schedule_cron=request.schedule_cron,
        schedule_enabled=request.schedule_enabled,
        generate_report=request.generate_report,
        report_format=request.report_format,
        notification_config=request.notification_config,
        tags=request.tags,
        metadata=request.metadata,
    )
    
    # Build HATEOAS links
    response = TaskResponse.model_validate(task)
    response._links = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
        executions=f"/api/v1/tasks/{task.id}/executions",
    )
    
    return response


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """
    Get task details by ID.
    """
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
            detail="Not authorized to access this task",
        )
    
    # Build HATEOAS links
    response = TaskResponse.model_validate(task)
    response._links = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
        executions=f"/api/v1/tasks/{task.id}/executions",
    )
    
    return response


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
    service = TaskService(db)
    
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
        task_id=str(task_id),
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
    service = TaskService(db)
    
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
    service = TaskService(db)
    
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
            detail="Not authorized to execute this task",
        )
    
    # Execute task
    execution = await service.execute_task(
        task_id=str(task_id),
        trigger_type="manual",
        variables=request.variables,
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
    executions = await exec_repo.list_by_task(
        task_id=str(task_id),
        offset=pagination.offset,
        limit=pagination.limit,
    )
    
    # Get total count
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
