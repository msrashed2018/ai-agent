"""Session database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, ForeignKey, DateTime, Text, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class SessionModel(Base):
    """Session table model."""
    
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identity
    name = Column(String(255))
    description = Column(Text)
    
    # Session Type
    mode = Column(String(50), nullable=False)  # 'interactive', 'non_interactive', 'forked'

    # State Management
    status = Column(String(50), nullable=False, default="created", index=True)
    # Status values: created, connecting, active, paused, waiting, processing, completed, failed, terminated, archived

    # Claude SDK Configuration
    sdk_options = Column(JSONB, nullable=False, default={})

    # Advanced SDK Options (Phase 1 - New)
    include_partial_messages = Column(Boolean, default=False)
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Numeric(10, 2), default=2.0)
    timeout_seconds = Column(Integer, default=120)
    hooks_enabled = Column(JSONB, default=[])
    permission_mode = Column(String(50), default="default")
    custom_policies = Column(JSONB, default=[])
    
    # Working Directory
    working_directory_path = Column(Text)
    
    # Session Relationships
    parent_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
    is_fork = Column(Boolean, default=False)
    
    # Metrics & Cost
    total_messages = Column(Integer, default=0)
    total_tool_calls = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    duration_ms = Column(BigInteger)

    # Advanced Metrics (Phase 1 - New)
    total_hook_executions = Column(Integer, default=0)
    total_permission_checks = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_retries = Column(Integer, default=0)
    
    # API Usage
    api_input_tokens = Column(Integer, default=0)
    api_output_tokens = Column(Integer, default=0)
    api_cache_creation_tokens = Column(Integer, default=0)
    api_cache_read_tokens = Column(Integer, default=0)
    
    # Result
    result_data = Column(JSONB)
    error_message = Column(Text)

    # References (Phase 1 - New)
    archive_id = Column(UUID(as_uuid=True), ForeignKey("working_directory_archives.id"), index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("session_templates.id"), index=True)

    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCallModel", back_populates="session", cascade="all, delete-orphan")
    task_executions = relationship("TaskExecutionModel", back_populates="session")
    reports = relationship("ReportModel", back_populates="session")
    working_directory = relationship("WorkingDirectoryModel", back_populates="session", uselist=False)
    audit_logs = relationship("AuditLogModel", back_populates="session")

    # Phase 1 - New Relationships
    hook_executions = relationship("HookExecutionModel", back_populates="session", cascade="all, delete-orphan")
    permission_decisions = relationship("PermissionDecisionModel", back_populates="session", cascade="all, delete-orphan")
    archive = relationship("WorkingDirectoryArchiveModel", foreign_keys=[archive_id], back_populates="session", uselist=False)
    template = relationship("SessionTemplateModel", foreign_keys=[template_id], back_populates="sessions")
    metrics_snapshots = relationship("SessionMetricsSnapshotModel", back_populates="session", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("mode IN ('interactive', 'non_interactive', 'forked')", name="chk_mode"),
        CheckConstraint(
            "status IN ('created', 'connecting', 'active', 'paused', 'waiting', 'processing', 'completed', 'failed', 'terminated', 'archived')",
            name="chk_status"
        ),
    )


# Alias for backward compatibility
Session = SessionModel
