"""Session template service for business logic."""
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.session_template import SessionTemplate, TemplateCategory
from app.domain.exceptions import (
    TemplateNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.repositories.session_template_repository import SessionTemplateRepository
from app.repositories.user_repository import UserRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.audit_service import AuditService
from app.models.session_template import SessionTemplateModel


class SessionTemplateService:
    """Business logic for session template management."""

    def __init__(
        self,
        db: AsyncSession,
        template_repo: SessionTemplateRepository,
        user_repo: UserRepository,
        mcp_server_repo: MCPServerRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.template_repo = template_repo
        self.user_repo = user_repo
        self.mcp_server_repo = mcp_server_repo
        self.audit_service = audit_service

    async def create_template(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        sdk_options: Optional[dict] = None,
        mcp_server_ids: Optional[List[UUID]] = None,
        is_public: bool = False,
        is_organization_shared: bool = False,
        tags: Optional[List[str]] = None,
        template_metadata: Optional[dict] = None,
    ) -> SessionTemplate:
        """Create a new session template."""
        # 1. Validate user exists
        user = await self.user_repo.get_by_id(str(user_id))
        if not user:
            raise ValidationError("User not found")

        # 2. Validate MCP servers if provided
        if mcp_server_ids:
            await self._validate_mcp_servers(user_id, mcp_server_ids)

        # 3. Create template entity
        template = SessionTemplate(
            id=uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            system_prompt=system_prompt,
            working_directory=working_directory,
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
            mcp_server_ids=mcp_server_ids,
            is_public=is_public,
            is_organization_shared=is_organization_shared,
            tags=tags,
            template_metadata=template_metadata,
        )

        # 4. Persist template
        template_model = self._entity_to_model(template)
        self.db.add(template_model)
        await self.db.flush()

        # 5. Audit log
        await self.audit_service.log_template_created(
            template_id=template.id,
            user_id=user_id,
            template_name=name,
        )

        await self.db.commit()
        return template

    async def get_template(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> SessionTemplate:
        """Get template by ID with authorization check."""
        template_model = await self.template_repo.get_by_id(str(template_id))
        if not template_model:
            raise TemplateNotFoundError(f"Template {template_id} not found")

        template = self._model_to_entity(template_model)

        # Check access permission
        user = await self.user_repo.get_by_id(str(user_id))
        if not template.is_accessible_by_user(user_id, user.organization_id):
            raise PermissionDeniedError("Not authorized to access this template")

        return template

    async def list_user_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplate]:
        """List all templates owned by a user."""
        template_models = await self.template_repo.get_by_user(user_id, skip, limit)
        return [self._model_to_entity(model) for model in template_models]

    async def list_public_templates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplate]:
        """List all public templates."""
        template_models = await self.template_repo.get_public_templates(skip, limit)
        return [self._model_to_entity(model) for model in template_models]

    async def list_accessible_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplate]:
        """List all templates accessible to a user (owned + public + org-shared)."""
        template_models = await self.template_repo.get_accessible_templates(
            user_id, skip, limit
        )
        return [self._model_to_entity(model) for model in template_models]

    async def search_templates(
        self,
        user_id: UUID,
        search_term: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplate]:
        """Search templates by various criteria."""
        if search_term:
            template_models = await self.template_repo.search_by_name(
                search_term, user_id, skip, limit
            )
        elif category:
            template_models = await self.template_repo.get_by_category(
                category.value, user_id, skip, limit
            )
        elif tags:
            template_models = await self.template_repo.search_by_tags(
                tags, user_id, skip, limit
            )
        else:
            template_models = await self.template_repo.get_accessible_templates(
                user_id, skip, limit
            )

        return [self._model_to_entity(model) for model in template_models]

    async def update_template(
        self,
        template_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        sdk_options: Optional[dict] = None,
        mcp_server_ids: Optional[List[UUID]] = None,
        tags: Optional[List[str]] = None,
        template_metadata: Optional[dict] = None,
    ) -> SessionTemplate:
        """Update an existing template."""
        # 1. Get template with authorization check
        template = await self.get_template(template_id, user_id)

        # 2. Only owner can update
        if template.user_id != user_id:
            raise PermissionDeniedError("Only template owner can update it")

        # 3. Validate MCP servers if being updated
        if mcp_server_ids is not None:
            await self._validate_mcp_servers(user_id, mcp_server_ids)

        # 4. Update template entity
        template.update_configuration(
            name=name,
            description=description,
            category=category,
            system_prompt=system_prompt,
            working_directory=working_directory,
            allowed_tools=allowed_tools,
            sdk_options=sdk_options,
            mcp_server_ids=mcp_server_ids,
        )

        # 5. Update tags if provided
        if tags is not None:
            template.tags = tags
            template.updated_at = datetime.utcnow()

        # 6. Update metadata if provided
        if template_metadata is not None:
            template.update_metadata(template_metadata)

        # 7. Persist changes
        template_model = await self.template_repo.get_by_id(str(template_id))
        if template_model:
            self._update_model_from_entity(template_model, template)
            await self.db.flush()

        # 8. Audit log
        await self.audit_service.log_template_updated(
            template_id=template_id,
            user_id=user_id,
        )

        await self.db.commit()
        return template

    async def update_sharing_settings(
        self,
        template_id: UUID,
        user_id: UUID,
        is_public: Optional[bool] = None,
        is_organization_shared: Optional[bool] = None,
    ) -> SessionTemplate:
        """Update template sharing settings."""
        # 1. Get template with authorization check
        template = await self.get_template(template_id, user_id)

        # 2. Only owner can update sharing settings
        if template.user_id != user_id:
            raise PermissionDeniedError("Only template owner can update sharing settings")

        # 3. Update sharing settings
        template.update_sharing_settings(is_public, is_organization_shared)

        # 4. Persist changes
        template_model = await self.template_repo.get_by_id(str(template_id))
        if template_model:
            if is_public is not None:
                template_model.is_public = is_public
            if is_organization_shared is not None:
                template_model.is_organization_shared = is_organization_shared
            template_model.updated_at = datetime.utcnow()
            await self.db.flush()

        await self.db.commit()
        return template

    async def delete_template(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> None:
        """Soft delete a template."""
        # 1. Get template with authorization check
        template = await self.get_template(template_id, user_id)

        # 2. Only owner can delete
        if template.user_id != user_id:
            raise PermissionDeniedError("Only template owner can delete it")

        # 3. Soft delete
        await self.template_repo.soft_delete(template_id)

        # 4. Audit log
        await self.audit_service.log_template_deleted(
            template_id=template_id,
            user_id=user_id,
        )

        await self.db.commit()

    async def increment_usage(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> SessionTemplate:
        """Increment template usage count (called when creating session from template)."""
        # 1. Get template (with access check)
        template = await self.get_template(template_id, user_id)

        # 2. Increment usage
        template.increment_usage()

        # 3. Persist changes
        await self.template_repo.update_usage_stats(template_id)

        await self.db.commit()
        return template

    async def get_most_used_templates(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[SessionTemplate]:
        """Get most frequently used templates accessible to user."""
        template_models = await self.template_repo.get_most_used(limit, user_id)
        return [self._model_to_entity(model) for model in template_models]

    async def _validate_mcp_servers(
        self,
        user_id: UUID,
        mcp_server_ids: List[UUID],
    ) -> None:
        """Validate that all MCP servers exist and are accessible to user."""
        for server_id in mcp_server_ids:
            server = await self.mcp_server_repo.get_by_id(str(server_id))
            if not server:
                raise ValidationError(f"MCP Server {server_id} not found")
            if server.user_id != user_id:
                raise PermissionDeniedError(
                    f"Not authorized to use MCP Server {server_id}"
                )

    def _entity_to_model(self, entity: SessionTemplate) -> SessionTemplateModel:
        """Convert domain entity to database model."""
        return SessionTemplateModel(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            category=entity.category.value if entity.category else None,
            system_prompt=entity.system_prompt,
            working_directory=entity.working_directory,
            allowed_tools=entity.allowed_tools,
            sdk_options=entity.sdk_options,
            mcp_server_ids=entity.mcp_server_ids,
            is_public=entity.is_public,
            is_organization_shared=entity.is_organization_shared,
            version=entity.version,
            tags=entity.tags,
            template_metadata=entity.template_metadata,
            usage_count=entity.usage_count,
            last_used_at=entity.last_used_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    def _model_to_entity(self, model: SessionTemplateModel) -> SessionTemplate:
        """Convert database model to domain entity."""
        entity = SessionTemplate(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            category=TemplateCategory(model.category) if model.category else None,
            system_prompt=model.system_prompt,
            working_directory=model.working_directory,
            allowed_tools=model.allowed_tools or [],
            sdk_options=model.sdk_options or {},
            mcp_server_ids=model.mcp_server_ids or [],
            is_public=model.is_public,
            is_organization_shared=model.is_organization_shared,
            version=model.version,
            tags=model.tags or [],
            template_metadata=model.template_metadata or {},
        )

        # Set statistics and timestamps from model
        entity.usage_count = model.usage_count
        entity.last_used_at = model.last_used_at
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at
        entity.deleted_at = model.deleted_at

        return entity

    def _update_model_from_entity(
        self,
        model: SessionTemplateModel,
        entity: SessionTemplate,
    ) -> None:
        """Update model fields from entity."""
        model.name = entity.name
        model.description = entity.description
        model.category = entity.category.value if entity.category else None
        model.system_prompt = entity.system_prompt
        model.working_directory = entity.working_directory
        model.allowed_tools = entity.allowed_tools
        model.sdk_options = entity.sdk_options
        model.mcp_server_ids = entity.mcp_server_ids
        model.is_public = entity.is_public
        model.is_organization_shared = entity.is_organization_shared
        model.tags = entity.tags
        model.template_metadata = entity.template_metadata
        model.updated_at = entity.updated_at
