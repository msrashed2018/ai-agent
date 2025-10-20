"""
Authentication API endpoints.
"""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.entities import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.token_service import TokenService, get_token_service

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> tuple[str, str]:
    """Create JWT access token with unique ID."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    expire = datetime.now(UTC) + expires_delta
    token_id = str(uuid.uuid4())

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "jti": token_id,  # JWT ID for tracking
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt, token_id


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Create JWT refresh token with unique ID."""
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    token_id = str(uuid.uuid4())

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": token_id,  # JWT ID for tracking
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt, token_id


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
    token_service: TokenService = Depends(get_token_service),
) -> LoginResponse:
    """
    Authenticate user and return JWT tokens.

    Returns access token (short-lived) and refresh token (long-lived).
    Use access token for API requests, refresh token to get new access tokens.
    """
    logger.info(f"Login attempt for email: {request.email}")

    # Get user by email
    repo = UserRepository(db)
    user = await repo.get_by_email(request.email)

    if user is None or not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.deleted_at is not None:
        logger.warning(f"Login attempt for deleted user: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted",
        )

    user_id = str(user.id)
    logger.info(f"User authenticated successfully: {user.email} (id={user_id})")

    # Create tokens
    access_token, access_token_id = create_access_token(user_id)
    refresh_token, refresh_token_id = create_refresh_token(user_id)
    logger.debug(f"Created tokens: access_id={access_token_id}, refresh_id={refresh_token_id}")

    # Calculate expiration times
    access_expires_at = (
        datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    refresh_expires_at = (
        datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    )

    # Store tokens in Redis
    logger.info(f"Storing tokens in Redis for user {user_id}")
    await token_service.store_token(
        access_token, user_id, "access", access_expires_at
    )
    await token_service.store_token(
        refresh_token, user_id, "refresh", refresh_expires_at
    )
    logger.info(f"Login successful for user {user.email}")

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
    token_service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    """
    Get new access token using refresh token.

    Refresh tokens are long-lived and can be used to obtain new access tokens
    without requiring the user to log in again.
    """
    # Validate refresh token and get new access token using token service
    new_access_token = await token_service.refresh_access_token(request.refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store the new access token in Redis
    # Extract user_id from the refresh token to get token metadata
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False}  # Allow expired tokens for user_id extraction
        )
        user_id = payload.get("sub")
        if user_id:
            expires_at = (
                datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
            )
            await token_service.store_token(new_access_token, user_id, "access", expires_at)
    except jwt.InvalidTokenError:
        # If we can't extract user_id, that's okay - token was already validated above
        pass

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """
    Logout user by revoking all their tokens.

    This endpoint invalidates all access and refresh tokens for the current user,
    effectively logging them out from all devices and sessions.
    """
    user_id = str(current_user.id)
    revoked_count = await token_service.revoke_all_user_tokens(user_id)

    return {
        "message": "Successfully logged out",
        "tokens_revoked": revoked_count,
        "user_id": user_id,
    }


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """
    Logout from all sessions (same as logout).

    This is an alias for the logout endpoint for consistency with other APIs.
    """
    user_id = str(current_user.id)
    revoked_count = await token_service.revoke_all_user_tokens(user_id)

    return {
        "message": "Successfully logged out from all sessions",
        "tokens_revoked": revoked_count,
        "user_id": user_id,
    }


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
