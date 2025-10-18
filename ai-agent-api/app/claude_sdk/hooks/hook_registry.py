"""Hook registry for managing registered hooks."""
from dataclasses import dataclass
from typing import List, Dict, Optional
from app.claude_sdk.hooks.base_hook import BaseHook, HookType


@dataclass
class RegisteredHook:
    """Wrapper for registered hook with priority."""
    hook: BaseHook
    priority: int


class HookRegistry:
    """Registry for managing hooks across hook types.

    Maintains a registry of hooks organized by type and supports priority-based
    ordering for execution.
    """

    def __init__(self):
        """Initialize empty hook registry."""
        self._hooks: Dict[HookType, List[RegisteredHook]] = {
            hook_type: [] for hook_type in HookType
        }

    def register(
        self,
        hook_type: HookType,
        hook: BaseHook,
        priority: int = 100
    ) -> None:
        """Register a hook for a specific type.

        Args:
            hook_type: Type of hook to register
            hook: Hook instance to register
            priority: Execution priority (lower = earlier)
        """
        registered_hook = RegisteredHook(hook=hook, priority=priority)
        self._hooks[hook_type].append(registered_hook)

    def get_hooks(self, hook_type: HookType) -> List[BaseHook]:
        """Get all hooks for a type, sorted by priority.

        Args:
            hook_type: Type of hooks to retrieve

        Returns:
            List of hooks sorted by priority (ascending)
        """
        registered_hooks = self._hooks.get(hook_type, [])
        sorted_hooks = sorted(registered_hooks, key=lambda rh: rh.priority)
        return [rh.hook for rh in sorted_hooks]

    def clear(self, hook_type: Optional[HookType] = None) -> None:
        """Clear hooks for a specific type or all types.

        Args:
            hook_type: Type to clear, or None to clear all
        """
        if hook_type:
            self._hooks[hook_type] = []
        else:
            self._hooks = {ht: [] for ht in HookType}

    def get_hook_count(self, hook_type: Optional[HookType] = None) -> int:
        """Get count of registered hooks.

        Args:
            hook_type: Type to count, or None to count all

        Returns:
            Number of registered hooks
        """
        if hook_type:
            return len(self._hooks.get(hook_type, []))
        return sum(len(hooks) for hooks in self._hooks.values())
