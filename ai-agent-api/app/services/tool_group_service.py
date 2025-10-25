"""Tool Group service for business logic."""
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tool_group import ToolGroup
from app.domain.exceptions import ValidationError, PermissionDeniedError
from app.repositories.tool_group_repository import ToolGroupRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolGroupService:
    """Business logic for tool group management."""

    def __init__(
        self,
        db: AsyncSession,
        tool_group_repo: ToolGroupRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.tool_group_repo = tool_group_repo
        self.user_repo = user_repo
        self.audit_service = audit_service

    async def create_tool_group(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        disallowed_tools: Optional[List[str]] = None,
    ) -> ToolGroup:
        """Create a new tool group."""
        logger.info(
            "Creating new tool group",
            extra={
                "user_id": str(user_id),
                "group_name": name,
                "allowed_tools_count": len(allowed_tools) if allowed_tools else 0,
                "disallowed_tools_count": len(disallowed_tools) if disallowed_tools else 0,
            }
        )

        # Validate name uniqueness
        existing = await self.tool_group_repo.get_by_name(user_id, name)
        if existing:
            raise ValidationError(f"Tool group '{name}' already exists for this user")

        # Create entity
        tool_group = ToolGroup(
            id=uuid4(),
            user_id=user_id,
            name=name,
            description=description,
        )

        tool_group.allowed_tools = allowed_tools or []
        tool_group.disallowed_tools = disallowed_tools or []

        # Persist
        await self.tool_group_repo.create(tool_group)
        await self.db.commit()

        logger.info(
            "Tool group created successfully",
            extra={
                "user_id": str(user_id),
                "tool_group_id": str(tool_group.id),
                "group_name": name,
            }
        )

        # Audit log
        await self.audit_service.log_action(
            user_id=user_id,
            action_type="tool_group.created",
            resource_type="tool_group",
            resource_id=tool_group.id,
            action_details={"name": name},
        )

        return tool_group

    async def get_tool_group(
        self,
        tool_group_id: UUID,
        user_id: UUID,
    ) -> ToolGroup:
        """Get tool group with authorization check."""
        tool_group = await self.tool_group_repo.get_by_id(str(tool_group_id))

        if not tool_group:
            raise ValidationError(f"Tool group {tool_group_id} not found")

        # Check authorization
        if tool_group.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user or (user.role != "admin" and not tool_group.is_public):
                raise PermissionDeniedError("Not authorized to access this tool group")

        return tool_group

    async def list_tool_groups(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolGroup]:
        """List tool groups for a user."""
        return await self.tool_group_repo.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    async def update_tool_group(
        self,
        tool_group_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        disallowed_tools: Optional[List[str]] = None,
    ) -> ToolGroup:
        """Update a tool group."""
        # Get and authorize
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        # Only owner can update
        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can update")

        # Validate name uniqueness if changing name
        if name and name != tool_group.name:
            existing = await self.tool_group_repo.get_by_name(user_id, name)
            if existing:
                raise ValidationError(f"Tool group '{name}' already exists for this user")

        # Update entity
        updates = {}
        audit_details = {}

        if name is not None:
            updates["name"] = name
            audit_details["name"] = name
        if description is not None:
            updates["description"] = description
            audit_details["description"] = description
        if allowed_tools is not None:
            updates["allowed_tools"] = allowed_tools
            audit_details["allowed_tools_count"] = len(allowed_tools)
        if disallowed_tools is not None:
            updates["disallowed_tools"] = disallowed_tools
            audit_details["disallowed_tools_count"] = len(disallowed_tools)

        updates["updated_at"] = datetime.utcnow()

        updated = await self.tool_group_repo.update(str(tool_group_id), **updates)
        await self.db.commit()

        logger.info(
            "Tool group updated",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(user_id),
                "updated_fields": [k for k in updates.keys() if k != "updated_at"],
            }
        )

        # Audit log - use audit_details (excludes non-serializable datetime)
        await self.audit_service.log_action(
            user_id=user_id,
            action_type="tool_group.updated",
            resource_type="tool_group",
            resource_id=tool_group_id,
            action_details=audit_details,
        )

        return updated

    async def delete_tool_group(
        self,
        tool_group_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft delete a tool group."""
        logger.info(
            "Deleting tool group",
            extra={
                "tool_group_id": str(tool_group_id),
                "user_id": str(user_id),
            }
        )

        # Get and authorize
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        # Only owner can delete
        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can delete")

        success = await self.tool_group_repo.soft_delete(str(tool_group_id))
        await self.db.commit()

        if success:
            logger.info(
                "Tool group deleted successfully",
                extra={
                    "tool_group_id": str(tool_group_id),
                    "user_id": str(user_id),
                }
            )

            # Audit log
            await self.audit_service.log_action(
                user_id=user_id,
                action_type="tool_group.deleted",
                resource_type="tool_group",
                resource_id=tool_group_id,
            )

        return success

    async def add_tool_to_allowed(
        self,
        tool_group_id: UUID,
        user_id: UUID,
        tool: str,
    ) -> ToolGroup:
        """Add tool to allowed list."""
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can update")

        if tool not in tool_group.allowed_tools:
            tool_group.allowed_tools.append(tool)

        await self.tool_group_repo.update(
            str(tool_group_id),
            allowed_tools=tool_group.allowed_tools,
            updated_at=datetime.utcnow(),
        )
        await self.db.commit()

        return tool_group

    async def remove_tool_from_allowed(
        self,
        tool_group_id: UUID,
        user_id: UUID,
        tool: str,
    ) -> ToolGroup:
        """Remove tool from allowed list."""
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can update")

        if tool in tool_group.allowed_tools:
            tool_group.allowed_tools.remove(tool)

        await self.tool_group_repo.update(
            str(tool_group_id),
            allowed_tools=tool_group.allowed_tools,
            updated_at=datetime.utcnow(),
        )
        await self.db.commit()

        return tool_group

    async def add_tool_to_disallowed(
        self,
        tool_group_id: UUID,
        user_id: UUID,
        tool: str,
    ) -> ToolGroup:
        """Add tool to disallowed list."""
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can update")

        if tool not in tool_group.disallowed_tools:
            tool_group.disallowed_tools.append(tool)

        await self.tool_group_repo.update(
            str(tool_group_id),
            disallowed_tools=tool_group.disallowed_tools,
            updated_at=datetime.utcnow(),
        )
        await self.db.commit()

        return tool_group

    async def remove_tool_from_disallowed(
        self,
        tool_group_id: UUID,
        user_id: UUID,
        tool: str,
    ) -> ToolGroup:
        """Remove tool from disallowed list."""
        tool_group = await self.get_tool_group(tool_group_id, user_id)

        if tool_group.user_id != user_id:
            raise PermissionDeniedError("Only tool group owner can update")

        if tool in tool_group.disallowed_tools:
            tool_group.disallowed_tools.remove(tool)

        await self.tool_group_repo.update(
            str(tool_group_id),
            disallowed_tools=tool_group.disallowed_tools,
            updated_at=datetime.utcnow(),
        )
        await self.db.commit()

        return tool_group
