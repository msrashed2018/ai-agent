"""Interactive executor for real-time chat sessions with streaming."""
import logging
from typing import AsyncIterator, Optional, Any

from claude_agent_sdk import AssistantMessage, ResultMessage
from claude_agent_sdk.types import StreamEvent

from app.domain.entities.session import Session
from app.domain.value_objects.message import Message as DomainMessage
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.stream_handler import StreamHandler
from app.claude_sdk.handlers.result_handler import ResultHandler
from app.claude_sdk.handlers.error_handler import ErrorHandler
from app.claude_sdk.execution.base_executor import BaseExecutor

logger = logging.getLogger(__name__)


class InteractiveExecutor(BaseExecutor):
    """Execute interactive chat sessions with real-time streaming.

    This executor provides ChatGPT-like real-time streaming experience:
    - Enables partial message updates (streaming)
    - Broadcasts events to WebSocket clients
    - Processes messages as they arrive
    - Suitable for interactive UI applications

    Reference: POC script 07_advanced_streaming.py for streaming patterns
    """

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        stream_handler: StreamHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        event_broadcaster: Optional[Any] = None,
    ):
        """Initialize interactive executor with streaming support.

        Args:
            session: Domain Session entity
            client: Enhanced Claude SDK client
            message_handler: Handler for processing messages
            stream_handler: Handler for streaming events
            result_handler: Handler for processing results
            error_handler: Handler for error recovery
            event_broadcaster: Optional WebSocket event broadcaster
        """
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.stream_handler = stream_handler
        self.event_broadcaster = event_broadcaster

    async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
        """Execute query and stream responses in real-time.

        Args:
            prompt: User prompt

        Yields:
            DomainMessage: Agent messages as they arrive

        Raises:
            Exception: If execution fails
        """
        logger.info(
            f"InteractiveExecutor executing query with streaming",
            extra={"session_id": str(self.session.id)},
        )

        try:
            # Enable partial messages for streaming
            self.client.config.include_partial_messages = True

            # Send query
            await self.client.query(prompt)

            # Stream responses
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    # Process and persist assistant message
                    domain_message = await self.message_handler.handle_assistant_message(
                        message, self.session.id
                    )

                    # Broadcast to WebSocket if available
                    if self.event_broadcaster:
                        await self.event_broadcaster.broadcast(
                            session_id=self.session.id,
                            event_type="message",
                            data={"message": domain_message},
                        )

                    yield domain_message

                elif isinstance(message, StreamEvent):
                    # Handle streaming event for partial updates
                    await self.stream_handler.handle_stream_event(message, self.session.id)

                elif isinstance(message, ResultMessage):
                    # Process final result and metrics
                    await self.result_handler.handle_result_message(message, self.session.id)
                    break

        except Exception as e:
            await self._handle_error(e, {"prompt": prompt})
            raise
