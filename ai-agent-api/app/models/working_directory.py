"""Working directory database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, BigInteger, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class WorkingDirectoryModel(Base):
    """Working directory table model."""
    
    __tablename__ = "working_directories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Paths
    directory_path = Column(Text, nullable=False)
    archive_path = Column(Text)  # Path to tar.gz archive after session ends
    
    # Stats
    total_files = Column(Integer, default=0)
    total_size_bytes = Column(BigInteger, default=0)
    
    # Archive Status
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True))
    
    # Metadata
    file_manifest = Column(JSONB)
    # List of files created/modified: [{"path": "...", "size": ..., "modified_at": "..."}]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("SessionModel", back_populates="working_directory", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_working_dirs_session", "session_id"),
        Index("idx_working_dirs_archived", "is_archived"),
    )
