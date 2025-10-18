"""MCP server configuration classes."""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class MCPServerType(str, Enum):
    """Type of MCP server."""
    SDK = "sdk"  # In-process SDK server with @tool decorator
    EXTERNAL = "external"  # Subprocess-based external server


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server.

    For SDK servers (in-process):
        From POC 05_mcp_sdk_servers.py:
        >>> server = create_sdk_mcp_server(
        ...     name="my_tools",
        ...     version="1.0.0",
        ...     tools=[calculate, unit_convert]
        ... )

    For External servers (subprocess):
        From POC 06_external_mcp_servers.py:
        >>> server_config = {
        ...     "command": "npx",
        ...     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
        ...     "env": {}
        ... }
    """
    name: str
    server_type: MCPServerType
    enabled: bool = True

    # For SDK servers
    sdk_server_config: Optional[Any] = None  # Result of create_sdk_mcp_server()

    # For external servers
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

    # Metadata
    description: Optional[str] = None
    version: Optional[str] = None

    def to_sdk_config(self) -> Any:
        """Convert to SDK-compatible configuration.

        Returns:
            For SDK servers: The McpSdkServerConfig object
            For external servers: Dictionary with command, args, env
        """
        if self.server_type == MCPServerType.SDK:
            if not self.sdk_server_config:
                raise ValueError(f"SDK server {self.name} has no config")
            return self.sdk_server_config

        elif self.server_type == MCPServerType.EXTERNAL:
            if not self.command:
                raise ValueError(f"External server {self.name} has no command")

            return {
                "command": self.command,
                "args": self.args or [],
                "env": self.env or {}
            }

        else:
            raise ValueError(f"Unknown server type: {self.server_type}")

    def is_sdk_server(self) -> bool:
        """Check if this is an SDK server."""
        return self.server_type == MCPServerType.SDK

    def is_external_server(self) -> bool:
        """Check if this is an external server."""
        return self.server_type == MCPServerType.EXTERNAL
