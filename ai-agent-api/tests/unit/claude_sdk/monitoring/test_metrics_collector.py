"""Unit tests for MetricsCollector."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal

from app.claude_sdk.monitoring.metrics_collector import (
    MetricsCollector,
    TokenUsage,
    SessionMetrics
)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def metrics_collector(mock_db_session):
    """Create MetricsCollector instance."""
    return MetricsCollector(mock_db_session)


class TestMetricsCollectorInitialization:
    """Tests for MetricsCollector initialization."""

    def test_initialization(self, mock_db_session):
        """Test MetricsCollector initializes correctly."""
        collector = MetricsCollector(mock_db_session)

        assert collector.db == mock_db_session
        assert collector._session_metrics == {}


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_creation(self):
        """Test creating TokenUsage instance."""
        tokens = TokenUsage(
            input_tokens=100,
            output_tokens=200,
            cache_creation_tokens=50,
            cache_read_tokens=25
        )

        assert tokens.input_tokens == 100
        assert tokens.output_tokens == 200
        assert tokens.cache_creation_tokens == 50
        assert tokens.cache_read_tokens == 25

    def test_token_usage_defaults(self):
        """Test TokenUsage default values."""
        tokens = TokenUsage(input_tokens=100, output_tokens=200)

        assert tokens.cache_creation_tokens == 0
        assert tokens.cache_read_tokens == 0


class TestRecordQueryDuration:
    """Tests for recording query duration."""

    @pytest.mark.asyncio
    async def test_record_query_duration(self, metrics_collector):
        """Test recording query duration."""
        session_id = uuid4()
        duration_ms = 1500

        # Should not raise exception
        await metrics_collector.record_query_duration(session_id, duration_ms)

    @pytest.mark.asyncio
    async def test_record_multiple_query_durations(self, metrics_collector):
        """Test recording multiple query durations."""
        session_id = uuid4()

        await metrics_collector.record_query_duration(session_id, 100)
        await metrics_collector.record_query_duration(session_id, 200)
        await metrics_collector.record_query_duration(session_id, 300)

        # Should not raise exception


class TestRecordToolExecution:
    """Tests for recording tool execution."""

    @pytest.mark.asyncio
    async def test_record_successful_tool_execution(self, metrics_collector):
        """Test recording successful tool execution."""
        session_id = uuid4()

        await metrics_collector.record_tool_execution(
            session_id=session_id,
            tool_name="read_file",
            duration_ms=150,
            success=True
        )

    @pytest.mark.asyncio
    async def test_record_failed_tool_execution(self, metrics_collector):
        """Test recording failed tool execution."""
        session_id = uuid4()

        await metrics_collector.record_tool_execution(
            session_id=session_id,
            tool_name="write_file",
            duration_ms=100,
            success=False
        )

    @pytest.mark.asyncio
    async def test_record_multiple_tool_executions(self, metrics_collector):
        """Test recording multiple tool executions."""
        session_id = uuid4()

        tools = [
            ("read_file", 100, True),
            ("write_file", 200, True),
            ("bash", 500, False),
        ]

        for tool_name, duration, success in tools:
            await metrics_collector.record_tool_execution(
                session_id=session_id,
                tool_name=tool_name,
                duration_ms=duration,
                success=success
            )


class TestRecordAPICost:
    """Tests for recording API costs."""

    @pytest.mark.asyncio
    async def test_record_api_cost(self, metrics_collector):
        """Test recording API cost."""
        session_id = uuid4()
        cost_usd = Decimal("0.25")
        tokens = TokenUsage(input_tokens=1000, output_tokens=500)

        await metrics_collector.record_api_cost(
            session_id=session_id,
            cost_usd=cost_usd,
            tokens=tokens
        )

    @pytest.mark.asyncio
    async def test_record_api_cost_with_cache_tokens(self, metrics_collector):
        """Test recording API cost with cache tokens."""
        session_id = uuid4()
        cost_usd = Decimal("0.15")
        tokens = TokenUsage(
            input_tokens=500,
            output_tokens=300,
            cache_creation_tokens=100,
            cache_read_tokens=50
        )

        await metrics_collector.record_api_cost(
            session_id=session_id,
            cost_usd=cost_usd,
            tokens=tokens
        )

    @pytest.mark.asyncio
    async def test_record_multiple_api_costs(self, metrics_collector):
        """Test recording multiple API costs."""
        session_id = uuid4()

        costs = [
            (Decimal("0.10"), TokenUsage(500, 250)),
            (Decimal("0.20"), TokenUsage(1000, 500)),
            (Decimal("0.05"), TokenUsage(250, 125)),
        ]

        for cost, tokens in costs:
            await metrics_collector.record_api_cost(
                session_id=session_id,
                cost_usd=cost,
                tokens=tokens
            )


class TestCreateSnapshot:
    """Tests for creating metrics snapshots."""

    @pytest.mark.asyncio
    async def test_create_snapshot_success(self, metrics_collector, mock_db_session):
        """Test creating metrics snapshot successfully."""
        session_id = uuid4()

        # Mock session repository
        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.total_messages = 10
            mock_session.total_tool_calls = 5
            mock_session.total_errors = 1
            mock_session.total_retries = 2
            mock_session.total_cost_usd = Decimal("0.50")
            mock_session.api_input_tokens = 1000
            mock_session.api_output_tokens = 500
            mock_session.api_cache_creation_tokens = 100
            mock_session.api_cache_read_tokens = 50
            mock_session.duration_ms = 5000

            mock_repo.get_by_id = AsyncMock(return_value=mock_session)

            # Mock metrics snapshot repository
            with patch('app.claude_sdk.monitoring.metrics_collector.SessionMetricsSnapshotRepository') as MockSnapshotRepo:
                mock_snapshot_repo = MockSnapshotRepo.return_value
                mock_snapshot = MagicMock()
                mock_snapshot.id = uuid4()
                mock_snapshot_repo.create = AsyncMock(return_value=mock_snapshot)

                await metrics_collector.create_snapshot(session_id)

                # Should create snapshot
                mock_snapshot_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_snapshot_session_not_found(self, metrics_collector):
        """Test creating snapshot when session not found."""
        session_id = uuid4()

        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            # Should not raise exception
            await metrics_collector.create_snapshot(session_id)

    @pytest.mark.asyncio
    async def test_create_snapshot_handles_errors(self, metrics_collector):
        """Test snapshot creation handles errors gracefully."""
        session_id = uuid4()

        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(side_effect=Exception("Database error"))

            # Should not raise exception
            await metrics_collector.create_snapshot(session_id)


class TestGetSessionMetrics:
    """Tests for getting session metrics."""

    @pytest.mark.asyncio
    async def test_get_session_metrics_success(self, metrics_collector):
        """Test getting session metrics successfully."""
        session_id = uuid4()

        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.total_messages = 15
            mock_session.total_tool_calls = 8
            mock_session.total_errors = 2
            mock_session.total_retries = 1
            mock_session.total_cost_usd = Decimal("0.75")
            mock_session.api_input_tokens = 2000
            mock_session.api_output_tokens = 1000
            mock_session.api_cache_creation_tokens = 200
            mock_session.api_cache_read_tokens = 100
            mock_session.duration_ms = 10000

            mock_repo.get_by_id = AsyncMock(return_value=mock_session)

            metrics = await metrics_collector.get_session_metrics(session_id)

            assert metrics is not None
            assert metrics["session_id"] == str(session_id)
            assert metrics["total_messages"] == 15
            assert metrics["total_tool_calls"] == 8
            assert metrics["total_errors"] == 2
            assert metrics["total_retries"] == 1
            assert metrics["total_cost_usd"] == 0.75
            assert metrics["total_input_tokens"] == 2000
            assert metrics["total_output_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_get_session_metrics_not_found(self, metrics_collector):
        """Test getting metrics for nonexistent session."""
        session_id = uuid4()

        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            metrics = await metrics_collector.get_session_metrics(session_id)

            assert metrics is None

    @pytest.mark.asyncio
    async def test_get_session_metrics_handles_none_values(self, metrics_collector):
        """Test getting metrics handles None values."""
        session_id = uuid4()

        with patch('app.claude_sdk.monitoring.metrics_collector.SessionRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.total_messages = 5
            mock_session.total_tool_calls = 3
            mock_session.total_errors = None
            mock_session.total_retries = None
            mock_session.total_cost_usd = None
            mock_session.api_input_tokens = None
            mock_session.api_output_tokens = None
            mock_session.api_cache_creation_tokens = None
            mock_session.api_cache_read_tokens = None
            mock_session.duration_ms = None

            mock_repo.get_by_id = AsyncMock(return_value=mock_session)

            metrics = await metrics_collector.get_session_metrics(session_id)

            # Should handle None values
            assert metrics["total_errors"] == 0
            assert metrics["total_retries"] == 0
            assert metrics["total_cost_usd"] == 0.0
            assert metrics["total_input_tokens"] == 0
            assert metrics["total_output_tokens"] == 0


class TestSessionMetrics:
    """Tests for SessionMetrics dataclass."""

    def test_session_metrics_creation(self):
        """Test creating SessionMetrics instance."""
        from datetime import datetime

        session_id = uuid4()
        now = datetime.utcnow()

        metrics = SessionMetrics(
            session_id=session_id,
            total_messages=10,
            total_tool_calls=5,
            total_errors=1,
            total_retries=2,
            total_cost_usd=Decimal("0.50"),
            total_input_tokens=1000,
            total_output_tokens=500,
            total_cache_creation_tokens=100,
            total_cache_read_tokens=50,
            total_duration_ms=5000,
            average_latency_ms=500,
            created_at=now
        )

        assert metrics.session_id == session_id
        assert metrics.total_messages == 10
        assert metrics.total_tool_calls == 5
        assert metrics.total_errors == 1
        assert metrics.total_cost_usd == Decimal("0.50")
        assert metrics.average_latency_ms == 500

    def test_session_metrics_optional_average_latency(self):
        """Test SessionMetrics with None average latency."""
        from datetime import datetime

        metrics = SessionMetrics(
            session_id=uuid4(),
            total_messages=5,
            total_tool_calls=2,
            total_errors=0,
            total_retries=0,
            total_cost_usd=Decimal("0.25"),
            total_input_tokens=500,
            total_output_tokens=250,
            total_cache_creation_tokens=0,
            total_cache_read_tokens=0,
            total_duration_ms=2000,
            average_latency_ms=None,
            created_at=datetime.utcnow()
        )

        assert metrics.average_latency_ms is None
