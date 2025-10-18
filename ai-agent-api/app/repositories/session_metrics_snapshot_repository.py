"""Session metrics snapshot repository for database operations."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session_metrics_snapshot import SessionMetricsSnapshotModel
from app.repositories.base import BaseRepository


class SessionMetricsSnapshotRepository(BaseRepository[SessionMetricsSnapshotModel]):
    """Repository for session metrics snapshot database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionMetricsSnapshotModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionMetricsSnapshotModel]:
        """Get all metrics snapshots for a session."""
        result = await self.db.execute(
            select(SessionMetricsSnapshotModel)
            .where(SessionMetricsSnapshotModel.session_id == session_id)
            .order_by(SessionMetricsSnapshotModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_snapshot_type(
        self,
        session_id: UUID,
        snapshot_type: str,  # 'hourly', 'checkpoint', 'final'
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionMetricsSnapshotModel]:
        """Get metrics snapshots filtered by type."""
        result = await self.db.execute(
            select(SessionMetricsSnapshotModel)
            .where(
                and_(
                    SessionMetricsSnapshotModel.session_id == session_id,
                    SessionMetricsSnapshotModel.snapshot_type == snapshot_type
                )
            )
            .order_by(SessionMetricsSnapshotModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_snapshot(
        self,
        session_id: UUID,
    ) -> Optional[SessionMetricsSnapshotModel]:
        """Get the most recent metrics snapshot for a session."""
        result = await self.db.execute(
            select(SessionMetricsSnapshotModel)
            .where(SessionMetricsSnapshotModel.session_id == session_id)
            .order_by(SessionMetricsSnapshotModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_snapshots_in_range(
        self,
        session_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> List[SessionMetricsSnapshotModel]:
        """Get metrics snapshots within a specific time range."""
        result = await self.db.execute(
            select(SessionMetricsSnapshotModel)
            .where(
                and_(
                    SessionMetricsSnapshotModel.session_id == session_id,
                    SessionMetricsSnapshotModel.created_at >= start_time,
                    SessionMetricsSnapshotModel.created_at <= end_time
                )
            )
            .order_by(SessionMetricsSnapshotModel.created_at)
        )
        return list(result.scalars().all())

    async def get_final_snapshot(
        self,
        session_id: UUID,
    ) -> Optional[SessionMetricsSnapshotModel]:
        """Get the final metrics snapshot for a session."""
        result = await self.db.execute(
            select(SessionMetricsSnapshotModel)
            .where(
                and_(
                    SessionMetricsSnapshotModel.session_id == session_id,
                    SessionMetricsSnapshotModel.snapshot_type == "final"
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
