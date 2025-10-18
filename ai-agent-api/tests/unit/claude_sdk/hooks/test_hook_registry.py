"""Unit tests for HookRegistry."""
import pytest
from app.claude_sdk.hooks.hook_registry import HookRegistry, RegisteredHook
from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from typing import Dict, Any, Optional


class MockHook1(BaseHook):
    """Mock hook for testing."""

    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        return {"continue_": True, "hook": "mock1"}


class MockHook2(BaseHook):
    """Mock hook with different priority."""

    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        return 50

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        return {"continue_": True, "hook": "mock2"}


class MockPostToolUseHook(BaseHook):
    """Mock post tool use hook."""

    @property
    def hook_type(self) -> HookType:
        return HookType.POST_TOOL_USE

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        return {"continue_": True, "hook": "post"}


class TestHookRegistry:
    """Tests for HookRegistry."""

    def test_initialization(self):
        """Test registry initializes with empty hooks for all types."""
        registry = HookRegistry()

        # Should have empty lists for all hook types
        for hook_type in HookType:
            hooks = registry.get_hooks(hook_type)
            assert hooks == []

    def test_register_single_hook(self):
        """Test registering a single hook."""
        registry = HookRegistry()
        hook = MockHook1()

        registry.register(HookType.PRE_TOOL_USE, hook, priority=100)

        hooks = registry.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0] == hook

    def test_register_multiple_hooks_same_type(self):
        """Test registering multiple hooks for same type."""
        registry = HookRegistry()
        hook1 = MockHook1()
        hook2 = MockHook2()

        registry.register(HookType.PRE_TOOL_USE, hook1, priority=100)
        registry.register(HookType.PRE_TOOL_USE, hook2, priority=50)

        hooks = registry.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 2

    def test_register_hooks_different_types(self):
        """Test registering hooks for different types."""
        registry = HookRegistry()
        pre_hook = MockHook1()
        post_hook = MockPostToolUseHook()

        registry.register(HookType.PRE_TOOL_USE, pre_hook)
        registry.register(HookType.POST_TOOL_USE, post_hook)

        pre_hooks = registry.get_hooks(HookType.PRE_TOOL_USE)
        post_hooks = registry.get_hooks(HookType.POST_TOOL_USE)

        assert len(pre_hooks) == 1
        assert len(post_hooks) == 1
        assert pre_hooks[0] == pre_hook
        assert post_hooks[0] == post_hook

    def test_get_hooks_sorted_by_priority(self):
        """Test hooks are returned in priority order (ascending)."""
        registry = HookRegistry()
        hook1 = MockHook1()  # priority 100 (default)
        hook2 = MockHook2()  # priority 50

        # Register in non-priority order
        registry.register(HookType.PRE_TOOL_USE, hook1, priority=100)
        registry.register(HookType.PRE_TOOL_USE, hook2, priority=50)

        hooks = registry.get_hooks(HookType.PRE_TOOL_USE)

        # Should be sorted by priority (lower first)
        assert len(hooks) == 2
        assert hooks[0] == hook2  # priority 50
        assert hooks[1] == hook1  # priority 100

    def test_get_hooks_with_same_priority(self):
        """Test hooks with same priority maintain registration order."""
        registry = HookRegistry()
        hook1 = MockHook1()
        hook2 = MockHook2()

        # Register with same priority
        registry.register(HookType.PRE_TOOL_USE, hook1, priority=100)
        registry.register(HookType.PRE_TOOL_USE, hook2, priority=100)

        hooks = registry.get_hooks(HookType.PRE_TOOL_USE)

        assert len(hooks) == 2
        # Stable sort should maintain registration order
        assert hooks[0] == hook1
        assert hooks[1] == hook2

    def test_get_hooks_empty_type(self):
        """Test getting hooks for type with no registrations."""
        registry = HookRegistry()
        hook = MockHook1()

        registry.register(HookType.PRE_TOOL_USE, hook)

        # Get hooks for different type
        hooks = registry.get_hooks(HookType.USER_PROMPT_SUBMIT)

        assert hooks == []

    def test_clear_specific_type(self):
        """Test clearing hooks for specific type."""
        registry = HookRegistry()
        pre_hook = MockHook1()
        post_hook = MockPostToolUseHook()

        registry.register(HookType.PRE_TOOL_USE, pre_hook)
        registry.register(HookType.POST_TOOL_USE, post_hook)

        # Clear only PRE_TOOL_USE
        registry.clear(HookType.PRE_TOOL_USE)

        pre_hooks = registry.get_hooks(HookType.PRE_TOOL_USE)
        post_hooks = registry.get_hooks(HookType.POST_TOOL_USE)

        assert pre_hooks == []
        assert len(post_hooks) == 1

    def test_clear_all_types(self):
        """Test clearing all hook types."""
        registry = HookRegistry()
        pre_hook = MockHook1()
        post_hook = MockPostToolUseHook()

        registry.register(HookType.PRE_TOOL_USE, pre_hook)
        registry.register(HookType.POST_TOOL_USE, post_hook)

        # Clear all
        registry.clear()

        # All types should be empty
        for hook_type in HookType:
            hooks = registry.get_hooks(hook_type)
            assert hooks == []

    def test_get_hook_count_specific_type(self):
        """Test counting hooks for specific type."""
        registry = HookRegistry()
        hook1 = MockHook1()
        hook2 = MockHook2()

        registry.register(HookType.PRE_TOOL_USE, hook1)
        registry.register(HookType.PRE_TOOL_USE, hook2)
        registry.register(HookType.POST_TOOL_USE, MockPostToolUseHook())

        count = registry.get_hook_count(HookType.PRE_TOOL_USE)

        assert count == 2

    def test_get_hook_count_all_types(self):
        """Test counting all hooks across all types."""
        registry = HookRegistry()

        registry.register(HookType.PRE_TOOL_USE, MockHook1())
        registry.register(HookType.PRE_TOOL_USE, MockHook2())
        registry.register(HookType.POST_TOOL_USE, MockPostToolUseHook())

        count = registry.get_hook_count()

        assert count == 3

    def test_get_hook_count_empty_registry(self):
        """Test counting hooks in empty registry."""
        registry = HookRegistry()

        count_all = registry.get_hook_count()
        count_pre = registry.get_hook_count(HookType.PRE_TOOL_USE)

        assert count_all == 0
        assert count_pre == 0

    def test_multiple_priority_levels(self):
        """Test hooks with multiple priority levels."""
        registry = HookRegistry()

        class HighPriorityHook(BaseHook):
            @property
            def hook_type(self):
                return HookType.PRE_TOOL_USE

            @property
            def priority(self):
                return 10

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True, "priority": "high"}

        class LowPriorityHook(BaseHook):
            @property
            def hook_type(self):
                return HookType.PRE_TOOL_USE

            @property
            def priority(self):
                return 200

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True, "priority": "low"}

        high_hook = HighPriorityHook()
        medium_hook = MockHook1()  # priority 100
        low_hook = LowPriorityHook()

        # Register out of order
        registry.register(HookType.PRE_TOOL_USE, medium_hook, priority=100)
        registry.register(HookType.PRE_TOOL_USE, low_hook, priority=200)
        registry.register(HookType.PRE_TOOL_USE, high_hook, priority=10)

        hooks = registry.get_hooks(HookType.PRE_TOOL_USE)

        # Should be sorted by priority
        assert len(hooks) == 3
        assert hooks[0] == high_hook  # 10
        assert hooks[1] == medium_hook  # 100
        assert hooks[2] == low_hook  # 200

    def test_registered_hook_dataclass(self):
        """Test RegisteredHook dataclass."""
        hook = MockHook1()
        registered = RegisteredHook(hook=hook, priority=50)

        assert registered.hook == hook
        assert registered.priority == 50

    def test_all_hook_types_supported(self):
        """Test registry supports all hook types."""
        registry = HookRegistry()

        # Verify all hook types can be registered
        hook_types = [
            HookType.PRE_TOOL_USE,
            HookType.POST_TOOL_USE,
            HookType.USER_PROMPT_SUBMIT,
            HookType.STOP,
            HookType.SUBAGENT_STOP,
            HookType.PRE_COMPACT
        ]

        for hook_type in hook_types:
            hooks = registry.get_hooks(hook_type)
            assert hooks == []

        assert len(hook_types) == 6  # Verify we have all 6 hook types
