"""Permission decision repository for database operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.permission_decision import PermissionDecisionModel
from app.repositories.base import BaseRepository


class PermissionDecisionRepository(BaseRepository[PermissionDecisionModel]):
    """Repository for permission decision database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(PermissionDecisionModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PermissionDecisionModel]:
        """Get all permission decisions for a session."""
        result = await self.db.execute(
            select(PermissionDecisionModel)
            .where(PermissionDecisionModel.session_id == session_id)
            .order_by(PermissionDecisionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_decision(
        self,
        session_id: UUID,
        decision: str,  # 'allowed', 'denied', 'bypassed'
        skip: int = 0,
        limit: int = 100,
    ) -> List[PermissionDecisionModel]:
        """Get permission decisions filtered by decision type."""
        result = await self.db.execute(
            select(PermissionDecisionModel)
            .where(
                and_(
                    PermissionDecisionModel.session_id == session_id,
                    PermissionDecisionModel.decision == decision
                )
            )
            .order_by(PermissionDecisionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tool_name(
        self,
        session_id: UUID,
        tool_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PermissionDecisionModel]:
        """Get permission decisions for a specific tool."""
        result = await self.db.execute(
            select(PermissionDecisionModel)
            .where(
                and_(
                    PermissionDecisionModel.session_id == session_id,
                    PermissionDecisionModel.tool_name == tool_name
                )
            )
            .order_by(PermissionDecisionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_decision(
        self,
        session_id: UUID,
        decision: str,
    ) -> int:
        """Count permission decisions by type for a session."""
        result = await self.db.execute(
            select(func.count())
            .select_from(PermissionDecisionModel)
            .where(
                and_(
                    PermissionDecisionModel.session_id == session_id,
                    PermissionDecisionModel.decision == decision
                )
            )
        )
        return result.scalar_one()

    async def get_denied_decisions(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PermissionDecisionModel]:
        """Get all denied permission decisions for a session."""
        return await self.get_by_decision(session_id, "denied", skip, limit)
