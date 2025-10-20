"""Message Processor for Claude SDK integration.

Processes message streams from the official Claude SDK, converting SDK messages
to our domain entities and persisting to database.

Based on Document 5: Session Management - Message Processing Pipeline
"""

from typing import AsyncIterator, Any, Dict
from uuid import UUID, uuid4
from datetime import datetime

from claude_agent_sdk.types import (
    Message as SDKMessage,
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from app.domain.entities.session import Session
from app.domain.value_objects.message import Message, MessageType
from app.domain.value_objects.tool_call import ToolCall
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.repositories.session_repository import SessionRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger

logger = get_logger(__name__)


class MessageProcessor:
    """Process message stream from Claude SDK.
    
    Pipeline stages:
    1. Parse SDK message to domain Message
    2. Persist to database
    3. Extract tool calls (ToolUseBlock, ToolResultBlock)
    4. Update session metrics (cost, tokens)
    5. Broadcast to WebSocket (if available)
    
    This bridges the official SDK and our domain model.
    """

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository,
        session_repo: SessionRepository,
        event_broadcaster=None,  # Optional EventBroadcaster
    ):
        """Initialize message processor with repositories."""
        self.db = db
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo
        self.session_repo = session_repo
        self.event_broadcaster = event_broadcaster

    async def process_message_stream(
        self,
        session: Session,
        sdk_messages: AsyncIterator[SDKMessage],
    ) -> AsyncIterator[Message]:
        """Process stream of messages from SDK.
        
        Args:
            session: Session entity
            sdk_messages: Async iterator of SDK messages
            
        Yields:
            Domain Message entities
            
        Example:
            >>> async with client.receive_response() as sdk_messages:
            ...     async for message in processor.process_message_stream(session, sdk_messages):
            ...         print(message)
        """
        message_count = 0

        async for sdk_msg in sdk_messages:
            try:
                # 1. Parse SDK message to domain message
                sequence = session.total_messages + message_count + 1
                domain_msg = self._parse_message(session.id, sdk_msg, sequence)

                # 2. Persist message to database
                await self.message_repo.create(domain_msg)
                message_count += 1

                # 3. Extract tool calls if assistant message
                if domain_msg.message_type == MessageType.ASSISTANT:
                    await self._extract_tool_calls(session, domain_msg)

                # 4. Update metrics if result message
                if domain_msg.message_type == MessageType.RESULT:
                    await self._update_metrics(session, domain_msg)

                # 5. Broadcast event to WebSocket subscribers
                if self.event_broadcaster:
                    await self.event_broadcaster.broadcast_message(
                        session.id, domain_msg
                    )

                # 6. Yield to caller
                yield domain_msg

            except Exception as e:
                logger.error(f"Error processing message in session {session.id}: {e}")
                # Continue processing remaining messages
                continue

        # Update session message count after stream completes
        session.total_messages += message_count
        await self.session_repo.update(session)
        await self.db.commit()

    def _parse_message(
        self,
        session_id: UUID,
        sdk_msg: SDKMessage,
        sequence: int,
    ) -> Message:
        """Convert SDK message to domain message.
        
        Maps official SDK message types to our domain model.
        
        Args:
            session_id: Session UUID
            sdk_msg: SDK message (UserMessage, AssistantMessage, etc.)
            sequence: Message sequence number
            
        Returns:
            Domain Message entity
        """
        message_id = uuid4()

        # Determine message type and extract content
        if isinstance(sdk_msg, UserMessage):
            message_type = MessageType.USER
            content = self._serialize_user_content(sdk_msg.content)

        elif isinstance(sdk_msg, AssistantMessage):
            message_type = MessageType.ASSISTANT
            content = self._serialize_assistant_content(sdk_msg.content)

        elif isinstance(sdk_msg, SystemMessage):
            message_type = MessageType.SYSTEM
            content = {
                "subtype": sdk_msg.subtype,
                "data": sdk_msg.data,
            }

        elif isinstance(sdk_msg, ResultMessage):
            message_type = MessageType.RESULT
            content = {
                "subtype": sdk_msg.subtype,
                "duration_ms": sdk_msg.duration_ms,
                "duration_api_ms": sdk_msg.duration_api_ms,
                "is_error": sdk_msg.is_error,
                "num_turns": sdk_msg.num_turns,
                "session_id": sdk_msg.session_id,
                "total_cost_usd": sdk_msg.total_cost_usd,
                "usage": sdk_msg.usage,
                "result": sdk_msg.result,
            }

        elif isinstance(sdk_msg, StreamEvent):
            # StreamEvent is for partial messages (when include_partial_messages=True)
            message_type = MessageType.SYSTEM
            content = {
                "subtype": "stream_event",
                "uuid": sdk_msg.uuid,
                "session_id": sdk_msg.session_id,
                "event": sdk_msg.event,
                "parent_tool_use_id": sdk_msg.parent_tool_use_id,
            }

        else:
            # Unknown message type
            message_type = MessageType.SYSTEM
            content = {"raw": str(sdk_msg)}

        # Create domain Message
        return Message(
            id=message_id,
            session_id=session_id,
            sequence_number=sequence,
            message_type=message_type,
            content=content,
        )

    def _serialize_user_content(self, content: Any) -> Dict:
        """Serialize user message content."""
        if isinstance(content, str):
            return {"text": content}
        elif isinstance(content, list):
            # List of content blocks
            return {"content": [self._serialize_content_block(b) for b in content]}
        else:
            return {"raw": str(content)}

    def _serialize_assistant_content(self, content: list) -> Dict:
        """Serialize assistant message content blocks."""
        return {
            "content": [self._serialize_content_block(block) for block in content]
        }

    def _serialize_content_block(self, block: Any) -> Dict:
        """Serialize individual content block."""
        if isinstance(block, TextBlock):
            return {"type": "text", "text": block.text}

        elif isinstance(block, ThinkingBlock):
            return {
                "type": "thinking",
                "thinking": block.thinking,
                "signature": block.signature,
            }

        elif isinstance(block, ToolUseBlock):
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }

        elif isinstance(block, ToolResultBlock):
            return {
                "type": "tool_result",
                "tool_use_id": block.tool_use_id,
                "content": block.content,
                "is_error": block.is_error,
            }

        else:
            # Unknown block type
            return {"type": "unknown", "raw": str(block)}

    async def _extract_tool_calls(
        self,
        session: Session,
        message: Message,
    ) -> None:
        """Extract and persist tool calls from assistant message.
        
        Creates ToolCall records for tool_use blocks and updates them
        when tool_result blocks are found.
        
        Args:
            session: Session entity
            message: Domain message with tool blocks
        """
        content_blocks = message.content.get("content", [])

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == "tool_use":
                # Create new tool call record
                tool_call = ToolCall(
                    id=uuid4(),
                    session_id=session.id,
                    message_id=message.id,
                    tool_name=block["name"],
                    tool_use_id=block["id"],
                    tool_input=block["input"],
                    status="running",
                    started_at=datetime.utcnow(),
                )
                
                # Persist to database
                await self.tool_call_repo.create(tool_call)
                
                # Increment session counter
                session.total_tool_calls = (session.total_tool_calls or 0) + 1

            elif block_type == "tool_result":
                # Update existing tool call with result
                tool_use_id = block["tool_use_id"]
                tool_call = await self.tool_call_repo.get_by_tool_use_id(tool_use_id)

                if tool_call:
                    tool_call.tool_output = block.get("content")
                    tool_call.is_error = block.get("is_error", False)
                    tool_call.status = "error" if tool_call.is_error else "success"
                    tool_call.completed_at = datetime.utcnow()

                    # Calculate duration
                    if tool_call.started_at:
                        duration = tool_call.completed_at - tool_call.started_at
                        tool_call.duration_ms = int(duration.total_seconds() * 1000)

                    # Update in database
                    await self.tool_call_repo.update(tool_call)

    async def _update_metrics(
        self,
        session: Session,
        result_message: Message,
    ) -> None:
        """Update session metrics from result message.
        
        Extracts cost, token usage, and other metrics from the SDK
        result message and updates the session entity.
        
        Args:
            session: Session entity to update
            result_message: Domain message with result data
        """
        result_data = result_message.content

        # Update cost
        cost = result_data.get("total_cost_usd", 0)
        if cost and cost > 0:
            current_cost = session.total_cost_usd or 0
            session.total_cost_usd = current_cost + cost

        # Update token usage
        usage = result_data.get("usage", {})
        if usage:
            session.api_input_tokens = (session.api_input_tokens or 0) + usage.get("input_tokens", 0)
            session.api_output_tokens = (session.api_output_tokens or 0) + usage.get("output_tokens", 0)
            session.api_cache_creation_tokens = (session.api_cache_creation_tokens or 0) + usage.get("cache_creation_input_tokens", 0)
            session.api_cache_read_tokens = (session.api_cache_read_tokens or 0) + usage.get("cache_read_input_tokens", 0)

        # Store full result data for reference
        if not hasattr(session, 'result_data') or session.result_data is None:
            session.result_data = {}
        session.result_data.update(result_data)

        # Update turn count
        num_turns = result_data.get("num_turns", 0)
        if num_turns > 0:
            session.total_turns = num_turns


class EventBroadcaster:
    """Event broadcaster for WebSocket message streaming.
    
    Optional component for real-time message broadcasting to connected clients.
    """

    def __init__(self):
        """Initialize event broadcaster."""
        self.subscribers: Dict[UUID, list] = {}

    async def broadcast_message(self, session_id: UUID, message: Message) -> None:
        """Broadcast message to session subscribers.
        
        Args:
            session_id: Session UUID
            message: Domain message to broadcast
        """
        if session_id in self.subscribers:
            # Convert message to dict for JSON serialization
            message_dict = {
                "id": str(message.id),
                "session_id": str(message.session_id),
                "sequence_number": message.sequence_number,
                "message_type": message.message_type.value,
                "content": message.content,
                "created_at": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
            }

            # Send to all subscribers
            for subscriber in self.subscribers[session_id]:
                try:
                    await subscriber.send_json(message_dict)
                except Exception as e:
                    logger.error(f"Error broadcasting to subscriber: {e}")

    def subscribe(self, session_id: UUID, websocket) -> None:
        """Add WebSocket subscriber for session.
        
        Args:
            session_id: Session UUID
            websocket: WebSocket connection
        """
        if session_id not in self.subscribers:
            self.subscribers[session_id] = []
        self.subscribers[session_id].append(websocket)

    def unsubscribe(self, session_id: UUID, websocket) -> None:
        """Remove WebSocket subscriber.
        
        Args:
            session_id: Session UUID
            websocket: WebSocket connection
        """
        if session_id in self.subscribers:
            self.subscribers[session_id].remove(websocket)
            if not self.subscribers[session_id]:
                del self.subscribers[session_id]
