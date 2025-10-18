"""Tool call database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class ToolCallModel(Base):
    """Tool call table model."""
    
    __tablename__ = "tool_calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    
    # Tool Identity
    tool_name = Column(String(255), nullable=False, index=True)
    tool_use_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Tool Invocation
    tool_input = Column(JSONB, nullable=False)
    tool_output = Column(JSONB)
    
    # Execution Status
    status = Column(String(50), nullable=False, default='pending', index=True)  # 'pending', 'running', 'success', 'error', 'denied'
    is_error = Column(Boolean, default=False)
    error_message = Column(String)
    
    # Permission
    permission_decision = Column(String(50))  # 'allow', 'deny', 'ask'
    permission_reason = Column(String)
    
    # Execution Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("SessionModel", back_populates="tool_calls")
    message = relationship("MessageModel")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'running', 'success', 'error', 'denied')", name="chk_tool_call_status"),
        CheckConstraint("permission_decision IN ('allow', 'deny', 'ask') OR permission_decision IS NULL", name="chk_permission_decision"),
        Index("idx_tool_calls_session", "session_id", "created_at"),
        Index("idx_tool_calls_status", "status", "created_at"),
        Index("idx_tool_calls_tool_name", "tool_name", "created_at"),
        Index("idx_tool_calls_permission", "permission_decision", postgresql_where="permission_decision IS NOT NULL"),
        Index("idx_tool_calls_input", "tool_input", postgresql_using="gin"),
        Index("idx_tool_calls_output", "tool_output", postgresql_using="gin"),
    )
