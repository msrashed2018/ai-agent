"""
Authentication schemas.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    """Login request."""
    
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    """Login response with tokens."""
    
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenResponse(BaseModel):
    """Token response."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
