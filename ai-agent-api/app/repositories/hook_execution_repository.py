"""Hook execution repository for database operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.hook_execution import HookExecutionModel
from app.repositories.base import BaseRepository


class HookExecutionRepository(BaseRepository[HookExecutionModel]):
    """Repository for hook execution database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(HookExecutionModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HookExecutionModel]:
        """Get all hook executions for a session."""
        result = await self.db.execute(
            select(HookExecutionModel)
            .where(HookExecutionModel.session_id == session_id)
            .order_by(HookExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_hook_name(
        self,
        session_id: UUID,
        hook_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HookExecutionModel]:
        """Get hook executions filtered by hook name."""
        result = await self.db.execute(
            select(HookExecutionModel)
            .where(
                and_(
                    HookExecutionModel.session_id == session_id,
                    HookExecutionModel.hook_name == hook_name
                )
            )
            .order_by(HookExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tool_use_id(
        self,
        tool_use_id: str,
    ) -> List[HookExecutionModel]:
        """Get all hook executions for a specific tool use."""
        result = await self.db.execute(
            select(HookExecutionModel)
            .where(HookExecutionModel.tool_use_id == tool_use_id)
            .order_by(HookExecutionModel.created_at)
        )
        return list(result.scalars().all())

    async def get_failed_executions(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HookExecutionModel]:
        """Get hook executions that failed (have error_message)."""
        result = await self.db.execute(
            select(HookExecutionModel)
            .where(
                and_(
                    HookExecutionModel.session_id == session_id,
                    HookExecutionModel.error_message.isnot(None)
                )
            )
            .order_by(HookExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
