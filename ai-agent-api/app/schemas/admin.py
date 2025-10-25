"""
Admin-related schemas.
"""

from typing import Dict
from pydantic import BaseModel, Field, ConfigDict


class SystemStatsResponse(BaseModel):
    """System statistics response."""

    model_config = ConfigDict(from_attributes=True)

    sessions: Dict[str, int] = Field(..., description="Session statistics")
    tasks: Dict[str, int] = Field(..., description="Task statistics")
    users: Dict[str, int] = Field(..., description="User statistics")
    cost: Dict[str, float] = Field(..., description="Cost statistics")
    storage: Dict[str, int] = Field(..., description="Storage statistics")
