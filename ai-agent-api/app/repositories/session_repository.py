"""Session repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import SessionModel
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[SessionModel]):
    """Repository for session database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionModel, db)

    async def get_by_id(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session by ID (excluding soft-deleted)."""
        result = await self.db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.id == session_id,
                    SessionModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionModel]:
        """Get all sessions for a user (excluding soft-deleted)."""
        result = await self.db.execute(
            select(SessionModel)
            .where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionModel]:
        """Get all sessions (excluding soft-deleted) - admin use only."""
        result = await self.db.execute(
            select(SessionModel)
            .where(SessionModel.deleted_at.is_(None))
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_sessions(self, user_id: UUID) -> List[SessionModel]:
        """Get all active sessions for a user."""
        result = await self.db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status.in_(['active', 'waiting', 'processing']),
                    SessionModel.deleted_at.is_(None)
                )
            )
        )
        return list(result.scalars().all())

    async def count_active_sessions(self, user_id: UUID) -> int:
        """Count active sessions for a user."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(SessionModel).where(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.status.in_(['active', 'waiting', 'processing']),
                    SessionModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionModel]:
        """Get sessions by status."""
        result = await self.db.execute(
            select(SessionModel)
            .where(
                and_(
                    SessionModel.status == status,
                    SessionModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_mode(
        self,
        mode: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionModel]:
        """Get sessions by mode, optionally filtered by user."""
        filters = [
            SessionModel.mode == mode,
            SessionModel.deleted_at.is_(None)
        ]
        
        if user_id:
            filters.append(SessionModel.user_id == user_id)
        
        result = await self.db.execute(
            select(SessionModel)
            .where(and_(*filters))
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_completed_before(
        self,
        cutoff_date: datetime,
        limit: int = 1000,
    ) -> List[SessionModel]:
        """Get completed sessions older than cutoff date for archival."""
        result = await self.db.execute(
            select(SessionModel)
            .where(
                and_(
                    SessionModel.status.in_(['completed', 'failed', 'terminated']),
                    SessionModel.completed_at < cutoff_date,
                    SessionModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionModel.completed_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_forked_sessions(
        self,
        parent_session_id: UUID,
    ) -> List[SessionModel]:
        """Get all sessions forked from a parent session."""
        result = await self.db.execute(
            select(SessionModel).where(
                and_(
                    SessionModel.parent_session_id == parent_session_id,
                    SessionModel.is_fork == True,
                    SessionModel.deleted_at.is_(None)
                )
            )
        )
        return list(result.scalars().all())

    async def soft_delete(self, session_id: UUID) -> bool:
        """Soft delete a session."""
        from sqlalchemy import update
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def update_metrics(
        self,
        session_id: UUID,
        total_messages: Optional[int] = None,
        total_tool_calls: Optional[int] = None,
        total_cost_usd: Optional[float] = None,
        api_input_tokens: Optional[int] = None,
        api_output_tokens: Optional[int] = None,
        api_cache_creation_tokens: Optional[int] = None,
        api_cache_read_tokens: Optional[int] = None,
    ) -> bool:
        """Update session metrics."""
        from sqlalchemy import update
        values = {"updated_at": datetime.utcnow()}
        
        if total_messages is not None:
            values["total_messages"] = total_messages
        if total_tool_calls is not None:
            values["total_tool_calls"] = total_tool_calls
        if total_cost_usd is not None:
            values["total_cost_usd"] = total_cost_usd
        if api_input_tokens is not None:
            values["api_input_tokens"] = api_input_tokens
        if api_output_tokens is not None:
            values["api_output_tokens"] = api_output_tokens
        if api_cache_creation_tokens is not None:
            values["api_cache_creation_tokens"] = api_cache_creation_tokens
        if api_cache_read_tokens is not None:
            values["api_cache_read_tokens"] = api_cache_read_tokens
        
        stmt = update(SessionModel).where(SessionModel.id == session_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
