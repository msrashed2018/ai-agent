"""Working directory archive database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, BigInteger, ForeignKey, DateTime, Index, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class WorkingDirectoryArchiveModel(Base):
    """Working directory archive table model."""

    __tablename__ = "working_directory_archives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Archive Location
    archive_path = Column(Text, nullable=False)  # S3 path or filesystem path
    storage_backend = Column(String(50), nullable=False)  # 's3', 'filesystem'

    # Archive Format
    compression_type = Column(String(50), nullable=False)  # 'zip', 'tar.gz', 'tar.bz2'

    # Size Metrics
    size_bytes = Column(BigInteger, nullable=False)

    # Status
    status = Column(String(50), nullable=False, default="pending", index=True)  # 'pending', 'in_progress', 'completed', 'failed'

    # Error Handling
    error_message = Column(Text)

    # Additional Metadata
    archive_metadata = Column(JSONB, default={})  # File counts, directory structure summary, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    session = relationship("SessionModel", foreign_keys=[session_id], back_populates="archive")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed')", name="chk_archive_status"),
        CheckConstraint("storage_backend IN ('s3', 'filesystem')", name="chk_storage_backend"),
        CheckConstraint("size_bytes >= 0", name="chk_size_bytes"),
        Index("idx_archives_status", "status", "created_at"),
        Index("idx_archives_backend", "storage_backend", "status"),
    )
