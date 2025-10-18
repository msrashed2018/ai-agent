"""Factory for creating appropriate executor based on session mode."""
import logging
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.session import Session, SessionMode
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.core.config import ClientConfig
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.stream_handler import StreamHandler
from app.claude_sdk.handlers.result_handler import ResultHandler
from app.claude_sdk.handlers.error_handler import ErrorHandler
from app.claude_sdk.execution.base_executor import BaseExecutor
from app.claude_sdk.execution.interactive_executor import InteractiveExecutor
from app.claude_sdk.execution.background_executor import BackgroundExecutor
from app.claude_sdk.execution.forked_executor import ForkedExecutor
from app.claude_sdk.retry.retry_manager import RetryManager, RetryPolicy
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.session_metrics_snapshot_repository import SessionMetricsSnapshotRepository
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class ExecutorFactory:
    """Create appropriate executor based on session mode.

    This factory encapsulates executor creation logic and dependency injection:
    - Selects executor type based on session mode
    - Creates and configures Claude SDK client
    - Initializes all required handlers
    - Wires up dependencies correctly

    Example:
        >>> factory = ExecutorFactory()
        >>> executor = await factory.create_executor(session, db, event_broadcaster)
        >>> result = await executor.execute("Hello")
    """

    @staticmethod
    async def create_executor(
        session: Session,
        db: AsyncSession,
        event_broadcaster: Optional[Any] = None,
    ) -> BaseExecutor:
        """Factory method to create executor for session.

        Args:
            session: Domain Session entity with configuration
            db: Async database session
            event_broadcaster: Optional WebSocket event broadcaster (for interactive mode)

        Returns:
            BaseExecutor: Appropriate executor for session mode

        Raises:
            ValueError: If session mode is unknown
        """
        logger.info(
            f"Creating executor for session {session.id} (mode={session.mode.value})",
            extra={"session_id": str(session.id), "mode": session.mode.value},
        )

        # Create client configuration
        from pathlib import Path

        client_config = ClientConfig(
            session_id=session.id,
            model=session.sdk_options.get("model", "claude-sonnet-4-5"),
            permission_mode=session.permission_mode or "default",
            max_turns=session.sdk_options.get("max_turns", 10),
            max_retries=session.max_retries or 3,
            retry_delay=session.retry_delay or 2.0,
            timeout_seconds=session.timeout_seconds or 120,
            include_partial_messages=session.include_partial_messages or False,
            working_directory=Path(session.working_directory_path),
            allowed_tools=session.sdk_options.get("allowed_tools"),
        )

        # Create enhanced client
        client = EnhancedClaudeClient(client_config)

        # Create repositories
        message_repo = MessageRepository(db)
        tool_call_repo = ToolCallRepository(db)
        session_repo = SessionRepository(db)
        metrics_repo = SessionMetricsSnapshotRepository(db)

        # Create handlers
        message_handler = MessageHandler(db, message_repo, tool_call_repo)
        result_handler = ResultHandler(db, session_repo, metrics_repo)
        error_handler = ErrorHandler(db, session_repo, AuditService(db))

        # Create executor based on session mode
        if session.mode == SessionMode.INTERACTIVE:
            stream_handler = StreamHandler(db, message_repo, event_broadcaster)
            return InteractiveExecutor(
                session=session,
                client=client,
                message_handler=message_handler,
                stream_handler=stream_handler,
                result_handler=result_handler,
                error_handler=error_handler,
                event_broadcaster=event_broadcaster,
            )

        elif session.mode == SessionMode.BACKGROUND:
            retry_policy = RetryPolicy(
                max_retries=session.max_retries or 3,
                base_delay=session.retry_delay or 2.0,
            )
            retry_manager = RetryManager(retry_policy)
            return BackgroundExecutor(
                session=session,
                client=client,
                message_handler=message_handler,
                result_handler=result_handler,
                error_handler=error_handler,
                retry_manager=retry_manager,
            )

        elif session.mode == SessionMode.FORKED:
            return ForkedExecutor(
                session=session,
                parent_session_id=session.parent_session_id,
                fork_at_message=None,  # Could be extracted from session metadata
                client=client,
                message_handler=message_handler,
                result_handler=result_handler,
                error_handler=error_handler,
                message_repo=message_repo,
            )

        else:
            raise ValueError(f"Unknown session mode: {session.mode}")
