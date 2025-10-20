"""
FastAPI dependencies for dependency injection.
"""

import jwt
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_db as get_db_session
from app.domain.entities import User
from app.repositories.user_repository import UserRepository
from app.services.token_service import TokenService, get_token_service

# Security scheme
security = HTTPBearer()
logger = get_logger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database session
        token_service: Token service for blacklist checking

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: If token is invalid, expired, or blacklisted
    """
    token = credentials.credentials
    logger.debug(f"Authenticating request with token: {token[:20]}...")

    # Validate token claims and check blacklist using token service
    is_valid, token_data = await token_service.validate_token_claims(token, "access")

    if not is_valid:
        logger.warning("Token validation failed: token is invalid or expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token_data:
        logger.error("Token validation returned no data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.get("user_id")
    if not user_id:
        logger.error("Token data missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Token validated, fetching user {user_id} from database")

    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        logger.warning(f"User {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User {user.email} authenticated successfully")
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
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
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
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """
    Authenticate WebSocket connection with JWT token.

    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter
        db: Database session
        token_service: Token service for blacklist checking

    Returns:
        User: Authenticated user

    Raises:
        Exception: If authentication fails (WebSocket will be closed)
    """
    try:
        # Validate token using token service (includes blacklist check)
        is_valid, token_data = await token_service.validate_token_claims(token, "access")

        if not is_valid or not token_data:
            raise ValueError("Token has expired or been revoked")

        user_id = token_data.get("user_id")
        if not user_id:
            raise ValueError("Invalid token")

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)

        if user is None or user.deleted_at is not None:
            raise ValueError("User not found or deleted")

        return user
    except Exception as e:
        await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
        raise


async def get_session_manager(
    db: AsyncSession = Depends(get_db_session)
):
    """Get SessionManager instance."""
    from app.claude_sdk.core.session_manager import SessionManager
    return SessionManager(db)


async def get_hook_manager(
    db: AsyncSession = Depends(get_db_session)
):
    """Get HookManager instance."""
    from app.claude_sdk.hooks.hook_manager import HookManager
    from app.repositories.hook_execution_repository import HookExecutionRepository
    return HookManager(db, HookExecutionRepository(db))


async def get_permission_manager(
    db: AsyncSession = Depends(get_db_session)
):
    """Get PermissionManager instance."""
    from app.claude_sdk.permissions.permission_manager import PermissionManager
    from app.claude_sdk.permissions.policy_engine import PolicyEngine
    from app.repositories.permission_decision_repository import PermissionDecisionRepository

    policy_engine = PolicyEngine()
    # Register default policies
    # TODO: Load and register policies based on configuration

    return PermissionManager(db, policy_engine, PermissionDecisionRepository(db))


async def get_storage_archiver():
    """Get StorageArchiver instance."""
    from app.claude_sdk.persistence.storage_archiver import StorageArchiver
    from app.core.config import settings

    return StorageArchiver(
        provider=settings.storage_provider,
        bucket=settings.aws_s3_bucket if settings.storage_provider == "s3" else None,
        region=settings.aws_s3_region if settings.storage_provider == "s3" else None
    )


async def get_metrics_collector(
    db: AsyncSession = Depends(get_db_session)
):
    """Get MetricsCollector instance."""
    from app.claude_sdk.monitoring.metrics_collector import MetricsCollector
    return MetricsCollector(db)


async def get_cost_tracker(
    db: AsyncSession = Depends(get_db_session)
):
    """Get CostTracker instance."""
    from app.claude_sdk.monitoring.cost_tracker import CostTracker
    return CostTracker(db)


async def get_health_checker(
    db: AsyncSession = Depends(get_db_session)
):
    """Get HealthChecker instance."""
    from app.claude_sdk.monitoring.health_checker import HealthChecker
    return HealthChecker(db)


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_admin",
    "get_optional_user",
    "get_websocket_user",
    "get_db_session",
    "get_session_manager",
    "get_hook_manager",
    "get_permission_manager",
    "get_storage_archiver",
    "get_metrics_collector",
    "get_cost_tracker",
    "get_health_checker",
]
