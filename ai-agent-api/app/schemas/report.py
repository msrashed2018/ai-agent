"""
Report-related schemas.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class ReportResponse(BaseModel):
    """Report response."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID = Field(..., description="Report UUID")
    session_id: UUID = Field(..., description="Session UUID")
    title: str = Field(..., description="Report title")
    description: Optional[str] = Field(None, description="Report description")
    report_type: str = Field(..., description="Report type (auto_generated/manual)")
    content: Dict[str, Any] = Field(..., description="Report content structure")
    file_format: str = Field(..., description="File format (html/pdf/json)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    storage_path: Optional[str] = Field(None, description="Storage path")
    created_at: datetime = Field(..., description="Creation timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links with download URLs")


class ReportListResponse(PaginatedResponse[ReportResponse]):
    """Paginated report list response."""
    pass
