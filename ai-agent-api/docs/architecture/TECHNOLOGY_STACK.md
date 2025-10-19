# Technology Stack

## Purpose

This document details all technologies, frameworks, libraries, and tools used in the AI-Agent-API service, including versions, purposes, and configuration details.

## Overview

The AI-Agent-API is built with modern Python async technologies optimized for high-performance AI agent management.

---

## Core Technologies

### Python 3.12+

**Purpose**: Primary programming language

**Why Python 3.12**:
- Native async/await support
- Performance improvements (up to 25% faster than 3.11)
- Better error messages
- Type hinting improvements
- Pattern matching (structural pattern matching)

**Configuration**: [pyproject.toml:10](../../pyproject.toml:10)
```toml
[tool.poetry.dependencies]
python = "^3.12"
```

---

## Web Framework

### FastAPI 0.110+

**Purpose**: Modern async web framework

**File**: [main.py:70-103](../../main.py:70-103)

**Why FastAPI**:
- Native async/await support
- Automatic API documentation (OpenAPI/Swagger)
- Pydantic integration for validation
- High performance (comparable to NodeJS, Go)
- Type hints for IDE support
- Dependency injection system

**Key Features Used**:
- **Lifespan Events** ([main.py:34-68](../../main.py:34-68)): Startup/shutdown hooks
- **Dependency Injection** ([dependencies.py](../../app/api/dependencies.py)): Auth, DB sessions
- **Middleware** ([main.py:91-94](../../main.py:91-94)): Request ID, logging, rate limiting
- **Exception Handlers** ([main.py:96-100](../../main.py:96-100)): Custom error handling
- **WebSocket Support** ([websocket/](../../app/websocket/)): Real-time streaming

**Configuration**:
```python
app = FastAPI(
    title="AI-Agent-API-Service",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

**Endpoints**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

---

## Database

### PostgreSQL 15+

**Purpose**: Primary relational database

**Connection**: [config.py:32-34](../../app/core/config.py:32-34)
```python
database_url: str  # postgresql+asyncpg://user:pass@host:5432/dbname
database_pool_size: int = 20
database_max_overflow: int = 10
```

**Why PostgreSQL**:
- ACID compliance
- JSONB support (for sdk_options, metadata)
- Full-text search
- Mature ecosystem
- Excellent async support (asyncpg)

**Features Used**:
- **JSONB columns**: sdk_options, message content, tool_call input/output
- **UUID primary keys**: All tables use UUID for distributed systems
- **Foreign keys**: Referential integrity
- **Indexes**: Performance optimization
- **Triggers**: Audit logging (if implemented)

### SQLAlchemy 2.0 (Async)

**Purpose**: ORM and database toolkit

**File**: [models/](../../app/models/), [repositories/base.py](../../app/repositories/base.py:11-86)

**Why SQLAlchemy 2.0**:
- Full async support (`AsyncSession`)
- Type-safe queries
- Relationship mapping
- Migration support via Alembic
- Connection pooling
- Query builder

**Key Features**:
- **Async Session** ([database/session.py](../../app/database/)):
  ```python
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

  engine = create_async_engine(settings.database_url, pool_size=20)
  async_session = sessionmaker(engine, class_=AsyncSession)
  ```

- **Declarative Base** ([models/](../../app/models/)):
  ```python
  from sqlalchemy.orm import DeclarativeBase

  class Base(DeclarativeBase):
      pass

  class SessionModel(Base):
      __tablename__ = "sessions"
      # ...
  ```

**Driver**: [asyncpg](https://github.com/MagicStack/asyncpg) - Fast PostgreSQL driver

---

### Alembic 1.13+

**Purpose**: Database migrations

**File**: [alembic/](../../alembic/), [alembic.ini](../../alembic.ini)

**Migration Files**:
- [20251018_0230_initial_database_schema.py](../../alembic/versions/20251018_0230_972fc63ffb69_initial_database_schema.py)
- [20251018_0355_add_session_templates.py](../../alembic/versions/20251018_0355_567cc0f251e5_add_session_templates_table.py)
- [20251019_0058_phase1_claude_sdk_v2.py](../../alembic/versions/20251019_0058_c0b7d0e366e7_phase1_claude_sdk_v2_foundation.py)

**Commands**:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Caching & Message Broker

### Redis 7+

**Purpose**: Caching, session storage, rate limiting

**Configuration**: [config.py:37](../../app/core/config.py:37)
```python
redis_url: str  # redis://localhost:6379/0
```

**Why Redis**:
- In-memory speed
- Pub/Sub for real-time features
- Built-in data structures (lists, sets, sorted sets)
- TTL support
- Atomic operations

**Use Cases**:
- API rate limiting (token bucket)
- Session caching
- Real-time WebSocket pub/sub
- Celery broker

**Driver**: [redis-py](https://redis-py.readthedocs.io/) with hiredis for performance

---

## Background Jobs

### Celery 5.3+

**Purpose**: Asynchronous task queue

**Configuration**: [config.py:40-41](../../app/core/config.py:40-41)
```python
celery_broker_url: str     # redis://localhost:6379/1
celery_result_backend: str # redis://localhost:6379/2
```

**Why Celery**:
- Distributed task execution
- Retry mechanisms
- Scheduled tasks (cron-like)
- Task prioritization
- Result tracking

**Tasks**:
- Background session execution
- Scheduled task runs
- Report generation
- Session archival
- Cleanup jobs

**File**: [tasks/](../../app/tasks/)

---

## Claude Integration

### Claude Code Agent SDK 0.1.4+

**Purpose**: Official Claude Code agent interface

**File**: [claude_sdk/](../../app/claude_sdk/)

**Why Official SDK**:
- Direct Anthropic support
- Tool execution
- Permission system
- Message streaming
- Context management

**Integration Points**:
- **Client Manager** ([client_manager.py](../../app/claude_sdk/client_manager.py)): SDK lifecycle
- **Execution Strategies** ([execution/](../../app/claude_sdk/execution/)): Interactive/Background
- **Permission Service** ([permission_service.py](../../app/claude_sdk/permission_service.py)): Access control
- **Hook System** ([hooks/](../../app/claude_sdk/hooks/)): Lifecycle events

**SDK Communication**:
- Spawns `claude-code` CLI subprocess
- JSON-RPC communication
- Streaming responses
- Tool execution callbacks

### Anthropic API

**Configuration**: [config.py:50](../../app/core/config.py:50)
```python
anthropic_api_key: str
```

**Models Used**:
- `claude-sonnet-4-5` (default)
- `claude-opus-4` (high-complexity tasks)

---

## Validation & Serialization

### Pydantic 2.6+

**Purpose**: Data validation and settings management

**Files**: [schemas/](../../app/schemas/), [config.py](../../app/core/config.py:8-80)

**Why Pydantic**:
- Fast (Rust core)
- Type-safe validation
- JSON schema generation
- Settings management
- IDE auto-completion

**Use Cases**:
- **Request/Response DTOs** ([schemas/session.py](../../app/schemas/session.py)):
  ```python
  class SessionCreateRequest(BaseModel):
      name: Optional[str] = None
      mode: SessionMode
      sdk_options: dict
  ```

- **Application Settings** ([config.py](../../app/core/config.py:8-80)):
  ```python
  class Settings(BaseSettings):
      database_url: str
      redis_url: str
      anthropic_api_key: str
  ```

- **Environment Variables**: Automatic .env parsing

---

## Authentication & Security

### JWT (JSON Web Tokens)

**Library**: python-jose 3.3+ with cryptography

**File**: [auth.py](../../app/api/v1/auth.py), [dependencies.py:21-78](../../app/api/dependencies.py:21-78)

**Algorithm**: HS256 (HMAC with SHA-256)

**Token Structure**:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "user",
  "exp": 1234567890
}
```

**Configuration**: [config.py:44-47](../../app/core/config.py:44-47)
```python
secret_key: str
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 60
jwt_refresh_token_expire_days: int = 7
```

### Password Hashing

**Library**: passlib 1.7+ with bcrypt

**Usage**:
```python
from passlib.hash import bcrypt

# Hash password
password_hash = bcrypt.hash("secret")

# Verify password
is_valid = bcrypt.verify("secret", password_hash)
```

---

## Logging & Monitoring

### Structlog 24.1+

**Purpose**: Structured logging

**File**: [core/logging.py](../../app/core/logging.py)

**Why Structlog**:
- Structured (JSON) logs
- Context binding
- Middleware integration
- Performance

**Configuration**:
```python
logger = get_logger(__name__)

logger.info(
    "Session created",
    session_id=session.id,
    user_id=user.id,
    mode=session.mode,
)
```

**Output** (JSON format):
```json
{
  "event": "Session created",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "789e4567-e89b-12d3-a456-426614174001",
  "mode": "interactive",
  "timestamp": "2025-10-19T12:34:56.789Z",
  "level": "info",
  "logger": "app.services.session_service"
}
```

### Prometheus Metrics

**Library**: prometheus-client 0.19+

**File**: [monitoring/](../../app/monitoring/)

**Metrics**:
- Request count/latency
- Session count by status
- Tool call count
- API token usage
- Error rates

**Endpoint**: `GET /metrics`

### Sentry 1.40+

**Purpose**: Error tracking and performance monitoring

**Configuration**: [config.py](../../app/core/config.py)
```python
sentry_dsn: Optional[str] = None
```

**Features**:
- Exception tracking
- Performance monitoring
- Release tracking
- Breadcrumbs

---

## Development Tools

### Testing

**Framework**: pytest 7.4+ with pytest-asyncio 0.23+

**File**: [tests/](../../tests/)

**Plugins**:
- `pytest-asyncio`: Async test support
- `pytest-cov`: Code coverage
- `factory-boy`: Test data factories
- `faker`: Fake data generation

**Commands**:
```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Code Quality

**Black 24.1+**: Code formatter
```bash
black app/ tests/
```

**Ruff 0.1+**: Fast linter (replaces flake8, isort, pylint)
```bash
ruff check app/ tests/
```

**MyPy 1.8+**: Static type checker
```bash
mypy app/
```

**Pre-commit 3.6+**: Git hooks
```bash
pre-commit install
pre-commit run --all-files
```

---

## Utilities

### Template Rendering

**Library**: Jinja2 3.1+

**Use Cases**:
- Task prompt templates ([task.py:50-54](../../app/domain/entities/task.py:50-54))
- Report templates
- Email templates (if implemented)

### Cron Scheduling

**Library**: croniter 2.0+

**Usage**: Validate cron expressions ([task.py:65-67](../../app/domain/entities/task.py:65-67))
```python
from croniter import croniter

if not croniter.is_valid("0 0 * * *"):
    raise ValidationError("Invalid cron expression")
```

### PDF Generation

**Library**: WeasyPrint 60.2+

**Usage**: Generate PDF reports from HTML
```python
from weasyprint import HTML

HTML(string=html_content).write_pdf("report.pdf")
```

### HTTP Client

**Library**: httpx 0.26+

**Why httpx**:
- Async support
- HTTP/2 support
- Connection pooling
- Timeout handling

**Usage**: External API calls, webhooks

---

## Infrastructure

### Docker

**File**: `docker-compose.yml`

**Services**:
- `app`: FastAPI application
- `postgres`: PostgreSQL database
- `redis`: Redis cache
- `celery_worker`: Background job worker
- `celery_beat`: Scheduled task runner

**Commands**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Restart service
docker-compose restart app
```

### Uvicorn 0.27+

**Purpose**: ASGI server

**Configuration**: [main.py:131-139](../../main.py:131-139)
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,  # Development only
)
```

**Production**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Kubernetes Integration

### Kubernetes Python Client 29.0+

**Purpose**: MCP tool integration

**File**: [mcp/sdk_tools.py](../../app/mcp/sdk_tools.py)

**Features**:
- Pod management
- Deployment queries
- Log retrieval
- Resource monitoring

---

## Configuration Management

### Python-dotenv 1.0+

**Purpose**: Load environment variables from .env file

**File**: `.env.example`

**Usage**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

---

## Version Matrix

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Language runtime |
| FastAPI | 0.110+ | Web framework |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Cache/Broker |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | 1.13+ | Migrations |
| Celery | 5.3+ | Task queue |
| Pydantic | 2.6+ | Validation |
| pytest | 7.4+ | Testing |
| claude-agent-sdk | 0.1.4+ | AI agent |
| structlog | 24.1+ | Logging |
| prometheus-client | 0.19+ | Metrics |
| uvicorn | 0.27+ | ASGI server |

---

## Performance Characteristics

### Async I/O

**All I/O operations are async**:
- Database queries (`AsyncSession`)
- Redis operations (`aioredis`)
- HTTP requests (`httpx`)
- File I/O (`aiofiles`, not yet used)

**Benefits**:
- Handle 1000s of concurrent requests
- Non-blocking I/O
- Efficient resource usage

### Connection Pooling

**PostgreSQL**: 20 connections, 10 overflow ([config.py:33-34](../../app/core/config.py:33-34))
**Redis**: Connection pooling via redis-py
**HTTP**: Connection pooling via httpx

---

## Security Features

1. **JWT Authentication**: Stateless auth
2. **Password Hashing**: bcrypt with salt
3. **CORS**: Configurable origins
4. **Rate Limiting**: Redis-based token bucket
5. **Input Validation**: Pydantic schemas
6. **SQL Injection Prevention**: SQLAlchemy parameterized queries
7. **Secret Management**: Environment variables

---

## Development Workflow

### Local Development

```bash
# Install dependencies
poetry install

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload

# Run tests
pytest tests/

# Format code
black app/ tests/

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

### Production Build

```bash
# Build Docker image
docker build -t ai-agent-api:1.0.0 .

# Run with Docker Compose
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery_worker=4
```

---

## Related Documentation

- **Architecture Overview**: [OVERVIEW.md](OVERVIEW.md)
- **Configuration**: [../components/core/CONFIGURATION.md](../components/core/CONFIGURATION.md)
- **Database Schema**: [../data-layer/DATABASE_SCHEMA.md](../data-layer/DATABASE_SCHEMA.md)
- **Setup Guide**: [../development/SETUP_GUIDE.md](../development/SETUP_GUIDE.md)

## Keywords

`technology-stack`, `python`, `fastapi`, `postgresql`, `redis`, `celery`, `sqlalchemy`, `alembic`, `pydantic`, `asyncio`, `async`, `claude-sdk`, `uvicorn`, `docker`, `jwt`, `authentication`, `logging`, `monitoring`, `prometheus`, `sentry`, `structlog`, `testing`, `pytest`, `dependencies`, `libraries`, `frameworks`
