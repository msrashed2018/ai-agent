"""MCP Server Repository.

Repository for MCP server configuration persistence and retrieval.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_server import MCPServerModel
from app.repositories.base import BaseRepository


class MCPServerRepository(BaseRepository[MCPServerModel]):
    """Repository for MCP server operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(MCPServerModel, db)

    async def get_by_name_and_user(
        self,
        name: str,
        user_id: UUID,
    ) -> Optional[MCPServerModel]:
        """Get MCP server by name and user ID.
        
        Args:
            name: Server name
            user_id: User UUID
            
        Returns:
            MCPServerModel if found, None otherwise
        """
        query = select(MCPServerModel).where(
            and_(
                MCPServerModel.name == name,
                MCPServerModel.user_id == user_id,
                MCPServerModel.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_global_by_name(self, name: str) -> Optional[MCPServerModel]:
        """Get global MCP server by name.
        
        Global servers have user_id = None.
        
        Args:
            name: Server name
            
        Returns:
            MCPServerModel if found, None otherwise
        """
        query = select(MCPServerModel).where(
            and_(
                MCPServerModel.name == name,
                MCPServerModel.user_id.is_(None),
                MCPServerModel.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        include_global: bool = True,
    ) -> List[MCPServerModel]:
        """List MCP servers for user.
        
        Args:
            user_id: User UUID
            include_global: Whether to include global servers
            
        Returns:
            List of MCPServerModel
        """
        conditions = [MCPServerModel.deleted_at.is_(None)]

        if include_global:
            conditions.append(
                (MCPServerModel.user_id == user_id) |
                (MCPServerModel.user_id.is_(None))
            )
        else:
            conditions.append(MCPServerModel.user_id == user_id)

        query = select(MCPServerModel).where(and_(*conditions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_enabled(
        self,
        user_id: Optional[UUID] = None,
    ) -> List[MCPServerModel]:
        """List enabled MCP servers.
        
        Args:
            user_id: Optional user UUID to filter by
            
        Returns:
            List of enabled MCPServerModel
        """
        conditions = [
            MCPServerModel.is_enabled == True,
            MCPServerModel.deleted_at.is_(None),
        ]

        if user_id:
            conditions.append(
                (MCPServerModel.user_id == user_id) |
                (MCPServerModel.user_id.is_(None))
            )

        query = select(MCPServerModel).where(and_(*conditions))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_health_status(
        self,
        server_id: UUID,
        status: str,
        last_error: Optional[str] = None,
    ) -> Optional[MCPServerModel]:
        """Update server health status.
        
        Args:
            server_id: Server UUID
            status: Health status
            last_error: Optional error message
            
        Returns:
            Updated MCPServerModel
        """
        server = await self.get_by_id(server_id)
        if not server:
            return None

        server.health_status = status
        server.last_error = last_error
        await self.db.commit()
        await self.db.refresh(server)
        return server
