"""Session metrics snapshot database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class SessionMetricsSnapshotModel(Base):
    """Session metrics snapshot table model.

    Captures point-in-time metrics for a session, useful for tracking
    session progress over time and generating reports.
    """

    __tablename__ = "session_metrics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Snapshot Type
    snapshot_type = Column(String(50), nullable=False)  # 'hourly', 'checkpoint', 'final'

    # Message Metrics
    total_messages = Column(Integer, default=0)
    total_tool_calls = Column(Integer, default=0)

    # Advanced Metrics
    total_hook_executions = Column(Integer, default=0)
    total_permission_checks = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_retries = Column(Integer, default=0)

    # Token Usage
    api_input_tokens = Column(Integer, default=0)
    api_output_tokens = Column(Integer, default=0)
    api_cache_creation_tokens = Column(Integer, default=0)
    api_cache_read_tokens = Column(Integer, default=0)

    # Cost Metrics
    total_cost_usd = Column(Numeric(10, 6), default=0)

    # Duration
    duration_ms = Column(BigInteger)

    # Additional Metrics
    metrics_data = Column(JSONB, default={})  # Flexible field for additional metrics

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    # session relationship removed (SessionModel being phased out)
    # Session references available via session_id foreign key

    # Indexes for common queries
    __table_args__ = (
        Index("idx_metrics_snapshots_session", "session_id", "created_at"),
        Index("idx_metrics_snapshots_type", "snapshot_type", "created_at"),
        Index("idx_metrics_snapshots_session_type", "session_id", "snapshot_type", "created_at"),
    )
