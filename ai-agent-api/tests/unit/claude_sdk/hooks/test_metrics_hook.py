"""Unit tests for MetricsHook."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.claude_sdk.hooks.implementations.metrics_hook import MetricsHook
from app.claude_sdk.hooks.base_hook import HookType


@pytest.fixture
def mock_metrics_collector():
    """Create mock metrics collector."""
    collector = AsyncMock()
    collector.record_tool_execution = AsyncMock()
    return collector


@pytest.fixture
def metrics_hook(mock_metrics_collector):
    """Create MetricsHook instance."""
    return MetricsHook(mock_metrics_collector)


class TestMetricsHookInitialization:
    """Tests for MetricsHook initialization."""

    def test_initialization(self, mock_metrics_collector):
        """Test MetricsHook initializes correctly."""
        hook = MetricsHook(mock_metrics_collector)

        assert hook.metrics_collector == mock_metrics_collector

    def test_hook_type(self, metrics_hook):
        """Test hook returns correct type."""
        assert metrics_hook.hook_type == HookType.POST_TOOL_USE

    def test_priority(self, metrics_hook):
        """Test hook has normal priority."""
        assert metrics_hook.priority == 100


class TestMetricsHookExecution:
    """Tests for MetricsHook execution."""

    @pytest.mark.asyncio
    async def test_execute_records_tool_execution(self, metrics_hook, mock_metrics_collector):
        """Test hook records tool execution metrics."""
        input_data = {
            "name": "read_file",
            "duration_ms": 150,
            "success": True
        }
        tool_use_id = "tool_123"

        context = MagicMock()
        context.session_id = uuid4()

        result = await metrics_hook.execute(input_data, tool_use_id, context)

        # Should record metrics
        mock_metrics_collector.record_tool_execution.assert_called_once()

        # Should allow execution
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_extracts_tool_name(self, metrics_hook, mock_metrics_collector):
        """Test hook extracts tool name correctly."""
        input_data = {
            "name": "write_file",
            "duration_ms": 200
        }

        context = MagicMock()
        context.session_id = uuid4()

        await metrics_hook.execute(input_data, None, context)

        call_args = mock_metrics_collector.record_tool_execution.call_args

        # Check tool name was passed
        assert "write_file" in str(call_args)

    @pytest.mark.asyncio
    async def test_execute_with_tool_name_field(self, metrics_hook, mock_metrics_collector):
        """Test hook handles tool_name field."""
        input_data = {
            "tool_name": "bash",
            "duration_ms": 1000
        }

        context = MagicMock()
        context.session_id = uuid4()

        await metrics_hook.execute(input_data, None, context)

        mock_metrics_collector.record_tool_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_without_duration(self, metrics_hook, mock_metrics_collector):
        """Test hook handles missing duration."""
        input_data = {
            "name": "test_tool"
        }

        context = MagicMock()
        context.session_id = uuid4()

        result = await metrics_hook.execute(input_data, None, context)

        # Should still record (with duration 0)
        mock_metrics_collector.record_tool_execution.assert_called_once()
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_without_context(self, metrics_hook, mock_metrics_collector):
        """Test hook handles None context."""
        input_data = {
            "name": "test_tool",
            "duration_ms": 100
        }

        result = await metrics_hook.execute(input_data, "tool_456", None)

        # Should not crash
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_with_success_status(self, metrics_hook, mock_metrics_collector):
        """Test hook tracks success status."""
        input_data = {
            "name": "test_tool",
            "duration_ms": 100,
            "success": True
        }

        context = MagicMock()
        context.session_id = uuid4()

        await metrics_hook.execute(input_data, None, context)

        mock_metrics_collector.record_tool_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_error_status(self, metrics_hook, mock_metrics_collector):
        """Test hook tracks error status."""
        input_data = {
            "name": "test_tool",
            "duration_ms": 100,
            "is_error": True
        }

        context = MagicMock()
        context.session_id = uuid4()

        await metrics_hook.execute(input_data, None, context)

        mock_metrics_collector.record_tool_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handles_collector_failure(self, metrics_hook, mock_metrics_collector):
        """Test hook handles metrics collector failures gracefully."""
        # Make collector fail
        mock_metrics_collector.record_tool_execution.side_effect = Exception("Metrics service down")

        input_data = {"name": "test_tool", "duration_ms": 100}

        context = MagicMock()
        context.session_id = uuid4()

        # Should not raise exception
        result = await metrics_hook.execute(input_data, None, context)

        # Should still allow execution
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_always_allows_continuation(self, metrics_hook, mock_metrics_collector):
        """Test hook always allows execution to continue."""
        scenarios = [
            {"name": "tool1", "duration_ms": 10},
            {"name": "tool2", "duration_ms": 1000},
            {"name": "tool3", "is_error": True},
        ]

        context = MagicMock()
        context.session_id = uuid4()

        for input_data in scenarios:
            result = await metrics_hook.execute(input_data, None, context)
            assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_logs_each_invocation(self, metrics_hook, mock_metrics_collector):
        """Test each execution is recorded separately."""
        context = MagicMock()
        context.session_id = uuid4()

        input_data1 = {"name": "tool1", "duration_ms": 100}
        input_data2 = {"name": "tool2", "duration_ms": 200}
        input_data3 = {"name": "tool3", "duration_ms": 300}

        await metrics_hook.execute(input_data1, None, context)
        await metrics_hook.execute(input_data2, None, context)
        await metrics_hook.execute(input_data3, None, context)

        # Should record 3 times
        assert mock_metrics_collector.record_tool_execution.call_count == 3
