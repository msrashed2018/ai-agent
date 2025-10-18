"""MCP server database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class MCPServerModel(Base):
    """MCP server table model."""
    
    __tablename__ = "mcp_servers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    # If NULL, server is global/system-level
    
    # Identity
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Server Type
    server_type = Column(String(50), nullable=False)  # 'stdio', 'sse', 'http', 'sdk'
    
    # Configuration
    config = Column(JSONB, nullable=False)
    
    # Availability
    is_enabled = Column(Boolean, default=True)
    is_global = Column(Boolean, default=False)  # If true, available to all users in org
    
    # Health
    last_health_check_at = Column(DateTime(timezone=True))
    health_status = Column(String(50))  # 'healthy', 'degraded', 'unhealthy', 'unknown'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("UserModel", back_populates="mcp_servers")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("server_type IN ('stdio', 'sse', 'http', 'sdk')", name="chk_server_type"),
        CheckConstraint("health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown') OR health_status IS NULL", name="chk_health_status"),
        UniqueConstraint("name", "user_id", name="uq_server_name_user"),
        Index("idx_mcp_servers_user", "user_id", postgresql_where="deleted_at IS NULL"),
        Index("idx_mcp_servers_enabled", "is_enabled", postgresql_where="deleted_at IS NULL"),
        Index("idx_mcp_servers_global", "is_global", postgresql_where="is_global = true"),
    )
