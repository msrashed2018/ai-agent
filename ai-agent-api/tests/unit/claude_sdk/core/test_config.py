"""Unit tests for ClientConfig and ClientMetrics."""

import pytest
from uuid import uuid4
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

from app.claude_sdk.core.config import ClientConfig, ClientMetrics, ClientState


class TestClientConfig:
    """Test cases for ClientConfig."""

    def test_client_config_creation_defaults(self):
        """Test client config creation with default values."""
        session_id = uuid4()
        config = ClientConfig(session_id=session_id)

        assert config.session_id == session_id
        assert config.model == "claude-sonnet-4-5"
        assert config.permission_mode == "default"
        assert config.max_turns == 10
        assert config.max_retries == 3
        assert config.retry_delay == 2.0
        assert config.timeout_seconds == 120
        assert config.include_partial_messages is False
        assert isinstance(config.working_directory, Path)
        assert config.mcp_servers == {}
        assert config.allowed_tools is None
        assert config.hooks is None
        assert config.can_use_tool is None

    def test_client_config_creation_custom_values(self):
        """Test client config creation with custom values."""
        session_id = uuid4()
        working_dir = Path("/tmp/test")
        mcp_servers = {"server1": {"type": "stdio", "command": "test"}}
        allowed_tools = ["file_reader", "calculator"]
        
        def mock_permission_callback(tool_name: str) -> bool:
            return True

        config = ClientConfig(
            session_id=session_id,
            model="claude-haiku-4",
            permission_mode="strict",
            max_turns=20,
            max_retries=5,
            retry_delay=1.5,
            timeout_seconds=300,
            include_partial_messages=True,
            working_directory=working_dir,
            mcp_servers=mcp_servers,
            allowed_tools=allowed_tools,
            can_use_tool=mock_permission_callback,
        )

        assert config.session_id == session_id
        assert config.model == "claude-haiku-4"
        assert config.permission_mode == "strict"
        assert config.max_turns == 20
        assert config.max_retries == 5
        assert config.retry_delay == 1.5
        assert config.timeout_seconds == 300
        assert config.include_partial_messages is True
        assert config.working_directory == working_dir
        assert config.mcp_servers == mcp_servers
        assert config.allowed_tools == allowed_tools
        assert config.can_use_tool == mock_permission_callback

    def test_client_config_validation_negative_max_turns(self):
        """Test validation fails for negative max_turns."""
        with pytest.raises(ValueError, match="max_turns must be positive"):
            ClientConfig(session_id=uuid4(), max_turns=-1)

    def test_client_config_validation_zero_max_turns(self):
        """Test validation fails for zero max_turns."""
        with pytest.raises(ValueError, match="max_turns must be positive"):
            ClientConfig(session_id=uuid4(), max_turns=0)

    def test_client_config_validation_negative_max_retries(self):
        """Test validation fails for negative max_retries."""
        with pytest.raises(ValueError, match="max_retries cannot be negative"):
            ClientConfig(session_id=uuid4(), max_retries=-1)

    def test_client_config_validation_zero_retry_delay(self):
        """Test validation fails for zero retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            ClientConfig(session_id=uuid4(), retry_delay=0.0)

    def test_client_config_validation_negative_retry_delay(self):
        """Test validation fails for negative retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            ClientConfig(session_id=uuid4(), retry_delay=-1.0)

    def test_client_config_validation_zero_timeout_seconds(self):
        """Test validation fails for zero timeout_seconds."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ClientConfig(session_id=uuid4(), timeout_seconds=0)

    def test_client_config_validation_negative_timeout_seconds(self):
        """Test validation fails for negative timeout_seconds."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            ClientConfig(session_id=uuid4(), timeout_seconds=-1)

    def test_client_config_validation_empty_model(self):
        """Test validation fails for empty model."""
        with pytest.raises(ValueError, match="model cannot be empty"):
            ClientConfig(session_id=uuid4(), model="   ")

    def test_client_config_validation_empty_permission_mode(self):
        """Test validation fails for empty permission_mode."""
        with pytest.raises(ValueError, match="permission_mode cannot be empty"):
            ClientConfig(session_id=uuid4(), permission_mode="")

    def test_client_config_is_streaming_enabled(self):
        """Test is_streaming_enabled method."""
        config_streaming = ClientConfig(session_id=uuid4(), include_partial_messages=True)
        config_no_streaming = ClientConfig(session_id=uuid4(), include_partial_messages=False)

        assert config_streaming.is_streaming_enabled() is True
        assert config_no_streaming.is_streaming_enabled() is False

    def test_client_config_get_retry_backoff(self):
        """Test get_retry_backoff method with exponential backoff."""
        config = ClientConfig(session_id=uuid4(), retry_delay=2.0)

        assert config.get_retry_backoff(0) == 2.0  # 2.0 * 2^0
        assert config.get_retry_backoff(1) == 4.0  # 2.0 * 2^1
        assert config.get_retry_backoff(2) == 8.0  # 2.0 * 2^2
        assert config.get_retry_backoff(3) == 16.0  # 2.0 * 2^3

    def test_client_config_zero_max_retries_allowed(self):
        """Test that zero max_retries is allowed (no retries)."""
        config = ClientConfig(session_id=uuid4(), max_retries=0)
        assert config.max_retries == 0


class TestClientMetrics:
    """Test cases for ClientMetrics."""

    def test_client_metrics_creation_defaults(self):
        """Test client metrics initialization with default values."""
        session_id = uuid4()
        metrics = ClientMetrics(session_id=session_id)

        assert metrics.session_id == session_id
        assert metrics.total_messages == 0
        assert metrics.total_tool_calls == 0
        assert metrics.total_errors == 0
        assert metrics.total_retries == 0
        assert metrics.total_cost_usd == Decimal("0.0")
        assert metrics.total_input_tokens == 0
        assert metrics.total_output_tokens == 0
        assert metrics.total_cache_creation_tokens == 0
        assert metrics.total_cache_read_tokens == 0
        assert metrics.total_duration_ms == 0
        assert metrics.started_at is None
        assert metrics.completed_at is None

    def test_client_metrics_increment_messages(self):
        """Test incrementing message count."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.total_messages == 0
        
        metrics.increment_messages()
        assert metrics.total_messages == 1
        
        metrics.increment_messages()
        assert metrics.total_messages == 2

    def test_client_metrics_increment_tool_calls(self):
        """Test incrementing tool call count."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.total_tool_calls == 0
        
        metrics.increment_tool_calls()
        assert metrics.total_tool_calls == 1
        
        metrics.increment_tool_calls()
        assert metrics.total_tool_calls == 2

    def test_client_metrics_increment_errors(self):
        """Test incrementing error count."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.total_errors == 0
        
        metrics.increment_errors()
        assert metrics.total_errors == 1
        
        metrics.increment_errors()
        assert metrics.total_errors == 2

    def test_client_metrics_increment_retries(self):
        """Test incrementing retry count."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.total_retries == 0
        
        metrics.increment_retries()
        assert metrics.total_retries == 1
        
        metrics.increment_retries()
        assert metrics.total_retries == 2

    def test_client_metrics_add_tokens(self):
        """Test adding token counts."""
        metrics = ClientMetrics(session_id=uuid4())
        
        metrics.add_tokens(
            input_tokens=100,
            output_tokens=50,
            cache_creation_tokens=10,
            cache_read_tokens=5
        )
        
        assert metrics.total_input_tokens == 100
        assert metrics.total_output_tokens == 50
        assert metrics.total_cache_creation_tokens == 10
        assert metrics.total_cache_read_tokens == 5

    def test_client_metrics_add_tokens_accumulates(self):
        """Test that token additions accumulate."""
        metrics = ClientMetrics(session_id=uuid4())
        
        metrics.add_tokens(input_tokens=100, output_tokens=50)
        metrics.add_tokens(input_tokens=200, output_tokens=75)
        
        assert metrics.total_input_tokens == 300
        assert metrics.total_output_tokens == 125

    def test_client_metrics_add_cost(self):
        """Test adding cost."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.total_cost_usd == Decimal("0.0")
        
        metrics.add_cost(Decimal("0.50"))
        assert metrics.total_cost_usd == Decimal("0.50")
        
        metrics.add_cost(Decimal("0.30"))
        assert metrics.total_cost_usd == Decimal("0.80")

    def test_client_metrics_mark_started(self):
        """Test marking session start time."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.started_at is None
        
        before_mark = datetime.utcnow()
        metrics.mark_started()
        after_mark = datetime.utcnow()
        
        assert metrics.started_at is not None
        assert before_mark <= metrics.started_at <= after_mark

    def test_client_metrics_mark_started_idempotent(self):
        """Test that marking started multiple times doesn't change the timestamp."""
        metrics = ClientMetrics(session_id=uuid4())
        
        metrics.mark_started()
        first_started_at = metrics.started_at
        
        # Wait a bit and mark again
        import time
        time.sleep(0.01)
        metrics.mark_started()
        
        # Should still be the same timestamp
        assert metrics.started_at == first_started_at

    def test_client_metrics_mark_completed(self):
        """Test marking session completion and duration calculation."""
        metrics = ClientMetrics(session_id=uuid4())
        
        # Mark started first
        start_time = datetime.utcnow()
        metrics.started_at = start_time
        
        # Mark completed after a delay
        import time
        time.sleep(0.01)
        
        metrics.mark_completed()
        
        assert metrics.completed_at is not None
        assert metrics.completed_at > start_time
        assert metrics.total_duration_ms > 0

    def test_client_metrics_mark_completed_without_start(self):
        """Test marking completion without start time."""
        metrics = ClientMetrics(session_id=uuid4())
        
        metrics.mark_completed()
        
        assert metrics.completed_at is not None
        # Duration should be 0 since no start time
        assert metrics.total_duration_ms == 0

    def test_client_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        session_id = uuid4()
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=5)
        
        metrics = ClientMetrics(session_id=session_id)
        metrics.total_messages = 10
        metrics.total_tool_calls = 5
        metrics.total_errors = 2
        metrics.total_retries = 1
        metrics.total_cost_usd = Decimal("1.50")
        metrics.total_input_tokens = 500
        metrics.total_output_tokens = 300
        metrics.total_cache_creation_tokens = 50
        metrics.total_cache_read_tokens = 25
        metrics.total_duration_ms = 5000
        metrics.started_at = start_time
        metrics.completed_at = end_time
        
        result = metrics.to_dict()
        
        expected = {
            "session_id": str(session_id),
            "total_messages": 10,
            "total_tool_calls": 5,
            "total_errors": 2,
            "total_retries": 1,
            "total_cost_usd": 1.50,
            "total_input_tokens": 500,
            "total_output_tokens": 300,
            "total_cache_creation_tokens": 50,
            "total_cache_read_tokens": 25,
            "total_duration_ms": 5000,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
        }
        
        assert result == expected

    def test_client_metrics_to_dict_with_none_timestamps(self):
        """Test to_dict with None timestamps."""
        metrics = ClientMetrics(session_id=uuid4())
        
        result = metrics.to_dict()
        
        assert result["started_at"] is None
        assert result["completed_at"] is None

    def test_client_metrics_get_duration_seconds(self):
        """Test getting duration in seconds."""
        metrics = ClientMetrics(session_id=uuid4())
        
        # No timestamps
        assert metrics.get_duration_seconds() is None
        
        # Only start time
        metrics.started_at = datetime.utcnow()
        assert metrics.get_duration_seconds() is None
        
        # Both timestamps
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=3.5)
        metrics.started_at = start_time
        metrics.completed_at = end_time
        
        duration = metrics.get_duration_seconds()
        assert duration is not None
        assert abs(duration - 3.5) < 0.1  # Allow small floating point differences

    def test_client_metrics_is_completed(self):
        """Test is_completed method."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.is_completed() is False
        
        metrics.completed_at = datetime.utcnow()
        assert metrics.is_completed() is True

    def test_client_metrics_get_total_tokens(self):
        """Test get_total_tokens method."""
        metrics = ClientMetrics(session_id=uuid4())
        
        assert metrics.get_total_tokens() == 0
        
        metrics.add_tokens(
            input_tokens=100,
            output_tokens=50,
            cache_creation_tokens=10,
            cache_read_tokens=5
        )
        
        assert metrics.get_total_tokens() == 165  # 100 + 50 + 10 + 5


class TestClientState:
    """Test cases for ClientState enum."""

    def test_client_state_enum_values(self):
        """Test ClientState enum values."""
        assert ClientState.CREATED == "created"
        assert ClientState.CONNECTING == "connecting"
        assert ClientState.CONNECTED == "connected"
        assert ClientState.DISCONNECTING == "disconnecting"
        assert ClientState.DISCONNECTED == "disconnected"
        assert ClientState.FAILED == "failed"

    def test_client_state_enum_membership(self):
        """Test ClientState enum membership."""
        all_states = [
            ClientState.CREATED,
            ClientState.CONNECTING,
            ClientState.CONNECTED,
            ClientState.DISCONNECTING,
            ClientState.DISCONNECTED,
            ClientState.FAILED,
        ]
        
        for state in all_states:
            assert state in ClientState
        
        assert "invalid_state" not in ClientState