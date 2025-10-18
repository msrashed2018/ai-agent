"""
Session Templates API endpoints.
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
from app.domain.entities import User, TemplateCategory
from app.domain.exceptions import (
    TemplateNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.repositories.session_template_repository import SessionTemplateRepository
from app.repositories.user_repository import UserRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.session_template_service import SessionTemplateService
from app.services.audit_service import AuditService
from app.schemas.session_template import (
    SessionTemplateCreateRequest,
    SessionTemplateUpdateRequest,
    SessionTemplateSharingUpdateRequest,
    SessionTemplateResponse,
    SessionTemplateListResponse,
    SessionTemplateSearchRequest,
)
from app.schemas.common import PaginationParams, PaginatedResponse, Links


router = APIRouter(prefix="/session-templates", tags=["session-templates"])


def get_template_service(
    db: AsyncSession = Depends(get_db_session),
) -> SessionTemplateService:
    """Get session template service instance."""
    return SessionTemplateService(
        db=db,
        template_repo=SessionTemplateRepository(db),
        user_repo=UserRepository(db),
        mcp_server_repo=MCPServerRepository(db),
        audit_service=AuditService(db),
    )


@router.post("", response_model=SessionTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: SessionTemplateCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateResponse:
    """
    Create a new session template.

    Creates a reusable session configuration template that can be used
    to quickly create new sessions with pre-configured settings.

    **Backend Flow**:
    1. Validate user exists and has permission to create templates
    2. Validate MCP servers if provided (must exist and be accessible)
    3. Create SessionTemplate domain entity
    4. Persist to database via repository
    5. Log template creation to audit trail
    6. Return template with HATEOAS links
    """
    try:
        # Parse category enum if provided
        category = TemplateCategory(request.category) if request.category else None

        template = await service.create_template(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            category=category,
            system_prompt=request.system_prompt,
            working_directory=request.working_directory,
            allowed_tools=request.allowed_tools,
            sdk_options=request.sdk_options,
            mcp_server_ids=request.mcp_server_ids,
            is_public=request.is_public,
            is_organization_shared=request.is_organization_shared,
            tags=request.tags,
            template_metadata=request.template_metadata,
        )

        # Build response with HATEOAS links
        response = SessionTemplateResponse.model_validate(template)
        response._links = Links(
            self=f"/api/v1/session-templates/{template.id}",
        )

        return response

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{template_id}", response_model=SessionTemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateResponse:
    """
    Get session template by ID.

    Returns template details with full configuration.
    User must have access to the template (owner, public, or org-shared).

    **Backend Flow**:
    1. Retrieve template from database by ID
    2. Check if template exists (raise 404 if not)
    3. Verify user has access (owner, public, or org-shared)
    4. Return template with HATEOAS links
    """
    try:
        template = await service.get_template(template_id, current_user.id)

        # Build response with HATEOAS links
        response = SessionTemplateResponse.model_validate(template)
        response._links = Links(
            self=f"/api/v1/session-templates/{template.id}",
            update=f"/api/v1/session-templates/{template.id}",
            delete=f"/api/v1/session-templates/{template.id}",
            create_session=f"/api/v1/sessions?template_id={template.id}",
        )

        return response

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this template",
        )


@router.get("", response_model=SessionTemplateListResponse)
async def list_templates(
    scope: Optional[str] = Query("accessible", description="Scope: 'my', 'public', 'accessible'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateListResponse:
    """
    List session templates with filtering.

    **Scopes**:
    - `my`: Only templates owned by current user
    - `public`: Only public templates (available to all users)
    - `accessible`: All templates accessible to user (owned + public + org-shared)

    **Backend Flow**:
    1. Parse scope parameter
    2. Query templates based on scope and filters
    3. Apply pagination (offset/limit)
    4. Convert models to response DTOs
    5. Build paginated response with HATEOAS links
    """
    try:
        # Get templates based on scope
        if scope == "my":
            templates = await service.list_user_templates(
                current_user.id,
                skip=pagination.offset,
                limit=pagination.limit,
            )
        elif scope == "public":
            templates = await service.list_public_templates(
                skip=pagination.offset,
                limit=pagination.limit,
            )
        else:  # accessible
            if category:
                # Filter by category
                category_enum = TemplateCategory(category)
                templates = await service.search_templates(
                    user_id=current_user.id,
                    category=category_enum,
                    skip=pagination.offset,
                    limit=pagination.limit,
                )
            else:
                templates = await service.list_accessible_templates(
                    current_user.id,
                    skip=pagination.offset,
                    limit=pagination.limit,
                )

        # Convert to response models
        items = []
        for template in templates:
            response = SessionTemplateResponse.model_validate(template)
            response._links = Links(
                self=f"/api/v1/session-templates/{template.id}",
            )
            items.append(response)

        # Calculate total (simplified - in production use count query)
        total = len(items)

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameter: {str(e)}",
        )


@router.post("/search", response_model=SessionTemplateListResponse)
async def search_templates(
    request: SessionTemplateSearchRequest,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateListResponse:
    """
    Search session templates.

    Search by name, category, or tags. Results include templates
    accessible to the current user.

    **Backend Flow**:
    1. Parse search criteria (search_term, category, tags)
    2. Query repository with search filters
    3. Apply pagination
    4. Return paginated results with HATEOAS links
    """
    try:
        offset = (request.page - 1) * request.page_size

        # Parse category if provided
        category = TemplateCategory(request.category) if request.category else None

        templates = await service.search_templates(
            user_id=current_user.id,
            search_term=request.search_term,
            category=category,
            tags=request.tags,
            skip=offset,
            limit=request.page_size,
        )

        # Convert to response models
        items = []
        for template in templates:
            response = SessionTemplateResponse.model_validate(template)
            response._links = Links(
                self=f"/api/v1/session-templates/{template.id}",
            )
            items.append(response)

        total = len(items)

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameter: {str(e)}",
        )


@router.get("/popular/top", response_model=List[SessionTemplateResponse])
async def get_most_used_templates(
    limit: int = Query(10, ge=1, le=50, description="Number of templates to return"),
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> List[SessionTemplateResponse]:
    """
    Get most frequently used templates.

    Returns templates sorted by usage count, filtered to those
    accessible by the current user.

    **Backend Flow**:
    1. Query templates ordered by usage_count DESC
    2. Filter to templates accessible to user
    3. Limit results
    4. Return with HATEOAS links
    """
    templates = await service.get_most_used_templates(
        user_id=current_user.id,
        limit=limit,
    )

    # Convert to response models
    items = []
    for template in templates:
        response = SessionTemplateResponse.model_validate(template)
        response._links = Links(
            self=f"/api/v1/session-templates/{template.id}",
            create_session=f"/api/v1/sessions?template_id={template.id}",
        )
        items.append(response)

    return items


@router.put("/{template_id}", response_model=SessionTemplateResponse)
async def update_template(
    template_id: UUID,
    request: SessionTemplateUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateResponse:
    """
    Update session template.

    Only the template owner can update the template.
    Partial updates are supported - only provided fields are updated.

    **Backend Flow**:
    1. Retrieve template and verify ownership
    2. Validate new MCP servers if provided
    3. Update template entity with new values
    4. Persist changes to database
    5. Log update to audit trail
    6. Return updated template
    """
    try:
        # Parse category if provided
        category = TemplateCategory(request.category) if request.category else None

        template = await service.update_template(
            template_id=template_id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            category=category,
            system_prompt=request.system_prompt,
            working_directory=request.working_directory,
            allowed_tools=request.allowed_tools,
            sdk_options=request.sdk_options,
            mcp_server_ids=request.mcp_server_ids,
            tags=request.tags,
            template_metadata=request.template_metadata,
        )

        # Build response
        response = SessionTemplateResponse.model_validate(template)
        response._links = Links(
            self=f"/api/v1/session-templates/{template.id}",
        )

        return response

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only template owner can update it",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{template_id}/sharing", response_model=SessionTemplateResponse)
async def update_sharing_settings(
    template_id: UUID,
    request: SessionTemplateSharingUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> SessionTemplateResponse:
    """
    Update template sharing settings.

    Only the template owner can update sharing settings.

    **Backend Flow**:
    1. Retrieve template and verify ownership
    2. Update is_public and/or is_organization_shared flags
    3. Persist changes
    4. Return updated template
    """
    try:
        template = await service.update_sharing_settings(
            template_id=template_id,
            user_id=current_user.id,
            is_public=request.is_public,
            is_organization_shared=request.is_organization_shared,
        )

        # Build response
        response = SessionTemplateResponse.model_validate(template)
        response._links = Links(
            self=f"/api/v1/session-templates/{template.id}",
        )

        return response

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only template owner can update sharing settings",
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: SessionTemplateService = Depends(get_template_service),
) -> None:
    """
    Delete session template (soft delete).

    Only the template owner can delete the template.
    Template is soft-deleted (marked as deleted but not removed from database).

    **Backend Flow**:
    1. Retrieve template and verify ownership
    2. Soft delete template (set deleted_at timestamp)
    3. Log deletion to audit trail
    4. Return 204 No Content
    """
    try:
        await service.delete_template(
            template_id=template_id,
            user_id=current_user.id,
        )

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only template owner can delete it",
        )
