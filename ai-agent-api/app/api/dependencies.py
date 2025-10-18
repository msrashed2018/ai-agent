"""
FastAPI dependencies for dependency injection.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.database.session import get_db as get_db_session
from app.core.config import settings
from app.domain.entities import User
from app.repositories.user_repository import UserRepository


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database session
    
    Returns:
        User: Authenticated user
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (non-deleted).
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Active user
    
    Raises:
        HTTPException: If user is deleted
    """
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require admin role.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Admin user
    
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Get optional authenticated user (for endpoints that work with/without auth).
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
    
    Returns:
        Optional[User]: Authenticated user or None
    """
    if credentials is None:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


async def get_websocket_user(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Authenticate WebSocket connection with JWT token.
    
    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter
        db: Database session
    
    Returns:
        User: Authenticated user
    
    Raises:
        Exception: If authentication fails (WebSocket will be closed)
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if user is None or user.deleted_at is not None:
            raise ValueError("User not found or deleted")
        
        return user
    except Exception as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
        raise


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "get_optional_user",
    "get_websocket_user",
    "get_db_session",
]
