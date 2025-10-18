"""
Session template schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class SessionTemplateCreateRequest(BaseModel):
    """Create session template request."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category (development/security/production/debugging/performance/custom)")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    working_directory: Optional[str] = Field(None, max_length=500, description="Default working directory path")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns (glob)")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="Claude SDK options")
    mcp_server_ids: Optional[List[UUID]] = Field(None, description="MCP server UUIDs to attach")
    is_public: bool = Field(False, description="Make template publicly available")
    is_organization_shared: bool = Field(False, description="Share template with organization")
    tags: Optional[List[str]] = Field(None, description="Template tags for search/categorization")
    template_metadata: Optional[Dict[str, Any]] = Field(None, description="Custom template metadata")


class SessionTemplateUpdateRequest(BaseModel):
    """Update session template request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    working_directory: Optional[str] = Field(None, max_length=500, description="Default working directory path")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="Claude SDK options")
    mcp_server_ids: Optional[List[UUID]] = Field(None, description="MCP server UUIDs")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    template_metadata: Optional[Dict[str, Any]] = Field(None, description="Custom template metadata")


class SessionTemplateSharingUpdateRequest(BaseModel):
    """Update template sharing settings request."""

    is_public: Optional[bool] = Field(None, description="Make template publicly available")
    is_organization_shared: Optional[bool] = Field(None, description="Share template with organization")


class SessionTemplateResponse(BaseModel):
    """Session template response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(..., description="Template UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    working_directory: Optional[str] = Field(None, description="Default working directory")
    allowed_tools: List[str] = Field(default_factory=list, description="Allowed tool patterns")
    sdk_options: Dict[str, Any] = Field(default_factory=dict, description="Claude SDK options")
    mcp_server_ids: List[UUID] = Field(default_factory=list, description="Attached MCP server UUIDs")
    is_public: bool = Field(..., description="Is publicly available")
    is_organization_shared: bool = Field(..., description="Is shared with organization")
    version: str = Field(..., description="Template version")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    template_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    usage_count: int = Field(..., description="Number of times template was used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    links: Links = Field(default_factory=Links, description="HATEOAS links", alias="_links")


class SessionTemplateListResponse(PaginatedResponse[SessionTemplateResponse]):
    """Paginated session template list response."""
    pass


class SessionTemplateSearchRequest(BaseModel):
    """Search templates request."""

    search_term: Optional[str] = Field(None, min_length=1, max_length=255, description="Search in template names")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (matches any)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class CreateSessionFromTemplateRequest(BaseModel):
    """Create session from template request."""

    template_id: UUID = Field(..., description="Template UUID to use")
    name: Optional[str] = Field(None, max_length=255, description="Override session name")
    description: Optional[str] = Field(None, description="Override session description")
    working_directory: Optional[str] = Field(None, description="Override working directory")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="Override SDK options (merged with template)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional session metadata")
