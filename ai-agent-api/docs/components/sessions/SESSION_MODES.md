# Session Execution Modes

## Purpose

Session execution modes determine how Claude Code agent sessions execute queries and interact with users. The AI-Agent-API supports three distinct execution modes, each optimized for specific use cases:

- **INTERACTIVE**: Real-time chat-like interaction with streaming responses for UI applications
- **NON_INTERACTIVE** (Background): Asynchronous task execution without streaming for automation and batch processing
- **FORKED**: Cloned sessions that inherit context from parent sessions for experimentation and parallel execution

Understanding these modes is critical for choosing the right approach for your application architecture. Interactive mode provides ChatGPT-like real-time streaming, background mode optimizes for reliability and throughput, and forked mode enables branching conversation paths.

---

## Session Mode Enum

**Implementation**: [session.py:22-26](../../app/domain/entities/session.py:22-26)

```python
class SessionMode(str, Enum):
    """Session mode enumeration."""
    INTERACTIVE = "interactive"
    NON_INTERACTIVE = "non_interactive"
    FORKED = "forked"
```

Modes are stored in the database as strings but validated against this enum in the domain layer.

---

## INTERACTIVE Mode

### Overview

Interactive mode provides real-time, streaming chat-like experience similar to ChatGPT or Claude.ai. This is the default mode for user-facing applications that require immediate visual feedback.

**Key Characteristics**:
- Real-time message streaming with partial updates
- WebSocket support for live UI updates
- Streaming token-by-token responses
- User can see Claude "thinking" in real-time
- Optimized for low perceived latency

**Implementation**: [interactive_executor.py](../../app/claude_sdk/execution/interactive_executor.py)

### How Interactive Mode Works

```
User Query Flow (Interactive):
1. Client → POST /api/v1/sessions/{id}/query
2. Session status: ACTIVE → PROCESSING
3. InteractiveExecutor created via ExecutorFactory
4. Claude SDK client with include_partial_messages=True
5. Query sent to Claude API
6. Stream responses as they arrive:
   ├─ StreamEvent (partial text) → WebSocket broadcast
   ├─ AssistantMessage (complete) → Save to database
   └─ ResultMessage (final metrics) → Update session stats
7. Session status: PROCESSING → ACTIVE
8. Return final response to client
```

### Implementation Details

From [interactive_executor.py:57-111](../../app/claude_sdk/execution/interactive_executor.py:57-111):

```python
async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
    """Execute query and stream responses in real-time."""
    logger.info(
        f"InteractiveExecutor executing query with streaming",
        extra={"session_id": str(self.session.id)},
    )

    try:
        # Enable partial messages for streaming
        self.client.config.include_partial_messages = True

        # Send query
        await self.client.query(prompt)

        # Stream responses
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                # Process and persist assistant message
                domain_message = await self.message_handler.handle_assistant_message(
                    message, self.session.id
                )

                # Broadcast to WebSocket if available
                if self.event_broadcaster:
                    await self.event_broadcaster.broadcast(
                        session_id=self.session.id,
                        event_type="message",
                        data={"message": domain_message},
                    )

                yield domain_message

            elif isinstance(message, StreamEvent):
                # Handle streaming event for partial updates
                await self.stream_handler.handle_stream_event(message, self.session.id)

            elif isinstance(message, ResultMessage):
                # Process final result and metrics
                await self.result_handler.handle_result_message(message, self.session.id)
                break

    except Exception as e:
        await self._handle_error(e, {"prompt": prompt})
        raise
```

### WebSocket Integration

Interactive mode integrates with WebSocket broadcasting via the `EventBroadcaster`:

From [interactive_executor.py:40-41](../../app/claude_sdk/execution/interactive_executor.py:40-41):
```python
def __init__(
    self,
    session: Session,
    client: EnhancedClaudeClient,
    message_handler: MessageHandler,
    stream_handler: StreamHandler,
    result_handler: ResultHandler,
    error_handler: ErrorHandler,
    event_broadcaster: Optional[Any] = None,
):
```

The `event_broadcaster` pushes real-time updates to connected WebSocket clients, enabling live UI updates without polling.

### Use Cases

**Interactive Mode is ideal for**:
- Web-based chat UIs (React, Vue, etc.)
- Real-time collaborative coding tools
- Interactive debugging and troubleshooting sessions
- Live demonstrations and presentations
- Any scenario requiring immediate visual feedback

**NOT recommended for**:
- Background batch processing
- Scheduled automation tasks
- High-throughput API endpoints
- Server-to-server communication

### API Usage

**Creating Interactive Session**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chat Session",
    "mode": "interactive",
    "sdk_options": {
      "model": "claude-sonnet-4-5",
      "max_turns": 20
    }
  }'
```

**Sending Query with Streaming**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{id}/query \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain async/await in Python"
  }'
```

The response streams back as messages arrive, providing real-time feedback.

### Configuration

From [executor_factory.py:145-160](../../app/claude_sdk/execution/executor_factory.py:145-160):

```python
client_config = ClientConfig(
    session_id=session.id,
    model=session.sdk_options.get("model", "claude-sonnet-4-5"),
    permission_mode=session.permission_mode or "default",
    max_turns=session.sdk_options.get("max_turns", 10),
    max_retries=session.max_retries or 3,
    retry_delay=session.retry_delay or 2.0,
    timeout_seconds=session.timeout_seconds or 120,
    include_partial_messages=session.include_partial_messages or False,  # TRUE for interactive
    working_directory=Path(session.working_directory_path),
    allowed_tools=session.sdk_options.get("allowed_tools"),
    hooks=hooks_dict,
    can_use_tool=permission_callback,
)
```

**Key Settings for Interactive Mode**:
- `include_partial_messages`: **TRUE** (enables streaming)
- `timeout_seconds`: 120s (default, can be higher for complex queries)
- `max_turns`: 20 (default conversation turns)

---

## NON_INTERACTIVE (Background) Mode

### Overview

Background mode (NON_INTERACTIVE) executes tasks asynchronously without streaming, optimized for automation, batch processing, and high-throughput scenarios. This mode prioritizes reliability and performance over real-time feedback.

**Key Characteristics**:
- No streaming (better performance)
- Built-in retry logic for transient failures
- Returns final result with complete metrics
- Lower overhead than interactive mode
- Suitable for API-driven automation

**Implementation**: [background_executor.py](../../app/claude_sdk/execution/background_executor.py)

### How Background Mode Works

```
Background Execution Flow:
1. Scheduled Task / API Call → Execute query
2. BackgroundExecutor created via ExecutorFactory
3. Claude SDK client with include_partial_messages=False
4. Query sent to Claude API (no streaming)
5. Wait for complete response
6. Retry on failure (configurable retries)
7. Process final result:
   ├─ Save messages to database
   ├─ Update session metrics
   └─ Return ExecutionResult
8. Optionally trigger completion webhook/notification
```

### Implementation Details

From [background_executor.py:74-116](../../app/claude_sdk/execution/background_executor.py:74-116):

```python
async def execute(self, prompt: str) -> ExecutionResult:
    """Execute task and return final result (no streaming)."""
    logger.info(
        f"BackgroundExecutor executing query (no streaming)",
        extra={"session_id": str(self.session.id)},
    )

    try:
        # Disable partial messages for background execution
        self.client.config.include_partial_messages = False

        # Execute with retry logic
        await self.retry_manager.execute_with_retry(self._execute_query, prompt)

        # Get final metrics
        metrics = await self.client.get_metrics()

        return ExecutionResult(
            session_id=self.session.id,
            success=True,
            data={"status": "completed"},
            error_message=None,
            metrics=metrics,
        )

    except Exception as e:
        await self._handle_error(e, {"prompt": prompt})

        return ExecutionResult(
            session_id=self.session.id,
            success=False,
            data=None,
            error_message=str(e),
            metrics=await self.client.get_metrics(),
        )
```

### Retry Logic

Background executor includes automatic retry for transient failures:

From [background_executor.py:51-73](../../app/claude_sdk/execution/background_executor.py:51-73):

```python
def __init__(
    self,
    session: Session,
    client: EnhancedClaudeClient,
    message_handler: MessageHandler,
    result_handler: ResultHandler,
    error_handler: ErrorHandler,
    retry_manager: RetryManager,  # Retry support
):
```

**Retry Configuration** (from [executor_factory.py:190-194](../../app/claude_sdk/execution/executor_factory.py:190-194)):
```python
retry_policy = RetryPolicy(
    max_retries=session.max_retries or 3,
    base_delay=session.retry_delay or 2.0,
)
retry_manager = RetryManager(retry_policy)
```

**Retry Behavior**:
- Max retries: 3 (configurable via `session.max_retries`)
- Base delay: 2 seconds (configurable via `session.retry_delay`)
- Exponential backoff for subsequent retries
- Only retries transient errors (network, timeout)

### Execution Result

Background mode returns structured `ExecutionResult` with complete metrics:

From [background_executor.py:21-38](../../app/claude_sdk/execution/background_executor.py:21-38):

```python
@dataclass
class ExecutionResult:
    """Background execution result with metrics."""

    session_id: UUID
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metrics: ClientMetrics
```

**Metrics include**:
- Total API calls made
- Input/output token counts
- Cache hit/miss statistics
- Total execution time
- Cost estimates (USD)

### Use Cases

**Background Mode is ideal for**:
- Scheduled batch processing (Celery tasks)
- Automated code reviews and analysis
- Recurring data transformation pipelines
- Server-to-server API integration
- High-volume content generation
- Asynchronous report generation

**NOT recommended for**:
- Interactive user-facing UIs
- Real-time chat applications
- Scenarios requiring immediate visual feedback

### API Usage

**Creating Background Session**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Batch Processing Session",
    "mode": "non_interactive",
    "sdk_options": {
      "model": "claude-sonnet-4-5",
      "max_retries": 5,
      "retry_delay": 3.0
    }
  }'
```

**Executing Background Query**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{id}/query \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this codebase and generate a report"
  }'
```

The response returns only after complete execution (no streaming).

### Configuration

**Key Settings for Background Mode**:
- `include_partial_messages`: **FALSE** (no streaming)
- `max_retries`: 3-5 (higher for reliability)
- `retry_delay`: 2-5 seconds
- `timeout_seconds`: 300+ (longer for complex tasks)

Environment variables (from [config.py:102-107](../../app/core/config.py:102-107)):
```python
# Phase 4: Claude SDK Settings
claude_sdk_default_model: str = "claude-sonnet-4-5"
claude_sdk_max_retries: int = 3
claude_sdk_retry_delay: float = 2.0
claude_sdk_timeout_seconds: int = 120
```

### Performance Characteristics

| Metric | Interactive | Background |
|--------|-------------|------------|
| Overhead | Higher (streaming) | Lower (batch) |
| Latency | Lower (perceived) | Higher (actual) |
| Throughput | Lower | **Higher** |
| Reliability | Moderate | **Higher** (retries) |
| Resource Usage | Higher (WebSocket) | Lower |

---

## FORKED Mode

### Overview

Forked mode creates a new session cloned from a parent session, inheriting working directory contents and optionally restoring conversation history. This enables experimentation without affecting the original session.

**Key Characteristics**:
- Clones parent session's working directory
- Optionally restores message history
- Maintains parent-child relationship tracking
- Useful for A/B testing different approaches
- Can fork from specific conversation point

**Implementation**: [forked_executor.py](../../app/claude_sdk/execution/forked_executor.py)

### How Forked Mode Works

```
Session Fork Flow:
1. Client → POST /api/v1/sessions/{parent_id}/fork
2. Retrieve parent session and validate state
3. Create new forked session:
   ├─ mode = FORKED
   ├─ parent_session_id = parent.id
   └─ is_fork = True
4. Clone working directory:
   └─ shutil.copytree(parent_workdir, forked_workdir)
5. Optionally clone message history:
   └─ Copy messages up to fork_at_message index
6. Initialize SDK client with cloned context
7. ForkedExecutor ready for queries
8. Return forked session response
```

### Implementation Details

From [forked_executor.py:60-98](../../app/claude_sdk/execution/forked_executor.py:60-98):

```python
async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
    """Execute in forked session with restored context."""
    logger.info(
        f"ForkedExecutor executing query (parent={self.parent_session_id}, fork_at={self.fork_at_message})",
        extra={"session_id": str(self.session.id), "parent_session_id": str(self.parent_session_id)},
    )

    try:
        # Restore context from parent session
        await self._restore_context()

        # Continue conversation (same as interactive executor)
        await self.client.query(prompt)

        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                domain_message = await self.message_handler.handle_assistant_message(
                    message, self.session.id
                )
                yield domain_message

            elif isinstance(message, ResultMessage):
                await self.result_handler.handle_result_message(message, self.session.id)
                break

    except Exception as e:
        await self._handle_error(e, {"prompt": prompt, "parent_session_id": str(self.parent_session_id)})
        raise
```

### Context Restoration

From [forked_executor.py:99-120](../../app/claude_sdk/execution/forked_executor.py:99-120):

```python
async def _restore_context(self) -> None:
    """Restore conversation history from parent session.

    This method retrieves parent messages and prepares context
    for the forked session. Full implementation depends on SDK
    support for session continuation (planned for Phase 3).
    """
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

**Note**: Full context restoration is a Phase 3 feature pending SDK support for conversation continuation.

### Parent-Child Relationship

Sessions track forking relationships via foreign key:

From [session.py:46-49](../../app/models/session.py:46-49):
```python
# Session Relationships
parent_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
is_fork = Column(Boolean, default=False)
```

You can query all forked sessions from a parent:

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

### Use Cases

**Forked Mode is ideal for**:
- Experimenting with different approaches without risk
- A/B testing conversation strategies
- Creating rollback points before risky operations
- Parallel exploration of solution paths
- Teaching/demonstration (fork to show alternatives)
- Debugging by forking at error point

**Example Scenario**:
```
Original Session: "Refactor this codebase"
├─ Fork 1: Try functional programming approach
├─ Fork 2: Try OOP approach
└─ Fork 3: Try hybrid approach

Compare results, choose best, continue from there
```

### API Usage

**Forking a Session**:
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{parent_id}/fork \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Experimental Fork",
    "fork_at_message": 10
  }'
```

From [sessions.py:712-766](../../app/api/v1/sessions.py:712-766):
```python
@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session_endpoint(
    session_id: UUID,
    request: SessionForkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Fork an existing session."""
    # ... implementation ...
    forked_session = await service.fork_session_advanced(
        parent_session_id=session_id,
        user_id=current_user.id,
        fork_at_message=request.fork_at_message,
        name=request.name,
    )
```

**Response includes parent link**:
```json
{
  "id": "new-fork-uuid",
  "parent_session_id": "parent-uuid",
  "is_fork": true,
  "name": "Experimental Fork",
  "_links": {
    "self": "/api/v1/sessions/new-fork-uuid",
    "parent": "/api/v1/sessions/parent-uuid",
    "query": "/api/v1/sessions/new-fork-uuid/query"
  }
}
```

### Configuration

Forked sessions inherit parent configuration by default:

From [session_service.py:366-373](../../app/services/session_service.py:366-373):
```python
# Create forked session
forked_session = await self.create_session(
    user_id=user_id,
    mode=SessionMode.FORKED,
    sdk_options=parent.sdk_options,  # Inherit SDK options
    name=name or f"{parent.name} (fork)" if parent.name else "Forked session",
    parent_session_id=parent.id,
)
```

**Inherited Settings**:
- `sdk_options` (model, max_turns, etc.)
- Permission policies
- Allowed/disallowed tools
- Hook configurations
- Custom policies

**New/Different**:
- `session_id` (new UUID)
- `working_directory_path` (cloned copy)
- `created_at` (fork creation time)
- `parent_session_id` (references parent)

### Limitations

**Current Limitations**:
1. **Context Restoration**: Message history restoration not yet fully implemented (Phase 3)
2. **Storage Consumption**: Each fork duplicates working directory (can be large)
3. **Performance**: Forking large working directories can be slow
4. **SDK Support**: Full conversation continuation requires SDK enhancement

**Planned Improvements** (Phase 3):
- Full message history replay
- SDK context initialization with history
- Optimized storage (copy-on-write)
- Selective file cloning

---

## Mode Selection Logic (ExecutorFactory)

The `ExecutorFactory` automatically selects the appropriate executor based on session mode:

From [executor_factory.py:176-217](../../app/claude_sdk/execution/executor_factory.py:176-217):

```python
# Create executor based on session mode
if session.mode == SessionMode.INTERACTIVE:
    stream_handler = StreamHandler(db, message_repo, event_broadcaster)
    return InteractiveExecutor(
        session=session,
        client=client,
        message_handler=message_handler,
        stream_handler=stream_handler,
        result_handler=result_handler,
        error_handler=error_handler,
        event_broadcaster=event_broadcaster,
    )

elif session.mode == SessionMode.BACKGROUND:
    retry_policy = RetryPolicy(
        max_retries=session.max_retries or 3,
        base_delay=session.retry_delay or 2.0,
    )
    retry_manager = RetryManager(retry_policy)
    return BackgroundExecutor(
        session=session,
        client=client,
        message_handler=message_handler,
        result_handler=result_handler,
        error_handler=error_handler,
        retry_manager=retry_manager,
    )

elif session.mode == SessionMode.FORKED:
    return ForkedExecutor(
        session=session,
        parent_session_id=session.parent_session_id,
        fork_at_message=None,
        client=client,
        message_handler=message_handler,
        result_handler=result_handler,
        error_handler=error_handler,
        message_repo=message_repo,
    )

else:
    raise ValueError(f"Unknown session mode: {session.mode}")
```

**Factory automatically wires**:
- Appropriate executor type
- Required handlers (message, stream, result, error)
- Mode-specific components (retry manager, event broadcaster)
- Database repositories
- Hook and permission managers

---

## Mode Comparison Table

| Feature | Interactive | Background | Forked |
|---------|-------------|------------|--------|
| **Streaming** | Yes | No | Yes (inherits) |
| **WebSocket** | Yes | No | Optional |
| **Use Case** | Chat UIs | Automation | Experimentation |
| **Retry Logic** | Basic | **Advanced** | Basic |
| **Performance** | Moderate | **High** | Moderate |
| **Reliability** | Moderate | **High** | Moderate |
| **Resource Usage** | Higher | Lower | **Highest** (clone) |
| **Real-time Feedback** | **Yes** | No | Yes |
| **Parent Tracking** | No | No | **Yes** |
| **Context Restore** | N/A | N/A | **Yes** (planned) |

---

## Common API Patterns

### Creating Sessions by Mode

**Interactive (default)**:
```bash
POST /api/v1/sessions
{
  "name": "Chat Session",
  "mode": "interactive"
}
```

**Background**:
```bash
POST /api/v1/sessions
{
  "name": "Batch Job",
  "mode": "non_interactive",
  "sdk_options": {
    "max_retries": 5,
    "timeout_seconds": 300
  }
}
```

**Forked**:
```bash
POST /api/v1/sessions/{parent_id}/fork
{
  "name": "Experimental Branch",
  "fork_at_message": 10
}
```

### Executing Queries

**All modes use same endpoint**:
```bash
POST /api/v1/sessions/{id}/query
{
  "message": "Your query here"
}
```

The executor is selected automatically based on session mode.

---

## Related Documentation

- **Session Lifecycle**: [SESSION_LIFECYCLE.md](SESSION_LIFECYCLE.md) - Complete session state machine
- **Session Forking**: [SESSION_FORKING.md](SESSION_FORKING.md) - Deep dive into forking process
- **Working Directories**: [WORKING_DIRECTORIES.md](WORKING_DIRECTORIES.md) - Directory management and cloning
- **Execution Strategies**: [../../claude_sdk/EXECUTION_STRATEGIES.md](../../claude_sdk/EXECUTION_STRATEGIES.md) - Executor implementations
- **API Endpoints**: [../../api/REST_API_ENDPOINTS.md](../../api/REST_API_ENDPOINTS.md) - Session API reference

---

## Related Files

**Domain Layer**:
- [session.py:22-26](../../app/domain/entities/session.py:22-26) - SessionMode enum
- [session.py:32-92](../../app/domain/entities/session.py:32-92) - Session entity

**Executors**:
- [executor_factory.py](../../app/claude_sdk/execution/executor_factory.py) - Factory for mode selection
- [interactive_executor.py](../../app/claude_sdk/execution/interactive_executor.py) - Interactive mode
- [background_executor.py](../../app/claude_sdk/execution/background_executor.py) - Background mode
- [forked_executor.py](../../app/claude_sdk/execution/forked_executor.py) - Forked mode

**Services**:
- [sdk_session_service.py:277-356](../../app/services/sdk_session_service.py:277-356) - execute_query method
- [session_service.py:351-404](../../app/services/session_service.py:351-404) - fork_session_advanced

**API**:
- [sessions.py:56-233](../../app/api/v1/sessions.py:56-233) - Create session endpoint
- [sessions.py:324-424](../../app/api/v1/sessions.py:324-424) - Query endpoint
- [sessions.py:712-766](../../app/api/v1/sessions.py:712-766) - Fork endpoint

**Configuration**:
- [config.py:102-107](../../app/core/config.py:102-107) - SDK settings

---

## Keywords

`session-modes`, `interactive`, `background`, `non-interactive`, `forked`, `executor-factory`, `streaming`, `websocket`, `real-time`, `batch-processing`, `automation`, `retry-logic`, `session-forking`, `execution-modes`, `mode-selection`, `interactive-executor`, `background-executor`, `forked-executor`, `execution-strategies`, `performance`, `throughput`
