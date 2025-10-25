"""Task template database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import ARRAY, JSONB
from app.database.base import Base


class TaskTemplateModel(Base):
    """Task template table model."""

    __tablename__ = "task_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic Information
    name = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(Text)
    category = Column(String(100), index=True)  # kubernetes, docker, git, database, monitoring

    # Prompt Configuration
    prompt_template = Column(Text, nullable=False)
    template_variables_schema = Column(JSONB)  # JSON Schema for variables documentation

    # Tool Configuration
    tool_group_id = Column(UUID(as_uuid=True), ForeignKey("tool_groups.id", ondelete="SET NULL"), nullable=True)
    allowed_tools = Column(ARRAY(String), nullable=False, server_default='{}')
    disallowed_tools = Column(ARRAY(String), server_default='{}')

    # SDK Configuration
    sdk_options = Column(JSONB, server_default='{}')

    # Post-Execution Defaults
    generate_report = Column(Boolean, default=False)
    report_format = Column(String(50))  # 'json', 'markdown', 'html', 'pdf'

    # Metadata
    tags = Column(ARRAY(String), server_default='{}')
    is_public = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    icon = Column(String(50))  # Icon name for UI

    # Usage Statistics
    usage_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_task_templates_category", "category", "is_active"),
        Index("idx_task_templates_tags", "tags", postgresql_using="gin"),
        Index("idx_task_templates_usage", "usage_count", postgresql_where="is_active = true"),
    )
