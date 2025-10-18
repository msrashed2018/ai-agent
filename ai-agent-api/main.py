"""Main FastAPI application for AI-Agent-API-Service"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.api.v1 import api_v1_router
from app.api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from app.api.exception_handlers import (
    validation_exception_handler,
    database_exception_handler,
    sdk_exception_handler,
    generic_exception_handler,
)
from app.claude_sdk.exceptions import SDKError
from app.db import seed_default_data


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events"""
    # Startup
    setup_logging(
        level=settings.log_level,
        format=settings.log_format,
        log_file=settings.log_file,
    )
    
    logger.info(f"Starting {settings.project_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    logger.info(f"Redis: {settings.redis_url}")
    logger.info(f"Anthropic API: {'configured' if settings.anthropic_api_key else 'NOT configured'}")
    
    # Seed database with default data
    try:
        engine = create_async_engine(settings.database_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            await seed_default_data(session)
        
        await engine.dispose()
        logger.info("Database seeding completed")
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        # Don't fail startup if seeding fails
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.project_name}")


app = FastAPI(
    title=settings.project_name,
    description="AI-Agent-API-Service - Claude Code Agent Management and Execution",
    version=settings.version,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

# Add custom middleware (order matters - first added is outermost)
app.add_middleware(RateLimitMiddleware, rate_limit=1000, window_seconds=3600)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(SDKError, sdk_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API routers
app.include_router(api_v1_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.project_name,
        "version": settings.version,
        "description": "AI-Agent-API-Service for Claude Code Agent Management",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/api/v1/openapi.json",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
