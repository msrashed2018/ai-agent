"""Unit tests for HookManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from typing import Dict, Any, Optional

from app.claude_sdk.hooks.hook_manager import HookManager
from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from app.repositories.hook_execution_repository import HookExecutionRepository


class MockHook(BaseHook):
    """Mock hook for testing."""

    def __init__(self, should_continue=True, raise_error=False):
        self.should_continue = should_continue
        self.raise_error = raise_error
        self.executed = False
        self.execution_count = 0

    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        return 100

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        self.executed = True
        self.execution_count += 1

        if self.raise_error:
            raise ValueError("Mock hook error")

        return {
            "continue_": self.should_continue,
            "hook_executed": True,
            "hook_name": self.__class__.__name__
        }


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_hook_repo():
    """Create mock hook execution repository."""
    repo = AsyncMock(spec=HookExecutionRepository)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def hook_manager(mock_db_session, mock_hook_repo):
    """Create HookManager instance."""
    return HookManager(mock_db_session, mock_hook_repo)


class TestHookManagerInitialization:
    """Tests for HookManager initialization."""

    def test_initialization(self, mock_db_session, mock_hook_repo):
        """Test HookManager initializes correctly."""
        manager = HookManager(mock_db_session, mock_hook_repo)

        assert manager.db == mock_db_session
        assert manager.hook_execution_repo == mock_hook_repo
        assert manager.registry is not None

    def test_initialization_creates_empty_registry(self, hook_manager):
        """Test initialization creates empty registry."""
        # Registry should have no hooks initially
        hooks = hook_manager.registry.get_hooks(HookType.PRE_TOOL_USE)
        assert hooks == []


class TestHookRegistration:
    """Tests for hook registration."""

    @pytest.mark.asyncio
    async def test_register_hook_with_default_priority(self, hook_manager):
        """Test registering hook with default priority."""
        hook = MockHook()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        hooks = hook_manager.registry.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0] == hook

    @pytest.mark.asyncio
    async def test_register_hook_with_custom_priority(self, hook_manager):
        """Test registering hook with custom priority."""
        hook = MockHook()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook, priority=50)

        hooks = hook_manager.registry.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0] == hook

    @pytest.mark.asyncio
    async def test_register_multiple_hooks(self, hook_manager):
        """Test registering multiple hooks."""
        hook1 = MockHook()
        hook2 = MockHook()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook1, priority=100)
        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook2, priority=50)

        hooks = hook_manager.registry.get_hooks(HookType.PRE_TOOL_USE)
        assert len(hooks) == 2
        # Lower priority first
        assert hooks[0] == hook2
        assert hooks[1] == hook1


class TestHookExecution:
    """Tests for hook execution."""

    @pytest.mark.asyncio
    async def test_execute_single_hook_success(self, hook_manager):
        """Test executing single hook successfully."""
        hook = MockHook(should_continue=True)
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool", "input": {}},
            tool_use_id="tool123",
            context=None,
            session_id=session_id
        )

        assert result["continue_"] is True
        assert result["hook_executed"] is True
        assert hook.executed is True

    @pytest.mark.asyncio
    async def test_execute_hook_that_blocks(self, hook_manager):
        """Test hook that blocks execution."""
        hook = MockHook(should_continue=False)
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        assert result["continue_"] is False
        assert hook.executed is True

    @pytest.mark.asyncio
    async def test_execute_multiple_hooks_in_priority_order(self, hook_manager):
        """Test multiple hooks execute in priority order."""
        hook1 = MockHook(should_continue=True)  # priority 100
        hook2 = MockHook(should_continue=True)  # priority 50

        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook1, priority=100)
        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook2, priority=50)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        # Both should execute
        assert hook1.executed is True
        assert hook2.executed is True
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_execution_stops_when_hook_blocks(self, hook_manager):
        """Test execution stops when hook returns continue_=False."""
        hook1 = MockHook(should_continue=False)  # Blocks
        hook2 = MockHook(should_continue=True)   # Should not execute

        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook1, priority=50)
        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook2, priority=100)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        assert hook1.executed is True
        assert hook2.executed is False  # Should not execute
        assert result["continue_"] is False

    @pytest.mark.asyncio
    async def test_execute_no_hooks_registered(self, hook_manager):
        """Test execution with no hooks registered."""
        session_id = uuid4()

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        # Should allow by default
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_hook_error_continues_execution(self, hook_manager):
        """Test that hook errors don't stop execution."""
        hook1 = MockHook(raise_error=True)   # Will raise error
        hook2 = MockHook(should_continue=True)  # Should still execute

        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook1, priority=50)
        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook2, priority=100)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        # hook1 raised error, hook2 should have executed
        assert hook2.executed is True
        assert result["continue_"] is True

    @pytest.mark.asyncio
    async def test_hook_results_merge(self, hook_manager):
        """Test hook results merge correctly."""
        class CustomHook1(BaseHook):
            @property
            def hook_type(self):
                return HookType.PRE_TOOL_USE

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True, "field1": "value1"}

        class CustomHook2(BaseHook):
            @property
            def hook_type(self):
                return HookType.PRE_TOOL_USE

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True, "field2": "value2"}

        hook1 = CustomHook1()
        hook2 = CustomHook2()
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook1)
        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook2)

        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        # Results should be merged
        assert result["continue_"] is True
        assert result["field1"] == "value1"
        assert result["field2"] == "value2"


class TestHookExecutionLogging:
    """Tests for hook execution logging."""

    @pytest.mark.asyncio
    async def test_successful_hook_execution_logged(self, hook_manager, mock_hook_repo):
        """Test successful hook execution is logged."""
        hook = MockHook(should_continue=True)
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool", "input": {"param": "value"}},
            tool_use_id="tool123",
            context=None,
            session_id=session_id
        )

        # Should log to repository
        mock_hook_repo.create.assert_called_once()
        call_args = mock_hook_repo.create.call_args[0][0]

        assert call_args.session_id == session_id
        assert call_args.tool_use_id == "tool123"
        assert call_args.tool_name == "test_tool"
        assert call_args.error_message is None

    @pytest.mark.asyncio
    async def test_failed_hook_execution_logged(self, hook_manager, mock_hook_repo):
        """Test failed hook execution is logged with error."""
        hook = MockHook(raise_error=True)
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id="tool123",
            context=None,
            session_id=session_id
        )

        # Should log error
        mock_hook_repo.create.assert_called_once()
        call_args = mock_hook_repo.create.call_args[0][0]

        assert call_args.session_id == session_id
        assert call_args.error_message is not None
        assert "ValueError" in call_args.error_message

    @pytest.mark.asyncio
    async def test_logging_failure_doesnt_stop_execution(self, hook_manager, mock_hook_repo):
        """Test that logging failures don't stop hook execution."""
        # Make logging fail
        mock_hook_repo.create.side_effect = Exception("Logging failed")

        hook = MockHook(should_continue=True)
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        # Should not raise exception
        result = await hook_manager.execute_hooks(
            hook_type=HookType.PRE_TOOL_USE,
            input_data={"name": "test_tool"},
            tool_use_id=None,
            context=None,
            session_id=session_id
        )

        assert result["continue_"] is True
        assert hook.executed is True


class TestBuildHookMatchers:
    """Tests for building SDK hook matchers."""

    @pytest.mark.asyncio
    async def test_build_hook_matchers_single_type(self, hook_manager):
        """Test building hook matchers for single hook type."""
        hook = MockHook()
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, hook)

        matchers = hook_manager.build_hook_matchers(
            session_id=session_id,
            enabled_hook_types=[HookType.PRE_TOOL_USE]
        )

        assert "PreToolUse" in matchers
        assert len(matchers["PreToolUse"]) == 1

    @pytest.mark.asyncio
    async def test_build_hook_matchers_multiple_types(self, hook_manager):
        """Test building hook matchers for multiple hook types."""
        class PostToolUseHook(BaseHook):
            @property
            def hook_type(self):
                return HookType.POST_TOOL_USE

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True}

        pre_hook = MockHook()
        post_hook = PostToolUseHook()
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, pre_hook)
        await hook_manager.register_hook(HookType.POST_TOOL_USE, post_hook)

        matchers = hook_manager.build_hook_matchers(
            session_id=session_id,
            enabled_hook_types=[HookType.PRE_TOOL_USE, HookType.POST_TOOL_USE]
        )

        assert "PreToolUse" in matchers
        assert "PostToolUse" in matchers
        assert len(matchers) == 2

    @pytest.mark.asyncio
    async def test_build_hook_matchers_no_hooks_registered(self, hook_manager):
        """Test building hook matchers when no hooks are registered."""
        session_id = uuid4()

        matchers = hook_manager.build_hook_matchers(
            session_id=session_id,
            enabled_hook_types=[HookType.PRE_TOOL_USE]
        )

        # Should return empty dict when no hooks registered
        assert matchers == {}

    @pytest.mark.asyncio
    async def test_build_hook_matchers_only_enabled_types(self, hook_manager):
        """Test only enabled hook types are included."""
        class PostToolUseHook(BaseHook):
            @property
            def hook_type(self):
                return HookType.POST_TOOL_USE

            async def execute(self, input_data, tool_use_id, context):
                return {"continue_": True}

        pre_hook = MockHook()
        post_hook = PostToolUseHook()
        session_id = uuid4()

        await hook_manager.register_hook(HookType.PRE_TOOL_USE, pre_hook)
        await hook_manager.register_hook(HookType.POST_TOOL_USE, post_hook)

        # Only enable PRE_TOOL_USE
        matchers = hook_manager.build_hook_matchers(
            session_id=session_id,
            enabled_hook_types=[HookType.PRE_TOOL_USE]
        )

        assert "PreToolUse" in matchers
        assert "PostToolUse" not in matchers


class TestContextSerialization:
    """Tests for context serialization."""

    @pytest.mark.asyncio
    async def test_serialize_dict_context(self, hook_manager):
        """Test serializing dict context."""
        context = {"key": "value", "number": 42}
        serialized = hook_manager._serialize_context(context)

        assert serialized == context

    @pytest.mark.asyncio
    async def test_serialize_object_context(self, hook_manager):
        """Test serializing object context."""
        class MockContext:
            def __init__(self):
                self.signal = "test_signal"
                self.suggestions = [1, 2, 3]

        context = MockContext()
        serialized = hook_manager._serialize_context(context)

        assert serialized["type"] == "MockContext"
        assert "signal" in serialized
        assert serialized["suggestions"] == 3

    @pytest.mark.asyncio
    async def test_serialize_none_context(self, hook_manager):
        """Test serializing None context."""
        serialized = hook_manager._serialize_context(None)

        assert serialized["type"] == "None"

    @pytest.mark.asyncio
    async def test_serialize_context_with_error(self, hook_manager):
        """Test serializing problematic context."""
        class ProblematicContext:
            @property
            def signal(self):
                raise AttributeError("Cannot access signal")

        context = ProblematicContext()
        serialized = hook_manager._serialize_context(context)

        # Should handle error gracefully
        assert "type" in serialized
        assert serialized["type"] == "ProblematicContext"
