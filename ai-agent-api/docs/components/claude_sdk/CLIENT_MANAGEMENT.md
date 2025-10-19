# Client Management

## Purpose

The Client Management subsystem handles the complete lifecycle of Claude SDK clients, from creation and initialization through connection management and graceful disposal. It provides two key implementations:

1. **Phase 1 (Legacy)**: `ClaudeSDKClientManager` - Direct SDK client pooling
2. **Phase 2 (NEW)**: `EnhancedClaudeClient` + `SessionManager` - Enhanced client with metrics and session lifecycle

Both approaches wrap the official `claude-agent-sdk.ClaudeSDKClient` but provide different levels of abstraction and features.

## Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  SDKIntegratedSessionService                                 │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 2 (Recommended)                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  SessionManager                                  │ │ │
│  │  │    • create_session()                            │ │ │
│  │  │    • resume_session()                            │ │ │
│  │  │    • fork_session()                              │ │ │
│  │  │    • archive_session()                           │ │ │
│  │  │    • Active clients registry                     │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │    ↓                                                  │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  EnhancedClaudeClient                            │ │ │
│  │  │    • Wraps ClaudeSDKClient                       │ │ │
│  │  │    • Retry logic & circuit breaker               │ │ │
│  │  │    • Metrics tracking                            │ │ │
│  │  │    • State management (ClientState enum)         │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 1 (Legacy - Still Used)                  │ │
│  │  ClaudeSDKClientManager                                │ │
│  │    • Client pool: Dict[UUID, ClaudeSDKClient]          │ │
│  │    • create_client()                                   │ │
│  │    • get_client()                                      │ │
│  │    • disconnect_client()                               │ │
│  │    • Direct SDK client management                      │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Official Claude SDK (claude-agent-sdk)                     │
│  └─> ClaudeSDKClient                                        │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes & Interfaces

### Phase 1: ClaudeSDKClientManager

**File**: [app/claude_sdk/client_manager.py](../../app/claude_sdk/client_manager.py)

**Purpose**: Manages a pool of official ClaudeSDKClient instances, one per session.

**Key Methods**:

```python
# Lines 56-106
async def create_client(
    session: Session,
    permission_callback: Optional[Callable] = None,
    hooks: Optional[dict] = None,
) -> ClaudeSDKClient:
    """Create and connect SDK client for session.

    1. Build ClaudeAgentOptions from Session entity
    2. Create ClaudeSDKClient with options
    3. Connect to Claude Code CLI
    4. Store in pool
    """

# Lines 108-116
async def get_client(session_id: UUID) -> ClaudeSDKClient:
    """Retrieve active client from pool."""

# Lines 118-145
async def disconnect_client(session_id: UUID) -> None:
    """Disconnect and remove client from pool."""

# Lines 165-216
def _build_options(
    session: Session,
    permission_callback: Optional[Callable],
    hooks: Optional[dict],
) -> ClaudeAgentOptions:
    """Convert domain Session to SDK options."""
```

**Internal State**:

```python
# Lines 50-54
self._clients: Dict[UUID, ClaudeSDKClient] = {}  # Client pool
self._locks: Dict[UUID, asyncio.Lock] = {}  # Per-session locks
self._background_tasks: Dict[UUID, asyncio.Task] = {}  # Task tracking
```

### Phase 2: EnhancedClaudeClient

**File**: [app/claude_sdk/core/client.py](../../app/claude_sdk/core/client.py)

**Purpose**: Wraps ClaudeSDKClient with retry logic, metrics tracking, and state management.

**Key Methods**:

```python
# Lines 53-139
async def connect() -> None:
    """Connect to Claude Code CLI with retry logic.

    - Exponential backoff retry
    - Metrics start time tracking
    - State transitions: CREATED → CONNECTING → CONNECTED | FAILED
    """

# Lines 140-166
async def query(prompt: str) -> None:
    """Send query to SDK with error tracking."""

# Lines 168-210
async def receive_response() -> AsyncIterator[Union[AssistantMessage, ResultMessage, StreamEvent]]:
    """Stream responses from SDK.

    - Tracks message count
    - Extracts cost/token metrics from ResultMessage
    - Yields messages to caller
    """

# Lines 212-250
async def disconnect() -> ClientMetrics:
    """Disconnect and return final metrics.

    Returns: ClientMetrics with complete session statistics
    """
```

**State Management**:

```python
# From app/claude_sdk/core/config.py:11-18
class ClientState(str, Enum):
    CREATED = "created"  # Initial state
    CONNECTING = "connecting"  # Connection in progress
    CONNECTED = "connected"  # Ready for queries
    DISCONNECTING = "disconnecting"  # Cleanup in progress
    DISCONNECTED = "disconnected"  # Fully closed
    FAILED = "failed"  # Connection/execution failed
```

**Metrics Tracking**:

```python
# From app/claude_sdk/core/config.py:66-131
@dataclass
class ClientMetrics:
    session_id: UUID
    total_messages: int = 0
    total_tool_calls: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_cost_usd: Decimal = Decimal("0.0")
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_creation_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Helper methods
    def increment_messages()
    def increment_tool_calls()
    def increment_errors()
    def increment_retries()
    def add_tokens(...)
    def add_cost(...)
    def mark_started()
    def mark_completed()
    def to_dict() -> Dict[str, Any]
```

### Phase 2: SessionManager

**File**: [app/claude_sdk/core/session_manager.py](../../app/claude_sdk/core/session_manager.py)

**Purpose**: Manages complete session lifecycle including creation, resumption, forking, and archival.

**Key Methods**:

```python
# Lines 67-120
async def create_session(
    session_id: UUID,
    mode: SessionMode,
    session: Session
) -> EnhancedClaudeClient:
    """Create new SDK session.

    1. Build ClientConfig from Session
    2. Create EnhancedClaudeClient
    3. Connect to SDK
    4. Register in active_clients
    """

# Lines 122-163
async def resume_session(
    session_id: UUID,
    session: Session,
    restore_context: bool = True
) -> EnhancedClaudeClient:
    """Resume paused session.

    - Validates session status (PAUSED or WAITING)
    - Creates new client
    - TODO: Restore conversation context
    """

# Lines 165-211
async def fork_session(
    parent_session_id: UUID,
    fork_session_id: UUID,
    fork_session: Session,
    fork_at_message: Optional[int] = None
) -> EnhancedClaudeClient:
    """Fork session from parent at specific point.

    - Retrieves parent messages up to fork point
    - Creates new forked client
    - TODO: Restore parent context
    """

# Lines 213-308
async def archive_session(
    session_id: UUID,
    archive_to_storage: bool = True,
    storage_backend: str = "s3",
    compression: str = "tar.gz"
) -> Dict[str, Any]:
    """Archive session and cleanup.

    1. Disconnect client if active
    2. Archive working directory to S3 (if enabled)
    3. Update session with archive_id
    4. Return archive metadata
    """
```

**Active Client Registry**:

```python
# Lines 54
self.active_clients: Dict[UUID, EnhancedClaudeClient] = {}
```

### Configuration: ClientConfig

**File**: [app/claude_sdk/core/config.py](../../app/claude_sdk/core/config.py)

**Purpose**: Configuration dataclass for EnhancedClaudeClient.

```python
# Lines 21-68
@dataclass
class ClientConfig:
    """Enhanced client configuration."""
    session_id: UUID
    model: str = "claude-sonnet-4-5"
    permission_mode: str = "default"
    max_turns: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout_seconds: int = 120
    include_partial_messages: bool = False
    working_directory: Path
    mcp_servers: Dict[str, Any]
    allowed_tools: Optional[List[str]]
    hooks: Optional[Dict[str, List[Any]]]  # HookMatcher dict
    can_use_tool: Optional[Callable]  # Permission callback

    def __post_init__() -> None:
        """Validate configuration."""

    def is_streaming_enabled() -> bool
    def get_retry_backoff(attempt: int) -> float
```

### Options Builder: OptionsBuilder

**File**: [app/claude_sdk/core/options_builder.py](../../app/claude_sdk/core/options_builder.py)

**Purpose**: Converts domain entities to SDK ClaudeAgentOptions.

```python
# Lines 18-67
@staticmethod
def build(
    session: Session,
    permission_callback: Optional[Callable] = None,
    hooks: Optional[Dict[str, List[Any]]] = None,
    mcp_servers: Optional[Dict[str, Any]] = None,
) -> ClaudeAgentOptions:
    """Build SDK options from domain Session entity.

    Returns ClaudeAgentOptions with:
    - model, max_turns, permission_mode
    - cwd (working directory)
    - allowed_tools list
    - can_use_tool callback
    - hooks (HookMatcher dict)
    - mcp_servers configuration
    """
```

## Implementation Details

### Client Creation Flow (Phase 2)

```
SessionService.create_session()
  ↓
SessionManager.create_session(session_id, mode, session)
  ↓
1. Build ClientConfig
   ├─> Extract model, max_turns from session.sdk_options
   ├─> Get permission_mode from session.permission_mode
   ├─> Set retry parameters (max_retries, retry_delay)
   ├─> Set timeout_seconds
   ├─> Get working_directory from session.working_directory_path
   └─> Set allowed_tools from sdk_options
  ↓
2. Create EnhancedClaudeClient(config)
   └─> Initialize ClientMetrics
   └─> Set state = CREATED
  ↓
3. client.connect()
   ├─> state = CONNECTING
   ├─> metrics.mark_started()
   ├─> Build ClaudeAgentOptions via OptionsBuilder
   ├─> Retry loop (max_retries + 1 attempts):
   │     ├─> Create ClaudeSDKClient(options)
   │     ├─> On CLIConnectionError:
   │     │     ├─> metrics.increment_errors()
   │     │     ├─> metrics.increment_retries()
   │     │     ├─> Calculate exponential backoff delay
   │     │     └─> await asyncio.sleep(delay)
   │     └─> On success:
   │           └─> state = CONNECTED
   └─> On failure after retries:
         └─> state = FAILED, raise
  ↓
4. Register in active_clients
   └─> active_clients[session_id] = client
  ↓
5. Return EnhancedClaudeClient (ready for queries)
```

### Session Archival Flow

```
SessionManager.archive_session(session_id, archive_to_storage=True)
  ↓
1. Get session from database
   └─> session_repo.get_by_id(session_id)
  ↓
2. Disconnect client if active
   ├─> client = active_clients.get(session_id)
   ├─> metrics = await client.disconnect()
   │     ├─> state = DISCONNECTING
   │     ├─> sdk_client = None  # Cleanup
   │     ├─> state = DISCONNECTED
   │     ├─> metrics.mark_completed()
   │     └─> Return ClientMetrics
   └─> del active_clients[session_id]
  ↓
3. Archive working directory (if archive_to_storage=True)
   └─> storage_archiver.archive_working_directory(
         session_id=session_id,
         working_directory=Path(session.working_directory_path),
         storage_backend="s3",
         compression_type="tar.gz"
       )
       ↓
       ├─> Create tar.gz of working directory
       ├─> Upload to S3
       ├─> Create WorkingDirectoryArchive record
       └─> Return archive_metadata
  ↓
4. Update session with archive_id
   └─> session_repo.update(session_id, archive_id=archive_metadata.id)
  ↓
5. Return archive result
   └─> {
         "session_id": session_id,
         "archived": True,
         "storage_path": "s3://bucket/path",
         "archive_metadata": {...}
       }
```

### Connection Retry Logic

From [app/claude_sdk/core/client.py:94-129](../../app/claude_sdk/core/client.py:94-129):

```python
for attempt in range(self.config.max_retries + 1):
    try:
        # Create SDK client
        self.sdk_client = ClaudeSDKClient(options=self._sdk_options)
        self.state = ClientState.CONNECTED
        return

    except CLIConnectionError as e:
        self.metrics.increment_errors()

        if attempt < self.config.max_retries:
            self.metrics.increment_retries()
            # Exponential backoff: delay = retry_delay * (2 ** attempt)
            delay = self.config.retry_delay * (2**attempt)
            await asyncio.sleep(delay)
        else:
            # All retries exhausted
            self.state = ClientState.FAILED
            raise

    except ClaudeSDKError as e:
        # Non-retryable error
        self.metrics.increment_errors()
        self.state = ClientState.FAILED
        raise
```

## Configuration

### Session SDK Options

Domain Session entity contains SDK configuration:

```python
# From app/domain/entities/session.py
session.sdk_options = {
    "model": "claude-sonnet-4-5",
    "max_turns": 10,
    "allowed_tools": ["Bash", "Read", "Write"],
    "disallowed_tools": [],
    "system_prompt": "You are a helpful AI assistant...",
    "mcp_servers": {
        "server_name": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-..."]
        }
    },
    "env": {},
    "add_dirs": []
}
```

### Retry Configuration

```python
# From ClientConfig
max_retries: int = 3  # Total attempts = max_retries + 1 = 4
retry_delay: float = 2.0  # Initial delay in seconds
exponential_base: float = 2.0  # Delay multiplier

# Backoff schedule:
# Attempt 0: No delay (first attempt)
# Attempt 1: 2.0s (2.0 * 2^0)
# Attempt 2: 4.0s (2.0 * 2^1)
# Attempt 3: 8.0s (2.0 * 2^2)
```

## Common Tasks

### How to Create and Use a Session Client

**Phase 2 Approach (Recommended)**:

```python
from app.claude_sdk.core.session_manager import SessionManager
from app.claude_sdk.core.config import ClientConfig
from pathlib import Path

# Initialize SessionManager
session_manager = SessionManager(db)

# Create session
client = await session_manager.create_session(
    session_id=session.id,
    mode=SessionMode.INTERACTIVE,
    session=session
)

# Client is now connected and ready
await client.query("Hello, Claude!")

async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        print(message.content)
    elif isinstance(message, ResultMessage):
        print(f"Cost: ${message.total_cost_usd}")

# Get final metrics
metrics = await client.disconnect()
print(f"Total messages: {metrics.total_messages}")
print(f"Total cost: ${metrics.total_cost_usd}")
```

**Phase 1 Approach (Legacy)**:

```python
from app.claude_sdk.client_manager import ClaudeSDKClientManager

# Initialize manager
manager = ClaudeSDKClientManager()

# Create client
client = await manager.create_client(
    session=session,
    permission_callback=permission_callback,
    hooks=hooks_dict
)

# Use SDK client directly
await client.query("Hello!")
async for message in client.receive_response():
    # Process message
    pass

# Cleanup
await manager.disconnect_client(session.id)
```

### How to Archive a Session

```python
from app.claude_sdk.core.session_manager import SessionManager

session_manager = SessionManager(db)

# Archive with S3 upload
result = await session_manager.archive_session(
    session_id=session_id,
    archive_to_storage=True,
    storage_backend="s3",
    compression="tar.gz"
)

print(f"Archived to: {result['storage_path']}")
print(f"Archive ID: {result['archive_metadata']['id']}")
```

### How to Resume a Paused Session

```python
# Get paused session
session = await session_repo.get_by_id(session_id)

# Resume it
client = await session_manager.resume_session(
    session_id=session_id,
    session=session,
    restore_context=True  # TODO: Not yet implemented
)

# Continue querying
await client.query("Continue where we left off")
```

### How to Fork a Session

```python
# Create fork from parent at specific message
client = await session_manager.fork_session(
    parent_session_id=parent_id,
    fork_session_id=fork_id,
    fork_session=fork_session,
    fork_at_message=10  # Fork at message #10
)

# Fork has parent context (when implemented)
await client.query("Try a different approach")
```

## Cleanup and Disposal

### Graceful Shutdown

```python
# Disconnect all active sessions
await session_manager.disconnect_all()
# This iterates all active_clients and calls client.disconnect()
```

### Per-Session Cleanup

```python
# Manual disconnect
if session_id in session_manager.active_clients:
    client = session_manager.active_clients[session_id]
    metrics = await client.disconnect()
    del session_manager.active_clients[session_id]
```

## Related Files

**Phase 1 (Legacy)**:
- [app/claude_sdk/client_manager.py](../../app/claude_sdk/client_manager.py) - ClaudeSDKClientManager

**Phase 2 (NEW)**:
- [app/claude_sdk/core/config.py](../../app/claude_sdk/core/config.py) - ClientConfig, ClientMetrics, ClientState
- [app/claude_sdk/core/client.py](../../app/claude_sdk/core/client.py) - EnhancedClaudeClient
- [app/claude_sdk/core/session_manager.py](../../app/claude_sdk/core/session_manager.py) - SessionManager
- [app/claude_sdk/core/options_builder.py](../../app/claude_sdk/core/options_builder.py) - OptionsBuilder

**Dependencies**:
- [app/claude_sdk/retry/retry_manager.py](../../app/claude_sdk/retry/retry_manager.py) - Retry logic
- [app/claude_sdk/retry/circuit_breaker.py](../../app/claude_sdk/retry/circuit_breaker.py) - Circuit breaker
- [app/claude_sdk/persistence/storage_archiver.py](../../app/claude_sdk/persistence/storage_archiver.py) - S3 archival
- [app/domain/entities/session.py](../../app/domain/entities/session.py) - Session entity

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - How clients are used in executors
- [RETRY_RESILIENCE.md](./RETRY_RESILIENCE.md) - Retry and circuit breaker details

## Keywords

client-management, enhanced-client, session-manager, client-lifecycle, connection-management, claude-sdk-client, retry-logic, metrics-tracking, client-state, session-archival, session-forking, session-resumption, working-directory-archival, s3-upload, active-clients, client-pool, options-builder, claude-agent-options, client-config, graceful-shutdown, connection-retry, exponential-backoff, circuit-breaker-integration, session-persistence
