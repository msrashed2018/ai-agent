"""Unit tests for MCP Configuration Builder."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.mcp.config_builder import MCPConfigBuilder
from app.mcp.sdk_tools import SDK_MCP_SERVERS
from app.models.mcp_server import MCPServerModel


class TestMCPConfigBuilder:
    """Test cases for MCPConfigBuilder."""

    @pytest.fixture
    def mcp_config_builder(self):
        """Create MCPConfigBuilder with mocked repository."""
        mock_repo = AsyncMock()
        return MCPConfigBuilder(mock_repo)

    @pytest.fixture
    def sample_user_servers(self):
        """Sample user MCP servers from database."""
        return [
            MCPServerModel(
                id=uuid4(),
                user_id=uuid4(),
                name="user_filesystem",
                description="User filesystem server",
                config_type="stdio",
                config={
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-filesystem", "/path/to/files"],
                },
                is_enabled=True,
                is_global=False,
            ),
            MCPServerModel(
                id=uuid4(),
                user_id=uuid4(),
                name="user_github",
                description="User GitHub server",
                config_type="stdio",
                config={
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "user_token"},
                },
                is_enabled=True,
                is_global=False,
            ),
        ]

    @pytest.fixture
    def sample_global_servers(self):
        """Sample global MCP servers from database."""
        return [
            MCPServerModel(
                id=uuid4(),
                user_id=None,
                name="global_brave_search",
                description="Global Brave Search server",
                config_type="stdio",
                config={
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-brave-search"],
                    "env": {"BRAVE_API_KEY": "global_key"},
                },
                is_enabled=True,
                is_global=True,
            ),
        ]

    @pytest.mark.asyncio
    async def test_build_user_mcp_config_with_servers(
        self,
        mcp_config_builder,
        sample_user_servers,
        sample_global_servers,
    ):
        """Test building user MCP config with user and global servers."""
        # Arrange
        user_id = uuid4()
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = sample_user_servers
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = sample_global_servers
        
        # Act
        config = await mcp_config_builder.build_user_mcp_config(user_id)
        
        # Assert
        assert "user_filesystem" in config
        assert "user_github" in config
        assert "global_brave_search" in config
        
        # Verify filesystem server config
        filesystem_config = config["user_filesystem"]
        assert filesystem_config["command"] == "npx"
        assert "@modelcontextprotocol/server-filesystem" in filesystem_config["args"]
        
        # Verify repository calls
        mcp_config_builder.mcp_server_repo.get_by_user.assert_called_once_with(user_id)
        mcp_config_builder.mcp_server_repo.get_global_enabled.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_user_mcp_config_empty(
        self,
        mcp_config_builder,
    ):
        """Test building user MCP config with no servers."""
        # Arrange
        user_id = uuid4()
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = []
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = []
        
        # Act
        config = await mcp_config_builder.build_user_mcp_config(user_id)
        
        # Assert
        assert config == {}

    @pytest.mark.asyncio
    async def test_build_session_mcp_config_with_sdk_tools(
        self,
        mcp_config_builder,
        sample_user_servers,
    ):
        """Test building session MCP config including SDK tools."""
        # Arrange
        user_id = uuid4()
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = sample_user_servers
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = []
        
        # Act
        config = await mcp_config_builder.build_session_mcp_config(
            user_id=user_id,
            include_sdk_tools=True,
        )
        
        # Assert
        # Should include SDK tools
        assert "kubernetes_readonly" in config
        assert "database" in config
        assert "monitoring" in config
        
        # Should include user servers
        assert "user_filesystem" in config
        assert "user_github" in config
        
        # Verify SDK tool config structure
        k8s_config = config["kubernetes_readonly"]
        assert "tools" in k8s_config
        assert len(k8s_config["tools"]) > 0

    @pytest.mark.asyncio
    async def test_build_session_mcp_config_without_sdk_tools(
        self,
        mcp_config_builder,
        sample_user_servers,
    ):
        """Test building session MCP config without SDK tools."""
        # Arrange
        user_id = uuid4()
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = sample_user_servers
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = []
        
        # Act
        config = await mcp_config_builder.build_session_mcp_config(
            user_id=user_id,
            include_sdk_tools=False,
        )
        
        # Assert
        # Should NOT include SDK tools
        assert "kubernetes_readonly" not in config
        assert "database" not in config
        assert "monitoring" not in config
        
        # Should include user servers
        assert "user_filesystem" in config
        assert "user_github" in config

    def test_convert_to_sdk_format_stdio(self, mcp_config_builder):
        """Test converting stdio server to SDK format."""
        # Arrange
        server = MCPServerModel(
            id=uuid4(),
            user_id=uuid4(),
            name="test_stdio",
            config_type="stdio",
            config={
                "command": "python",
                "args": ["-m", "test.server"],
                "env": {"TEST_VAR": "value"},
            },
            is_enabled=True,
        )
        
        # Act
        sdk_config = mcp_config_builder._convert_to_sdk_format(server)
        
        # Assert
        assert sdk_config["command"] == "python"
        assert sdk_config["args"] == ["-m", "test.server"]
        assert sdk_config["env"] == {"TEST_VAR": "value"}

    def test_convert_to_sdk_format_sse(self, mcp_config_builder):
        """Test converting SSE server to SDK format."""
        # Arrange
        server = MCPServerModel(
            id=uuid4(),
            user_id=uuid4(),
            name="test_sse",
            config_type="sse",
            config={
                "url": "http://localhost:3000/sse",
                "headers": {"Authorization": "Bearer token"},
            },
            is_enabled=True,
        )
        
        # Act
        sdk_config = mcp_config_builder._convert_to_sdk_format(server)
        
        # Assert
        assert sdk_config["type"] == "sse"
        assert sdk_config["url"] == "http://localhost:3000/sse"
        assert sdk_config["headers"] == {"Authorization": "Bearer token"}

    def test_convert_to_sdk_format_http(self, mcp_config_builder):
        """Test converting HTTP server to SDK format."""
        # Arrange
        server = MCPServerModel(
            id=uuid4(),
            user_id=uuid4(),
            name="test_http",
            config_type="http",
            config={
                "url": "https://api.example.com/mcp",
                "headers": {"X-API-Key": "secret"},
            },
            is_enabled=True,
        )
        
        # Act
        sdk_config = mcp_config_builder._convert_to_sdk_format(server)
        
        # Assert
        assert sdk_config["type"] == "http"
        assert sdk_config["url"] == "https://api.example.com/mcp"
        assert sdk_config["headers"] == {"X-API-Key": "secret"}

    @pytest.mark.asyncio
    async def test_build_session_mcp_config_filters_disabled_servers(
        self,
        mcp_config_builder,
    ):
        """Test that disabled servers are filtered out."""
        # Arrange
        user_id = uuid4()
        
        enabled_server = MCPServerModel(
            id=uuid4(),
            user_id=user_id,
            name="enabled_server",
            config_type="stdio",
            config={"command": "test"},
            is_enabled=True,
        )
        
        disabled_server = MCPServerModel(
            id=uuid4(),
            user_id=user_id,
            name="disabled_server",
            config_type="stdio",
            config={"command": "test"},
            is_enabled=False,
        )
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = [
            enabled_server,
            disabled_server,
        ]
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = []
        
        # Act
        config = await mcp_config_builder.build_session_mcp_config(
            user_id=user_id,
            include_sdk_tools=False,
        )
        
        # Assert
        assert "enabled_server" in config
        assert "disabled_server" not in config

    def test_sdk_mcp_servers_structure(self):
        """Test SDK_MCP_SERVERS has correct structure."""
        # Assert
        assert isinstance(SDK_MCP_SERVERS, dict)
        
        # Check expected servers exist
        expected_servers = ["kubernetes_readonly", "database", "monitoring"]
        for server_name in expected_servers:
            assert server_name in SDK_MCP_SERVERS
            
            server_config = SDK_MCP_SERVERS[server_name]
            assert "tools" in server_config
            assert isinstance(server_config["tools"], list)
            assert len(server_config["tools"]) > 0
            
            # Each tool should have name and function
            for tool in server_config["tools"]:
                assert "name" in tool
                assert "function" in tool
                assert callable(tool["function"])

    @pytest.mark.asyncio
    async def test_merge_sdk_servers_with_external(
        self,
        mcp_config_builder,
        sample_user_servers,
    ):
        """Test merging SDK servers with external servers."""
        # Arrange
        user_id = uuid4()
        
        mcp_config_builder.mcp_server_repo.get_by_user.return_value = sample_user_servers
        mcp_config_builder.mcp_server_repo.get_global_enabled.return_value = []
        
        # Act
        config = await mcp_config_builder.build_session_mcp_config(
            user_id=user_id,
            include_sdk_tools=True,
        )
        
        # Assert
        # SDK servers should have tools
        assert "tools" in config["kubernetes_readonly"]
        assert "tools" in config["database"]
        
        # External servers should have command/args or url
        user_server = config["user_filesystem"]
        assert "command" in user_server or "url" in user_server
        
        # No conflicts - all servers present
        expected_count = len(SDK_MCP_SERVERS) + len(sample_user_servers)
        assert len(config) == expected_count