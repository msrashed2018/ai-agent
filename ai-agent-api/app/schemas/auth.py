"""
Authentication schemas.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class UserResponse(BaseModel):
    """User information response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    username: Optional[str] = Field(None, description="User username")
    role: str = Field(..., description="User role (admin, user, viewer)")
    is_active: bool = Field(True, description="User active status")
    created_at: datetime = Field(..., description="User creation timestamp")


class LoginResponse(BaseModel):
    """Login response with tokens and user info."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserResponse = Field(..., description="Authenticated user information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenResponse(BaseModel):
    """Token response."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
