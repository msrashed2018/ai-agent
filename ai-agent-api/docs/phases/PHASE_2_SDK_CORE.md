# Phase 2: SDK Core Integration & Execution Strategies

**Epic**: Claude SDK Module Rebuild - Core Integration Layer
**Phase**: 2 of 4
**Status**: Pending Phase 1 Completion
**Estimated Effort**: 2 weeks

---

## User Story

**As a** Backend Developer
**I want** a robust Claude SDK integration layer with enhanced client, message handlers, and execution strategies
**So that** I can build interactive chat sessions, background automation tasks, and forked session continuations with proper error handling and retry logic

---

## Business Value

- **Multi-mode execution**: Support chat UI, background tasks, and session forking
- **Production reliability**: Automatic retry, error handling, circuit breaker
- **Real-time streaming**: Enable ChatGPT-like typing effect for better UX
- **Session continuation**: Allow users to fork and continue conversations
- **Developer productivity**: Clean abstractions make it easy to add new features

---

## Acceptance Criteria

### ✅ Core SDK Components (`app/claude_sdk/core/`)
- [ ] `EnhancedClaudeClient` wraps official `ClaudeSDKClient` with retry logic
- [ ] `SessionManager` handles session lifecycle (create, resume, fork, archive)
- [ ] `OptionsBuilder` converts domain config to `ClaudeAgentOptions`
- [ ] `ClientConfig` dataclass for all client configuration
- [ ] `ClientMetrics` tracks session performance (duration, cost, tokens)
- [ ] `ClientState` enum tracks connection state
- [ ] All core components are type-safe with full type hints
- [ ] All core components have comprehensive error handling

### ✅ Message & Event Handlers (`app/claude_sdk/handlers/`)
- [ ] `MessageHandler` processes `AssistantMessage` and extracts content blocks
- [ ] `StreamHandler` handles `StreamEvent` for partial message updates
- [ ] `ResultHandler` processes `ResultMessage` and finalizes metrics
- [ ] `ErrorHandler` centralizes error handling and recovery logic
- [ ] All handlers convert SDK messages to domain entities
- [ ] All handlers trigger persistence via repositories
- [ ] All handlers support WebSocket broadcasting

### ✅ Execution Strategies (`app/claude_sdk/execution/`)
- [ ] `ExecutorFactory` creates appropriate executor based on session mode
- [ ] `InteractiveExecutor` for real-time chat (streaming with partial messages)
- [ ] `BackgroundExecutor` for automation tasks (batch mode, no streaming)
- [ ] `ForkedExecutor` for session continuation (restore context, continue chat)
- [ ] `BaseExecutor` abstract class defines common interface
- [ ] All executors support async iteration for message streaming
- [ ] All executors handle errors gracefully with proper logging

### ✅ Retry & Resilience (`app/claude_sdk/retry/`)
- [ ] `RetryManager` orchestrates retry logic with exponential backoff
- [ ] `RetryPolicy` defines retry configuration (max retries, delays, jitter)
- [ ] `CircuitBreaker` prevents cascading failures
- [ ] Retry only on transient errors (`CLIConnectionError`)
- [ ] Non-retryable errors fail fast
- [ ] Retry attempts logged for debugging

### ✅ Testing
- [ ] Unit tests for `EnhancedClaudeClient` (connect, query, disconnect, retry)
- [ ] Unit tests for `SessionManager` (create, resume, fork, archive)
- [ ] Unit tests for all handlers (message, stream, result, error)
- [ ] Unit tests for all executors (interactive, background, forked)
- [ ] Unit tests for `RetryManager` and `CircuitBreaker`
- [ ] Integration tests for end-to-end execution flows
- [ ] Test coverage ≥ 80%

### ✅ Documentation
- [ ] Core components documented with examples
- [ ] Execution strategies explained with use cases
- [ ] Retry logic documented with configuration options
- [ ] Developer guide for adding custom executors

---

## Technical Tasks

### 1. Core SDK Components

#### 1.1 Create `EnhancedClaudeClient` (`app/claude_sdk/core/client.py`)

```python
@dataclass
class ClientConfig:
    """Configuration for enhanced Claude client."""
    session_id: UUID
    model: str = "claude-sonnet-4-5"
    permission_mode: str = "default"
    max_turns: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout_seconds: int = 120
    include_partial_messages: bool = False
    working_directory: Path
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: Optional[List[str]] = None
    hooks: Optional[Dict[str, List[HookMatcher]]] = None
    can_use_tool: Optional[Callable] = None


@dataclass
class ClientMetrics:
    """Session metrics tracking."""
    session_id: UUID
    total_messages: int = 0
    total_tool_calls: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_cost_usd: Decimal = Decimal("0.0")
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ClientState(str, Enum):
    """Client connection state."""
    CREATED = "created"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class EnhancedClaudeClient:
    """Enhanced wrapper around ClaudeSDKClient with retry and metrics."""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.sdk_client: Optional[ClaudeSDKClient] = None
        self.metrics = ClientMetrics(session_id=config.session_id)
        self.state = ClientState.CREATED
        self.retry_manager: Optional[RetryManager] = None

    async def connect(self) -> None:
        """Connect to Claude Code CLI with retry logic."""

    async def query(self, prompt: str) -> None:
        """Send query with automatic retry on connection errors."""

    async def receive_response(self) -> AsyncIterator[Message]:
        """Stream responses with error handling and metrics tracking."""

    async def disconnect(self) -> ClientMetrics:
        """Disconnect and return final metrics."""

    async def get_metrics(self) -> ClientMetrics:
        """Get current session metrics."""
```

#### 1.2 Create `SessionManager` (`app/claude_sdk/core/session_manager.py`)

```python
class SessionManager:
    """Manages Claude SDK sessions throughout their lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.active_clients: Dict[UUID, EnhancedClaudeClient] = {}

    async def create_session(
        self,
        session_id: UUID,
        mode: SessionMode,
        config: SessionConfiguration
    ) -> EnhancedClaudeClient:
        """Create new Claude SDK session."""

    async def resume_session(
        self,
        session_id: UUID,
        restore_context: bool = True
    ) -> EnhancedClaudeClient:
        """Resume paused or archived session."""

    async def fork_session(
        self,
        parent_session_id: UUID,
        fork_at_message: Optional[int] = None
    ) -> EnhancedClaudeClient:
        """Fork session from specific point in history."""

    async def archive_session(
        self,
        session_id: UUID,
        archive_to_storage: bool = True
    ) -> ArchiveResult:
        """Archive session and upload to S3/storage."""

    async def get_client(self, session_id: UUID) -> Optional[EnhancedClaudeClient]:
        """Get active client for session."""

    async def disconnect_all(self) -> None:
        """Disconnect all active clients."""
```

#### 1.3 Create `OptionsBuilder` (`app/claude_sdk/core/options_builder.py`)

```python
class OptionsBuilder:
    """Build ClaudeAgentOptions from business configuration."""

    def build(
        self,
        session: Session,
        permission_callback: Optional[Callable] = None,
        hooks: Optional[Dict[str, List[HookMatcher]]] = None,
        mcp_servers: Optional[Dict[str, Any]] = None
    ) -> ClaudeAgentOptions:
        """Build SDK options from domain Session entity."""

        return ClaudeAgentOptions(
            model=session.sdk_options.get("model", "claude-sonnet-4-5"),
            permission_mode=session.permission_mode,
            max_turns=session.sdk_options.get("max_turns", 10),
            include_partial_messages=session.include_partial_messages,
            cwd=session.working_directory_path,
            mcp_servers=mcp_servers or {},
            allowed_tools=session.sdk_options.get("allowed_tools"),
            can_use_tool=permission_callback,
            hooks=hooks or {}
        )
```

### 2. Message & Event Handlers

#### 2.1 Create `MessageHandler` (`app/claude_sdk/handlers/message_handler.py`)

```python
class MessageHandler:
    """Process AssistantMessage and extract content blocks."""

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository
    ):
        self.db = db
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo

    async def handle_assistant_message(
        self,
        message: AssistantMessage,
        session_id: UUID
    ) -> AgentMessage:
        """Process AssistantMessage from SDK and persist to database."""

    async def handle_tool_use_block(
        self,
        block: ToolUseBlock,
        session_id: UUID,
        message_id: UUID
    ) -> ToolExecution:
        """Extract and persist tool usage."""

    async def handle_tool_result_block(
        self,
        block: ToolResultBlock,
        session_id: UUID,
        message_id: UUID
    ) -> ToolExecution:
        """Process tool execution result."""

    async def handle_text_block(
        self,
        block: TextBlock,
        session_id: UUID,
        message_id: UUID
    ) -> Dict[str, Any]:
        """Extract text content."""

    async def handle_thinking_block(
        self,
        block: ThinkingBlock,
        session_id: UUID,
        message_id: UUID
    ) -> Dict[str, Any]:
        """Extract thinking content."""
```

#### 2.2 Create `StreamHandler` (`app/claude_sdk/handlers/stream_handler.py`)

```python
class StreamHandler:
    """Handle StreamEvent for partial message updates."""

    def __init__(
        self,
        db: AsyncSession,
        message_repo: MessageRepository,
        event_broadcaster: Optional[EventBroadcaster] = None
    ):
        self.db = db
        self.message_repo = message_repo
        self.event_broadcaster = event_broadcaster

    async def handle_stream_event(
        self,
        event: StreamEvent,
        session_id: UUID
    ) -> PartialMessage:
        """Process streaming event and broadcast partial update."""

    async def aggregate_partial_messages(
        self,
        session_id: UUID,
        parent_message_id: UUID
    ) -> AgentMessage:
        """Aggregate all partial messages into complete message."""
```

#### 2.3 Create `ResultHandler` (`app/claude_sdk/handlers/result_handler.py`)

```python
class ResultHandler:
    """Process ResultMessage and finalize session metrics."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        metrics_repo: SessionMetricsSnapshotRepository
    ):
        self.db = db
        self.session_repo = session_repo
        self.metrics_repo = metrics_repo

    async def handle_result_message(
        self,
        message: ResultMessage,
        session_id: UUID
    ) -> SessionMetrics:
        """Process final result and persist metrics."""

    async def create_metrics_snapshot(
        self,
        session_id: UUID,
        metrics: SessionMetrics
    ) -> None:
        """Save metrics snapshot for historical tracking."""
```

#### 2.4 Create `ErrorHandler` (`app/claude_sdk/handlers/error_handler.py`)

```python
class ErrorHandler:
    """Centralized error handling and recovery logic."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        audit_service: AuditService
    ):
        self.db = db
        self.session_repo = session_repo
        self.audit_service = audit_service

    async def handle_sdk_error(
        self,
        error: Exception,
        session_id: UUID,
        context: Dict[str, Any]
    ) -> None:
        """Handle SDK errors and update session state."""

    def is_retryable(self, error: Exception) -> bool:
        """Determine if error is retryable."""
        return isinstance(error, CLIConnectionError)

    async def log_error(
        self,
        error: Exception,
        session_id: UUID,
        context: Dict[str, Any]
    ) -> None:
        """Log error to audit trail."""
```

### 3. Execution Strategies

#### 3.1 Create `BaseExecutor` (`app/claude_sdk/execution/base_executor.py`)

```python
class BaseExecutor(ABC):
    """Abstract base class for all executors."""

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler
    ):
        self.session = session
        self.client = client
        self.message_handler = message_handler
        self.result_handler = result_handler
        self.error_handler = error_handler

    @abstractmethod
    async def execute(self, prompt: str) -> Any:
        """Execute query. Returns different types based on executor."""
        pass

    async def _handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Common error handling logic."""
        await self.error_handler.handle_sdk_error(
            error=error,
            session_id=self.session.id,
            context=context
        )
```

#### 3.2 Create `InteractiveExecutor` (`app/claude_sdk/execution/interactive_executor.py`)

```python
class InteractiveExecutor(BaseExecutor):
    """Execute interactive chat sessions with real-time streaming."""

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        stream_handler: StreamHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        event_broadcaster: Optional[EventBroadcaster] = None
    ):
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.stream_handler = stream_handler
        self.event_broadcaster = event_broadcaster

    async def execute(self, prompt: str) -> AsyncIterator[AgentMessage]:
        """Execute query and stream responses in real-time."""

        # Enable partial messages for UI
        self.client.config.include_partial_messages = True

        await self.client.query(prompt)

        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                agent_message = await self.message_handler.handle_assistant_message(
                    message, self.session.id
                )

                # Broadcast to WebSocket
                if self.event_broadcaster:
                    await self.event_broadcaster.broadcast(
                        session_id=self.session.id,
                        event_type="message",
                        data=agent_message
                    )

                yield agent_message

            elif isinstance(message, StreamEvent):
                partial_message = await self.stream_handler.handle_stream_event(
                    message, self.session.id
                )

                # Broadcast partial update
                if self.event_broadcaster:
                    await self.event_broadcaster.broadcast(
                        session_id=self.session.id,
                        event_type="partial_message",
                        data=partial_message
                    )

            elif isinstance(message, ResultMessage):
                await self.result_handler.handle_result_message(
                    message, self.session.id
                )
                break
```

#### 3.3 Create `BackgroundExecutor` (`app/claude_sdk/execution/background_executor.py`)

```python
@dataclass
class ExecutionResult:
    """Background execution result."""
    session_id: UUID
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metrics: ClientMetrics


class BackgroundExecutor(BaseExecutor):
    """Execute background automation tasks without streaming."""

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        retry_manager: RetryManager
    ):
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.retry_manager = retry_manager

    async def execute(self, prompt: str) -> ExecutionResult:
        """Execute task and return final result (no streaming)."""

        # Disable partial messages for background
        self.client.config.include_partial_messages = False

        try:
            # Execute with retry logic
            await self.retry_manager.execute_with_retry(
                lambda: self._execute_query(prompt)
            )

            # Get final metrics
            metrics = await self.client.get_metrics()

            return ExecutionResult(
                session_id=self.session.id,
                success=True,
                data={"status": "completed"},
                error_message=None,
                metrics=metrics
            )

        except Exception as e:
            await self._handle_error(e, {"prompt": prompt})

            return ExecutionResult(
                session_id=self.session.id,
                success=False,
                data=None,
                error_message=str(e),
                metrics=await self.client.get_metrics()
            )

    async def _execute_query(self, prompt: str) -> None:
        """Execute query without streaming."""
        await self.client.query(prompt)

        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                await self.message_handler.handle_assistant_message(
                    message, self.session.id
                )
            elif isinstance(message, ResultMessage):
                await self.result_handler.handle_result_message(
                    message, self.session.id
                )
                break
```

#### 3.4 Create `ForkedExecutor` (`app/claude_sdk/execution/forked_executor.py`)

```python
class ForkedExecutor(BaseExecutor):
    """Execute forked session with restored context."""

    def __init__(
        self,
        session: Session,
        parent_session_id: UUID,
        fork_at_message: Optional[int],
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        message_repo: MessageRepository
    ):
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.parent_session_id = parent_session_id
        self.fork_at_message = fork_at_message
        self.message_repo = message_repo

    async def execute(self, prompt: str) -> AsyncIterator[AgentMessage]:
        """Execute in forked session with restored context."""

        # Restore context from parent session
        await self._restore_context()

        # Continue conversation (same as interactive)
        await self.client.query(prompt)

        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                agent_message = await self.message_handler.handle_assistant_message(
                    message, self.session.id
                )
                yield agent_message

            elif isinstance(message, ResultMessage):
                await self.result_handler.handle_result_message(
                    message, self.session.id
                )
                break

    async def _restore_context(self) -> None:
        """Restore conversation history from parent session."""

        # Retrieve parent session messages
        parent_messages = await self.message_repo.get_session_messages(
            self.parent_session_id,
            limit=self.fork_at_message
        )

        # TODO: Implement context restoration
        # (Depends on SDK's session continuation support)
        logger.info(f"Restoring {len(parent_messages)} messages from parent session")
```

#### 3.5 Create `ExecutorFactory` (`app/claude_sdk/execution/executor_factory.py`)

```python
class ExecutorFactory:
    """Create appropriate executor based on session mode."""

    @staticmethod
    async def create_executor(
        session: Session,
        db: AsyncSession,
        event_broadcaster: Optional[EventBroadcaster] = None
    ) -> BaseExecutor:
        """Factory method to create executor."""

        # Create client
        client_config = ClientConfig(
            session_id=session.id,
            model=session.sdk_options.get("model", "claude-sonnet-4-5"),
            permission_mode=session.permission_mode,
            max_retries=session.max_retries,
            retry_delay=session.retry_delay,
            timeout_seconds=session.timeout_seconds,
            include_partial_messages=session.include_partial_messages,
            working_directory=Path(session.working_directory_path)
        )
        client = EnhancedClaudeClient(client_config)

        # Create handlers
        message_handler = MessageHandler(db, MessageRepository(db), ToolCallRepository(db))
        result_handler = ResultHandler(db, SessionRepository(db), SessionMetricsSnapshotRepository(db))
        error_handler = ErrorHandler(db, SessionRepository(db), AuditService(db))

        # Create appropriate executor
        if session.mode == SessionMode.INTERACTIVE:
            stream_handler = StreamHandler(db, MessageRepository(db), event_broadcaster)
            return InteractiveExecutor(
                session, client, message_handler, stream_handler,
                result_handler, error_handler, event_broadcaster
            )

        elif session.mode == SessionMode.BACKGROUND:
            retry_manager = RetryManager(
                RetryPolicy(max_retries=session.max_retries, base_delay=session.retry_delay)
            )
            return BackgroundExecutor(
                session, client, message_handler,
                result_handler, error_handler, retry_manager
            )

        elif session.mode == SessionMode.FORKED:
            return ForkedExecutor(
                session, session.parent_session_id, None,
                client, message_handler, result_handler,
                error_handler, MessageRepository(db)
            )

        else:
            raise ValueError(f"Unknown session mode: {session.mode}")
```

### 4. Retry & Resilience

#### 4.1 Create `RetryManager` (`app/claude_sdk/retry/retry_manager.py`)

```python
@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_retries: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryManager:
    """Manage retry logic with exponential backoff."""

    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        self.circuit_breaker = CircuitBreaker()

    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with retry logic."""

        for attempt in range(self.policy.max_retries + 1):
            try:
                # Check circuit breaker
                if not self.circuit_breaker.allow_request():
                    raise CircuitBreakerOpenError("Circuit breaker is open")

                # Execute operation
                result = await operation(*args, **kwargs)

                # Success - reset circuit breaker
                self.circuit_breaker.record_success()
                return result

            except CLIConnectionError as e:
                # Transient error - retry
                if attempt < self.policy.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.policy.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    self.circuit_breaker.record_failure()
                    logger.error(f"All {self.policy.max_retries + 1} attempts failed")
                    raise

            except (ClaudeSDKError, Exception) as e:
                # Non-retryable error - fail fast
                self.circuit_breaker.record_failure()
                logger.error(f"Non-retryable error: {e}")
                raise

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.policy.base_delay * (self.policy.exponential_base ** attempt),
            self.policy.max_delay
        )

        if self.policy.jitter:
            # Add random jitter (0-25% of delay)
            import random
            jitter = delay * random.uniform(0, 0.25)
            delay += jitter

        return delay
```

#### 4.2 Create `CircuitBreaker` (`app/claude_sdk/retry/circuit_breaker.py`)

```python
class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout elapsed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0

        self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
```

---

## File Structure (What Gets Created)

```
app/claude_sdk/
├── core/
│   ├── __init__.py                    [NEW]
│   ├── client.py                      [NEW] - EnhancedClaudeClient, ClientConfig, ClientMetrics
│   ├── session_manager.py             [NEW] - SessionManager
│   ├── options_builder.py             [NEW] - OptionsBuilder
│   └── exceptions.py                  [NEW] - SDK-specific exceptions
│
├── handlers/
│   ├── __init__.py                    [NEW]
│   ├── message_handler.py             [NEW] - MessageHandler
│   ├── stream_handler.py              [NEW] - StreamHandler
│   ├── result_handler.py              [NEW] - ResultHandler
│   └── error_handler.py               [NEW] - ErrorHandler
│
├── execution/
│   ├── __init__.py                    [NEW]
│   ├── base_executor.py               [NEW] - BaseExecutor (abstract)
│   ├── interactive_executor.py        [NEW] - InteractiveExecutor
│   ├── background_executor.py         [NEW] - BackgroundExecutor
│   ├── forked_executor.py             [NEW] - ForkedExecutor
│   └── executor_factory.py            [NEW] - ExecutorFactory
│
├── retry/
│   ├── __init__.py                    [NEW]
│   ├── retry_manager.py               [NEW] - RetryManager, RetryPolicy
│   └── circuit_breaker.py             [NEW] - CircuitBreaker
│
└── __init__.py                        [UPDATED] - Export all components

tests/
├── unit/
│   └── claude_sdk/
│       ├── core/
│       │   ├── test_client.py         [NEW]
│       │   ├── test_session_manager.py [NEW]
│       │   └── test_options_builder.py [NEW]
│       ├── handlers/
│       │   ├── test_message_handler.py [NEW]
│       │   ├── test_stream_handler.py [NEW]
│       │   └── test_result_handler.py [NEW]
│       ├── execution/
│       │   ├── test_interactive_executor.py [NEW]
│       │   ├── test_background_executor.py [NEW]
│       │   └── test_forked_executor.py [NEW]
│       └── retry/
│           ├── test_retry_manager.py  [NEW]
│           └── test_circuit_breaker.py [NEW]
│
└── integration/
    └── claude_sdk/
        ├── test_interactive_flow.py   [NEW] - E2E interactive session
        ├── test_background_flow.py    [NEW] - E2E background task
        └── test_forked_flow.py        [NEW] - E2E session forking
```

---

## Dependencies

**Prerequisites**:
- Phase 1 completed (database schema, domain entities, repositories)
- Official `claude-agent-sdk` installed
- All Phase 1 tests passing

**Blocking**:
- Phase 1: Core Foundation & Domain Layer

**Blocked By**:
- None

---

## Reference Materials for Implementers

### Claude SDK Documentation
- **SDK Installation Path**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/`
- **SDK Client Reference**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/client.py`
- **SDK Types Reference**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/types.py`
- **Check these files** to understand:
  - `ClaudeSDKClient` interface (connect, query, receive_response methods)
  - `ClaudeAgentOptions` configuration structure
  - Message flow: `UserMessage` → SDK → `AssistantMessage`/`StreamEvent` → `ResultMessage`
  - Error types: `ClaudeSDKError`, `CLIConnectionError`, `ProcessError`

### Example Usage Scripts
- **Script Directory**: `/workspace/me/repositories/claude-code-sdk-tests/claude-code-sdk-usage-poc/`
- **Critical Scripts to Reference**:
  - `01_basic_hello_world.py` - **START HERE** - Shows basic client usage, message handling
  - `02_interactive_chat.py` - Interactive session pattern (similar to InteractiveExecutor)
  - `07_advanced_streaming.py` - Streaming with `include_partial_messages=True`, StreamEvent handling
  - `08_production_ready.py` - **CRITICAL** - Shows retry logic, error handling, metrics collection, all in production pattern

**Implementation Notes**:
- `EnhancedClaudeClient` should wrap the patterns from `08_production_ready.py`
- `InteractiveExecutor` should follow `02_interactive_chat.py` + `07_advanced_streaming.py` patterns
- `BackgroundExecutor` should follow `08_production_ready.py` pattern (no streaming)
- Message handling should match `04_hook_system.py` (full logging of inputs/outputs)

---

## Testing Strategy

### Unit Tests
- **EnhancedClaudeClient**: Mock `ClaudeSDKClient`, test retry logic
- **SessionManager**: Test session lifecycle methods
- **Handlers**: Mock repositories, test message processing
- **Executors**: Mock client and handlers, test execution flow
- **RetryManager**: Test exponential backoff, jitter, max retries
- **CircuitBreaker**: Test state transitions

### Integration Tests
- **Interactive Flow**: Create session, send query, receive streaming responses
- **Background Flow**: Create session, execute task, get final result
- **Forked Flow**: Create parent session, fork, verify context restoration

### Manual Testing
- Test real Claude SDK integration with actual API calls
- Verify streaming works with WebSocket
- Test error scenarios (connection failures, timeouts)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All technical tasks completed
- [ ] Code reviewed and approved
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥ 80%
- [ ] Documentation complete
- [ ] Integration with Phase 1 components verified
- [ ] Performance benchmarks meet targets

---

## Success Metrics

- ✅ Interactive executor streams messages in real-time (< 100ms latency)
- ✅ Background executor completes tasks without streaming overhead
- ✅ Retry logic recovers from transient failures (95%+ success rate)
- ✅ Circuit breaker prevents cascading failures
- ✅ All executors handle errors gracefully
- ✅ Test coverage ≥ 80%

---

## Next Phase

After Phase 2 completion, proceed to **Phase 3: Advanced Features (Hooks, Permissions, MCP)** which adds extensibility, security, and persistence features.
