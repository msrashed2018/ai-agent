"""MCP Server domain entity."""
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID


class MCPServer:
    """MCP Server aggregate root."""

    def __init__(
        self,
        id: UUID,
        name: str,
        command: str,
        user_id: Optional[UUID] = None,
    ):
        self.id = id
        self.name = name
        self.command = command
        self.user_id = user_id

        # Configuration
        self.description: Optional[str] = None
        self.args: List[str] = []
        self.env: Dict[str, str] = {}
        self.cwd: Optional[str] = None

        # Metadata
        self.is_global = False
        self.is_active = True
        self.version: Optional[str] = None
        self.tags: List[str] = []

        # Timestamps
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None

    def is_owned_by(self, user_id: UUID) -> bool:
        """Check if server is owned by user."""
        return self.user_id == user_id

    def is_accessible_by(self, user_id: UUID) -> bool:
        """Check if server is accessible by user."""
        return self.is_global or self.user_id == user_id

    def activate(self) -> None:
        """Activate the server."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the server."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def update_config(
        self,
        description: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """Update server configuration."""
        if description is not None:
            self.description = description
        if args is not None:
            self.args = args
        if env is not None:
            self.env = env
        if cwd is not None:
            self.cwd = cwd
        
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the server."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the server."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete the server."""
        self.deleted_at = datetime.utcnow()
        self.is_active = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "cwd": self.cwd,
            "user_id": str(self.user_id) if self.user_id else None,
            "is_global": self.is_global,
            "is_active": self.is_active,
            "version": self.version,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPServer":
        """Create instance from dictionary."""
        server = cls(
            id=UUID(data["id"]),
            name=data["name"],
            command=data["command"],
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
        )
        
        server.description = data.get("description")
        server.args = data.get("args", [])
        server.env = data.get("env", {})
        server.cwd = data.get("cwd")
        server.is_global = data.get("is_global", False)
        server.is_active = data.get("is_active", True)
        server.version = data.get("version")
        server.tags = data.get("tags", [])
        
        if data.get("created_at"):
            server.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            server.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("deleted_at"):
            server.deleted_at = datetime.fromisoformat(data["deleted_at"])
            
        return server