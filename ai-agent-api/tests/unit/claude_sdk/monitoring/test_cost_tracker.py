"""Unit tests for CostTracker."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta

from app.claude_sdk.monitoring.cost_tracker import (
    CostTracker,
    CostSummary,
    BudgetStatus,
    TimePeriod
)
from app.claude_sdk.monitoring.metrics_collector import TokenUsage


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def cost_tracker(mock_db_session):
    """Create CostTracker instance."""
    return CostTracker(mock_db_session)


class TestCostTrackerInitialization:
    """Tests for CostTracker initialization."""

    def test_initialization(self, mock_db_session):
        """Test CostTracker initializes correctly."""
        tracker = CostTracker(mock_db_session)

        assert tracker.db == mock_db_session


class TestTimePeriod:
    """Tests for TimePeriod enum."""

    def test_time_period_values(self):
        """Test TimePeriod enum values."""
        assert TimePeriod.HOURLY.value == "hourly"
        assert TimePeriod.DAILY.value == "daily"
        assert TimePeriod.WEEKLY.value == "weekly"
        assert TimePeriod.MONTHLY.value == "monthly"


class TestTrackCost:
    """Tests for tracking costs."""

    @pytest.mark.asyncio
    async def test_track_cost(self, cost_tracker):
        """Test tracking cost for session."""
        session_id = uuid4()
        user_id = uuid4()
        cost_usd = Decimal("0.50")
        tokens = TokenUsage(input_tokens=1000, output_tokens=500)

        # Should not raise exception
        await cost_tracker.track_cost(
            session_id=session_id,
            user_id=user_id,
            cost_usd=cost_usd,
            tokens=tokens
        )

    @pytest.mark.asyncio
    async def test_track_cost_with_cache_tokens(self, cost_tracker):
        """Test tracking cost with cache tokens."""
        session_id = uuid4()
        user_id = uuid4()
        cost_usd = Decimal("0.30")
        tokens = TokenUsage(
            input_tokens=800,
            output_tokens=400,
            cache_creation_tokens=100,
            cache_read_tokens=50
        )

        await cost_tracker.track_cost(
            session_id=session_id,
            user_id=user_id,
            cost_usd=cost_usd,
            tokens=tokens
        )

    @pytest.mark.asyncio
    async def test_track_multiple_costs(self, cost_tracker):
        """Test tracking multiple costs."""
        user_id = uuid4()

        costs = [
            (uuid4(), Decimal("0.10"), TokenUsage(500, 250)),
            (uuid4(), Decimal("0.20"), TokenUsage(1000, 500)),
            (uuid4(), Decimal("0.15"), TokenUsage(750, 375)),
        ]

        for session_id, cost, tokens in costs:
            await cost_tracker.track_cost(
                session_id=session_id,
                user_id=user_id,
                cost_usd=cost,
                tokens=tokens
            )


class TestCheckBudget:
    """Tests for checking budget."""

    @pytest.mark.asyncio
    async def test_check_budget_under_limit(self, cost_tracker):
        """Test checking budget when under limit."""
        user_id = uuid4()

        # Mock user repository
        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user = MagicMock()
            mock_user.id = user_id
            mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)

            # Mock settings
            with patch('app.claude_sdk.monitoring.cost_tracker.settings') as mock_settings:
                mock_settings.user_monthly_budget_usd = 100.0

                # Mock database query (current month cost)
                mock_result = MagicMock()
                mock_result.scalar = MagicMock(return_value=Decimal("25.00"))
                cost_tracker.db.execute = AsyncMock(return_value=mock_result)

                budget_status = await cost_tracker.check_budget(user_id)

                assert budget_status.user_id == user_id
                assert budget_status.monthly_budget_usd == Decimal("100.0")
                assert budget_status.current_month_cost_usd == Decimal("25.00")
                assert budget_status.remaining_budget_usd == Decimal("75.00")
                assert budget_status.percent_used == 25.0
                assert budget_status.is_over_budget is False

    @pytest.mark.asyncio
    async def test_check_budget_over_limit(self, cost_tracker):
        """Test checking budget when over limit."""
        user_id = uuid4()

        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user = MagicMock()
            mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)

            with patch('app.claude_sdk.monitoring.cost_tracker.settings') as mock_settings:
                mock_settings.user_monthly_budget_usd = 100.0

                # Current cost exceeds budget
                mock_result = MagicMock()
                mock_result.scalar = MagicMock(return_value=Decimal("125.00"))
                cost_tracker.db.execute = AsyncMock(return_value=mock_result)

                budget_status = await cost_tracker.check_budget(user_id)

                assert budget_status.current_month_cost_usd == Decimal("125.00")
                assert budget_status.remaining_budget_usd == Decimal("-25.00")
                assert budget_status.percent_used == 125.0
                assert budget_status.is_over_budget is True

    @pytest.mark.asyncio
    async def test_check_budget_at_limit(self, cost_tracker):
        """Test checking budget when at exact limit."""
        user_id = uuid4()

        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user = MagicMock()
            mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)

            with patch('app.claude_sdk.monitoring.cost_tracker.settings') as mock_settings:
                mock_settings.user_monthly_budget_usd = 100.0

                mock_result = MagicMock()
                mock_result.scalar = MagicMock(return_value=Decimal("100.00"))
                cost_tracker.db.execute = AsyncMock(return_value=mock_result)

                budget_status = await cost_tracker.check_budget(user_id)

                assert budget_status.current_month_cost_usd == Decimal("100.00")
                assert budget_status.remaining_budget_usd == Decimal("0.00")
                assert budget_status.percent_used == 100.0
                assert budget_status.is_over_budget is True

    @pytest.mark.asyncio
    async def test_check_budget_user_not_found(self, cost_tracker):
        """Test checking budget for nonexistent user."""
        user_id = uuid4()

        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="User .* not found"):
                await cost_tracker.check_budget(user_id)

    @pytest.mark.asyncio
    async def test_check_budget_no_costs(self, cost_tracker):
        """Test checking budget with no costs."""
        user_id = uuid4()

        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as MockUserRepo:
            mock_user_repo = MockUserRepo.return_value
            mock_user = MagicMock()
            mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)

            with patch('app.claude_sdk.monitoring.cost_tracker.settings') as mock_settings:
                mock_settings.user_monthly_budget_usd = 100.0

                # No costs
                mock_result = MagicMock()
                mock_result.scalar = MagicMock(return_value=None)
                cost_tracker.db.execute = AsyncMock(return_value=mock_result)

                budget_status = await cost_tracker.check_budget(user_id)

                assert budget_status.current_month_cost_usd == Decimal("0.0")
                assert budget_status.remaining_budget_usd == Decimal("100.0")
                assert budget_status.percent_used == 0.0
                assert budget_status.is_over_budget is False


class TestGetUserCosts:
    """Tests for getting user costs."""

    @pytest.mark.asyncio
    async def test_get_user_costs_daily(self, cost_tracker):
        """Test getting daily user costs."""
        user_id = uuid4()

        # Mock query result
        mock_row = MagicMock()
        mock_row.total_cost = Decimal("5.00")
        mock_row.total_sessions = 10
        mock_row.total_messages = 100
        mock_row.total_tool_calls = 50
        mock_row.total_tokens = 10000

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row)
        cost_tracker.db.execute = AsyncMock(return_value=mock_result)

        summary = await cost_tracker.get_user_costs(user_id, TimePeriod.DAILY)

        assert summary.user_id == user_id
        assert summary.period == TimePeriod.DAILY
        assert summary.total_cost_usd == Decimal("5.00")
        assert summary.total_sessions == 10
        assert summary.total_messages == 100
        assert summary.total_tool_calls == 50
        assert summary.total_tokens == 10000
        assert summary.average_cost_per_session == Decimal("0.50")

    @pytest.mark.asyncio
    async def test_get_user_costs_monthly(self, cost_tracker):
        """Test getting monthly user costs."""
        user_id = uuid4()

        mock_row = MagicMock()
        mock_row.total_cost = Decimal("75.00")
        mock_row.total_sessions = 150
        mock_row.total_messages = 1500
        mock_row.total_tool_calls = 750
        mock_row.total_tokens = 150000

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row)
        cost_tracker.db.execute = AsyncMock(return_value=mock_result)

        summary = await cost_tracker.get_user_costs(user_id, TimePeriod.MONTHLY)

        assert summary.period == TimePeriod.MONTHLY
        assert summary.total_cost_usd == Decimal("75.00")
        assert summary.total_sessions == 150

    @pytest.mark.asyncio
    async def test_get_user_costs_no_activity(self, cost_tracker):
        """Test getting costs with no activity."""
        user_id = uuid4()

        mock_row = MagicMock()
        mock_row.total_cost = None
        mock_row.total_sessions = None
        mock_row.total_messages = None
        mock_row.total_tool_calls = None
        mock_row.total_tokens = None

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row)
        cost_tracker.db.execute = AsyncMock(return_value=mock_result)

        summary = await cost_tracker.get_user_costs(user_id, TimePeriod.DAILY)

        assert summary.total_cost_usd == Decimal("0.0")
        assert summary.total_sessions == 0
        assert summary.total_messages == 0
        assert summary.total_tool_calls == 0
        assert summary.total_tokens == 0
        assert summary.average_cost_per_session == Decimal("0.0")

    @pytest.mark.asyncio
    async def test_get_user_costs_all_periods(self, cost_tracker):
        """Test getting costs for all time periods."""
        user_id = uuid4()

        mock_row = MagicMock()
        mock_row.total_cost = Decimal("10.00")
        mock_row.total_sessions = 20
        mock_row.total_messages = 200
        mock_row.total_tool_calls = 100
        mock_row.total_tokens = 20000

        mock_result = MagicMock()
        mock_result.first = MagicMock(return_value=mock_row)
        cost_tracker.db.execute = AsyncMock(return_value=mock_result)

        for period in TimePeriod:
            summary = await cost_tracker.get_user_costs(user_id, period)
            assert summary.period == period


class TestAlertIfOverBudget:
    """Tests for budget alerts."""

    @pytest.mark.asyncio
    async def test_alert_at_threshold(self, cost_tracker):
        """Test alert triggers at threshold."""
        user_id = uuid4()

        with patch.object(cost_tracker, 'check_budget') as mock_check:
            budget_status = BudgetStatus(
                user_id=user_id,
                monthly_budget_usd=Decimal("100.0"),
                current_month_cost_usd=Decimal("80.0"),
                remaining_budget_usd=Decimal("20.0"),
                percent_used=80.0,
                is_over_budget=False,
                days_remaining=15
            )
            mock_check.return_value = budget_status

            # Should not raise exception
            await cost_tracker.alert_if_over_budget(user_id, threshold_percent=80.0)

    @pytest.mark.asyncio
    async def test_alert_over_threshold(self, cost_tracker):
        """Test alert triggers when over threshold."""
        user_id = uuid4()

        with patch.object(cost_tracker, 'check_budget') as mock_check:
            budget_status = BudgetStatus(
                user_id=user_id,
                monthly_budget_usd=Decimal("100.0"),
                current_month_cost_usd=Decimal("95.0"),
                remaining_budget_usd=Decimal("5.0"),
                percent_used=95.0,
                is_over_budget=False,
                days_remaining=15
            )
            mock_check.return_value = budget_status

            await cost_tracker.alert_if_over_budget(user_id, threshold_percent=80.0)

    @pytest.mark.asyncio
    async def test_no_alert_under_threshold(self, cost_tracker):
        """Test no alert when under threshold."""
        user_id = uuid4()

        with patch.object(cost_tracker, 'check_budget') as mock_check:
            budget_status = BudgetStatus(
                user_id=user_id,
                monthly_budget_usd=Decimal("100.0"),
                current_month_cost_usd=Decimal("50.0"),
                remaining_budget_usd=Decimal("50.0"),
                percent_used=50.0,
                is_over_budget=False,
                days_remaining=15
            )
            mock_check.return_value = budget_status

            # Should complete without alert
            await cost_tracker.alert_if_over_budget(user_id, threshold_percent=80.0)


class TestDataClasses:
    """Tests for dataclasses."""

    def test_cost_summary_creation(self):
        """Test creating CostSummary."""
        user_id = uuid4()
        now = datetime.utcnow()

        summary = CostSummary(
            user_id=user_id,
            period=TimePeriod.DAILY,
            total_cost_usd=Decimal("10.00"),
            total_sessions=20,
            total_messages=200,
            total_tool_calls=100,
            total_tokens=20000,
            average_cost_per_session=Decimal("0.50"),
            start_date=now - timedelta(days=1),
            end_date=now
        )

        assert summary.user_id == user_id
        assert summary.period == TimePeriod.DAILY
        assert summary.total_cost_usd == Decimal("10.00")
        assert summary.average_cost_per_session == Decimal("0.50")

    def test_budget_status_creation(self):
        """Test creating BudgetStatus."""
        user_id = uuid4()

        status = BudgetStatus(
            user_id=user_id,
            monthly_budget_usd=Decimal("100.0"),
            current_month_cost_usd=Decimal("75.0"),
            remaining_budget_usd=Decimal("25.0"),
            percent_used=75.0,
            is_over_budget=False,
            days_remaining=10
        )

        assert status.user_id == user_id
        assert status.monthly_budget_usd == Decimal("100.0")
        assert status.current_month_cost_usd == Decimal("75.0")
        assert status.percent_used == 75.0
        assert status.is_over_budget is False
