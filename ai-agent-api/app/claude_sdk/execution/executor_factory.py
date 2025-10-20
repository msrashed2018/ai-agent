"""Factory for creating appropriate executor based on session mode."""
from typing import Optional, Any, Dict, List

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
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.services.audit_service import AuditService
from app.claude_sdk.hooks.hook_manager import HookManager
from app.claude_sdk.hooks.base_hook import HookType
from app.claude_sdk.hooks.implementations.audit_hook import AuditHook
from app.claude_sdk.hooks.implementations.metrics_hook import MetricsHook
from app.claude_sdk.hooks.implementations.validation_hook import ValidationHook
from app.claude_sdk.hooks.implementations.notification_hook import NotificationHook
from app.claude_sdk.permissions.permission_manager import PermissionManager
from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.core.logging import get_logger

logger = get_logger(__name__)


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
            "Creating executor for session",
            extra={
                "session_id": str(session.id),
                "user_id": str(session.user_id),
                "mode": session.mode.value,
                "status": session.status.value,
                "has_event_broadcaster": event_broadcaster is not None
            }
        )

        # Create hook and permission repositories
        hook_execution_repo = HookExecutionRepository(db)
        permission_decision_repo = PermissionDecisionRepository(db)

        # Initialize HookManager and register default hooks
        hook_manager = HookManager(db, hook_execution_repo)
        hooks_dict: Optional[Dict[str, List[Any]]] = None

        if session.hooks_enabled:
            logger.info(
                f"Registering hooks for session {session.id}: {session.hooks_enabled}",
                extra={"session_id": str(session.id), "hooks": session.hooks_enabled}
            )

            # Register default hook implementations based on enabled hooks
            for hook_type_name in session.hooks_enabled:
                try:
                    hook_type = HookType(hook_type_name)

                    # Register AuditHook for PreToolUse
                    if hook_type == HookType.PRE_TOOL_USE:
                        audit_hook = AuditHook(db)
                        await hook_manager.register_hook(hook_type, audit_hook, priority=10)

                        validation_hook = ValidationHook(db)
                        await hook_manager.register_hook(hook_type, validation_hook, priority=20)

                    # Register MetricsHook for PostToolUse
                    elif hook_type == HookType.POST_TOOL_USE:
                        metrics_hook = MetricsHook(db)
                        await hook_manager.register_hook(hook_type, metrics_hook, priority=10)

                    # Register NotificationHook for Stop events
                    elif hook_type == HookType.STOP:
                        notification_hook = NotificationHook(db)
                        await hook_manager.register_hook(hook_type, notification_hook, priority=10)

                except ValueError:
                    logger.warning(
                        f"Unknown hook type: {hook_type_name}",
                        extra={"session_id": str(session.id)}
                    )

            # Build SDK-compatible hook matchers
            enabled_hook_types = [HookType(ht) for ht in session.hooks_enabled if ht in [e.value for e in HookType]]
            hooks_dict = hook_manager.build_hook_matchers(session.id, enabled_hook_types)

            logger.info(
                f"Built {len(hooks_dict)} hook matchers for session {session.id}",
                extra={"session_id": str(session.id), "hook_types": list(hooks_dict.keys())}
            )

        # Initialize PermissionManager and PolicyEngine
        policy_engine = PolicyEngine()
        permission_manager = PermissionManager(db, policy_engine, permission_decision_repo)

        # Register default policies based on permission mode
        # For now, we'll use the policy engine without pre-registered policies
        # Specific policies can be added based on session.custom_policies if needed

        # Create permission callback
        permission_callback = permission_manager.create_callback(
            session_id=session.id,
            user_id=session.user_id,
            working_directory=session.working_directory_path
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
            hooks=hooks_dict,
            can_use_tool=permission_callback,
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
            logger.info(
                "Creating interactive executor with streaming",
                extra={
                    "session_id": str(session.id),
                    "executor_type": "InteractiveExecutor"
                }
            )
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
            logger.info(
                "Creating background executor for automation",
                extra={
                    "session_id": str(session.id),
                    "executor_type": "BackgroundExecutor",
                    "max_retries": session.max_retries or 3,
                    "retry_delay": session.retry_delay or 2.0
                }
            )
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
