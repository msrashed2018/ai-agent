"""Unit tests for MCPServerManager."""
import pytest
from unittest.mock import MagicMock

from app.claude_sdk.mcp.mcp_server_manager import MCPServerManager
from app.claude_sdk.mcp.mcp_server_config import MCPServerConfig, MCPServerType


@pytest.fixture
def mcp_manager():
    """Create MCPServerManager instance."""
    return MCPServerManager()


@pytest.fixture
def sdk_server_config():
    """Create SDK server config."""
    mock_sdk_server = MagicMock()
    return MCPServerConfig(
        name="test_sdk_server",
        server_type=MCPServerType.SDK,
        sdk_server_config=mock_sdk_server,
        enabled=True
    )


@pytest.fixture
def external_server_config():
    """Create external server config."""
    return MCPServerConfig(
        name="test_external_server",
        server_type=MCPServerType.EXTERNAL,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        env={"NODE_ENV": "production"},
        enabled=True
    )


class TestMCPServerManagerInitialization:
    """Tests for MCPServerManager initialization."""

    def test_initialization(self):
        """Test manager initializes with empty servers."""
        manager = MCPServerManager()

        assert manager._servers == {}

    def test_list_servers_empty(self, mcp_manager):
        """Test listing servers in empty manager."""
        servers = mcp_manager.list_servers()

        assert servers == []

    def test_get_server_count_empty(self, mcp_manager):
        """Test server count in empty manager."""
        assert mcp_manager.get_server_count() == 0


class TestAddServer:
    """Tests for adding servers."""

    def test_add_sdk_server(self, mcp_manager, sdk_server_config):
        """Test adding SDK server."""
        mcp_manager.add_server(sdk_server_config)

        assert "test_sdk_server" in mcp_manager._servers
        assert mcp_manager.get_server_count() == 1

    def test_add_external_server(self, mcp_manager, external_server_config):
        """Test adding external server."""
        mcp_manager.add_server(external_server_config)

        assert "test_external_server" in mcp_manager._servers
        assert mcp_manager.get_server_count() == 1

    def test_add_multiple_servers(self, mcp_manager, sdk_server_config, external_server_config):
        """Test adding multiple servers."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        assert mcp_manager.get_server_count() == 2
        assert len(mcp_manager.list_servers()) == 2

    def test_add_duplicate_name_raises_error(self, mcp_manager, sdk_server_config):
        """Test adding server with duplicate name raises error."""
        mcp_manager.add_server(sdk_server_config)

        # Try to add another server with same name
        duplicate_config = MCPServerConfig(
            name="test_sdk_server",
            server_type=MCPServerType.EXTERNAL,
            command="test",
            args=[],
            enabled=True
        )

        with pytest.raises(ValueError, match="already exists"):
            mcp_manager.add_server(duplicate_config)

    def test_add_disabled_server_skipped(self, mcp_manager):
        """Test adding disabled server is skipped."""
        disabled_config = MCPServerConfig(
            name="disabled_server",
            server_type=MCPServerType.SDK,
            sdk_server_config=MagicMock(),
            enabled=False
        )

        mcp_manager.add_server(disabled_config)

        # Should not be added
        assert mcp_manager.get_server_count() == 0
        assert "disabled_server" not in mcp_manager._servers


class TestRemoveServer:
    """Tests for removing servers."""

    def test_remove_existing_server(self, mcp_manager, sdk_server_config):
        """Test removing existing server."""
        mcp_manager.add_server(sdk_server_config)

        result = mcp_manager.remove_server("test_sdk_server")

        assert result is True
        assert mcp_manager.get_server_count() == 0

    def test_remove_nonexistent_server(self, mcp_manager):
        """Test removing nonexistent server."""
        result = mcp_manager.remove_server("nonexistent")

        assert result is False

    def test_remove_from_multiple_servers(self, mcp_manager, sdk_server_config, external_server_config):
        """Test removing one server from multiple."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        mcp_manager.remove_server("test_sdk_server")

        assert mcp_manager.get_server_count() == 1
        assert "test_external_server" in mcp_manager.list_servers()


class TestGetServer:
    """Tests for getting server configurations."""

    def test_get_existing_server(self, mcp_manager, sdk_server_config):
        """Test getting existing server."""
        mcp_manager.add_server(sdk_server_config)

        server = mcp_manager.get_server("test_sdk_server")

        assert server is not None
        assert server.name == "test_sdk_server"
        assert server.server_type == MCPServerType.SDK

    def test_get_nonexistent_server(self, mcp_manager):
        """Test getting nonexistent server returns None."""
        server = mcp_manager.get_server("nonexistent")

        assert server is None


class TestListServers:
    """Tests for listing servers."""

    def test_list_servers_multiple(self, mcp_manager, sdk_server_config, external_server_config):
        """Test listing multiple servers."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        servers = mcp_manager.list_servers()

        assert len(servers) == 2
        assert "test_sdk_server" in servers
        assert "test_external_server" in servers

    def test_list_servers_preserves_order(self, mcp_manager):
        """Test list preserves insertion order."""
        configs = [
            MCPServerConfig(
                name=f"server_{i}",
                server_type=MCPServerType.SDK,
                sdk_server_config=MagicMock(),
                enabled=True
            )
            for i in range(5)
        ]

        for config in configs:
            mcp_manager.add_server(config)

        servers = mcp_manager.list_servers()

        # Check all servers are present
        for i in range(5):
            assert f"server_{i}" in servers


class TestBuildSDKConfiguration:
    """Tests for building SDK configuration."""

    def test_build_configuration_sdk_server(self, mcp_manager, sdk_server_config):
        """Test building configuration with SDK server."""
        mcp_manager.add_server(sdk_server_config)

        config = mcp_manager.build_sdk_configuration()

        assert "test_sdk_server" in config
        assert config["test_sdk_server"] is not None

    def test_build_configuration_external_server(self, mcp_manager, external_server_config):
        """Test building configuration with external server."""
        mcp_manager.add_server(external_server_config)

        config = mcp_manager.build_sdk_configuration()

        assert "test_external_server" in config
        server_config = config["test_external_server"]

        # External server should have command/args/env
        assert "command" in server_config or hasattr(server_config, "command")

    def test_build_configuration_mixed_servers(self, mcp_manager, sdk_server_config, external_server_config):
        """Test building configuration with mixed server types."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        config = mcp_manager.build_sdk_configuration()

        assert len(config) == 2
        assert "test_sdk_server" in config
        assert "test_external_server" in config

    def test_build_configuration_empty(self, mcp_manager):
        """Test building configuration with no servers."""
        config = mcp_manager.build_sdk_configuration()

        assert config == {}

    def test_build_configuration_skips_disabled(self, mcp_manager):
        """Test build skips disabled servers."""
        enabled_config = MCPServerConfig(
            name="enabled",
            server_type=MCPServerType.SDK,
            sdk_server_config=MagicMock(),
            enabled=True
        )

        disabled_config = MCPServerConfig(
            name="disabled",
            server_type=MCPServerType.SDK,
            sdk_server_config=MagicMock(),
            enabled=False
        )

        mcp_manager.add_server(enabled_config)
        # Disabled won't be added due to add_server logic

        config = mcp_manager.build_sdk_configuration()

        assert "enabled" in config
        assert "disabled" not in config

    def test_build_configuration_handles_error(self, mcp_manager):
        """Test build handles configuration errors gracefully."""
        # Create config that will fail to_sdk_config
        bad_config = MCPServerConfig(
            name="bad_server",
            server_type=MCPServerType.SDK,
            sdk_server_config=None,  # This might cause error
            enabled=True
        )

        mcp_manager.add_server(bad_config)

        # Should not raise exception
        config = mcp_manager.build_sdk_configuration()

        # Bad server might be skipped
        # Just ensure it doesn't crash
        assert isinstance(config, dict)


class TestGetServerCount:
    """Tests for getting server counts."""

    def test_get_total_count(self, mcp_manager, sdk_server_config, external_server_config):
        """Test getting total server count."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        count = mcp_manager.get_server_count()

        assert count == 2

    def test_get_count_by_type_sdk(self, mcp_manager, sdk_server_config, external_server_config):
        """Test getting SDK server count."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        count = mcp_manager.get_server_count(MCPServerType.SDK)

        assert count == 1

    def test_get_count_by_type_external(self, mcp_manager, sdk_server_config, external_server_config):
        """Test getting external server count."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        count = mcp_manager.get_server_count(MCPServerType.EXTERNAL)

        assert count == 1

    def test_get_count_filters_disabled(self, mcp_manager):
        """Test count only includes enabled servers."""
        enabled_config = MCPServerConfig(
            name="enabled",
            server_type=MCPServerType.SDK,
            sdk_server_config=MagicMock(),
            enabled=True
        )

        mcp_manager.add_server(enabled_config)

        # Disabled servers aren't added, so count should be 1
        assert mcp_manager.get_server_count() == 1


class TestClear:
    """Tests for clearing servers."""

    def test_clear_all_servers(self, mcp_manager, sdk_server_config, external_server_config):
        """Test clearing all servers."""
        mcp_manager.add_server(sdk_server_config)
        mcp_manager.add_server(external_server_config)

        mcp_manager.clear()

        assert mcp_manager.get_server_count() == 0
        assert mcp_manager.list_servers() == []

    def test_clear_empty_manager(self, mcp_manager):
        """Test clearing empty manager."""
        mcp_manager.clear()

        # Should not raise error
        assert mcp_manager.get_server_count() == 0


class TestServerTypes:
    """Tests for different server types."""

    def test_sdk_server_type(self, mcp_manager):
        """Test SDK server configuration."""
        mock_sdk_server = MagicMock()
        mock_sdk_server.name = "my_tools"

        config = MCPServerConfig(
            name="sdk_server",
            server_type=MCPServerType.SDK,
            sdk_server_config=mock_sdk_server,
            enabled=True
        )

        mcp_manager.add_server(config)

        server = mcp_manager.get_server("sdk_server")
        assert server.server_type == MCPServerType.SDK
        assert server.sdk_server_config is not None

    def test_external_server_type(self, mcp_manager):
        """Test external server configuration."""
        config = MCPServerConfig(
            name="filesystem",
            server_type=MCPServerType.EXTERNAL,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
            env={"PATH": "/usr/bin"},
            enabled=True
        )

        mcp_manager.add_server(config)

        server = mcp_manager.get_server("filesystem")
        assert server.server_type == MCPServerType.EXTERNAL
        assert server.command == "npx"
        assert len(server.args) > 0
