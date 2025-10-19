# Domain Model

## Purpose

This document describes the domain model of the AI-Agent-API, including domain entities, value objects, aggregates, and business rules. The domain layer is the heart of the application, containing core business logic independent of infrastructure concerns.

## Domain-Driven Design (DDD) Concepts

The AI-Agent-API follows **Domain-Driven Design** principles:

- **Entities**: Objects with unique identity that persist over time
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Clusters of entities and value objects with a root entity
- **Domain Services**: Stateless operations that don't belong to entities
- **Domain Events**: Things that happened in the domain

```
┌─────────────────────────────────────────────────┐
│              DOMAIN LAYER                       │
│                                                 │
│  ┌───────────────┐      ┌──────────────────┐   │
│  │   ENTITIES    │      │  VALUE OBJECTS   │   │
│  │  (Identity)   │      │  (Immutable)     │   │
│  ├───────────────┤      ├──────────────────┤   │
│  │ - Session     │      │ - Message        │   │
│  │ - User        │      │ - ToolCall       │   │
│  │ - Task        │      │ - SDKOptions     │   │
│  │ - Report      │      │                  │   │
│  │ - MCPServer   │      │                  │   │
│  └───────────────┘      └──────────────────┘   │
│                                                 │
│  ┌───────────────┐      ┌──────────────────┐   │
│  │   ENUMS       │      │  EXCEPTIONS      │   │
│  ├───────────────┤      ├──────────────────┤   │
│  │ SessionStatus │      │ ValidationError  │   │
│  │ SessionMode   │      │ BusinessError    │   │
│  │ UserRole      │      │ StateTransition  │   │
│  │ ReportFormat  │      │      Error       │   │
│  └───────────────┘      └──────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Domain Entities

**Location**: [`app/domain/entities/`](../../app/domain/entities/)

Entities are objects with **unique identity** and a lifecycle. Two entities with the same ID are considered the same object, even if their attributes differ.

### 1. Session (Aggregate Root)

**File**: [session.py](../../app/domain/entities/session.py:29-209)

**Purpose**: Represents a Claude Code agent session with working directory, message history, and execution state.

**Key Attributes**:
```python
class Session:
    # Identity
    id: UUID                           # Unique identifier
    user_id: UUID                      # Owner

    # Configuration
    name: Optional[str]
    mode: SessionMode                  # INTERACTIVE | NON_INTERACTIVE | FORKED
    status: SessionStatus              # State machine status
    sdk_options: dict                  # Claude SDK configuration

    # Working Directory
    working_directory_path: Optional[str]

    # Forking
    parent_session_id: Optional[UUID]
    is_fork: bool

    # SDK Configuration
    include_partial_messages: bool
    max_retries: int
    retry_delay: float
    timeout_seconds: int
    hooks_enabled: List[str]
    permission_mode: str
    custom_policies: List[str]

    # Metrics
    total_messages: int
    total_tool_calls: int
    total_cost_usd: float
    total_hook_executions: int
    total_permission_checks: int
    total_errors: int
    total_retries: int

    # API Usage
    api_input_tokens: int
    api_output_tokens: int
    api_cache_creation_tokens: int
    api_cache_read_tokens: int

    # Result
    result_data: Optional[dict]
    error_message: Optional[str]

    # Archival
    archive_id: Optional[UUID]
    template_id: Optional[UUID]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
```

**State Machine** ([session.py:8-20](../../app/domain/entities/session.py:8-20)):
```python
class SessionStatus(str, Enum):
    CREATED = "created"          # Initial state
    CONNECTING = "connecting"    # Connecting to SDK
    ACTIVE = "active"            # Running and accepting queries
    PAUSED = "paused"            # Temporarily suspended
    WAITING = "waiting"          # Waiting for user input
    PROCESSING = "processing"    # Executing a query
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"            # Failed with error
    TERMINATED = "terminated"    # Manually terminated
    ARCHIVED = "archived"        # Archived (final state)
```

**Valid State Transitions** ([session.py:93-114](../../app/domain/entities/session.py:93-114)):
```
CREATED → CONNECTING | TERMINATED
CONNECTING → ACTIVE | FAILED
ACTIVE → WAITING | PROCESSING | PAUSED | COMPLETED | FAILED | TERMINATED
WAITING → ACTIVE | PROCESSING | TERMINATED
PROCESSING → ACTIVE | COMPLETED | FAILED
PAUSED → ACTIVE | TERMINATED
COMPLETED → ARCHIVED
FAILED → ARCHIVED
TERMINATED → ARCHIVED
ARCHIVED → (final state, no transitions)
```

**Business Rules**:

1. **State Transition Validation** ([session.py:116-133](../../app/domain/entities/session.py:116-133)):
```python
def transition_to(self, new_status: SessionStatus) -> None:
    """Transition to new status with validation."""
    if not self.can_transition_to(new_status):
        raise InvalidStateTransitionError(
            f"Cannot transition from {self.status} to {new_status}"
        )
    self.status = new_status
    self.updated_at = datetime.utcnow()

    # Automatic timestamp updates
    if new_status == SessionStatus.ACTIVE and not self.started_at:
        self.started_at = datetime.utcnow()
    elif new_status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.TERMINATED]:
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
```

2. **Active State Check** ([session.py:163-169](../../app/domain/entities/session.py:163-169)):
```python
def is_active(self) -> bool:
    """Check if session is in active state."""
    return self.status in [
        SessionStatus.ACTIVE,
        SessionStatus.WAITING,
        SessionStatus.PROCESSING,
    ]
```

3. **Terminal State Check** ([session.py:171-178](../../app/domain/entities/session.py:171-178)):
```python
def is_terminal(self) -> bool:
    """Check if session is in terminal state."""
    return self.status in [
        SessionStatus.COMPLETED,
        SessionStatus.FAILED,
        SessionStatus.TERMINATED,
        SessionStatus.ARCHIVED,
    ]
```

4. **Metric Tracking** ([session.py:134-208](../../app/domain/entities/session.py:134-208)):
- `increment_message_count()`
- `increment_tool_call_count()`
- `add_cost(cost_usd: float)`
- `update_api_tokens(...)`
- `increment_hook_execution_count()`
- `increment_permission_check_count()`
- `increment_error_count()`
- `increment_retry_count()`

**Session Modes** ([session.py:22-27](../../app/domain/entities/session.py:22-27)):
```python
class SessionMode(str, Enum):
    INTERACTIVE = "interactive"          # Real-time query execution
    NON_INTERACTIVE = "non_interactive"  # Background execution
    FORKED = "forked"                    # Cloned from parent session
```

---

### 2. User (Aggregate Root)

**File**: [user.py](../../app/domain/entities/user.py:14-100)

**Purpose**: Represents a user account with roles, permissions, and quotas.

**Key Attributes**:
```python
class User:
    # Identity
    id: UUID
    organization_id: UUID

    # Authentication
    email: str
    username: str
    password_hash: str

    # Profile
    full_name: Optional[str]
    avatar_url: Optional[str]

    # Authorization
    role: str                           # UserRole constant
    is_active: bool
    is_superuser: bool

    # Quotas & Limits
    max_concurrent_sessions: int        # Default: 5
    max_api_calls_per_hour: int         # Default: 1000
    max_storage_mb: int                 # Default: 10GB

    # Audit
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    deleted_at: Optional[datetime]
```

**User Roles** ([user.py:7-11](../../app/domain/entities/user.py:7-11)):
```python
class UserRole:
    ADMIN = "admin"      # Full access
    USER = "user"        # Standard access
    VIEWER = "viewer"    # Read-only access
```

**Business Rules**:

1. **Role Validation** ([user.py:66-75](../../app/domain/entities/user.py:66-75)):
```python
def set_role(self, role: str) -> None:
    """Set user role with validation."""
    valid_roles = [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]
    if role not in valid_roles:
        raise ValidationError(f"Invalid role: {role}")
    self.role = role
    self.updated_at = datetime.utcnow()
```

2. **Admin Check** ([user.py:93-95](../../app/domain/entities/user.py:93-95)):
```python
def is_admin(self) -> bool:
    """Check if user is admin."""
    return self.role == UserRole.ADMIN or self.is_superuser
```

3. **Session Access Control** ([user.py:97-100](../../app/domain/entities/user.py:97-100)):
```python
def can_access_session(self, session_user_id: UUID) -> bool:
    """Check if user can access a session."""
    return self.is_admin() or self.id == session_user_id
```

4. **Quota Management** ([user.py:77-91](../../app/domain/entities/user.py:77-91)):
```python
def update_quotas(
    self,
    max_concurrent_sessions: Optional[int] = None,
    max_api_calls_per_hour: Optional[int] = None,
    max_storage_mb: Optional[int] = None,
) -> None:
    """Update user quotas."""
    if max_concurrent_sessions is not None:
        self.max_concurrent_sessions = max_concurrent_sessions
    # ...
    self.updated_at = datetime.utcnow()
```

---

### 3. Task

**File**: [task.py](../../app/domain/entities/task.py:7-95)

**Purpose**: Represents an automated task template with scheduling and reporting.

**Key Attributes**:
```python
class Task:
    # Identity
    id: UUID
    user_id: UUID

    # Definition
    name: str
    description: Optional[str]
    prompt_template: str               # Jinja2 template
    allowed_tools: List[str]
    disallowed_tools: List[str]
    sdk_options: dict
    working_directory_path: Optional[str]

    # Scheduling
    is_scheduled: bool
    schedule_cron: Optional[str]       # Cron expression
    schedule_enabled: bool

    # Post-execution
    generate_report: bool
    report_format: Optional[str]       # json | markdown | html | pdf
    notification_config: Optional[dict]

    # Metadata
    tags: List[str]
    is_public: bool
    is_active: bool
    is_deleted: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
```

**Business Rules**:

1. **Prompt Rendering** ([task.py:50-54](../../app/domain/entities/task.py:50-54)):
```python
def render_prompt(self, variables: dict) -> str:
    """Render prompt template with variables using Jinja2."""
    from jinja2 import Template
    template = Template(self.prompt_template)
    return template.render(**variables)
```

2. **Schedule Validation** ([task.py:56-67](../../app/domain/entities/task.py:56-67)):
```python
def validate_schedule(self) -> None:
    """Validate cron expression if scheduled."""
    if self.is_scheduled:
        if not self.schedule_cron:
            raise ValidationError("schedule_cron required when is_scheduled=True")

        from croniter import croniter
        if not croniter.is_valid(self.schedule_cron):
            raise ValidationError(f"Invalid cron expression: {self.schedule_cron}")
```

3. **Report Format Validation** ([task.py:69-78](../../app/domain/entities/task.py:69-78)):
```python
def validate_report_format(self) -> None:
    """Validate report format if report generation enabled."""
    if self.generate_report:
        valid_formats = ["json", "markdown", "html", "pdf"]
        if not self.report_format or self.report_format not in valid_formats:
            raise ValidationError(
                f"Invalid report_format: {self.report_format}. Must be one of {valid_formats}"
            )
```

---

### 4. Other Entities

**Report** ([report.py](../../app/domain/entities/report.py)):
- Report metadata for session exports
- Formats: JSON, Markdown, HTML, PDF
- Includes session data, messages, tool calls, metrics

**MCPServer** ([mcp_server.py](../../app/domain/entities/mcp_server.py)):
- MCP server configuration
- Server types: BUILTIN, STDIO, SSE
- Tool registry and capabilities

**SessionTemplate** ([session_template.py](../../app/domain/entities/session_template.py)):
- Reusable session configurations
- Template variables with Jinja2
- Categories: GENERAL, DEVOPS, DATA_ANALYSIS, etc.

**HookExecution** ([hook_execution.py](../../app/domain/entities/hook_execution.py)):
- Tracks hook execution events
- Hook types, duration, result

**PermissionDecision** ([permission_decision.py](../../app/domain/entities/permission_decision.py)):
- Records permission check decisions
- ALLOW | DENY | ASK
- Policy evaluation results

**ArchiveMetadata** ([archive_metadata.py](../../app/domain/entities/archive_metadata.py)):
- Working directory archive metadata
- Compression format, size, file count

---

## Value Objects

**Location**: [`app/domain/value_objects/`](../../app/domain/value_objects/)

Value objects are **immutable** and defined by their attributes (no unique identity). Two value objects with the same attributes are considered equal.

### 1. Message

**File**: [message.py](../../app/domain/value_objects/message.py:18-115)

**Purpose**: Immutable chat message in a session.

**Structure**:
```python
@dataclass(frozen=True)  # ← Immutable
class Message:
    id: UUID
    session_id: UUID
    message_type: MessageType        # USER | ASSISTANT | SYSTEM | RESULT
    content: Dict[str, Any]          # JSONB format
    sequence_number: int
    created_at: datetime
    model: Optional[str] = None
    parent_tool_use_id: Optional[str] = None
```

**Message Types** ([message.py:9-14](../../app/domain/value_objects/message.py:9-14)):
```python
class MessageType(str, Enum):
    USER = "user"              # User input
    ASSISTANT = "assistant"    # Claude response
    SYSTEM = "system"          # System message
    RESULT = "result"          # Tool execution result
```

**Factory Methods** ([message.py:29-92](../../app/domain/value_objects/message.py:29-92)):
```python
@classmethod
def from_user_text(cls, session_id: UUID, text: str, sequence: int) -> "Message":
    """Create user text message."""
    return cls(
        id=uuid4(),
        session_id=session_id,
        message_type=MessageType.USER,
        content={"content": text},
        sequence_number=sequence,
        created_at=datetime.utcnow(),
    )

@classmethod
def from_assistant(cls, session_id: UUID, content: Dict, sequence: int, model: Optional[str]) -> "Message":
    """Create assistant message."""
    # ...

@classmethod
def from_system(cls, ...) -> "Message":
    """Create system message."""
    # ...

@classmethod
def from_result(cls, ...) -> "Message":
    """Create result message."""
    # ...
```

**Query Methods** ([message.py:94-114](../../app/domain/value_objects/message.py:94-114)):
```python
def is_user_message(self) -> bool
def is_assistant_message(self) -> bool
def is_system_message(self) -> bool
def is_result_message(self) -> bool
def get_text_content(self) -> Optional[str]
```

**Immutability**: Messages are `frozen=True` dataclasses, meaning once created, they cannot be modified. To change a message, create a new instance.

---

### 2. ToolCall

**File**: [tool_call.py](../../app/domain/value_objects/tool_call.py:26-131)

**Purpose**: Immutable record of a tool execution.

**Structure**:
```python
@dataclass(frozen=True)
class ToolCall:
    id: UUID
    session_id: UUID
    tool_name: str
    tool_use_id: str
    tool_input: Dict[str, Any]
    status: ToolCallStatus            # PENDING | RUNNING | SUCCESS | ERROR | DENIED
    created_at: datetime
    message_id: Optional[UUID] = None
    tool_output: Optional[Dict[str, Any]] = None
    is_error: bool = False
    error_message: Optional[str] = None
    permission_decision: Optional[PermissionDecision] = None  # ALLOW | DENY | ASK
    permission_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
```

**Tool Call Status** ([tool_call.py:9-15](../../app/domain/value_objects/tool_call.py:9-15)):
```python
class ToolCallStatus(str, Enum):
    PENDING = "pending"      # Created, awaiting execution
    RUNNING = "running"      # Executing
    SUCCESS = "success"      # Completed successfully
    ERROR = "error"          # Failed with error
    DENIED = "denied"        # Permission denied
```

**Permission Decision** ([tool_call.py:18-22](../../app/domain/value_objects/tool_call.py:18-22)):
```python
class PermissionDecision(str, Enum):
    ALLOW = "allow"  # Permission granted
    DENY = "deny"    # Permission denied
    ASK = "ask"      # Ask user for permission
```

**Immutability Pattern** ([tool_call.py:66-115](../../app/domain/value_objects/tool_call.py:66-115)):

Since ToolCall is frozen, modifications create new instances:

```python
def with_status(self, status: ToolCallStatus) -> "ToolCall":
    """Create new instance with updated status."""
    from dataclasses import replace
    return replace(self, status=status)

def with_permission(self, decision: PermissionDecision, reason: Optional[str]) -> "ToolCall":
    """Create new instance with permission decision."""
    from dataclasses import replace
    return replace(self, permission_decision=decision, permission_reason=reason)

def with_output(self, output: Dict, is_error: bool, error_message: Optional[str]) -> "ToolCall":
    """Create new instance with output."""
    from dataclasses import replace
    completed_at = datetime.utcnow()
    duration_ms = int((completed_at - self.started_at).total_seconds() * 1000) if self.started_at else None

    return replace(
        self,
        tool_output=output,
        is_error=is_error,
        error_message=error_message,
        status=ToolCallStatus.ERROR if is_error else ToolCallStatus.SUCCESS,
        completed_at=completed_at,
        duration_ms=duration_ms,
    )

def with_started(self) -> "ToolCall":
    """Create new instance marked as started."""
    return replace(self, status=ToolCallStatus.RUNNING, started_at=datetime.utcnow())
```

---

### 3. SDKOptions

**File**: [sdk_options.py](../../app/domain/value_objects/sdk_options.py)

**Purpose**: Immutable SDK configuration options.

Contains:
- Permission mode
- Allowed/disallowed tools
- Retry configuration
- Timeout settings
- Hook configuration

---

## Domain Exceptions

**Location**: [`app/domain/exceptions.py`](../../app/domain/exceptions.py)

Domain exceptions represent business rule violations:

```python
class ValidationError(Exception):
    """Raised when domain validation fails."""
    pass

class InvalidStateTransitionError(Exception):
    """Raised when invalid state transition attempted."""
    pass

class SessionNotFoundError(Exception):
    """Raised when session doesn't exist."""
    pass

class SessionNotActiveError(Exception):
    """Raised when operation requires active session."""
    pass

class PermissionDeniedError(Exception):
    """Raised when permission check fails."""
    pass

class QuotaExceededError(Exception):
    """Raised when user quota exceeded."""
    pass
```

These exceptions are caught and handled by the **service layer**, never by the domain layer itself.

---

## Aggregates

An **aggregate** is a cluster of domain objects (entities + value objects) with a root entity that controls access.

### Session Aggregate

**Root**: Session entity

**Components**:
- Session (root entity)
- Messages (value objects, collection)
- ToolCalls (value objects, collection)
- HookExecutions (entities, collection)
- PermissionDecisions (entities, collection)
- ArchiveMetadata (entity, optional)

**Invariants**:
1. Messages must have sequential `sequence_number`
2. Session must be ACTIVE to accept new queries
3. Cannot delete session with active tool calls
4. Archive can only be created for terminal sessions

**Access Rule**: All operations on aggregate components must go through the Session root.

---

## Domain Enums

Enums provide type-safe constants for domain concepts:

**SessionStatus** ([session.py:8-19](../../app/domain/entities/session.py:8-19))
**SessionMode** ([session.py:22-26](../../app/domain/entities/session.py:22-26))
**MessageType** ([message.py:9-14](../../app/domain/value_objects/message.py:9-14))
**ToolCallStatus** ([tool_call.py:9-15](../../app/domain/value_objects/tool_call.py:9-15))
**PermissionDecision** ([tool_call.py:18-22](../../app/domain/value_objects/tool_call.py:18-22))
**UserRole** ([user.py:7-11](../../app/domain/entities/user.py:7-11))
**ReportFormat**: JSON, MARKDOWN, HTML, PDF
**ReportType**: SESSION, TASK_EXECUTION, AUDIT
**TemplateCategory**: GENERAL, DEVOPS, DATA_ANALYSIS, SECURITY

---

## Entity vs Value Object Guidelines

**Use Entity when**:
- Object has unique identity (ID)
- Object lifecycle matters (created, updated, deleted)
- Object can change over time
- Examples: Session, User, Task

**Use Value Object when**:
- Object is defined by its attributes
- Object is immutable
- Two objects with same attributes are equal
- Examples: Message, ToolCall, Address

---

## Domain Services

Domain services are **stateless** operations that don't naturally belong to entities.

Examples (not yet implemented):
- **SessionCloner**: Clone session with working directory
- **PermissionEvaluator**: Evaluate complex permission rules
- **ReportGenerator**: Generate reports from session data

Currently, these are implemented in the **service layer** ([`app/services/`](../../app/services/)), but could be refactored to domain services.

---

## Relationship Diagram

```
User (1) ─────────< (N) Session
                       │
                       ├────< (N) Message
                       ├────< (N) ToolCall
                       ├────< (N) HookExecution
                       ├────< (N) PermissionDecision
                       └────< (1) ArchiveMetadata

User (1) ─────────< (N) Task
                       │
                       └────< (N) TaskExecution
                                  │
                                  └────< (1) Session

User (1) ─────────< (N) Report
                       │
                       └────< (1) Session

User (1) ─────────< (N) MCPServer
  │                    │
  └──< (N) SessionTemplate
```

---

## Domain Rules Summary

### Session Rules
1. Status transitions must follow state machine
2. Cannot query non-active sessions
3. Cannot delete active sessions
4. Metrics are auto-updated on events
5. Timestamps are auto-managed on state changes

### User Rules
1. Role must be ADMIN | USER | VIEWER
2. Active users can exceed quotas temporarily
3. Admins can access all sessions
4. Users can only access own sessions

### Task Rules
1. Cron expression must be valid
2. Report format must be valid
3. Prompt template must be valid Jinja2
4. Scheduled tasks must have cron expression

### Message Rules
1. Sequence numbers must be sequential
2. Messages are immutable once created
3. Content structure varies by message type

### ToolCall Rules
1. Permission decision required before execution
2. Tool calls are immutable once created
3. Duration calculated on completion
4. DENIED tool calls are never executed

---

## Best Practices

1. **Keep domain logic in domain layer**: Don't put business rules in services
2. **Use factory methods**: Create value objects via factory methods
3. **Enforce invariants**: Validate in entity methods, not constructors
4. **Raise domain exceptions**: Use specific exceptions for rule violations
5. **Immutable value objects**: Use `@dataclass(frozen=True)`
6. **State machines**: Use enums and transition validation
7. **Rich domain models**: Entities should have behavior, not just getters/setters

---

## Related Documentation

- **Architecture Overview**: [OVERVIEW.md](OVERVIEW.md)
- **Layered Architecture**: [LAYERED_ARCHITECTURE.md](LAYERED_ARCHITECTURE.md)
- **Data Layer**: [../data-layer/DATABASE_SCHEMA.md](../data-layer/DATABASE_SCHEMA.md)
- **ORM Models**: [../data-layer/ORM_MODELS.md](../data-layer/ORM_MODELS.md)

## Keywords

`domain-model`, `ddd`, `domain-driven-design`, `entities`, `value-objects`, `aggregates`, `session`, `user`, `task`, `message`, `tool-call`, `state-machine`, `business-rules`, `immutability`, `domain-logic`, `enums`, `domain-exceptions`, `aggregate-root`, `invariants`
