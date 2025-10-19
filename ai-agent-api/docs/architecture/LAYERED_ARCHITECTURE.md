# Layered Architecture

## Purpose

This document explains the layered architecture pattern used in AI-Agent-API, detailing the responsibilities of each layer, their dependencies, and how data flows between them.

## Architecture Principles

The AI-Agent-API follows a **strict layered architecture** where:

1. **Layers can only depend on layers below them** (unidirectional dependency)
2. **Each layer has a single, well-defined responsibility**
3. **Lower layers know nothing about upper layers** (dependency inversion)
4. **Cross-cutting concerns** (logging, auth) use middleware and dependency injection

```
┌─────────────────────────────────────┐
│         Presentation Layer          │  ← HTTP/WebSocket Interface
│           (API Layer)               │
├─────────────────────────────────────┤
│        Application Layer            │  ← Business Logic
│        (Service Layer)              │
├─────────────────────────────────────┤
│      SDK Integration Layer          │  ← Claude SDK Wrapper
│       (Claude SDK Layer)            │
├─────────────────────────────────────┤
│         Domain Layer                │  ← Business Rules & Entities
│    (Entities + Value Objects)       │
├─────────────────────────────────────┤
│        Data Access Layer            │  ← Data Persistence Abstraction
│      (Repository Layer)             │
├─────────────────────────────────────┤
│       Infrastructure Layer          │  ← External Systems
│   (Database, Redis, External APIs)  │
└─────────────────────────────────────┘
```

## Layer Details

### 1. Presentation Layer (API)

**Location**: [`app/api/`](../../app/api/)

**Responsibility**: Handle HTTP/WebSocket requests and responses

**Components**:
- **REST Endpoints** ([`app/api/v1/`](../../app/api/v1/))
  - [sessions.py](../../app/api/v1/sessions.py:56-100) - Session management endpoints
  - [auth.py](../../app/api/v1/auth.py) - Authentication endpoints
  - [tasks.py](../../app/api/v1/tasks.py) - Task automation endpoints
  - [reports.py](../../app/api/v1/reports.py) - Report generation endpoints
  - [mcp_servers.py](../../app/api/v1/mcp_servers.py) - MCP server management

- **WebSocket Handlers** ([`app/websocket/`](../../app/websocket/))
  - Real-time streaming for session queries

- **Middleware** ([`app/api/middleware/`](../../app/api/middleware/))
  - Request ID tracking
  - Logging
  - Rate limiting
  - CORS handling

- **Dependencies** ([`app/api/dependencies.py`](../../app/api/dependencies.py:21-78))
  - JWT authentication (`get_current_user`)
  - Database session injection (`get_db_session`)
  - Service instantiation

**Responsibilities**:
- ✅ Validate request data (Pydantic schemas)
- ✅ Authenticate and authorize users
- ✅ Call service layer methods
- ✅ Transform domain objects to DTOs (response schemas)
- ✅ Handle HTTP errors and status codes
- ❌ No business logic
- ❌ No direct database access
- ❌ No domain rule enforcement

**Example Flow** ([sessions.py](../../app/api/v1/sessions.py:56-100)):
```python
@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,              # ← Request validation
    current_user: User = Depends(get_current_active_user),  # ← Auth
    db: AsyncSession = Depends(get_db_session), # ← DI
) -> SessionResponse:
    # Initialize service layer (business logic)
    service = SDKIntegratedSessionService(...)

    # Call service method
    session = await service.create_session(...)

    # Transform to DTO
    return session_to_response(session)
```

---

### 2. Application Layer (Services)

**Location**: [`app/services/`](../../app/services/)

**Responsibility**: Orchestrate business logic and coordinate between layers

**Components**:
- **SessionService** ([session_service.py](../../app/services/session_service.py:30-100))
  - Core session lifecycle management
  - Working directory management
  - Quota validation

- **SDKIntegratedSessionService** ([sdk_session_service.py](../../app/services/sdk_session_service.py))
  - Extends SessionService with Claude SDK integration
  - Query execution via SDK
  - Session forking

- **TaskService** ([task_service.py](../../app/services/task_service.py))
  - Task template management
  - Task execution scheduling

- **StorageManager** ([storage_manager.py](../../app/services/storage_manager.py))
  - File system operations
  - Working directory creation/archival

- **AuditService** ([audit_service.py](../../app/services/audit_service.py))
  - Audit log creation
  - Compliance tracking

**Responsibilities**:
- ✅ Implement business logic
- ✅ Coordinate between repositories
- ✅ Validate business rules
- ✅ Transaction management
- ✅ Call domain entity methods
- ✅ Orchestrate SDK integration layer
- ❌ No HTTP concerns (status codes, headers)
- ❌ No direct SQL queries
- ❌ No request/response formatting

**Example** ([session_service.py](../../app/services/session_service.py:51-100)):
```python
class SessionService:
    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,      # ← Repository injection
        message_repo: MessageRepository,
        storage_manager: StorageManager,      # ← Service collaboration
        audit_service: AuditService,
    ):
        self.db = db
        self.session_repo = session_repo
        self.storage_manager = storage_manager
        self.audit_service = audit_service

    async def create_session(
        self,
        user_id: UUID,
        mode: SessionMode,
        sdk_options: dict,
    ) -> Session:
        # 1. Business rule: Validate user quotas
        await self._validate_user_quotas(user_id)

        # 2. Create domain entity
        session = Session(
            id=uuid4(),
            user_id=user_id,
            mode=mode,
            sdk_options=sdk_options,
        )

        # 3. Coordinate with infrastructure
        workdir = await self.storage_manager.create_working_directory(session.id)
        session.working_directory_path = str(workdir)

        # 4. Persist via repository
        await self.session_repo.save(session)

        # 5. Audit logging (cross-cutting concern)
        await self.audit_service.log_session_created(session.id, user_id)

        return session
```

**Dependency Direction**: Service → Repository → Database (never Service → API)

---

### 3. SDK Integration Layer

**Location**: [`app/claude_sdk/`](../../app/claude_sdk/)

**Responsibility**: Wrap official claude-agent-sdk with business features

**Components**:
- **Client Management** ([client_manager.py](../../app/claude_sdk/client_manager.py))
  - SDK client lifecycle
  - Connection pooling

- **Execution Strategies** ([execution/](../../app/claude_sdk/execution/))
  - [InteractiveExecutor](../../app/claude_sdk/execution/interactive_executor.py) - Real-time execution
  - [BackgroundExecutor](../../app/claude_sdk/execution/background_executor.py) - Async execution
  - [ForkedExecutor](../../app/claude_sdk/execution/forked_executor.py) - Cloned session execution
  - [ExecutorFactory](../../app/claude_sdk/execution/executor_factory.py) - Strategy selection

- **Permission System** ([permissions/](../../app/claude_sdk/permissions/))
  - Policy engine for file/command/network access

- **Hook System** ([hooks/](../../app/claude_sdk/hooks/))
  - Lifecycle event hooks
  - Audit, metrics, validation hooks

- **Retry & Resilience** ([retry/](../../app/claude_sdk/retry/))
  - Circuit breakers
  - Retry policies

**Responsibilities**:
- ✅ Wrap claude-agent-sdk API
- ✅ Provide execution strategies
- ✅ Implement permission callbacks
- ✅ Execute lifecycle hooks
- ✅ Handle SDK errors and retries
- ❌ No direct database access (uses repositories via service layer)
- ❌ No HTTP concerns

**Example** ([execution/interactive_executor.py](../../app/claude_sdk/execution/)):
```python
class InteractiveExecutor(BaseExecutor):
    async def execute_query(
        self,
        session: Session,
        message: str,
    ) -> ExecutionResult:
        # 1. Get SDK client
        client = await self.client_manager.get_client(session.id)

        # 2. Execute hooks (before)
        await self.hook_manager.execute_hooks(HookType.BEFORE_QUERY, ...)

        # 3. Check permissions
        if not await self.permission_manager.check_permissions(...):
            raise PermissionDeniedError()

        # 4. Execute via SDK
        response = await client.send_message(message)

        # 5. Execute hooks (after)
        await self.hook_manager.execute_hooks(HookType.AFTER_QUERY, ...)

        # 6. Persist via service layer
        await self.session_persister.save_message(...)

        return ExecutionResult(response)
```

---

### 4. Domain Layer

**Location**: [`app/domain/`](../../app/domain/)

**Responsibility**: Core business entities, value objects, and business rules

**Components**:

**Entities** ([`entities/`](../../app/domain/entities/)):
- [Session](../../app/domain/entities/session.py:29-209) - Session aggregate root with state machine
- [User](../../app/domain/entities/user.py:14-100) - User with roles and quotas
- [Task](../../app/domain/entities/task.py) - Task definition
- [Report](../../app/domain/entities/report.py) - Report metadata
- [MCPServer](../../app/domain/entities/mcp_server.py) - MCP server configuration

**Value Objects** ([`value_objects/`](../../app/domain/value_objects/)):
- [Message](../../app/domain/value_objects/message.py) - Immutable message
- [ToolCall](../../app/domain/value_objects/tool_call.py) - Tool execution record
- [SDKOptions](../../app/domain/value_objects/sdk_options.py) - SDK configuration

**Enums** ([`entities/session.py`](../../app/domain/entities/session.py:8-27)):
- `SessionStatus`: CREATED, CONNECTING, ACTIVE, PAUSED, COMPLETED, FAILED, TERMINATED, ARCHIVED
- `SessionMode`: INTERACTIVE, NON_INTERACTIVE, FORKED
- `UserRole`: ADMIN, USER, VIEWER

**Responsibilities**:
- ✅ Define business entities with identity
- ✅ Enforce business rules (e.g., state transitions)
- ✅ Provide domain methods (e.g., `session.transition_to()`)
- ✅ Value object immutability
- ❌ No persistence logic
- ❌ No API/HTTP concerns
- ❌ No external service calls

**Example** ([session.py](../../app/domain/entities/session.py:93-133)):
```python
class Session:
    """Session aggregate root."""

    def can_transition_to(self, new_status: SessionStatus) -> bool:
        """Business rule: Valid state transitions."""
        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.CONNECTING, SessionStatus.TERMINATED],
            SessionStatus.CONNECTING: [SessionStatus.ACTIVE, SessionStatus.FAILED],
            SessionStatus.ACTIVE: [
                SessionStatus.WAITING,
                SessionStatus.PROCESSING,
                SessionStatus.COMPLETED,
                SessionStatus.FAILED,
            ],
            # ...
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: SessionStatus) -> None:
        """Transition to new status with validation."""
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Business logic: Set timestamps on state changes
        if new_status == SessionStatus.ACTIVE and not self.started_at:
            self.started_at = datetime.utcnow()
```

**Key Principle**: Domain entities are **framework-agnostic**. They don't know about FastAPI, SQLAlchemy, or PostgreSQL.

---

### 5. Data Access Layer (Repository)

**Location**: [`app/repositories/`](../../app/repositories/)

**Responsibility**: Abstract data persistence and retrieval

**Components**:
- **BaseRepository** ([base.py](../../app/repositories/base.py:11-86))
  - Generic CRUD operations
  - Pagination, filtering, counting

- **Specialized Repositories**:
  - [SessionRepository](../../app/repositories/session_repository.py) - Session data access
  - [UserRepository](../../app/repositories/user_repository.py) - User data access
  - [TaskRepository](../../app/repositories/task_repository.py) - Task data access
  - [MessageRepository](../../app/repositories/message_repository.py) - Message data access
  - [ToolCallRepository](../../app/repositories/tool_call_repository.py) - Tool call data access
  - [ReportRepository](../../app/repositories/report_repository.py) - Report data access

**Responsibilities**:
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Query building
- ✅ Convert between domain entities and ORM models
- ✅ Data filtering and pagination
- ❌ No business logic
- ❌ No domain rule enforcement

**Example** ([base.py](../../app/repositories/base.py:11-50)):
```python
class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None,
    ) -> List[ModelType]:
        """Get all records with optional filters."""
        query = select(self.model)

        if filters:
            for filter_condition in filters:
                query = query.where(filter_condition)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

**Specialized Repository Example** ([session_repository.py](../../app/repositories/session_repository.py)):
```python
class SessionRepository:
    async def get_active_sessions_for_user(
        self,
        user_id: UUID,
    ) -> List[SessionModel]:
        """Get all active sessions for a user."""
        result = await self.db.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.status.in_([
                SessionStatus.ACTIVE.value,
                SessionStatus.WAITING.value,
                SessionStatus.PROCESSING.value,
            ]))
        )
        return list(result.scalars().all())
```

---

### 6. Infrastructure Layer

**Location**: [`app/models/`](../../app/models/), [`app/database/`](../../app/database/)

**Responsibility**: External systems and data storage

**Components**:
- **ORM Models** ([`app/models/`](../../app/models/))
  - SQLAlchemy models representing database tables
  - Relationships and constraints

- **Database Connection** ([`app/database/session.py`](../../app/database/))
  - Async SQLAlchemy engine
  - Session factory

- **Migrations** ([`alembic/versions/`](../../alembic/versions/))
  - Database schema migrations

**External Systems**:
- PostgreSQL (primary database)
- Redis (caching, sessions)
- Celery (background jobs)
- Anthropic Claude API (via SDK)
- Kubernetes API (via MCP)

**Responsibilities**:
- ✅ Database schema definition
- ✅ Connection management
- ✅ Migration scripts
- ✅ External API clients
- ❌ No business logic
- ❌ No domain rules

**Example ORM Model** ([models/session.py](../../app/models/session.py)):
```python
class SessionModel(Base):
    """SQLAlchemy ORM model for sessions table."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=True)
    mode = Column(String, nullable=False)  # SessionMode enum value
    status = Column(String, nullable=False)  # SessionStatus enum value
    sdk_options = Column(JSON, nullable=False, default=dict)

    # Relationships
    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session")
    tool_calls = relationship("ToolCallModel", back_populates="session")
```

---

## Layer Dependencies

### Allowed Dependencies (Top → Bottom)

```
API Layer
  ↓ can use
Service Layer
  ↓ can use
SDK Integration Layer
  ↓ can use
Domain Layer
  ↓ can use
Repository Layer
  ↓ can use
Infrastructure Layer
```

### Forbidden Dependencies

```
❌ Domain Layer → Repository Layer
❌ Domain Layer → Service Layer
❌ Repository Layer → Service Layer
❌ Infrastructure Layer → any upper layer
```

### How Layers Communicate

**Upward Communication** (via interfaces/callbacks):
- Domain raises exceptions (caught by service layer)
- Repositories return domain entities (created by service layer)
- Infrastructure emits events (handled by service layer)

**Example**:
```python
# Domain entity raises exception
class Session:
    def transition_to(self, new_status: SessionStatus) -> None:
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(...)  # ← Domain exception

# Service layer catches and handles
class SessionService:
    async def activate_session(self, session_id: UUID) -> Session:
        session = await self.session_repo.get_by_id(session_id)

        try:
            session.transition_to(SessionStatus.ACTIVE)  # ← Call domain method
        except InvalidStateTransitionError as e:
            # Service layer handles domain exception
            await self.audit_service.log_error(...)
            raise SessionCannotActivateError(...) from e
```

---

## Cross-Cutting Concerns

### 1. Authentication & Authorization
**Implementation**: Middleware + Dependency Injection

- **Middleware** ([`app/api/middleware/`](../../app/api/middleware/))
- **Dependencies** ([`dependencies.py:21-78`](../../app/api/dependencies.py:21-78))

```python
# Injected into API layer
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    # Decode JWT, validate, fetch user
    ...
```

### 2. Logging
**Implementation**: Structured logging via structlog

- **Setup** ([`app/core/logging.py`](../../app/core/logging.py))
- **Usage**: All layers import logger

```python
from app.core.logging import get_logger
logger = get_logger(__name__)

logger.info("Session created", session_id=session.id, user_id=user.id)
```

### 3. Error Handling
**Implementation**: Exception handlers at API layer

- **Handlers** ([`app/api/exception_handlers.py`](../../app/api/exception_handlers.py))
- **Main app** ([`main.py:96-100`](../../main.py:96-100))

```python
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(SDKError, sdk_exception_handler)
```

### 4. Transactions
**Implementation**: Service layer manages transactions

```python
async def create_session_with_template(self, ...):
    async with self.db.begin():  # ← Transaction boundary
        session = await self.session_repo.create(...)
        template = await self.template_repo.apply_to(session)
        await self.audit_service.log_action(...)
    # Auto-commit or rollback on exception
```

---

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently with mocks
2. **Maintainability**: Changes in one layer don't affect others
3. **Scalability**: Layers can be optimized independently
4. **Flexibility**: Easy to swap implementations (e.g., PostgreSQL → MongoDB)
5. **Separation of Concerns**: Clear responsibility boundaries
6. **Reusability**: Domain logic can be reused across different interfaces

---

## Common Patterns

### 1. Entity → Model Conversion (Domain → ORM)
**Where**: Service layer

```python
# Service layer converts domain entity to ORM model
session_entity = Session(...)  # Domain entity

session_model = SessionModel(  # ORM model
    id=session_entity.id,
    user_id=session_entity.user_id,
    status=session_entity.status.value,  # Enum → string
    ...
)
self.db.add(session_model)
```

### 2. Model → Entity Conversion (ORM → Domain)
**Where**: Repository layer

```python
class SessionRepository:
    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        # Get ORM model
        model = await self.db.get(SessionModel, session_id)

        # Convert to domain entity
        if model:
            return Session(
                id=model.id,
                user_id=model.user_id,
                mode=SessionMode(model.mode),  # String → enum
                status=SessionStatus(model.status),
                ...
            )
        return None
```

### 3. DTO Conversion (Entity → Response Schema)
**Where**: API layer

```python
from app.schemas.mappers import session_to_response

@router.get("/{session_id}")
async def get_session(...) -> SessionResponse:
    session_entity = await service.get_session(session_id)
    return session_to_response(session_entity)  # ← DTO conversion
```

---

## Related Documentation

- **Overview**: [OVERVIEW.md](OVERVIEW.md) - System architecture overview
- **Domain Model**: [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Domain entities and rules
- **Data Flow**: [DATA_FLOW.md](DATA_FLOW.md) - Request flow through layers
- **Repositories**: [../data-layer/REPOSITORIES.md](../data-layer/REPOSITORIES.md) - Repository pattern details

## Keywords

`layered-architecture`, `clean-architecture`, `layers`, `separation-of-concerns`, `dependency-injection`, `api-layer`, `service-layer`, `repository-layer`, `domain-layer`, `infrastructure-layer`, `ddd`, `repository-pattern`, `orm`, `sqlalchemy`, `fastapi`, `async`, `python`, `architecture-patterns`, `solid-principles`
