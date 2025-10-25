"""Tool Group schemas."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class ToolGroupCreateRequest(BaseModel):
    """Create tool group request."""

    name: str = Field(..., min_length=1, max_length=255, description="Tool group name")
    description: Optional[str] = Field(None, description="Tool group description")
    allowed_tools: Optional[List[str]] = Field(None, description="List of allowed tools")
    disallowed_tools: Optional[List[str]] = Field(None, description="List of disallowed tools")


class ToolGroupUpdateRequest(BaseModel):
    """Update tool group request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tool group name")
    description: Optional[str] = Field(None, description="Tool group description")
    allowed_tools: Optional[List[str]] = Field(None, description="List of allowed tools")
    disallowed_tools: Optional[List[str]] = Field(None, description="List of disallowed tools")


class ToolGroupResponse(BaseModel):
    """Tool group response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(..., description="Tool group UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    name: str = Field(..., description="Tool group name")
    description: Optional[str] = Field(None, description="Tool group description")
    allowed_tools: List[str] = Field(default_factory=list, description="Allowed tools")
    disallowed_tools: List[str] = Field(default_factory=list, description="Disallowed tools")
    is_public: bool = Field(default=False, description="Is publicly available")
    is_active: bool = Field(default=True, description="Whether tool group is active")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class AddToolRequest(BaseModel):
    """Add tool to tool group request."""

    tool: str = Field(..., description="Tool pattern to add")


class RemoveToolRequest(BaseModel):
    """Remove tool from tool group request."""

    tool: str = Field(..., description="Tool pattern to remove")


class ToolGroupListResponse(BaseModel):
    """Paginated tool group list response."""

    model_config = ConfigDict(from_attributes=True)

    items: List[ToolGroupResponse] = Field(..., description="List of tool groups")
    total: int = Field(..., description="Total number of tool groups")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
