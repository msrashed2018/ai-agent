"""Permission system for Claude SDK integration.

This module provides a comprehensive permission system for controlling tool access:

- BasePolicy: Abstract base class for all policies
- PolicyEngine: Evaluates policies in priority order
- PermissionManager: Orchestrates permission checks and logging
- PermissionContext: Context object for policy evaluation
- Built-in policies: FileAccessPolicy, CommandPolicy, NetworkPolicy, etc.

Example usage:
    >>> from app.claude_sdk.permissions import PermissionManager, PolicyEngine
    >>> from app.claude_sdk.permissions.policies import FileAccessPolicy, CommandPolicy
    >>>
    >>> # Create engine and register policies
    >>> engine = PolicyEngine()
    >>> engine.register_policy(FileAccessPolicy(
    ...     restricted_read_paths=["/etc/passwd", "~/.ssh/"],
    ...     allowed_write_paths=["/tmp/", "/workspace/"]
    ... ))
    >>> engine.register_policy(CommandPolicy(
    ...     blocked_patterns=["rm -rf", "sudo rm"]
    ... ))
    >>>
    >>> # Create manager
    >>> manager = PermissionManager(db, engine, permission_repo)
    >>>
    >>> # Create callback for SDK
    >>> callback = manager.create_callback(session_id, user_id)
    >>> options = ClaudeAgentOptions(can_use_tool=callback, ...)
"""
from app.claude_sdk.permissions.base_policy import BasePolicy
from app.claude_sdk.permissions.permission_context import PermissionContext
from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.claude_sdk.permissions.permission_manager import PermissionManager
from app.claude_sdk.permissions.policies import (
    FileAccessPolicy,
    CommandPolicy,
    NetworkPolicy,
    ToolWhitelistPolicy,
    ToolBlacklistPolicy,
)

__all__ = [
    # Base classes
    "BasePolicy",
    "PermissionContext",
    "PolicyEngine",
    "PermissionManager",
    # Built-in policies
    "FileAccessPolicy",
    "CommandPolicy",
    "NetworkPolicy",
    "ToolWhitelistPolicy",
    "ToolBlacklistPolicy",
]
