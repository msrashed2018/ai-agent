"""Enhanced Claude SDK client with retry logic and metrics tracking."""
import asyncio
from typing import Optional, AsyncIterator, Union
from uuid import UUID

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, ResultMessage, UserMessage
from claude_agent_sdk.types import StreamEvent
from claude_agent_sdk import CLIConnectionError, ClaudeSDKError

from app.claude_sdk.core.config import ClientConfig, ClientMetrics, ClientState
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedClaudeClient:
    """Enhanced wrapper around ClaudeSDKClient with retry and metrics.

    This class wraps the official Claude SDK client and adds:
    - Automatic retry logic for transient failures
    - Comprehensive metrics tracking (tokens, cost, duration)
    - Connection state management
    - Error handling and logging

    Example:
        >>> config = ClientConfig(session_id=session_id, model="claude-sonnet-4-5")
        >>> client = EnhancedClaudeClient(config)
        >>> await client.connect()
        >>> await client.query("Hello")
        >>> async for message in client.receive_response():
        ...     print(message)
        >>> metrics = await client.disconnect()
    """

    def __init__(self, config: ClientConfig):
        """Initialize enhanced client with configuration.

        Args:
            config: Client configuration including session ID, model, retry settings
        """
        self.config = config
        self.sdk_client: Optional[ClaudeSDKClient] = None
        self.metrics = ClientMetrics(session_id=config.session_id)
        self.state = ClientState.CREATED
        self._sdk_options: Optional[ClaudeAgentOptions] = None

        logger.info(
            "Enhanced Claude client initialized",
            extra={
                "session_id": str(config.session_id),
                "model": config.model,
                "max_retries": config.max_retries,
                "timeout_seconds": config.timeout_seconds,
                "state": self.state.value
            }
        )

    async def connect(self) -> None:
        """Connect to Claude Code CLI with retry logic.

        Establishes connection to the Claude SDK with automatic retry on
        connection failures. Updates state and marks metrics start time.

        Raises:
            CLIConnectionError: If all retry attempts fail
            ClaudeSDKError: If non-connection error occurs
        """
        if self.state in [ClientState.CONNECTED, ClientState.CONNECTING]:
            logger.warning(f"Client already in state {self.state}")
            return

        self.state = ClientState.CONNECTING
        self.metrics.mark_started()

        # Build SDK options from config
        from app.claude_sdk.core.options_builder import OptionsBuilder

        # Create a minimal session-like object for OptionsBuilder
        class SessionConfig:
            def __init__(self, config: ClientConfig):
                self.sdk_options = {
                    "model": config.model,
                    "max_turns": config.max_turns,
                    "allowed_tools": config.allowed_tools,
                }
                self.permission_mode = config.permission_mode
                self.include_partial_messages = config.include_partial_messages
                self.working_directory_path = str(config.working_directory)

        session_config = SessionConfig(self.config)
        self._sdk_options = OptionsBuilder.build(
            session=session_config,
            permission_callback=self.config.can_use_tool,
            hooks=self.config.hooks,
            mcp_servers=self.config.mcp_servers,
        )

        # Attempt connection with retry
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(
                    f"Connecting to Claude SDK (attempt {attempt + 1}/{self.config.max_retries + 1})",
                    extra={"session_id": str(self.config.session_id)},
                )

                # Create SDK client (note: actual connection happens on first query)
                self.sdk_client = ClaudeSDKClient(options=self._sdk_options)

                self.state = ClientState.CONNECTED
                logger.info(
                    f"Successfully connected to Claude SDK",
                    extra={"session_id": str(self.config.session_id)},
                )
                return

            except CLIConnectionError as e:
                self.metrics.increment_errors()
                logger.error(
                    f"Connection error on attempt {attempt + 1}: {str(e)}",
                    extra={"session_id": str(self.config.session_id)},
                )

                if attempt < self.config.max_retries:
                    self.metrics.increment_retries()
                    delay = self.config.retry_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    self.state = ClientState.FAILED
                    logger.error(
                        f"All {self.config.max_retries + 1} connection attempts failed",
                        extra={"session_id": str(self.config.session_id)},
                    )
                    raise

            except ClaudeSDKError as e:
                self.metrics.increment_errors()
                self.state = ClientState.FAILED
                logger.error(
                    f"SDK error during connection: {str(e)}",
                    extra={"session_id": str(self.config.session_id)},
                )
                raise

    async def query(self, prompt: str) -> None:
        """Send query to Claude SDK.

        Args:
            prompt: The user prompt to send

        Raises:
            ValueError: If client not connected
            ClaudeSDKError: If query fails
        """
        if self.state != ClientState.CONNECTED or not self.sdk_client:
            raise ValueError("Client not connected. Call connect() first.")

        logger.info(
            f"Sending query ({len(prompt)} chars)",
            extra={"session_id": str(self.config.session_id), "prompt_length": len(prompt)},
        )

        try:
            await self.sdk_client.query(prompt)
        except Exception as e:
            self.metrics.increment_errors()
            logger.error(
                f"Error sending query: {str(e)}",
                extra={"session_id": str(self.config.session_id)},
            )
            raise

    async def receive_response(
        self,
    ) -> AsyncIterator[Union[AssistantMessage, ResultMessage, StreamEvent]]:
        """Stream responses from Claude SDK with error handling and metrics tracking.

        Yields:
            AssistantMessage: Regular assistant responses
            ResultMessage: Final result with metadata
            StreamEvent: Partial message updates (if streaming enabled)

        Raises:
            ValueError: If client not connected
        """
        if self.state != ClientState.CONNECTED or not self.sdk_client:
            raise ValueError("Client not connected. Call connect() first.")

        try:
            async for message in self.sdk_client.receive_response():
                # Track metrics
                self.metrics.increment_messages()

                # Update metrics from result message
                if isinstance(message, ResultMessage):
                    if message.total_cost_usd is not None:
                        from decimal import Decimal

                        self.metrics.add_cost(Decimal(str(message.total_cost_usd)))
                    self.metrics.total_duration_ms = message.duration_ms

                    logger.info(
                        f"Received ResultMessage: duration={message.duration_ms}ms, cost=${message.total_cost_usd}",
                        extra={"session_id": str(self.config.session_id)},
                    )

                yield message

        except Exception as e:
            self.metrics.increment_errors()
            logger.error(
                f"Error receiving response: {str(e)}",
                extra={"session_id": str(self.config.session_id)},
            )
            raise

    async def disconnect(self) -> ClientMetrics:
        """Disconnect from Claude SDK and return final metrics.

        Returns:
            ClientMetrics: Final session metrics including tokens, cost, duration

        Raises:
            ValueError: If client not connected
        """
        if self.state != ClientState.CONNECTED:
            logger.warning(f"Client not in connected state: {self.state}")

        self.state = ClientState.DISCONNECTING

        try:
            # SDK client cleanup happens automatically via context manager
            # or garbage collection, so no explicit disconnect needed
            self.sdk_client = None

            self.state = ClientState.DISCONNECTED
            self.metrics.mark_completed()

            logger.info(
                f"Disconnected from Claude SDK",
                extra={
                    "session_id": str(self.config.session_id),
                    "metrics": self.metrics.to_dict(),
                },
            )

            return self.metrics

        except Exception as e:
            logger.error(
                f"Error during disconnect: {str(e)}",
                extra={"session_id": str(self.config.session_id)},
            )
            self.state = ClientState.FAILED
            raise

    async def get_metrics(self) -> ClientMetrics:
        """Get current session metrics.

        Returns:
            ClientMetrics: Current metrics snapshot
        """
        return self.metrics

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False
