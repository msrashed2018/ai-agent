"""Tool registry for discovering and tracking MCP tools."""
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about an MCP tool."""
    name: str
    server_name: str
    full_name: str  # e.g., "mcp__my_tools__calculate"
    description: Optional[str] = None


class ToolRegistry:
    """Registry for discovering and tracking available MCP tools.

    Based on POC scripts, MCP tools are prefixed with:
    mcp__<server_name>__<tool_name>

    Example:
        - SDK server "my_tools" with tool "calculate"
          -> Full name: "mcp__my_tools__calculate"
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, ToolInfo] = {}
        self._tools_by_server: Dict[str, Set[str]] = {}

    def register_sdk_server_tools(
        self,
        server_name: str,
        tool_names: List[str]
    ) -> None:
        """Register tools from an SDK server.

        Args:
            server_name: MCP server name
            tool_names: List of tool names (without mcp__ prefix)
        """
        if server_name not in self._tools_by_server:
            self._tools_by_server[server_name] = set()

        for tool_name in tool_names:
            # MCP tools are prefixed: mcp__<server>__<tool>
            full_name = f"mcp__{server_name}__{tool_name}"

            tool_info = ToolInfo(
                name=tool_name,
                server_name=server_name,
                full_name=full_name
            )

            self._tools[full_name] = tool_info
            self._tools_by_server[server_name].add(full_name)

        logger.info(
            f"Registered {len(tool_names)} tools from SDK server '{server_name}'"
        )

    def register_external_server(
        self,
        server_name: str,
        tool_names: Optional[List[str]] = None
    ) -> None:
        """Register an external MCP server.

        Note: For external servers, we may not know tool names upfront
        unless we query the server via MCP protocol.

        Args:
            server_name: MCP server name
            tool_names: Optional list of tool names
        """
        if server_name not in self._tools_by_server:
            self._tools_by_server[server_name] = set()

        if tool_names:
            for tool_name in tool_names:
                full_name = f"mcp__{server_name}__{tool_name}"

                tool_info = ToolInfo(
                    name=tool_name,
                    server_name=server_name,
                    full_name=full_name
                )

                self._tools[full_name] = tool_info
                self._tools_by_server[server_name].add(full_name)

            logger.info(
                f"Registered {len(tool_names)} tools from external server '{server_name}'"
            )
        else:
            logger.info(
                f"Registered external server '{server_name}' (tools unknown)"
            )

    def get_tool_info(self, full_name: str) -> Optional[ToolInfo]:
        """Get tool information by full name.

        Args:
            full_name: Full tool name (e.g., "mcp__my_tools__calculate")

        Returns:
            Tool info or None if not found
        """
        return self._tools.get(full_name)

    def get_server_tools(self, server_name: str) -> List[str]:
        """Get all tool names for a server.

        Args:
            server_name: Server name

        Returns:
            List of full tool names
        """
        return sorted(self._tools_by_server.get(server_name, set()))

    def list_all_tools(self) -> List[str]:
        """Get list of all registered tools.

        Returns:
            List of full tool names
        """
        return sorted(self._tools.keys())

    def list_servers(self) -> List[str]:
        """Get list of all servers.

        Returns:
            List of server names
        """
        return sorted(self._tools_by_server.keys())

    def get_tool_count(self, server_name: Optional[str] = None) -> int:
        """Get count of tools.

        Args:
            server_name: Server to count, or None for all

        Returns:
            Number of tools
        """
        if server_name:
            return len(self._tools_by_server.get(server_name, set()))
        return len(self._tools)

    def clear(self, server_name: Optional[str] = None) -> None:
        """Clear tools.

        Args:
            server_name: Server to clear, or None to clear all
        """
        if server_name:
            # Remove tools for specific server
            tool_names = self._tools_by_server.get(server_name, set())
            for tool_name in tool_names:
                del self._tools[tool_name]
            del self._tools_by_server[server_name]
            logger.info(f"Cleared tools for server: {server_name}")
        else:
            # Clear all
            self._tools.clear()
            self._tools_by_server.clear()
            logger.info("Cleared all tools")
