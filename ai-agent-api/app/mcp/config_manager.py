"""
MCP Config Manager - Import/export Claude Desktop compatible configs.

Handles uploading claude_desktop_config.json and exporting user configs
in the same format.
"""

from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
import json
import logging

from app.domain.entities import MCPServer
from app.repositories.mcp_server_repository import MCPServerRepository

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Manage MCP server configurations with Claude Desktop compatibility.
    
    Supports:
    - Import from claude_desktop_config.json
    - Export to Claude Desktop format
    - CRUD operations for MCP servers
    - Validation
    """
    
    def __init__(self, mcp_server_repo: MCPServerRepository):
        self.mcp_server_repo = mcp_server_repo
    
    async def import_claude_desktop_config(
        self,
        config_data: Dict[str, Any],
        user_id: UUID,
        override_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Import MCP servers from Claude Desktop config format.
        
        Claude Desktop format:
        {
            "mcpServers": {
                "server_name": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
                    "env": {"KEY": "value"}
                },
                "remote_server": {
                    "type": "sse",
                    "url": "https://...",
                    "headers": {"Authorization": "Bearer ..."}
                }
            }
        }
        
        Args:
            config_data: Claude Desktop config JSON
            user_id: User ID to associate servers with
            override_existing: Whether to override existing servers
        
        Returns:
            Import summary
        """
        if "mcpServers" not in config_data:
            raise ValueError("Invalid config: missing 'mcpServers' key")
        
        mcp_servers = config_data["mcpServers"]
        
        imported = []
        skipped = []
        errors = []
        
        for server_name, server_config in mcp_servers.items():
            try:
                # Check if server already exists
                existing_servers = await self.mcp_server_repo.list_by_user(str(user_id))
                exists = any(s.name == server_name for s in existing_servers)
                
                if exists and not override_existing:
                    skipped.append(server_name)
                    logger.info(f"Skipped existing server: {server_name}")
                    continue
                
                # Determine server type
                server_type = server_config.get("type", "stdio")
                
                # Validate and normalize config
                normalized_config = self._normalize_config(server_type, server_config)
                
                # Create MCPServer entity
                mcp_server = MCPServer(
                    id=uuid4(),
                    user_id=user_id,
                    name=server_name,
                    description=f"Imported from Claude Desktop config",
                    server_type=server_type,
                    config=normalized_config,
                    is_global=False,
                    is_enabled=True,
                    health_status="unknown",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                
                # Save to database
                if exists and override_existing:
                    # Update existing
                    existing = [s for s in existing_servers if s.name == server_name][0]
                    mcp_server.id = existing.id
                    await self.mcp_server_repo.update(mcp_server)
                else:
                    # Create new
                    await self.mcp_server_repo.create(mcp_server)
                
                imported.append(server_name)
                logger.info(f"Imported MCP server: {server_name} ({server_type})")
            
            except Exception as e:
                errors.append({"server": server_name, "error": str(e)})
                logger.error(f"Failed to import server {server_name}: {e}")
        
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "summary": f"Imported {len(imported)}, skipped {len(skipped)}, errors {len(errors)}"
        }
    
    async def export_claude_desktop_config(
        self,
        user_id: UUID,
        include_global: bool = True
    ) -> Dict[str, Any]:
        """
        Export user's MCP servers to Claude Desktop config format.
        
        Args:
            user_id: User ID
            include_global: Whether to include global servers
        
        Returns:
            Claude Desktop compatible config JSON
        """
        # Get user's servers
        user_servers = await self.mcp_server_repo.list_by_user(str(user_id))
        
        # Get global servers if requested
        servers = user_servers
        if include_global:
            all_servers = await self.mcp_server_repo.list_enabled()
            global_servers = [s for s in all_servers if s.is_global and s.is_enabled]
            # Add globals not already in user's list
            servers += [
                s for s in global_servers 
                if s.name not in [us.name for us in user_servers]
            ]
        
        # Build Claude Desktop format
        mcp_servers_config = {}
        for server in servers:
            if not server.is_enabled:
                continue
            
            config = server.config.copy()
            
            # Add type for non-stdio servers
            if server.server_type != "stdio":
                config["type"] = server.server_type
            
            mcp_servers_config[server.name] = config
        
        return {
            "mcpServers": mcp_servers_config
        }
    
    def _normalize_config(self, server_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate server config.
        
        Args:
            server_type: Server type (stdio/sse/http)
            config: Raw config from import
        
        Returns:
            Normalized config
        
        Raises:
            ValueError: If config is invalid
        """
        if server_type == "stdio":
            if "command" not in config:
                raise ValueError("stdio server requires 'command'")
            
            return {
                "command": config["command"],
                "args": config.get("args", []),
                "env": config.get("env", {})
            }
        
        elif server_type in ["sse", "http"]:
            if "url" not in config:
                raise ValueError(f"{server_type} server requires 'url'")
            
            if not config["url"].startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {config['url']}")
            
            return {
                "url": config["url"],
                "headers": config.get("headers", {})
            }
        
        else:
            raise ValueError(f"Unsupported server type: {server_type}")
    
    async def create_server(
        self,
        user_id: UUID,
        name: str,
        server_type: str,
        config: Dict[str, Any],
        description: str = None,
        is_global: bool = False
    ) -> MCPServer:
        """
        Create a new MCP server.
        
        Args:
            user_id: User ID
            name: Server name (must be unique per user)
            server_type: Server type (stdio/sse/http)
            config: Server configuration
            description: Optional description
            is_global: Whether server is global (admin only)
        
        Returns:
            Created MCPServer entity
        """
        # Validate config
        normalized_config = self._normalize_config(server_type, config)
        
        # Create entity
        server = MCPServer(
            id=uuid4(),
            user_id=user_id if not is_global else None,
            name=name,
            description=description,
            server_type=server_type,
            config=normalized_config,
            is_global=is_global,
            is_enabled=True,
            health_status="unknown",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Save
        await self.mcp_server_repo.create(server)
        logger.info(f"Created MCP server: {name} ({server_type})")
        
        return server
    
    async def update_server(
        self,
        server_id: UUID,
        updates: Dict[str, Any]
    ) -> MCPServer:
        """
        Update an MCP server.
        
        Args:
            server_id: Server ID
            updates: Fields to update
        
        Returns:
            Updated MCPServer entity
        """
        server = await self.mcp_server_repo.get_by_id(str(server_id))
        if not server:
            raise ValueError(f"Server {server_id} not found")
        
        # Update fields
        if "name" in updates:
            server.name = updates["name"]
        if "description" in updates:
            server.description = updates["description"]
        if "config" in updates:
            # Validate config
            normalized = self._normalize_config(server.server_type, updates["config"])
            server.config = normalized
        if "is_enabled" in updates:
            server.is_enabled = updates["is_enabled"]
        
        server.updated_at = datetime.utcnow()
        
        # Save
        await self.mcp_server_repo.update(server)
        logger.info(f"Updated MCP server: {server.name}")
        
        return server
    
    async def delete_server(self, server_id: UUID) -> None:
        """
        Delete an MCP server.
        
        Args:
            server_id: Server ID
        """
        await self.mcp_server_repo.delete(str(server_id))
        logger.info(f"Deleted MCP server: {server_id}")
    
    async def get_server_templates(self) -> List[Dict[str, Any]]:
        """
        Get pre-configured templates for popular MCP servers.
        
        Returns:
            List of server templates
        """
        return [
            {
                "name": "kubernetes",
                "display_name": "Kubernetes",
                "description": "Query Kubernetes clusters",
                "server_type": "stdio",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
                    "env": {
                        "KUBECONFIG": "/path/to/kubeconfig"
                    }
                },
                "required_env": ["KUBECONFIG"]
            },
            {
                "name": "filesystem",
                "display_name": "Filesystem",
                "description": "Access local filesystem",
                "server_type": "stdio",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
                },
                "required_args": ["path"]
            },
            {
                "name": "postgres",
                "display_name": "PostgreSQL",
                "description": "Query PostgreSQL databases",
                "server_type": "stdio",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres"],
                    "env": {
                        "POSTGRES_URL": "postgresql://localhost/mydb"
                    }
                },
                "required_env": ["POSTGRES_URL"]
            },
            {
                "name": "brave-search",
                "display_name": "Brave Search",
                "description": "Search the web with Brave",
                "server_type": "stdio",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {
                        "BRAVE_API_KEY": "your-api-key"
                    }
                },
                "required_env": ["BRAVE_API_KEY"]
            },
            {
                "name": "github",
                "display_name": "GitHub",
                "description": "Access GitHub repositories",
                "server_type": "stdio",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_TOKEN": "your-token"
                    }
                },
                "required_env": ["GITHUB_TOKEN"]
            }
        ]


__all__ = ["MCPConfigManager"]
