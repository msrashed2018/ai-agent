"""MCP integration for Claude SDK.

This module provides MCP (Model Context Protocol) server management:

- MCPServerConfig: Configuration for SDK and external MCP servers
- MCPServerType: Enumeration of server types (SDK, External)
- MCPServerManager: Manager for MCP server lifecycle
- ToolRegistry: Registry for discovering and tracking MCP tools
- ToolInfo: Information about individual tools

Example usage:
    >>> from app.claude_sdk.mcp import MCPServerManager, MCPServerConfig, MCPServerType
    >>> from claude_agent_sdk import create_sdk_mcp_server, tool
    >>>
    >>> # Create SDK server with tools
    >>> @tool("calculate", "Perform calculations", {"expression": str})
    >>> async def calculate(args):
    ...     return {"content": [{"type": "text", "text": str(eval(args["expression"]))}]}
    >>>
    >>> sdk_server = create_sdk_mcp_server(
    ...     name="my_tools",
    ...     version="1.0.0",
    ...     tools=[calculate]
    ... )
    >>>
    >>> # Add to manager
    >>> manager = MCPServerManager()
    >>> manager.add_server(MCPServerConfig(
    ...     name="my_tools",
    ...     server_type=MCPServerType.SDK,
    ...     sdk_server_config=sdk_server
    ... ))
    >>>
    >>> # Add external server
    >>> manager.add_server(MCPServerConfig(
    ...     name="filesystem",
    ...     server_type=MCPServerType.EXTERNAL,
    ...     command="npx",
    ...     args=["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    ... ))
    >>>
    >>> # Build SDK configuration
    >>> mcp_servers = manager.build_sdk_configuration()
    >>> options = ClaudeAgentOptions(mcp_servers=mcp_servers, ...)
"""
from app.claude_sdk.mcp.mcp_server_config import MCPServerConfig, MCPServerType
from app.claude_sdk.mcp.mcp_server_manager import MCPServerManager
from app.claude_sdk.mcp.tool_registry import ToolRegistry, ToolInfo

__all__ = [
    "MCPServerConfig",
    "MCPServerType",
    "MCPServerManager",
    "ToolRegistry",
    "ToolInfo",
]
