"""Hook database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class HookModel(Base):
    """Hook table model."""
    
    __tablename__ = "hooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Identity
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Hook Configuration
    hook_event = Column(String(50), nullable=False)
    # Values: 'PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop', 'SubagentStop', 'PreCompact'
    
    matcher = Column(String(255))  # Tool name pattern (e.g., "Bash", "Write|Edit")
    
    # Hook Implementation
    implementation_type = Column(String(50), nullable=False)  # 'webhook', 'script', 'builtin'
    
    implementation_config = Column(JSONB, nullable=False)
    
    # Execution
    is_enabled = Column(Boolean, default=True)
    execution_timeout_ms = Column(Integer, default=5000)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("UserModel", back_populates="hooks")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("hook_event IN ('PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'Stop', 'SubagentStop', 'PreCompact')", name="chk_hook_event"),
        CheckConstraint("implementation_type IN ('webhook', 'script', 'builtin')", name="chk_implementation_type"),
        Index("idx_hooks_user", "user_id", postgresql_where="deleted_at IS NULL"),
        Index("idx_hooks_event", "hook_event", "is_enabled"),
    )
