# Error Handling Guide

**Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Exception hierarchy, error handling patterns, and best practices for AI-Agent-API

---

## Overview

The AI-Agent-API uses a **layered exception hierarchy** where errors are raised at the appropriate layer and handled at the layer above. This ensures clean separation of concerns and provides meaningful error messages to clients.

**Philosophy**:
- **Fail Fast**: Raise specific errors immediately when validation fails
- **Log Everything**: Log all errors with full context
- **Return Meaningful Messages**: Provide clear, actionable error messages
- **Never Expose Sensitive Data**: Never return passwords, tokens, or internal details

---

## Exception Hierarchy

### Domain Exceptions

**Location**: `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/domain/exceptions.py`

Domain exceptions represent **business rule violations** and are raised by domain entities.

```python
# Base Exception
class DomainException(Exception):
    """Base exception for domain errors."""
    pass

# Validation Errors
class ValidationError(DomainException):
    """Raised when domain validation fails."""
    pass

# State Transition Errors
class InvalidStateTransitionError(DomainException):
    """Raised when invalid state transition is attempted."""
    pass

# Resource Not Found
class SessionNotFoundError(DomainException):
    """Raised when session is not found."""
    pass

class TaskNotFoundError(DomainException):
    """Raised when task is not found."""
    pass

class ReportNotFoundError(DomainException):
    """Raised when report is not found."""
    pass

class TemplateNotFoundError(DomainException):
    """Raised when template is not found."""
    pass

class UserNotFoundError(DomainException):
    """Raised when user is not found."""
    pass

class ResourceNotFoundError(DomainException):
    """Raised when a generic resource is not found."""
    pass

# Business Logic Errors
class SessionNotActiveError(DomainException):
    """Raised when operation requires active session."""
    pass

class SessionCannotResumeError(DomainException):
    """Raised when session cannot be resumed."""
    pass

# Permission & Quota Errors
class PermissionDeniedError(DomainException):
    """Raised when user lacks permission for operation."""
    pass

class QuotaExceededError(DomainException):
    """Raised when user quota is exceeded."""
    pass

# Operational Errors
class InvalidOperationError(DomainException):
    """Raised when operation is invalid in current context."""
    pass

class ConcurrencyError(DomainException):
    """Raised when concurrent modification conflict occurs."""
    pass
```

### SDK Exceptions

**Location**: `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/claude_sdk/exceptions.py`

SDK exceptions represent **errors from Claude SDK integration**.

```python
# Base Exception
class SDKError(Exception):
    """Base exception for Claude SDK errors."""
    pass

# Client Management
class ClientAlreadyExistsError(SDKError):
    """Raised when attempting to create a client that already exists."""
    pass

class ClientNotFoundError(SDKError):
    """Raised when client is not found in the manager."""
    pass

# Connection & Runtime Errors
class SDKConnectionError(SDKError):
    """Raised when SDK connection fails."""
    pass

class SDKRuntimeError(SDKError):
    """Raised when SDK runtime error occurs."""
    pass

# Permission & Circuit Breaker
class PermissionDeniedError(SDKError):
    """Raised when tool permission is denied."""
    pass

class CircuitBreakerOpenError(SDKError):
    """Raised when circuit breaker is open and request is rejected."""
    pass
```

### FastAPI HTTP Exceptions

FastAPI's built-in `HTTPException` is used at the **API layer**.

```python
from fastapi import HTTPException

# Common HTTP exceptions
HTTPException(status_code=400, detail="Bad Request")
HTTPException(status_code=401, detail="Unauthorized")
HTTPException(status_code=403, detail="Forbidden")
HTTPException(status_code=404, detail="Not Found")
HTTPException(status_code=409, detail="Conflict")
HTTPException(status_code=422, detail="Validation Error")
HTTPException(status_code=429, detail="Too Many Requests")
HTTPException(status_code=500, detail="Internal Server Error")
HTTPException(status_code=503, detail="Service Unavailable")
```

---

## Error Flow by Layer

### 1. Domain Layer

**Responsibility**: Raise domain exceptions when business rules are violated.

```python
# app/domain/entities/session.py
from app.domain.exceptions import InvalidStateTransitionError

class Session:
    def transition_to(self, new_status: SessionStatus):
        """Transition to a new status."""
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def can_transition_to(self, new_status: SessionStatus) -> bool:
        """Check if transition is valid."""
        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.CONNECTING, SessionStatus.TERMINATED],
            SessionStatus.ACTIVE: [SessionStatus.PAUSED, SessionStatus.COMPLETED],
            # ... more transitions
        }
        return new_status in valid_transitions.get(self.status, [])
```

### 2. Service Layer

**Responsibility**: Catch domain exceptions, add context, and may wrap or re-raise.

```python
# app/services/session_service.py
from app.core.logging import get_logger
from app.domain.exceptions import InvalidStateTransitionError, SessionNotFoundError

logger = get_logger(__name__)

class SessionService:
    async def activate_session(self, session_id: UUID, user_id: UUID) -> Session:
        """Activate a session."""
        # Get session
        session = await self.get_session(session_id, user_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        try:
            # Attempt state transition
            session.transition_to(SessionStatus.ACTIVE)

            # Persist changes
            await self._save(session)

            # Audit log
            await self.audit_service.log_session_activated(session_id, user_id)

            logger.info(
                "Session activated",
                extra={"session_id": str(session_id), "user_id": str(user_id)}
            )

            return session

        except InvalidStateTransitionError as e:
            logger.error(
                "Failed to activate session",
                extra={
                    "session_id": str(session_id),
                    "current_status": session.status.value,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise SessionNotActiveError(
                f"Cannot activate session in {session.status} status"
            ) from e
```

### 3. API Layer

**Responsibility**: Convert domain/service exceptions to HTTP exceptions.

```python
# app/api/v1/sessions.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.exceptions import (
    SessionNotFoundError,
    SessionNotActiveError,
    PermissionDeniedError,
)

router = APIRouter()

@router.post("/sessions/{session_id}/activate")
async def activate_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    current_user: User = Depends(get_current_user),
):
    """Activate a session."""
    try:
        session = await service.activate_session(session_id, current_user.id)
        return SessionResponse.from_entity(session)

    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except SessionNotActiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    except Exception as e:
        logger.error(
            "Unexpected error activating session",
            extra={"session_id": str(session_id), "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred",
        )
```

---

## Global Exception Handlers

**Location**: `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/api/exception_handlers.py`

Global exception handlers catch unhandled exceptions and return standardized error responses.

### Validation Exception Handler

Handles Pydantic validation errors (422 Unprocessable Entity).

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
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
                "details": {"errors": exc.errors()},
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
```

### Database Exception Handler

Handles SQLAlchemy database errors (500 Internal Server Error).

```python
from sqlalchemy.exc import SQLAlchemyError

async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle database errors."""
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
                "details": {"type": exc.__class__.__name__},
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
```

### SDK Exception Handler

Handles Claude SDK errors with appropriate status codes.

```python
from app.claude_sdk.exceptions import (
    SDKError,
    ClientNotFoundError,
    ClientAlreadyExistsError,
    PermissionDeniedError,
    CircuitBreakerOpenError,
)

async def sdk_exception_handler(
    request: Request,
    exc: SDKError,
) -> JSONResponse:
    """Handle Claude SDK errors."""
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
        CircuitBreakerOpenError: status.HTTP_503_SERVICE_UNAVAILABLE,
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
                "details": {"type": exc.__class__.__name__},
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
```

### Generic Exception Handler

Catches all other unhandled exceptions.

```python
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all other exceptions."""
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
                "details": {"type": exc.__class__.__name__},
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
```

### Registering Exception Handlers

```python
# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.exception_handlers import (
    validation_exception_handler,
    database_exception_handler,
    sdk_exception_handler,
    generic_exception_handler,
)
from app.claude_sdk.exceptions import SDKError

app = FastAPI()

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(SDKError, sdk_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

---

## Error Response Format

All error responses follow a **consistent JSON structure**:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "type": "ExceptionClassName",
      "errors": []
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-10-19T12:00:00.000Z"
  }
}
```

### Examples

**404 Not Found**:
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": {
      "type": "SessionNotFoundError"
    },
    "request_id": "req_12345",
    "timestamp": "2025-10-19T12:00:00.000Z"
  }
}
```

**422 Validation Error**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "errors": [
        {
          "loc": ["body", "mode"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    },
    "request_id": "req_12345",
    "timestamp": "2025-10-19T12:00:00.000Z"
  }
}
```

---

## HTTP Status Codes

### 4xx Client Errors

| Code | Status | Usage |
|------|--------|-------|
| 400 | Bad Request | Invalid input, invalid state |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |

### 5xx Server Errors

| Code | Status | Usage |
|------|--------|-------|
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Circuit breaker open, service down |

---

## Logging Errors

### Log with Full Context

Always include:
- **User ID**: Who encountered the error
- **Session ID**: Which session (if applicable)
- **Request ID**: For tracing
- **Error Type**: Exception class name
- **Stack Trace**: For 500 errors

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    session = await service.create_session(...)
except Exception as e:
    logger.error(
        "Failed to create session",
        extra={
            "user_id": str(user_id),
            "error": str(e),
            "error_type": e.__class__.__name__,
            "sdk_options": sdk_options,
        },
        exc_info=True,  # Include stack trace
    )
    raise
```

### Log Levels for Errors

```python
# WARNING - Expected errors, recoverable
logger.warning(
    "Session quota nearing limit",
    extra={"user_id": str(user_id), "active_sessions": count}
)

# ERROR - Unexpected errors, may recover
logger.error(
    "Failed to connect to SDK",
    extra={"session_id": str(session_id)},
    exc_info=True,
)

# CRITICAL - System-level failures
logger.critical(
    "Database connection pool exhausted",
    exc_info=True,
)
```

### Never Log Sensitive Data

```python
# BAD - Logging secrets
logger.error(f"API key validation failed: {api_key}")  # NEVER!
logger.error(f"Password mismatch: {password}")  # NEVER!
logger.error(f"JWT token expired: {token}")  # NEVER!

# GOOD - Log safely
logger.error("API key validation failed", extra={"key_prefix": api_key[:8]})
logger.error("Password validation failed", extra={"user_id": str(user_id)})
logger.error("JWT token expired", extra={"user_id": str(user_id)})
```

---

## Retry Logic

For **transient failures**, implement retry with exponential backoff.

### Retry Manager Pattern

```python
# app/claude_sdk/retry_manager.py
import asyncio
from typing import Callable, TypeVar

T = TypeVar('T')

class RetryManager:
    """Manages retry logic for transient failures."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except (ConnectionError, TimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(
                        self.base_delay * (2 ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{self.max_retries}",
                        extra={
                            "delay_seconds": delay,
                            "error": str(e),
                        }
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Max retries exceeded",
                        extra={"attempts": self.max_retries},
                    )

        raise last_exception
```

### Usage

```python
retry_manager = RetryManager(max_retries=3)

try:
    result = await retry_manager.execute_with_retry(
        sdk_client.query,
        message="Hello"
    )
except Exception as e:
    logger.error("Operation failed after retries", exc_info=e)
    raise
```

---

## Circuit Breaker

Prevent cascading failures by **opening the circuit** after repeated failures.

### Circuit Breaker Pattern

```python
# app/claude_sdk/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset circuit on success."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Record failure."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker opened due to failures")

    def _should_attempt_reset(self) -> bool:
        """Check if timeout has passed."""
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_seconds
```

---

## Error Handling Best Practices

### 1. Use Specific Exceptions

```python
# GOOD - Specific exception
if not session:
    raise SessionNotFoundError(f"Session {session_id} not found")

# BAD - Generic exception
if not session:
    raise Exception("Session not found")  # Too generic!
```

### 2. Don't Catch Exception (Too Broad)

```python
# BAD - Catches everything
try:
    result = await process()
except Exception:  # Too broad!
    pass

# GOOD - Catch specific exceptions
try:
    result = await process()
except (ValidationError, SessionNotFoundError) as e:
    logger.error("Processing failed", exc_info=e)
    raise
```

### 3. Always Log Errors

```python
# BAD - Silent failure
try:
    await process()
except Exception:
    pass  # Error disappears!

# GOOD - Log and re-raise
try:
    await process()
except Exception as e:
    logger.error("Process failed", exc_info=e)
    raise
```

### 4. Include Error Context

```python
# BAD - No context
raise ValidationError("Invalid input")

# GOOD - Helpful context
raise ValidationError(
    f"Invalid SDK options: max_turns must be positive, got {max_turns}"
)
```

### 5. Return User-Friendly Messages

```python
# BAD - Internal error exposed
raise HTTPException(
    status_code=500,
    detail="NoneType object has no attribute 'id'"  # Confusing!
)

# GOOD - User-friendly message
raise HTTPException(
    status_code=400,
    detail="Session must be in 'created' status to activate"
)
```

---

## Error Handling Patterns

### Pattern 1: Domain Entity Validation

```python
# Domain entity validates and raises specific error
class Session:
    def transition_to(self, new_status: SessionStatus):
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
```

### Pattern 2: Service Layer Error Handling

```python
# Service catches domain errors and adds context
class SessionService:
    async def activate_session(self, session_id: UUID) -> Session:
        try:
            session = await self.get_session(session_id)
            session.transition_to(SessionStatus.ACTIVE)
            await self._save(session)
            return session
        except InvalidStateTransitionError as e:
            logger.error("Activation failed", exc_info=e)
            raise SessionNotActiveError(str(e)) from e
```

### Pattern 3: API Layer HTTP Conversion

```python
# API converts to HTTP exceptions
@router.post("/sessions/{session_id}/activate")
async def activate_session(session_id: UUID, service: SessionService):
    try:
        session = await service.activate_session(session_id)
        return SessionResponse.from_entity(session)
    except SessionNotActiveError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## Related Files

**Exception Definitions**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/domain/exceptions.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/claude_sdk/exceptions.py`

**Exception Handlers**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/api/exception_handlers.py`

**Retry & Circuit Breaker**:
- See `docs/components/claude_sdk/RETRY_RESILIENCE.md`

---

## Keywords

error-handling, exceptions, exception-hierarchy, domain-exceptions, sdk-exceptions, http-exceptions, error-responses, status-codes, logging, error-logging, retry-logic, circuit-breaker, error-patterns, validation-errors, state-transition-errors, resource-not-found, permission-denied, quota-exceeded, exception-handlers, global-handlers, fastapi-exceptions, structured-errors, error-messages

---

**Related Documentation**:
- [CODE_PATTERNS.md](./CODE_PATTERNS.md) - Error handling patterns
- [DEBUGGING_GUIDE.md](./DEBUGGING_GUIDE.md) - Debugging errors
- [RETRY_RESILIENCE.md](../components/claude_sdk/RETRY_RESILIENCE.md) - Retry and circuit breaker details
