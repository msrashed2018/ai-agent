"""
Common schemas for API requests/responses.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    model_config = ConfigDict(from_attributes=True)
    
    error: "ErrorDetail"


class ErrorDetail(BaseModel):
    """Error details."""
    
    code: str = Field(..., description="Error code (e.g., SESSION_NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias for page_size."""
        return self.page_size


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class Links(BaseModel):
    """HATEOAS links."""
    
    model_config = ConfigDict(extra="allow")
    
    self: Optional[str] = None


ErrorResponse.model_rebuild()
