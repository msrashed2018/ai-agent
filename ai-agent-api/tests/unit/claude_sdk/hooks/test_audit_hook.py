"""Unit tests for AuditHook."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.claude_sdk.hooks.implementations.audit_hook import AuditHook
from app.claude_sdk.hooks.base_hook import HookType
from app.services.audit_service import AuditService


@pytest.fixture
def mock_audit_service():
    """Create mock audit service."""
    service = AsyncMock(spec=AuditService)
    service.log_event = AsyncMock()
    return service


@pytest.fixture
def audit_hook(mock_audit_service):
    """Create AuditHook instance."""
    return AuditHook(mock_audit_service)


class TestAuditHookInitialization:
    """Tests for AuditHook initialization."""

    def test_initialization(self, mock_audit_service):
        """Test AuditHook initializes correctly."""
        hook = AuditHook(mock_audit_service)

        assert hook.audit_service == mock_audit_service

    def test_hook_type(self, audit_hook):
        """Test hook returns correct type."""
        assert audit_hook.hook_type == HookType.PRE_TOOL_USE

    def test_priority(self, audit_hook):
        """Test hook has high priority."""
        # Audit should run early
        assert audit_hook.priority == 10


class TestAuditHookExecution:
    """Tests for AuditHook execution."""

    @pytest.mark.asyncio
    async def test_execute_logs_tool_execution(self, audit_hook, mock_audit_service):
        """Test hook logs tool execution to audit service."""
        input_data = {
            "name": "read_file",
            "input": {"path": "/tmp/test.txt"}
        }
        tool_use_id = "tool_123"

        # Create mock context with session_id
        context = MagicMock()
        context.session_id = uuid4()

        result = await audit_hook.execute(input_data, tool_use_id, context)

        # Should log to audit service
        mock_audit_service.log_event.assert_called_once()
        call_args = mock_audit_service.log_event.call_args

        assert call_args[1]["event_type"] == "tool_execution_attempt"
        assert call_args[1]["event_category"] == "tool"
        assert call_args[1]["resource_id"] == "read_file"
        assert call_args[1]["session_id"] == context.session_id

        # Should allow execution
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_with_tool_name_field(self, audit_hook, mock_audit_service):
        """Test hook handles tool_name field."""
        input_data = {
            "tool_name": "write_file",
            "input": {"content": "test"}
        }

        result = await audit_hook.execute(input_data, None, None)

        # Should extract tool_name
        call_args = mock_audit_service.log_event.call_args
        assert call_args[1]["resource_id"] == "write_file"

        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_with_unknown_tool(self, audit_hook, mock_audit_service):
        """Test hook handles missing tool name."""
        input_data = {"input": {"some": "data"}}

        result = await audit_hook.execute(input_data, None, None)

        # Should use "unknown" as fallback
        call_args = mock_audit_service.log_event.call_args
        assert call_args[1]["resource_id"] == "unknown"

        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_without_context(self, audit_hook, mock_audit_service):
        """Test hook handles None context."""
        input_data = {"name": "bash", "input": {"command": "ls"}}

        result = await audit_hook.execute(input_data, "tool_456", None)

        # Should not crash
        mock_audit_service.log_event.assert_called_once()
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_includes_tool_input(self, audit_hook, mock_audit_service):
        """Test hook logs tool input parameters."""
        input_data = {
            "name": "execute_query",
            "input": {
                "query": "SELECT * FROM users",
                "params": [1, 2, 3]
            }
        }

        await audit_hook.execute(input_data, "tool_789", None)

        call_args = mock_audit_service.log_event.call_args
        details = call_args[1]["details"]

        assert details["tool_input"]["query"] == "SELECT * FROM users"
        assert details["tool_input"]["params"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_execute_includes_tool_use_id(self, audit_hook, mock_audit_service):
        """Test hook logs tool use ID."""
        input_data = {"name": "test_tool"}
        tool_use_id = "unique_tool_id_123"

        await audit_hook.execute(input_data, tool_use_id, None)

        call_args = mock_audit_service.log_event.call_args
        details = call_args[1]["details"]

        assert details["tool_use_id"] == tool_use_id

    @pytest.mark.asyncio
    async def test_execute_includes_hook_identifier(self, audit_hook, mock_audit_service):
        """Test hook identifies itself in log."""
        input_data = {"name": "test_tool"}

        await audit_hook.execute(input_data, None, None)

        call_args = mock_audit_service.log_event.call_args
        details = call_args[1]["details"]

        assert details["hook"] == "AuditHook"

    @pytest.mark.asyncio
    async def test_execute_handles_audit_service_failure(self, audit_hook, mock_audit_service):
        """Test hook handles audit service failures gracefully."""
        # Make audit service fail
        mock_audit_service.log_event.side_effect = Exception("Audit service down")

        input_data = {"name": "test_tool"}

        # Should not raise exception
        result = await audit_hook.execute(input_data, None, None)

        # Should still allow execution
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_always_allows_continuation(self, audit_hook, mock_audit_service):
        """Test hook always allows execution to continue."""
        # Try various scenarios
        scenarios = [
            {"name": "dangerous_tool"},
            {"name": "read_file", "input": {"path": "/etc/passwd"}},
            {"name": "bash", "input": {"command": "rm -rf /"}},
        ]

        for input_data in scenarios:
            result = await audit_hook.execute(input_data, None, None)
            assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_logs_each_invocation(self, audit_hook, mock_audit_service):
        """Test each execution is logged separately."""
        input_data1 = {"name": "tool1"}
        input_data2 = {"name": "tool2"}
        input_data3 = {"name": "tool3"}

        await audit_hook.execute(input_data1, None, None)
        await audit_hook.execute(input_data2, None, None)
        await audit_hook.execute(input_data3, None, None)

        # Should log 3 times
        assert mock_audit_service.log_event.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_empty_input(self, audit_hook, mock_audit_service):
        """Test hook handles empty input data."""
        input_data = {"name": "test_tool", "input": {}}

        result = await audit_hook.execute(input_data, None, None)

        mock_audit_service.log_event.assert_called_once()
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execute_with_complex_input(self, audit_hook, mock_audit_service):
        """Test hook handles complex nested input."""
        input_data = {
            "name": "complex_tool",
            "input": {
                "nested": {
                    "level1": {
                        "level2": ["value1", "value2"],
                        "number": 42
                    }
                },
                "list": [1, 2, {"key": "value"}]
            }
        }

        result = await audit_hook.execute(input_data, "tool_complex", None)

        # Should handle complex data
        mock_audit_service.log_event.assert_called_once()
        call_args = mock_audit_service.log_event.call_args
        details = call_args[1]["details"]

        assert "tool_input" in details
        assert result["continue_"] is True
