"""Message value objects."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class MessageType(str, Enum):
    """Message type enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    RESULT = "result"


@dataclass(frozen=True)
class Message:
    """Immutable message value object."""
    id: UUID
    session_id: UUID
    message_type: MessageType
    content: Dict[str, Any]  # JSONB stored format
    sequence_number: int
    created_at: datetime
    model: Optional[str] = None
    parent_tool_use_id: Optional[str] = None

    @classmethod
    def from_user_text(cls, session_id: UUID, text: str, sequence: int) -> "Message":
        """Factory method for user text message."""
        return cls(
            id=uuid4(),
            session_id=session_id,
            message_type=MessageType.USER,
            content={"content": text},
            sequence_number=sequence,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def from_assistant(
        cls,
        session_id: UUID,
        content: Dict[str, Any],
        sequence: int,
        model: Optional[str] = None,
    ) -> "Message":
        """Factory method for assistant message."""
        return cls(
            id=uuid4(),
            session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=content,
            sequence_number=sequence,
            model=model,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def from_system(
        cls,
        session_id: UUID,
        content: Dict[str, Any],
        sequence: int,
    ) -> "Message":
        """Factory method for system message."""
        return cls(
            id=uuid4(),
            session_id=session_id,
            message_type=MessageType.SYSTEM,
            content=content,
            sequence_number=sequence,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def from_result(
        cls,
        session_id: UUID,
        content: Dict[str, Any],
        sequence: int,
    ) -> "Message":
        """Factory method for result message."""
        return cls(
            id=uuid4(),
            session_id=session_id,
            message_type=MessageType.RESULT,
            content=content,
            sequence_number=sequence,
            created_at=datetime.utcnow(),
        )

    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.message_type == MessageType.USER

    def is_assistant_message(self) -> bool:
        """Check if message is from assistant."""
        return self.message_type == MessageType.ASSISTANT

    def is_system_message(self) -> bool:
        """Check if message is system message."""
        return self.message_type == MessageType.SYSTEM

    def is_result_message(self) -> bool:
        """Check if message is result message."""
        return self.message_type == MessageType.RESULT

    def get_text_content(self) -> Optional[str]:
        """Extract text content if available."""
        if isinstance(self.content.get("content"), str):
            return self.content["content"]
        return None
