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
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.models.task import Task as TaskModel
from app.models.user import User as UserModel
from app.schemas.admin import SystemStatsResponse
from app.schemas.common import PaginationParams


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
    # Task statistics
    task_repo = TaskRepository(db)
    total_tasks = await task_repo.count()

    # User statistics
    user_repo = UserRepository(db)
    total_users = await user_repo.count()

    return SystemStatsResponse(
        sessions={
            "total": 0,
            "active": 0,
            "completed_today": 0,
        },
        tasks={
            "total": total_tasks or 0,
            "scheduled_enabled": 0,
            "executions_today": 0,
        },
        users={
            "total": total_users or 0,
            "active_today": 0,
        },
        cost={
            "total_usd": 0.0,
            "today_usd": 0.0,
        },
        storage={
            "working_dirs_mb": 0,
            "reports_mb": 0,
            "archives_mb": 0,
        },
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
