# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AI-Agent-API-Service is an enterprise-grade FastAPI wrapper around the Claude Code Agent SDK. It transforms the SDK into a stateful, persistent, multi-tenant service with comprehensive session management, business logic, MCP tool integration, and extensibility features.

Key capabilities:
- **Session Management** - Persistent sessions with full execution history stored in PostgreSQL
- **Claude SDK Integration** - Wrapper around the Claude Code CLI for agent execution
- **MCP Tool Integration** - Configuration and execution of MCP servers within sessions
- **Task Automation** - Template-based tasks with Celery scheduling
- **Reporting** - Multi-format report generation (JSON, Markdown, HTML, PDF)
- **WebSocket Support** - Real-time streaming APIs for agent output
- **Security & Compliance** - JWT authentication, RBAC, comprehensive audit logging

## Architecture Overview

### Layered Architecture

The application follows a **clean architecture** with clear separation of concerns:

```
API Layer (FastAPI routes)
        ↓
Service Layer (business logic)
        ↓
Repository Layer (data access)
        ↓
Database Layer (PostgreSQL/SQLAlchemy ORM)
```

Additionally:
- **Domain Layer** - Entities (Session, Task, User) and Value Objects (Message, ToolCall)
- **Core Layer** - Shared utilities, configuration, logging, monitoring
- **MCP Layer** - Claude SDK integration and MCP server management

### Database Schema

**Key Models (in `app/models/`)**:
- `User` - System users with permissions
- `Session` - Claude agent sessions (long-lived conversations with working directories)
- `Message` - Conversation history (user queries and AI responses)
- `ToolCall` - Tracking of tool invocations with results
- `Task` - Scheduled/automated tasks
- `TaskExecution` - Execution history of tasks
- `Report` - Generated reports (JSON/Markdown/HTML/PDF)
- `MCPServer` - External MCP server configurations
- `AuditLog` - Security audit trail
- `WorkingDirectory` - Session file storage metadata

**Database**: PostgreSQL 15+ with asyncpg for async operations. Migrations via Alembic.

### Core Service Components

**Session Management** (`app/services/session_service.py`):
- Create/resume/archive sessions
- Permission checks
- Message persistence
- Working directory management
- Quota enforcement

**SDK Session Service** (`app/services/sdk_session_service.py`):
- Bridges AI-Agent-API with Claude SDK
- Manages SDK configuration and MCP servers
- Handles execution lifecycle
- Streaming output to WebSockets

**Task Service** (`app/services/task_service.py`):
- CRUD for scheduled tasks
- Execution via Celery workers
- Template-based task creation
- Retry logic and error handling

**Report Service** (`app/services/report_service.py`):
- Multi-format generation (JSON, Markdown, HTML, PDF)
- Template engine (Jinja2)
- Report scheduling and archival

**Audit Service** (`app/services/audit_service.py`):
- Compliance logging
- User action tracking
- Security event recording

### API Structure

**Routers** (in `app/api/v1/`):
- `sessions.py` - Session CRUD and message APIs
- `tasks.py` - Task management and execution
- `reports.py` - Report generation and retrieval
- `auth.py` - Authentication (JWT tokens)
- `admin.py` - Admin operations and system health
- `mcp_servers.py` - MCP server configuration
- `websocket.py` - WebSocket connections for real-time streaming

**Middleware** (in `app/api/middleware.py`):
- `RequestIDMiddleware` - Adds X-Request-ID for tracing
- `LoggingMiddleware` - Structured request/response logging
- `RateLimitMiddleware` - Enforces rate limits
- `CORSMiddleware` - Handles cross-origin requests (configured in main.py)

### Repository Pattern

All data access is abstracted via repositories in `app/repositories/`:
- `SessionRepository` - Session queries and mutations
- `MessageRepository` - Message persistence
- `TaskRepository` - Task CRUD
- `UserRepository` - User management
- `ReportRepository` - Report storage
- etc.

**Base class** (`base.py`) provides:
- Common CRUD operations
- Async/await patterns
- Query filtering and pagination
- Error handling

## Common Development Commands

### Setup & Installation

```bash
# Install dependencies with Poetry
make install

# Complete development setup (install + migrate + directories)
make setup

# Install with dev tools (linters, formatters, type checker)
make dev
```

### Running the Application

```bash
# Run FastAPI server (auto-reload enabled)
make run

# Run Celery worker (for background tasks/scheduling)
make run-worker

# Run Celery beat scheduler (for scheduled tasks)
make run-beat

# Start full stack with Docker Compose (includes Postgres, Redis, Nginx)
make docker-up

# Stop Docker Compose services
make docker-down
```

### Database Operations

```bash
# Run all pending migrations
make migrate

# Create a new migration
make migrate-create

# Downgrade one migration
make migrate-downgrade

# Reset database (WARNING: destroys all data)
make db-reset
```

### Testing

```bash
# Run full test suite (unit + integration + e2e with coverage)
make test

# Run specific test category
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests only

# Run specific test suites
make test-sessions     # Session functionality tests
make test-permissions  # Permission system tests
make test-tasks        # Task management tests
make test-api          # API endpoint tests

# Run tests with coverage analysis
make test-cov

# Watch mode (re-run on changes)
make test-watch

# Check test dependencies are installed
make deps-check
```

### Code Quality

```bash
# Run linters (ruff)
make lint

# Format code (Black, ruff formatter)
make format

# Run type checking (mypy)
make type-check

# Run all quality checks
make quality

# CI pipeline (deps-check + quality + test)
make ci
```

### Cleanup

```bash
# Remove Python cache, coverage files, etc.
make clean
```

## Running Tests Locally

### Test Structure

Tests are organized by type in `tests/`:
- `tests/unit/` - Fast, isolated unit tests (no external dependencies)
- `tests/integration/` - Tests with database, Redis, real repositories
- `tests/e2e/` - Complete end-to-end workflows

### Running Single Tests

```bash
# Run specific test file
poetry run pytest tests/unit/test_session_service.py -v

# Run specific test function
poetry run pytest tests/unit/test_session_service.py::test_create_session -v

# Run with output capture disabled (see print statements)
poetry run pytest tests/unit/test_session_service.py -v -s

# Run with short traceback format
poetry run pytest tests/unit/test_session_service.py -v --tb=short
```

### Test Configuration

- `pytest.ini` - pytest configuration (asyncio_mode=auto)
- `tests/conftest.py` - Fixtures and test setup
  - Database fixtures (async SQLAlchemy sessions)
  - FastAPI test client
  - Mock factories (factory-boy)
  - Mocked services and external dependencies

### Coverage Requirements

- Minimum 80% coverage enforced in CI
- HTML coverage report generated: `htmlcov/index.html`
- XML report for CI tools: `coverage.xml`

## Key File Locations by Task

### Adding a New API Endpoint

1. Create route in `app/api/v1/{feature}.py`
2. Define request/response schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Create repository methods if needed in `app/repositories/`
5. Add tests in `tests/integration/` or `tests/unit/`

**Example**: See `app/api/v1/sessions.py` for comprehensive examples with pagination, filtering, and error handling.

### Adding a New Service

1. Create service class in `app/services/{name}_service.py`
2. Implement business logic with dependency injection
3. Register in `app/api/dependencies.py` as a FastAPI Depends()
4. Add comprehensive tests in `tests/unit/test_{name}_service.py`

**Example**: `SessionService`, `TaskService`, `ReportService` show the pattern.

### Working with Sessions and the Claude SDK

- **Core**: `app/services/sdk_session_service.py` - manages Claude SDK integration
- **Models**: `app/models/session.py`, `app/models/message.py`, `app/models/tool_call.py`
- **Domain**: `app/domain/entities/session.py` - Session entity and SessionStatus enum
- **Repository**: `app/repositories/session_repository.py` - data access
- **API**: `app/api/v1/sessions.py` - HTTP endpoints

Session workflow:
1. User creates session via POST `/api/v1/sessions`
2. SDK session initialized with MCP server configuration
3. User sends query via POST `/api/v1/sessions/{id}/query`
4. Message stored, SDK invoked, tool calls executed
5. Real-time streaming via WebSocket `/ws/sessions/{id}`

### Working with Tasks and Scheduling

- **Service**: `app/services/task_service.py` - CRUD and execution logic
- **Models**: `app/models/task.py`, `app/models/task_execution.py`
- **API**: `app/api/v1/tasks.py` - HTTP endpoints
- **Celery**: `app/celery_app.py` - background job configuration
- **Executor**: `app/tasks/task_executor.py` - actual execution logic

### Working with Reports

- **Service**: `app/services/report_service.py` - generation and retrieval
- **Models**: `app/models/report.py`
- **API**: `app/api/v1/reports.py` - HTTP endpoints
- **Templates**: `data/report_templates/` - Jinja2 templates for each format
- **Formats**: JSON, Markdown, HTML, PDF (via WeasyPrint)

### Working with MCP Integration

- **Service**: `app/services/sdk_session_service.py` - MCP configuration
- **Models**: `app/models/mcp_server.py`
- **API**: `app/api/v1/mcp_servers.py` - MCP server CRUD
- **Builder**: `app/mcp/config_builder.py` - MCP configuration construction
- **SDK**: `app/claude_sdk/` - Claude SDK wrapper and error handling

### Working with Authentication & Permissions

- **Auth routes**: `app/api/v1/auth.py` - JWT token generation
- **Middleware**: `app/api/dependencies.py` - current_user dependency
- **Service**: Session service checks user permissions for access
- **Models**: `app/models/user.py` - User and Role models
- **Repository**: `app/repositories/user_repository.py` - User queries

### Database Migrations

```bash
# After modifying ORM models, auto-generate migration:
poetry run alembic revision --autogenerate -m "Description of change"

# Review generated migration in alembic/versions/
# Apply to database:
poetry run alembic upgrade head
```

**Important**: Alembic auto-generation works by comparing models to schema. Always review generated migrations for data loss.

## Configuration Management

### Environment Variables

Configuration via `.env` file (see `.env.example` for all options):

**Database**:
- `DATABASE_URL` - PostgreSQL connection string (asyncpg driver)
- `DATABASE_POOL_SIZE` - Connection pool size (default: 20)
- `DATABASE_MAX_OVERFLOW` - Max overflow connections (default: 10)

**Redis & Celery**:
- `REDIS_URL` - Redis connection for caching
- `CELERY_BROKER_URL` - Celery message broker (usually Redis db 1)
- `CELERY_RESULT_BACKEND` - Task result storage (usually Redis db 2)

**Claude & SDK**:
- `ANTHROPIC_API_KEY` - Anthropic API key (required)
- `CLAUDE_CLI_PATH` - Path to claude CLI executable (default: "claude")

**Security**:
- `SECRET_KEY` - JWT signing key (min 32 chars, change in production)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token lifetime (default: 60)

**Storage**:
- `STORAGE_BASE_PATH` - Base directory for session working directories
- `MAX_STORAGE_MB` - Total storage quota (default: 10240)
- `MAX_WORKING_DIR_SIZE_MB` - Per-session working dir limit (default: 1024)

**Session Limits**:
- `MAX_CONCURRENT_SESSIONS` - Per-user concurrent sessions (default: 5)
- `SESSION_TIMEOUT_HOURS` - Session inactivity timeout (default: 24)
- `SESSION_ARCHIVE_DAYS` - Days before auto-archival (default: 180)

**Rate Limiting**:
- `RATE_LIMIT_ENABLED` - Enable rate limiting (default: true)
- `RATE_LIMIT_PER_MINUTE` - Requests per minute (default: 60)
- `RATE_LIMIT_PER_HOUR` - Requests per hour (default: 1000)

Configuration loaded via Pydantic Settings (`app/core/config.py`), supports environment variable overrides with `_` to `__` conversion.

## Code Quality Standards

### Python Version & Dependencies

- **Python**: 3.12+ (required by FastAPI, SQLAlchemy async)
- **Package manager**: Poetry for dependency management
- **Async/await**: All I/O operations (database, Redis, HTTP) must be async

### Linting & Formatting

- **Black**: Code formatter (line length: 100)
- **Ruff**: Linter with import sorting (line length: 100)
- **mypy**: Type checker (not strict, but `check_untyped_defs: true`)

All enforced via `make quality`. Fix issues with `make format`.

### Type Hints

- Add type hints to function signatures and return types
- Use `Optional[T]`, `List[T]`, `Dict[K, V]` from typing
- Use `AsyncSession` from SQLAlchemy for database operations
- mypy will catch most issues during `make type-check`

### Error Handling

- Use domain exceptions from `app/domain/exceptions.py`:
  - `SessionNotFoundError` - Session doesn't exist
  - `PermissionDeniedError` - User lacks permission
  - `QuotaExceededError` - Resource limit exceeded
  - etc.
- Never use bare `except Exception` - be specific
- Database exceptions handled in `app/api/exception_handlers.py` and converted to HTTP responses

### Logging

- Use `from app.core.logging import get_logger` to get logger instance
- Structured logging with context: `logger.info("msg", extra={"session_id": id})`
- Levels: DEBUG (detailed), INFO (general), WARNING (issues), ERROR (failures)
- Never log sensitive data: passwords, tokens, API keys, PII

### Import Patterns

Standard imports from `app.*` modules (not `src.*`):
```python
from app.services.session_service import SessionService
from app.domain.entities.session import Session
from app.core.logging import get_logger
```

## Development Workflow

### Creating a New Feature

1. **Define domain entities** in `app/domain/entities/` if needed
2. **Create ORM models** in `app/models/`
3. **Create/update repository** in `app/repositories/`
4. **Implement service logic** in `app/services/`
5. **Create API endpoint** in `app/api/v1/`
6. **Write tests** - unit tests first, then integration tests
7. **Update migrations** via `make migrate-create`
8. **Run quality checks**: `make quality`

### Testing Best Practices

**Arrange-Act-Assert pattern**:
```python
async def test_create_session():
    # Arrange
    user = await user_factory.create()

    # Act
    session = await session_service.create_session(user.id, SessionMode.INTERACTIVE, {})

    # Assert
    assert session.user_id == user.id
    assert session.status == SessionStatus.ACTIVE
```

**Mocking external dependencies**:
- Mock Celery tasks with `unittest.mock.patch`
- Mock SDK calls with fixtures
- Use `AsyncMock` for async functions
- Mock Redis operations for integration tests

**Test categories**:
- **Unit**: Fast, single service/function, all dependencies mocked
- **Integration**: Uses real database, Redis, repositories
- **E2E**: Full workflow, multiple services interacting

### Modifying Shared Code

When changing:
- **Domain entities** - Update API schemas and tests
- **Database models** - Create migration, test migration
- **Service signatures** - Update callers in API routes
- **Exception types** - Update exception handlers

## Important Architectural Decisions

### Async-First Design

All I/O operations are async:
- SQLAlchemy with asyncio support (`async_engine`, `AsyncSession`)
- asyncpg for database driver
- httpx for async HTTP calls
- Redis async client
- FastAPI handles async endpoints automatically

Never use blocking calls (requests, time.sleep, os.system) in async code.

### Dependency Injection

Services receive dependencies via constructor, not global state:
```python
async def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(db, repositories..., services...)
```

Benefits:
- Easy to mock for testing
- Clear service dependencies
- Thread-safe (each request has its own dependencies)

### Repository Pattern Motivation

Repositories abstract data access to:
- Make switching databases easier (PostgreSQL → MongoDB)
- Simplify testing (mock repositories)
- Keep business logic in services separate from data access
- Centralize query logic

### Session Isolation

Each session is isolated:
- Has own working directory on disk
- Separate tool call history
- Independent message thread
- Can't access other user's sessions (permission checks)

This enables multi-user, multi-session concurrent operation.

### MCP Server Lifecycle

MCP servers configured per-session:
- User specifies MCP servers when creating session
- SDK loads server configurations at session start
- Servers run in subprocess managed by Claude CLI
- Tool calls routed to appropriate server
- Servers stopped when session archived

## Known Limitations & Future Improvements

### Known Limitations

1. **WebSocket connections** - Real-time streaming to browser assumes single consumer. Multiple WebSocket clients on same session may receive duplicate messages.
2. **Session archive** - Archived sessions can't be resumed (by design). To enable resume-after-archive requires significant data model changes.
3. **Report generation** - PDF generation (via WeasyPrint) can be slow with large documents (>10MB). Async execution planned.
4. **Rate limiting** - In-memory rate limiter doesn't work across multiple API instances. Use Redis-backed limiter for production scaling.

### Future Improvements

- Distributed rate limiting via Redis
- Async PDF generation with background jobs
- Session cloning (duplicate with history)
- Webhook delivery for session events
- Streaming logs to external services (ELK, DataDog)
- Plugin architecture for custom actions

## Troubleshooting

### Service Not Starting

```bash
# Check environment configuration
grep -E "DATABASE_URL|REDIS_URL|ANTHROPIC_API_KEY" .env

# Check dependencies installed
poetry install

# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connection
redis-cli PING
```

### Tests Failing

```bash
# Check dependencies
make deps-check

# Run with verbose output
poetry run pytest tests/ -vvv -s

# Run single test in isolation
poetry run pytest tests/unit/test_x.py::test_y -vv

# Clear cache
make clean && poetry run pytest tests/
```

### Database Migrations Issue

```bash
# Check current migration status
poetry run alembic current

# Check available migrations
poetry run alembic history

# Rollback to specific revision
poetry run alembic downgrade <revision>
```

## Additional Resources

- **README.md** - Quick start and feature overview
- **Makefile** - All available development commands
- **`.env.example`** - Complete configuration reference
- **Docker Compose** - Local development with all services
- **OpenAPI Docs** - Auto-generated at `/docs` when running service
- **Test fixtures** - `tests/conftest.py` for test utilities and factories
