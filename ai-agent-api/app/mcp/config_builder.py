"""
MCP Config Builder - Builds SDK-compatible MCP configurations.

Converts database MCP server configs to SDK format that can be passed
to ClaudeAgentOptions.mcp_servers.
"""

from typing import Dict, Any
from uuid import UUID
import logging

from app.repositories.mcp_server_repository import MCPServerRepository

logger = logging.getLogger(__name__)


class MCPConfigBuilder:
    """
    Build SDK-compatible MCP server configurations from database.
    
    The SDK accepts mcp_servers in this format:
    {
        "server_name": {
            "type": "stdio",  # or "sse", "http"
            "command": "npx",
            "args": ["@modelcontextprotocol/server-kubernetes"],
            "env": {"KEY": "value"}
        }
    }
    """
    
    def __init__(self, mcp_server_repo: MCPServerRepository):
        self.mcp_server_repo = mcp_server_repo
    
    async def build_user_mcp_config(self, user_id: UUID) -> Dict[str, Any]:
        """
        Build MCP config for a specific user.
        
        Includes:
        - User's own MCP servers
        - Global/shared MCP servers
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary of MCP server configs in SDK format
        """
        # Get user's servers
        user_servers = await self.mcp_server_repo.list_by_user(str(user_id))
        
        # Get global servers
        all_servers = await self.mcp_server_repo.list_enabled()
        global_servers = [s for s in all_servers if s.is_global and s.is_enabled]
        
        # Combine (user servers take precedence over global)
        all_servers_list = user_servers + [
            s for s in global_servers 
            if s.name not in [us.name for us in user_servers]
        ]
        
        # Build SDK config
        mcp_config = {}
        for server in all_servers_list:
            if not server.is_enabled:
                continue
            
            try:
                sdk_config = self._convert_to_sdk_format(server)
                mcp_config[server.name] = sdk_config
                logger.debug(f"Added MCP server to config: {server.name} ({server.server_type})")
            except Exception as e:
                logger.error(f"Failed to convert MCP server {server.name}: {e}")
        
        return mcp_config
    
    def _convert_to_sdk_format(self, server) -> Dict[str, Any]:
        """
        Convert database MCPServer entity to SDK format.
        
        Args:
            server: MCPServer entity
        
        Returns:
            SDK-compatible server config
        """
        config = server.config
        
        if server.server_type == "stdio":
            # stdio format
            sdk_config = {
                "command": config["command"],
                "args": config.get("args", []),
            }
            if "env" in config and config["env"]:
                sdk_config["env"] = config["env"]
            
            return sdk_config
        
        elif server.server_type == "sse":
            # SSE format
            return {
                "type": "sse",
                "url": config["url"],
                "headers": config.get("headers", {})
            }
        
        elif server.server_type == "http":
            # HTTP format
            return {
                "type": "http",
                "url": config["url"],
                "headers": config.get("headers", {})
            }
        
        else:
            raise ValueError(f"Unsupported server type: {server.server_type}")
    
    async def build_session_mcp_config(
        self,
        user_id: UUID,
        include_sdk_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Build complete MCP config for a session.
        
        Args:
            user_id: User ID
            include_sdk_tools: Whether to include SDK MCP tools
        
        Returns:
            Complete MCP config including SDK tools and external servers
        """
        # Start with SDK tools
        from app.mcp.sdk_tools import SDK_MCP_SERVERS
        
        if include_sdk_tools:
            config = dict(SDK_MCP_SERVERS)
        else:
            config = {}
        
        # Add user's external servers
        user_config = await self.build_user_mcp_config(user_id)
        config.update(user_config)
        
        logger.info(
            f"Built MCP config for user {user_id}: "
            f"{len(config)} servers total"
        )
        
        return config


__all__ = ["MCPConfigBuilder"]
