"""Permission Service for tool access control.

Provides fine-grained permission checking for Claude SDK tool execution.
Integrates with our audit logging and repository layers.

Based on Document 7: Hook & Permission System
"""

import re
import logging
from typing import Optional
from uuid import UUID
from pathlib import Path

from claude_agent_sdk.types import (
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)

from app.domain.entities.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionService:
    """Centralized tool permission management.
    
    Provides permission callbacks for the official Claude SDK.
    Checks user roles, tool types, and dangerous patterns before
    allowing tool execution.
    
    Used by ClaudeSDKClientManager when building ClaudeAgentOptions.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        mcp_server_repo: MCPServerRepository,
        audit_service: AuditService,
    ):
        """Initialize permission service with dependencies."""
        self.db = db
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.mcp_server_repo = mcp_server_repo
        self.audit_service = audit_service

        # Dangerous bash command patterns
        self.dangerous_commands = [
            r"rm\s+-rf\s+/",  # Delete root
            r"mkfs",  # Format filesystem
            r"dd\s+if=.*of=/dev/",  # Direct disk write
            r":(){ :|:& };:",  # Fork bomb
            r"chmod\s+777",  # Overly permissive
            r"chown\s+.*root",  # Change owner to root
            r">.*\/dev\/",  # Write to device files
            r"curl.*\|.*bash",  # Pipe to bash
            r"wget.*\|.*bash",  # Pipe to bash
        ]

        # System paths blocked from write access
        self.blocked_paths = [
            "/etc",
            "/usr",
            "/bin",
            "/sbin",
            "/sys",
            "/proc",
            "/boot",
            "/dev",
            "/root",
        ]

    async def check_tool_permission(
        self,
        session_id: UUID,
        user_id: UUID,
        tool_name: str,
        tool_input: dict,
        context: Optional[ToolPermissionContext] = None,
    ) -> PermissionResult:
        """Check if user has permission to use tool with given input.
        
        This is called by the Claude SDK before executing each tool.
        Returns allow/deny decision with optional modifications.
        
        Args:
            session_id: Session UUID
            user_id: User UUID
            tool_name: Name of tool (e.g., "Bash", "Write", "mcp__server__tool")
            tool_input: Tool input parameters
            context: SDK permission context
            
        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        logger.info(
            f"Checking tool permission",
            extra={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "tool_name": tool_name,
                "tool_input_keys": list(tool_input.keys()) if tool_input else [],
                "has_context": context is not None
            }
        )
        
        # Get user and validate
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            logger.warning(
                f"Permission denied - user not found or inactive",
                extra={
                    "session_id": str(session_id),
                    "user_id": str(user_id),
                    "tool_name": tool_name,
                    "user_exists": user is not None,
                    "user_active": user.is_active if user else None
                }
            )
            await self.audit_service.log_permission_denied(
                session_id=session_id,
                user_id=user_id,
                tool_name=tool_name,
                tool_input=tool_input,
                reason="User not found or inactive",
            )
            return PermissionResultDeny(
                message="User not found or inactive",
                interrupt=True
            )

        # Route to specific permission checker
        logger.debug(
            f"Routing to specific permission checker",
            extra={
                "session_id": str(session_id),
                "tool_name": tool_name,
                "user_role": user.role.value if user.role else None
            }
        )
        
        if tool_name == "Bash":
            return await self._check_bash_permission(
                session_id, user, tool_input, context
            )
        elif tool_name in ["Write", "Edit", "MultiEdit"]:
            return await self._check_file_write_permission(
                session_id, user, tool_input, context
            )
        elif tool_name.startswith("mcp__"):
            return await self._check_mcp_tool_permission(
                session_id, user, tool_name, tool_input, context
            )
        else:
            # Default: allow builtin read tools
            logger.info(
                f"Permission granted for built-in read tool",
                extra={
                    "session_id": str(session_id),
                    "tool_name": tool_name,
                    "user_id": str(user.id)
                }
            )
            await self.audit_service.log_permission_allowed(
                session_id=session_id,
                user_id=user.id,
                tool_name=tool_name,
                tool_input=tool_input,
            )
            return PermissionResultAllow()

    async def _check_bash_permission(
        self,
        session_id: UUID,
        user: User,
        tool_input: dict,
        context: Optional[ToolPermissionContext],
    ) -> PermissionResult:
        """Check Bash command permission."""
        command = tool_input.get("command", "")
        
        logger.debug(
            f"Checking bash permission",
            extra={
                "session_id": str(session_id),
                "user_id": str(user.id),
                "command_length": len(command),
                "command_preview": command[:100] + "..." if len(command) > 100 else command
            }
        )

        # Check for dangerous commands
        for pattern in self.dangerous_commands:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(
                    f"Dangerous bash command blocked",
                    extra={
                        "session_id": str(session_id),
                        "user_id": str(user.id),
                        "command": command,
                        "matched_pattern": pattern
                    }
                )
                await self.audit_service.log_permission_denied(
                    session_id=session_id,
                    user_id=user.id,
                    tool_name="Bash",
                    tool_input=tool_input,
                    reason=f"Dangerous command pattern: {pattern}",
                )
                return PermissionResultDeny(
                    message=f"Dangerous command blocked: {command[:50]}...",
                    interrupt=False
                )

        # Check user role restrictions
        if user.role == "viewer":
            # Viewers can only run read-only commands
            readonly_commands = [
                "ls", "cat", "grep", "find", "ps", "df", "du",
                "head", "tail", "wc", "pwd", "echo", "date"
            ]
            cmd_name = command.split()[0] if command.strip() else ""

            logger.debug(
                f"Checking viewer role restrictions",
                extra={
                    "session_id": str(session_id),
                    "user_id": str(user.id),
                    "command_name": cmd_name,
                    "is_readonly": cmd_name in readonly_commands
                }
            )

            if cmd_name not in readonly_commands:
                logger.warning(
                    f"Viewer role command blocked - not read-only",
                    extra={
                        "session_id": str(session_id),
                        "user_id": str(user.id),
                        "command": command,
                        "command_name": cmd_name,
                        "allowed_commands": readonly_commands
                    }
                )
                await self.audit_service.log_permission_denied(
                    session_id=session_id,
                    user_id=user.id,
                    tool_name="Bash",
                    tool_input=tool_input,
                    reason="Viewer role: read-only commands only",
                )
                return PermissionResultDeny(
                    message=f"Viewer role can only run read-only commands",
                    interrupt=False
                )

        # Allow command
        logger.info(
            f"Bash command permission granted",
            extra={
                "session_id": str(session_id),
                "user_id": str(user.id),
                "user_role": user.role.value if user.role else None,
                "command_name": command.split()[0] if command.strip() else ""
            }
        )
        await self.audit_service.log_permission_allowed(
            session_id=session_id,
            user_id=user.id,
            tool_name="Bash",
            tool_input=tool_input,
        )
        return PermissionResultAllow()

    async def _check_file_write_permission(
        self,
        session_id: UUID,
        user: User,
        tool_input: dict,
        context: Optional[ToolPermissionContext],
    ) -> PermissionResult:
        """Check file write permission."""
        file_path = tool_input.get("file_path", "")

        # Check if path is blocked (system directories)
        path = Path(file_path)
        for blocked in self.blocked_paths:
            if str(path).startswith(blocked):
                await self.audit_service.log_permission_denied(
                    session_id=session_id,
                    user_id=user.id,
                    tool_name="Write",
                    tool_input=tool_input,
                    reason=f"Blocked system path: {blocked}",
                )
                return PermissionResultDeny(
                    message=f"Cannot write to system path: {file_path}",
                    interrupt=False
                )

        # Check if path is within session working directory
        session = await self.session_repo.get_by_id(session_id)
        if session and session.working_directory_path:
            workdir = Path(session.working_directory_path)
            try:
                # Resolve paths and check containment
                if path.is_absolute():
                    resolved_path = path.resolve()
                else:
                    resolved_path = (workdir / path).resolve()

                # Check if resolved path is within workdir
                if not str(resolved_path).startswith(str(workdir.resolve())):
                    await self.audit_service.log_permission_denied(
                        session_id=session_id,
                        user_id=user.id,
                        tool_name="Write",
                        tool_input=tool_input,
                        reason="Path outside working directory",
                    )
                    return PermissionResultDeny(
                        message=f"Path outside working directory: {file_path}",
                        interrupt=False
                    )
            except Exception as e:
                logger.error(f"Error resolving path {file_path}: {e}")
                return PermissionResultDeny(
                    message=f"Invalid path: {file_path}",
                    interrupt=False
                )

        # Allow write
        await self.audit_service.log_permission_allowed(
            session_id=session_id,
            user_id=user.id,
            tool_name="Write",
            tool_input=tool_input,
        )
        return PermissionResultAllow()

    async def _check_mcp_tool_permission(
        self,
        session_id: UUID,
        user: User,
        tool_name: str,
        tool_input: dict,
        context: Optional[ToolPermissionContext],
    ) -> PermissionResult:
        """Check MCP tool permission based on server access."""
        # Parse MCP tool name: mcp__server_name__tool_name
        parts = tool_name.split("__")
        if len(parts) < 3:
            await self.audit_service.log_permission_denied(
                session_id=session_id,
                user_id=user.id,
                tool_name=tool_name,
                tool_input=tool_input,
                reason="Invalid MCP tool name format",
            )
            return PermissionResultDeny(
                message="Invalid MCP tool name format",
                interrupt=False
            )

        server_name = parts[1]

        # Check if user has access to this MCP server
        server = await self.mcp_server_repo.get_by_name_and_user(server_name, user.id)
        if not server:
            # Check if it's a global server
            server = await self.mcp_server_repo.get_global_by_name(server_name)
            if not server:
                await self.audit_service.log_permission_denied(
                    session_id=session_id,
                    user_id=user.id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    reason=f"MCP server not found: {server_name}",
                )
                return PermissionResultDeny(
                    message=f"MCP server not found: {server_name}",
                    interrupt=False
                )

        # Check if server is enabled
        if not server.is_enabled:
            await self.audit_service.log_permission_denied(
                session_id=session_id,
                user_id=user.id,
                tool_name=tool_name,
                tool_input=tool_input,
                reason=f"MCP server disabled: {server_name}",
            )
            return PermissionResultDeny(
                message=f"MCP server disabled: {server_name}",
                interrupt=False
            )

        # Allow MCP tool
        await self.audit_service.log_permission_allowed(
            session_id=session_id,
            user_id=user.id,
            tool_name=tool_name,
            tool_input=tool_input,
        )
        return PermissionResultAllow()

    def create_permission_callback(
        self,
        session_id: UUID,
        user_id: UUID,
    ):
        """Create permission callback function for SDK client.
        
        Returns async callback that can be used in ClaudeAgentOptions.can_use_tool.
        
        Args:
            session_id: Session UUID
            user_id: User UUID
            
        Returns:
            Async callback function matching CanUseTool signature
            
        Example:
            >>> callback = permission_service.create_permission_callback(
            ...     session_id=session.id,
            ...     user_id=user.id
            ... )
            >>> options = ClaudeAgentOptions(can_use_tool=callback)
        """

        async def permission_callback(
            tool_name: str,
            tool_input: dict,
            context: ToolPermissionContext,
        ) -> PermissionResult:
            return await self.check_tool_permission(
                session_id=session_id,
                user_id=user_id,
                tool_name=tool_name,
                tool_input=tool_input,
                context=context,
            )

        return permission_callback
