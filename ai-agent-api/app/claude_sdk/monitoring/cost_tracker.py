"""Cost tracker for API usage and budget management."""

from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logging import get_logger
from app.claude_sdk.monitoring.metrics_collector import TokenUsage


logger = get_logger(__name__)


class TimePeriod(str, Enum):
    """Time period for cost aggregation."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class CostSummary:
    """Cost summary for a time period."""
    user_id: UUID
    period: TimePeriod
    total_cost_usd: Decimal
    total_sessions: int
    total_messages: int
    total_tool_calls: int
    total_tokens: int
    average_cost_per_session: Decimal
    start_date: datetime
    end_date: datetime


@dataclass
class BudgetStatus:
    """User budget status."""
    user_id: UUID
    monthly_budget_usd: Decimal
    current_month_cost_usd: Decimal
    remaining_budget_usd: Decimal
    percent_used: float
    is_over_budget: bool
    days_remaining: int


class CostTracker:
    """Track API costs and enforce budgets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_cost(
        self,
        session_id: UUID,
        user_id: UUID,
        cost_usd: Decimal,
        tokens: TokenUsage
    ) -> None:
        """Track cost for session and user."""
        logger.info(
            f"Tracking cost for user {user_id}: ${cost_usd}",
            extra={
                "user_id": str(user_id),
                "session_id": str(session_id),
                "cost_usd": float(cost_usd),
                "tokens": {
                    "input": tokens.input_tokens,
                    "output": tokens.output_tokens,
                    "cache_creation": tokens.cache_creation_tokens,
                    "cache_read": tokens.cache_read_tokens
                }
            }
        )

    async def check_budget(
        self,
        user_id: UUID
    ) -> BudgetStatus:
        """Check if user has exceeded budget."""
        from app.repositories.user_repository import UserRepository
        from app.repositories.session_repository import SessionRepository
        from app.models.session import SessionModel

        user_repo = UserRepository(self.db)
        user = await user_repo.get_by_id(str(user_id))

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get monthly budget from settings
        from app.core.config import settings
        monthly_budget = Decimal(str(settings.user_monthly_budget_usd))

        # Calculate current month costs
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Query total costs for current month
        stmt = select(func.sum(SessionModel.total_cost_usd)).where(
            SessionModel.user_id == user_id,
            SessionModel.created_at >= month_start,
            SessionModel.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        current_month_cost = result.scalar() or Decimal("0.0")

        remaining_budget = monthly_budget - current_month_cost
        percent_used = (current_month_cost / monthly_budget * 100) if monthly_budget > 0 else 0
        is_over_budget = current_month_cost >= monthly_budget

        # Calculate days remaining in month
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        days_remaining = (next_month - now).days

        return BudgetStatus(
            user_id=user_id,
            monthly_budget_usd=monthly_budget,
            current_month_cost_usd=current_month_cost,
            remaining_budget_usd=remaining_budget,
            percent_used=float(percent_used),
            is_over_budget=is_over_budget,
            days_remaining=days_remaining
        )

    async def get_user_costs(
        self,
        user_id: UUID,
        period: TimePeriod
    ) -> CostSummary:
        """Get user costs for time period."""
        from app.models.session import SessionModel

        # Determine date range based on period
        now = datetime.utcnow()
        if period == TimePeriod.HOURLY:
            start_date = now - timedelta(hours=1)
        elif period == TimePeriod.DAILY:
            start_date = now - timedelta(days=1)
        elif period == TimePeriod.WEEKLY:
            start_date = now - timedelta(weeks=1)
        elif period == TimePeriod.MONTHLY:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=30)

        # Query session aggregates
        stmt = select(
            func.sum(SessionModel.total_cost_usd).label("total_cost"),
            func.count(SessionModel.id).label("total_sessions"),
            func.sum(SessionModel.total_messages).label("total_messages"),
            func.sum(SessionModel.total_tool_calls).label("total_tool_calls"),
            func.sum(
                SessionModel.api_input_tokens +
                SessionModel.api_output_tokens
            ).label("total_tokens")
        ).where(
            SessionModel.user_id == user_id,
            SessionModel.created_at >= start_date,
            SessionModel.deleted_at.is_(None)
        )

        result = await self.db.execute(stmt)
        row = result.first()

        total_cost = row.total_cost or Decimal("0.0")
        total_sessions = row.total_sessions or 0
        total_messages = row.total_messages or 0
        total_tool_calls = row.total_tool_calls or 0
        total_tokens = row.total_tokens or 0

        average_cost = (total_cost / total_sessions) if total_sessions > 0 else Decimal("0.0")

        return CostSummary(
            user_id=user_id,
            period=period,
            total_cost_usd=total_cost,
            total_sessions=total_sessions,
            total_messages=total_messages,
            total_tool_calls=total_tool_calls,
            total_tokens=total_tokens,
            average_cost_per_session=average_cost,
            start_date=start_date,
            end_date=now
        )

    async def alert_if_over_budget(
        self,
        user_id: UUID,
        threshold_percent: float = 80.0
    ) -> None:
        """Send alert if user is approaching budget limit."""
        budget_status = await self.check_budget(user_id)

        if budget_status.percent_used >= threshold_percent:
            logger.warning(
                f"User {user_id} has used {budget_status.percent_used:.1f}% of monthly budget",
                extra={
                    "user_id": str(user_id),
                    "percent_used": budget_status.percent_used,
                    "current_cost": float(budget_status.current_month_cost_usd),
                    "monthly_budget": float(budget_status.monthly_budget_usd),
                    "is_over_budget": budget_status.is_over_budget
                }
            )

            # TODO: Implement notification service integration
            # await notification_service.send_budget_alert(user_id, budget_status)
