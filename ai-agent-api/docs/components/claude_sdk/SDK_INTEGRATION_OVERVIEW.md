# Claude SDK Integration Overview

## Purpose

The Claude SDK Integration layer is the **most critical component** of the AI-Agent-API service. It wraps the official `claude-agent-sdk` Python package and provides a production-ready integration with comprehensive features including execution strategies, permission policies, lifecycle hooks, circuit breakers, and message processing.

This integration transforms the raw SDK into a full-featured session management system with enterprise-level capabilities for security, observability, and reliability.

## High-Level Architecture

The Claude SDK integration is organized into **three evolutionary phases**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI-Agent-API Service                        │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer (SDKIntegratedSessionService)                    │
│    ↓                                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │        Claude SDK Integration Layer                     │    │
│  │                                                          │    │
│  │  Phase 1 (Legacy):                                      │    │
│  │    • ClaudeSDKClientManager                             │    │
│  │    • PermissionService                                  │    │
│  │    • hook_handlers (factory functions)                  │    │
│  │    • MessageProcessor                                   │    │
│  │                                                          │    │
│  │  Phase 2 (Core):                                        │    │
│  │    • core/ - EnhancedClaudeClient, SessionManager       │    │
│  │    • execution/ - Executor strategies                   │    │
│  │    • handlers/ - Message/Stream/Result/Error            │    │
│  │    • retry/ - RetryManager, CircuitBreaker              │    │
│  │                                                          │    │
│  │  Phase 3 (Advanced):                                    │    │
│  │    • hooks/ - HookManager, BaseHook, implementations    │    │
│  │    • permissions/ - PolicyEngine, BasePolicy, policies  │    │
│  │    • mcp/ - MCP server integration                      │    │
│  │    • persistence/ - Session/metrics persistence         │    │
│  │    • monitoring/ - Cost tracking, health checks         │    │
│  └────────────────────────────────────────────────────────┘    │
│    ↓                                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Official Claude Agent SDK                       │    │
│  │         (claude-agent-sdk)                              │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Three-Phase Evolution

### Phase 1: Legacy Components (Still in Use)

These were the initial integration components built directly on the SDK patterns:

#### [client_manager.py](../../app/claude_sdk/client_manager.py)
- **Purpose**: Manages pool of ClaudeSDKClient instances (one per session)
- **Responsibilities**:
  - Creates and connects SDK clients
  - Converts domain Session entities to ClaudeAgentOptions
  - Manages client lifecycle (create, get, disconnect)
  - Background task management
- **Key Classes**: `ClaudeSDKClientManager`

#### [permission_service.py](../../app/claude_sdk/permission_service.py)
- **Purpose**: Provides permission callbacks for tool execution
- **Responsibilities**:
  - Checks Bash command permissions (dangerous pattern detection)
  - Validates file write permissions (path restrictions)
  - MCP tool access control
  - Audit logging of permission decisions
- **Key Classes**: `PermissionService`

#### [hook_handlers.py](../../app/claude_sdk/hook_handlers.py)
- **Purpose**: Factory functions for creating SDK hooks
- **Responsibilities**:
  - Creates audit hooks for tool tracking
  - Creates cost tracking hooks
  - Creates validation hooks for prompt security
  - Creates rate limiting hooks
  - Creates notification and webhook hooks
- **Key Functions**: `create_audit_hook`, `create_tool_tracking_hook`, `create_cost_tracking_hook`, etc.

#### [message_processor.py](../../app/claude_sdk/message_processor.py)
- **Purpose**: Processes message streams from SDK
- **Responsibilities**:
  - Converts SDK messages to domain entities
  - Persists messages to database
  - Extracts tool calls from message blocks
  - Updates session metrics (cost, tokens)
  - WebSocket event broadcasting
- **Key Classes**: `MessageProcessor`, `EventBroadcaster`

### Phase 2: Core Components (NEW Architecture)

Phase 2 introduces a cleaner, more modular architecture with clear separation of concerns:

#### core/ - Client & Session Management
- **[config.py](../../app/claude_sdk/core/config.py)**: Configuration dataclasses
  - `ClientConfig`: SDK client configuration
  - `ClientMetrics`: Session metrics tracking
  - `ClientState`: Connection state enum
- **[client.py](../../app/claude_sdk/core/client.py)**: Enhanced SDK client
  - `EnhancedClaudeClient`: Wraps ClaudeSDKClient with retry logic and metrics
- **[session_manager.py](../../app/claude_sdk/core/session_manager.py)**: Session lifecycle
  - `SessionManager`: Create, resume, fork, archive sessions
- **[options_builder.py](../../app/claude_sdk/core/options_builder.py)**: Configuration builder
  - `OptionsBuilder`: Converts domain entities to ClaudeAgentOptions

#### execution/ - Execution Strategies
- **[base_executor.py](../../app/claude_sdk/execution/base_executor.py)**: Abstract base class
  - `BaseExecutor`: Common interface for all executors
- **[interactive_executor.py](../../app/claude_sdk/execution/interactive_executor.py)**: Real-time chat
  - `InteractiveExecutor`: Streaming responses for UI
- **[background_executor.py](../../app/claude_sdk/execution/background_executor.py)**: Automation
  - `BackgroundExecutor`: Non-streaming execution with retry
  - `ExecutionResult`: Result dataclass
- **[forked_executor.py](../../app/claude_sdk/execution/forked_executor.py)**: Session forking
  - `ForkedExecutor`: Continue from parent session
- **[executor_factory.py](../../app/claude_sdk/execution/executor_factory.py)**: Factory pattern
  - `ExecutorFactory`: Creates appropriate executor based on SessionMode

#### handlers/ - Message Processing Pipeline
- **[message_handler.py](../../app/claude_sdk/handlers/message_handler.py)**: Process AssistantMessage
  - `MessageHandler`: Extracts content blocks, persists messages
- **[stream_handler.py](../../app/claude_sdk/handlers/stream_handler.py)**: Streaming events
  - `StreamHandler`: Processes StreamEvent for partial updates
- **[result_handler.py](../../app/claude_sdk/handlers/result_handler.py)**: Final results
  - `ResultHandler`: Extracts metrics from ResultMessage
- **[error_handler.py](../../app/claude_sdk/handlers/error_handler.py)**: Error handling
  - `ErrorHandler`: Classifies errors, updates session state

#### retry/ - Resilience & Reliability
- **[retry_manager.py](../../app/claude_sdk/retry/retry_manager.py)**: Retry logic
  - `RetryManager`: Executes operations with exponential backoff
  - `RetryPolicy`: Configuration for retry behavior
- **[circuit_breaker.py](../../app/claude_sdk/retry/circuit_breaker.py)**: Failure protection
  - `CircuitBreaker`: Prevents cascading failures
  - `CircuitBreakerState`: CLOSED/OPEN/HALF_OPEN states

### Phase 3: Advanced Features (NEW Architecture)

Phase 3 adds enterprise-grade features for observability and control:

#### hooks/ - Lifecycle Hook System
- **[base_hook.py](../../app/claude_sdk/hooks/base_hook.py)**: Hook interface
  - `BaseHook`: Abstract base class for hooks
  - `HookType`: Enum of hook types (PreToolUse, PostToolUse, etc.)
- **[hook_manager.py](../../app/claude_sdk/hooks/hook_manager.py)**: Orchestration
  - `HookManager`: Registers and executes hooks
- **[hook_registry.py](../../app/claude_sdk/hooks/hook_registry.py)**: Registration
  - `HookRegistry`: Maintains hook registry by type
- **implementations/** - Built-in hooks
  - `AuditHook`: Comprehensive audit logging
  - `MetricsHook`: Tool usage statistics
  - `ValidationHook`: Prompt security validation
  - `NotificationHook`: Event notifications

#### permissions/ - Policy-Based Access Control
- **[base_policy.py](../../app/claude_sdk/permissions/base_policy.py)**: Policy interface
  - `BasePolicy`: Abstract base class for policies
- **[policy_engine.py](../../app/claude_sdk/permissions/policy_engine.py)**: Evaluation engine
  - `PolicyEngine`: Evaluates policies in priority order
- **[permission_manager.py](../../app/claude_sdk/permissions/permission_manager.py)**: Orchestration
  - `PermissionManager`: Creates SDK callbacks, logs decisions
- **policies/** - Built-in policies
  - `FileAccessPolicy`: Restricts file operations
  - `CommandPolicy`: Whitelists/blacklists commands
  - `NetworkPolicy`: URL restrictions
  - `ToolWhitelistPolicy`: Allowed tools only
  - `ToolBlacklistPolicy`: Block specific tools

#### mcp/ - Model Context Protocol Integration
- **[mcp_server_manager.py](../../app/claude_sdk/mcp/mcp_server_manager.py)**: MCP server lifecycle
- **[mcp_server_config.py](../../app/claude_sdk/mcp/mcp_server_config.py)**: Configuration
- **[tool_registry.py](../../app/claude_sdk/mcp/tool_registry.py)**: Tool discovery

#### persistence/ - Data Persistence
- **[session_persister.py](../../app/claude_sdk/persistence/session_persister.py)**: Session snapshots
- **[metrics_persister.py](../../app/claude_sdk/persistence/metrics_persister.py)**: Metrics snapshots
- **[storage_archiver.py](../../app/claude_sdk/persistence/storage_archiver.py)**: Working directory archival to S3

#### monitoring/ - Observability
- **[cost_tracker.py](../../app/claude_sdk/monitoring/cost_tracker.py)**: Cost tracking
- **[metrics_collector.py](../../app/claude_sdk/monitoring/metrics_collector.py)**: Metrics aggregation
- **[health_checker.py](../../app/claude_sdk/monitoring/health_checker.py)**: Health monitoring

## Component Relationships

The components interact in a layered dependency graph:

```
Service Layer
  └─> ExecutorFactory
        ├─> BaseExecutor (InteractiveExecutor | BackgroundExecutor | ForkedExecutor)
        │     ├─> EnhancedClaudeClient
        │     │     ├─> OptionsBuilder → ClaudeAgentOptions
        │     │     └─> RetryManager → CircuitBreaker
        │     ├─> MessageHandler → MessageRepository, ToolCallRepository
        │     ├─> StreamHandler → EventBroadcaster
        │     ├─> ResultHandler → SessionRepository, MetricsRepository
        │     └─> ErrorHandler → AuditService
        │
        ├─> HookManager
        │     ├─> HookRegistry
        │     └─> Hook Implementations (AuditHook, MetricsHook, etc.)
        │
        └─> PermissionManager
              ├─> PolicyEngine
              └─> Policy Implementations (FileAccessPolicy, CommandPolicy, etc.)
```

## Entry Points

### From Service Layer

The primary entry point is `SDKIntegratedSessionService.execute_query()`:

```python
# From app/services/sdk_session_service.py:179-205
async def execute_query(self, session_id: UUID, query: str):
    """Execute query using appropriate executor strategy."""

    # 1. Get session from database
    session = await self.session_repository.get_by_id(session_id)

    # 2. Create executor via factory (handles all dependency injection)
    executor = await ExecutorFactory.create_executor(
        session=session,
        db=self.db,
        event_broadcaster=self.event_broadcaster
    )

    # 3. Execute query with strategy-specific behavior
    if session.mode == SessionMode.INTERACTIVE:
        # Returns AsyncIterator[Message] for streaming
        async for message in executor.execute(query):
            yield message
    else:
        # Returns ExecutionResult for background tasks
        result = await executor.execute(query)
        return result
```

### Key Workflows

#### 1. Session Creation → Client Initialization

```
User Request
  → SessionService.create_session()
  → SessionManager.create_session()
      → ClientConfig builder
      → EnhancedClaudeClient(config)
      → client.connect()  # with retry logic
      → Register in active_clients
```

#### 2. Query Execution → Full Pipeline

```
User Query
  → ExecutorFactory.create_executor()
      ├─> Create EnhancedClaudeClient
      ├─> Register Hooks (HookManager)
      ├─> Register Policies (PermissionManager)
      ├─> Create Handlers (Message, Stream, Result, Error)
      └─> Instantiate Executor (Interactive | Background | Forked)

  → Executor.execute(prompt)
      ├─> client.query(prompt)  # Send to SDK
      │
      ├─> client.receive_response()  # Stream from SDK
      │     │
      │     ├─> For each message:
      │     │     │
      │     │     ├─> HookManager.execute_hooks(PreToolUse)
      │     │     │     └─> AuditHook, ValidationHook, etc.
      │     │     │
      │     │     ├─> PermissionManager.can_use_tool()
      │     │     │     └─> PolicyEngine.evaluate()
      │     │     │           └─> FileAccessPolicy, CommandPolicy, etc.
      │     │     │
      │     │     ├─> MessageHandler.handle_assistant_message()
      │     │     │     ├─> Parse content blocks
      │     │     │     ├─> Persist to message table
      │     │     │     └─> Extract tool calls
      │     │     │
      │     │     ├─> StreamHandler.handle_stream_event()
      │     │     │     └─> Broadcast to WebSocket clients
      │     │     │
      │     │     ├─> HookManager.execute_hooks(PostToolUse)
      │     │     │     └─> MetricsHook, NotificationHook, etc.
      │     │     │
      │     │     └─> ResultHandler.handle_result_message()
      │     │           ├─> Extract metrics (cost, tokens)
      │     │           ├─> Update session
      │     │           └─> Create metrics snapshot
      │     │
      │     └─> Yield domain message to caller
      │
      └─> ErrorHandler.handle_sdk_error()  # On exceptions
            ├─> Update session status to failed
            ├─> Log to audit trail
            └─> Classify error (retryable vs permanent)
```

## Configuration & Options

The SDK integration uses a multi-layer configuration approach:

### Domain Session Entity
```python
# app/domain/entities/session.py
class Session:
    mode: SessionMode  # INTERACTIVE | BACKGROUND | FORKED
    permission_mode: str  # "default" | "strict" | "custom"
    sdk_options: dict  # Raw SDK configuration
    hooks_enabled: list[str]  # Hook types to enable
    include_partial_messages: bool  # Enable streaming
    max_retries: int
    retry_delay: float
    timeout_seconds: int
    working_directory_path: str
```

### ClientConfig (Phase 2)
```python
# app/claude_sdk/core/config.py:22-41
@dataclass
class ClientConfig:
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
    hooks: Optional[Dict[str, List[Any]]]  # HookMatcher
    can_use_tool: Optional[Callable]  # Permission callback
```

### ClaudeAgentOptions (SDK)
```python
# Built by OptionsBuilder.build() from Session
ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    permission_mode="default",
    max_turns=10,
    cwd=Path("/workspace/session_123"),
    allowed_tools=["Bash", "Read", "Write"],
    can_use_tool=permission_callback,  # From PermissionManager
    hooks={  # From HookManager
        "PreToolUse": [HookMatcher(hooks=[...])],
        "PostToolUse": [HookMatcher(hooks=[...])]
    },
    mcp_servers={"server_name": {...}},
    include_partial_messages=True
)
```

## Extension Points

The SDK integration provides multiple extension points for customization:

### 1. Custom Executors
Extend `BaseExecutor` to implement new execution strategies:
```python
from app.claude_sdk.execution.base_executor import BaseExecutor

class MyCustomExecutor(BaseExecutor):
    async def execute(self, prompt: str) -> Any:
        # Custom execution logic
        pass
```

### 2. Custom Hooks
Implement `BaseHook` to add custom lifecycle hooks:
```python
from app.claude_sdk.hooks.base_hook import BaseHook, HookType

class MyCustomHook(BaseHook):
    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    async def execute(self, input_data, tool_use_id, context):
        # Custom hook logic
        return {"continue_": True}
```

### 3. Custom Policies
Implement `BasePolicy` to add custom permission policies:
```python
from app.claude_sdk.permissions.base_policy import BasePolicy

class MyCustomPolicy(BasePolicy):
    @property
    def policy_name(self) -> str:
        return "my_custom_policy"

    async def evaluate(self, tool_name, input_data, context):
        # Custom policy logic
        if should_allow:
            return PermissionResultAllow()
        else:
            return PermissionResultDeny(message="Reason")
```

### 4. Custom Handlers
Extend handlers to customize message processing:
```python
from app.claude_sdk.handlers.message_handler import MessageHandler

class MyCustomMessageHandler(MessageHandler):
    async def handle_assistant_message(self, message, session_id):
        # Custom processing before/after base handler
        result = await super().handle_assistant_message(message, session_id)
        # Additional custom logic
        return result
```

## Exception Hierarchy

```python
# app/claude_sdk/exceptions.py
SDKError (base)
  ├─> ClientAlreadyExistsError
  ├─> ClientNotFoundError
  ├─> SDKConnectionError (transient - retryable)
  ├─> SDKRuntimeError (permanent - not retryable)
  ├─> PermissionDeniedError
  └─> CircuitBreakerOpenError
```

## Common Tasks

### How to Add a New Hook

1. Create hook implementation:
```python
# app/claude_sdk/hooks/implementations/my_hook.py
from app.claude_sdk.hooks.base_hook import BaseHook, HookType

class MyHook(BaseHook):
    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        return 50  # Lower = higher priority

    async def execute(self, input_data, tool_use_id, context):
        # Your logic here
        return {"continue_": True}
```

2. Register in `ExecutorFactory`:
```python
# app/claude_sdk/execution/executor_factory.py:96-99
from app.claude_sdk.hooks.implementations.my_hook import MyHook

my_hook = MyHook()
await hook_manager.register_hook(HookType.PRE_TOOL_USE, my_hook, priority=50)
```

### How to Add a New Policy

1. Create policy implementation:
```python
# app/claude_sdk/permissions/policies/my_policy.py
from app.claude_sdk.permissions.base_policy import BasePolicy

class MyPolicy(BasePolicy):
    @property
    def policy_name(self) -> str:
        return "my_policy"

    async def evaluate(self, tool_name, input_data, context):
        if should_deny:
            return PermissionResultDeny(message="Reason", interrupt=False)
        return PermissionResultAllow()
```

2. Register in `ExecutorFactory`:
```python
# app/claude_sdk/execution/executor_factory.py:134-136
from app.claude_sdk.permissions.policies.my_policy import MyPolicy

policy_engine.register_policy(MyPolicy(...))
```

### How to Add a New Execution Strategy

1. Create executor:
```python
# app/claude_sdk/execution/my_executor.py
from app.claude_sdk.execution.base_executor import BaseExecutor

class MyExecutor(BaseExecutor):
    async def execute(self, prompt: str):
        # Implementation
        pass
```

2. Add to `ExecutorFactory`:
```python
# app/claude_sdk/execution/executor_factory.py:217
elif session.mode == SessionMode.MY_MODE:
    return MyExecutor(...)
```

3. Add mode to `SessionMode` enum:
```python
# app/domain/entities/session.py
class SessionMode(str, Enum):
    MY_MODE = "my_mode"
```

## Related Documentation

- [CLIENT_MANAGEMENT.md](./CLIENT_MANAGEMENT.md) - Client lifecycle and session management
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - Executor pattern implementation
- [PERMISSION_SYSTEM.md](./PERMISSION_SYSTEM.md) - Policy engine and access control
- [HOOK_SYSTEM.md](./HOOK_SYSTEM.md) - Lifecycle hooks and event handling
- [RETRY_RESILIENCE.md](./RETRY_RESILIENCE.md) - Error handling and circuit breakers
- [MESSAGE_PROCESSING.md](./MESSAGE_PROCESSING.md) - Message handling and streaming

## Keywords

claude-sdk, sdk-integration, executor, execution-strategies, hooks, lifecycle-hooks, permissions, policy-engine, access-control, circuit-breaker, retry-logic, message-processing, session-management, client-manager, enhanced-client, phase-1, phase-2, phase-3, claude-agent-sdk, mcp-integration, persistence, monitoring, observability, resilience, reliability, streaming, websocket, real-time, background-execution, forked-sessions, tool-permissions, audit-logging, metrics-tracking, cost-tracking, validation-hooks, notification-hooks, file-access-policy, command-policy, network-policy, tool-whitelist, tool-blacklist
