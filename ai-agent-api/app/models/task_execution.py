"""Task execution database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class TaskExecutionModel(Base):
    """Task execution table model."""
    
    __tablename__ = "task_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL", use_alter=True, name="fk_task_executions_report_id_reports"))
    
    # Execution Context
    trigger_type = Column(String(50), nullable=False)  # 'manual', 'scheduled', 'webhook', 'api'
    trigger_metadata = Column(JSONB)
    
    # Execution Parameters
    prompt_variables = Column(JSONB)
    # Variables injected into prompt template
    
    # Status
    status = Column(String(50), nullable=False, default='pending', index=True)  # 'pending', 'queued', 'running', 'completed', 'failed', 'cancelled'
    error_message = Column(String)
    
    # Results
    result_data = Column(JSONB)
    
    # Metrics
    total_messages = Column(Integer, default=0)
    total_tool_calls = Column(Integer, default=0)
    duration_seconds = Column(Integer)

    # Celery Integration Fields
    celery_task_id = Column(String(255), index=True)  # Celery task ID for async execution
    worker_hostname = Column(String(255))  # Worker that processed the task
    retry_count = Column(Integer, default=0)  # Number of retry attempts

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    queued_at = Column(DateTime(timezone=True))  # When queued to Celery
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    task = relationship("TaskModel", back_populates="task_executions")
    session = relationship("SessionModel", back_populates="task_executions")
    report = relationship("ReportModel", foreign_keys="[ReportModel.task_execution_id]", back_populates="task_execution")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("trigger_type IN ('manual', 'scheduled', 'webhook', 'api')", name="chk_trigger_type"),
        CheckConstraint("status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')", name="chk_task_execution_status"),
        Index("idx_task_executions_task", "task_id", "created_at"),
        Index("idx_task_executions_session", "session_id"),
        Index("idx_task_executions_status", "status", "created_at"),
        Index("idx_task_executions_trigger", "trigger_type"),
        Index("idx_task_executions_celery_task", "celery_task_id"),  # For lookup by Celery task ID
    )
