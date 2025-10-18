"""Hook system for Claude SDK integration.

This module provides a comprehensive hook system for extending Claude SDK behavior:

- BaseHook: Abstract base class for all hooks
- HookType: Enumeration of available hook types
- HookManager: Orchestrator for hook execution
- HookRegistry: Registry for managing hooks
- HookContext: Context object passed to hooks
- Built-in hooks: AuditHook, MetricsHook, ValidationHook, NotificationHook

Example usage:
    >>> from app.claude_sdk.hooks import HookManager, HookType
    >>> from app.claude_sdk.hooks.implementations import AuditHook, MetricsHook
    >>>
    >>> # Create manager
    >>> manager = HookManager(db, hook_execution_repo)
    >>>
    >>> # Register hooks
    >>> manager.register_hook(HookType.PRE_TOOL_USE, AuditHook(audit_service))
    >>> manager.register_hook(HookType.POST_TOOL_USE, MetricsHook())
    >>>
    >>> # Build SDK configuration
    >>> hooks = manager.build_hook_matchers(session_id, [HookType.PRE_TOOL_USE])
    >>> options = ClaudeAgentOptions(hooks=hooks, ...)
"""
from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from app.claude_sdk.hooks.hook_context import HookContext
from app.claude_sdk.hooks.hook_manager import HookManager
from app.claude_sdk.hooks.hook_registry import HookRegistry, RegisteredHook
from app.claude_sdk.hooks.implementations import (
    AuditHook,
    MetricsHook,
    ValidationHook,
    NotificationHook,
    NotificationChannel,
)

__all__ = [
    # Base classes and types
    "BaseHook",
    "HookType",
    "HookContext",
    "HookManager",
    "HookRegistry",
    "RegisteredHook",
    # Built-in hooks
    "AuditHook",
    "MetricsHook",
    "ValidationHook",
    "NotificationHook",
    "NotificationChannel",
]
