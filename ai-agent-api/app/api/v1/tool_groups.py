"""
Tool Groups API endpoints.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.domain.entities import User
from app.repositories.tool_group_repository import ToolGroupRepository
from app.services.tool_group_service import ToolGroupService
from app.schemas.tool_group import (
    ToolGroupCreateRequest,
    ToolGroupUpdateRequest,
    ToolGroupResponse,
    ToolGroupListResponse,
    AddToolRequest,
    RemoveToolRequest,
)
from app.schemas.common import PaginationParams
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tool-groups", tags=["tool-groups"])


@router.get("", response_model=ToolGroupListResponse)
async def list_tool_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupListResponse:
    """
    List all tool groups for the current user.

    Returns both user's own tool groups.
    """
    repo = ToolGroupRepository(db)

    # Get user's tool groups
    tool_groups = await repo.get_by_user(current_user.id, skip=skip, limit=limit)
    total = await repo.count_by_user(current_user.id)

    # Convert to response models
    items = [ToolGroupResponse.model_validate(group) for group in tool_groups]

    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return ToolGroupListResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=ToolGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_tool_group(
    request: ToolGroupCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Create a new tool group.

    Tool groups allow organizing and reusing sets of allowed and disallowed tools.
    """
    from app.services.audit_service import AuditService

    repo = ToolGroupRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, None, audit_service)

    try:
        # Create tool group
        tool_group = await service.create_tool_group(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            allowed_tools=request.allowed_tools,
            disallowed_tools=request.disallowed_tools,
        )

        response = ToolGroupResponse.model_validate(tool_group)
        return response
    except Exception as e:
        logger.error(
            "Failed to create tool group",
            extra={"user_id": str(current_user.id), "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{tool_group_id}", response_model=ToolGroupResponse)
async def get_tool_group(
    tool_group_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Get tool group details by ID.
    """
    repo = ToolGroupRepository(db)
    tool_group = await repo.get_by_id(str(tool_group_id))

    if tool_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool group {tool_group_id} not found",
        )

    # Check authorization
    if tool_group.user_id != current_user.id:
        if current_user.role != "admin" and not tool_group.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this tool group",
            )

    return ToolGroupResponse.model_validate(tool_group)


@router.patch("/{tool_group_id}", response_model=ToolGroupResponse)
async def update_tool_group(
    tool_group_id: UUID,
    request: ToolGroupUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Update a tool group.
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    # Get tool group
    tool_group = await repo.get_by_id(str(tool_group_id))

    if tool_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool group {tool_group_id} not found",
        )

    # Check ownership
    if tool_group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tool group owner can update",
        )

    try:
        # Update tool group
        updated = await service.update_tool_group(
            tool_group_id=tool_group_id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            allowed_tools=request.allowed_tools,
            disallowed_tools=request.disallowed_tools,
        )

        return ToolGroupResponse.model_validate(updated)
    except Exception as e:
        logger.error(
            "Failed to update tool group",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{tool_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_group(
    tool_group_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a tool group (soft delete).
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    # Get tool group
    tool_group = await repo.get_by_id(str(tool_group_id))

    if tool_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool group {tool_group_id} not found",
        )

    # Check ownership
    if tool_group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tool group owner can delete",
        )

    try:
        await service.delete_tool_group(tool_group_id, current_user.id)
    except Exception as e:
        logger.error(
            "Failed to delete tool group",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{tool_group_id}/allowed-tools", response_model=ToolGroupResponse)
async def add_allowed_tool(
    tool_group_id: UUID,
    request: AddToolRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Add a tool to the allowed list.
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    try:
        tool_group = await service.add_tool_to_allowed(
            tool_group_id=tool_group_id,
            user_id=current_user.id,
            tool=request.tool,
        )
        return ToolGroupResponse.model_validate(tool_group)
    except Exception as e:
        logger.error(
            "Failed to add allowed tool",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "tool": request.tool,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{tool_group_id}/allowed-tools/{tool}")
async def remove_allowed_tool(
    tool_group_id: UUID,
    tool: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Remove a tool from the allowed list.
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    try:
        tool_group = await service.remove_tool_from_allowed(
            tool_group_id=tool_group_id,
            user_id=current_user.id,
            tool=tool,
        )
        return ToolGroupResponse.model_validate(tool_group)
    except Exception as e:
        logger.error(
            "Failed to remove allowed tool",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "tool": tool,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{tool_group_id}/disallowed-tools", response_model=ToolGroupResponse)
async def add_disallowed_tool(
    tool_group_id: UUID,
    request: AddToolRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Add a tool to the disallowed list.
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    try:
        tool_group = await service.add_tool_to_disallowed(
            tool_group_id=tool_group_id,
            user_id=current_user.id,
            tool=request.tool,
        )
        return ToolGroupResponse.model_validate(tool_group)
    except Exception as e:
        logger.error(
            "Failed to add disallowed tool",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "tool": request.tool,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{tool_group_id}/disallowed-tools/{tool}")
async def remove_disallowed_tool(
    tool_group_id: UUID,
    tool: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ToolGroupResponse:
    """
    Remove a tool from the disallowed list.
    """
    from app.services.audit_service import AuditService
    from app.repositories.user_repository import UserRepository

    repo = ToolGroupRepository(db)
    user_repo = UserRepository(db)
    audit_service = AuditService(db)
    service = ToolGroupService(db, repo, user_repo, audit_service)

    try:
        tool_group = await service.remove_tool_from_disallowed(
            tool_group_id=tool_group_id,
            user_id=current_user.id,
            tool=tool,
        )
        return ToolGroupResponse.model_validate(tool_group)
    except Exception as e:
        logger.error(
            "Failed to remove disallowed tool",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(current_user.id),
                "tool": tool,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
