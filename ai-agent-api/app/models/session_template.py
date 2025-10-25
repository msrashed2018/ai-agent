"""Session template database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, JSONB, ARRAY


class SessionTemplateModel(Base):
    """Session template table model."""

    __tablename__ = "session_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Template Identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100))  # 'development', 'security', 'production', 'debugging', 'custom'

    # Template Configuration
    system_prompt = Column(Text)
    working_directory = Column(String(500))
    allowed_tools = Column(ARRAY(String))
    sdk_options = Column(JSONB, default={})

    # MCP Server Configuration
    mcp_server_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])  # References to mcp_servers

    # Sharing and Access
    is_public = Column(Boolean, default=False)  # Public templates available to all users
    is_organization_shared = Column(Boolean, default=False)  # Shared within organization

    # Versioning
    version = Column(String(50), default="1.0.0")

    # Metadata
    tags = Column(ARRAY(String), default=[])
    template_metadata = Column(JSONB, default={})

    # Usage Statistics
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("UserModel", back_populates="session_templates")
    # sessions relationship removed (SessionModel being phased out)

    # Constraints
    __table_args__ = (
        CheckConstraint("category IN ('development', 'security', 'production', 'debugging', 'performance', 'custom') OR category IS NULL", name="chk_template_category"),
        Index("idx_templates_user", "user_id", postgresql_where="deleted_at IS NULL"),
        Index("idx_templates_public", "is_public", postgresql_where="is_public = true AND deleted_at IS NULL"),
        Index("idx_templates_category", "category", postgresql_where="deleted_at IS NULL"),
        Index("idx_templates_tags", "tags", postgresql_using="gin"),
        Index("idx_templates_name", "name", postgresql_ops={"name": "varchar_pattern_ops"}),
    )
