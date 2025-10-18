"""
Monitoring API endpoints for health checks, metrics, and cost tracking.
"""

from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_active_user,
    get_db_session,
    get_health_checker,
    get_cost_tracker,
    get_metrics_collector,
)
from app.domain.entities import User
from app.claude_sdk.monitoring.cost_tracker import TimePeriod


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check(
    health_checker = Depends(get_health_checker)
) -> Dict[str, Any]:
    """
    Overall system health check.

    Checks the health of all system components including database,
    Claude SDK, S3 storage, and MCP servers.

    Returns:
        Health status with individual component checks
    """
    health_status = await health_checker.get_health_status()
    return health_status


@router.get("/health/database")
async def database_health(
    health_checker = Depends(get_health_checker)
) -> Dict[str, bool]:
    """Check database connectivity."""
    is_healthy = await health_checker.check_database()
    return {"healthy": is_healthy}


@router.get("/health/sdk")
async def sdk_health(
    health_checker = Depends(get_health_checker)
) -> Dict[str, bool]:
    """Check Claude SDK availability."""
    is_available = await health_checker.check_sdk_availability()
    return {"available": is_available}


@router.get("/health/storage")
async def storage_health(
    health_checker = Depends(get_health_checker)
) -> Dict[str, bool]:
    """Check storage (S3 or filesystem) availability."""
    is_healthy = await health_checker.check_s3_storage()
    return {"healthy": is_healthy}


@router.get("/costs/user/{user_id}")
async def get_user_costs(
    user_id: UUID,
    period: TimePeriod = TimePeriod.MONTHLY,
    current_user: User = Depends(get_current_active_user),
    cost_tracker = Depends(get_cost_tracker),
):
    """
    Get user costs for a time period.

    Returns aggregated cost information for the specified user
    and time period including total costs, session counts, and token usage.

    Args:
        user_id: User UUID to get costs for
        period: Time period (hourly, daily, weekly, monthly)
        current_user: Authenticated user (must match user_id or be admin)
        cost_tracker: Cost tracking service

    Returns:
        Cost summary for the period
    """
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these costs"
        )

    cost_summary = await cost_tracker.get_user_costs(user_id, period)

    return {
        "user_id": str(cost_summary.user_id),
        "period": cost_summary.period.value,
        "total_cost_usd": float(cost_summary.total_cost_usd),
        "total_sessions": cost_summary.total_sessions,
        "total_messages": cost_summary.total_messages,
        "total_tool_calls": cost_summary.total_tool_calls,
        "total_tokens": cost_summary.total_tokens,
        "average_cost_per_session": float(cost_summary.average_cost_per_session),
        "start_date": cost_summary.start_date.isoformat(),
        "end_date": cost_summary.end_date.isoformat(),
    }


@router.get("/costs/budget/{user_id}")
async def get_budget_status(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    cost_tracker = Depends(get_cost_tracker),
):
    """
    Get user budget status.

    Returns current budget status including monthly spend,
    remaining budget, and usage percentage.

    Args:
        user_id: User UUID to check budget for
        current_user: Authenticated user (must match user_id or be admin)
        cost_tracker: Cost tracking service

    Returns:
        Budget status information
    """
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this budget"
        )

    budget_status = await cost_tracker.check_budget(user_id)

    return {
        "user_id": str(budget_status.user_id),
        "monthly_budget_usd": float(budget_status.monthly_budget_usd),
        "current_month_cost_usd": float(budget_status.current_month_cost_usd),
        "remaining_budget_usd": float(budget_status.remaining_budget_usd),
        "percent_used": budget_status.percent_used,
        "is_over_budget": budget_status.is_over_budget,
        "days_remaining": budget_status.days_remaining,
    }


@router.get("/metrics/session/{session_id}")
async def get_session_metrics(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    metrics_collector = Depends(get_metrics_collector),
):
    """
    Get current metrics for a session.

    Returns real-time metrics including costs, token usage,
    and performance statistics.

    Args:
        session_id: Session UUID to get metrics for
        current_user: Authenticated user
        db: Database session
        metrics_collector: Metrics collection service

    Returns:
        Session metrics
    """
    from app.repositories.session_repository import SessionRepository

    # Check session ownership
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    metrics = await metrics_collector.get_session_metrics(session_id)

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics not found for session",
        )

    return metrics
