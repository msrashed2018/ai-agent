"""Audit log database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB, INET
from sqlalchemy.orm import relationship
from app.database.base import Base


class AuditLogModel(Base):
    """Audit log table model."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
    
    # Action
    action_type = Column(String(100), nullable=False)
    # Examples: 'session.created', 'tool.executed', 'permission.denied', 'api.request'
    
    resource_type = Column(String(50))  # 'session', 'task', 'report', 'tool', etc.
    resource_id = Column(UUID(as_uuid=True))
    
    # Details
    action_details = Column(JSONB)
    # Full context of the action
    
    # Request Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_id = Column(String(255))
    
    # Result
    status = Column(String(50))  # 'success', 'failure', 'denied'
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("UserModel")
    # session relationship removed (SessionModel being phased out)
    # Session references available via session_id foreign key
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failure', 'denied') OR status IS NULL", name="chk_audit_status"),
        Index("idx_audit_logs_user", "user_id", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_audit_logs_session", "session_id", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_audit_logs_action", "action_type", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_audit_logs_details", "action_details", postgresql_using="gin"),
    )
