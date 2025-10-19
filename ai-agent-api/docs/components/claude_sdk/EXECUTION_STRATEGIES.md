# Execution Strategies

## Purpose

The Execution Strategies subsystem implements the **Strategy Pattern** to provide different execution modes for Claude SDK sessions. Each strategy optimizes for specific use cases:

- **InteractiveExecutor**: Real-time streaming for chat UIs (like ChatGPT)
- **BackgroundExecutor**: Non-streaming automation for batch processing
- **ForkedExecutor**: Session continuation from a parent session

The factory pattern (`ExecutorFactory`) selects the appropriate executor based on `SessionMode` and handles all dependency injection automatically.

## Architecture

### Strategy Pattern Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  SDKIntegratedSessionService.execute_query()                 │
│    ↓                                                          │
│  ExecutorFactory.create_executor(session, db, broadcaster)   │
│    ├─> Creates EnhancedClaudeClient                          │
│    ├─> Initializes all handlers                              │
│    ├─> Registers hooks and policies                          │
│    └─> Returns appropriate executor                          │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              BaseExecutor (Abstract)                   │ │
│  │              • execute(prompt: str) → Any              │ │
│  │              • _handle_error(error, context)           │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↑                 ↑                ↑                  │
│         │                 │                │                  │
│  ┌──────────┐    ┌──────────────┐   ┌────────────┐          │
│  │Interactive│    │ Background   │   │  Forked    │          │
│  │Executor   │    │ Executor     │   │  Executor  │          │
│  └──────────┘    └──────────────┘   └────────────┘          │
│  • Streaming     • No streaming      • Context               │
│  • WebSocket     • Retry logic       • restoration           │
│  • Real-time     • ExecutionResult   • Parent msgs           │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes & Interfaces

### BaseExecutor (Abstract Base Class)

**File**: [app/claude_sdk/execution/base_executor.py](../../app/claude_sdk/execution/base_executor.py)

**Purpose**: Defines the common interface and error handling for all executors.

```python
# Lines 15-108
class BaseExecutor(ABC):
    """Abstract base for all execution strategies."""

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
    ):
        """Initialize with dependencies."""

    @abstractmethod
    async def execute(self, prompt: str) -> Any:
        """Execute query (return type varies by strategy)."""

    async def _handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Common error handling logic."""
```

**Key Properties**:
- All executors share the same dependencies (session, client, handlers)
- Common error handling via `_handle_error()`
- Subclasses define strategy-specific `execute()` implementation

### InteractiveExecutor (Streaming Strategy)

**File**: [app/claude_sdk/execution/interactive_executor.py](../../app/claude_sdk/execution/interactive_executor.py)

**Purpose**: Provides real-time streaming for chat UIs with WebSocket broadcasting.

**Signature**:
```python
# Lines 20-111
class InteractiveExecutor(BaseExecutor):
    async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
        """Execute and stream responses in real-time."""
```

**Additional Dependencies**:
```python
# Lines 32-55
def __init__(
    self,
    session: Session,
    client: EnhancedClaudeClient,
    message_handler: MessageHandler,
    stream_handler: StreamHandler,  # For StreamEvent processing
    result_handler: ResultHandler,
    error_handler: ErrorHandler,
    event_broadcaster: Optional[Any] = None,  # WebSocket broadcaster
):
```

**Execution Flow**:
```python
# Lines 74-106
1. Enable partial messages for streaming
   client.config.include_partial_messages = True

2. Send query
   await self.client.query(prompt)

3. Stream responses
   async for message in self.client.receive_response():

       # AssistantMessage
       if isinstance(message, AssistantMessage):
           domain_message = await message_handler.handle_assistant_message(...)
           if event_broadcaster:
               await event_broadcaster.broadcast(...)
           yield domain_message

       # StreamEvent (partial updates)
       elif isinstance(message, StreamEvent):
           await stream_handler.handle_stream_event(...)

       # ResultMessage (final metrics)
       elif isinstance(message, ResultMessage):
           await result_handler.handle_result_message(...)
           break
```

**Key Features**:
- Yields messages as they arrive (AsyncIterator)
- Processes StreamEvent for token-by-token updates
- Broadcasts to WebSocket clients for real-time UI
- Suitable for ChatGPT-like interfaces

### BackgroundExecutor (Non-Streaming Strategy)

**File**: [app/claude_sdk/execution/background_executor.py](../../app/claude_sdk/execution/background_executor.py)

**Purpose**: Executes automation tasks without streaming, with built-in retry logic.

**Signature**:
```python
# Lines 40-131
class BackgroundExecutor(BaseExecutor):
    async def execute(self, prompt: str) -> ExecutionResult:
        """Execute and return final result (no streaming)."""
```

**Additional Dependencies**:
```python
# Lines 52-72
def __init__(
    self,
    session: Session,
    client: EnhancedClaudeClient,
    message_handler: MessageHandler,
    result_handler: ResultHandler,
    error_handler: ErrorHandler,
    retry_manager: RetryManager,  # For retry logic
):
```

**Result Structure**:
```python
# Lines 21-38
@dataclass
class ExecutionResult:
    """Background execution result."""
    session_id: UUID
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metrics: ClientMetrics
```

**Execution Flow**:
```python
# Lines 74-115
1. Disable partial messages (no streaming)
   client.config.include_partial_messages = False

2. Execute with retry logic
   await retry_manager.execute_with_retry(self._execute_query, prompt)

3. Return final result
   return ExecutionResult(
       session_id=session.id,
       success=True,
       data={"status": "completed"},
       error_message=None,
       metrics=await client.get_metrics()
   )

4. On error, return error result
   return ExecutionResult(
       session_id=session.id,
       success=False,
       error_message=str(e),
       metrics=await client.get_metrics()
   )
```

**Key Features**:
- No real-time streaming (better performance)
- Automatic retry via RetryManager
- Returns final ExecutionResult with metrics
- Suitable for scheduled tasks, batch processing, APIs

### ForkedExecutor (Session Continuation Strategy)

**File**: [app/claude_sdk/execution/forked_executor.py](../../app/claude_sdk/execution/forked_executor.py)

**Purpose**: Continues execution from a parent session at a specific message.

**Signature**:
```python
# Lines 20-120
class ForkedExecutor(BaseExecutor):
    async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
        """Execute in forked session with restored context."""
```

**Additional Dependencies**:
```python
# Lines 32-58
def __init__(
    self,
    session: Session,
    parent_session_id: UUID,  # Parent to fork from
    fork_at_message: Optional[int],  # Message index
    client: EnhancedClaudeClient,
    message_handler: MessageHandler,
    result_handler: ResultHandler,
    error_handler: ErrorHandler,
    message_repo: MessageRepository,  # For parent messages
):
```

**Execution Flow**:
```python
# Lines 72-119
1. Restore context from parent
   await self._restore_context()
       ├─> Retrieve parent messages up to fork_at_message
       └─> TODO: Restore to SDK session (Phase 3 feature)

2. Continue conversation (same as interactive)
   await client.query(prompt)
   async for message in client.receive_response():
       if isinstance(message, AssistantMessage):
           yield await message_handler.handle_assistant_message(...)
       elif isinstance(message, ResultMessage):
           await result_handler.handle_result_message(...)
           break
```

**Key Features**:
- Restores conversation history from parent
- Enables "what-if" exploration
- Maintains parent-child relationship
- Note: Full context restoration pending SDK support (Phase 3)

### ExecutorFactory (Factory Pattern)

**File**: [app/claude_sdk/execution/executor_factory.py](../../app/claude_sdk/execution/executor_factory.py)

**Purpose**: Creates appropriate executor with all dependencies wired correctly.

**Main Method**:
```python
# Lines 54-218
@staticmethod
async def create_executor(
    session: Session,
    db: AsyncSession,
    event_broadcaster: Optional[Any] = None,
) -> BaseExecutor:
    """Create executor for session mode."""
```

**Creation Flow**:
```python
1. Initialize repositories
   hook_execution_repo = HookExecutionRepository(db)
   permission_decision_repo = PermissionDecisionRepository(db)
   message_repo = MessageRepository(db)
   tool_call_repo = ToolCallRepository(db)
   session_repo = SessionRepository(db)
   metrics_repo = SessionMetricsSnapshotRepository(db)

2. Initialize HookManager (if hooks_enabled)
   hook_manager = HookManager(db, hook_execution_repo)
   for hook_type in session.hooks_enabled:
       if hook_type == HookType.PRE_TOOL_USE:
           await hook_manager.register_hook(HookType.PRE_TOOL_USE, AuditHook(db))
           await hook_manager.register_hook(HookType.PRE_TOOL_USE, ValidationHook(db))
       elif hook_type == HookType.POST_TOOL_USE:
           await hook_manager.register_hook(HookType.POST_TOOL_USE, MetricsHook(db))
       # ... etc
   hooks_dict = hook_manager.build_hook_matchers(session.id, enabled_hook_types)

3. Initialize PermissionManager
   policy_engine = PolicyEngine()
   permission_manager = PermissionManager(db, policy_engine, permission_decision_repo)
   permission_callback = permission_manager.create_callback(
       session_id=session.id,
       user_id=session.user_id,
       working_directory=session.working_directory_path
   )

4. Create ClientConfig
   client_config = ClientConfig(
       session_id=session.id,
       model=session.sdk_options.get("model", "claude-sonnet-4-5"),
       hooks=hooks_dict,
       can_use_tool=permission_callback,
       # ... all other config
   )

5. Create EnhancedClaudeClient
   client = EnhancedClaudeClient(client_config)

6. Create handlers
   message_handler = MessageHandler(db, message_repo, tool_call_repo)
   result_handler = ResultHandler(db, session_repo, metrics_repo)
   error_handler = ErrorHandler(db, session_repo, AuditService(db))

7. Create executor based on session.mode
   if session.mode == SessionMode.INTERACTIVE:
       stream_handler = StreamHandler(db, message_repo, event_broadcaster)
       return InteractiveExecutor(
           session=session,
           client=client,
           message_handler=message_handler,
           stream_handler=stream_handler,
           result_handler=result_handler,
           error_handler=error_handler,
           event_broadcaster=event_broadcaster
       )

   elif session.mode == SessionMode.BACKGROUND:
       retry_policy = RetryPolicy(max_retries=3, base_delay=2.0)
       retry_manager = RetryManager(retry_policy)
       return BackgroundExecutor(
           session=session,
           client=client,
           message_handler=message_handler,
           result_handler=result_handler,
           error_handler=error_handler,
           retry_manager=retry_manager
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
           message_repo=message_repo
       )
```

## Execution Strategy Selection

### Based on SessionMode Enum

```python
# From app/domain/entities/session.py
class SessionMode(str, Enum):
    INTERACTIVE = "interactive"  # → InteractiveExecutor
    BACKGROUND = "background"    # → BackgroundExecutor
    FORKED = "forked"            # → ForkedExecutor
```

### Strategy Comparison Matrix

| Feature | InteractiveExecutor | BackgroundExecutor | ForkedExecutor |
|---------|--------------------|--------------------|----------------|
| **Return Type** | AsyncIterator[Message] | ExecutionResult | AsyncIterator[Message] |
| **Streaming** | Yes (partial messages) | No | Optional |
| **WebSocket** | Yes (event broadcasting) | No | No |
| **Retry Logic** | Manual (EnhancedClient) | Automatic (RetryManager) | Manual |
| **Use Case** | Chat UIs, real-time | Automation, batch jobs | Exploration, "what-if" |
| **Performance** | Lower (streaming overhead) | Higher (no streaming) | Medium |
| **Context Restoration** | No | No | Yes (from parent) |
| **Best For** | ChatGPT-like apps | Scheduled tasks, APIs | Session branching |

## Flow Diagrams

### InteractiveExecutor Flow

```
User sends query
  ↓
InteractiveExecutor.execute(prompt)
  ↓
1. Enable streaming
   client.config.include_partial_messages = True
  ↓
2. Send query to SDK
   await client.query(prompt)
  ↓
3. Stream responses
   async for message in client.receive_response():
  ↓
  ├─> AssistantMessage
  │     ├─> message_handler.handle_assistant_message()
  │     │     ├─> Extract text, tool_use, tool_result blocks
  │     │     ├─> Persist message to DB
  │     │     └─> Persist tool calls to DB
  │     ├─> event_broadcaster.broadcast() to WebSocket clients
  │     └─> yield domain_message
  │
  ├─> StreamEvent (partial update)
  │     ├─> stream_handler.handle_stream_event()
  │     └─> event_broadcaster.broadcast() partial update
  │
  └─> ResultMessage (final)
        ├─> result_handler.handle_result_message()
        │     ├─> Extract cost, tokens, duration
        │     ├─> Update session with metrics
        │     └─> Create metrics snapshot
        └─> break (end of stream)
```

### BackgroundExecutor Flow

```
API request with query
  ↓
BackgroundExecutor.execute(prompt)
  ↓
1. Disable streaming
   client.config.include_partial_messages = False
  ↓
2. Execute with retry
   await retry_manager.execute_with_retry(_execute_query, prompt)
  ↓
  ├─> Attempt 1
  │     ├─> client.query(prompt)
  │     ├─> async for message in client.receive_response():
  │     │     ├─> message_handler.handle_assistant_message()
  │     │     └─> result_handler.handle_result_message()
  │     └─> Success → return
  │
  ├─> On CLIConnectionError (retryable)
  │     ├─> Calculate exponential backoff delay
  │     ├─> await asyncio.sleep(delay)
  │     └─> Attempt 2, 3, ...
  │
  └─> On ClaudeSDKError (non-retryable)
        └─> Raise immediately
  ↓
3. Return ExecutionResult
   ExecutionResult(
       success=True,
       data={"status": "completed"},
       metrics=client_metrics
   )
```

### ForkedExecutor Flow

```
Request to fork session
  ↓
ForkedExecutor.execute(prompt)
  ↓
1. Restore parent context
   await _restore_context()
     ├─> Retrieve parent messages up to fork_at_message
     │     message_repo.get_by_session(parent_session_id, limit=fork_at_message)
     └─> TODO: Restore to SDK session
           (Waiting for SDK context continuation support)
  ↓
2. Continue conversation (same as interactive)
   await client.query(prompt)
   async for message in client.receive_response():
       ├─> message_handler.handle_assistant_message()
       ├─> result_handler.handle_result_message()
       └─> yield domain_message
```

## Configuration

### Session Mode Configuration

```python
# Create interactive session
session = Session(
    mode=SessionMode.INTERACTIVE,
    include_partial_messages=True,  # Enable streaming
    # ... other config
)

# Create background session
session = Session(
    mode=SessionMode.BACKGROUND,
    max_retries=5,  # More retries for automation
    retry_delay=3.0,
    include_partial_messages=False,  # Disable streaming
)

# Create forked session
session = Session(
    mode=SessionMode.FORKED,
    parent_session_id=parent_id,
    # ... other config
)
```

## Common Tasks

### How to Use InteractiveExecutor

```python
from app.claude_sdk.execution.executor_factory import ExecutorFactory
from app.domain.entities.session import SessionMode

# Create session with INTERACTIVE mode
session = await session_repo.create(
    user_id=user_id,
    mode=SessionMode.INTERACTIVE,
    include_partial_messages=True
)

# Create executor via factory
executor = await ExecutorFactory.create_executor(
    session=session,
    db=db,
    event_broadcaster=websocket_broadcaster
)

# Execute and stream responses
async for message in executor.execute("Write a Python script"):
    print(f"Message: {message.content}")
    # WebSocket clients automatically receive updates via event_broadcaster
```

### How to Use BackgroundExecutor

```python
# Create session with BACKGROUND mode
session = await session_repo.create(
    user_id=user_id,
    mode=SessionMode.BACKGROUND,
    max_retries=5,
    include_partial_messages=False
)

# Create executor
executor = await ExecutorFactory.create_executor(
    session=session,
    db=db
)

# Execute and get final result
result = await executor.execute("Analyze this dataset")

if result.success:
    print(f"Completed! Cost: ${result.metrics.total_cost_usd}")
else:
    print(f"Failed: {result.error_message}")
```

### How to Fork a Session

```python
# Get parent session
parent_session = await session_repo.get_by_id(parent_id)

# Create forked session
forked_session = await session_repo.create(
    user_id=user_id,
    mode=SessionMode.FORKED,
    parent_session_id=parent_id,
    # Inherits parent config
)

# Create executor
executor = await ExecutorFactory.create_executor(
    session=forked_session,
    db=db
)

# Execute from parent context
async for message in executor.execute("Try a different approach"):
    print(f"Forked response: {message.content}")
```

### How to Add a Custom Executor

1. Create executor class:
```python
# app/claude_sdk/execution/my_executor.py
from app.claude_sdk.execution.base_executor import BaseExecutor

class MyCustomExecutor(BaseExecutor):
    async def execute(self, prompt: str) -> Any:
        # Custom execution logic
        await self.client.query(prompt)

        async for message in self.client.receive_response():
            # Custom processing
            pass

        return custom_result
```

2. Add to ExecutorFactory:
```python
# app/claude_sdk/execution/executor_factory.py
elif session.mode == SessionMode.CUSTOM:
    return MyCustomExecutor(
        session=session,
        client=client,
        # ... handlers
    )
```

3. Add mode to SessionMode enum:
```python
# app/domain/entities/session.py
class SessionMode(str, Enum):
    CUSTOM = "custom"
```

## Related Files

**Core Executor Files**:
- [app/claude_sdk/execution/base_executor.py](../../app/claude_sdk/execution/base_executor.py) - Abstract base
- [app/claude_sdk/execution/interactive_executor.py](../../app/claude_sdk/execution/interactive_executor.py) - Streaming
- [app/claude_sdk/execution/background_executor.py](../../app/claude_sdk/execution/background_executor.py) - Non-streaming
- [app/claude_sdk/execution/forked_executor.py](../../app/claude_sdk/execution/forked_executor.py) - Forking
- [app/claude_sdk/execution/executor_factory.py](../../app/claude_sdk/execution/executor_factory.py) - Factory

**Dependencies**:
- [app/claude_sdk/core/client.py](../../app/claude_sdk/core/client.py) - EnhancedClaudeClient
- [app/claude_sdk/handlers/](../../app/claude_sdk/handlers/) - All handlers
- [app/claude_sdk/retry/retry_manager.py](../../app/claude_sdk/retry/retry_manager.py) - Retry logic
- [app/domain/entities/session.py](../../app/domain/entities/session.py) - Session entity, SessionMode enum

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [CLIENT_MANAGEMENT.md](./CLIENT_MANAGEMENT.md) - Client lifecycle
- [MESSAGE_PROCESSING.md](./MESSAGE_PROCESSING.md) - Message handlers
- [RETRY_RESILIENCE.md](./RETRY_RESILIENCE.md) - Retry manager details

## Keywords

execution-strategies, strategy-pattern, executor-factory, interactive-executor, background-executor, forked-executor, base-executor, session-mode, streaming-execution, non-streaming-execution, real-time-streaming, websocket-broadcasting, event-broadcaster, partial-messages, stream-event, execution-result, retry-logic, session-forking, context-restoration, parent-session, dependency-injection, factory-pattern, async-iterator, automation, batch-processing, chat-ui
