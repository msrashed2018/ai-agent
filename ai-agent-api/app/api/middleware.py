"""
Custom middleware for the FastAPI application.
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger


logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request for tracing.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests and responses.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )
            
            # Add timing header
            response.headers["X-Response-Time"] = f"{round(duration_ms, 2)}ms"
            
            return response
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
                exc_info=True,
            )
            
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting (for production use Redis-based rate limiting).
    """
    
    def __init__(self, app, rate_limit: int = 1000, window_seconds: int = 3600):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.requests: dict = {}  # {client_ip: [(timestamp, path), ...]}
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, path)
                for ts, path in self.requests[client_ip]
                if current_time - ts < self.window_seconds
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        request_count = len(self.requests[client_ip])
        
        if request_count >= self.rate_limit:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "request_count": request_count,
                    "rate_limit": self.rate_limit,
                }
            )
            
            # Calculate retry after
            oldest_request = min(ts for ts, _ in self.requests[client_ip])
            retry_after = int(self.window_seconds - (current_time - oldest_request)) + 1
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "details": {
                            "limit": self.rate_limit,
                            "window_seconds": self.window_seconds,
                            "retry_after_seconds": retry_after,
                        }
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after)),
                }
            )
        
        # Record request
        self.requests[client_ip].append((current_time, request.url.path))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.rate_limit - request_count - 1
        reset_time = int(current_time + self.window_seconds)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


class CORSHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add CORS headers (for development, use FastAPI's CORSMiddleware in production).
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        response = await call_next(request)
        
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Response-Time"
        
        return response
