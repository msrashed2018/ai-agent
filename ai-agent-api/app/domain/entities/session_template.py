"""Session template domain entity."""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TemplateCategory(str, Enum):
    """Template category enumeration."""
    DEVELOPMENT = "development"
    SECURITY = "security"
    PRODUCTION = "production"
    DEBUGGING = "debugging"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class SessionTemplate:
    """Session template aggregate root."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        sdk_options: Optional[dict] = None,
        mcp_server_ids: Optional[List[UUID]] = None,
        is_public: bool = False,
        is_organization_shared: bool = False,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        template_metadata: Optional[dict] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.category = category
        self.system_prompt = system_prompt
        self.working_directory = working_directory
        self.allowed_tools = allowed_tools or []
        self.sdk_options = sdk_options or {}
        self.mcp_server_ids = mcp_server_ids or []
        self.is_public = is_public
        self.is_organization_shared = is_organization_shared
        self.version = version
        self.tags = tags or []
        self.template_metadata = template_metadata or {}

        # Usage statistics
        self.usage_count = 0
        self.last_used_at: Optional[datetime] = None

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deleted_at: Optional[datetime] = None

    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_configuration(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[TemplateCategory] = None,
        system_prompt: Optional[str] = None,
        working_directory: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        sdk_options: Optional[dict] = None,
        mcp_server_ids: Optional[List[UUID]] = None,
    ) -> None:
        """Update template configuration."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if working_directory is not None:
            self.working_directory = working_directory
        if allowed_tools is not None:
            self.allowed_tools = allowed_tools
        if sdk_options is not None:
            self.sdk_options = sdk_options
        if mcp_server_ids is not None:
            self.mcp_server_ids = mcp_server_ids

        self.updated_at = datetime.utcnow()

    def update_sharing_settings(
        self,
        is_public: Optional[bool] = None,
        is_organization_shared: Optional[bool] = None,
    ) -> None:
        """Update template sharing settings."""
        if is_public is not None:
            self.is_public = is_public
        if is_organization_shared is not None:
            self.is_organization_shared = is_organization_shared

        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the template."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the template."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata: dict) -> None:
        """Update template metadata."""
        self.template_metadata.update(metadata)
        self.updated_at = datetime.utcnow()

    def is_accessible_by_user(self, user_id: UUID, user_organization_id: Optional[UUID] = None) -> bool:
        """Check if template is accessible by a specific user."""
        # Owner always has access
        if self.user_id == user_id:
            return True

        # Public templates are accessible to everyone
        if self.is_public:
            return True

        # Organization-shared templates are accessible to org members
        if self.is_organization_shared and user_organization_id:
            # Note: This requires user's organization_id to match template owner's organization
            # The actual org check should be done at the service layer
            return True

        return False

    def soft_delete(self) -> None:
        """Mark template as deleted (soft delete)."""
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        """Check if template is soft-deleted."""
        return self.deleted_at is not None

    def clone_configuration(self) -> dict:
        """Get template configuration for session creation."""
        return {
            "system_prompt": self.system_prompt,
            "working_directory": self.working_directory,
            "allowed_tools": self.allowed_tools.copy() if self.allowed_tools else [],
            "sdk_options": self.sdk_options.copy() if self.sdk_options else {},
            "mcp_server_ids": self.mcp_server_ids.copy() if self.mcp_server_ids else [],
        }
