"""MCP server manager for managing MCP server lifecycle."""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.claude_sdk.mcp.mcp_server_config import MCPServerConfig, MCPServerType

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manager for MCP server lifecycle and configuration.

    Handles both SDK servers (in-process) and external servers (subprocess).

    Based on POC scripts:
    - 05_mcp_sdk_servers.py: SDK servers with @tool decorator
    - 06_external_mcp_servers.py: External servers with command/args

    Example usage:
        >>> manager = MCPServerManager()
        >>>
        >>> # Add SDK server
        >>> sdk_config = MCPServerConfig(
        ...     name="my_tools",
        ...     server_type=MCPServerType.SDK,
        ...     sdk_server_config=my_server
        ... )
        >>> manager.add_server(sdk_config)
        >>>
        >>> # Add external server
        >>> ext_config = MCPServerConfig(
        ...     name="filesystem",
        ...     server_type=MCPServerType.EXTERNAL,
        ...     command="npx",
        ...     args=["-y", "@modelcontextprotocol/server-filesystem", "/path"]
        ... )
        >>> manager.add_server(ext_config)
        >>>
        >>> # Get SDK configuration
        >>> mcp_servers = manager.build_sdk_configuration()
        >>> options = ClaudeAgentOptions(mcp_servers=mcp_servers, ...)
    """

    def __init__(self):
        """Initialize MCP server manager."""
        self._servers: Dict[str, MCPServerConfig] = {}

    def add_server(self, config: MCPServerConfig) -> None:
        """Add an MCP server configuration.

        Args:
            config: Server configuration

        Raises:
            ValueError: If server with same name already exists
        """
        if config.name in self._servers:
            raise ValueError(f"Server with name '{config.name}' already exists")

        if not config.enabled:
            logger.info(f"Skipping disabled MCP server: {config.name}")
            return

        self._servers[config.name] = config

        logger.info(
            f"Added MCP server: {config.name} "
            f"(type={config.server_type.value})"
        )

    def remove_server(self, name: str) -> bool:
        """Remove an MCP server.

        Args:
            name: Server name

        Returns:
            True if removed, False if not found
        """
        if name in self._servers:
            del self._servers[name]
            logger.info(f"Removed MCP server: {name}")
            return True
        return False

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name.

        Args:
            name: Server name

        Returns:
            Server config or None if not found
        """
        return self._servers.get(name)

    def list_servers(self) -> List[str]:
        """Get list of all server names.

        Returns:
            List of server names
        """
        return list(self._servers.keys())

    def build_sdk_configuration(self) -> Dict[str, Any]:
        """Build SDK-compatible MCP server configuration.

        Based on POC scripts, the SDK expects a dictionary where:
        - Keys are server names
        - Values are either:
          - McpSdkServerConfig (for SDK servers)
          - Dict with command/args/env (for external servers)

        Example output:
            {
                "my_tools": <McpSdkServerConfig>,
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
                    "env": {}
                }
            }

        Returns:
            Dictionary of MCP server configurations for SDK
        """
        sdk_config: Dict[str, Any] = {}

        for name, config in self._servers.items():
            if not config.enabled:
                continue

            try:
                sdk_config[name] = config.to_sdk_config()
            except Exception as e:
                logger.error(
                    f"Failed to build SDK config for {name}: "
                    f"{type(e).__name__} - {str(e)}",
                    exc_info=True
                )
                # Skip this server on error
                continue

        logger.info(
            f"Built MCP configuration with {len(sdk_config)} servers: "
            f"{list(sdk_config.keys())}"
        )

        return sdk_config

    def get_server_count(self, server_type: Optional[MCPServerType] = None) -> int:
        """Get count of servers.

        Args:
            server_type: Filter by type, or None for all

        Returns:
            Number of servers
        """
        if server_type:
            return sum(
                1 for cfg in self._servers.values()
                if cfg.server_type == server_type and cfg.enabled
            )
        return sum(1 for cfg in self._servers.values() if cfg.enabled)

    def clear(self) -> None:
        """Clear all servers."""
        self._servers.clear()
        logger.info("Cleared all MCP servers")
