"""Report database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, BigInteger, Boolean, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import ARRAY
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class ReportModel(Base):
    """Report table model."""
    
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    task_execution_id = Column(UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="SET NULL"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Identity
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Report Type
    report_type = Column(String(50), default='auto_generated')  # 'auto_generated', 'custom', 'template'
    
    # Content
    content = Column(JSONB, nullable=False)
    
    # File Outputs
    file_path = Column(Text)
    file_format = Column(String(50))  # 'json', 'markdown', 'html', 'pdf'
    file_size_bytes = Column(BigInteger)
    
    # Metadata
    template_name = Column(String(255))
    tags = Column(ARRAY(String))
    
    # Visibility
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    session = relationship("SessionModel", back_populates="reports")
    task_execution = relationship("TaskExecutionModel", foreign_keys=[task_execution_id], back_populates="report")
    user = relationship("UserModel", back_populates="reports")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("report_type IN ('auto_generated', 'custom', 'template')", name="chk_report_type"),
        CheckConstraint("file_format IN ('json', 'markdown', 'html', 'pdf') OR file_format IS NULL", name="chk_file_format"),
        Index("idx_reports_session", "session_id"),
        Index("idx_reports_user", "user_id"),
        Index("idx_reports_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_reports_tags", "tags", postgresql_using="gin"),
        Index("idx_reports_content", "content", postgresql_using="gin"),
    )
