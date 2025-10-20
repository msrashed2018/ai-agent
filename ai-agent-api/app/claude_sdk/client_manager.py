"""Claude SDK Client Manager.

Integration layer for managing ClaudeSDKClient instances from the official
claude-agent-sdk package. Provides business logic for session lifecycle,
permission callbacks, and hook management.

Architecture:
- Wraps official claude-agent-sdk.ClaudeSDKClient
- Manages pool of clients (one per session)
- Integrates with our domain entities and services
- Handles connection lifecycle and cleanup

Based on Document 5: Session Management Architecture
"""

import asyncio
from typing import Dict, Optional, Callable
from uuid import UUID

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions

from app.domain.entities.session import Session
from app.claude_sdk.exceptions import (
    ClientAlreadyExistsError,
    ClientNotFoundError,
    SDKConnectionError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClaudeSDKClientManager:
    """Manages pool of ClaudeSDKClient instances from official SDK.
    
    This is an integration layer that:
    - Creates and manages official ClaudeSDKClient instances
    - Converts our domain Session entities to ClaudeAgentOptions
    - Provides lifecycle management (create, get, disconnect)
    - Integrates with our permission and hook systems
    
    Each session gets its own isolated SDK client with:
    - Dedicated working directory
    - Custom permission callbacks
    - Hook handlers for audit logging
    - Automatic cleanup on disconnect
    """

    def __init__(self):
        """Initialize the client manager with empty pools."""
        self._clients: Dict[UUID, ClaudeSDKClient] = {}
        self._locks: Dict[UUID, asyncio.Lock] = {}
        self._background_tasks: Dict[UUID, asyncio.Task] = {}

    async def create_client(
        self,
        session: Session,
        permission_callback: Optional[Callable] = None,
        hooks: Optional[dict] = None,
    ) -> ClaudeSDKClient:
        """Create and connect a new SDK client for session.
        
        This wraps the official claude-agent-sdk.ClaudeSDKClient.
        
        Args:
            session: Our domain Session entity
            permission_callback: Optional permission callback (can_use_tool)
            hooks: Optional hooks configuration
            
        Returns:
            Connected ClaudeSDKClient from official SDK
            
        Raises:
            ClientAlreadyExistsError: If client already exists
            SDKConnectionError: If connection fails
        """
        session_id = session.id
        
        logger.info(
            "Creating Claude SDK client for session",
            extra={
                "session_id": str(session_id),
                "user_id": str(session.user_id),
                "mode": session.mode.value,
                "has_permission_callback": permission_callback is not None,
                "hooks_count": len(hooks) if hooks else 0
            }
        )

        # Create lock for this session
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        async with self._locks[session_id]:
            if session_id in self._clients:
                raise ClientAlreadyExistsError(
                    f"Client already exists for session {session_id}"
                )

            # Build ClaudeAgentOptions from our Session entity
            options = self._build_options(session, permission_callback, hooks)

            # Create official SDK client
            client = ClaudeSDKClient(options=options)

            # Connect to Claude Code CLI
            try:
                await client.connect(prompt=None)
                logger.info(
                    "Claude SDK client connected successfully",
                    extra={
                        "session_id": str(session_id),
                        "user_id": str(session.user_id)
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to connect Claude SDK client",
                    extra={
                        "session_id": str(session_id),
                        "user_id": str(session.user_id),
                        "error": str(e)
                    }
                )
                raise SDKConnectionError(f"Failed to connect to Claude Code CLI: {e}") from e

            # Store in pool
            self._clients[session_id] = client
            
            logger.info(
                "Claude SDK client created and stored in pool",
                extra={
                    "session_id": str(session_id),
                    "active_clients": len(self._clients)
                }
            )
            
            return client

    async def get_client(self, session_id: UUID) -> ClaudeSDKClient:
        """Get existing SDK client for session.
        
        Returns:
            ClaudeSDKClient from official SDK
        """
        if session_id not in self._clients:
            raise ClientNotFoundError(f"No client found for session {session_id}")
        return self._clients[session_id]

    async def disconnect_client(self, session_id: UUID) -> None:
        """Disconnect and remove SDK client."""
        logger.info(
            "Disconnecting Claude SDK client",
            extra={
                "session_id": str(session_id),
                "active_clients_before": len(self._clients)
            }
        )
        
        lock = self._locks.get(session_id, asyncio.Lock())
        async with lock:
            if session_id in self._clients:
                client = self._clients[session_id]
                try:
                    await client.disconnect()
                    logger.info(
                        "Claude SDK client disconnected successfully",
                        extra={"session_id": str(session_id)}
                    )
                except Exception as e:
                    logger.error(f"Error disconnecting client: {e}")
                finally:
                    del self._clients[session_id]

            # Cancel background tasks
            if session_id in self._background_tasks:
                task = self._background_tasks[session_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._background_tasks[session_id]

            # Remove lock
            if session_id in self._locks:
                del self._locks[session_id]

    def has_client(self, session_id: UUID) -> bool:
        """Check if client exists for session."""
        return session_id in self._clients

    async def get_active_count(self) -> int:
        """Get count of active SDK clients."""
        return len(self._clients)

    async def cleanup_all(self) -> None:
        """Disconnect all clients (called on shutdown)."""
        session_ids = list(self._clients.keys())
        logger.info(f"Cleaning up {len(session_ids)} SDK clients")

        for session_id in session_ids:
            try:
                await self.disconnect_client(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")

    def _build_options(
        self,
        session: Session,
        permission_callback: Optional[Callable] = None,
        hooks: Optional[dict] = None,
    ) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions from our Session entity.
        
        Converts our domain model to official SDK options format.
        """
        # session.sdk_options is already a dict
        sdk_config = session.sdk_options if isinstance(session.sdk_options, dict) else {}

        # Build official SDK options
        options = ClaudeAgentOptions(
            # Tool configuration
            allowed_tools=sdk_config.get("allowed_tools", []),
            disallowed_tools=sdk_config.get("disallowed_tools", []),
            
            # Permission mode
            permission_mode=sdk_config.get("permission_mode", "default"),
            
            # Model and limits
            model=sdk_config.get("model"),
            max_turns=sdk_config.get("max_turns"),
            
            # Working directory
            cwd=str(session.working_directory_path) if session.working_directory_path else None,
            
            # MCP servers
            mcp_servers=sdk_config.get("mcp_servers", {}),
            
            # System prompt
            system_prompt=sdk_config.get("system_prompt"),
            
            # Additional settings
            env=sdk_config.get("env", {}),
            add_dirs=sdk_config.get("add_dirs", []),
            settings=sdk_config.get("settings"),
        )

        # Add custom permission callback if provided
        if permission_callback:
            options.can_use_tool = permission_callback
            # SDK requires this when using can_use_tool
            options.permission_prompt_tool_name = "stdio"

        # Add hooks if provided
        if hooks:
            options.hooks = hooks

        return options
