"""
MCP (Model Context Protocol) integration package.

This package handles:
1. SDK MCP Tools: In-process Python tools with @tool decorator
2. External MCP Config: Building SDK-compatible configs from database
3. Config Management: Import/export Claude Desktop compatible configs
"""

from app.mcp.sdk_tools import SDK_MCP_SERVERS
from app.mcp.config_builder import MCPConfigBuilder
from app.mcp.config_manager import MCPConfigManager

__all__ = [
    "SDK_MCP_SERVERS",
    "MCPConfigBuilder",
    "MCPConfigManager",
]
