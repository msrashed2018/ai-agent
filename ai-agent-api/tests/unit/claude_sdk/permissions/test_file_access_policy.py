"""Unit tests for FileAccessPolicy."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.policies.file_access_policy import FileAccessPolicy


@pytest.fixture
def mock_context():
    """Create mock permission context."""
    return AsyncMock(spec=ToolPermissionContext)


class TestFileAccessPolicyInitialization:
    """Tests for FileAccessPolicy initialization."""

    def test_initialization(self):
        """Test policy initializes with paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd", "~/.ssh/"],
            allowed_write_paths=["/tmp/", "/workspace/"]
        )

        assert len(policy.restricted_read_paths) == 2
        assert len(policy.allowed_write_paths) == 2

    def test_initialization_expands_tilde(self):
        """Test policy expands ~ in paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=["~/.ssh/"],
            allowed_write_paths=["~/workspace/"]
        )

        # Paths should be expanded
        for path in policy.restricted_read_paths:
            assert "~" not in str(path)

        for path in policy.allowed_write_paths:
            assert "~" not in str(path)

    def test_policy_name(self):
        """Test policy returns correct name."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.policy_name == "file_access_policy"

    def test_priority(self):
        """Test policy has high priority."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        # Security policies should have high priority
        assert policy.priority == 10


class TestAppliesToTool:
    """Tests for applies_to_tool method."""

    def test_applies_to_read_file(self):
        """Test policy applies to read_file tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("read_file") is True

    def test_applies_to_read_capital(self):
        """Test policy applies to Read tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("Read") is True

    def test_applies_to_write_file(self):
        """Test policy applies to write_file tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("write_file") is True

    def test_applies_to_write_capital(self):
        """Test policy applies to Write tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("Write") is True

    def test_applies_to_edit(self):
        """Test policy applies to Edit tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("Edit") is True

    def test_not_applies_to_bash(self):
        """Test policy doesn't apply to bash tool."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("bash") is False

    def test_not_applies_to_other_tools(self):
        """Test policy doesn't apply to other tools."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=[]
        )

        assert policy.applies_to_tool("list_files") is False
        assert policy.applies_to_tool("execute_query") is False


class TestReadRestrictions:
    """Tests for read file restrictions."""

    @pytest.mark.asyncio
    async def test_read_unrestricted_file_allowed(self, mock_context):
        """Test reading unrestricted file is allowed."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd", "/etc/shadow"],
            allowed_write_paths=[]
        )

        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "/tmp/test.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_read_restricted_file_denied(self, mock_context):
        """Test reading restricted file is denied."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd"],
            allowed_write_paths=[]
        )

        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "/etc/passwd"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert "restricted" in result.message.lower()

    @pytest.mark.asyncio
    async def test_read_file_in_restricted_directory_denied(self, mock_context):
        """Test reading file in restricted directory is denied."""
        policy = FileAccessPolicy(
            restricted_read_paths=["~/.ssh/"],
            allowed_write_paths=[]
        )

        # Expand home directory for test
        from pathlib import Path
        ssh_dir = Path("~/.ssh/").expanduser()
        test_file = str(ssh_dir / "id_rsa")

        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": test_file},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_read_multiple_restricted_paths(self, mock_context):
        """Test multiple restricted paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd", "/etc/shadow", "~/.ssh/"],
            allowed_write_paths=[]
        )

        # All should be denied
        restricted_files = ["/etc/passwd", "/etc/shadow"]

        for file_path in restricted_files:
            result = await policy.evaluate(
                tool_name="read_file",
                input_data={"file_path": file_path},
                context=mock_context
            )

            assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_read_with_path_field(self, mock_context):
        """Test read with 'path' field instead of 'file_path'."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd"],
            allowed_write_paths=[]
        )

        result = await policy.evaluate(
            tool_name="Read",
            input_data={"path": "/etc/passwd"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_read_with_no_path_allows(self, mock_context):
        """Test read with no path specified allows."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd"],
            allowed_write_paths=[]
        )

        result = await policy.evaluate(
            tool_name="read_file",
            input_data={},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)


class TestWriteRestrictions:
    """Tests for write file restrictions."""

    @pytest.mark.asyncio
    async def test_write_to_allowed_path_succeeds(self, mock_context):
        """Test writing to allowed path succeeds."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/", "/workspace/"]
        )

        result = await policy.evaluate(
            tool_name="write_file",
            input_data={"file_path": "/tmp/output.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_write_to_disallowed_path_denied(self, mock_context):
        """Test writing to disallowed path is denied."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/"]
        )

        result = await policy.evaluate(
            tool_name="write_file",
            input_data={"file_path": "/etc/config.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert "not allowed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_write_within_allowed_directory(self, mock_context):
        """Test writing file within allowed directory."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/workspace/"]
        )

        result = await policy.evaluate(
            tool_name="write_file",
            input_data={"file_path": "/workspace/project/file.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_write_to_multiple_allowed_paths(self, mock_context):
        """Test writing to various allowed paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/", "/workspace/", "/var/log/"]
        )

        allowed_files = [
            "/tmp/test.txt",
            "/workspace/code.py",
            "/var/log/app.log"
        ]

        for file_path in allowed_files:
            result = await policy.evaluate(
                tool_name="write_file",
                input_data={"file_path": file_path},
                context=mock_context
            )

            assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_edit_uses_write_restrictions(self, mock_context):
        """Test Edit tool uses write restrictions."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/"]
        )

        # Edit to allowed path - allowed
        result1 = await policy.evaluate(
            tool_name="Edit",
            input_data={"file_path": "/tmp/file.txt"},
            context=mock_context
        )

        assert isinstance(result1, PermissionResultAllow)

        # Edit to disallowed path - denied
        result2 = await policy.evaluate(
            tool_name="Edit",
            input_data={"file_path": "/etc/file.txt"},
            context=mock_context
        )

        assert isinstance(result2, PermissionResultDeny)

    @pytest.mark.asyncio
    async def test_write_with_path_field(self, mock_context):
        """Test write with 'path' field instead of 'file_path'."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/"]
        )

        result = await policy.evaluate(
            tool_name="Write",
            input_data={"path": "/tmp/output.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)


class TestDenyMessages:
    """Tests for denial messages."""

    @pytest.mark.asyncio
    async def test_read_denial_includes_file_path(self, mock_context):
        """Test read denial message includes file path."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd"],
            allowed_write_paths=[]
        )

        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "/etc/passwd"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        assert "/etc/passwd" in result.message

    @pytest.mark.asyncio
    async def test_write_denial_includes_allowed_paths(self, mock_context):
        """Test write denial message includes allowed paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/", "/workspace/"]
        )

        result = await policy.evaluate(
            tool_name="write_file",
            input_data={"file_path": "/etc/config.txt"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultDeny)
        # Message should mention allowed paths
        assert "allowed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_denial_does_not_interrupt(self, mock_context):
        """Test denials don't interrupt execution."""
        policy = FileAccessPolicy(
            restricted_read_paths=["/etc/passwd"],
            allowed_write_paths=["/tmp/"]
        )

        # Test read denial
        result1 = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "/etc/passwd"},
            context=mock_context
        )

        assert result1.interrupt is False

        # Test write denial
        result2 = await policy.evaluate(
            tool_name="write_file",
            input_data={"file_path": "/etc/config.txt"},
            context=mock_context
        )

        assert result2.interrupt is False


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_restricted_paths(self, mock_context):
        """Test policy with no restricted paths."""
        policy = FileAccessPolicy(
            restricted_read_paths=[],
            allowed_write_paths=["/tmp/"]
        )

        # Any read should be allowed
        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "/etc/passwd"},
            context=mock_context
        )

        assert isinstance(result, PermissionResultAllow)

    @pytest.mark.asyncio
    async def test_tilde_expansion_in_runtime(self, mock_context):
        """Test tilde is expanded at runtime."""
        policy = FileAccessPolicy(
            restricted_read_paths=["~/.aws/credentials"],
            allowed_write_paths=[]
        )

        # User passes path with tilde
        result = await policy.evaluate(
            tool_name="read_file",
            input_data={"file_path": "~/.aws/credentials"},
            context=mock_context
        )

        # Should still be blocked
        assert isinstance(result, PermissionResultDeny)
