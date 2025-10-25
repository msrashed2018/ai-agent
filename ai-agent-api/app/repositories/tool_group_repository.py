"""Tool Group repository for data access."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.tool_group import ToolGroupModel
from app.domain.entities.tool_group import ToolGroup


class ToolGroupRepository:
    """Repository for tool group data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tool_group: ToolGroup) -> ToolGroup:
        """Create a new tool group."""
        model = ToolGroupModel(
            id=tool_group.id,
            user_id=tool_group.user_id,
            name=tool_group.name,
            description=tool_group.description,
            allowed_tools=tool_group.allowed_tools,
            disallowed_tools=tool_group.disallowed_tools,
            is_public=tool_group.is_public,
            is_active=tool_group.is_active,
            created_at=tool_group.created_at,
            updated_at=tool_group.updated_at,
        )
        self.db.add(model)
        await self.db.flush()
        return tool_group

    async def get_by_id(self, tool_group_id: str) -> Optional[ToolGroup]:
        """Get tool group by ID."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.id == UUID(tool_group_id),
            ToolGroupModel.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolGroup]:
        """Get tool groups for a user."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.user_id == user_id,
            ToolGroupModel.is_deleted == False,
        ).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def get_by_name(self, user_id: UUID, name: str) -> Optional[ToolGroup]:
        """Get tool group by user and name."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.user_id == user_id,
            ToolGroupModel.name == name,
            ToolGroupModel.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def update(
        self,
        tool_group_id: str,
        **updates,
    ) -> Optional[ToolGroup]:
        """Update tool group."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.id == UUID(tool_group_id),
            ToolGroupModel.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)

        await self.db.flush()
        return self._model_to_entity(model)

    async def soft_delete(self, tool_group_id: str) -> bool:
        """Soft delete a tool group."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.id == UUID(tool_group_id),
            ToolGroupModel.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.is_deleted = True
        model.deleted_at = __import__('datetime').datetime.utcnow()
        await self.db.flush()
        return True

    async def count_by_user(self, user_id: UUID) -> int:
        """Count active tool groups for a user."""
        stmt = select(ToolGroupModel).where(
            ToolGroupModel.user_id == user_id,
            ToolGroupModel.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return len(models)

    def _model_to_entity(self, model: ToolGroupModel) -> ToolGroup:
        """Convert database model to domain entity."""
        entity = ToolGroup(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
        )
        entity.allowed_tools = model.allowed_tools or []
        entity.disallowed_tools = model.disallowed_tools or []
        entity.is_public = model.is_public
        entity.is_active = model.is_active
        entity.is_deleted = model.is_deleted
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at
        entity.deleted_at = model.deleted_at
        return entity
