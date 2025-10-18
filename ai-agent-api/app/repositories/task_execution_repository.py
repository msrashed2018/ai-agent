"""Task execution repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task_execution import TaskExecutionModel
from app.repositories.base import BaseRepository


class TaskExecutionRepository(BaseRepository[TaskExecutionModel]):
    """Repository for task execution database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(TaskExecutionModel, db)

    async def get_by_task(
        self,
        task_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskExecutionModel]:
        """Get all executions for a task."""
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(TaskExecutionModel.task_id == task_id)
            .order_by(TaskExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_session(self, session_id: UUID) -> Optional[TaskExecutionModel]:
        """Get task execution by session ID."""
        result = await self.db.execute(
            select(TaskExecutionModel).where(TaskExecutionModel.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: str,
        task_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskExecutionModel]:
        """Get task executions by status."""
        filters = [TaskExecutionModel.status == status]
        
        if task_id:
            filters.append(TaskExecutionModel.task_id == task_id)
        
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(and_(*filters))
            .order_by(TaskExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_trigger_type(
        self,
        trigger_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TaskExecutionModel]:
        """Get task executions by trigger type."""
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(TaskExecutionModel.trigger_type == trigger_type)
            .order_by(TaskExecutionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_execution(self, task_id: UUID) -> Optional[TaskExecutionModel]:
        """Get the latest execution for a task."""
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(TaskExecutionModel.task_id == task_id)
            .order_by(TaskExecutionModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_successful_executions(
        self,
        task_id: UUID,
        limit: int = 10,
    ) -> List[TaskExecutionModel]:
        """Get recent successful executions for a task."""
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(
                and_(
                    TaskExecutionModel.task_id == task_id,
                    TaskExecutionModel.status == 'completed'
                )
            )
            .order_by(TaskExecutionModel.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_failed_executions(
        self,
        task_id: UUID,
        limit: int = 10,
    ) -> List[TaskExecutionModel]:
        """Get recent failed executions for a task."""
        result = await self.db.execute(
            select(TaskExecutionModel)
            .where(
                and_(
                    TaskExecutionModel.task_id == task_id,
                    TaskExecutionModel.status == 'failed'
                )
            )
            .order_by(TaskExecutionModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        execution_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None,
    ) -> bool:
        """Update execution status."""
        values = {
            "status": status
        }

        if error_message:
            values["error_message"] = error_message

        if result_data:
            values["result_data"] = result_data

        if status == 'running' and not error_message:
            values["started_at"] = datetime.utcnow()
        elif status in ['completed', 'failed', 'cancelled']:
            values["completed_at"] = datetime.utcnow()

        stmt = update(TaskExecutionModel).where(TaskExecutionModel.id == execution_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def set_report(self, execution_id: UUID, report_id: UUID) -> bool:
        """Link a report to an execution."""
        stmt = (
            update(TaskExecutionModel)
            .where(TaskExecutionModel.id == execution_id)
            .values(report_id=report_id)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_by_task(self, task_id: UUID) -> int:
        """Count executions for a task."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(TaskExecutionModel)
            .where(TaskExecutionModel.task_id == task_id)
        )
        return result.scalar_one()

    async def get_execution_stats(self, task_id: UUID) -> dict:
        """Get execution statistics for a task."""
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(
                func.count(TaskExecutionModel.id).label('total'),
                func.count().filter(TaskExecutionModel.status == 'completed').label('completed'),
                func.count().filter(TaskExecutionModel.status == 'failed').label('failed'),
                func.count().filter(TaskExecutionModel.status == 'cancelled').label('cancelled'),
                func.avg(TaskExecutionModel.duration_seconds).label('avg_duration')
            ).where(TaskExecutionModel.task_id == task_id)
        )
        
        row = result.first()
        
        return {
            "total": row.total or 0,
            "completed": row.completed or 0,
            "failed": row.failed or 0,
            "cancelled": row.cancelled or 0,
            "avg_duration_seconds": float(row.avg_duration) if row.avg_duration else None
        }
