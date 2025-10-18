"""Unit tests for EnhancedClaudeClient."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
from pathlib import Path
from decimal import Decimal

from claude_agent_sdk import CLIConnectionError, ClaudeSDKError
from claude_agent_sdk import AssistantMessage, ResultMessage, UserMessage
from claude_agent_sdk.types import StreamEvent

from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.core.config import ClientConfig, ClientState, ClientMetrics


class TestEnhancedClaudeClient:
    """Test cases for EnhancedClaudeClient."""

    @pytest.fixture
    def sample_config(self):
        """Sample client configuration."""
        return ClientConfig(
            session_id=uuid4(),
            model="claude-sonnet-4-5",
            max_retries=2,
            retry_delay=0.1,  # Fast retry for tests
            working_directory=Path("/tmp/test"),
        )

    @pytest.fixture
    def client(self, sample_config):
        """EnhancedClaudeClient instance."""
        return EnhancedClaudeClient(sample_config)

    def test_client_initialization(self, client, sample_config):
        """Test client initialization."""
        assert client.config == sample_config
        assert client.sdk_client is None
        assert client.state == ClientState.CREATED
        assert isinstance(client.metrics, ClientMetrics)
        assert client.metrics.session_id == sample_config.session_id
        assert client._sdk_options is None

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_success(self, mock_options_builder, mock_sdk_client, client):
        """Test successful connection."""
        # Mock OptionsBuilder
        mock_options = MagicMock()
        mock_options_builder.build.return_value = mock_options
        
        # Mock SDK client
        mock_sdk_instance = AsyncMock()
        mock_sdk_client.return_value = mock_sdk_instance

        await client.connect()

        assert client.state == ClientState.CONNECTED
        assert client.sdk_client == mock_sdk_instance
        assert client._sdk_options == mock_options
        assert client.metrics.started_at is not None
        mock_options_builder.build.assert_called_once()

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_already_connected(self, mock_options_builder, mock_sdk_client, client):
        """Test connection when already connected."""
        client.state = ClientState.CONNECTED
        
        await client.connect()
        
        # Should not call SDK client creation
        mock_sdk_client.assert_not_called()

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_already_connecting(self, mock_options_builder, mock_sdk_client, client):
        """Test connection when already connecting."""
        client.state = ClientState.CONNECTING
        
        await client.connect()
        
        # Should not call SDK client creation
        mock_sdk_client.assert_not_called()

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_with_retry_success(self, mock_options_builder, mock_sdk_client, client):
        """Test connection with retry that eventually succeeds."""
        mock_options = MagicMock()
        mock_options_builder.build.return_value = mock_options
        
        # Mock SDK client to fail first, then succeed
        mock_sdk_client.side_effect = [
            CLIConnectionError("Connection failed"),
            AsyncMock()
        ]

        await client.connect()

        assert client.state == ClientState.CONNECTED
        assert client.metrics.total_retries == 1
        assert client.metrics.total_errors == 1
        assert mock_sdk_client.call_count == 2

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_retry_exhausted(self, mock_options_builder, mock_sdk_client, client):
        """Test connection with retries exhausted."""
        mock_options = MagicMock()
        mock_options_builder.build.return_value = mock_options
        
        # Mock SDK client to always fail
        mock_sdk_client.side_effect = CLIConnectionError("Connection failed")

        with pytest.raises(CLIConnectionError):
            await client.connect()

        assert client.state == ClientState.FAILED
        assert client.metrics.total_retries == client.config.max_retries
        assert client.metrics.total_errors == client.config.max_retries + 1
        assert mock_sdk_client.call_count == client.config.max_retries + 1

    @patch('app.claude_sdk.core.client.ClaudeSDKClient')
    @patch('app.claude_sdk.core.client.OptionsBuilder')
    async def test_connect_non_retryable_error(self, mock_options_builder, mock_sdk_client, client):
        """Test connection with non-retryable error."""
        mock_options = MagicMock()
        mock_options_builder.build.return_value = mock_options
        
        # Mock SDK client to fail with non-retryable error
        mock_sdk_client.side_effect = ClaudeSDKError("SDK error")

        with pytest.raises(ClaudeSDKError):
            await client.connect()

        assert client.state == ClientState.FAILED
        assert client.metrics.total_errors == 1
        assert client.metrics.total_retries == 0
        assert mock_sdk_client.call_count == 1

    async def test_query_not_connected(self, client):
        """Test query when not connected."""
        with pytest.raises(ValueError, match="Client not connected"):
            await client.query("Hello")

    async def test_query_success(self, client):
        """Test successful query."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        client.sdk_client = mock_sdk_client

        await client.query("Hello, Claude!")

        mock_sdk_client.query.assert_called_once_with("Hello, Claude!")

    async def test_query_error(self, client):
        """Test query with error."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        mock_sdk_client.query.side_effect = Exception("Query failed")
        client.sdk_client = mock_sdk_client

        with pytest.raises(Exception, match="Query failed"):
            await client.query("Hello")

        assert client.metrics.total_errors == 1

    async def test_receive_response_not_connected(self, client):
        """Test receive_response when not connected."""
        with pytest.raises(ValueError, match="Client not connected"):
            async for _ in client.receive_response():
                pass

    async def test_receive_response_assistant_message(self, client):
        """Test receiving assistant message."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Create mock assistant message
        mock_message = MagicMock(spec=AssistantMessage)
        
        # Mock async generator
        async def mock_receive():
            yield mock_message
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        messages = []
        async for message in client.receive_response():
            messages.append(message)

        assert len(messages) == 1
        assert messages[0] == mock_message
        assert client.metrics.total_messages == 1

    async def test_receive_response_result_message(self, client):
        """Test receiving result message with metrics update."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Create mock result message
        mock_result = MagicMock(spec=ResultMessage)
        mock_result.total_cost_usd = 1.5
        mock_result.duration_ms = 2500
        
        # Mock async generator
        async def mock_receive():
            yield mock_result
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        messages = []
        async for message in client.receive_response():
            messages.append(message)

        assert len(messages) == 1
        assert messages[0] == mock_result
        assert client.metrics.total_messages == 1
        assert client.metrics.total_cost_usd == Decimal("1.5")
        assert client.metrics.total_duration_ms == 2500

    async def test_receive_response_stream_event(self, client):
        """Test receiving stream event."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Create mock stream event
        mock_stream = MagicMock(spec=StreamEvent)
        
        # Mock async generator
        async def mock_receive():
            yield mock_stream
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        messages = []
        async for message in client.receive_response():
            messages.append(message)

        assert len(messages) == 1
        assert messages[0] == mock_stream
        assert client.metrics.total_messages == 1

    async def test_receive_response_multiple_messages(self, client):
        """Test receiving multiple messages."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Create mock messages
        mock_assistant = MagicMock(spec=AssistantMessage)
        mock_stream = MagicMock(spec=StreamEvent)
        mock_result = MagicMock(spec=ResultMessage)
        mock_result.total_cost_usd = 0.75
        mock_result.duration_ms = 1200
        
        # Mock async generator
        async def mock_receive():
            yield mock_assistant
            yield mock_stream
            yield mock_result
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        messages = []
        async for message in client.receive_response():
            messages.append(message)

        assert len(messages) == 3
        assert messages[0] == mock_assistant
        assert messages[1] == mock_stream
        assert messages[2] == mock_result
        assert client.metrics.total_messages == 3
        assert client.metrics.total_cost_usd == Decimal("0.75")

    async def test_receive_response_error(self, client):
        """Test receive_response with error."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Mock async generator that raises error
        async def mock_receive():
            raise Exception("Receive failed")
            yield  # unreachable
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        with pytest.raises(Exception, match="Receive failed"):
            async for _ in client.receive_response():
                pass

        assert client.metrics.total_errors == 1

    async def test_disconnect_success(self, client):
        """Test successful disconnect."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        client.sdk_client = AsyncMock()
        client.metrics.mark_started()

        result_metrics = await client.disconnect()

        assert client.state == ClientState.DISCONNECTED
        assert client.sdk_client is None
        assert result_metrics == client.metrics
        assert client.metrics.is_completed() is True

    async def test_disconnect_not_connected(self, client):
        """Test disconnect when not connected."""
        client.state = ClientState.CREATED

        result_metrics = await client.disconnect()

        assert client.state == ClientState.DISCONNECTED
        assert result_metrics == client.metrics

    async def test_disconnect_error(self, client):
        """Test disconnect with error."""
        # Setup connected state with problematic cleanup
        client.state = ClientState.CONNECTED
        client.sdk_client = AsyncMock()
        
        # Force an error during disconnect by making metrics.mark_completed() raise
        with patch.object(client.metrics, 'mark_completed', side_effect=Exception("Disconnect error")):
            with pytest.raises(Exception, match="Disconnect error"):
                await client.disconnect()

        assert client.state == ClientState.FAILED

    async def test_get_metrics(self, client):
        """Test getting current metrics."""
        metrics = await client.get_metrics()
        assert metrics == client.metrics

    async def test_context_manager_success(self, sample_config):
        """Test async context manager usage - success case."""
        with patch('app.claude_sdk.core.client.ClaudeSDKClient'), \
             patch('app.claude_sdk.core.client.OptionsBuilder'):
            
            async with EnhancedClaudeClient(sample_config) as client:
                assert client.state == ClientState.CONNECTED
                assert client.sdk_client is not None

            assert client.state == ClientState.DISCONNECTED

    async def test_context_manager_connection_error(self, sample_config):
        """Test async context manager with connection error."""
        with patch('app.claude_sdk.core.client.ClaudeSDKClient') as mock_sdk, \
             patch('app.claude_sdk.core.client.OptionsBuilder'):
            
            mock_sdk.side_effect = CLIConnectionError("Connection failed")

            with pytest.raises(CLIConnectionError):
                async with EnhancedClaudeClient(sample_config) as client:
                    pass  # Should not reach here

    async def test_context_manager_runtime_error(self, sample_config):
        """Test async context manager with runtime error."""
        with patch('app.claude_sdk.core.client.ClaudeSDKClient'), \
             patch('app.claude_sdk.core.client.OptionsBuilder'):
            
            with pytest.raises(RuntimeError, match="Test error"):
                async with EnhancedClaudeClient(sample_config) as client:
                    assert client.state == ClientState.CONNECTED
                    raise RuntimeError("Test error")

            # Client should still be properly disconnected
            assert client.state == ClientState.DISCONNECTED

    async def test_exponential_backoff_calculation(self, client):
        """Test exponential backoff calculation during retries."""
        expected_delays = []
        actual_delays = []
        
        with patch('app.claude_sdk.core.client.ClaudeSDKClient') as mock_sdk, \
             patch('app.claude_sdk.core.client.OptionsBuilder'), \
             patch('asyncio.sleep') as mock_sleep:
            
            # Mock SDK to always fail
            mock_sdk.side_effect = CLIConnectionError("Connection failed")
            
            # Calculate expected delays
            for attempt in range(client.config.max_retries):
                expected_delays.append(client.config.retry_delay * (2 ** attempt))
            
            try:
                await client.connect()
            except CLIConnectionError:
                pass

            # Check that sleep was called with exponential backoff delays
            assert mock_sleep.call_count == client.config.max_retries
            for i, call in enumerate(mock_sleep.call_args_list):
                assert call[0][0] == expected_delays[i]

    async def test_metrics_tracking_comprehensive(self, client):
        """Test comprehensive metrics tracking during session."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        client.sdk_client = mock_sdk_client
        
        # Start metrics
        client.metrics.mark_started()
        initial_time = client.metrics.started_at
        
        # Simulate various operations
        client.metrics.increment_messages()
        client.metrics.increment_tool_calls()
        client.metrics.increment_errors()
        client.metrics.increment_retries()
        client.metrics.add_cost(Decimal("0.25"))
        client.metrics.add_tokens(input_tokens=100, output_tokens=50)
        
        # Complete session
        await client.disconnect()
        
        # Verify comprehensive metrics
        assert client.metrics.total_messages == 1
        assert client.metrics.total_tool_calls == 1
        assert client.metrics.total_errors == 1
        assert client.metrics.total_retries == 1
        assert client.metrics.total_cost_usd == Decimal("0.25")
        assert client.metrics.total_input_tokens == 100
        assert client.metrics.total_output_tokens == 50
        assert client.metrics.started_at == initial_time
        assert client.metrics.completed_at is not None
        assert client.metrics.total_duration_ms > 0

    async def test_client_state_transitions(self, client):
        """Test proper client state transitions."""
        # Initial state
        assert client.state == ClientState.CREATED
        
        with patch('app.claude_sdk.core.client.ClaudeSDKClient'), \
             patch('app.claude_sdk.core.client.OptionsBuilder'):
            
            # Connect
            await client.connect()
            assert client.state == ClientState.CONNECTED
            
            # Disconnect
            await client.disconnect()
            assert client.state == ClientState.DISCONNECTED

    async def test_logging_integration(self, client, caplog):
        """Test that proper logging occurs during operations."""
        import logging
        
        with patch('app.claude_sdk.core.client.ClaudeSDKClient'), \
             patch('app.claude_sdk.core.client.OptionsBuilder'):
            
            # Test connection logging
            await client.connect()
            
            # Test query logging
            await client.query("test query")
            
            # Test disconnect logging
            await client.disconnect()
        
        # Verify log messages contain session ID
        session_id_str = str(client.config.session_id)
        log_messages = [record.message for record in caplog.records]
        
        # Should have logged connection, query, and disconnect events
        assert any(session_id_str in msg for msg in log_messages)
        assert any("created for session" in msg for msg in log_messages)
        assert any("Successfully connected" in msg for msg in log_messages)
        assert any("Sending query" in msg for msg in log_messages)

    async def test_result_message_none_cost(self, client):
        """Test handling ResultMessage with None cost."""
        # Setup connected state
        client.state = ClientState.CONNECTED
        mock_sdk_client = AsyncMock()
        
        # Create mock result message with None cost
        mock_result = MagicMock(spec=ResultMessage)
        mock_result.total_cost_usd = None
        mock_result.duration_ms = 1500
        
        # Mock async generator
        async def mock_receive():
            yield mock_result
        
        mock_sdk_client.receive_response.return_value = mock_receive()
        client.sdk_client = mock_sdk_client

        # This should not raise an error
        async for message in client.receive_response():
            assert message == mock_result

        # Cost should remain 0 since None was provided
        assert client.metrics.total_cost_usd == Decimal("0.0")
        assert client.metrics.total_duration_ms == 1500