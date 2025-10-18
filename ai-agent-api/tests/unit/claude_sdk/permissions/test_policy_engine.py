"""Unit tests for PolicyEngine."""
import pytest
from unittest.mock import AsyncMock
from typing import Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.claude_sdk.permissions.base_policy import BasePolicy


class MockAllowPolicy(BasePolicy):
    """Mock policy that always allows."""

    def __init__(self, applies_to="test_tool", priority=100):
        self._applies_to = applies_to
        self._priority = priority

    @property
    def policy_name(self) -> str:
        return "mock_allow_policy"

    @property
    def priority(self) -> int:
        return self._priority

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name == self._applies_to

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        return PermissionResultAllow()


class MockDenyPolicy(BasePolicy):
    """Mock policy that always denies."""

    def __init__(self, applies_to="test_tool", priority=100, message="Denied"):
        self._applies_to = applies_to
        self._priority = priority
        self._message = message

    @property
    def policy_name(self) -> str:
        return "mock_deny_policy"

    @property
    def priority(self) -> int:
        return self._priority

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name == self._applies_to

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        return PermissionResultDeny(message=self._message, interrupt=False)


class MockErrorPolicy(BasePolicy):
    """Mock policy that raises an error."""

    @property
    def policy_name(self) -> str:
        return "mock_error_policy"

    def applies_to_tool(self, tool_name: str) -> bool:
        return True

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        raise ValueError("Policy evaluation failed")


@pytest.fixture
def policy_engine():
    """Create PolicyEngine instance."""
    return PolicyEngine()


@pytest.fixture
def mock_context():
    """Create mock permission context."""
    context = AsyncMock(spec=ToolPermissionContext)
    return context


class TestPolicyEngineInitialization:
    """Tests for PolicyEngine initialization."""

    def test_initialization(self):
        """Test PolicyEngine initializes with empty policies."""
        engine = PolicyEngine()

        assert engine._policies == []

    def test_get_policy_count_empty(self, policy_engine):
        """Test getting count from empty engine."""
        assert policy_engine.get_policy_count() == 0


class TestPolicyRegistration:
    """Tests for policy registration."""

    def test_register_single_policy(self, policy_engine):
        """Test registering a single policy."""
        policy = MockAllowPolicy()

        policy_engine.register_policy(policy)

        assert policy_engine.get_policy_count() == 1

    def test_register_multiple_policies(self, policy_engine):
        """Test registering multiple policies."""
        policy1 = MockAllowPolicy(applies_to="tool1")
        policy2 = MockAllowPolicy(applies_to="tool2")
        policy3 = MockAllowPolicy(applies_to="tool3")

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)
        policy_engine.register_policy(policy3)

        assert policy_engine.get_policy_count() == 3

    def test_policies_sorted_by_priority_on_registration(self, policy_engine):
        """Test policies are sorted by priority when registered."""
        policy1 = MockAllowPolicy(applies_to="tool1", priority=100)
        policy2 = MockAllowPolicy(applies_to="tool2", priority=50)
        policy3 = MockAllowPolicy(applies_to="tool3", priority=200)

        # Register in non-priority order
        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy3)
        policy_engine.register_policy(policy2)

        # Should be sorted by priority
        policies = policy_engine._policies
        assert policies[0].priority == 50
        assert policies[1].priority == 100
        assert policies[2].priority == 200

    def test_clear_policies(self, policy_engine):
        """Test clearing all policies."""
        policy1 = MockAllowPolicy()
        policy2 = MockAllowPolicy()

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)

        assert policy_engine.get_policy_count() == 2

        policy_engine.clear_policies()

        assert policy_engine.get_policy_count() == 0


class TestGetPolicies:
    """Tests for getting applicable policies."""

    def test_get_policies_for_tool(self, policy_engine):
        """Test getting policies that apply to specific tool."""
        policy1 = MockAllowPolicy(applies_to="read_file")
        policy2 = MockAllowPolicy(applies_to="write_file")
        policy3 = MockAllowPolicy(applies_to="read_file")

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)
        policy_engine.register_policy(policy3)

        read_policies = policy_engine.get_policies("read_file")
        write_policies = policy_engine.get_policies("write_file")

        assert len(read_policies) == 2
        assert len(write_policies) == 1

    def test_get_policies_no_matches(self, policy_engine):
        """Test getting policies when none apply."""
        policy = MockAllowPolicy(applies_to="read_file")
        policy_engine.register_policy(policy)

        policies = policy_engine.get_policies("bash")

        assert policies == []

    def test_get_policies_returns_in_priority_order(self, policy_engine):
        """Test policies are returned in priority order."""
        policy1 = MockAllowPolicy(applies_to="test_tool", priority=100)
        policy2 = MockAllowPolicy(applies_to="test_tool", priority=10)
        policy3 = MockAllowPolicy(applies_to="test_tool", priority=50)

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)
        policy_engine.register_policy(policy3)

        policies = policy_engine.get_policies("test_tool")

        # Should be in priority order (lowest first)
        assert policies[0].priority == 10
        assert policies[1].priority == 50
        assert policies[2].priority == 100


class TestPolicyEvaluation:
    """Tests for policy evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_no_policies(self, policy_engine, mock_context):
        """Test evaluation with no policies allows by default."""
        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_single_allow_policy(self, policy_engine, mock_context):
        """Test evaluation with single allowing policy."""
        policy = MockAllowPolicy(applies_to="test_tool")
        policy_engine.register_policy(policy)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_single_deny_policy(self, policy_engine, mock_context):
        """Test evaluation with single denying policy."""
        policy = MockDenyPolicy(applies_to="test_tool", message="Access denied")
        policy_engine.register_policy(policy)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert result.message == "Access denied"

    @pytest.mark.asyncio
    async def test_evaluate_multiple_allow_policies(self, policy_engine, mock_context):
        """Test evaluation with multiple allowing policies."""
        policy1 = MockAllowPolicy(applies_to="test_tool", priority=10)
        policy2 = MockAllowPolicy(applies_to="test_tool", priority=20)

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_stops_on_first_deny(self, policy_engine, mock_context):
        """Test evaluation stops on first denial."""
        policy1 = MockAllowPolicy(applies_to="test_tool", priority=10)
        policy2 = MockDenyPolicy(applies_to="test_tool", priority=20, message="Blocked")
        policy3 = MockAllowPolicy(applies_to="test_tool", priority=30)

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)
        policy_engine.register_policy(policy3)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        # Should deny from policy2
        assert isinstance(result, PermissionResultDeny)
        assert result.message == "Blocked"

    @pytest.mark.asyncio
    async def test_evaluate_deny_with_high_priority_stops_early(self, policy_engine, mock_context):
        """Test high-priority denial stops evaluation immediately."""
        # High priority deny (runs first)
        policy1 = MockDenyPolicy(applies_to="test_tool", priority=10, message="High priority deny")
        # Low priority allow (should not run)
        policy2 = MockAllowPolicy(applies_to="test_tool", priority=100)

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert result.message == "High priority deny"

    @pytest.mark.asyncio
    async def test_evaluate_no_applicable_policies(self, policy_engine, mock_context):
        """Test evaluation when no policies apply to tool."""
        policy = MockAllowPolicy(applies_to="read_file")
        policy_engine.register_policy(policy)

        result = await policy_engine.evaluate(
            tool_name="bash",
            input_data={},
            context=mock_context
        )

        # Should allow by default
        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_handles_policy_error(self, policy_engine, mock_context):
        """Test evaluation continues when policy raises error."""
        policy1 = MockErrorPolicy()
        policy2 = MockAllowPolicy(applies_to="test_tool")

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)

        # Should not raise exception
        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        # Should allow from policy2
        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_all_policies_error_allows(self, policy_engine, mock_context):
        """Test evaluation allows if all policies error."""
        policy1 = MockErrorPolicy()
        policy2 = MockErrorPolicy()

        policy_engine.register_policy(policy1)
        policy_engine.register_policy(policy2)

        result = await policy_engine.evaluate(
            tool_name="test_tool",
            input_data={},
            context=mock_context
        )

        # Should allow when all policies fail
        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_evaluate_with_input_data(self, policy_engine, mock_context):
        """Test evaluation passes input data to policies."""
        class InputCheckingPolicy(BasePolicy):
            @property
            def policy_name(self):
                return "input_checker"

            def applies_to_tool(self, tool_name):
                return True

            async def evaluate(self, tool_name, input_data, context):
                # Check if dangerous path
                if input_data.get("path") == "/etc/passwd":
                    return PermissionResultDeny(message="Dangerous path", interrupt=False)
                return PermissionResultAllow()

        policy = InputCheckingPolicy()
        policy_engine.register_policy(policy)

        # Test with dangerous path
        result1 = await policy_engine.evaluate(
            tool_name="read_file",
            input_data={"path": "/etc/passwd"},
            context=mock_context
        )

        assert isinstance(result1, PermissionResultDeny)

        # Test with safe path
        result2 = await policy_engine.evaluate(
            tool_name="read_file",
            input_data={"path": "/tmp/safe.txt"},
            context=mock_context
        )

        assert isinstance(result2, PermissionResultAllow)
