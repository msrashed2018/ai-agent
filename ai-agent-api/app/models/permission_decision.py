"""Permission decision database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, DateTime, Index, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class PermissionDecisionModel(Base):
    """Permission decision table model."""

    __tablename__ = "permission_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_call_id = Column(UUID(as_uuid=True), ForeignKey("tool_calls.id", ondelete="SET NULL"))

    # Tool Identity
    tool_use_id = Column(String(255), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False, index=True)

    # Permission Context
    input_data = Column(JSONB, nullable=False)
    context_data = Column(JSONB, default={})

    # Decision
    decision = Column(String(50), nullable=False, index=True)  # 'allowed', 'denied', 'bypassed'
    reason = Column(Text, nullable=False)
    policy_applied = Column(String(255))  # Name of policy that made the decision

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("SessionModel", back_populates="permission_decisions")
    tool_call = relationship("ToolCallModel")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("decision IN ('allowed', 'denied', 'bypassed')", name="chk_permission_decision"),
        Index("idx_permission_decisions_session", "session_id", "created_at"),
        Index("idx_permission_decisions_decision", "decision", "created_at"),
        Index("idx_permission_decisions_tool", "tool_use_id", "decision"),
        Index("idx_permission_decisions_tool_name", "tool_name", "decision"),
        Index("idx_permission_decisions_input", "input_data", postgresql_using="gin"),
    )
