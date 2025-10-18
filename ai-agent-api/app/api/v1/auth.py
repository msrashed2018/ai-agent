"""
Authentication API endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import bcrypt

from app.api.dependencies import get_db_session, get_current_active_user
from app.core.config import settings
from app.domain.entities import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.
    
    Returns access token (short-lived) and refresh token (long-lived).
    Use access token for API requests, refresh token to get new access tokens.
    """
    # Get user by email
    repo = UserRepository(db)
    user = await repo.get_by_email(request.email)
    
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )
    
    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Get new access token using refresh token.
    
    Refresh tokens are long-lived and can be used to obtain new access tokens
    without requiring the user to log in again.
    """
    try:
        # Decode refresh token
        payload = jwt.decode(
            request.refresh_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    
    if user is None or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token = create_access_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get current authenticated user information.
    
    Returns user profile from JWT token.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
    }
