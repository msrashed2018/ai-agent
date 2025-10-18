"""
MCP Server-related schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import PaginatedResponse


class MCPServerCreateRequest(BaseModel):
    """Create MCP server request."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Server name (unique per user)")
    description: Optional[str] = Field(None, description="Server description")
    server_type: str = Field(..., description="Server type (stdio/sse/http)")
    config: Dict[str, Any] = Field(..., description="Server configuration")
    is_enabled: bool = Field(True, description="Whether server is enabled")


class MCPServerUpdateRequest(BaseModel):
    """Update MCP server request."""
    
    description: Optional[str] = Field(None, description="Server description")
    config: Optional[Dict[str, Any]] = Field(None, description="Server configuration")
    is_enabled: Optional[bool] = Field(None, description="Whether server is enabled")


class MCPServerResponse(BaseModel):
    """MCP server response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Server UUID")
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    server_type: str = Field(..., description="Server type (stdio/sse/http)")
    config: Dict[str, Any] = Field(..., description="Server configuration")
    is_enabled: bool = Field(..., description="Whether server is enabled")
    is_global: bool = Field(..., description="Whether server is global (admin-only)")
    health_status: Optional[str] = Field(None, description="Health status (healthy/unhealthy/unknown)")
    last_health_check_at: Optional[datetime] = Field(None, description="Last health check timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MCPServerListResponse(BaseModel):
    """MCP server list response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    items: List[MCPServerResponse] = Field(..., description="List of MCP servers")
    total: int = Field(..., description="Total number of servers")
