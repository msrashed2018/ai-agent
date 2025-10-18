"""Task database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import ARRAY
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class TaskModel(Base):
    """Task table model."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Prompt Configuration
    prompt_template = Column(Text, nullable=False)
    default_variables = Column(JSONB)
    
    # Allowed Tools
    allowed_tools = Column(ARRAY(String), nullable=False, server_default='{}')
    disallowed_tools = Column(ARRAY(String), server_default='{}')
    
    # Session Configuration
    sdk_options = Column(JSONB, server_default='{}')
    working_directory_path = Column(String(1000))
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_cron = Column(String(100))
    schedule_enabled = Column(Boolean, default=False)
    
    # Post-Execution Actions
    generate_report = Column(Boolean, default=False)
    report_format = Column(String(50))  # 'json', 'markdown', 'html', 'pdf'
    
    # Notifications
    notification_config = Column(JSONB)
    
    # Metadata
    tags = Column(ARRAY(String))
    is_public = Column(Boolean, default=False)  # If true, visible to all org users
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("UserModel", back_populates="tasks")
    task_executions = relationship("TaskExecutionModel", back_populates="task", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        CheckConstraint("report_format IN ('json', 'markdown', 'html', 'pdf') OR report_format IS NULL", name="chk_report_format"),
        Index("idx_tasks_user", "user_id", "is_deleted"),
        Index("idx_tasks_scheduled", "is_scheduled", "schedule_enabled", postgresql_where="is_deleted = false"),
        Index("idx_tasks_tags", "tags", postgresql_using="gin"),
        Index("idx_tasks_name", "name", postgresql_ops={"name": "varchar_pattern_ops"}),
    )


# Alias for backward compatibility  
Task = TaskModel
