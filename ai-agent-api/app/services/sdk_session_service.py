"""Extended SessionService with Claude SDK integration.

Extends SessionService with methods for sending messages through the
official Claude SDK and processing responses.
"""

import logging
from typing import AsyncIterator, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session_service import SessionService
from app.claude_sdk import (
    ClaudeSDKClientManager,
    PermissionService,
    MessageProcessor,
    EventBroadcaster,
    create_audit_hook,
    create_tool_tracking_hook,
    create_cost_tracking_hook,
)
from app.domain.value_objects.message import Message
from app.domain.entities.session import SessionStatus
from app.domain.exceptions import SessionNotActiveError
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.repositories.user_repository import UserRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.storage_manager import StorageManager
from app.services.audit_service import AuditService
from app.claude_sdk.execution.executor_factory import ExecutorFactory
from app.claude_sdk.execution.base_executor import BaseExecutor

logger = logging.getLogger(__name__)


class SDKIntegratedSessionService(SessionService):
    """SessionService with Claude SDK integration.
    
    Adds methods for:
    - Sending messages through official Claude SDK
    - Processing message streams
    - Managing SDK client lifecycle
    - Permission callbacks and hooks
    
    Example:
        >>> service = SDKIntegratedSessionService(...)
        >>> session = await service.create_session(...)
        >>> async for message in service.send_message(session.id, user.id, "Hello"):
        ...     print(message)
    """

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository,
        user_repo: UserRepository,
        mcp_server_repo: MCPServerRepository,
        storage_manager: StorageManager,
        audit_service: AuditService,
        sdk_client_manager: ClaudeSDKClientManager,
        permission_service: PermissionService,
        event_broadcaster: Optional[EventBroadcaster] = None,
    ):
        """Initialize with SDK components."""
        super().__init__(
            db=db,
            session_repo=session_repo,
            message_repo=message_repo,
            tool_call_repo=tool_call_repo,
            user_repo=user_repo,
            storage_manager=storage_manager,
            audit_service=audit_service,
        )
        self.sdk_client_manager = sdk_client_manager
        self.permission_service = permission_service
        self.event_broadcaster = event_broadcaster

    async def send_message(
        self,
        session_id: UUID,
        user_id: UUID,
        message_text: str,
    ) -> AsyncIterator[Message]:
        """Send message to Claude and stream responses.
        
        Complete flow:
        1. Validate session and user
        2. Get or create SDK client
        3. Set up permission callbacks and hooks
        4. Send message through SDK
        5. Process and persist response stream
        6. Update session metrics
        7. Broadcast to WebSocket subscribers
        
        Args:
            session_id: Session UUID
            user_id: User UUID
            message_text: User message text
            
        Yields:
            Domain Message entities from response stream
            
        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionNotActiveError: Session not in active state
            PermissionDeniedError: User doesn't have access
            
        Example:
            >>> async for message in service.send_message(session_id, user_id, "Hello"):
            ...     if message.message_type == MessageType.ASSISTANT:
            ...         print(f"Claude: {message.content}")
        """
        # 1. Get and validate session
        session = await self.get_session(session_id, user_id)
        
        if session.status not in [SessionStatus.CREATED, SessionStatus.ACTIVE, SessionStatus.CONNECTING]:
            raise SessionNotActiveError(f"Session {session_id} is not in a valid state for messaging")

        # 2. Update status following proper state transitions
        if session.status == SessionStatus.CREATED:
            # CREATED → CONNECTING (when initializing SDK client)
            session.transition_to(SessionStatus.CONNECTING)
            await self.session_repo.update(session_id, status=SessionStatus.CONNECTING.value)
            await self.db.commit()
            
            # Setup SDK client during CONNECTING phase
            if not self.sdk_client_manager.has_client(session_id):
                await self._setup_sdk_client(session, user_id)
            
            # CONNECTING → ACTIVE (after SDK client is ready)
            session.transition_to(SessionStatus.ACTIVE)
            await self.session_repo.update(session_id, status=SessionStatus.ACTIVE.value)
            await self.db.commit()

        # ACTIVE → PROCESSING (while handling message)
        session.transition_to(SessionStatus.PROCESSING)
        await self.session_repo.update(session_id, status=SessionStatus.PROCESSING.value)
        await self.db.commit()

        try:
            # 3. Get SDK client (already created in CONNECTING phase if it was a new session)
            client = await self.sdk_client_manager.get_client(session_id)

            # 4. Send message through SDK
            await client.query(message_text)

            # 5. Process response stream
            message_processor = MessageProcessor(
                db=self.db,
                message_repo=self.message_repo,
                tool_call_repo=self.tool_call_repo,
                session_repo=self.session_repo,
                event_broadcaster=self.event_broadcaster,
            )

            # Stream and process messages
            async for message in message_processor.process_message_stream(
                session=session,
                sdk_messages=client.receive_response(),
            ):
                yield message

            # 6. Update status back to ACTIVE
            session.transition_to(SessionStatus.ACTIVE)
            await self.session_repo.update(session_id, status=SessionStatus.ACTIVE.value)
            await self.db.commit()

        except Exception as e:
            logger.error(f"Error sending message in session {session_id}: {e}")
            
            # Mark session as failed
            session.transition_to(SessionStatus.FAILED)
            session.error_message = str(e)
            await self.session_repo.update(
                session_id,
                status=SessionStatus.FAILED.value,
                error_message=str(e),
            )
            await self.db.commit()
            
            raise

    async def _setup_sdk_client(self, session, user_id: UUID):
        """Set up SDK client with permission callbacks, hooks, and MCP config.
        
        This method:
        1. Builds dynamic MCP config (SDK tools + user external servers)
        2. Updates session.sdk_options with merged MCP config
        3. Creates permission callbacks for tool access control
        4. Sets up hooks for audit, tracking, and cost monitoring
        5. Creates SDK client with all configurations
        """
        from claude_agent_sdk.types import HookMatcher
        from app.mcp import MCPConfigBuilder
        from app.repositories.mcp_server_repository import MCPServerRepository
        from app.domain.value_objects.sdk_options import SDKOptions

        # 1. Build dynamic MCP configuration
        # This merges SDK_MCP_SERVERS (kubernetes_readonly, database, monitoring)
        # with user's personal MCP servers and global MCP servers from database
        mcp_server_repo = MCPServerRepository(self.db)
        mcp_config_builder = MCPConfigBuilder(mcp_server_repo)
        
        logger.info(f"Building MCP config for session {session.id}, user {user_id}")
        mcp_config = await mcp_config_builder.build_session_mcp_config(
            user_id=user_id,
            include_sdk_tools=True,  # Include SDK tools (7 tools across 3 servers)
        )
        logger.info(f"Built MCP config with {len(mcp_config)} servers: {list(mcp_config.keys())}")

        # 2. Merge MCP config into session's sdk_options
        sdk_options_dict = session.sdk_options.to_dict() if session.sdk_options else {}
        sdk_options_dict["mcp_servers"] = mcp_config

        # Update session entity with merged config
        session.sdk_options = SDKOptions.from_dict(sdk_options_dict)

        # Persist updated sdk_options to database
        await self.session_repo.update(
            str(session.id),
            sdk_options=sdk_options_dict
        )
        await self.db.commit()
        logger.info(f"Updated session {session.id} with merged MCP config")

        # 3. Create permission callback
        permission_callback = self.permission_service.create_permission_callback(
            session_id=session.id,
            user_id=user_id,
        )

        # 4. Create hooks
        hooks = {
            "PreToolUse": [
                HookMatcher(hooks=[
                    create_audit_hook(session.id, self.audit_service),
                    create_tool_tracking_hook(
                        session.id,
                        self.db,
                        self.tool_call_repo,
                    ),
                ]),
            ],
            "PostToolUse": [
                HookMatcher(hooks=[
                    create_audit_hook(session.id, self.audit_service),
                    create_tool_tracking_hook(
                        session.id,
                        self.db,
                        self.tool_call_repo,
                    ),
                    create_cost_tracking_hook(
                        session.id,
                        self.db,
                        self.session_repo,
                    ),
                ]),
            ],
        }

        # 5. Create SDK client with merged configuration
        # Now the client will have access to all MCP servers:
        # - SDK tools (kubernetes_readonly, database, monitoring)
        # - User's personal external MCP servers
        # - Global MCP servers
        await self.sdk_client_manager.create_client(
            session=session,
            permission_callback=permission_callback,
            hooks=hooks,
        )

    async def execute_query(
        self,
        session_id: UUID,
        user_id: UUID,
        query: str,
    ) -> Any:
        """Execute query using ExecutorFactory pattern (Phase 2 integration).

        This is the new implementation that uses ExecutorFactory to create
        appropriate executors based on session mode, with hooks and permissions
        automatically wired in.

        Args:
            session_id: Session UUID
            user_id: User UUID
            query: User query text

        Returns:
            Execution result from executor

        Raises:
            SessionNotFoundError: Session doesn't exist
            SessionNotActiveError: Session not in active state

        Example:
            >>> result = await service.execute_query(session_id, user_id, "Hello")
        """
        # 1. Get and validate session
        session = await self.get_session(session_id, user_id)

        if session.status not in [SessionStatus.CREATED, SessionStatus.ACTIVE, SessionStatus.CONNECTING]:
            raise SessionNotActiveError(f"Session {session_id} is not in a valid state for messaging")

        # 2. Update status to PROCESSING
        session.transition_to(SessionStatus.PROCESSING)
        await self.session_repo.update(session_id, status=SessionStatus.PROCESSING.value)
        await self.db.commit()

        try:
            # 3. Create executor using ExecutorFactory
            # This automatically wires in HookManager and PermissionManager
            executor = await ExecutorFactory.create_executor(
                session=session,
                db=self.db,
                event_broadcaster=self.event_broadcaster,
            )

            # 4. Execute query
            logger.info(
                f"Executing query for session {session_id} using {executor.__class__.__name__}",
                extra={"session_id": str(session_id), "executor_type": executor.__class__.__name__}
            )
            result = await executor.execute(query)

            # 5. Update status back to ACTIVE
            session.transition_to(SessionStatus.ACTIVE)
            await self.session_repo.update(session_id, status=SessionStatus.ACTIVE.value)
            await self.db.commit()

            return result

        except Exception as e:
            logger.error(
                f"Error executing query in session {session_id}: {e}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )

            # Mark session as failed
            session.transition_to(SessionStatus.FAILED)
            session.error_message = str(e)
            await self.session_repo.update(
                session_id,
                status=SessionStatus.FAILED.value,
                error_message=str(e),
            )
            await self.db.commit()

            raise

    async def cleanup_session_client(self, session_id: UUID):
        """Disconnect SDK client for session.

        Called when terminating or deleting a session.

        Args:
            session_id: Session UUID
        """
        try:
            await self.sdk_client_manager.disconnect_client(session_id)
        except Exception as e:
            logger.error(f"Error disconnecting client for session {session_id}: {e}")

    async def terminate_session(
        self,
        session_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ):
        """Terminate session and disconnect SDK client."""
        # Disconnect SDK client first
        await self.cleanup_session_client(session_id)
        
        # Call parent implementation
        return await super().terminate_session(session_id, user_id, reason)

    async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """Delete session and disconnect SDK client."""
        # Disconnect SDK client first
        await self.cleanup_session_client(session_id)
        
        # Call parent implementation
        return await super().delete_session(session_id, user_id)
