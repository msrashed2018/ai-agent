# AI-Agent-API Architecture Overview

## Purpose

The AI-Agent-API-Service is an enterprise-grade FastAPI wrapper around the official Claude Code Agent SDK that transforms the SDK into a stateful, persistent, multi-tenant service. It provides session management, task automation, security, audit logging, and extensibility features for running Claude Code agents in production environments.

## High-Level Architecture

The system is built on a **clean layered architecture** that separates concerns into distinct layers, enabling maintainability, testability, and scalability.

```
┌─────────────────────────────────────────────────────────────┐
│                     External Clients                         │
│              (REST API, WebSocket, CLI)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     API Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  REST APIs   │  │  WebSocket   │  │  Middleware  │      │
│  │   (v1/*)     │  │   Streaming  │  │    (CORS,    │      │
│  │              │  │              │  │  Rate Limit) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/api/, app/api/v1/, app/api/middleware/          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Service Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Session    │  │     Task     │  │    Report    │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Storage    │  │    Audit     │  │  MCP Server  │      │
│  │   Manager    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/services/                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Claude SDK Integration Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Client     │  │  Permission  │  │     Hook     │      │
│  │   Manager    │  │   System     │  │    System    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Execution   │  │    Retry     │  │     MCP      │      │
│  │  Strategies  │  │   Manager    │  │  Integration │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/claude_sdk/                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Domain Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Entities   │  │    Value     │  │  Exceptions  │      │
│  │  (Session,   │  │   Objects    │  │   (Domain    │      │
│  │   User,      │  │  (Message,   │  │    Rules)    │      │
│  │   Task)      │  │   ToolCall)  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/domain/entities/, app/domain/value_objects/      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Repository Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Session    │  │     User     │  │     Task     │      │
│  │  Repository  │  │  Repository  │  │  Repository  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/repositories/                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               Data Access Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLAlchemy  │  │     Redis    │  │   Alembic    │      │
│  │  ORM Models  │  │    Cache     │  │  Migrations  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  File: app/models/, app/database/                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Infrastructure Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │     Redis    │  │    Celery    │      │
│  │   Database   │  │   (Cache)    │  │  (Background │      │
│  │              │  │              │  │    Jobs)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Anthropic  │  │  Kubernetes  │                        │
│  │   Claude API │  │  (via MCP)   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`app/api/`)
**Purpose**: HTTP interface for external clients

- **REST Endpoints** ([app/api/v1/](../../app/api/v1/)): Version 1 REST API
  - Sessions: [sessions.py](../../app/api/v1/sessions.py) - Session CRUD and query execution
  - Authentication: [auth.py](../../app/api/v1/auth.py) - JWT token management
  - Tasks: [tasks.py](../../app/api/v1/tasks.py) - Task automation
  - Reports: [reports.py](../../app/api/v1/reports.py) - Report generation
  - MCP Servers: [mcp_servers.py](../../app/api/v1/mcp_servers.py) - MCP management
  - Admin: [admin.py](../../app/api/v1/admin.py) - Admin operations

- **WebSocket** ([app/websocket/](../../app/websocket/)): Real-time streaming

- **Middleware** ([app/api/middleware/](../../app/api/middleware/)): Cross-cutting concerns
  - CORS, rate limiting, request logging, error handling

- **Dependencies** ([dependencies.py](../../app/api/dependencies.py:1-80)): Dependency injection
  - Authentication, database sessions, metrics collection

### 2. Service Layer (`app/services/`)
**Purpose**: Business logic and orchestration

- **SessionService** ([session_service.py](../../app/services/session_service.py:30-100)): Core session management
- **SDKIntegratedSessionService** ([sdk_session_service.py](../../app/services/sdk_session_service.py)): SDK-integrated sessions
- **TaskService** ([task_service.py](../../app/services/task_service.py)): Task automation
- **ReportService** ([report_service.py](../../app/services/report_service.py)): Report generation
- **StorageManager** ([storage_manager.py](../../app/services/storage_manager.py)): File and directory management
- **AuditService** ([audit_service.py](../../app/services/audit_service.py)): Compliance and audit logging
- **MCPServerService** ([mcp_server_service.py](../../app/services/mcp_server_service.py)): MCP server management

### 3. Claude SDK Integration (`app/claude_sdk/`)
**Purpose**: Wrap official claude-agent-sdk with business features

The SDK integration is organized in three phases:

**Phase 1 (Legacy)**:
- **ClaudeSDKClientManager** ([client_manager.py](../../app/claude_sdk/client_manager.py)): SDK client lifecycle
- **PermissionService** ([permission_service.py](../../app/claude_sdk/permission_service.py)): Permission callbacks
- **MessageProcessor** ([message_processor.py](../../app/claude_sdk/message_processor.py)): Message handling

**Phase 2 (Core Components)**:
- **Core** ([core/](../../app/claude_sdk/core/)): ClientConfig, SessionManager, EnhancedClaudeClient
- **Execution** ([execution/](../../app/claude_sdk/execution/)): InteractiveExecutor, BackgroundExecutor, ForkedExecutor
- **Handlers** ([handlers/](../../app/claude_sdk/handlers/)): MessageHandler, StreamHandler, ErrorHandler
- **Retry** ([retry/](../../app/claude_sdk/retry/)): CircuitBreaker, RetryManager

**Phase 3 (Advanced Features)**:
- **Hooks** ([hooks/](../../app/claude_sdk/hooks/)): Hook system for lifecycle events
- **Permissions** ([permissions/](../../app/claude_sdk/permissions/)): Policy engine for access control
- **MCP** ([mcp/](../../app/claude_sdk/mcp/)): MCP server integration
- **Persistence** ([persistence/](../../app/claude_sdk/persistence/)): Session/metrics persistence

### 4. Domain Layer (`app/domain/`)
**Purpose**: Core business entities and rules

**Entities** ([entities/](../../app/domain/entities/)):
- **Session** ([session.py](../../app/domain/entities/session.py:29-209)): Aggregate root for Claude sessions
- **User** ([user.py](../../app/domain/entities/user.py:14-100)): User accounts with roles and quotas
- **Task** ([task.py](../../app/domain/entities/task.py)): Automated task definitions
- **Report** ([report.py](../../app/domain/entities/report.py)): Report metadata
- **MCPServer** ([mcp_server.py](../../app/domain/entities/mcp_server.py)): MCP server configuration
- **SessionTemplate** ([session_template.py](../../app/domain/entities/session_template.py)): Reusable session configs

**Value Objects** ([value_objects/](../../app/domain/value_objects/)):
- **Message** ([message.py](../../app/domain/value_objects/message.py)): Chat messages
- **ToolCall** ([tool_call.py](../../app/domain/value_objects/tool_call.py)): Tool execution records
- **SDKOptions** ([sdk_options.py](../../app/domain/value_objects/sdk_options.py)): SDK configuration

### 5. Repository Layer (`app/repositories/`)
**Purpose**: Data access abstraction

- **BaseRepository** ([base.py](../../app/repositories/base.py:11-86)): Generic CRUD operations
- **SessionRepository** ([session_repository.py](../../app/repositories/session_repository.py)): Session data access
- **UserRepository** ([user_repository.py](../../app/repositories/user_repository.py)): User data access
- **TaskRepository** ([task_repository.py](../../app/repositories/task_repository.py)): Task data access
- Plus 10+ specialized repositories

### 6. Data Access Layer (`app/models/`, `app/database/`)
**Purpose**: Database schema and ORM

- **ORM Models** ([models/](../../app/models/)): SQLAlchemy models matching database schema
- **Migrations** ([alembic/versions/](../../alembic/versions/)): Alembic database migrations
- **Database Session** ([database/session.py](../../app/database/)): Connection management

## Key Architectural Patterns

### 1. **Layered Architecture**
Strict separation of concerns with unidirectional dependencies (API → Service → Repository → Database). See [LAYERED_ARCHITECTURE.md](LAYERED_ARCHITECTURE.md).

### 2. **Domain-Driven Design (DDD)**
- **Entities**: Objects with identity (Session, User, Task)
- **Value Objects**: Immutable objects (Message, ToolCall)
- **Repositories**: Data access abstraction
- **Services**: Domain logic orchestration

See [DOMAIN_MODEL.md](DOMAIN_MODEL.md).

### 3. **Dependency Injection**
FastAPI's dependency injection system is used throughout for:
- Database sessions
- Authentication
- Service instantiation
- Configuration access

See [dependencies.py](../../app/api/dependencies.py).

### 4. **Repository Pattern**
All data access goes through repository interfaces, decoupling domain logic from persistence. See [../data-layer/REPOSITORIES.md](../data-layer/REPOSITORIES.md).

### 5. **Strategy Pattern**
ExecutorFactory selects execution strategies (Interactive, Background, Forked) based on session mode. See [../components/claude_sdk/EXECUTION_STRATEGIES.md](../components/claude_sdk/EXECUTION_STRATEGIES.md).

### 6. **Hook/Event System**
Extensible lifecycle hooks for audit, metrics, notifications. See [../components/claude_sdk/HOOK_SYSTEM.md](../components/claude_sdk/HOOK_SYSTEM.md).

## Request Flow Example

### Creating and Querying a Session

```
1. Client sends POST /api/v1/sessions
   ↓
2. API Layer (sessions.py:56-100)
   - Validates request schema
   - Authenticates user via JWT
   - Extracts request data
   ↓
3. Service Layer (sdk_session_service.py)
   - Creates session entity
   - Validates user quotas
   - Creates working directory
   - Initializes Claude SDK client
   - Persists to database via repository
   ↓
4. Repository Layer (session_repository.py)
   - Converts domain entity to ORM model
   - Saves to PostgreSQL
   ↓
5. Returns SessionResponse to client

---

6. Client sends POST /api/v1/sessions/{id}/query
   ↓
7. API Layer (sessions.py)
   - Validates session exists
   - Authenticates user
   - Extracts query message
   ↓
8. Service Layer (sdk_session_service.py)
   - Retrieves session
   - Selects execution strategy (Interactive/Background)
   - Calls ExecutorFactory
   ↓
9. Claude SDK Layer (execution/)
   - InteractiveExecutor.execute_query()
   - Sends message to Claude SDK
   - Processes streaming response
   - Executes hooks (audit, metrics)
   - Applies permission policies
   ↓
10. Persistence Layer
    - Saves message to database
    - Updates session metrics
    - Logs audit events
    ↓
11. Returns QueryResponse with result
```

See [DATA_FLOW.md](DATA_FLOW.md) for detailed flow diagrams.

## Technology Stack

- **Framework**: FastAPI 0.110+
- **Language**: Python 3.12+
- **Database**: PostgreSQL 15+ (via SQLAlchemy 2.0 async)
- **Cache**: Redis 7+
- **Task Queue**: Celery
- **SDK**: claude-agent-sdk 0.1.4+
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Logging**: structlog
- **Monitoring**: Prometheus, Sentry
- **Testing**: pytest, pytest-asyncio

See [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md) for full details.

## Directory Structure

```
ai-agent-api/
├── app/                           # Application code
│   ├── api/                       # API layer
│   │   ├── v1/                    # Version 1 endpoints
│   │   └── middleware/            # Middleware
│   ├── services/                  # Service layer (business logic)
│   ├── claude_sdk/                # Claude SDK integration
│   ├── domain/                    # Domain layer
│   │   ├── entities/              # Domain entities
│   │   └── value_objects/         # Value objects
│   ├── repositories/              # Repository layer (data access)
│   ├── models/                    # SQLAlchemy ORM models
│   ├── schemas/                   # Pydantic schemas (DTOs)
│   ├── database/                  # Database configuration
│   ├── mcp/                       # MCP tool implementations
│   ├── core/                      # Core utilities (config, logging)
│   ├── tasks/                     # Celery background tasks
│   └── monitoring/                # Monitoring and metrics
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
├── alembic/                       # Database migrations
├── docs/                          # Documentation
├── main.py                        # Application entry point
├── pyproject.toml                 # Dependencies
└── docker-compose.yml             # Development environment
```

## Core Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Dependency Inversion**: Depend on abstractions (repositories), not implementations
3. **Async-First**: All I/O operations are async
4. **Type Safety**: Full type hints with Pydantic and dataclasses
5. **Testability**: Dependency injection enables easy mocking
6. **Security**: JWT auth, RBAC, audit logging
7. **Observability**: Structured logging, metrics, tracing
8. **Resilience**: Circuit breakers, retries, graceful degradation

## Related Documentation

- **Layered Architecture**: [LAYERED_ARCHITECTURE.md](LAYERED_ARCHITECTURE.md)
- **Domain Model**: [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- **Data Flow**: [DATA_FLOW.md](DATA_FLOW.md)
- **Technology Stack**: [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md)
- **Component Details**: [../components/](../components/)

## Keywords

`architecture`, `overview`, `layers`, `fastapi`, `clean-architecture`, `ddd`, `domain-driven-design`, `layered-architecture`, `components`, `system-design`, `claude-sdk`, `postgresql`, `repository-pattern`, `dependency-injection`, `async`, `python`, `rest-api`, `websocket`, `session-management`, `multi-tenant`
