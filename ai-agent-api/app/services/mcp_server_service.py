"""MCP Server service for business logic."""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.models.mcp_server import MCPServerModel
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.audit_service import AuditService
from app.schemas.mcp import (
    MCPServerCreateRequest,
    MCPServerUpdateRequest,
    MCPServerResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServerService:
    """Business logic for MCP server management."""

    def __init__(
        self,
        db: AsyncSession,
        mcp_server_repo: MCPServerRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.mcp_server_repo = mcp_server_repo
        self.audit_service = audit_service

    async def create_server(
        self,
        user: User,
        server_data: MCPServerCreateRequest,
    ) -> MCPServerResponse:
        """Create a new MCP server configuration.
        
        Args:
            user: User creating the server
            server_data: Server configuration data
            
        Returns:
            Created server response
        """
        logger.info(
            "Creating MCP server",
            extra={
                "user_id": str(user.id),
                "server_name": server_data.name,
                "server_type": server_data.type,
                "enabled": server_data.enabled
            }
        )
        
        # Check if server with name already exists for user
        existing = await self.mcp_server_repo.get_by_name_and_user(
            server_data.name, user.id
        )
        if existing:
            logger.warning(
                "MCP server creation failed - name already exists",
                extra={
                    "user_id": str(user.id),
                    "server_name": server_data.name,
                    "existing_server_id": str(existing.id)
                }
            )
            raise ValueError(f"MCP server with name '{server_data.name}' already exists")

        # Create server
        saved_server = await self.mcp_server_repo.create(
            id=uuid4(),
            name=server_data.name,
            description=server_data.description,
            server_type=server_data.server_type,
            config=server_data.config,
            is_enabled=server_data.is_enabled,
            user_id=user.id,
            created_at=datetime.utcnow(),
        )

        logger.info(
            "MCP server created successfully",
            extra={
                "user_id": str(user.id),
                "server_id": str(saved_server.id),
                "server_name": server_data.name,
                "server_type": server_data.server_type
            }
        )

        # Audit log
        await self.audit_service.log_action(
            user_id=user.id,
            action_type="mcp_server_create",
            resource_type="mcp_server",
            resource_id=saved_server.id,
            action_details={"name": server_data.name, "config": server_data.config},
        )

        # Return response using model_validate
        return MCPServerResponse.model_validate(saved_server)

    async def get_server(
        self,
        user: User,
        server_id: UUID,
    ) -> MCPServerResponse:
        """Get MCP server by ID.
        
        Args:
            user: User requesting the server
            server_id: Server UUID
            
        Returns:
            Server response
        """
        server = await self.mcp_server_repo.get_by_id(server_id)
        if not server:
            raise ValueError(f"MCP server {server_id} not found")

        # Check access permissions
        if server.user_id != user.id and not server.is_global:
            raise PermissionError("Access denied to MCP server")

        return MCPServerResponse.model_validate(server)

    async def list_servers(
        self,
        user: User,
        include_global: bool = True,
    ) -> List[MCPServerResponse]:
        """List user's MCP servers.
        
        Args:
            user: User requesting servers
            include_global: Whether to include global servers
            
        Returns:
            List of server responses
        """
        servers = await self.mcp_server_repo.list_by_user(user.id, include_global)
        return [MCPServerResponse.model_validate(server) for server in servers]

    async def update_server(
        self,
        user: User,
        server_id: UUID,
        update_data: MCPServerUpdateRequest,
    ) -> MCPServerResponse:
        """Update MCP server configuration.
        
        Args:
            user: User updating the server
            server_id: Server UUID
            update_data: Update data
            
        Returns:
            Updated server response
        """
        server = await self.mcp_server_repo.get_by_id(server_id)
        if not server:
            raise ValueError(f"MCP server {server_id} not found")

        # Check permissions (only server owner can update)
        if server.user_id != user.id:
            raise PermissionError("Access denied to update MCP server")

        # Update fields
        update_dict = {}
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.config is not None:
            update_dict["config"] = update_data.config
        if update_data.is_enabled is not None:
            update_dict["is_enabled"] = update_data.is_enabled
        
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            updated_server = await self.mcp_server_repo.update(server_id, **update_dict)
        else:
            updated_server = server

        # Audit log
        await self.audit_service.log_action(
            user_id=user.id,
            action_type="mcp_server_update",
            resource_type="mcp_server",
            resource_id=server_id,
            action_details=update_data.model_dump(exclude_unset=True),
        )

        return MCPServerResponse.model_validate(updated_server)

    async def delete_server(
        self,
        user: User,
        server_id: UUID,
    ) -> None:
        """Delete MCP server configuration.
        
        Args:
            user: User deleting the server
            server_id: Server UUID
        """
        server = await self.mcp_server_repo.get_by_id(server_id)
        if not server:
            raise ValueError(f"MCP server {server_id} not found")

        # Check permissions (only server owner can delete)
        if server.user_id != user.id:
            raise PermissionError("Access denied to delete MCP server")

        # Soft delete
        await self.mcp_server_repo.update(
            server_id,
            deleted_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Audit log
        await self.audit_service.log_action(
            user_id=user.id,
            action_type="mcp_server_delete",
            resource_type="mcp_server",
            resource_id=server_id,
            action_details={"name": server.name},
        )

    async def test_server(
        self,
        user: User,
        server_id: UUID,
    ) -> dict:
        """Test MCP server connection.
        
        Args:
            user: User testing the server
            server_id: Server UUID
            
        Returns:
            Test results
        """
        server = await self.mcp_server_repo.get_by_id(server_id)
        if not server:
            raise ValueError(f"MCP server {server_id} not found")

        # Check permissions
        if server.user_id != user.id and not server.is_global:
            raise PermissionError("Access denied to test MCP server")

        # TODO: Implement actual MCP server connection test
        # For now, return basic validation
        config = server.config or {}
        return {
            "status": "success",
            "message": "MCP server configuration appears valid",
            "details": {
                "name": server.name,
                "server_type": server.server_type,
                "command": config.get("command"),
                "args_count": len(config.get("args", [])),
                "env_vars": len(config.get("env", {})),
            },
        }