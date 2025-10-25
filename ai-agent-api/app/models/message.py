"""Message database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, CheckConstraint, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class MessageModel(Base):
    """Message table model."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Message Type
    message_type = Column(String(50), nullable=False)  # 'user', 'assistant', 'system', 'result'
    
    # Message Content
    content = Column(JSONB, nullable=False)
    
    # Metadata
    model = Column(String(100))  # AI model used (for assistant messages)
    parent_tool_use_id = Column(String(255))

    # Phase 1 - Streaming Support
    is_partial = Column(Boolean, default=False)  # For streaming partial messages
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
    thinking_content = Column(Text)  # Claude's thinking/reasoning content

    # Sequence
    sequence_number = Column(Integer, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    # session relationship removed (SessionModel being phased out)
    # Messages can still reference sessions via session_id foreign key
    
    # Constraints
    __table_args__ = (
        CheckConstraint("message_type IN ('user', 'assistant', 'system', 'result')", name="chk_message_type"),
        Index("idx_messages_session", "session_id", "sequence_number"),
        Index("idx_messages_content", "content", postgresql_using="gin"),
        Index("idx_messages_result", "session_id", postgresql_where="message_type = 'result'"),
    )
