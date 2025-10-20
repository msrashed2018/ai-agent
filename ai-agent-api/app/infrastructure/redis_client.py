"""Redis client configuration and connection pooling."""


from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisClientManager:
    """Manages Redis client lifecycle and connection pooling."""

    _instance: Redis | None = None
    _pool: ConnectionPool | None = None

    @classmethod
    async def initialize(cls) -> Redis:
        """Initialize Redis connection pool and client."""
        if cls._instance is not None:
            return cls._instance

        cls._pool = ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )

        cls._instance = Redis(connection_pool=cls._pool)

        # Test connection
        await cls._instance.ping()

        return cls._instance

    @classmethod
    def get_client(cls) -> Redis:
        """Get Redis client instance (must call initialize first)."""
        if cls._instance is None:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection."""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None


async def get_redis() -> Redis:
    """Dependency injection for Redis client."""
    return RedisClientManager.get_client()
