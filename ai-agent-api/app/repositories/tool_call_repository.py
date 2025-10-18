"""Tool call repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tool_call import ToolCallModel
from app.repositories.base import BaseRepository


class ToolCallRepository(BaseRepository[ToolCallModel]):
    """Repository for tool call database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(ToolCallModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolCallModel]:
        """Get all tool calls for a session."""
        result = await self.db.execute(
            select(ToolCallModel)
            .where(ToolCallModel.session_id == session_id)
            .order_by(ToolCallModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tool_use_id(self, tool_use_id: str) -> Optional[ToolCallModel]:
        """Get tool call by tool_use_id."""
        result = await self.db.execute(
            select(ToolCallModel).where(ToolCallModel.tool_use_id == tool_use_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: str,
        session_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolCallModel]:
        """Get tool calls by status, optionally filtered by session."""
        filters = [ToolCallModel.status == status]
        
        if session_id:
            filters.append(ToolCallModel.session_id == session_id)
        
        result = await self.db.execute(
            select(ToolCallModel)
            .where(and_(*filters))
            .order_by(ToolCallModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_tool_name(
        self,
        tool_name: str,
        session_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolCallModel]:
        """Get tool calls by tool name, optionally filtered by session."""
        filters = [ToolCallModel.tool_name == tool_name]
        
        if session_id:
            filters.append(ToolCallModel.session_id == session_id)
        
        result = await self.db.execute(
            select(ToolCallModel)
            .where(and_(*filters))
            .order_by(ToolCallModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_for_permission(
        self,
        session_id: Optional[UUID] = None,
    ) -> List[ToolCallModel]:
        """Get pending tool calls awaiting permission decision."""
        filters = [
            ToolCallModel.status == 'pending',
            ToolCallModel.permission_decision.is_(None)
        ]
        
        if session_id:
            filters.append(ToolCallModel.session_id == session_id)
        
        result = await self.db.execute(
            select(ToolCallModel)
            .where(and_(*filters))
            .order_by(ToolCallModel.created_at)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        tool_call_id: UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update tool call status."""
        values = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if error_message:
            values["error_message"] = error_message
            values["is_error"] = True
        
        if status == 'running' and not error_message:
            values["started_at"] = datetime.utcnow()
        elif status in ['success', 'error']:
            values["completed_at"] = datetime.utcnow()
        
        stmt = update(ToolCallModel).where(ToolCallModel.id == tool_call_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def set_permission_decision(
        self,
        tool_call_id: UUID,
        decision: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Set permission decision for a tool call."""
        values = {
            "permission_decision": decision,
            "permission_reason": reason,
            "updated_at": datetime.utcnow()
        }
        
        if decision == 'deny':
            values["status"] = 'denied'
        
        stmt = update(ToolCallModel).where(ToolCallModel.id == tool_call_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def set_output(
        self,
        tool_call_id: UUID,
        output: dict,
        is_error: bool = False,
    ) -> bool:
        """Set tool call output."""
        values = {
            "tool_output": output,
            "is_error": is_error,
            "status": 'error' if is_error else 'success',
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        stmt = update(ToolCallModel).where(ToolCallModel.id == tool_call_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_by_session(self, session_id: UUID) -> int:
        """Count tool calls in a session."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(ToolCallModel)
            .where(ToolCallModel.session_id == session_id)
        )
        return result.scalar_one()

    async def get_statistics_by_tool(
        self,
        session_id: Optional[UUID] = None,
    ) -> List[dict]:
        """Get tool call statistics grouped by tool name."""
        from sqlalchemy import func
        
        query = select(
            ToolCallModel.tool_name,
            func.count(ToolCallModel.id).label('total_calls'),
            func.count().filter(ToolCallModel.status == 'success').label('success_count'),
            func.count().filter(ToolCallModel.status == 'error').label('error_count'),
            func.avg(ToolCallModel.duration_ms).label('avg_duration_ms')
        ).group_by(ToolCallModel.tool_name)
        
        if session_id:
            query = query.where(ToolCallModel.session_id == session_id)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "tool_name": row.tool_name,
                "total_calls": row.total_calls,
                "success_count": row.success_count,
                "error_count": row.error_count,
                "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms else None
            }
            for row in rows
        ]
