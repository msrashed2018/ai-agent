"""Task repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import TaskModel
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[TaskModel]):
    """Repository for task database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(TaskModel, db)

    async def get_by_id(self, task_id: UUID) -> Optional[TaskModel]:
        """Get task by ID (excluding soft-deleted)."""
        result = await self.db.execute(
            select(TaskModel).where(
                and_(
                    TaskModel.id == task_id,
                    TaskModel.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[TaskModel]:
        """Get all tasks for a user."""
        filters = [TaskModel.user_id == user_id]
        
        if not include_deleted:
            filters.append(TaskModel.is_deleted == False)
        
        result = await self.db.execute(
            select(TaskModel)
            .where(and_(*filters))
            .order_by(TaskModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_name(
        self,
        name: str,
        user_id: UUID,
    ) -> Optional[TaskModel]:
        """Get task by name and user."""
        result = await self.db.execute(
            select(TaskModel).where(
                and_(
                    TaskModel.name == name,
                    TaskModel.user_id == user_id,
                    TaskModel.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_scheduled_tasks(
        self,
        enabled_only: bool = True,
    ) -> List[TaskModel]:
        """Get all scheduled tasks."""
        filters = [
            TaskModel.is_scheduled == True,
            TaskModel.is_deleted == False
        ]
        
        if enabled_only:
            filters.append(TaskModel.schedule_enabled == True)
        
        result = await self.db.execute(
            select(TaskModel).where(and_(*filters))
        )
        return list(result.scalars().all())

    async def get_by_tags(
        self,
        tags: List[str],
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskModel]:
        """Get tasks that have any of the specified tags."""
        filters = [
            TaskModel.tags.overlap(tags),
            TaskModel.is_deleted == False
        ]
        
        if user_id:
            filters.append(TaskModel.user_id == user_id)
        
        result = await self.db.execute(
            select(TaskModel)
            .where(and_(*filters))
            .order_by(TaskModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_public_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskModel]:
        """Get all public tasks."""
        result = await self.db.execute(
            select(TaskModel)
            .where(
                and_(
                    TaskModel.is_public == True,
                    TaskModel.is_deleted == False
                )
            )
            .order_by(TaskModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def soft_delete(self, task_id: UUID) -> bool:
        """Soft delete a task."""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def activate(self, task_id: UUID) -> bool:
        """Activate a task."""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(is_active=True, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def deactivate(self, task_id: UUID) -> bool:
        """Deactivate a task."""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def enable_schedule(self, task_id: UUID) -> bool:
        """Enable task schedule."""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(schedule_enabled=True, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def disable_schedule(self, task_id: UUID) -> bool:
        """Disable task schedule."""
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(schedule_enabled=False, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_by_user(self, user_id: UUID, include_deleted: bool = False) -> int:
        """Count tasks for a user."""
        from sqlalchemy import func
        
        filters = [TaskModel.user_id == user_id]
        if not include_deleted:
            filters.append(TaskModel.is_deleted == False)
        
        result = await self.db.execute(
            select(func.count())
            .select_from(TaskModel)
            .where(and_(*filters))
        )
        return result.scalar_one()
