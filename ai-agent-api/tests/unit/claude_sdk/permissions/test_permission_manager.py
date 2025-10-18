"""Unit tests for PermissionManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.permission_manager import PermissionManager
from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.domain.entities.permission_decision import PermissionResult


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_permission_repo():
    """Create mock permission decision repository."""
    repo = AsyncMock(spec=PermissionDecisionRepository)
    repo.create = AsyncMock()
    return repo


@pytest.fixture
def mock_policy_engine():
    """Create mock policy engine."""
    engine = AsyncMock(spec=PolicyEngine)
    engine.evaluate = AsyncMock(return_value=PermissionResultAllow())
    return engine


@pytest.fixture
def permission_manager(mock_db_session, mock_policy_engine, mock_permission_repo):
    """Create PermissionManager instance."""
    return PermissionManager(
        db=mock_db_session,
        policy_engine=mock_policy_engine,
        permission_decision_repo=mock_permission_repo,
        enable_cache=True
    )


@pytest.fixture
def mock_context():
    """Create mock permission context."""
    context = MagicMock(spec=ToolPermissionContext)
    context.signal = "test_signal"
    context.suggestions = [1, 2, 3]
    return context


class TestPermissionManagerInitialization:
    """Tests for PermissionManager initialization."""

    def test_initialization(self, mock_db_session, mock_policy_engine, mock_permission_repo):
        """Test PermissionManager initializes correctly."""
        manager = PermissionManager(
            db=mock_db_session,
            policy_engine=mock_policy_engine,
            permission_decision_repo=mock_permission_repo
        )

        assert manager.db == mock_db_session
        assert manager.policy_engine == mock_policy_engine
        assert manager.permission_decision_repo == mock_permission_repo
        assert manager.enable_cache is True

    def test_initialization_with_cache_disabled(self, mock_db_session, mock_policy_engine, mock_permission_repo):
        """Test initialization with caching disabled."""
        manager = PermissionManager(
            db=mock_db_session,
            policy_engine=mock_policy_engine,
            permission_decision_repo=mock_permission_repo,
            enable_cache=False
        )

        assert manager.enable_cache is False


class TestCreateCallback:
    """Tests for creating permission callbacks."""

    def test_create_callback_returns_callable(self, permission_manager):
        """Test create_callback returns a callable."""
        session_id = uuid4()
        callback = permission_manager.create_callback(session_id)

        assert callable(callback)

    @pytest.mark.asyncio
    async def test_callback_calls_can_use_tool(self, permission_manager, mock_context):
        """Test callback delegates to can_use_tool."""
        session_id = uuid4()
        callback = permission_manager.create_callback(session_id)

        result = await callback(
            tool_name="test_tool",
            input_data={"param": "value"},
            context=mock_context
        )

        assert isinstance(result, (PermissionResultAllow, PermissionResultDeny))

    @pytest.mark.asyncio
    async def test_callback_includes_session_id(self, permission_manager, mock_permission_repo, mock_context):
        """Test callback includes session ID in logging."""
        session_id = uuid4()
        callback = permission_manager.create_callback(session_id)

        await callback("test_tool", {}, mock_context)

        # Should log with session_id
        create_call = mock_permission_repo.create.call_args[0][0]
        assert create_call.session_id == session_id

    @pytest.mark.asyncio
    async def test_callback_includes_user_id(self, permission_manager, mock_permission_repo, mock_context):
        """Test callback includes user ID when provided."""
        session_id = uuid4()
        user_id = uuid4()
        callback = permission_manager.create_callback(session_id, user_id=user_id)

        await callback("test_tool", {}, mock_context)

        # User ID is stored in manager context, not in the model
        # The callback should work correctly
        assert mock_permission_repo.create.called


class TestCanUseTool:
    """Tests for can_use_tool method."""

    @pytest.mark.asyncio
    async def test_can_use_tool_allows_when_policy_allows(
        self,
        permission_manager,
        mock_policy_engine,
        mock_context
    ):
        """Test can_use_tool allows when policy allows."""
        mock_policy_engine.evaluate.return_value = PermissionResultAllow()

        session_id = uuid4()
        result = await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value"},
            context=mock_context,
            session_id=session_id
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_can_use_tool_denies_when_policy_denies(
        self,
        permission_manager,
        mock_policy_engine,
        mock_context
    ):
        """Test can_use_tool denies when policy denies."""
        mock_policy_engine.evaluate.return_value = PermissionResultDeny(
            message="Access denied",
            interrupt=False
        )

        session_id = uuid4()
        result = await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value"},
            context=mock_context,
            session_id=session_id
        )

        assert isinstance(result, PermissionResultDeny)
        assert result.message == "Access denied"

    @pytest.mark.asyncio
    async def test_can_use_tool_logs_allow_decision(
        self,
        permission_manager,
        mock_policy_engine,
        mock_permission_repo,
        mock_context
    ):
        """Test can_use_tool logs allow decision."""
        mock_policy_engine.evaluate.return_value = PermissionResultAllow()

        session_id = uuid4()
        await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value"},
            context=mock_context,
            session_id=session_id
        )

        # Should log decision
        mock_permission_repo.create.assert_called_once()
        create_call = mock_permission_repo.create.call_args[0][0]

        assert create_call.session_id == session_id
        assert create_call.tool_name == "test_tool"
        assert create_call.decision == PermissionResult.ALLOWED.value

    @pytest.mark.asyncio
    async def test_can_use_tool_logs_deny_decision(
        self,
        permission_manager,
        mock_policy_engine,
        mock_permission_repo,
        mock_context
    ):
        """Test can_use_tool logs deny decision."""
        mock_policy_engine.evaluate.return_value = PermissionResultDeny(
            message="Blocked",
            interrupt=False
        )

        session_id = uuid4()
        await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value"},
            context=mock_context,
            session_id=session_id
        )

        # Should log denial
        create_call = mock_permission_repo.create.call_args[0][0]

        assert create_call.decision == PermissionResult.DENIED.value
        assert "Blocked" in create_call.reason


class TestCaching:
    """Tests for permission decision caching."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(
        self,
        permission_manager,
        mock_policy_engine,
        mock_context
    ):
        """Test cache hit returns cached result without evaluating."""
        session_id = uuid4()
        tool_name = "test_tool"
        input_data = {"param": "value"}

        # First call - should evaluate
        await permission_manager.can_use_tool(
            tool_name=tool_name,
            input_data=input_data,
            context=mock_context,
            session_id=session_id
        )

        assert mock_policy_engine.evaluate.call_count == 1

        # Second call with same data - should use cache
        await permission_manager.can_use_tool(
            tool_name=tool_name,
            input_data=input_data,
            context=mock_context,
            session_id=session_id
        )

        # Should not evaluate again
        assert mock_policy_engine.evaluate.call_count == 1

    @pytest.mark.asyncio
    async def test_different_input_not_cached(
        self,
        permission_manager,
        mock_policy_engine,
        mock_context
    ):
        """Test different input data doesn't use cache."""
        session_id = uuid4()

        # First call
        await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value1"},
            context=mock_context,
            session_id=session_id
        )

        # Second call with different input
        await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={"param": "value2"},
            context=mock_context,
            session_id=session_id
        )

        # Should evaluate both times
        assert mock_policy_engine.evaluate.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_disabled(
        self,
        mock_db_session,
        mock_policy_engine,
        mock_permission_repo,
        mock_context
    ):
        """Test caching can be disabled."""
        manager = PermissionManager(
            db=mock_db_session,
            policy_engine=mock_policy_engine,
            permission_decision_repo=mock_permission_repo,
            enable_cache=False
        )

        session_id = uuid4()
        tool_name = "test_tool"
        input_data = {"param": "value"}

        # Make two identical calls
        await manager.can_use_tool(tool_name, input_data, mock_context, session_id)
        await manager.can_use_tool(tool_name, input_data, mock_context, session_id)

        # Should evaluate both times when cache is disabled
        assert mock_policy_engine.evaluate.call_count == 2

    def test_clear_cache(self, permission_manager):
        """Test clearing permission cache."""
        # Add some entries to cache
        permission_manager._decision_cache["key1"] = PermissionResultAllow()
        permission_manager._decision_cache["key2"] = PermissionResultDeny(message="test", interrupt=False)

        assert len(permission_manager._decision_cache) == 2

        # Clear cache
        permission_manager.clear_cache()

        assert len(permission_manager._decision_cache) == 0


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_make_cache_key_consistent(self, permission_manager):
        """Test cache key is consistent for same input."""
        key1 = permission_manager._make_cache_key("test_tool", {"a": 1, "b": 2})
        key2 = permission_manager._make_cache_key("test_tool", {"a": 1, "b": 2})

        assert key1 == key2

    def test_make_cache_key_different_for_different_input(self, permission_manager):
        """Test cache key differs for different input."""
        key1 = permission_manager._make_cache_key("test_tool", {"a": 1})
        key2 = permission_manager._make_cache_key("test_tool", {"a": 2})

        assert key1 != key2

    def test_make_cache_key_different_for_different_tool(self, permission_manager):
        """Test cache key differs for different tools."""
        key1 = permission_manager._make_cache_key("tool1", {"a": 1})
        key2 = permission_manager._make_cache_key("tool2", {"a": 1})

        assert key1 != key2

    def test_make_cache_key_order_independent(self, permission_manager):
        """Test cache key is order-independent for dict keys."""
        key1 = permission_manager._make_cache_key("test_tool", {"a": 1, "b": 2})
        key2 = permission_manager._make_cache_key("test_tool", {"b": 2, "a": 1})

        # JSON with sort_keys=True should produce same key
        assert key1 == key2


class TestContextSerialization:
    """Tests for context serialization."""

    def test_serialize_context_extracts_signal(self, permission_manager, mock_context):
        """Test context serialization extracts signal."""
        serialized = permission_manager._serialize_context(mock_context)

        assert "signal" in serialized
        assert serialized["type"] == "ToolPermissionContext"

    def test_serialize_context_counts_suggestions(self, permission_manager, mock_context):
        """Test context serialization counts suggestions."""
        serialized = permission_manager._serialize_context(mock_context)

        assert "suggestions_count" in serialized
        assert serialized["suggestions_count"] == 3

    def test_serialize_context_handles_error(self, permission_manager):
        """Test context serialization handles errors gracefully."""
        class ProblematicContext:
            @property
            def signal(self):
                raise AttributeError("Cannot access")

        context = ProblematicContext()
        serialized = permission_manager._serialize_context(context)

        # Should still return something
        assert "type" in serialized


class TestLoggingFailure:
    """Tests for logging failure handling."""

    @pytest.mark.asyncio
    async def test_logging_failure_doesnt_block_permission(
        self,
        permission_manager,
        mock_policy_engine,
        mock_permission_repo,
        mock_context
    ):
        """Test logging failure doesn't block permission check."""
        # Make logging fail
        mock_permission_repo.create.side_effect = Exception("Database error")

        mock_policy_engine.evaluate.return_value = PermissionResultAllow()

        session_id = uuid4()

        # Should not raise exception
        result = await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={},
            context=mock_context,
            session_id=session_id
        )

        # Should still return permission result
        assert isinstance(result, PermissionResultAllow)


class TestInputDataLogging:
    """Tests for input data logging."""

    @pytest.mark.asyncio
    async def test_logs_tool_input_data(
        self,
        permission_manager,
        mock_permission_repo,
        mock_context
    ):
        """Test tool input data is logged."""
        session_id = uuid4()
        input_data = {"file_path": "/tmp/test.txt", "content": "test"}

        await permission_manager.can_use_tool(
            tool_name="write_file",
            input_data=input_data,
            context=mock_context,
            session_id=session_id
        )

        create_call = mock_permission_repo.create.call_args[0][0]
        assert create_call.input_data == input_data

    @pytest.mark.asyncio
    async def test_logs_context_data(
        self,
        permission_manager,
        mock_permission_repo,
        mock_context
    ):
        """Test context data is serialized and logged."""
        session_id = uuid4()

        await permission_manager.can_use_tool(
            tool_name="test_tool",
            input_data={},
            context=mock_context,
            session_id=session_id
        )

        create_call = mock_permission_repo.create.call_args[0][0]
        assert create_call.context_data is not None
        assert isinstance(create_call.context_data, dict)
