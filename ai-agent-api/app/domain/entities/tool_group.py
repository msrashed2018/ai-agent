"""Tool Group domain entity."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ToolGroup:
    """Tool group definition for organizing allowed and disallowed tools."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description

        # Tool lists
        self.allowed_tools: List[str] = []
        self.disallowed_tools: List[str] = []

        # Metadata
        self.is_public = False
        self.is_active = True
        self.is_deleted = False

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deleted_at: Optional[datetime] = None

    def add_allowed_tool(self, tool: str) -> None:
        """Add tool to allowed list."""
        if tool not in self.allowed_tools:
            self.allowed_tools.append(tool)

    def remove_allowed_tool(self, tool: str) -> None:
        """Remove tool from allowed list."""
        if tool in self.allowed_tools:
            self.allowed_tools.remove(tool)

    def add_disallowed_tool(self, tool: str) -> None:
        """Add tool to disallowed list."""
        if tool not in self.disallowed_tools:
            self.disallowed_tools.append(tool)

    def remove_disallowed_tool(self, tool: str) -> None:
        """Remove tool from disallowed list."""
        if tool in self.disallowed_tools:
            self.disallowed_tools.remove(tool)

    def soft_delete(self) -> None:
        """Soft delete the tool group."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the tool group."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the tool group."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
