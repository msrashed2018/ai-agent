# Repositories

## Purpose

Complete documentation of the Repository pattern implementation for data access abstraction. Repositories provide a clean separation between business logic and data persistence, offering type-safe async database operations.

---

## Repository Pattern Overview

### What is the Repository Pattern?

The Repository pattern abstracts data access logic from business logic:

```
Service Layer → Repository → Database
```

**Benefits**:
- **Abstraction**: Business logic doesn't know about database implementation
- **Testability**: Easy to mock repositories in tests
- **Maintainability**: Centralized data access logic
- **Swappable Backends**: Can switch databases without changing services
- **Type Safety**: Strong typing with TypeVar generics

---

## BaseRepository

### Purpose

Generic base class providing common CRUD operations for all repositories.

**File**: [app/repositories/base.py](../../app/repositories/base.py)

### Type Safety

```python
from typing import Generic, TypeVar, Type
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
```

### Core Methods

#### create(**kwargs)

**Purpose**: Create a new record

```python
async def create(self, **kwargs) -> ModelType:
    """Create a new record."""
    instance = self.model(**kwargs)
    self.db.add(instance)
    await self.db.flush()
    await self.db.refresh(instance)
    return instance
```

**Example**:
```python
session = await session_repo.create(
    user_id=user_id,
    name="My Session",
    mode="interactive",
    status="created"
)
```

#### get_by_id(id: UUID)

**Purpose**: Get single record by ID

```python
async def get_by_id(self, id: UUID) -> Optional[ModelType]:
    """Get record by ID."""
    result = await self.db.execute(
        select(self.model).where(self.model.id == id)
    )
    return result.scalar_one_or_none()
```

**Example**:
```python
session = await session_repo.get_by_id(session_id)
if session:
    print(f"Found session: {session.name}")
```

#### get_all(skip, limit, filters)

**Purpose**: Get multiple records with pagination and filtering

```python
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

**Example**:
```python
# Get first 50 active users
users = await user_repo.get_all(
    skip=0,
    limit=50,
    filters=[UserModel.is_active == True]
)
```

#### update(id: UUID, **kwargs)

**Purpose**: Update a record by ID

```python
async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
    """Update a record by ID."""
    stmt = (
        update(self.model)
        .where(self.model.id == id)
        .values(**kwargs)
        .returning(self.model)
    )
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.scalar_one_or_none()
```

**Example**:
```python
updated_session = await session_repo.update(
    session_id,
    status="completed",
    completed_at=datetime.utcnow()
)
```

#### delete(id: UUID)

**Purpose**: Hard delete a record

```python
async def delete(self, id: UUID) -> bool:
    """Hard delete a record by ID."""
    stmt = delete(self.model).where(self.model.id == id)
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.rowcount > 0
```

**Example**:
```python
deleted = await session_repo.delete(session_id)
if deleted:
    print("Session deleted successfully")
```

#### count(filters)

**Purpose**: Count records with optional filtering

```python
async def count(self, filters: Optional[List[Any]] = None) -> int:
    """Count records with optional filters."""
    query = select(func.count()).select_from(self.model)

    if filters:
        for filter_condition in filters:
            query = query.where(filter_condition)

    result = await self.db.execute(query)
    return result.scalar_one()
```

**Example**:
```python
active_count = await session_repo.count(
    filters=[SessionModel.status == "active"]
)
```

#### exists(id: UUID)

**Purpose**: Check if record exists

```python
async def exists(self, id: UUID) -> bool:
    """Check if record exists by ID."""
    query = select(func.count()).select_from(self.model).where(self.model.id == id)
    result = await self.db.execute(query)
    return result.scalar_one() > 0
```

---

## Specialized Repositories

All 13 specialized repositories extend BaseRepository with domain-specific queries.

### 1. SessionRepository

**Purpose**: Session data access operations

**File**: [app/repositories/session_repository.py](../../app/repositories/session_repository.py)

**Specialized Methods**:

#### get_by_user(user_id, skip, limit)

Get all sessions for a user (excluding soft-deleted):

```python
async def get_by_user(
    self,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[SessionModel]:
    result = await self.db.execute(
        select(SessionModel)
        .where(
            and_(
                SessionModel.user_id == user_id,
                SessionModel.deleted_at.is_(None)
            )
        )
        .order_by(SessionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### get_active_sessions(user_id)

Get all active sessions for a user:

```python
async def get_active_sessions(self, user_id: UUID) -> List[SessionModel]:
    result = await self.db.execute(
        select(SessionModel).where(
            and_(
                SessionModel.user_id == user_id,
                SessionModel.status.in_(['active', 'waiting', 'processing']),
                SessionModel.deleted_at.is_(None)
            )
        )
    )
    return list(result.scalars().all())
```

#### count_active_sessions(user_id)

Count active sessions for quota enforcement:

```python
async def count_active_sessions(self, user_id: UUID) -> int:
    result = await self.db.execute(
        select(func.count()).select_from(SessionModel).where(
            and_(
                SessionModel.user_id == user_id,
                SessionModel.status.in_(['active', 'waiting', 'processing']),
                SessionModel.deleted_at.is_(None)
            )
        )
    )
    return result.scalar_one()
```

#### get_by_status(status, skip, limit)

Get sessions by status:

```python
async def get_by_status(
    self,
    status: str,
    skip: int = 0,
    limit: int = 100,
) -> List[SessionModel]:
    result = await self.db.execute(
        select(SessionModel)
        .where(
            and_(
                SessionModel.status == status,
                SessionModel.deleted_at.is_(None)
            )
        )
        .order_by(SessionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### get_completed_before(cutoff_date, limit)

Get old completed sessions for archival:

```python
async def get_completed_before(
    self,
    cutoff_date: datetime,
    limit: int = 1000,
) -> List[SessionModel]:
    result = await self.db.execute(
        select(SessionModel)
        .where(
            and_(
                SessionModel.status.in_(['completed', 'failed', 'terminated']),
                SessionModel.completed_at < cutoff_date,
                SessionModel.deleted_at.is_(None)
            )
        )
        .order_by(SessionModel.completed_at)
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### soft_delete(session_id)

Soft delete a session:

```python
async def soft_delete(self, session_id: UUID) -> bool:
    stmt = (
        update(SessionModel)
        .where(SessionModel.id == session_id)
        .values(deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
    )
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.rowcount > 0
```

#### update_metrics(session_id, **metrics)

Update session metrics atomically:

```python
async def update_metrics(
    self,
    session_id: UUID,
    total_messages: Optional[int] = None,
    total_tool_calls: Optional[int] = None,
    total_cost_usd: Optional[float] = None,
    api_input_tokens: Optional[int] = None,
    api_output_tokens: Optional[int] = None,
    api_cache_creation_tokens: Optional[int] = None,
    api_cache_read_tokens: Optional[int] = None,
) -> bool:
    values = {"updated_at": datetime.utcnow()}

    if total_messages is not None:
        values["total_messages"] = total_messages
    if total_tool_calls is not None:
        values["total_tool_calls"] = total_tool_calls
    # ... additional metrics

    stmt = update(SessionModel).where(SessionModel.id == session_id).values(**values)
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.rowcount > 0
```

---

### 2. UserRepository

**Purpose**: User data access operations

**File**: [app/repositories/user_repository.py](../../app/repositories/user_repository.py)

**Specialized Methods**:

#### get_by_email(email)

```python
async def get_by_email(self, email: str) -> Optional[UserModel]:
    result = await self.db.execute(
        select(UserModel).where(
            and_(
                UserModel.email == email,
                UserModel.deleted_at.is_(None)
            )
        )
    )
    return result.scalar_one_or_none()
```

#### get_by_username(username)

```python
async def get_by_username(self, username: str) -> Optional[UserModel]:
    result = await self.db.execute(
        select(UserModel).where(
            and_(
                UserModel.username == username,
                UserModel.deleted_at.is_(None)
            )
        )
    )
    return result.scalar_one_or_none()
```

#### update_last_login(user_id)

```python
async def update_last_login(self, user_id: UUID) -> bool:
    stmt = (
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(
            last_login_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.rowcount > 0
```

#### email_exists(email) / username_exists(username)

Check uniqueness before registration:

```python
async def email_exists(self, email: str) -> bool:
    result = await self.db.execute(
        select(func.count())
        .select_from(UserModel)
        .where(
            and_(
                UserModel.email == email,
                UserModel.deleted_at.is_(None)
            )
        )
    )
    return result.scalar_one() > 0
```

---

### 3. MessageRepository

**Purpose**: Message data access operations

**File**: [app/repositories/message_repository.py](../../app/repositories/message_repository.py)

**Specialized Methods**:

#### get_by_session(session_id, skip, limit)

Get messages ordered by sequence:

```python
async def get_by_session(
    self,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[MessageModel]:
    result = await self.db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.sequence_number)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### get_next_sequence_number(session_id)

Get next sequence number for new message:

```python
async def get_next_sequence_number(self, session_id: UUID) -> int:
    result = await self.db.execute(
        select(MessageModel.sequence_number)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.sequence_number.desc())
        .limit(1)
    )
    last_sequence = result.scalar_one_or_none()
    return (last_sequence or 0) + 1
```

#### get_result_message(session_id)

Get the result message for a session:

```python
async def get_result_message(
    self,
    session_id: UUID,
) -> Optional[MessageModel]:
    result = await self.db.execute(
        select(MessageModel).where(
            and_(
                MessageModel.session_id == session_id,
                MessageModel.message_type == 'result'
            )
        ).order_by(MessageModel.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
```

---

### 4. ToolCallRepository

**Purpose**: Tool call data access operations

**File**: [app/repositories/tool_call_repository.py](../../app/repositories/tool_call_repository.py)

**Specialized Methods**:

#### get_by_tool_use_id(tool_use_id)

Get tool call by SDK tool_use_id:

```python
async def get_by_tool_use_id(self, tool_use_id: str) -> Optional[ToolCallModel]:
    result = await self.db.execute(
        select(ToolCallModel).where(ToolCallModel.tool_use_id == tool_use_id)
    )
    return result.scalar_one_or_none()
```

#### get_pending_for_permission(session_id)

Get pending tool calls awaiting permission:

```python
async def get_pending_for_permission(
    self,
    session_id: Optional[UUID] = None,
) -> List[ToolCallModel]:
    filters = [
        ToolCallModel.status == 'pending',
        ToolCallModel.permission_decision.is_(None)
    ]

    if session_id:
        filters.append(ToolCallModel.session_id == session_id)

    result = await self.db.execute(
        select(ToolCallModel)
        .where(and_(*filters))
        .order_by(ToolCallModel.created_at)
    )
    return list(result.scalars().all())
```

#### update_status(tool_call_id, status, error_message)

Update tool call status with timestamps:

```python
async def update_status(
    self,
    tool_call_id: UUID,
    status: str,
    error_message: Optional[str] = None,
) -> bool:
    values = {
        "status": status,
        "updated_at": datetime.utcnow()
    }

    if error_message:
        values["error_message"] = error_message
        values["is_error"] = True

    if status == 'running' and not error_message:
        values["started_at"] = datetime.utcnow()
    elif status in ['success', 'error']:
        values["completed_at"] = datetime.utcnow()

    stmt = update(ToolCallModel).where(ToolCallModel.id == tool_call_id).values(**values)
    result = await self.db.execute(stmt)
    await self.db.flush()
    return result.rowcount > 0
```

#### get_statistics_by_tool(session_id)

Get aggregated tool statistics:

```python
async def get_statistics_by_tool(
    self,
    session_id: Optional[UUID] = None,
) -> List[dict]:
    query = select(
        ToolCallModel.tool_name,
        func.count(ToolCallModel.id).label('total_calls'),
        func.count().filter(ToolCallModel.status == 'success').label('success_count'),
        func.count().filter(ToolCallModel.status == 'error').label('error_count'),
        func.avg(ToolCallModel.duration_ms).label('avg_duration_ms')
    ).group_by(ToolCallModel.tool_name)

    if session_id:
        query = query.where(ToolCallModel.session_id == session_id)

    result = await self.db.execute(query)
    rows = result.all()

    return [
        {
            "tool_name": row.tool_name,
            "total_calls": row.total_calls,
            "success_count": row.success_count,
            "error_count": row.error_count,
            "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms else None
        }
        for row in rows
    ]
```

---

### 5. TaskRepository

**Purpose**: Task template data access operations

**File**: [app/repositories/task_repository.py](../../app/repositories/task_repository.py)

**Specialized Methods**:

#### get_scheduled_tasks(enabled_only)

Get all scheduled tasks:

```python
async def get_scheduled_tasks(
    self,
    enabled_only: bool = True,
) -> List[TaskModel]:
    filters = [
        TaskModel.is_scheduled == True,
        TaskModel.is_deleted == False
    ]

    if enabled_only:
        filters.append(TaskModel.schedule_enabled == True)

    result = await self.db.execute(
        select(TaskModel).where(and_(*filters))
    )
    return list(result.scalars().all())
```

#### get_by_tags(tags, user_id, skip, limit)

Get tasks with any of the specified tags:

```python
async def get_by_tags(
    self,
    tags: List[str],
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[TaskModel]:
    filters = [
        TaskModel.tags.overlap(tags),  # Array overlap operator
        TaskModel.is_deleted == False
    ]

    if user_id:
        filters.append(TaskModel.user_id == user_id)

    result = await self.db.execute(
        select(TaskModel)
        .where(and_(*filters))
        .order_by(TaskModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

---

### 6. TaskExecutionRepository

**Purpose**: Task execution history operations

**File**: [app/repositories/task_execution_repository.py](../../app/repositories/task_execution_repository.py)

**Specialized Methods**:

#### get_execution_stats(task_id)

Get aggregated execution statistics:

```python
async def get_execution_stats(self, task_id: UUID) -> dict:
    result = await self.db.execute(
        select(
            func.count(TaskExecutionModel.id).label('total'),
            func.count().filter(TaskExecutionModel.status == 'completed').label('completed'),
            func.count().filter(TaskExecutionModel.status == 'failed').label('failed'),
            func.count().filter(TaskExecutionModel.status == 'cancelled').label('cancelled'),
            func.avg(TaskExecutionModel.duration_seconds).label('avg_duration')
        ).where(TaskExecutionModel.task_id == task_id)
    )

    row = result.first()

    return {
        "total": row.total or 0,
        "completed": row.completed or 0,
        "failed": row.failed or 0,
        "cancelled": row.cancelled or 0,
        "avg_duration_seconds": float(row.avg_duration) if row.avg_duration else None
    }
```

---

### 7. ReportRepository

**Purpose**: Report data access operations

**File**: [app/repositories/report_repository.py](../../app/repositories/report_repository.py)

**Specialized Methods**:

#### search_content(search_text, user_id, limit)

Search reports by content using JSONB operators:

```python
async def search_content(
    self,
    search_text: str,
    user_id: Optional[UUID] = None,
    limit: int = 50,
) -> List[ReportModel]:
    filters = [
        ReportModel.content.op('@>')(f'{{"text": "{search_text}"}}'),
        ReportModel.deleted_at.is_(None)
    ]

    if user_id:
        filters.append(ReportModel.user_id == user_id)

    result = await self.db.execute(
        select(ReportModel)
        .where(and_(*filters))
        .order_by(ReportModel.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
```

---

### 8. MCPServerRepository

**Purpose**: MCP server configuration operations

**File**: [app/repositories/mcp_server_repository.py](../../app/repositories/mcp_server_repository.py)

**Specialized Methods**:

#### list_by_user(user_id, include_global)

List MCP servers for user (including global):

```python
async def list_by_user(
    self,
    user_id: UUID,
    include_global: bool = True,
) -> List[MCPServerModel]:
    conditions = [MCPServerModel.deleted_at.is_(None)]

    if include_global:
        conditions.append(
            (MCPServerModel.user_id == user_id) |
            (MCPServerModel.user_id.is_(None))
        )
    else:
        conditions.append(MCPServerModel.user_id == user_id)

    query = select(MCPServerModel).where(and_(*conditions))
    result = await self.db.execute(query)
    return list(result.scalars().all())
```

---

### 9. SessionTemplateRepository

**Purpose**: Session template operations

**File**: [app/repositories/session_template_repository.py](../../app/repositories/session_template_repository.py)

**Specialized Methods**:

#### search_by_tags(tags, user_id, skip, limit)

Search templates using array overlap:

```python
async def search_by_tags(
    self,
    tags: List[str],
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[SessionTemplateModel]:
    conditions = [
        SessionTemplateModel.tags.bool_op("&&")(tags),  # Overlap operator
        SessionTemplateModel.deleted_at.is_(None)
    ]

    if user_id:
        conditions.append(
            or_(
                SessionTemplateModel.user_id == user_id,
                SessionTemplateModel.is_public == True,
                SessionTemplateModel.is_organization_shared == True,
            )
        )

    result = await self.db.execute(
        select(SessionTemplateModel)
        .where(and_(*conditions))
        .order_by(SessionTemplateModel.usage_count.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### update_usage_stats(template_id)

Increment usage counter:

```python
async def update_usage_stats(self, template_id: UUID) -> None:
    template = await self.db.get(SessionTemplateModel, template_id)
    if template:
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(template)
```

---

### 10. HookExecutionRepository

**Purpose**: Hook execution tracking operations

**File**: [app/repositories/hook_execution_repository.py](../../app/repositories/hook_execution_repository.py)

**Specialized Methods**:

#### get_by_tool_use_id(tool_use_id)

Get all hook executions for a tool use:

```python
async def get_by_tool_use_id(
    self,
    tool_use_id: str,
) -> List[HookExecutionModel]:
    result = await self.db.execute(
        select(HookExecutionModel)
        .where(HookExecutionModel.tool_use_id == tool_use_id)
        .order_by(HookExecutionModel.created_at)
    )
    return list(result.scalars().all())
```

---

### 11. PermissionDecisionRepository

**Purpose**: Permission decision tracking operations

**File**: [app/repositories/permission_decision_repository.py](../../app/repositories/permission_decision_repository.py)

**Specialized Methods**:

#### count_by_decision(session_id, decision)

Count decisions by type:

```python
async def count_by_decision(
    self,
    session_id: UUID,
    decision: str,
) -> int:
    result = await self.db.execute(
        select(func.count())
        .select_from(PermissionDecisionModel)
        .where(
            and_(
                PermissionDecisionModel.session_id == session_id,
                PermissionDecisionModel.decision == decision
            )
        )
    )
    return result.scalar_one()
```

---

### 12. WorkingDirectoryArchiveRepository

**Purpose**: Working directory archive operations

**File**: [app/repositories/working_directory_archive_repository.py](../../app/repositories/working_directory_archive_repository.py)

**Specialized Methods**:

#### get_pending_archives(limit)

Get archives waiting for processing:

```python
async def get_pending_archives(
    self,
    limit: int = 100,
) -> List[WorkingDirectoryArchiveModel]:
    result = await self.db.execute(
        select(WorkingDirectoryArchiveModel)
        .where(WorkingDirectoryArchiveModel.status == "pending")
        .order_by(WorkingDirectoryArchiveModel.created_at)
        .limit(limit)
    )
    return list(result.scalars().all())
```

---

### 13. SessionMetricsSnapshotRepository

**Purpose**: Session metrics snapshot operations

**File**: [app/repositories/session_metrics_snapshot_repository.py](../../app/repositories/session_metrics_snapshot_repository.py)

**Specialized Methods**:

#### get_snapshots_in_range(session_id, start_time, end_time)

Get snapshots within time range:

```python
async def get_snapshots_in_range(
    self,
    session_id: UUID,
    start_time: datetime,
    end_time: datetime,
) -> List[SessionMetricsSnapshotModel]:
    result = await self.db.execute(
        select(SessionMetricsSnapshotModel)
        .where(
            and_(
                SessionMetricsSnapshotModel.session_id == session_id,
                SessionMetricsSnapshotModel.created_at >= start_time,
                SessionMetricsSnapshotModel.created_at <= end_time
            )
        )
        .order_by(SessionMetricsSnapshotModel.created_at)
    )
    return list(result.scalars().all())
```

---

## Query Patterns

### Simple Queries

Get single record by ID:

```python
result = await db.execute(
    select(SessionModel).where(SessionModel.id == session_id)
)
session = result.scalar_one_or_none()
```

### Filtered Queries

Multiple conditions with AND:

```python
result = await db.execute(
    select(SessionModel).where(
        and_(
            SessionModel.user_id == user_id,
            SessionModel.status == "active",
            SessionModel.deleted_at.is_(None)
        )
    )
)
```

### IN Queries

Multiple possible values:

```python
result = await db.execute(
    select(SessionModel).where(
        SessionModel.status.in_(['active', 'waiting', 'processing'])
    )
)
```

### Joins and Relationships

Eager loading with selectinload:

```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(SessionModel)
    .options(selectinload(SessionModel.messages))
    .where(SessionModel.id == session_id)
)
session = result.scalar_one_or_none()
# session.messages are now loaded
```

### Aggregations

Count, sum, avg:

```python
result = await db.execute(
    select(
        func.count(ToolCallModel.id).label('total'),
        func.avg(ToolCallModel.duration_ms).label('avg_duration')
    ).where(ToolCallModel.session_id == session_id)
)
stats = result.first()
```

### Pagination

Offset and limit:

```python
result = await db.execute(
    select(SessionModel)
    .where(SessionModel.user_id == user_id)
    .order_by(SessionModel.created_at.desc())
    .offset(skip)
    .limit(limit)
)
sessions = list(result.scalars().all())
```

### JSONB Queries

Contains operator:

```python
# Find messages containing specific text
result = await db.execute(
    select(MessageModel).where(
        MessageModel.content.op('@>')(f'{{"text": "{search_text}"}}')
    )
)
```

Array overlap:

```python
# Find tasks with overlapping tags
result = await db.execute(
    select(TaskModel).where(
        TaskModel.tags.bool_op("&&")(['python', 'automation'])
    )
)
```

---

## Entity Conversion

### ORM Model to Domain Entity

Repositories typically return ORM models. Services convert them to domain entities:

```python
# In service layer
session_model = await session_repo.get_by_id(session_id)
if session_model:
    session_entity = Session.from_orm(session_model)
    return session_entity
```

### Domain Entity to ORM Model

When creating/updating, convert domain entities to ORM kwargs:

```python
# In service layer
session = Session(...)
session_model = await session_repo.create(
    user_id=session.user_id,
    name=session.name,
    mode=session.mode.value,  # Enum to string
    sdk_options=session.sdk_options,  # Dict to JSONB
    # ...
)
```

---

## Transaction Management

### Session Lifecycle

Repositories use the AsyncSession provided by dependency injection:

```python
from app.database.session import get_db

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Auto-rollback on error
            raise
        finally:
            await session.close()
```

### Service Layer Controls Transactions

Multiple repository calls share same transaction:

```python
async def create_session_with_message(
    session_data: dict,
    message_data: dict,
    db: AsyncSession
):
    # Both operations in same transaction
    session = await session_repo.create(**session_data)
    message_data["session_id"] = session.id
    message = await message_repo.create(**message_data)

    # Commit happens in get_db() after function returns
    return session, message
```

### Explicit Flush

Flush to get auto-generated IDs without committing:

```python
async def create(self, **kwargs) -> ModelType:
    instance = self.model(**kwargs)
    self.db.add(instance)
    await self.db.flush()  # Get ID without commit
    await self.db.refresh(instance)
    return instance
```

---

## Testing Repositories

### Mock Database Session

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.fixture
def mock_db():
    """Mock AsyncSession."""
    db = AsyncMock(spec=AsyncSession)
    return db

@pytest.mark.asyncio
async def test_get_by_id(mock_db):
    # Arrange
    session_id = uuid4()
    expected_session = SessionModel(id=session_id, name="Test")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_session
    mock_db.execute.return_value = mock_result

    repo = SessionRepository(mock_db)

    # Act
    result = await repo.get_by_id(session_id)

    # Assert
    assert result == expected_session
    mock_db.execute.assert_called_once()
```

### In-Memory SQLite for Integration Tests

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def test_db():
    """In-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()
```

---

## Best Practices

### DO

1. **Use repositories in services**: Never access database directly from API endpoints
2. **Keep repositories focused**: One repository per model
3. **Use type hints**: Strong typing prevents errors
4. **Handle None gracefully**: Check `scalar_one_or_none()` results
5. **Use filters parameter**: Reusable filtering logic
6. **Paginate large results**: Always use skip/limit
7. **Use async/await**: All database operations are async

### DON'T

1. **Don't put business logic in repositories**: Repositories are data access only
2. **Don't return partial data**: Always return complete ORM models
3. **Don't bypass repositories**: Services should never construct SQL directly
4. **Don't forget soft deletes**: Filter out deleted_at IS NOT NULL
5. **Don't leak database errors**: Catch and convert to domain exceptions
6. **Don't use blocking I/O**: No sync database calls

---

## Common Tasks

### Create Repository for New Model

```python
from app.repositories.base import BaseRepository
from app.models.my_model import MyModel

class MyModelRepository(BaseRepository[MyModel]):
    """Repository for MyModel operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(MyModel, db)

    async def get_by_custom_field(self, value: str) -> Optional[MyModel]:
        """Custom query method."""
        result = await self.db.execute(
            select(MyModel).where(MyModel.custom_field == value)
        )
        return result.scalar_one_or_none()
```

### Use in Service

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

async def get_my_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    repo = MyModelRepository(db)
    resource = await repo.get_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Not found")
    return resource
```

---

## Related Documentation

- **ORM Models**: [ORM_MODELS.md](ORM_MODELS.md) - Model definitions
- **Database Schema**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Schema reference
- **Base Repository**: [app/repositories/base.py](../../app/repositories/base.py)

---

## Keywords

`repository-pattern`, `data-access`, `crud`, `sqlalchemy`, `async`, `queries`, `filtering`, `pagination`, `joins`, `aggregations`, `transactions`, `type-safety`, `orm`, `database`, `abstraction`, `testing`, `mocking`, `soft-delete`, `jsonb-queries`, `array-queries`
