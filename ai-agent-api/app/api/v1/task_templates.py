"""
Task templates API endpoints.
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
from app.repositories.task_template_repository import TaskTemplateRepository
from app.repositories.task_repository import TaskRepository
from app.services.task_template_service import TaskTemplateService
from app.schemas.task_template import (
    TaskTemplateCreateRequest,
    TaskTemplateUpdateRequest,
    TaskTemplateResponse,
    TaskTemplateListResponse,
    CreateTaskFromTemplateRequest,
    TaskTemplateStatsResponse,
)
from app.schemas.task import TaskResponse
from app.schemas.common import Links


router = APIRouter(prefix="/task-templates", tags=["task-templates"])


@router.post("", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_task_template(
    request: TaskTemplateCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateResponse:
    """
    Create a new task template.

    Only admin users can create templates.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create task templates"
        )

    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    # Create template
    template = await service.create_template(
        name=request.name,
        description=request.description,
        category=request.category,
        prompt_template=request.prompt_template,
        template_variables_schema=request.template_variables_schema,
        allowed_tools=request.allowed_tools,
        disallowed_tools=request.disallowed_tools,
        sdk_options=request.sdk_options,
        generate_report=request.generate_report,
        report_format=request.report_format,
        tags=request.tags,
        icon=request.icon,
    )

    # Build HATEOAS links
    response = TaskTemplateResponse.model_validate(template)
    response._links = Links(
        self=f"/api/v1/task-templates/{template.id}",
        create_task=f"/api/v1/task-templates/{template.id}/create-task",
    )

    return response


@router.get("", response_model=TaskTemplateListResponse)
async def list_task_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateListResponse:
    """
    List task templates with optional filters.

    All users can view templates.
    """
    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    # Get templates
    templates, total = await service.list_templates(
        category=category,
        tags=tags,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    # Build response
    items = []
    for template in templates:
        template_response = TaskTemplateResponse.model_validate(template)
        template_response._links = Links(
            self=f"/api/v1/task-templates/{template.id}",
            create_task=f"/api/v1/task-templates/{template.id}/create-task",
        )
        items.append(template_response)

    return TaskTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats", response_model=TaskTemplateStatsResponse)
async def get_template_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateStatsResponse:
    """
    Get task template statistics.
    """
    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    stats = await service.get_template_stats()

    # Build most used responses with links
    most_used = []
    for template in stats["most_used"]:
        template_response = TaskTemplateResponse.model_validate(template)
        template_response._links = Links(
            self=f"/api/v1/task-templates/{template.id}",
            create_task=f"/api/v1/task-templates/{template.id}/create-task",
        )
        most_used.append(template_response)

    return TaskTemplateStatsResponse(
        total_templates=stats["total_templates"],
        active_templates=stats["active_templates"],
        categories=stats["categories"],
        most_used=most_used,
    )


@router.get("/category/{category}", response_model=TaskTemplateListResponse)
async def get_templates_by_category(
    category: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateListResponse:
    """
    Get templates by category.
    """
    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    # Get templates by category
    all_templates = await service.get_templates_by_category(category)

    # Paginate
    skip = (page - 1) * page_size
    templates = all_templates[skip:skip + page_size]
    total = len(all_templates)

    # Build response
    items = []
    for template in templates:
        template_response = TaskTemplateResponse.model_validate(template)
        template_response._links = Links(
            self=f"/api/v1/task-templates/{template.id}",
            create_task=f"/api/v1/task-templates/{template.id}/create-task",
        )
        items.append(template_response)

    return TaskTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{template_id}", response_model=TaskTemplateResponse)
async def get_task_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateResponse:
    """
    Get task template by ID.
    """
    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    template = await service.get_template(template_id)

    # Build HATEOAS links
    response = TaskTemplateResponse.model_validate(template)
    response._links = Links(
        self=f"/api/v1/task-templates/{template.id}",
        create_task=f"/api/v1/task-templates/{template.id}/create-task",
    )

    return response


@router.patch("/{template_id}", response_model=TaskTemplateResponse)
async def update_task_template(
    template_id: UUID,
    request: TaskTemplateUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskTemplateResponse:
    """
    Update a task template.

    Only admin users can update templates.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update task templates"
        )

    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    # Update template
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    template = await service.update_template(template_id, **update_data)

    # Build HATEOAS links
    response = TaskTemplateResponse.model_validate(template)
    response._links = Links(
        self=f"/api/v1/task-templates/{template.id}",
        create_task=f"/api/v1/task-templates/{template.id}/create-task",
    )

    return response


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a task template.

    Only admin users can delete templates.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete task templates"
        )

    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    await service.delete_template(template_id)


@router.post("/{template_id}/create-task", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_from_template(
    template_id: UUID,
    request: CreateTaskFromTemplateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """
    Create a task from a template.

    All users can create tasks from templates.
    """
    template_repo = TaskTemplateRepository(db)
    task_repo = TaskRepository(db)
    service = TaskTemplateService(db, template_repo, task_repo)

    # Create task from template
    task = await service.create_task_from_template(
        template_id=template_id,
        user_id=current_user.id,
        custom_name=request.name,
        custom_description=request.description,
        additional_tags=request.tags,
        is_scheduled=request.is_scheduled,
        schedule_cron=request.schedule_cron,
        schedule_enabled=request.schedule_enabled,
    )

    # Build HATEOAS links
    response = TaskResponse.model_validate(task)
    response._links = Links(
        self=f"/api/v1/tasks/{task.id}",
        execute=f"/api/v1/tasks/{task.id}/execute",
        executions=f"/api/v1/tasks/{task.id}/executions",
    )

    return response
