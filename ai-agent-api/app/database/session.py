"""Database session management."""
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create async engine with conditional pool configuration
engine_kwargs = {
    "echo": False,  # Disable SQLAlchemy echo to respect logging configuration
    "pool_pre_ping": True,
}

# Only add pool parameters if not using NullPool
if settings.environment == "test":
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = settings.database_pool_size
    engine_kwargs["max_overflow"] = settings.database_max_overflow

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting async database session.

    Useful for Celery tasks and other non-FastAPI contexts where
    we need an async context manager instead of a FastAPI dependency.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
