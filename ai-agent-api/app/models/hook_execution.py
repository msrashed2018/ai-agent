"""Hook execution database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class HookExecutionModel(Base):
    """Hook execution table model."""

    __tablename__ = "hook_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_call_id = Column(UUID(as_uuid=True), ForeignKey("tool_calls.id", ondelete="SET NULL"))

    # Hook Identity
    hook_name = Column(String(100), nullable=False, index=True)  # pre_tool_use, post_tool_use, etc.
    tool_use_id = Column(String(255), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False)

    # Hook Data
    input_data = Column(JSONB, nullable=False)
    output_data = Column(JSONB, nullable=False)
    context_data = Column(JSONB, default={})

    # Execution Metrics
    execution_time_ms = Column(Integer, nullable=False)

    # Error Handling
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("SessionModel", back_populates="hook_executions")
    tool_call = relationship("ToolCallModel")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_hook_executions_session", "session_id", "created_at"),
        Index("idx_hook_executions_hook_name", "hook_name", "created_at"),
        Index("idx_hook_executions_tool", "tool_use_id", "hook_name"),
        Index("idx_hook_executions_input", "input_data", postgresql_using="gin"),
        Index("idx_hook_executions_output", "output_data", postgresql_using="gin"),
    )
