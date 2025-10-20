"""
Token management service for handling JWT token lifecycle in Redis.

This service manages token storage, validation, and revocation using Redis
as a high-performance token store with automatic expiration.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from redis.asyncio import Redis

from fastapi import Depends

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.redis_client import get_redis

logger = get_logger(__name__)


class TokenService:
    """Service for managing JWT tokens in Redis."""

    def __init__(self, redis_client: Redis):
        """Initialize token service with Redis client."""
        self.redis = redis_client
        self._token_prefix = "token:"
        self._blacklist_prefix = "blacklist:"
        self._user_tokens_prefix = "user_tokens:"

    async def store_token(
        self,
        token: str,
        user_id: str,
        token_type: str,
        expires_at: datetime | None = None
    ) -> str:
        """
        Store token in Redis with metadata.

        Args:
            token: JWT token string
            user_id: User ID the token belongs to
            token_type: 'access' or 'refresh'
            expires_at: Token expiration datetime (optional)

        Returns:
            Token ID for tracking
        """
        token_id = str(uuid.uuid4())
        logger.info(
            f"Storing {token_type} token for user {user_id}, token_id: {token_id}"
        )

        # Calculate TTL if not provided
        if expires_at is None:
            if token_type == "access":
                ttl = settings.jwt_access_token_expire_minutes * 60
            else:  # refresh token
                ttl = settings.jwt_refresh_token_expire_days * 24 * 3600
        else:
            ttl = int((expires_at - datetime.now(UTC)).total_seconds())

        logger.debug(f"Token TTL: {ttl} seconds ({ttl/3600:.1f} hours)")

        # Store token metadata
        token_data = {
            "token_id": token_id,
            "user_id": user_id,
            "token_type": token_type,
            "issued_at": datetime.now(UTC).isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

        # Store token with expiration
        await self.redis.setex(
            f"{self._token_prefix}{token_id}",
            ttl,
            json.dumps(token_data)
        )
        logger.debug(f"Token data stored in Redis: {self._token_prefix}{token_id}")

        # Add to user's token set for easy cleanup
        await self.redis.sadd(f"{self._user_tokens_prefix}{user_id}", token_id)

        # Set expiration on user's token set
        await self.redis.expire(f"{self._user_tokens_prefix}{user_id}", ttl)

        logger.info(f"Successfully stored {token_type} token {token_id} in Redis")
        return token_id

    async def get_token_data(self, token_id: str) -> dict | None:
        """Get token metadata from Redis."""
        token_data = await self.redis.get(f"{self._token_prefix}{token_id}")
        if token_data:
            return json.loads(token_data)
        return None

    async def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a specific token by adding it to blacklist.

        Args:
            token_id: Token ID to revoke

        Returns:
            True if token was revoked, False if not found
        """
        token_data = await self.get_token_data(token_id)
        if not token_data:
            return False

        # Add to blacklist with original expiration
        expires_at = token_data.get("expires_at")
        if expires_at:
            ttl = int((datetime.fromisoformat(expires_at) - datetime.now(UTC)).total_seconds())
            if ttl > 0:
                await self.redis.setex(f"{self._blacklist_prefix}{token_id}", ttl, "revoked")

        # Remove from active tokens
        await self.redis.srem(f"{self._user_tokens_prefix}{token_data['user_id']}", token_id)

        # Delete token data
        await self.redis.delete(f"{self._token_prefix}{token_id}")

        return True

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (logout all sessions).

        Args:
            user_id: User ID whose tokens to revoke

        Returns:
            Number of tokens revoked
        """
        user_tokens_key = f"{self._user_tokens_prefix}{user_id}"
        token_ids = await self.redis.smembers(user_tokens_key)

        revoked_count = 0
        for token_id in token_ids:
            if await self.revoke_token(token_id):
                revoked_count += 1

        # Clean up user's token set
        await self.redis.delete(user_tokens_key)

        return revoked_count

    async def is_token_revoked(self, token_id: str) -> bool:
        """Check if token is blacklisted."""
        return await self.redis.exists(f"{self._blacklist_prefix}{token_id}") == 1

    async def get_user_active_tokens(self, user_id: str) -> list[str]:
        """Get all active token IDs for a user."""
        return await self.redis.smembers(f"{self._user_tokens_prefix}{user_id}")

    async def validate_token_claims(self, token: str, token_type: str) -> tuple[bool, dict | None]:
        """
        Validate token claims and check if token is revoked.

        Args:
            token: JWT token to validate
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Tuple of (is_valid, token_data)
        """
        logger.debug(f"Validating {token_type} token")
        try:
            # Decode token payload
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            logger.debug(f"Token decoded successfully, type={payload.get('type')}, sub={payload.get('sub')}")

            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(
                    f"Token type mismatch: expected {token_type}, got {payload.get('type')}"
                )
                return False, None

            user_id = payload.get("sub")
            if not user_id:
                logger.error("Token missing user_id (sub claim)")
                return False, None

            # Extract token ID from payload
            token_id = payload.get("jti")  # JWT ID claim
            logger.debug(f"Token jti: {token_id}")

            if token_id:
                # Check if token is blacklisted
                is_revoked = await self.is_token_revoked(token_id)
                logger.debug(f"Token blacklist check: revoked={is_revoked}")
                if is_revoked:
                    logger.warning(f"Token {token_id} is blacklisted")
                    return False, None

                # Get token data if available (for additional metadata)
                token_data = await self.get_token_data(token_id)
                if token_data:
                    # Validate user_id matches
                    if token_data.get("user_id") == user_id:
                        logger.info(f"Token {token_id} validated successfully from Redis")
                        return True, token_data
                    else:
                        logger.error(
                            f"User ID mismatch: token={token_data.get('user_id')}, payload={user_id}"
                        )
                        return False, None
                else:
                    # Token not in Redis but has valid jti and not blacklisted
                    # This is okay - token is valid but not tracked in Redis
                    logger.info(
                        f"Token {token_id} not found in Redis but valid (JWT signature OK, not blacklisted)"
                    )
                    return True, {"user_id": user_id, "token_type": token_type}
            else:
                # Token without jti (backwards compatibility or old tokens)
                # Accept if JWT signature is valid
                logger.info(f"Token without jti accepted (backwards compatibility), user_id={user_id}")
                return True, {"user_id": user_id, "token_type": token_type}

            return False, None

        except jwt.ExpiredSignatureError as e:
            logger.warning(f"Token expired: {e}")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return False, None

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        """
        Validate refresh token and generate new access token data.

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token if refresh token is valid, None otherwise
        """
        is_valid, token_data = await self.validate_token_claims(refresh_token, "refresh")
        if not is_valid or not token_data:
            return None

        user_id = token_data["user_id"]

        # Create new access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        expires_at = datetime.now(UTC) + access_token_expires

        access_token = jwt.encode(
            {
                "sub": user_id,
                "exp": expires_at,
                "type": "access",
                "jti": str(uuid.uuid4()),  # Add unique token ID
            },
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

        return access_token


async def get_token_service(redis: Redis = Depends(get_redis)) -> TokenService:
    """Dependency injection for token service."""
    return TokenService(redis)
