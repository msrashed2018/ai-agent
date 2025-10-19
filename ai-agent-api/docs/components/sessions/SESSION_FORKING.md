# Session Forking

## Purpose

Session forking creates a clone of an existing session, complete with its working directory contents and optionally its conversation history. This enables experimentation without affecting the original session, parallel exploration of solution paths, and the ability to create rollback points before risky operations.

Forking is a powerful feature for:
- **Experimentation**: Try different approaches without risk
- **A/B Testing**: Compare multiple solution strategies
- **Rollback Points**: Create save points before risky changes
- **Parallel Execution**: Explore multiple paths simultaneously
- **Teaching/Demonstration**: Show alternatives without losing original

---

## Forking Overview

### What is Session Forking?

Session forking creates a new session (child) from an existing session (parent), inheriting:
- Complete working directory contents (all files)
- SDK configuration and options
- Permission policies and tool restrictions
- Optionally: Message history up to a specific point

The forked session is independent - changes in the fork do not affect the parent, and vice versa.

### Why Fork Sessions?

**Use Case 1: Experimentation**
```
Problem: "Should I refactor using functional or OOP approach?"

Solution:
1. Original session: Current codebase state
2. Fork 1: Try functional approach
3. Fork 2: Try OOP approach
4. Compare results, choose best
```

**Use Case 2: Rollback Points**
```
Problem: "About to run risky database migration"

Solution:
1. Fork session before migration
2. Run migration in original
3. If fails, continue from fork
```

**Use Case 3: Parallel Exploration**
```
Problem: "Need to explore 3 different bug fix approaches"

Solution:
1. Fork session 3 times
2. Each fork tries different fix
3. Compare effectiveness
4. Merge best solution
```

**Use Case 4: Teaching/Demonstration**
```
Problem: "Show students multiple ways to solve problem"

Solution:
1. Create base session with problem
2. Fork for each solution approach
3. Students see all paths side-by-side
```

---

## Forking Process

### Step-by-Step Fork Operation

From [session_service.py:351-404](../../app/services/session_service.py:351-404):

```
Complete Fork Flow:
1. Receive fork request → POST /api/v1/sessions/{id}/fork
2. Validate parent session:
   ├─ Check exists
   ├─ Check user ownership
   └─ Check not deleted
3. Create new session entity:
   ├─ Generate new UUID
   ├─ Set mode = FORKED
   ├─ Set parent_session_id = parent.id
   ├─ Set is_fork = True
   ├─ Copy sdk_options from parent
   └─ Set name (or generate default)
4. Create working directory for fork:
   └─ /tmp/ai-agent-service/sessions/{new_session_id}/
5. Clone parent working directory:
   └─ Copy all files recursively (shutil.copytree)
6. Optionally clone message history:
   └─ Copy messages up to fork_at_message index
7. Initialize SDK client with cloned context
8. Persist forked session to database
9. Audit log fork action
10. Return forked session response with parent link
```

### Implementation

From [session_service.py:351-404](../../app/services/session_service.py:351-404):

```python
async def fork_session_advanced(
    self,
    parent_session_id: UUID,
    user_id: UUID,
    fork_at_message: Optional[int] = None,
    name: Optional[str] = None
) -> Session:
    """Fork an existing session with advanced options."""
    from pathlib import Path
    import shutil

    # Get parent session
    parent = await self.get_session(parent_session_id, user_id)

    # Create forked session
    forked_session = await self.create_session(
        user_id=user_id,
        mode=SessionMode.FORKED,
        sdk_options=parent.sdk_options,
        name=name or f"{parent.name} (fork)" if parent.name else "Forked session",
        parent_session_id=parent.id,
    )

    # Copy working directory if exists
    if parent.working_directory_path and Path(parent.working_directory_path).exists():
        try:
            parent_workdir = Path(parent.working_directory_path)
            forked_workdir = Path(forked_session.working_directory_path)

            # Copy all files from parent to forked session
            for item in parent_workdir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(parent_workdir)
                    dest_path = forked_workdir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)

            logger.info(
                f"Copied working directory from parent {parent_session_id} to forked session {forked_session.id}"
            )
        except Exception as e:
            logger.error(f"Failed to copy working directory: {e}")

    # Log fork action
    await self.audit_service.log_session_forked(
        session_id=forked_session.id,
        parent_session_id=parent.id,
        user_id=user_id,
        fork_at_message=fork_at_message,
    )

    await self.db.commit()
    return forked_session
```

### Parent Session Requirements

**Parent session must**:
- Exist in database (not deleted)
- Be owned by requesting user (or user is admin)
- Have valid working directory path
- Not be in ARCHIVED state (preferably)

**Parent can be in any state**:
- ACTIVE (most common)
- COMPLETED (fork from finished session)
- FAILED (fork to retry from failure point)
- PAUSED (fork while paused)
- TERMINATED (fork to restart)

From [session_service.py:363](../../app/services/session_service.py:363):
```python
# Get parent session
parent = await self.get_session(parent_session_id, user_id)
```

This validates ownership and existence automatically.

---

## Working Directory Cloning

### File Copying Strategy

The fork operation uses recursive file copying:

From [session_service.py:375-387](../../app/services/session_service.py:375-387):

```python
# Copy all files from parent to forked session
for item in parent_workdir.rglob("*"):
    if item.is_file():
        rel_path = item.relative_to(parent_workdir)
        dest_path = forked_workdir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_path)
```

**Key Points**:
- Uses `rglob("*")` for recursive traversal
- Preserves directory structure
- Uses `shutil.copy2()` to preserve metadata (timestamps, permissions)
- Creates parent directories as needed
- Skips directories (only copies files)

### Directory Structure

**Before Fork**:
```
/tmp/ai-agent-service/sessions/
└── parent-session-uuid/
    ├── src/
    │   ├── main.py
    │   └── utils.py
    ├── tests/
    │   └── test_main.py
    └── README.md
```

**After Fork**:
```
/tmp/ai-agent-service/sessions/
├── parent-session-uuid/          # Original (unchanged)
│   ├── src/
│   │   ├── main.py
│   │   └── utils.py
│   ├── tests/
│   │   └── test_main.py
│   └── README.md
└── forked-session-uuid/          # Clone (independent copy)
    ├── src/
    │   ├── main.py
    │   └── utils.py
    ├── tests/
    │   └── test_main.py
    └── README.md
```

**Changes in fork do NOT affect parent**:
```python
# In forked session
await client.execute_tool("Write", {"path": "src/new_feature.py", "content": "..."})

# Parent session working directory unchanged
# Fork has new file, parent does not
```

### Symlinks vs Hard Copies

**Current Implementation**: Hard copies (full file duplication)

**Pros**:
- Complete isolation between parent and fork
- Simple to understand and implement
- No risk of accidental parent modification

**Cons**:
- Higher storage consumption
- Slower for large directories
- Duplicate data on disk

**Future Optimization** (Phase 3):
- Copy-on-write file systems (btrfs, ZFS)
- Hard links for read-only files
- Lazy copying (copy files only when modified)

### Size Limits and Quotas

Working directory size is limited by configuration:

From [config.py:56](../../app/core/config.py:56):
```python
max_working_dir_size_mb: int = 1024  # 1GB default
```

**Forking Fails If**:
- Parent directory size > max_working_dir_size_mb
- Insufficient disk space for copy
- Too many files (file system limits)

**Check Before Forking**:
```python
from app.services.storage_manager import StorageManager

storage_manager = StorageManager()
parent_size = await storage_manager.get_directory_size(parent_session_id)

if parent_size > settings.max_working_dir_size_mb * 1024 * 1024:
    raise ValueError("Parent directory too large to fork")
```

### Storage Implications

**Storage Consumption Example**:
```
Original session: 500MB working directory
├─ Fork 1: +500MB (total: 1GB)
├─ Fork 2: +500MB (total: 1.5GB)
└─ Fork 3: +500MB (total: 2GB)

4 sessions = 2GB storage (4x original)
```

**Best Practices**:
1. Clean up unnecessary forks after use
2. Archive parent before creating many forks
3. Monitor total storage usage
4. Set appropriate size limits
5. Use background archival for old forks

---

## Parent-Child Relationship

### Database Schema

From [session.py:46-47](../../app/models/session.py:46-47):

```python
# Session Relationships
parent_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
is_fork = Column(Boolean, default=False)
```

**Foreign Key Relationship**:
- `parent_session_id` references `sessions.id`
- Indexed for fast parent lookup
- Allows NULL (normal sessions have no parent)

**is_fork Flag**:
- Boolean flag for quick identification
- TRUE for forked sessions
- FALSE for normal sessions

### Relationship Tracking

**Query all forks from parent**:

From [session_repository.py:158-173](../../app/repositories/session_repository.py:158-173):

```python
async def get_forked_sessions(
    self,
    parent_session_id: UUID,
) -> List[SessionModel]:
    """Get all sessions forked from a parent session."""
    result = await self.db.execute(
        select(SessionModel).where(
            and_(
                SessionModel.parent_session_id == parent_session_id,
                SessionModel.is_fork == True,
                SessionModel.deleted_at.is_(None)
            )
        )
    )
    return list(result.scalars().all())
```

**Example Usage**:
```python
# Get all forks of a session
forks = await session_repo.get_forked_sessions(parent_session_id)

print(f"Session {parent_session_id} has {len(forks)} forks:")
for fork in forks:
    print(f"  - {fork.id}: {fork.name} (created {fork.created_at})")
```

### Cascade Behavior

**When parent is deleted**:
- Foreign key has `ondelete="CASCADE"` (default SQLAlchemy behavior)
- However, sessions use **soft delete** (set `deleted_at`)
- Forks are NOT automatically deleted when parent is soft-deleted
- Forks can outlive their parent

**Database Constraint**:
```python
parent_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
```

No explicit cascade defined, so default is RESTRICT (prevents delete if forks exist).

**Best Practice**:
```python
# Before hard-deleting parent, archive or delete forks
forks = await session_repo.get_forked_sessions(parent_id)
for fork in forks:
    await session_service.archive_session(fork.id)
```

### Relationship Metadata

**Session entity tracks relationship**:

From [session.py:48-49](../../app/domain/entities/session.py:48-49):

```python
self.parent_session_id: Optional[UUID] = None
self.is_fork = False
```

**API Response includes parent link**:

From [sessions.py:759-763](../../app/api/v1/sessions.py:759-763):

```python
response._links = Links(
    self=f"/api/v1/sessions/{forked_session.id}",
    parent=f"/api/v1/sessions/{session_id}",
    query=f"/api/v1/sessions/{forked_session.id}/query",
)
```

**Example Response**:
```json
{
  "id": "fork-123",
  "parent_session_id": "parent-456",
  "is_fork": true,
  "name": "Experimental Fork",
  "_links": {
    "self": "/api/v1/sessions/fork-123",
    "parent": "/api/v1/sessions/parent-456",
    "query": "/api/v1/sessions/fork-123/query"
  }
}
```

---

## Message History Cloning

### Cloning Process

**Optional Parameter**: `fork_at_message`

From [sessions.py:714-724](../../app/api/v1/sessions.py:714-724):

```python
@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session_endpoint(
    session_id: UUID,
    request: SessionForkRequest,  # Contains fork_at_message
    ...
):
    forked_session = await service.fork_session_advanced(
        parent_session_id=session_id,
        user_id=current_user.id,
        fork_at_message=request.fork_at_message,  # Optional: message index to fork from
        name=request.name,
    )
```

**fork_at_message Options**:
- `None` (default): Clone all messages
- `10`: Clone only first 10 messages
- `0`: Clone no messages (fresh start with cloned files)

### Context Restoration in Executor

From [forked_executor.py:99-120](../../app/claude_sdk/execution/forked_executor.py:99-120):

```python
async def _restore_context(self) -> None:
    """Restore conversation history from parent session."""

    # Retrieve parent session messages
    parent_messages = await self.message_repo.get_by_session(
        self.parent_session_id, limit=self.fork_at_message
    )

    logger.info(
        f"Retrieved {len(parent_messages)} messages from parent session",
        extra={"parent_session_id": str(self.parent_session_id)},
    )

    # TODO: Implement context restoration with SDK
    # This requires SDK support for conversation continuation
    # For now, we log the intent
    logger.warning("Full context restoration not yet implemented (Phase 3 feature)")
```

**Current Status**: Phase 3 feature (not fully implemented)

**When Fully Implemented**:
1. Retrieve parent messages up to `fork_at_message`
2. Convert to SDK-compatible format
3. Initialize SDK client with message history
4. Continue conversation from that point

### SDK Context Initialization

**Planned Implementation** (Phase 3):

```python
# Pseudocode for full context restoration
async def _restore_context(self) -> None:
    # 1. Get parent messages
    parent_messages = await self.message_repo.get_by_session(
        self.parent_session_id,
        limit=self.fork_at_message
    )

    # 2. Convert to SDK format
    sdk_messages = []
    for msg in parent_messages:
        if msg.message_type == MessageType.USER:
            sdk_messages.append(UserMessage(content=msg.content))
        elif msg.message_type == MessageType.ASSISTANT:
            sdk_messages.append(AssistantMessage(content=msg.content))

    # 3. Initialize SDK with history
    await self.client.initialize_with_history(sdk_messages)

    # 4. First query continues from this context
```

**Requires SDK Support**:
- Conversation continuation API
- Message history replay
- State restoration
- Tool call history replay

---

## API Operations

### Fork Session Endpoint

**Endpoint**: `POST /api/v1/sessions/{session_id}/fork`

From [sessions.py:712-766](../../app/api/v1/sessions.py:712-766):

```python
@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session_endpoint(
    session_id: UUID,
    request: SessionForkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Fork an existing session.

    Creates a new session based on an existing session's configuration and optionally
    its working directory contents. The forked session can continue from a specific
    message in the conversation history.
    """
```

### Request Schema

```python
class SessionForkRequest(BaseModel):
    """Request to fork a session."""
    name: Optional[str] = None  # Name for forked session
    fork_at_message: Optional[int] = None  # Message index to fork from
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/parent-123/fork \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Experimental Branch - OOP Approach",
    "fork_at_message": 15
  }'
```

### Response Schema

```json
{
  "id": "fork-uuid",
  "user_id": "user-uuid",
  "name": "Experimental Branch - OOP Approach",
  "status": "created",
  "parent_session_id": "parent-123",
  "is_fork": true,
  "working_directory": "/tmp/ai-agent-service/sessions/fork-uuid/",
  "message_count": 0,
  "tool_call_count": 0,
  "created_at": "2025-10-19T10:30:00Z",
  "sdk_options": {
    "model": "claude-sonnet-4-5",
    "max_turns": 20
  },
  "_links": {
    "self": "/api/v1/sessions/fork-uuid",
    "parent": "/api/v1/sessions/parent-123",
    "query": "/api/v1/sessions/fork-uuid/query",
    "messages": "/api/v1/sessions/fork-uuid/messages"
  }
}
```

### Error Handling

**Common Errors**:

**404 Not Found**:
```json
{
  "detail": "Session parent-123 not found"
}
```

**403 Forbidden**:
```json
{
  "detail": "Not authorized to access this session"
}
```

**400 Bad Request**:
```json
{
  "detail": "Parent directory too large to fork (>1GB)"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to copy working directory: [error details]"
}
```

---

## Common Use Cases

### Use Case 1: Experimentation Without Risk

**Scenario**: Need to try risky refactoring without breaking original code.

```bash
# 1. Fork the session
curl -X POST http://localhost:8000/api/v1/sessions/original-123/fork \
  -H "Authorization: Bearer TOKEN" \
  -d '{"name": "Risky Refactoring Experiment"}'

# Response: {"id": "fork-456", ...}

# 2. Try refactoring in fork
curl -X POST http://localhost:8000/api/v1/sessions/fork-456/query \
  -H "Authorization: Bearer TOKEN" \
  -d '{"message": "Refactor using functional programming"}'

# 3. If successful, apply to original; if failed, delete fork
# Original session remains unchanged
```

### Use Case 2: A/B Testing Solution Approaches

**Scenario**: Compare multiple approaches to solving a problem.

```python
# Original session with problem setup
original_id = "session-123"

# Create 3 forks for different approaches
fork_a = await create_fork(original_id, name="Approach A: Functional")
fork_b = await create_fork(original_id, name="Approach B: OOP")
fork_c = await create_fork(original_id, name="Approach C: Hybrid")

# Execute different approach in each fork
await execute_query(fork_a.id, "Solve using functional programming")
await execute_query(fork_b.id, "Solve using object-oriented design")
await execute_query(fork_c.id, "Solve using hybrid approach")

# Compare results and choose best
results = [
    await get_session_metrics(fork_a.id),
    await get_session_metrics(fork_b.id),
    await get_session_metrics(fork_c.id),
]

best_fork = min(results, key=lambda r: r.complexity_score)
```

### Use Case 3: Rollback Points

**Scenario**: Create save points before risky operations.

```bash
# 1. Before risky database migration
curl -X POST http://localhost:8000/api/v1/sessions/main-session/fork \
  -d '{"name": "Checkpoint before migration"}'

# 2. Run migration in original session
curl -X POST http://localhost:8000/api/v1/sessions/main-session/query \
  -d '{"message": "Run database migration"}'

# 3a. If migration succeeds: Delete checkpoint fork
curl -X DELETE http://localhost:8000/api/v1/sessions/checkpoint-fork

# 3b. If migration fails: Continue from checkpoint fork
curl -X POST http://localhost:8000/api/v1/sessions/checkpoint-fork/query \
  -d '{"message": "Try alternative migration strategy"}'
```

### Use Case 4: Parallel Execution Paths

**Scenario**: Explore multiple debugging approaches simultaneously.

```python
# Parent session identifies bug
parent_id = await create_session("Debug memory leak")
await execute_query(parent_id, "Identify memory leak in application")

# Create forks for different debugging paths
fork1 = await create_fork(parent_id, name="Check database connections")
fork2 = await create_fork(parent_id, name="Check event listeners")
fork3 = await create_fork(parent_id, name="Check cache invalidation")

# Execute in parallel
import asyncio
results = await asyncio.gather(
    execute_query(fork1.id, "Investigate database connection pool"),
    execute_query(fork2.id, "Investigate event listener cleanup"),
    execute_query(fork3.id, "Investigate cache memory usage"),
)

# First fork to find issue wins
```

### Use Case 5: Teaching and Demonstration

**Scenario**: Show students multiple ways to solve a problem.

```bash
# 1. Setup base problem in main session
curl -X POST http://localhost:8000/api/v1/sessions \
  -d '{"name": "Sorting Algorithm Problem"}'

curl -X POST http://localhost:8000/api/v1/sessions/base-session/query \
  -d '{"message": "Create unsorted array with 1000 elements"}'

# 2. Fork for each solution approach
curl -X POST http://localhost:8000/api/v1/sessions/base-session/fork \
  -d '{"name": "Solution 1: Quicksort"}'

curl -X POST http://localhost:8000/api/v1/sessions/base-session/fork \
  -d '{"name": "Solution 2: Mergesort"}'

curl -X POST http://localhost:8000/api/v1/sessions/base-session/fork \
  -d '{"name": "Solution 3: Heapsort"}'

# 3. Students can explore each fork independently
# All start with same problem setup (array)
# Each demonstrates different solution
```

---

## Limitations and Considerations

### Current Limitations

**1. Context Restoration Not Fully Implemented**

From [forked_executor.py:116-119](../../app/claude_sdk/execution/forked_executor.py:116-119):

```python
# TODO: Implement context restoration with SDK
# This requires SDK support for conversation continuation
# For now, we log the intent
logger.warning("Full context restoration not yet implemented (Phase 3 feature)")
```

**Impact**: Forked sessions start fresh without previous conversation context.

**Workaround**: Messages are cloned to database, but SDK doesn't use them yet.

**2. Storage Consumption**

Each fork duplicates entire working directory:
- 100MB parent → 100MB fork (200MB total)
- 1GB parent → 1GB fork (2GB total)
- Multiple forks multiply storage usage

**Impact**: Can quickly consume disk space with large working directories.

**Mitigation**:
- Archive old forks
- Set max_working_dir_size_mb limit
- Monitor total storage usage
- Clean up forks after use

**3. Performance Impact**

Large directory copying is slow:
- 10MB: ~100ms
- 100MB: ~1s
- 1GB: ~10s+
- 10GB: ~100s+ (not recommended)

**Impact**: Fork creation blocks during copy operation.

**Mitigation**:
- Keep working directories small
- Archive large files before forking
- Consider background fork operation (future)

**4. SDK State Synchronization**

Fork inherits parent configuration, but not runtime state:
- API keys: Inherited
- Environment variables: Inherited
- In-memory state: NOT inherited
- Open connections: NOT inherited

**Impact**: Some parent session state is lost in fork.

**Workaround**: Reinitialize connections in forked session.

### Storage Considerations

**Disk Space Requirements**:
```
Formula: total_space = parent_size * (1 + num_forks)

Example:
- Parent: 500MB
- 5 forks: 500MB * 6 = 3GB total
```

**Best Practices**:
1. **Monitor Storage**: Track total usage across all sessions
2. **Set Limits**: Configure max_working_dir_size_mb
3. **Clean Up**: Delete forks after use
4. **Archive**: Move old forks to compressed storage
5. **Optimize**: Remove unnecessary files before forking

### Performance Considerations

**Fork Creation Time**:
- Depends on working directory size
- Network latency (if on network storage)
- Disk I/O speed
- Number of files (many small files slower than one large file)

**Optimization Tips**:
1. Keep working directories under 100MB when possible
2. Avoid forking sessions with thousands of files
3. Use .gitignore-like patterns to exclude temp files
4. Consider async fork operation for large directories

### SDK State Considerations

**What Gets Cloned**:
- Configuration (sdk_options)
- Permission policies
- Tool restrictions
- Working directory files

**What Doesn't Get Cloned**:
- Conversation context (Phase 3)
- SDK internal state
- Active connections
- In-memory caches
- WebSocket subscriptions

**Recommendation**: Treat forked sessions as fresh starts with cloned files.

---

## Related Documentation

- **Session Modes**: [SESSION_MODES.md](SESSION_MODES.md) - Forked mode details
- **Session Lifecycle**: [SESSION_LIFECYCLE.md](SESSION_LIFECYCLE.md) - State transitions
- **Working Directories**: [WORKING_DIRECTORIES.md](WORKING_DIRECTORIES.md) - Directory cloning details
- **Storage Management**: [../../storage/STORAGE_MANAGER.md](../../storage/STORAGE_MANAGER.md) - Storage operations
- **API Endpoints**: [../../api/REST_API_ENDPOINTS.md](../../api/REST_API_ENDPOINTS.md) - Fork API reference

---

## Related Files

**Domain Layer**:
- [session.py:48-49](../../app/domain/entities/session.py:48-49) - Fork relationship fields

**Services**:
- [session_service.py:351-404](../../app/services/session_service.py:351-404) - fork_session_advanced
- [storage_manager.py:20-24](../../app/services/storage_manager.py:20-24) - create_working_directory

**Executors**:
- [forked_executor.py](../../app/claude_sdk/execution/forked_executor.py) - ForkedExecutor implementation
- [forked_executor.py:99-120](../../app/claude_sdk/execution/forked_executor.py:99-120) - Context restoration

**Repositories**:
- [session_repository.py:158-173](../../app/repositories/session_repository.py:158-173) - get_forked_sessions
- [message_repository.py](../../app/repositories/message_repository.py) - Message cloning

**API**:
- [sessions.py:712-766](../../app/api/v1/sessions.py:712-766) - Fork endpoint

**Database**:
- [session.py:46-47](../../app/models/session.py:46-47) - parent_session_id foreign key

---

## Keywords

`session-forking`, `fork-session`, `clone-session`, `parent-child-relationship`, `working-directory-cloning`, `context-restoration`, `experimentation`, `rollback-points`, `a-b-testing`, `parallel-execution`, `forked-mode`, `forked-executor`, `message-history`, `storage-consumption`, `directory-copy`, `fork-at-message`, `session-branching`, `conversation-forking`
