"""Result handler for processing ResultMessage from Claude SDK."""
import logging
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from claude_agent_sdk import ResultMessage

from app.claude_sdk.core.config import ClientMetrics
from app.repositories.session_repository import SessionRepository
from app.repositories.session_metrics_snapshot_repository import SessionMetricsSnapshotRepository

logger = logging.getLogger(__name__)


class ResultHandler:
    """Process ResultMessage and finalize session metrics.

    This handler:
    - Extracts final metrics from ResultMessage
    - Updates session with final statistics
    - Creates metrics snapshot for historical tracking
    - Persists cost and token usage data

    Example:
        >>> handler = ResultHandler(db, session_repo, metrics_repo)
        >>> metrics = await handler.handle_result_message(result_message, session_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        metrics_repo: SessionMetricsSnapshotRepository,
    ):
        """Initialize result handler with repositories.

        Args:
            db: Async database session
            session_repo: Repository for session updates
            metrics_repo: Repository for metrics snapshots
        """
        self.db = db
        self.session_repo = session_repo
        self.metrics_repo = metrics_repo

    async def handle_result_message(
        self, message: ResultMessage, session_id: UUID
    ) -> ClientMetrics:
        """Process final result and persist metrics.

        Args:
            message: ResultMessage from Claude SDK
            session_id: Session identifier

        Returns:
            ClientMetrics: Final session metrics

        Raises:
            Exception: If persistence fails
        """
        logger.info(
            f"Processing ResultMessage: duration={message.duration_ms}ms, cost=${message.total_cost_usd}, turns={message.num_turns}",
            extra={
                "session_id": str(session_id),
                "duration_ms": message.duration_ms,
                "cost_usd": message.total_cost_usd,
                "num_turns": message.num_turns,
            },
        )

        # Create metrics object
        metrics = ClientMetrics(
            session_id=session_id,
            total_duration_ms=message.duration_ms,
            total_cost_usd=Decimal(str(message.total_cost_usd)) if message.total_cost_usd else Decimal("0.0"),
        )

        # Extract token usage if available
        if hasattr(message, "api_usage") and message.api_usage:
            usage = message.api_usage
            metrics.total_input_tokens = usage.get("input_tokens", 0)
            metrics.total_output_tokens = usage.get("output_tokens", 0)
            metrics.total_cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
            metrics.total_cache_read_tokens = usage.get("cache_read_input_tokens", 0)

        # Mark as completed
        metrics.mark_completed()

        # Update session in database
        from app.models.session import SessionModel
        from sqlalchemy import update

        update_stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                status="completed",
                duration_ms=message.duration_ms,
                total_cost_usd=float(metrics.total_cost_usd),
                api_input_tokens=metrics.total_input_tokens,
                api_output_tokens=metrics.total_output_tokens,
                api_cache_creation_tokens=metrics.total_cache_creation_tokens,
                api_cache_read_tokens=metrics.total_cache_read_tokens,
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(update_stmt)
        await self.db.flush()

        logger.info(
            f"Updated session with final metrics",
            extra={"session_id": str(session_id), "metrics": metrics.to_dict()},
        )

        # Create metrics snapshot
        await self.create_metrics_snapshot(session_id, metrics)

        return metrics

    async def create_metrics_snapshot(
        self, session_id: UUID, metrics: ClientMetrics
    ) -> None:
        """Save metrics snapshot for historical tracking.

        Args:
            session_id: Session identifier
            metrics: Session metrics to snapshot
        """
        logger.info(
            f"Creating metrics snapshot for session {session_id}",
            extra={"session_id": str(session_id)},
        )

        # Create snapshot in database
        from app.models.session_metrics_snapshot import SessionMetricsSnapshotModel

        snapshot = SessionMetricsSnapshotModel(
            session_id=session_id,
            snapshot_time=datetime.utcnow(),
            total_messages=metrics.total_messages,
            total_tool_calls=metrics.total_tool_calls,
            total_errors=metrics.total_errors,
            total_retries=metrics.total_retries,
            total_cost_usd=float(metrics.total_cost_usd),
            api_input_tokens=metrics.total_input_tokens,
            api_output_tokens=metrics.total_output_tokens,
            api_cache_creation_tokens=metrics.total_cache_creation_tokens,
            api_cache_read_tokens=metrics.total_cache_read_tokens,
            duration_ms=metrics.total_duration_ms,
        )

        self.db.add(snapshot)
        await self.db.flush()

        logger.info(
            f"Metrics snapshot created",
            extra={"session_id": str(session_id), "snapshot_id": str(snapshot.id)},
        )
