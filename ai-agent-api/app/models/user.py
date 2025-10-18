"""User and Organization database models."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


class OrganizationModel(Base):
    """Organization table model."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Contact
    primary_email = Column(String(255))
    primary_contact_name = Column(String(255))
    
    # Subscription
    plan = Column(String(50), nullable=False, default="free")
    
    # Quotas
    max_users = Column(Integer, default=10)
    max_sessions_per_month = Column(Integer, default=1000)
    max_storage_gb = Column(Integer, default=100)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    users = relationship("UserModel", back_populates="organization")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("plan IN ('free', 'pro', 'enterprise')", name="chk_plan"),
    )


class UserModel(Base):
    """User table model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    avatar_url = Column(String)
    
    # Authorization
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    
    # Quotas & Limits
    max_concurrent_sessions = Column(Integer, default=5)
    max_api_calls_per_hour = Column(Integer, default=1000)
    max_storage_mb = Column(Integer, default=10240)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("OrganizationModel", back_populates="users")
    sessions = relationship("SessionModel", back_populates="user")
    tasks = relationship("TaskModel", back_populates="user")
    reports = relationship("ReportModel", back_populates="user")
    mcp_servers = relationship("MCPServerModel", back_populates="user")
    hooks = relationship("HookModel", back_populates="user")
    session_templates = relationship("SessionTemplateModel", back_populates="user")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user', 'viewer')", name="chk_role"),
        CheckConstraint(
            "max_concurrent_sessions > 0 AND max_api_calls_per_hour > 0 AND max_storage_mb > 0",
            name="chk_positive_quotas"
        ),
    )


# Aliases for backward compatibility
User = UserModel
Organization = OrganizationModel
