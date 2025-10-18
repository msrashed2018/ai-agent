"""
Exception handlers for the FastAPI application.
"""

from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.claude_sdk.exceptions import (
    SDKError,
    ClientNotFoundError,
    ClientAlreadyExistsError,
    PermissionDeniedError,
)


logger = get_logger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": exc.errors(),
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle database errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Database error",
        extra={
            "request_id": request_id,
            "error": str(exc),
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": {
                    "type": exc.__class__.__name__,
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def sdk_exception_handler(
    request: Request,
    exc: SDKError,
) -> JSONResponse:
    """
    Handle Claude SDK errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "SDK error",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "error_type": exc.__class__.__name__,
        },
        exc_info=True,
    )
    
    # Map exception types to status codes
    status_code_map = {
        ClientNotFoundError: status.HTTP_404_NOT_FOUND,
        ClientAlreadyExistsError: status.HTTP_409_CONFLICT,
        PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    }
    
    status_code = status_code_map.get(
        exc.__class__,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": "CLAUDE_SDK_ERROR",
                "message": str(exc),
                "details": {
                    "type": exc.__class__.__name__,
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all other exceptions.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "error_type": exc.__class__.__name__,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {
                    "type": exc.__class__.__name__,
                },
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
