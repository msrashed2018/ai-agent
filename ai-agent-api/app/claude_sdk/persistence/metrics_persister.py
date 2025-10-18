"""Metrics persister for creating performance and cost snapshots."""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.session_metrics_snapshot_repository import SessionMetricsSnapshotRepository
from app.models.session_metrics_snapshot import SessionMetricsSnapshotModel

logger = logging.getLogger(__name__)


class MetricsPersister:
    """Persist metrics snapshots at checkpoints during session execution.

    Creates point-in-time snapshots of session metrics for historical
    tracking and analysis.
    """

    def __init__(
        self,
        db: AsyncSession,
        metrics_snapshot_repo: SessionMetricsSnapshotRepository
    ):
        """Initialize metrics persister.

        Args:
            db: Database session
            metrics_snapshot_repo: Metrics snapshot repository
        """
        self.db = db
        self.metrics_snapshot_repo = metrics_snapshot_repo

    async def create_snapshot(
        self,
        session_id: UUID,
        snapshot_reason: str,
        api_input_tokens: int = 0,
        api_output_tokens: int = 0,
        total_cost_usd: float = 0.0,
        tool_call_count: int = 0,
        message_count: int = 0,
        hook_execution_count: int = 0,
        permission_check_count: int = 0,
        duration_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionMetricsSnapshotModel:
        """Create a metrics snapshot.

        Args:
            session_id: Session ID
            snapshot_reason: Reason for snapshot (e.g., "query_complete", "checkpoint")
            api_input_tokens: API input tokens so far
            api_output_tokens: API output tokens so far
            total_cost_usd: Total API cost so far
            tool_call_count: Number of tool calls
            message_count: Number of messages
            hook_execution_count: Number of hook executions
            permission_check_count: Number of permission checks
            duration_ms: Duration since session start
            metadata: Optional additional metadata

        Returns:
            Created snapshot model
        """
        try:
            snapshot = SessionMetricsSnapshotModel(
                session_id=session_id,
                snapshot_reason=snapshot_reason,
                api_input_tokens=api_input_tokens,
                api_output_tokens=api_output_tokens,
                total_cost_usd=total_cost_usd,
                tool_call_count=tool_call_count,
                message_count=message_count,
                hook_execution_count=hook_execution_count,
                permission_check_count=permission_check_count,
                duration_ms=duration_ms,
                metadata=metadata or {}
            )

            created = await self.metrics_snapshot_repo.create(snapshot)

            logger.info(
                f"Created metrics snapshot: reason={snapshot_reason}, "
                f"cost=${total_cost_usd:.4f}, tools={tool_call_count}",
                extra={"session_id": str(session_id)}
            )

            return created

        except Exception as e:
            logger.error(
                f"Failed to create metrics snapshot: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            raise

    async def create_checkpoint_snapshot(
        self,
        session_id: UUID,
        checkpoint_name: str,
        current_metrics: Dict[str, Any]
    ) -> Optional[SessionMetricsSnapshotModel]:
        """Create a snapshot at a checkpoint.

        Args:
            session_id: Session ID
            checkpoint_name: Name of checkpoint
            current_metrics: Current metrics dictionary

        Returns:
            Created snapshot or None if failed
        """
        try:
            return await self.create_snapshot(
                session_id=session_id,
                snapshot_reason=f"checkpoint_{checkpoint_name}",
                api_input_tokens=current_metrics.get("api_input_tokens", 0),
                api_output_tokens=current_metrics.get("api_output_tokens", 0),
                total_cost_usd=current_metrics.get("total_cost_usd", 0.0),
                tool_call_count=current_metrics.get("tool_call_count", 0),
                message_count=current_metrics.get("message_count", 0),
                hook_execution_count=current_metrics.get("hook_execution_count", 0),
                permission_check_count=current_metrics.get("permission_check_count", 0),
                duration_ms=current_metrics.get("duration_ms", 0),
                metadata={"checkpoint": checkpoint_name}
            )
        except Exception as e:
            logger.error(
                f"Failed to create checkpoint snapshot: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            return None

    async def create_completion_snapshot(
        self,
        session_id: UUID,
        final_metrics: Dict[str, Any]
    ) -> Optional[SessionMetricsSnapshotModel]:
        """Create a snapshot when session completes.

        Args:
            session_id: Session ID
            final_metrics: Final metrics dictionary

        Returns:
            Created snapshot or None if failed
        """
        try:
            return await self.create_snapshot(
                session_id=session_id,
                snapshot_reason="session_complete",
                api_input_tokens=final_metrics.get("api_input_tokens", 0),
                api_output_tokens=final_metrics.get("api_output_tokens", 0),
                total_cost_usd=final_metrics.get("total_cost_usd", 0.0),
                tool_call_count=final_metrics.get("tool_call_count", 0),
                message_count=final_metrics.get("message_count", 0),
                hook_execution_count=final_metrics.get("hook_execution_count", 0),
                permission_check_count=final_metrics.get("permission_check_count", 0),
                duration_ms=final_metrics.get("duration_ms", 0),
                metadata={"completion": True}
            )
        except Exception as e:
            logger.error(
                f"Failed to create completion snapshot: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            return None
