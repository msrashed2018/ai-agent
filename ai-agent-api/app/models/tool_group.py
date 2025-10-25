"""Tool Group database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import ARRAY
from sqlalchemy.orm import relationship
from app.database.base import Base


class ToolGroupModel(Base):
    """Tool group table model."""

    __tablename__ = "tool_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Tool Lists
    allowed_tools = Column(ARRAY(String), nullable=False, server_default='{}')
    disallowed_tools = Column(ARRAY(String), server_default='{}')

    # Metadata
    is_public = Column(Boolean, default=False)  # If true, visible to all org users
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("UserModel", back_populates="tool_groups")
    tasks = relationship("TaskModel", back_populates="tool_group")

    # Indexes
    __table_args__ = (
        Index("idx_tool_groups_user", "user_id", "is_deleted"),
        Index("idx_tool_groups_name", "name", postgresql_ops={"name": "varchar_pattern_ops"}),
    )


# Alias for backward compatibility
ToolGroup = ToolGroupModel
