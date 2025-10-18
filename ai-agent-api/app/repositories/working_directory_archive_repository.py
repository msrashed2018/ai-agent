"""Working directory archive repository for database operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.working_directory_archive import WorkingDirectoryArchiveModel
from app.repositories.base import BaseRepository


class WorkingDirectoryArchiveRepository(BaseRepository[WorkingDirectoryArchiveModel]):
    """Repository for working directory archive database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(WorkingDirectoryArchiveModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
    ) -> Optional[WorkingDirectoryArchiveModel]:
        """Get archive for a specific session (one-to-one relationship)."""
        result = await self.db.execute(
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: str,  # 'pending', 'in_progress', 'completed', 'failed'
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkingDirectoryArchiveModel]:
        """Get archives filtered by status."""
        result = await self.db.execute(
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.status == status)
            .order_by(WorkingDirectoryArchiveModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_storage_backend(
        self,
        storage_backend: str,  # 's3', 'filesystem'
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkingDirectoryArchiveModel]:
        """Get archives filtered by storage backend."""
        result = await self.db.execute(
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.storage_backend == storage_backend)
            .order_by(WorkingDirectoryArchiveModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_archives(
        self,
        limit: int = 100,
    ) -> List[WorkingDirectoryArchiveModel]:
        """Get all pending archives for processing."""
        result = await self.db.execute(
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.status == "pending")
            .order_by(WorkingDirectoryArchiveModel.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_failed_archives(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkingDirectoryArchiveModel]:
        """Get all failed archives for retry or investigation."""
        result = await self.db.execute(
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.status == "failed")
            .order_by(WorkingDirectoryArchiveModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
