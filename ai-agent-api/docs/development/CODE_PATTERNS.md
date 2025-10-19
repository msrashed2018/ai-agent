# Code Patterns and Standards

**Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Coding standards, patterns, and best practices for AI-Agent-API

---

## Overview

This document defines the coding standards, architectural patterns, and best practices used in the AI-Agent-API codebase. Following these patterns ensures consistency, maintainability, and code quality.

---

## Code Organization

### Layered Architecture

The codebase follows a strict layered architecture with clear separation of concerns:

```
app/
├── api/                    # API Layer - FastAPI routes, request/response handling
│   ├── v1/                 # API version 1 endpoints
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── exception_handlers.py  # Global exception handlers
│   └── middleware.py       # Custom middleware
├── domain/                 # Domain Layer - Business entities and rules
│   ├── entities/           # Aggregate roots and entities
│   ├── value_objects/      # Immutable value objects
│   └── exceptions.py       # Domain-specific exceptions
├── services/               # Service Layer - Business logic orchestration
├── repositories/           # Repository Layer - Data access
├── models/                 # ORM Models - SQLAlchemy database models
├── claude_sdk/             # Claude SDK Integration - SDK wrapper and utilities
├── mcp_tools/              # MCP Tool Implementations
├── core/                   # Core Utilities - Config, logging, etc.
└── database/               # Database - Connection and base classes
```

### Where to Put New Code

**API Endpoint** → `app/api/v1/`
- HTTP request/response handling
- Input validation (Pydantic models)
- Authentication/authorization checks
- Call service layer

**Business Logic** → `app/services/`
- Orchestrate domain entities
- Coordinate repositories
- Transaction management
- Call external services

**Domain Logic** → `app/domain/entities/`
- Business rules
- State transitions
- Domain validations

**Data Access** → `app/repositories/`
- Database queries
- CRUD operations
- Data filtering and pagination

**Database Models** → `app/models/`
- SQLAlchemy ORM models
- Table definitions
- Relationships

---

## Coding Standards

### PEP 8 Compliance

We enforce PEP 8 with the following tools:

```bash
# Format code
make format  # Uses Black + Ruff

# Check formatting
make lint    # Uses Ruff

# Type checking
make type-check  # Uses mypy
```

**Configuration**:
- **Black**: Line length 100 characters
- **Ruff**: Checks E, F, I, N, W, UP rules
- **Mypy**: Strict type checking

### Line Length

**Maximum**: 100 characters

```python
# GOOD
def create_session(
    user_id: UUID,
    mode: SessionMode,
    sdk_options: dict,
) -> Session:
    pass

# BAD - Line too long
def create_session(user_id: UUID, mode: SessionMode, sdk_options: dict, name: Optional[str] = None, parent_session_id: Optional[UUID] = None) -> Session:
    pass
```

### Type Hints

**Always use type hints** on all functions and methods:

```python
# GOOD - Complete type hints
async def create_session(
    self,
    user_id: UUID,
    mode: SessionMode,
    sdk_options: dict,
    name: Optional[str] = None,
) -> Session:
    """Create a new session."""
    pass

# BAD - Missing type hints
async def create_session(self, user_id, mode, sdk_options, name=None):
    pass
```

### Docstrings

Use **Google-style docstrings** for all public classes and methods:

```python
def create_session(
    self,
    user_id: UUID,
    mode: SessionMode,
    sdk_options: dict,
) -> Session:
    """Create and initialize a new session.

    Args:
        user_id: User identifier who owns the session
        mode: Session mode (interactive, non_interactive, forked)
        sdk_options: Claude SDK configuration options

    Returns:
        Session: Created session domain entity

    Raises:
        QuotaExceededError: User has exceeded session quota
        ValidationError: Invalid SDK options provided
    """
    pass
```

### Import Ordering

Imports are organized using **Ruff** in this order:

```python
# 1. Standard library
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

# 2. Third-party packages
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

# 3. Local application imports
from app.core.logging import get_logger
from app.domain.entities.session import Session, SessionStatus
from app.domain.exceptions import SessionNotFoundError
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService
```

---

## Naming Conventions

### Classes

**PascalCase** for class names:

```python
# GOOD
class SessionService:
    pass

class UserRepository:
    pass

class SessionNotFoundError(DomainException):
    pass

# BAD
class session_service:
    pass

class userRepo:
    pass
```

### Functions and Methods

**snake_case** for function and method names:

```python
# GOOD
async def create_session(user_id: UUID) -> Session:
    pass

async def get_active_sessions(user_id: UUID) -> List[Session]:
    pass

# BAD
async def CreateSession(user_id: UUID) -> Session:
    pass

async def getActiveSessions(user_id: UUID) -> List[Session]:
    pass
```

### Constants

**UPPER_SNAKE_CASE** for constants:

```python
# GOOD
MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 120
SESSION_ARCHIVE_DAYS = 180

# BAD
maxRetries = 3
default_timeout_seconds = 120
```

### Private Methods

**Leading underscore** for private methods:

```python
class SessionService:
    async def create_session(self) -> Session:
        """Public method."""
        await self._validate_user_quotas()
        return session

    async def _validate_user_quotas(self, user_id: UUID) -> None:
        """Private helper method."""
        pass
```

### Domain Entities vs ORM Models

**Distinguish** between domain entities and database models:

```python
# Domain entity (business logic)
from app.domain.entities.session import Session

# ORM model (database)
from app.models.session import SessionModel

# GOOD - Clear distinction
session_entity = Session(id=uuid4(), ...)
session_model = SessionModel(id=session_entity.id, ...)

# BAD - Confusion
session = SessionModel(id=uuid4(), ...)  # Is this domain or database?
```

---

## Common Patterns

### 1. Repository Pattern

**All data access goes through repositories**:

```python
# app/repositories/session_repository.py
from app.repositories.base import BaseRepository
from app.models.session import SessionModel

class SessionRepository(BaseRepository[SessionModel]):
    """Repository for session data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionModel, db)

    async def get_active_sessions(self, user_id: UUID) -> List[SessionModel]:
        """Get all active sessions for a user."""
        query = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.status == "active",
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

**Usage in service**:

```python
# GOOD - Use repository
class SessionService:
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    async def get_session(self, session_id: UUID) -> Session:
        model = await self.session_repo.get_by_id(session_id)
        return self._model_to_entity(model)

# BAD - Direct database access in service
class SessionService:
    async def get_session(self, session_id: UUID) -> Session:
        result = await self.db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )  # Don't do this!
```

### 2. Dependency Injection

**Use FastAPI's dependency injection**:

```python
# app/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async with async_session_maker() as session:
        yield session

def get_session_service(
    db: AsyncSession = Depends(get_db)
) -> SessionService:
    """Session service dependency."""
    return SessionService(
        db=db,
        session_repo=SessionRepository(db),
        # ... other dependencies
    )

# app/api/v1/sessions.py
@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    service: SessionService = Depends(get_session_service),
    current_user: User = Depends(get_current_user),
):
    """Create a new session."""
    session = await service.create_session(
        user_id=current_user.id,
        mode=request.mode,
        sdk_options=request.sdk_options,
    )
    return SessionResponse.from_entity(session)
```

### 3. Strategy Pattern

**ExecutorFactory selects execution strategies**:

```python
# app/claude_sdk/execution/executor_factory.py
class ExecutorFactory:
    """Factory for creating SDK executors based on session mode."""

    @staticmethod
    def create_executor(session: Session, client: ClaudeClient) -> BaseExecutor:
        """Create appropriate executor for session mode."""
        if session.mode == SessionMode.INTERACTIVE:
            return InteractiveExecutor(client)
        elif session.mode == SessionMode.NON_INTERACTIVE:
            return NonInteractiveExecutor(client)
        else:
            raise ValueError(f"Unknown session mode: {session.mode}")
```

### 4. Factory Pattern

**Create complex objects with factories**:

```python
# Domain entity factory
class SessionFactory:
    """Factory for creating session entities."""

    @staticmethod
    def create_interactive_session(
        user_id: UUID,
        sdk_options: SDKOptions,
        name: Optional[str] = None,
    ) -> Session:
        """Create an interactive session with defaults."""
        return Session(
            id=uuid4(),
            user_id=user_id,
            mode=SessionMode.INTERACTIVE,
            status=SessionStatus.CREATED,
            sdk_options=sdk_options,
            name=name or f"Session-{datetime.utcnow().isoformat()}",
        )
```

### 5. Value Objects

**Immutable value objects with frozen dataclasses**:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SDKOptions:
    """Immutable SDK configuration options."""

    model: str = "claude-sonnet-4-5"
    max_turns: int = 10
    permission_mode: str = "default"
    timeout_seconds: int = 120

    def __post_init__(self):
        """Validate on creation."""
        if self.max_turns < 1:
            raise ValueError("max_turns must be positive")
```

---

## Async/Await Best Practices

### All I/O Operations Must Be Async

```python
# GOOD - Async I/O
async def get_session(self, session_id: UUID) -> Session:
    result = await self.db.execute(query)  # Async database call
    return result.scalar_one_or_none()

async def send_message(self, message: str) -> Response:
    response = await self.http_client.post(url, json=data)  # Async HTTP
    return response

# BAD - Blocking I/O
def get_session(self, session_id: UUID) -> Session:
    import requests
    response = requests.get(url)  # Blocking! Use httpx instead
```

### Use AsyncSession for Database

```python
# GOOD
from sqlalchemy.ext.asyncio import AsyncSession

async def create_session(self, db: AsyncSession) -> Session:
    model = SessionModel(...)
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return model

# BAD - Sync session in async context
from sqlalchemy.orm import Session

def create_session(self, db: Session) -> Session:  # Don't mix sync/async!
    pass
```

### Parallel Operations with asyncio.gather()

```python
import asyncio

# GOOD - Parallel execution
async def get_session_details(self, session_id: UUID):
    session, messages, tools = await asyncio.gather(
        self.session_repo.get_by_id(session_id),
        self.message_repo.get_by_session(session_id),
        self.tool_call_repo.get_by_session(session_id),
    )
    return session, messages, tools

# BAD - Sequential execution
async def get_session_details(self, session_id: UUID):
    session = await self.session_repo.get_by_id(session_id)
    messages = await self.message_repo.get_by_session(session_id)
    tools = await self.tool_call_repo.get_by_session(session_id)
    return session, messages, tools  # 3x slower!
```

### Never Use Blocking Calls

```python
# BAD - Blocking operations in async code
import time

async def process_with_delay():
    time.sleep(5)  # DON'T! Blocks entire event loop

# GOOD - Async sleep
import asyncio

async def process_with_delay():
    await asyncio.sleep(5)  # Non-blocking
```

---

## Error Handling Patterns

### Raise Specific Exceptions

```python
# GOOD - Specific domain exceptions
from app.domain.exceptions import SessionNotFoundError, QuotaExceededError

async def get_session(self, session_id: UUID) -> Session:
    session = await self.session_repo.get_by_id(session_id)
    if not session:
        raise SessionNotFoundError(f"Session {session_id} not found")
    return session

# BAD - Generic exceptions
async def get_session(self, session_id: UUID) -> Session:
    session = await self.session_repo.get_by_id(session_id)
    if not session:
        raise Exception("Session not found")  # Too generic!
```

### Layer-Specific Error Handling

```python
# Domain layer - Raise domain exceptions
class Session:
    def transition_to(self, new_status: SessionStatus):
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )

# Service layer - Catch and handle domain exceptions
class SessionService:
    async def activate_session(self, session_id: UUID) -> Session:
        try:
            session = await self.get_session(session_id)
            session.transition_to(SessionStatus.ACTIVE)
            await self._save(session)
            return session
        except InvalidStateTransitionError as e:
            logger.error("State transition failed", exc_info=e)
            raise SessionCannotActivateError(str(e)) from e

# API layer - Convert to HTTP exceptions
@router.post("/sessions/{session_id}/activate")
async def activate_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
):
    try:
        session = await service.activate_session(session_id)
        return SessionResponse.from_entity(session)
    except SessionCannotActivateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Always Log Errors with Context

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# GOOD - Log with context
async def create_session(self, user_id: UUID) -> Session:
    try:
        session = Session(...)
        await self.session_repo.create(session)
        return session
    except Exception as e:
        logger.error(
            "Failed to create session",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "error_type": e.__class__.__name__,
            },
            exc_info=True,  # Include stack trace
        )
        raise

# BAD - No logging or context
async def create_session(self, user_id: UUID) -> Session:
    session = Session(...)
    await self.session_repo.create(session)
    return session  # Exceptions disappear!
```

---

## Logging Best Practices

### Use Structured Logging

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# GOOD - Structured logging with context
logger.info(
    "Session created successfully",
    extra={
        "session_id": str(session.id),
        "user_id": str(user_id),
        "mode": session.mode.value,
        "duration_ms": duration,
    }
)

# BAD - String concatenation
logger.info(f"Session {session.id} created for user {user_id}")
```

### Log Levels

```python
# DEBUG - Detailed diagnostic information
logger.debug("Validating SDK options", extra={"options": sdk_options})

# INFO - General informational messages
logger.info("Session activated", extra={"session_id": str(session.id)})

# WARNING - Potentially harmful situations
logger.warning("Session quota nearing limit", extra={"user_id": str(user_id)})

# ERROR - Error events that might still allow app to continue
logger.error("Failed to connect to SDK", exc_info=True)
```

### Never Log Sensitive Data

```python
# BAD - Logging secrets
logger.info(f"API key: {api_key}")  # NEVER!
logger.debug(f"User password: {password}")  # NEVER!
logger.info(f"JWT token: {token}")  # NEVER!

# GOOD - Log safely
logger.info("API key configured", extra={"key_prefix": api_key[:8]})
logger.info("User authenticated", extra={"user_id": str(user_id)})
```

---

## Database Patterns

### Use Repositories for All Data Access

```python
# GOOD - Repository pattern
class SessionService:
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo

    async def get_session(self, session_id: UUID) -> Session:
        model = await self.session_repo.get_by_id(session_id)
        return self._model_to_entity(model)

# BAD - Direct database queries in service
class SessionService:
    async def get_session(self, session_id: UUID) -> Session:
        result = await self.db.execute(select(SessionModel)...)  # Don't!
```

### Entity-Model Conversion in Service Layer

```python
# Service layer converts between domain entities and ORM models
class SessionService:
    def _entity_to_model(self, session: Session) -> SessionModel:
        """Convert domain entity to ORM model."""
        return SessionModel(
            id=session.id,
            user_id=session.user_id,
            name=session.name,
            mode=session.mode.value,
            status=session.status.value,
            sdk_options=session.sdk_options.dict(),
            working_directory_path=session.working_directory_path,
        )

    def _model_to_entity(self, model: SessionModel) -> Session:
        """Convert ORM model to domain entity."""
        return Session(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            mode=SessionMode(model.mode),
            status=SessionStatus(model.status),
            sdk_options=SDKOptions(**model.sdk_options),
        )
```

### Transaction Management

```python
# Service layer manages transactions
class SessionService:
    async def create_session(self, user_id: UUID) -> Session:
        # Create entity
        session = Session(id=uuid4(), user_id=user_id, ...)

        # Convert and add to database
        model = self._entity_to_model(session)
        self.db.add(model)
        await self.db.flush()  # Get ID immediately

        # Create related records
        await self.message_repo.create(session_id=session.id, ...)

        # Commit at end (or let caller commit)
        # await self.db.commit()  # Usually done by API layer

        return session
```

### Use db.flush() vs db.commit()

```python
# flush() - Persist changes but keep transaction open
model = SessionModel(...)
self.db.add(model)
await self.db.flush()  # Get auto-generated ID
await self.db.refresh(model)  # Refresh with DB values

# commit() - Persist and close transaction
await self.db.commit()  # Usually done at API layer or decorator
```

---

## Configuration Management

### Use Settings Class

```python
# GOOD - Access via settings
from app.core.config import settings

max_sessions = settings.max_concurrent_sessions
api_key = settings.anthropic_api_key
db_url = settings.database_url

# BAD - Hardcoded values
max_sessions = 5  # Don't hardcode!
api_key = "sk-ant-api03-..."  # Never hardcode secrets!
```

### Environment Variables via .env

```python
# Configuration loaded from .env automatically
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    max_concurrent_sessions: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Type Safety

### Type Hints Everywhere

```python
# GOOD - Complete type hints
from typing import Optional, List, Dict, Any
from uuid import UUID

async def create_session(
    user_id: UUID,
    mode: SessionMode,
    options: Dict[str, Any],
) -> Session:
    pass

# BAD - No type hints
async def create_session(user_id, mode, options):
    pass
```

### Use Pydantic for Validation

```python
from pydantic import BaseModel, Field, validator

# API request model
class CreateSessionRequest(BaseModel):
    """Request model for creating a session."""

    name: Optional[str] = None
    mode: SessionMode
    sdk_options: SDKOptions

    @validator('name')
    def validate_name(cls, v):
        if v and len(v) > 255:
            raise ValueError('Name too long')
        return v
```

### Enums for Constants

```python
from enum import Enum

# GOOD - Type-safe enums
class SessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"

status = SessionStatus.ACTIVE  # Type-safe

# BAD - String constants
STATUS_CREATED = "created"  # Not type-safe
STATUS_ACTIVE = "active"
```

---

## Testing Patterns

See [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) for comprehensive testing patterns.

**Quick Example**:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_create_session_success(
    session_service,
    test_user,
    mock_storage_manager,
):
    # Arrange
    mock_storage_manager.create_working_directory.return_value = "/tmp/test"

    # Act
    session = await session_service.create_session(
        user_id=test_user.id,
        mode=SessionMode.INTERACTIVE,
        sdk_options={"model": "claude-sonnet-4-5"},
    )

    # Assert
    assert session is not None
    assert session.user_id == test_user.id
    assert session.status == SessionStatus.CREATED
```

---

## Code Examples - Good vs Bad

### Example 1: Service Layer Method

**GOOD**:
```python
# app/services/session_service.py
class SessionService:
    """Business logic for session management."""

    async def create_session(
        self,
        user_id: UUID,
        mode: SessionMode,
        sdk_options: dict,
    ) -> Session:
        """Create and initialize a new session.

        Args:
            user_id: User identifier
            mode: Session mode
            sdk_options: SDK configuration

        Returns:
            Created session entity

        Raises:
            QuotaExceededError: User quota exceeded
        """
        # Validate quotas
        await self._validate_user_quotas(user_id)

        # Create domain entity
        session = Session(
            id=uuid4(),
            user_id=user_id,
            mode=mode,
            sdk_options=sdk_options,
        )

        # Create working directory
        workdir = await self.storage_manager.create_working_directory(session.id)
        session.working_directory_path = str(workdir)

        # Persist to database
        model = self._entity_to_model(session)
        self.db.add(model)
        await self.db.flush()

        # Audit log
        await self.audit_service.log_session_created(session.id, user_id)

        logger.info(
            "Session created",
            extra={"session_id": str(session.id), "user_id": str(user_id)}
        )

        return session
```

**BAD**:
```python
# Multiple issues in this code
def create_session(user_id, mode, sdk_options):  # No async, no types
    s = Session(uuid4(), user_id, mode, sdk_options)  # Bad var name
    db.execute(f"INSERT INTO sessions VALUES ({s.id}, ...)")  # SQL injection!
    return s  # No error handling, no logging
```

### Example 2: Repository Method

**GOOD**:
```python
# app/repositories/session_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class SessionRepository(BaseRepository[SessionModel]):
    """Repository for session data access."""

    async def get_active_sessions(self, user_id: UUID) -> List[SessionModel]:
        """Get all active sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active session models
        """
        query = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.status == SessionStatus.ACTIVE.value,
            SessionModel.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

**BAD**:
```python
def get_active_sessions(user_id):  # No types, not async
    # Direct SQL in repository (should use SQLAlchemy)
    sessions = db.execute(
        f"SELECT * FROM sessions WHERE user_id = {user_id} AND status = 'active'"
    ).fetchall()  # SQL injection vulnerability!
    return sessions
```

---

## Related Files

**Service Layer**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/services/session_service.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/services/sdk_session_service.py`

**Repository Layer**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/repositories/base.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/repositories/session_repository.py`

**Domain Layer**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/domain/entities/session.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/domain/exceptions.py`

**Configuration**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/core/config.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/pyproject.toml`

---

## Keywords

coding-standards, pep8, black, ruff, mypy, type-hints, docstrings, naming-conventions, layered-architecture, repository-pattern, dependency-injection, strategy-pattern, factory-pattern, value-objects, async-await, error-handling, logging, structured-logging, database-patterns, sqlalchemy, pydantic, validation, enums, type-safety, code-organization, best-practices, clean-code, solid-principles, separation-of-concerns, domain-driven-design

---

**Related Documentation**:
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Development setup
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Testing patterns
- [ERROR_HANDLING.md](./ERROR_HANDLING.md) - Exception handling
- [LAYERED_ARCHITECTURE.md](../architecture/LAYERED_ARCHITECTURE.md) - Architecture overview
