"""Session persister for saving session state, messages, and tool calls."""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.models.message import MessageModel
from app.models.tool_call import ToolCallModel

logger = logging.getLogger(__name__)


class SessionPersister:
    """Persist session data including messages and tool calls.

    Handles conversion from SDK message objects to database models
    and persistence via repositories.
    """

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository
    ):
        """Initialize session persister.

        Args:
            db: Database session
            session_repo: Session repository
            message_repo: Message repository
            tool_call_repo: Tool call repository
        """
        self.db = db
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo

    async def persist_message(
        self,
        session_id: UUID,
        message_type: str,
        content: str,
        sequence_number: int,
        model: Optional[str] = None,
        is_partial: bool = False,
        parent_message_id: Optional[UUID] = None
    ) -> MessageModel:
        """Persist a message to the database.

        Args:
            session_id: Session ID
            message_type: Type of message (human, assistant, system, etc.)
            content: Message content
            sequence_number: Message sequence number
            model: Model name if assistant message
            is_partial: Whether this is a partial streaming message
            parent_message_id: Parent message ID for partial messages

        Returns:
            Created message model
        """
        try:
            message = MessageModel(
                session_id=session_id,
                message_type=message_type,
                content=content,
                sequence_number=sequence_number,
                model=model,
                is_partial=is_partial,
                parent_message_id=parent_message_id
            )

            created = await self.message_repo.create(message)

            logger.debug(
                f"Persisted message: type={message_type}, "
                f"seq={sequence_number}, partial={is_partial}",
                extra={"session_id": str(session_id)}
            )

            return created

        except Exception as e:
            logger.error(
                f"Failed to persist message: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            raise

    async def persist_tool_call(
        self,
        session_id: UUID,
        message_id: Optional[UUID],
        tool_name: str,
        tool_use_id: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        is_error: bool = False,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None
    ) -> ToolCallModel:
        """Persist a tool call to the database.

        Args:
            session_id: Session ID
            message_id: Message ID
            tool_name: Tool name
            tool_use_id: Tool use ID from SDK
            tool_input: Tool input parameters
            tool_output: Tool output/result
            status: Tool call status
            is_error: Whether tool execution errored
            error_message: Error message if failed
            started_at: Tool execution start time
            completed_at: Tool execution completion time
            duration_ms: Execution duration in milliseconds

        Returns:
            Created tool call model
        """
        try:
            tool_call = ToolCallModel(
                session_id=session_id,
                message_id=message_id,
                tool_name=tool_name,
                tool_use_id=tool_use_id,
                tool_input=tool_input,
                tool_output=tool_output,
                status=status,
                is_error=is_error,
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms
            )

            created = await self.tool_call_repo.create(tool_call)

            logger.debug(
                f"Persisted tool call: {tool_name}, status={status}",
                extra={"session_id": str(session_id), "tool_use_id": tool_use_id}
            )

            return created

        except Exception as e:
            logger.error(
                f"Failed to persist tool call: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            raise

    async def update_session_metrics(
        self,
        session_id: UUID,
        total_messages: Optional[int] = None,
        total_tool_calls: Optional[int] = None,
        total_cost_usd: Optional[float] = None,
        api_input_tokens: Optional[int] = None,
        api_output_tokens: Optional[int] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Update session-level metrics.

        Args:
            session_id: Session ID
            total_messages: Total message count
            total_tool_calls: Total tool call count
            total_cost_usd: Total API cost
            api_input_tokens: Total input tokens
            api_output_tokens: Total output tokens
            duration_ms: Total duration
        """
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return

            # Update metrics
            update_data = {}
            if total_messages is not None:
                update_data["total_messages"] = total_messages
            if total_tool_calls is not None:
                update_data["total_tool_calls"] = total_tool_calls
            if total_cost_usd is not None:
                update_data["total_cost_usd"] = total_cost_usd
            if api_input_tokens is not None:
                update_data["api_input_tokens"] = api_input_tokens
            if api_output_tokens is not None:
                update_data["api_output_tokens"] = api_output_tokens
            if duration_ms is not None:
                update_data["duration_ms"] = duration_ms

            await self.session_repo.update(session_id, **update_data)

            logger.debug(
                f"Updated session metrics: {list(update_data.keys())}",
                extra={"session_id": str(session_id)}
            )

        except Exception as e:
            logger.error(
                f"Failed to update session metrics: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            # Don't raise - metrics update failure shouldn't break execution

    async def batch_persist_messages(
        self,
        session_id: UUID,
        messages: List[Dict[str, Any]]
    ) -> List[MessageModel]:
        """Persist multiple messages in batch.

        Args:
            session_id: Session ID
            messages: List of message dictionaries

        Returns:
            List of created message models
        """
        created_messages = []

        for msg in messages:
            try:
                created = await self.persist_message(
                    session_id=session_id,
                    **msg
                )
                created_messages.append(created)
            except Exception as e:
                logger.error(
                    f"Failed to persist message in batch: {type(e).__name__} - {str(e)}",
                    exc_info=True
                )
                # Continue with other messages
                continue

        return created_messages
