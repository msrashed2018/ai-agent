"""Metrics collector for session performance tracking."""

from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class SessionMetrics:
    """Session metrics snapshot."""
    session_id: UUID
    total_messages: int
    total_tool_calls: int
    total_errors: int
    total_retries: int
    total_cost_usd: Decimal
    total_input_tokens: int
    total_output_tokens: int
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_duration_ms: int
    average_latency_ms: Optional[int]
    created_at: datetime


class MetricsCollector:
    """Collect runtime metrics for observability."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._session_metrics: Dict[UUID, SessionMetrics] = {}

    async def record_query_duration(
        self,
        session_id: UUID,
        duration_ms: int
    ) -> None:
        """Record query execution time."""
        logger.info(
            f"Query duration recorded for session {session_id}: {duration_ms}ms",
            extra={"session_id": str(session_id), "duration_ms": duration_ms}
        )

    async def record_tool_execution(
        self,
        session_id: UUID,
        tool_name: str,
        duration_ms: int,
        success: bool
    ) -> None:
        """Record tool execution metrics."""
        logger.info(
            f"Tool execution recorded: {tool_name}",
            extra={
                "session_id": str(session_id),
                "tool_name": tool_name,
                "duration_ms": duration_ms,
                "success": success
            }
        )

    async def record_api_cost(
        self,
        session_id: UUID,
        cost_usd: Decimal,
        tokens: TokenUsage
    ) -> None:
        """Record API usage cost."""
        logger.info(
            f"API cost recorded for session {session_id}: ${cost_usd}",
            extra={
                "session_id": str(session_id),
                "cost_usd": float(cost_usd),
                "input_tokens": tokens.input_tokens,
                "output_tokens": tokens.output_tokens
            }
        )

    async def create_snapshot(
        self,
        session_id: UUID
    ) -> None:
        """Create metrics snapshot for historical tracking."""
        from app.repositories.session_metrics_snapshot_repository import (
            SessionMetricsSnapshotRepository
        )

        metrics_repo = SessionMetricsSnapshotRepository(self.db)

        try:
            # Get session data
            from app.repositories.session_repository import SessionRepository
            session_repo = SessionRepository(self.db)
            session = await session_repo.get_by_id(str(session_id))

            if not session:
                logger.warning(f"Session {session_id} not found for metrics snapshot")
                return

            # Create snapshot
            snapshot = await metrics_repo.create(
                session_id=session_id,
                total_messages=session.total_messages,
                total_tool_calls=session.total_tool_calls,
                total_errors=session.total_errors or 0,
                total_retries=session.total_retries or 0,
                total_cost_usd=session.total_cost_usd,
                total_input_tokens=session.api_input_tokens or 0,
                total_output_tokens=session.api_output_tokens or 0,
                total_cache_creation_tokens=session.api_cache_creation_tokens or 0,
                total_cache_read_tokens=session.api_cache_read_tokens or 0,
                total_duration_ms=session.duration_ms or 0,
            )

            logger.info(
                f"Metrics snapshot created for session {session_id}",
                extra={"session_id": str(session_id), "snapshot_id": str(snapshot.id)}
            )
        except Exception as e:
            logger.error(
                f"Failed to create metrics snapshot for session {session_id}: {e}",
                exc_info=True
            )

    async def get_session_metrics(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current session metrics."""
        from app.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(self.db)
        session = await session_repo.get_by_id(str(session_id))

        if not session:
            return None

        return {
            "session_id": str(session.id),
            "total_messages": session.total_messages,
            "total_tool_calls": session.total_tool_calls,
            "total_errors": session.total_errors or 0,
            "total_retries": session.total_retries or 0,
            "total_cost_usd": float(session.total_cost_usd) if session.total_cost_usd else 0.0,
            "total_input_tokens": session.api_input_tokens or 0,
            "total_output_tokens": session.api_output_tokens or 0,
            "total_cache_creation_tokens": session.api_cache_creation_tokens or 0,
            "total_cache_read_tokens": session.api_cache_read_tokens or 0,
            "total_duration_ms": session.duration_ms or 0,
        }
