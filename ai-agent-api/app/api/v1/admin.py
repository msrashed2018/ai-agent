"""
Admin API endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime, timedelta

from app.api.dependencies import require_admin, get_db_session
from app.domain.entities import User
from app.repositories.session_repository import SessionRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.models.session import Session as SessionModel
from app.models.task import Task as TaskModel
from app.models.user import User as UserModel
from app.schemas.admin import SystemStatsResponse, AdminSessionListResponse
from app.schemas.session import SessionResponse
from app.schemas.common import PaginationParams, PaginatedResponse, Links
from app.schemas.mappers import session_to_response


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> SystemStatsResponse:
    """
    Get system-wide statistics (admin only).
    
    Returns aggregated statistics across all users.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Session statistics
    total_sessions = await db.scalar(
        select(func.count()).select_from(SessionModel)
    )
    active_sessions = await db.scalar(
        select(func.count()).select_from(SessionModel).where(SessionModel.status == "active")
    )
    completed_today = await db.scalar(
        select(func.count()).select_from(SessionModel).where(
            SessionModel.status == "completed",
            SessionModel.completed_at >= today_start,
        )
    )
    
    # Task statistics
    total_tasks = await db.scalar(
        select(func.count()).select_from(TaskModel)
    )
    scheduled_enabled = await db.scalar(
        select(func.count()).select_from(TaskModel).where(
            TaskModel.is_scheduled == True,
            TaskModel.schedule_enabled == True,
        )
    )
    
    # User statistics
    total_users = await db.scalar(
        select(func.count()).select_from(UserModel).where(UserModel.deleted_at.is_(None))
    )
    
    # Cost statistics
    total_cost = await db.scalar(
        select(func.sum(SessionModel.total_cost_usd)).select_from(SessionModel)
    ) or 0.0
    today_cost = await db.scalar(
        select(func.sum(SessionModel.total_cost_usd)).select_from(SessionModel).where(
            SessionModel.updated_at >= today_start,
        )
    ) or 0.0
    
    return SystemStatsResponse(
        sessions={
            "total": total_sessions or 0,
            "active": active_sessions or 0,
            "completed_today": completed_today or 0,
        },
        tasks={
            "total": total_tasks or 0,
            "scheduled_enabled": scheduled_enabled or 0,
            "executions_today": 0,  # Would need task_executions table query
        },
        users={
            "total": total_users or 0,
            "active_today": 0,  # Would need activity tracking
        },
        cost={
            "total_usd": float(total_cost),
            "today_usd": float(today_cost),
        },
        storage={
            "working_dirs_mb": 0,  # Would need filesystem scan
            "reports_mb": 0,
            "archives_mb": 0,
        },
    )


@router.get("/sessions", response_model=AdminSessionListResponse)
async def list_all_sessions(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    pagination: PaginationParams = Depends(),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> AdminSessionListResponse:
    """
    List all sessions across all users (admin only).
    
    Supports filtering by user ID and status.
    """
    repo = SessionRepository(db)
    
    if user_id:
        # Filter by specific user
        sessions = await repo.get_by_user(
            user_id=user_id,
            skip=pagination.offset,
            limit=pagination.limit,
        )
    else:
        # Get all sessions
        sessions = await repo.get_all(
            skip=pagination.offset,
            limit=pagination.limit,
        )
    
    # Apply status filter
    if status_filter:
        sessions = [s for s in sessions if s.status == status_filter]
    
    # Get total count
    total = len(sessions)
    
    # Convert to response models
    items = []
    for session in sessions:
        response = session_to_response(session)
        response._links = Links(
            self=f"/api/v1/sessions/{session.id}",
            user=f"/api/v1/admin/users/{session.user_id}",
        )
        items.append(response)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/users", response_model=dict)
async def list_all_users(
    include_deleted: bool = Query(False, description="Include deleted users"),
    pagination: PaginationParams = Depends(),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    List all users (admin only).
    """
    repo = UserRepository(db)
    
    # Build query
    query = select(UserModel)
    if not include_deleted:
        query = query.where(UserModel.deleted_at.is_(None))
    
    # Add pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    # Execute
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get total count
    count_query = select(func.count()).select_from(UserModel)
    if not include_deleted:
        count_query = count_query.where(UserModel.deleted_at.is_(None))
    total = await db.scalar(count_query) or 0
    
    # Convert to dict (would normally use UserResponse schema)
    items = [
        {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_deleted": user.deleted_at is not None,
            "created_at": user.created_at.isoformat(),
        }
        for user in users
    ]
    
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": (total + pagination.page_size - 1) // pagination.page_size,
    }
