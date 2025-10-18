"""Unit tests for SDKOptions value object."""

import pytest
from app.domain.value_objects.sdk_options import SDKOptions


class TestSDKOptionsValueObject:
    """Test cases for SDKOptions value object."""

    def test_sdk_options_default_values(self):
        """Test SDKOptions default values."""
        options = SDKOptions()

        assert options.permission_mode == "default"
        assert options.model == "claude-sonnet-4-5"
        assert options.max_turns == 20
        assert options.allowed_tools is None
        assert options.disallowed_tools is None
        assert options.cwd is None
        assert options.mcp_servers is None
        assert options.custom_config is None

    def test_sdk_options_custom_values(self):
        """Test creating SDKOptions with custom values."""
        mcp_servers = {"kubernetes": {"type": "stdio"}}
        allowed_tools = ["read", "write", "list"]

        options = SDKOptions(
            permission_mode="requirePermissions",
            model="claude-opus-4",
            max_turns=50,
            allowed_tools=allowed_tools,
            cwd="/home/user",
            mcp_servers=mcp_servers,
        )

        assert options.permission_mode == "requirePermissions"
        assert options.model == "claude-opus-4"
        assert options.max_turns == 50
        assert options.allowed_tools == allowed_tools
        assert options.cwd == "/home/user"
        assert options.mcp_servers == mcp_servers

    def test_sdk_options_to_dict(self):
        """Test converting SDKOptions to dictionary."""
        options = SDKOptions(
            permission_mode="bypassPermissions",
            model="claude-opus-4",
            max_turns=30,
            allowed_tools=["read", "write"],
        )

        result = options.to_dict()

        assert result["permission_mode"] == "bypassPermissions"
        assert result["model"] == "claude-opus-4"
        assert result["max_turns"] == 30
        assert result["allowed_tools"] == ["read", "write"]

    def test_sdk_options_to_dict_excludes_none_values(self):
        """Test that to_dict excludes None values."""
        options = SDKOptions(
            allowed_tools=None,
            disallowed_tools=None,
            cwd=None,
        )

        result = options.to_dict()

        assert "allowed_tools" not in result
        assert "disallowed_tools" not in result
        assert "cwd" not in result

    def test_sdk_options_to_dict_includes_set_values(self):
        """Test that to_dict includes explicitly set values."""
        options = SDKOptions(
            allowed_tools=["read"],
            cwd="/tmp",
        )

        result = options.to_dict()

        assert "allowed_tools" in result
        assert "cwd" in result
        assert result["allowed_tools"] == ["read"]
        assert result["cwd"] == "/tmp"

    def test_sdk_options_from_dict(self):
        """Test creating SDKOptions from dictionary."""
        data = {
            "permission_mode": "requirePermissions",
            "model": "claude-opus-4",
            "max_turns": 25,
            "allowed_tools": ["execute"],
            "cwd": "/workspace",
        }

        options = SDKOptions.from_dict(data)

        assert options.permission_mode == "requirePermissions"
        assert options.model == "claude-opus-4"
        assert options.max_turns == 25
        assert options.allowed_tools == ["execute"]
        assert options.cwd == "/workspace"

    def test_sdk_options_from_dict_with_defaults(self):
        """Test from_dict applies defaults for missing values."""
        data = {
            "model": "claude-sonnet-4-5",
        }

        options = SDKOptions.from_dict(data)

        assert options.permission_mode == "default"
        assert options.model == "claude-sonnet-4-5"
        assert options.max_turns == 20

    def test_sdk_options_from_dict_with_extra_fields(self):
        """Test from_dict handles extra fields as custom config."""
        data = {
            "permission_mode": "default",
            "model": "claude-opus-4",
            "max_turns": 20,
            "custom_param1": "value1",
            "custom_param2": 123,
        }

        options = SDKOptions.from_dict(data)

        assert options.custom_config["custom_param1"] == "value1"
        assert options.custom_config["custom_param2"] == 123

    def test_sdk_options_with_permission_mode(self):
        """Test creating new instance with different permission mode."""
        original = SDKOptions(permission_mode="default")
        updated = original.with_permission_mode("requirePermissions")

        assert original.permission_mode == "default"
        assert updated.permission_mode == "requirePermissions"

    def test_sdk_options_with_model(self):
        """Test creating new instance with different model."""
        original = SDKOptions(model="claude-sonnet-4-5")
        updated = original.with_model("claude-opus-4")

        assert original.model == "claude-sonnet-4-5"
        assert updated.model == "claude-opus-4"

    def test_sdk_options_with_tools(self):
        """Test creating new instance with updated tools."""
        original = SDKOptions(
            allowed_tools=["read"],
            disallowed_tools=None
        )

        updated = original.with_tools(
            allowed_tools=["read", "write"],
            disallowed_tools=["delete"]
        )

        assert original.allowed_tools == ["read"]
        assert updated.allowed_tools == ["read", "write"]
        assert updated.disallowed_tools == ["delete"]

    def test_sdk_options_immutability(self):
        """Test that SDKOptions is immutable (frozen dataclass)."""
        options = SDKOptions()

        with pytest.raises((AttributeError, TypeError)):
            options.model = "claude-opus-4"

    def test_sdk_options_with_mcp_servers(self):
        """Test SDKOptions with MCP server configuration."""
        mcp_config = {
            "kubernetes_readonly": {
                "command": "python",
                "args": ["-m", "kubemind.mcp.kubernetes"],
                "env": {"K8S_CONTEXT": "prod"},
            },
            "database": {
                "command": "python",
                "args": ["-m", "kubemind.mcp.database"],
            },
        }

        options = SDKOptions(mcp_servers=mcp_config)

        assert options.mcp_servers == mcp_config
        assert "kubernetes_readonly" in options.mcp_servers
        assert "database" in options.mcp_servers

    def test_sdk_options_to_dict_with_mcp_servers(self):
        """Test to_dict includes MCP servers."""
        mcp_config = {"kubernetes": {"command": "python"}}
        options = SDKOptions(mcp_servers=mcp_config)

        result = options.to_dict()
        assert result["mcp_servers"] == mcp_config

    def test_sdk_options_with_custom_config(self):
        """Test SDKOptions with custom configuration."""
        custom_config = {
            "log_level": "DEBUG",
            "timeout": 60,
            "retries": 3,
        }

        options = SDKOptions(custom_config=custom_config)

        assert options.custom_config == custom_config

    def test_sdk_options_to_dict_merges_custom_config(self):
        """Test to_dict merges custom config into result."""
        custom_config = {
            "custom_key": "custom_value",
            "another_key": 123,
        }

        options = SDKOptions(custom_config=custom_config)
        result = options.to_dict()

        assert result["custom_key"] == "custom_value"
        assert result["another_key"] == 123
        assert result["permission_mode"] == "default"  # Default still present

    def test_sdk_options_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = SDKOptions(
            permission_mode="requirePermissions",
            model="claude-opus-4",
            max_turns=40,
            allowed_tools=["read", "write"],
            cwd="/home/user",
        )

        dict_repr = original.to_dict()
        reconstructed = SDKOptions.from_dict(dict_repr)

        assert reconstructed.permission_mode == original.permission_mode
        assert reconstructed.model == original.model
        assert reconstructed.max_turns == original.max_turns
        assert reconstructed.allowed_tools == original.allowed_tools
        assert reconstructed.cwd == original.cwd

    def test_sdk_options_with_disallowed_tools(self):
        """Test SDKOptions with disallowed tools."""
        options = SDKOptions(
            allowed_tools=None,  # All tools allowed
            disallowed_tools=["delete", "execute_shell"],
        )

        assert options.disallowed_tools == ["delete", "execute_shell"]

    def test_sdk_options_permission_modes(self):
        """Test different permission modes."""
        modes = ["default", "bypassPermissions", "requirePermissions"]

        for mode in modes:
            options = SDKOptions(permission_mode=mode)
            assert options.permission_mode == mode
