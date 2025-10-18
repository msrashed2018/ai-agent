"""Message handler for processing AssistantMessage from Claude SDK."""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ThinkingBlock

from app.domain.value_objects.message import Message as DomainMessage, MessageType
from app.domain.value_objects.tool_call import ToolCall as DomainToolCall
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository

logger = logging.getLogger(__name__)


class MessageHandler:
    """Process AssistantMessage and extract content blocks.

    This handler:
    - Converts SDK AssistantMessage to domain entities
    - Extracts and persists text blocks
    - Tracks tool usage blocks
    - Persists tool result blocks
    - Handles thinking blocks (extended thinking)
    - Stores all data to database

    Example:
        >>> handler = MessageHandler(db, message_repo, tool_call_repo)
        >>> domain_message = await handler.handle_assistant_message(sdk_message, session_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository,
    ):
        """Initialize message handler with repositories.

        Args:
            db: Async database session
            message_repo: Repository for message persistence
            tool_call_repo: Repository for tool call persistence
        """
        self.db = db
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo

    async def handle_assistant_message(
        self, message: AssistantMessage, session_id: UUID
    ) -> DomainMessage:
        """Process AssistantMessage from SDK and persist to database.

        Args:
            message: AssistantMessage from Claude SDK
            session_id: Session identifier

        Returns:
            DomainMessage: Domain entity representation

        Raises:
            Exception: If persistence fails
        """
        logger.info(
            f"Processing AssistantMessage: model={message.model}, blocks={len(message.content)}",
            extra={"session_id": str(session_id)},
        )

        # Extract all content
        text_content: List[str] = []
        thinking_content: List[str] = []
        tool_use_blocks: List[ToolUseBlock] = []
        tool_result_blocks: List[ToolResultBlock] = []

        for block in message.content:
            if isinstance(block, TextBlock):
                text_content.append(block.text)

            elif isinstance(block, ThinkingBlock):
                # Extended thinking content
                thinking_content.append(block.thinking)

            elif isinstance(block, ToolUseBlock):
                tool_use_blocks.append(block)

            elif isinstance(block, ToolResultBlock):
                tool_result_blocks.append(block)

        # Combine all text content
        combined_content = "\n\n".join(text_content) if text_content else ""
        combined_thinking = "\n\n".join(thinking_content) if thinking_content else None

        # Get next sequence number for this session
        sequence_number = await self.message_repo.get_next_sequence_number(session_id)

        # Create message ID
        message_id = uuid4()

        # Persist message to database
        from app.models.message import MessageModel

        message_model = MessageModel(
            id=message_id,
            session_id=session_id,
            message_type=MessageType.ASSISTANT.value,
            content=combined_content,
            sequence_number=sequence_number,
            model=message.model,
            thinking_content=combined_thinking,
            is_partial=False,
            created_at=datetime.utcnow(),
        )

        self.db.add(message_model)
        await self.db.flush()

        logger.info(
            f"Persisted AssistantMessage: id={message_id}, sequence={sequence_number}",
            extra={
                "session_id": str(session_id),
                "message_id": str(message_id),
                "sequence_number": sequence_number,
            },
        )

        # Process tool use blocks
        for tool_block in tool_use_blocks:
            await self.handle_tool_use_block(tool_block, session_id, message_id)

        # Process tool result blocks
        for result_block in tool_result_blocks:
            await self.handle_tool_result_block(result_block, session_id, message_id)

        # Create domain entity
        domain_message = DomainMessage(
            id=message_id,
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=combined_content,
            sequence_number=sequence_number,
            model=message.model,
            created_at=message_model.created_at,
        )

        return domain_message

    async def handle_tool_use_block(
        self, block: ToolUseBlock, session_id: UUID, message_id: UUID
    ) -> DomainToolCall:
        """Extract and persist tool usage.

        Args:
            block: ToolUseBlock from SDK message
            session_id: Session identifier
            message_id: Parent message identifier

        Returns:
            DomainToolCall: Domain entity representation
        """
        logger.info(
            f"Processing ToolUseBlock: name={block.name}, id={block.id}",
            extra={"session_id": str(session_id), "tool_name": block.name, "tool_use_id": block.id},
        )

        # Create tool call in database
        from app.models.tool_call import ToolCallModel

        tool_call_id = uuid4()
        tool_call_model = ToolCallModel(
            id=tool_call_id,
            session_id=session_id,
            message_id=message_id,
            tool_name=block.name,
            tool_use_id=block.id,
            tool_input=block.input,
            status="pending",  # Will be updated when result comes
            created_at=datetime.utcnow(),
        )

        self.db.add(tool_call_model)
        await self.db.flush()

        logger.info(
            f"Persisted ToolUseBlock: id={tool_call_id}",
            extra={"session_id": str(session_id), "tool_call_id": str(tool_call_id)},
        )

        # Create domain entity
        domain_tool_call = DomainToolCall(
            id=tool_call_id,
            session_id=session_id,
            tool_name=block.name,
            tool_use_id=block.id,
            tool_input=block.input,
            tool_output=None,
            status="pending",
            created_at=tool_call_model.created_at,
        )

        return domain_tool_call

    async def handle_tool_result_block(
        self, block: ToolResultBlock, session_id: UUID, message_id: UUID
    ) -> Optional[DomainToolCall]:
        """Process tool execution result.

        Args:
            block: ToolResultBlock from SDK message
            session_id: Session identifier
            message_id: Parent message identifier

        Returns:
            DomainToolCall if found and updated, None otherwise
        """
        logger.info(
            f"Processing ToolResultBlock: tool_use_id={block.tool_use_id}, is_error={block.is_error}",
            extra={
                "session_id": str(session_id),
                "tool_use_id": block.tool_use_id,
                "is_error": block.is_error,
            },
        )

        # Find corresponding tool call by tool_use_id
        from app.models.tool_call import ToolCallModel
        from sqlalchemy import select, update

        # Update tool call with result
        stmt = (
            update(ToolCallModel)
            .where(
                ToolCallModel.session_id == session_id,
                ToolCallModel.tool_use_id == block.tool_use_id,
            )
            .values(
                tool_output={"content": block.content},
                status="failed" if block.is_error else "completed",
                is_error=block.is_error,
                completed_at=datetime.utcnow(),
            )
            .returning(ToolCallModel)
        )

        result = await self.db.execute(stmt)
        updated_tool_call = result.scalar_one_or_none()

        if updated_tool_call:
            await self.db.flush()

            logger.info(
                f"Updated ToolCall with result: id={updated_tool_call.id}, status={updated_tool_call.status}",
                extra={
                    "session_id": str(session_id),
                    "tool_call_id": str(updated_tool_call.id),
                },
            )

            # Create domain entity
            domain_tool_call = DomainToolCall(
                id=updated_tool_call.id,
                session_id=session_id,
                tool_name=updated_tool_call.tool_name,
                tool_use_id=updated_tool_call.tool_use_id,
                tool_input=updated_tool_call.tool_input,
                tool_output=updated_tool_call.tool_output,
                status=updated_tool_call.status,
                created_at=updated_tool_call.created_at,
            )

            return domain_tool_call
        else:
            logger.warning(
                f"No ToolCall found for tool_use_id={block.tool_use_id}",
                extra={"session_id": str(session_id), "tool_use_id": block.tool_use_id},
            )
            return None

    async def handle_text_block(self, block: TextBlock, session_id: UUID, message_id: UUID) -> Dict[str, Any]:
        """Extract text content.

        This is a utility method for extracting text blocks separately if needed.

        Args:
            block: TextBlock from SDK message
            session_id: Session identifier
            message_id: Parent message identifier

        Returns:
            Dictionary with text content and metadata
        """
        return {
            "type": "text",
            "text": block.text,
            "length": len(block.text),
            "session_id": session_id,
            "message_id": message_id,
        }

    async def handle_thinking_block(
        self, block: ThinkingBlock, session_id: UUID, message_id: UUID
    ) -> Dict[str, Any]:
        """Extract thinking content (extended thinking).

        Args:
            block: ThinkingBlock from SDK message
            session_id: Session identifier
            message_id: Parent message identifier

        Returns:
            Dictionary with thinking content and metadata
        """
        return {
            "type": "thinking",
            "thinking": block.thinking,
            "length": len(block.thinking),
            "session_id": session_id,
            "message_id": message_id,
        }
