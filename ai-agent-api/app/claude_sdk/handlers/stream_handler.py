"""Stream handler for handling StreamEvent from Claude SDK."""
import logging
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from claude_agent_sdk.types import StreamEvent

from app.domain.value_objects.message import Message as DomainMessage, MessageType
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class StreamHandler:
    """Handle StreamEvent for partial message updates.

    This handler processes streaming events when include_partial_messages=True,
    enabling real-time message updates for chat UI experiences.

    Features:
    - Processes partial message chunks
    - Optionally broadcasts to WebSocket clients
    - Aggregates partial messages into complete messages
    - Tracks message progression in real-time

    Example:
        >>> handler = StreamHandler(db, message_repo, event_broadcaster)
        >>> partial_msg = await handler.handle_stream_event(event, session_id)
        >>> # Event broadcaster sends updates to WebSocket clients
    """

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        event_broadcaster: Optional[Any] = None,
    ):
        """Initialize stream handler with repositories and optional broadcaster.

        Args:
            db: Async database session
            message_repo: Repository for message persistence
            event_broadcaster: Optional WebSocket event broadcaster
        """
        self.db = db
        self.message_repo = message_repo
        self.event_broadcaster = event_broadcaster

    async def handle_stream_event(
        self, event: StreamEvent, session_id: UUID
    ) -> Dict[str, Any]:
        """Process streaming event and broadcast partial update.

        Args:
            event: StreamEvent from SDK with partial message data
            session_id: Session identifier

        Returns:
            Dictionary with partial message data
        """
        logger.debug(
            f"Processing StreamEvent: type={event.event.get('type')}",
            extra={"session_id": str(session_id)},
        )

        # Extract event data
        event_type = event.event.get("type", "unknown")
        event_data = event.event

        # Create partial message representation
        partial_message = {
            "session_id": str(session_id),
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast to WebSocket clients if broadcaster available
        if self.event_broadcaster:
            try:
                await self.event_broadcaster.broadcast(
                    session_id=session_id,
                    event_type="partial_message",
                    data=partial_message,
                )
                logger.debug(
                    f"Broadcasted StreamEvent to WebSocket clients",
                    extra={"session_id": str(session_id)},
                )
            except Exception as e:
                logger.error(
                    f"Failed to broadcast stream event: {str(e)}",
                    extra={"session_id": str(session_id)},
                )

        return partial_message

    async def aggregate_partial_messages(
        self, session_id: UUID, parent_message_id: Optional[UUID] = None
    ) -> Optional[DomainMessage]:
        """Aggregate all partial messages into complete message.

        This method is used when streaming completes to consolidate
        all partial updates into a final message.

        Args:
            session_id: Session identifier
            parent_message_id: Optional parent message to aggregate under

        Returns:
            DomainMessage: Aggregated complete message, or None if no partials found
        """
        logger.info(
            f"Aggregating partial messages for session {session_id}",
            extra={"session_id": str(session_id)},
        )

        # TODO: Implement partial message aggregation
        # This would query partial messages from database and combine them
        # For now, this is a placeholder for Phase 3 implementation

        logger.warning("Partial message aggregation not yet fully implemented")
        return None
