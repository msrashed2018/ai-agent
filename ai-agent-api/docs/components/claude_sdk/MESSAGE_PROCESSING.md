# Message Processing

## Purpose

The Message Processing subsystem handles the complete lifecycle of messages flowing from the Claude SDK, including parsing, persistence, streaming, result aggregation, and error handling. It transforms raw SDK message types into domain entities and coordinates database storage, WebSocket broadcasting, and metrics collection.

Key Components:
- **MessageHandler**: Processes AssistantMessage, extracts content blocks, persists messages and tool calls
- **StreamHandler**: Handles StreamEvent for real-time partial message updates
- **ResultHandler**: Processes ResultMessage, extracts final metrics and session statistics
- **ErrorHandler**: Centralizes error handling and session state updates
- **MessageProcessor (Legacy)**: Phase 1 message processing with broader responsibilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Executor Layer                           │
├─────────────────────────────────────────────────────────────┤
│  InteractiveExecutor / BackgroundExecutor / ForkedExecutor   │
│    ↓                                                          │
│  client.receive_response()  # Stream from SDK                │
│    ↓                                                          │
│  async for message in stream:                                │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Message Type Routing                                  │ │
│  │                                                         │ │
│  │  if AssistantMessage:                                  │ │
│  │      → MessageHandler                                  │ │
│  │                                                         │ │
│  │  elif StreamEvent:                                     │ │
│  │      → StreamHandler                                   │ │
│  │                                                         │ │
│  │  elif ResultMessage:                                   │ │
│  │      → ResultHandler                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│         │              │               │                      │
│         ↓              ↓               ↓                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐                  │
│  │ Message  │  │  Stream  │  │  Result   │                  │
│  │ Handler  │  │ Handler  │  │  Handler  │                  │
│  └──────────┘  └──────────┘  └───────────┘                  │
│       │              │               │                        │
│       ↓              ↓               ↓                        │
│  Repositories  EventBroadcaster  SessionRepo                 │
│  ├─ MessageRepo    (WebSocket)   MetricsRepo                 │
│  └─ ToolCallRepo                                              │
└─────────────────────────────────────────────────────────────┘
```

## SDK Message Types

The Claude SDK produces three main message types:

```python
from claude_agent_sdk import AssistantMessage, ResultMessage
from claude_agent_sdk.types import StreamEvent

# 1. AssistantMessage - Agent responses with content blocks
AssistantMessage(
    model="claude-sonnet-4-5",
    content=[
        TextBlock(text="Here is the code..."),
        ToolUseBlock(name="Write", id="toolu_123", input={...}),
        ToolResultBlock(tool_use_id="toolu_123", content="...", is_error=False),
        ThinkingBlock(thinking="Let me analyze...")  # Extended thinking
    ]
)

# 2. StreamEvent - Partial message updates (when include_partial_messages=True)
StreamEvent(
    event={
        "type": "content_block_delta",
        "delta": {"type": "text_delta", "text": " more text..."}
    }
)

# 3. ResultMessage - Final session metrics and statistics
ResultMessage(
    duration_ms=15234,
    total_cost_usd=0.0523,
    num_turns=3,
    api_usage={
        "input_tokens": 1523,
        "output_tokens": 892,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 1200
    }
)
```

## Key Classes & Interfaces

### MessageHandler

**File**: [app/claude_sdk/handlers/message_handler.py](../../app/claude_sdk/handlers/message_handler.py)

**Purpose**: Process AssistantMessage and extract all content blocks.

```python
# Lines 18-321
class MessageHandler:
    """Process AssistantMessage and extract content blocks."""

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository,
    ):
        self.db = db
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo

    async def handle_assistant_message(
        self, message: AssistantMessage, session_id: UUID
    ) -> DomainMessage:
        """Process AssistantMessage from SDK and persist to database.

        Flow:
        1. Extract all content blocks:
           - TextBlock → text_content list
           - ThinkingBlock → thinking_content list
           - ToolUseBlock → tool_use_blocks list
           - ToolResultBlock → tool_result_blocks list

        2. Combine text content

        3. Get next sequence number for session

        4. Create and persist MessageModel

        5. Process tool use blocks:
           - Create ToolCallModel for each ToolUseBlock
           - Status: "pending"

        6. Process tool result blocks:
           - Find corresponding ToolCallModel by tool_use_id
           - Update with result and status ("completed" or "failed")

        7. Return DomainMessage entity

        Returns:
            DomainMessage: Domain entity representation
        """

# Lines 51-147
async def handle_assistant_message(self, message, session_id):
    # 1. Extract content blocks
    text_content: List[str] = []
    thinking_content: List[str] = []
    tool_use_blocks: List[ToolUseBlock] = []
    tool_result_blocks: List[ToolResultBlock] = []

    for block in message.content:
        if isinstance(block, TextBlock):
            text_content.append(block.text)
        elif isinstance(block, ThinkingBlock):
            thinking_content.append(block.thinking)
        elif isinstance(block, ToolUseBlock):
            tool_use_blocks.append(block)
        elif isinstance(block, ToolResultBlock):
            tool_result_blocks.append(block)

    # 2. Combine content
    combined_content = "\n\n".join(text_content) if text_content else ""
    combined_thinking = "\n\n".join(thinking_content) if thinking_content else None

    # 3. Get sequence number
    sequence_number = await message_repo.get_next_sequence_number(session_id)

    # 4. Persist message
    message_model = MessageModel(
        id=uuid4(),
        session_id=session_id,
        message_type=MessageType.ASSISTANT.value,
        content=combined_content,
        sequence_number=sequence_number,
        model=message.model,
        thinking_content=combined_thinking,
        is_partial=False,
        created_at=datetime.utcnow(),
    )
    db.add(message_model)
    await db.flush()

    # 5. Process tool use blocks
    for tool_block in tool_use_blocks:
        await handle_tool_use_block(tool_block, session_id, message_id)

    # 6. Process tool result blocks
    for result_block in tool_result_blocks:
        await handle_tool_result_block(result_block, session_id, message_id)

    # 7. Return domain entity
    return DomainMessage(...)
```

**Content Block Handlers**:

```python
# Lines 149-202
async def handle_tool_use_block(self, block: ToolUseBlock, session_id, message_id):
    """Extract and persist tool usage.

    Creates ToolCallModel with:
    - tool_name: block.name
    - tool_use_id: block.id (SDK identifier)
    - tool_input: block.input
    - status: "pending" (will be updated when result arrives)
    """
    tool_call_model = ToolCallModel(
        id=uuid4(),
        session_id=session_id,
        message_id=message_id,
        tool_name=block.name,
        tool_use_id=block.id,
        tool_input=block.input,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(tool_call_model)
    await db.flush()

# Lines 204-278
async def handle_tool_result_block(self, block: ToolResultBlock, session_id, message_id):
    """Process tool execution result.

    Updates ToolCallModel:
    - Finds by tool_use_id
    - Sets tool_output
    - Sets status: "completed" or "failed"
    - Sets is_error
    - Sets completed_at
    """
    stmt = (
        update(ToolCallModel)
        .where(
            ToolCallModel.session_id == session_id,
            ToolCallModel.tool_use_id == block.tool_use_id,
        )
        .values(
            tool_output={"content": block.content},
            status="failed" if block.is_error else "completed",
            is_error=block.is_error,
            completed_at=datetime.utcnow(),
        )
        .returning(ToolCallModel)
    )
    result = await db.execute(stmt)
    updated_tool_call = result.scalar_one_or_none()
```

### StreamHandler

**File**: [app/claude_sdk/handlers/stream_handler.py](../../app/claude_sdk/handlers/stream_handler.py)

**Purpose**: Handle StreamEvent for partial message updates during streaming.

```python
# Lines 16-126
class StreamHandler:
    """Handle StreamEvent for partial message updates."""

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        event_broadcaster: Optional[Any] = None,
    ):
        self.db = db
        self.message_repo = message_repo
        self.event_broadcaster = event_broadcaster

    async def handle_stream_event(
        self, event: StreamEvent, session_id: UUID
    ) -> Dict[str, Any]:
        """Process streaming event and broadcast partial update.

        Flow:
        1. Extract event data from StreamEvent
        2. Create partial message representation
        3. Broadcast to WebSocket clients (if broadcaster available)
        4. Return partial message dict

        Note: Partial messages are not persisted to database.
        Only complete AssistantMessage is persisted.

        Returns:
            Dict with partial message data
        """
        event_type = event.event.get("type", "unknown")
        event_data = event.event

        # Create partial message
        partial_message = {
            "session_id": str(session_id),
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast to WebSocket clients
        if self.event_broadcaster:
            try:
                await self.event_broadcaster.broadcast(
                    session_id=session_id,
                    event_type="partial_message",
                    data=partial_message,
                )
            except Exception as e:
                logger.error(f"Failed to broadcast stream event: {str(e)}")

        return partial_message

    async def aggregate_partial_messages(
        self, session_id: UUID, parent_message_id: Optional[UUID] = None
    ) -> Optional[DomainMessage]:
        """Aggregate all partial messages into complete message.

        TODO: Not yet fully implemented (Phase 3 feature)

        Would query partial messages from database and combine them
        into a final message.
        """
        logger.warning("Partial message aggregation not yet fully implemented")
        return None
```

### ResultHandler

**File**: [app/claude_sdk/handlers/result_handler.py](../../app/claude_sdk/handlers/result_handler.py)

**Purpose**: Process ResultMessage and finalize session metrics.

```python
# Lines 17-163
class ResultHandler:
    """Process ResultMessage and finalize session metrics."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        metrics_repo: SessionMetricsSnapshotRepository,
    ):
        self.db = db
        self.session_repo = session_repo
        self.metrics_repo = metrics_repo

    async def handle_result_message(
        self, message: ResultMessage, session_id: UUID
    ) -> ClientMetrics:
        """Process final result and persist metrics.

        Flow:
        1. Create ClientMetrics object from ResultMessage

        2. Extract token usage from api_usage:
           - input_tokens
           - output_tokens
           - cache_creation_input_tokens
           - cache_read_input_tokens

        3. Mark metrics as completed

        4. Update session in database:
           - status: "completed"
           - duration_ms
           - total_cost_usd
           - token counts
           - completed_at

        5. Create metrics snapshot for historical tracking

        Returns:
            ClientMetrics: Final session metrics
        """

# Lines 48-122
async def handle_result_message(self, message, session_id):
    # 1. Create metrics
    metrics = ClientMetrics(
        session_id=session_id,
        total_duration_ms=message.duration_ms,
        total_cost_usd=Decimal(str(message.total_cost_usd)) if message.total_cost_usd else Decimal("0.0"),
    )

    # 2. Extract token usage
    if hasattr(message, "api_usage") and message.api_usage:
        usage = message.api_usage
        metrics.total_input_tokens = usage.get("input_tokens", 0)
        metrics.total_output_tokens = usage.get("output_tokens", 0)
        metrics.total_cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
        metrics.total_cache_read_tokens = usage.get("cache_read_input_tokens", 0)

    # 3. Mark completed
    metrics.mark_completed()

    # 4. Update session
    update_stmt = (
        update(SessionModel)
        .where(SessionModel.id == session_id)
        .values(
            status="completed",
            duration_ms=message.duration_ms,
            total_cost_usd=float(metrics.total_cost_usd),
            api_input_tokens=metrics.total_input_tokens,
            api_output_tokens=metrics.total_output_tokens,
            api_cache_creation_tokens=metrics.total_cache_creation_tokens,
            api_cache_read_tokens=metrics.total_cache_read_tokens,
            completed_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    await db.execute(update_stmt)
    await db.flush()

    # 5. Create metrics snapshot
    await create_metrics_snapshot(session_id, metrics)

    return metrics

# Lines 124-162
async def create_metrics_snapshot(self, session_id, metrics):
    """Save metrics snapshot for historical tracking."""
    snapshot = SessionMetricsSnapshotModel(
        session_id=session_id,
        snapshot_time=datetime.utcnow(),
        total_messages=metrics.total_messages,
        total_tool_calls=metrics.total_tool_calls,
        total_errors=metrics.total_errors,
        total_retries=metrics.total_retries,
        total_cost_usd=float(metrics.total_cost_usd),
        api_input_tokens=metrics.total_input_tokens,
        api_output_tokens=metrics.total_output_tokens,
        api_cache_creation_tokens=metrics.total_cache_creation_tokens,
        api_cache_read_tokens=metrics.total_cache_read_tokens,
        duration_ms=metrics.total_duration_ms,
    )
    db.add(snapshot)
    await db.flush()
```

### ErrorHandler

**File**: [app/claude_sdk/handlers/error_handler.py](../../app/claude_sdk/handlers/error_handler.py)

**Purpose**: Centralize error handling and recovery logic.

```python
# Lines 16-179
class ErrorHandler:
    """Centralized error handling and recovery logic."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.session_repo = session_repo
        self.audit_service = audit_service

    async def handle_sdk_error(
        self, error: Exception, session_id: UUID, context: Dict[str, Any]
    ) -> None:
        """Handle SDK errors and update session state.

        Flow:
        1. Extract error type and message
        2. Update session status to "failed"
        3. Log error to audit trail

        Args:
            error: Exception that occurred
            session_id: Session identifier
            context: Additional context (prompt, etc.)
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Update session
        update_stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                status="failed",
                error_message=error_message,
                updated_at=datetime.utcnow(),
            )
        )
        await db.execute(update_stmt)
        await db.flush()

        # Log to audit trail
        await log_error(error, session_id, context)

    def is_retryable(self, error: Exception) -> bool:
        """Determine if error is retryable."""
        if isinstance(error, CLIConnectionError):
            return True  # Transient
        if isinstance(error, ClaudeSDKError):
            return False  # Permanent
        return False  # Unknown = not retryable

    def classify_error(self, error: Exception) -> Dict[str, Any]:
        """Classify error with details."""
        return {
            "type": type(error).__name__,
            "message": str(error),
            "is_retryable": self.is_retryable(error),
            "category": "connection" if isinstance(error, CLIConnectionError)
                       else "sdk" if isinstance(error, ClaudeSDKError)
                       else "unknown",
            "severity": "warning" if isinstance(error, CLIConnectionError) else "error"
        }
```

## Message Processing Flow

### Complete Message Processing Pipeline

```
SDK sends message
  ↓
client.receive_response() yields message
  ↓
Executor receives message
  ↓
┌───────────────────────────────────────────────────────────┐
│ Type-based routing in executor                            │
├───────────────────────────────────────────────────────────┤
│                                                            │
│ if isinstance(message, AssistantMessage):                 │
│   ↓                                                        │
│   MessageHandler.handle_assistant_message()               │
│     ├─> Extract content blocks                            │
│     │     ├─> TextBlock → text_content                    │
│     │     ├─> ThinkingBlock → thinking_content            │
│     │     ├─> ToolUseBlock → tool_use_blocks              │
│     │     └─> ToolResultBlock → tool_result_blocks        │
│     │                                                      │
│     ├─> Create MessageModel                               │
│     │     ├─> id: UUID                                    │
│     │     ├─> session_id                                  │
│     │     ├─> message_type: "assistant"                   │
│     │     ├─> content: combined text                      │
│     │     ├─> sequence_number: auto-increment             │
│     │     ├─> model: "claude-sonnet-4-5"                  │
│     │     ├─> thinking_content: combined thinking         │
│     │     └─> is_partial: False                           │
│     │                                                      │
│     ├─> For each ToolUseBlock:                            │
│     │     └─> Create ToolCallModel                        │
│     │           ├─> tool_name: block.name                 │
│     │           ├─> tool_use_id: block.id                 │
│     │           ├─> tool_input: block.input               │
│     │           └─> status: "pending"                     │
│     │                                                      │
│     ├─> For each ToolResultBlock:                         │
│     │     └─> Update ToolCallModel (by tool_use_id)       │
│     │           ├─> tool_output: block.content            │
│     │           ├─> status: "completed" or "failed"       │
│     │           ├─> is_error: block.is_error              │
│     │           └─> completed_at: now                     │
│     │                                                      │
│     └─> Return DomainMessage entity                       │
│   ↓                                                        │
│   Yield domain_message to caller                          │
│                                                            │
│ elif isinstance(message, StreamEvent):                    │
│   ↓                                                        │
│   StreamHandler.handle_stream_event()                     │
│     ├─> Extract event data                                │
│     ├─> Create partial_message dict                       │
│     ├─> Broadcast to WebSocket clients                    │
│     │     └─> event_broadcaster.broadcast(               │
│     │           session_id,                                │
│     │           event_type="partial_message",             │
│     │           data=partial_message                      │
│     │         )                                            │
│     └─> Return partial_message                            │
│   ↓                                                        │
│   (No yield - partial messages not exposed to caller)     │
│                                                            │
│ elif isinstance(message, ResultMessage):                  │
│   ↓                                                        │
│   ResultHandler.handle_result_message()                   │
│     ├─> Create ClientMetrics from ResultMessage           │
│     │     ├─> duration_ms                                 │
│     │     ├─> total_cost_usd                              │
│     │     └─> token counts (input, output, cache)         │
│     │                                                      │
│     ├─> Update SessionModel                               │
│     │     ├─> status: "completed"                         │
│     │     ├─> duration_ms                                 │
│     │     ├─> total_cost_usd                              │
│     │     ├─> api_input_tokens                            │
│     │     ├─> api_output_tokens                           │
│     │     ├─> api_cache_creation_tokens                   │
│     │     ├─> api_cache_read_tokens                       │
│     │     └─> completed_at: now                           │
│     │                                                      │
│     ├─> Create SessionMetricsSnapshotModel                │
│     │     └─> Snapshot all metrics for historical record  │
│     │                                                      │
│     └─> Return ClientMetrics                              │
│   ↓                                                        │
│   Break loop (end of stream)                              │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

## Phase 1: MessageProcessor (Legacy)

**File**: [app/claude_sdk/message_processor.py](../../app/claude_sdk/message_processor.py)

**Purpose**: Legacy all-in-one message processor with broader responsibilities.

Combines functionality of MessageHandler, StreamHandler, ResultHandler, and EventBroadcaster into a single class. Still used in some parts of the codebase.

```python
class MessageProcessor:
    """Legacy message processor (Phase 1)."""

    async def process_assistant_message(self, message, session_id):
        """Process assistant message with persistence and broadcasting."""

    async def process_stream_event(self, event, session_id):
        """Process streaming event."""

    async def update_session_metrics(self, session_id, result_message):
        """Update session with final metrics."""

    async def broadcast_message(self, session_id, message):
        """Broadcast message to WebSocket clients."""
```

## Database Schema

### MessageModel

```python
class MessageModel:
    id: UUID                        # Primary key
    session_id: UUID                # Foreign key to sessions
    message_type: str               # "user" | "assistant" | "system"
    content: str                    # Combined text content
    sequence_number: int            # Order within session
    model: Optional[str]            # "claude-sonnet-4-5"
    thinking_content: Optional[str] # Extended thinking blocks
    is_partial: bool                # Whether message is partial (streaming)
    metadata: Optional[dict]        # Additional metadata
    created_at: datetime
```

### ToolCallModel

```python
class ToolCallModel:
    id: UUID                   # Primary key
    session_id: UUID           # Foreign key to sessions
    message_id: UUID           # Foreign key to messages
    tool_name: str             # "Bash", "Read", "Write", etc.
    tool_use_id: str           # SDK tool use identifier
    tool_input: dict           # Tool input parameters
    tool_output: Optional[dict] # Tool execution result
    status: str                # "pending" | "completed" | "failed"
    is_error: bool             # Whether tool execution failed
    created_at: datetime
    completed_at: Optional[datetime]
```

### SessionMetricsSnapshotModel

```python
class SessionMetricsSnapshotModel:
    id: UUID                        # Primary key
    session_id: UUID                # Foreign key to sessions
    snapshot_time: datetime         # When snapshot was taken
    total_messages: int
    total_tool_calls: int
    total_errors: int
    total_retries: int
    total_cost_usd: float
    api_input_tokens: int
    api_output_tokens: int
    api_cache_creation_tokens: int
    api_cache_read_tokens: int
    duration_ms: int
```

## WebSocket Event Broadcasting

### EventBroadcaster Integration

```python
# In InteractiveExecutor
if self.event_broadcaster:
    await self.event_broadcaster.broadcast(
        session_id=session_id,
        event_type="message",  # or "partial_message"
        data={
            "message": domain_message.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### Event Types

| Event Type | When Fired | Data Payload |
|------------|-----------|--------------|
| `message` | Complete AssistantMessage processed | DomainMessage dict |
| `partial_message` | StreamEvent received | StreamEvent data |
| `result` | ResultMessage received | ClientMetrics dict |
| `error` | Error occurred | Error details |

## Common Tasks

### How to Process Messages in an Executor

```python
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.stream_handler import StreamHandler
from app.claude_sdk.handlers.result_handler import ResultHandler

# Create handlers
message_handler = MessageHandler(db, message_repo, tool_call_repo)
stream_handler = StreamHandler(db, message_repo, event_broadcaster)
result_handler = ResultHandler(db, session_repo, metrics_repo)

# Process messages from SDK
async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        domain_message = await message_handler.handle_assistant_message(
            message, session_id
        )
        yield domain_message

    elif isinstance(message, StreamEvent):
        await stream_handler.handle_stream_event(message, session_id)
        # Partial messages broadcast but not yielded

    elif isinstance(message, ResultMessage):
        metrics = await result_handler.handle_result_message(message, session_id)
        break  # End of stream
```

### How to Query Message History

```python
from app.repositories.message_repository import MessageRepository

message_repo = MessageRepository(db)

# Get all messages for session
messages = await message_repo.get_by_session(session_id)

for msg in messages:
    print(f"[{msg.sequence_number}] {msg.message_type}: {msg.content[:100]}")

# Get specific message
message = await message_repo.get_by_id(message_id)

# Get messages with pagination
messages = await message_repo.get_by_session(session_id, limit=10, offset=20)
```

### How to Track Tool Calls

```python
from app.repositories.tool_call_repository import ToolCallRepository

tool_call_repo = ToolCallRepository(db)

# Get all tool calls for session
tool_calls = await tool_call_repo.get_by_session(session_id)

for tool_call in tool_calls:
    print(f"{tool_call.tool_name}: {tool_call.status}")
    if tool_call.is_error:
        print(f"  Error: {tool_call.tool_output}")

# Get pending tool calls
pending = await tool_call_repo.get_pending(session_id)

# Get completed tool calls
completed = await tool_call_repo.get_completed(session_id)
```

### How to Access Session Metrics

```python
from app.repositories.session_metrics_snapshot_repository import SessionMetricsSnapshotRepository

metrics_repo = SessionMetricsSnapshotRepository(db)

# Get all snapshots for session
snapshots = await metrics_repo.get_by_session(session_id)

# Get latest snapshot
latest = await metrics_repo.get_latest(session_id)

print(f"Total cost: ${latest.total_cost_usd}")
print(f"Total tokens: {latest.api_input_tokens + latest.api_output_tokens}")
print(f"Cache read: {latest.api_cache_read_tokens}")
```

## Related Files

**Phase 2 (NEW) - Handlers**:
- [app/claude_sdk/handlers/message_handler.py](../../app/claude_sdk/handlers/message_handler.py) - AssistantMessage processing
- [app/claude_sdk/handlers/stream_handler.py](../../app/claude_sdk/handlers/stream_handler.py) - StreamEvent handling
- [app/claude_sdk/handlers/result_handler.py](../../app/claude_sdk/handlers/result_handler.py) - ResultMessage processing
- [app/claude_sdk/handlers/error_handler.py](../../app/claude_sdk/handlers/error_handler.py) - Error handling

**Phase 1 (Legacy)**:
- [app/claude_sdk/message_processor.py](../../app/claude_sdk/message_processor.py) - All-in-one processor

**Dependencies**:
- [app/repositories/message_repository.py](../../app/repositories/message_repository.py) - Message persistence
- [app/repositories/tool_call_repository.py](../../app/repositories/tool_call_repository.py) - Tool call persistence
- [app/repositories/session_metrics_snapshot_repository.py](../../app/repositories/session_metrics_snapshot_repository.py) - Metrics snapshots
- [app/models/message.py](../../app/models/message.py) - Message model
- [app/models/tool_call.py](../../app/models/tool_call.py) - Tool call model
- [app/models/session_metrics_snapshot.py](../../app/models/session_metrics_snapshot.py) - Metrics snapshot model
- [app/domain/value_objects/message.py](../../app/domain/value_objects/message.py) - Domain message entity

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - How executors use handlers
- [CLIENT_MANAGEMENT.md](./CLIENT_MANAGEMENT.md) - Client lifecycle

## Keywords

message-processing, message-handler, stream-handler, result-handler, error-handler, message-processor, assistant-message, stream-event, result-message, content-blocks, text-block, tool-use-block, tool-result-block, thinking-block, message-persistence, tool-call-tracking, session-metrics, metrics-snapshot, websocket-broadcasting, event-broadcaster, partial-messages, streaming-messages, message-sequence, tool-execution-tracking, error-classification, domain-message, message-repository, tool-call-repository, metrics-repository
