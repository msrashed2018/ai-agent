"""Report repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import ReportModel
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[ReportModel]):
    """Repository for report database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(ReportModel, db)

    async def get_by_id(self, report_id: UUID) -> Optional[ReportModel]:
        """Get report by ID (excluding soft-deleted)."""
        result = await self.db.execute(
            select(ReportModel).where(
                and_(
                    ReportModel.id == report_id,
                    ReportModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get all reports for a session."""
        result = await self.db.execute(
            select(ReportModel)
            .where(
                and_(
                    ReportModel.session_id == session_id,
                    ReportModel.deleted_at.is_(None)
                )
            )
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get all reports for a user."""
        result = await self.db.execute(
            select(ReportModel)
            .where(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.deleted_at.is_(None)
                )
            )
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_task_execution(
        self,
        task_execution_id: UUID,
    ) -> Optional[ReportModel]:
        """Get report by task execution ID."""
        result = await self.db.execute(
            select(ReportModel).where(
                and_(
                    ReportModel.task_execution_id == task_execution_id,
                    ReportModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_tags(
        self,
        tags: List[str],
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get reports that have any of the specified tags."""
        filters = [
            ReportModel.tags.overlap(tags),
            ReportModel.deleted_at.is_(None)
        ]
        
        if user_id:
            filters.append(ReportModel.user_id == user_id)
        
        result = await self.db.execute(
            select(ReportModel)
            .where(and_(*filters))
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_public_reports(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get all public reports."""
        result = await self.db.execute(
            select(ReportModel)
            .where(
                and_(
                    ReportModel.is_public == True,
                    ReportModel.deleted_at.is_(None)
                )
            )
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_report_type(
        self,
        report_type: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get reports by type."""
        filters = [
            ReportModel.report_type == report_type,
            ReportModel.deleted_at.is_(None)
        ]
        
        if user_id:
            filters.append(ReportModel.user_id == user_id)
        
        result = await self.db.execute(
            select(ReportModel)
            .where(and_(*filters))
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_format(
        self,
        file_format: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ReportModel]:
        """Get reports by file format."""
        filters = [
            ReportModel.file_format == file_format,
            ReportModel.deleted_at.is_(None)
        ]
        
        if user_id:
            filters.append(ReportModel.user_id == user_id)
        
        result = await self.db.execute(
            select(ReportModel)
            .where(and_(*filters))
            .order_by(ReportModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def soft_delete(self, report_id: UUID) -> bool:
        """Soft delete a report."""
        stmt = (
            update(ReportModel)
            .where(ReportModel.id == report_id)
            .values(deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def search_content(
        self,
        search_text: str,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[ReportModel]:
        """Search reports by content text."""
        filters = [
            ReportModel.content.op('@>')(f'{{"text": "{search_text}"}}'),
            ReportModel.deleted_at.is_(None)
        ]
        
        if user_id:
            filters.append(ReportModel.user_id == user_id)
        
        result = await self.db.execute(
            select(ReportModel)
            .where(and_(*filters))
            .order_by(ReportModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: UUID) -> int:
        """Count reports for a user."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(ReportModel)
            .where(
                and_(
                    ReportModel.user_id == user_id,
                    ReportModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()
