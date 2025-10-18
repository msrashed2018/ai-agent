"""Unit tests for CommandPolicy."""
import pytest
from unittest.mock import AsyncMock

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.policies.command_policy import CommandPolicy


@pytest.fixture
def mock_context():
    """Create mock permission context."""
    return AsyncMock(spec=ToolPermissionContext)


class TestCommandPolicyInitialization:
    """Tests for CommandPolicy initialization."""

    def test_initialization(self):
        """Test policy initializes with blocked patterns."""
        policy = CommandPolicy(
            blocked_patterns=["rm -rf", "sudo rm", "format"]
        )

        assert len(policy.blocked_patterns) == 3
        assert "rm -rf" in policy.blocked_patterns

    def test_initialization_empty_patterns(self):
        """Test policy can be initialized with no patterns."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.blocked_patterns == []

    def test_policy_name(self):
        """Test policy returns correct name."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.policy_name == "command_policy"

    def test_priority(self):
        """Test policy has high priority."""
        policy = CommandPolicy(blocked_patterns=[])

        # Security policies should have high priority
        assert policy.priority == 10


class TestAppliesToTool:
    """Tests for applies_to_tool method."""

    def test_applies_to_bash(self):
        """Test policy applies to bash tool."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.applies_to_tool("bash") is True

    def test_applies_to_bash_capital(self):
        """Test policy applies to Bash tool."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.applies_to_tool("Bash") is True

    def test_not_applies_to_read_file(self):
        """Test policy doesn't apply to read_file."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.applies_to_tool("read_file") is False

    def test_not_applies_to_other_tools(self):
        """Test policy doesn't apply to other tools."""
        policy = CommandPolicy(blocked_patterns=[])

        assert policy.applies_to_tool("write_file") is False
        assert policy.applies_to_tool("list_files") is False


class TestCommandBlocking:
    """Tests for command blocking."""

    @pytest.mark.asyncio
    async def test_safe_command_allowed(self, mock_context):
        """Test safe command is allowed."""
        policy = CommandPolicy(blocked_patterns=["rm -rf", "sudo rm"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "ls -la"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_dangerous_command_blocked(self, mock_context):
        """Test dangerous command is blocked."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "rm -rf /"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert "blocked" in result.message.lower()

    @pytest.mark.asyncio
    async def test_multiple_blocked_patterns(self, mock_context):
        """Test multiple blocked patterns."""
        policy = CommandPolicy(blocked_patterns=[
            "rm -rf",
            "sudo rm",
            "format",
            "> /dev/sda"
        ])

        dangerous_commands = [
            "rm -rf /tmp/*",
            "sudo rm -f /etc/passwd",
            "format c:",
            "dd if=/dev/zero of=/dev/sda"
        ]

        for command in dangerous_commands:
            result = await policy.evaluate(
                tool_name="bash",
                input_data={"command": command},
                context=mock_context
            )

            assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_pattern_matching_case_sensitive(self, mock_context):
        """Test pattern matching is case-sensitive."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        # Exact match blocked
        result1 = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "rm -rf /tmp"},
            context=mock_context
        )
        assert isinstance(result1, PermissionResultDeny)

        # Different case might not be blocked (depends on implementation)
        result2 = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "RM -RF /tmp"},
            context=mock_context
        )
        # This would pass if case-sensitive
        assert isinstance(result2, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_partial_pattern_match(self, mock_context):
        """Test partial pattern matching."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        # Pattern in middle of command
        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "echo 'test' && rm -rf /tmp && echo 'done'"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_empty_command_allowed(self, mock_context):
        """Test empty command is allowed."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": ""},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_no_command_field_allowed(self, mock_context):
        """Test missing command field is allowed."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)


class TestCommonDangerousCommands:
    """Tests for common dangerous command patterns."""

    @pytest.mark.asyncio
    async def test_blocks_recursive_delete(self, mock_context):
        """Test blocks recursive delete commands."""
        policy = CommandPolicy(blocked_patterns=["rm -rf", "rm -fr"])

        dangerous_deletes = [
            "rm -rf /",
            "rm -rf /*",
            "rm -rf /tmp/*",
            "sudo rm -rf /var",
        ]

        for command in dangerous_deletes:
            result = await policy.evaluate(
                tool_name="bash",
                input_data={"command": command},
                context=mock_context
            )
            assert isinstance(result, PermissionResultDeny), f"Should block: {command}"

    @pytest.mark.asyncio
    async def test_blocks_format_commands(self, mock_context):
        """Test blocks disk format commands."""
        policy = CommandPolicy(blocked_patterns=["format", "mkfs"])

        format_commands = [
            "format c:",
            "mkfs.ext4 /dev/sda1",
            "mkfs -t ext4 /dev/sdb",
        ]

        for command in format_commands:
            result = await policy.evaluate(
                tool_name="bash",
                input_data={"command": command},
                context=mock_context
            )
            assert isinstance(result, PermissionResultDeny), f"Should block: {command}"

    @pytest.mark.asyncio
    async def test_blocks_disk_wipe_commands(self, mock_context):
        """Test blocks disk wipe commands."""
        policy = CommandPolicy(blocked_patterns=["dd if=", "> /dev/"])

        wipe_commands = [
            "dd if=/dev/zero of=/dev/sda",
            "cat /dev/urandom > /dev/sda",
        ]

        for command in wipe_commands:
            result = await policy.evaluate(
                tool_name="bash",
                input_data={"command": command},
                context=mock_context
            )
            assert isinstance(result, PermissionResultDeny), f"Should block: {command}"


class TestDenyMessages:
    """Tests for denial messages."""

    @pytest.mark.asyncio
    async def test_denial_includes_pattern(self, mock_context):
        """Test denial message includes blocked pattern."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "rm -rf /tmp"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert "rm -rf" in result.message

    @pytest.mark.asyncio
    async def test_denial_does_not_interrupt(self, mock_context):
        """Test denial doesn't interrupt execution."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "rm -rf /"},
            context=mock_context
        )

        assert result.interrupt is False


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_no_blocked_patterns_allows_all(self, mock_context):
        """Test policy with no patterns allows everything."""
        policy = CommandPolicy(blocked_patterns=[])

        dangerous_commands = [
            "rm -rf /",
            "format c:",
            "dd if=/dev/zero of=/dev/sda"
        ]

        for command in dangerous_commands:
            result = await policy.evaluate(
                tool_name="bash",
                input_data={"command": command},
                context=mock_context
            )
            assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_whitespace_in_pattern(self, mock_context):
        """Test patterns with whitespace."""
        policy = CommandPolicy(blocked_patterns=["rm -rf", "sudo  rm"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "rm -rf /tmp"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_special_characters_in_command(self, mock_context):
        """Test commands with special characters."""
        policy = CommandPolicy(blocked_patterns=["rm -rf"])

        result = await policy.evaluate(
            tool_name="bash",
            input_data={"command": "echo 'test' | grep 'test'"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)
