# Claude SDK Module Architecture Design

**Version**: 2.0
**Date**: 2025-10-19
**Status**: Architecture Proposal

---

## Executive Summary

This document outlines the complete redesign of the `app/claude_sdk` module to transform it into an enterprise-grade, production-ready integration layer for the Claude Agent SDK. The new design addresses current limitations and provides a flexible, extensible architecture supporting hundreds of use cases across different industries.

### Current Problems

1. **Limited Feature Coverage**: Current implementation doesn't expose all SDK capabilities (streaming modes, retry logic, metrics export, session continuation)
2. **Poor Separation of Concerns**: Business logic mixed with SDK integration
3. **Insufficient Persistence**: Not all interactions, hooks, permissions, and metrics are persisted
4. **No Session Continuation**: Can't resume or fork existing sessions
5. **Missing Background Task Support**: No distinction between interactive chat and background automation
6. **Limited Observability**: Incomplete logging, metrics, and audit trails
7. **No Storage Archival**: Working directories not archived to S3/file storage

### Design Goals

✅ **Extensibility**: Plugin architecture for custom hooks, tools, and handlers
✅ **Maintainability**: Clear module boundaries, single responsibility, type safety
✅ **Observability**: Comprehensive logging, metrics, and audit trails
✅ **Persistence**: All interactions, state, and artifacts saved and linked to sessions
✅ **Flexibility**: Support interactive chat, background tasks, session forking
✅ **Production-Ready**: Retry logic, error handling, monitoring, storage archival

---

## Architecture Overview

### Module Structure

```
app/claude_sdk/
├── __init__.py                      # Public API exports
│
├── core/                            # Core SDK Integration
│   ├── __init__.py
│   ├── client.py                   # Enhanced ClaudeSDKClient wrapper
│   ├── session_manager.py          # Session lifecycle management
│   ├── options_builder.py          # ClaudeAgentOptions configuration
│   └── exceptions.py               # SDK-specific exceptions
│
├── domain/                          # Business Models (Domain Layer)
│   ├── __init__.py
│   ├── models.py                   # Domain entities (AgentSession, AgentMessage, etc.)
│   ├── enums.py                    # Session modes, statuses, hook types
│   └── value_objects.py            # Immutable value objects (ToolCallResult, MetricsSnapshot)
│
├── handlers/                        # Event & Message Handlers
│   ├── __init__.py
│   ├── message_handler.py          # Process AssistantMessage, ToolUseBlock, etc.
│   ├── stream_handler.py           # Handle StreamEvent for partial messages
│   ├── result_handler.py           # Process ResultMessage and final metrics
│   └── error_handler.py            # Centralized error handling and recovery
│
├── hooks/                           # Hook System
│   ├── __init__.py
│   ├── hook_manager.py             # Hook registration and execution
│   ├── hook_registry.py            # Hook discovery and lifecycle
│   ├── base_hooks.py               # Abstract base classes for hooks
│   └── implementations/            # Built-in hook implementations
│       ├── __init__.py
│       ├── audit_hook.py           # Audit logging hook
│       ├── tool_tracking_hook.py   # Tool usage tracking
│       ├── metrics_hook.py         # Cost and performance metrics
│       ├── notification_hook.py    # Real-time notifications
│       └── persistence_hook.py     # Database persistence
│
├── permissions/                     # Permission System
│   ├── __init__.py
│   ├── permission_manager.py       # Permission callback orchestration
│   ├── policy_engine.py            # Rule-based permission policies
│   ├── validators.py               # Input validation for tools
│   └── policies/                   # Built-in permission policies
│       ├── __init__.py
│       ├── file_access_policy.py   # File system restrictions
│       ├── command_policy.py       # Bash command filtering
│       └── mcp_policy.py           # MCP server permissions
│
├── mcp/                             # MCP Integration
│   ├── __init__.py
│   ├── server_manager.py           # MCP server lifecycle
│   ├── server_config_builder.py   # SDK vs External MCP config
│   ├── tool_registry.py            # MCP tool discovery
│   └── servers/                    # Custom MCP server implementations
│       ├── __init__.py
│       └── kubernetes_server.py    # Example: Kubernetes MCP server
│
├── persistence/                     # Data Persistence Layer
│   ├── __init__.py
│   ├── session_persister.py        # Save session state, messages, metrics
│   ├── metrics_persister.py        # Persist performance and cost metrics
│   ├── artifact_persister.py       # Save tool outputs, files, logs
│   └── storage_archiver.py         # Archive working directories to S3/storage
│
├── streaming/                       # Streaming & Real-time
│   ├── __init__.py
│   ├── stream_orchestrator.py      # Manage streaming sessions
│   ├── event_broadcaster.py        # WebSocket/SSE event distribution
│   └── partial_message_aggregator.py  # Aggregate partial StreamEvents
│
├── execution/                       # Execution Strategies
│   ├── __init__.py
│   ├── executor_factory.py         # Create appropriate executor
│   ├── interactive_executor.py     # Interactive chat sessions
│   ├── background_executor.py      # Background automation tasks
│   └── forked_executor.py          # Continue existing session
│
├── monitoring/                      # Observability
│   ├── __init__.py
│   ├── metrics_collector.py        # Collect runtime metrics
│   ├── performance_tracker.py      # Track latency, throughput
│   ├── cost_tracker.py             # Track API costs
│   └── health_checker.py           # SDK health monitoring
│
├── retry/                           # Retry & Resilience
│   ├── __init__.py
│   ├── retry_manager.py            # Retry orchestration
│   ├── retry_policies.py           # Backoff strategies
│   └── circuit_breaker.py          # Circuit breaker pattern
│
└── utils/                           # Utilities
    ├── __init__.py
    ├── logging_utils.py            # JSON logging helpers
    ├── serialization.py            # JSON serialization for complex types
    └── working_dir_utils.py        # Working directory management
```

---

## Core Components Design

### 1. Core SDK Integration (`core/`)

#### **1.1 EnhancedClaudeClient (`core/client.py`)**

Wraps the official `ClaudeSDKClient` with additional capabilities:

```python
@dataclass
class ClientConfig:
    """Configuration for enhanced Claude client."""
    session_id: UUID
    model: str
    permission_mode: str
    max_turns: int
    max_retries: int
    retry_delay: float
    timeout_seconds: int
    include_partial_messages: bool
    working_directory: Path
    mcp_servers: Dict[str, Any]
    allowed_tools: Optional[List[str]]
    hooks: Optional[Dict[str, List[HookMatcher]]]
    can_use_tool: Optional[Callable]


class EnhancedClaudeClient:
    """Enhanced wrapper around ClaudeSDKClient.

    Features:
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - Metrics collection (duration, cost, tokens)
    - Lifecycle management (connect, disconnect, cleanup)
    - Session state tracking
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.sdk_client: Optional[ClaudeSDKClient] = None
        self.metrics = ClientMetrics()
        self.state = ClientState.CREATED

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

#### **1.2 SessionManager (`core/session_manager.py`)**

Manages Claude SDK session lifecycle:

```python
class SessionManager:
    """Manages Claude SDK sessions throughout their lifecycle.

    Responsibilities:
    - Create new sessions (interactive or background)
    - Resume existing sessions (session continuation)
    - Fork sessions (clone context)
    - Archive sessions (cleanup and storage)
    - Track active sessions
    """

    async def create_session(
        self,
        session_id: UUID,
        mode: SessionMode,
        config: SessionConfiguration
    ) -> AgentSession:
        """Create new Claude SDK session."""

    async def resume_session(
        self,
        session_id: UUID,
        restore_context: bool = True
    ) -> AgentSession:
        """Resume paused or archived session."""

    async def fork_session(
        self,
        parent_session_id: UUID,
        fork_at_message: Optional[int] = None
    ) -> AgentSession:
        """Fork session from specific point in history."""

    async def archive_session(
        self,
        session_id: UUID,
        archive_to_storage: bool = True
    ) -> ArchiveResult:
        """Archive session and upload to S3/storage."""
```

#### **1.3 OptionsBuilder (`core/options_builder.py`)**

Builds `ClaudeAgentOptions` from business configuration:

```python
class OptionsBuilder:
    """Build ClaudeAgentOptions from business configuration.

    Converts domain models to SDK options with:
    - MCP server configuration (SDK vs External)
    - Permission callbacks
    - Hook matchers
    - Tool restrictions
    - Streaming settings
    """

    def build(
        self,
        session: AgentSession,
        permission_manager: PermissionManager,
        hook_manager: HookManager,
        mcp_config: MCPConfiguration
    ) -> ClaudeAgentOptions:
        """Build SDK options from domain objects."""
```

---

### 2. Domain Layer (`domain/`)

#### **2.1 Domain Models (`domain/models.py`)**

Business entities representing SDK concepts:

```python
@dataclass
class AgentSession:
    """Domain entity for Claude agent session.

    Represents a complete agent interaction session with:
    - Lifecycle state (created, active, paused, completed, archived)
    - Configuration (model, permissions, MCP servers)
    - Metrics (cost, tokens, tool calls)
    - Relationships (parent session for forking)
    """
    id: UUID
    user_id: UUID
    mode: SessionMode  # INTERACTIVE, BACKGROUND, FORKED
    status: SessionStatus
    configuration: SessionConfiguration
    metrics: SessionMetrics
    working_directory: Path
    parent_session_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class AgentMessage:
    """Domain entity for Claude messages.

    Represents a message in the conversation with:
    - Direction (user -> claude, claude -> user)
    - Content blocks (text, tool_use, tool_result, thinking)
    - Metadata (model, tokens, timing)
    """
    id: UUID
    session_id: UUID
    direction: MessageDirection  # USER_TO_AGENT, AGENT_TO_USER
    content_blocks: List[ContentBlock]
    model: Optional[str]
    tokens_used: TokenUsage
    created_at: datetime


@dataclass
class ToolExecution:
    """Domain entity for tool execution.

    Captures complete tool execution with:
    - Tool identification
    - Input parameters
    - Output/result
    - Error information
    - Performance metrics
    """
    id: UUID
    session_id: UUID
    message_id: UUID
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    is_error: bool
    error_message: Optional[str]
    duration_ms: int
    executed_at: datetime


@dataclass
class HookExecution:
    """Domain entity for hook execution.

    Tracks all hook invocations for audit trail:
    - Hook type (PreToolUse, PostToolUse, etc.)
    - Input data passed to hook
    - Output/decision from hook
    - Tool association
    """
    id: UUID
    session_id: UUID
    hook_type: HookType
    tool_use_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    executed_at: datetime


@dataclass
class SessionMetrics:
    """Comprehensive session metrics.

    Tracks all performance and cost metrics:
    - Message counts
    - Tool usage
    - API costs and tokens
    - Timing information
    - Error counts
    """
    session_id: UUID
    total_messages: int = 0
    total_tool_calls: int = 0
    total_hook_executions: int = 0
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


@dataclass
class SessionConfiguration:
    """Session configuration.

    All options for configuring a Claude SDK session:
    - Model selection
    - Permission settings
    - MCP servers
    - Tool restrictions
    - Hooks
    - Streaming options
    """
    model: str = "claude-sonnet-4-5"
    permission_mode: PermissionMode = PermissionMode.DEFAULT
    max_turns: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout_seconds: int = 120
    include_partial_messages: bool = False
    allowed_tools: Optional[List[str]] = None
    mcp_servers: Dict[str, MCPServerConfig] = field(default_factory=dict)
    hooks_enabled: List[HookType] = field(default_factory=list)
    custom_policies: List[str] = field(default_factory=list)
```

#### **2.2 Enums (`domain/enums.py`)**

```python
class SessionMode(str, Enum):
    """Session execution modes."""
    INTERACTIVE = "interactive"          # Real-time chat (UI)
    BACKGROUND = "background"            # Automated task (no user interaction)
    FORKED = "forked"                   # Continuation of existing session


class SessionStatus(str, Enum):
    """Session lifecycle states."""
    CREATED = "created"
    CONNECTING = "connecting"
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING_USER = "waiting_user"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


class PermissionMode(str, Enum):
    """Permission callback modes."""
    DEFAULT = "default"                  # Prompt user for permissions
    ACCEPT_EDITS = "acceptEdits"        # Auto-approve file edits
    BYPASS_PERMISSIONS = "bypassPermissions"  # Allow all tools


class HookType(str, Enum):
    """All supported hook types."""
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"


class MessageDirection(str, Enum):
    """Message flow direction."""
    USER_TO_AGENT = "user_to_agent"
    AGENT_TO_USER = "agent_to_user"


class ArchiveStatus(str, Enum):
    """Working directory archive status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

### 3. Handlers (`handlers/`)

Message and event processing components:

#### **3.1 MessageHandler (`handlers/message_handler.py`)**

```python
class MessageHandler:
    """Process AssistantMessage and extract content blocks.

    Responsibilities:
    - Parse TextBlock, ToolUseBlock, ToolResultBlock, ThinkingBlock
    - Convert SDK messages to domain AgentMessage
    - Trigger persistence hooks
    - Broadcast to WebSocket subscribers
    """

    async def handle_assistant_message(
        self,
        message: AssistantMessage,
        session_id: UUID
    ) -> AgentMessage:
        """Process AssistantMessage from SDK."""

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
```

#### **3.2 StreamHandler (`handlers/stream_handler.py`)**

```python
class StreamHandler:
    """Handle StreamEvent for partial message updates.

    Used when include_partial_messages=True to show real-time
    progress to users (like ChatGPT typing effect).
    """

    async def handle_stream_event(
        self,
        event: StreamEvent,
        session_id: UUID
    ) -> PartialMessage:
        """Process streaming event and broadcast partial update."""
```

#### **3.3 ResultHandler (`handlers/result_handler.py`)**

```python
class ResultHandler:
    """Process ResultMessage and finalize session metrics.

    Responsibilities:
    - Extract final metrics (cost, tokens, duration)
    - Update session status
    - Persist metrics to database
    - Trigger session completion hooks
    """

    async def handle_result_message(
        self,
        message: ResultMessage,
        session_id: UUID
    ) -> SessionMetrics:
        """Process final result and persist metrics."""
```

---

### 4. Hook System (`hooks/`)

#### **4.1 HookManager (`hooks/hook_manager.py`)**

```python
class HookManager:
    """Orchestrate hook execution across all hook types.

    Features:
    - Register hooks dynamically
    - Execute hooks in order
    - Handle hook errors gracefully
    - Support hook chaining
    - Enable/disable hooks per session
    """

    def __init__(self):
        self.registry = HookRegistry()

    async def register_hook(
        self,
        hook_type: HookType,
        hook: BaseHook,
        priority: int = 100
    ) -> None:
        """Register hook with priority."""

    async def execute_hooks(
        self,
        hook_type: HookType,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Execute all hooks for given type."""

    def build_hook_matchers(
        self,
        session_id: UUID,
        enabled_hooks: List[HookType]
    ) -> Dict[str, List[HookMatcher]]:
        """Build SDK HookMatcher configuration."""
```

#### **4.2 Base Hooks (`hooks/base_hooks.py`)**

```python
class BaseHook(ABC):
    """Abstract base class for all hooks."""

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Execute hook logic and return result."""
        pass

    @property
    @abstractmethod
    def hook_type(self) -> HookType:
        """Return hook type."""
        pass


class PreToolUseHook(BaseHook):
    """Base for PreToolUse hooks."""
    hook_type = HookType.PRE_TOOL_USE


class PostToolUseHook(BaseHook):
    """Base for PostToolUse hooks."""
    hook_type = HookType.POST_TOOL_USE
```

#### **4.3 Built-in Hooks (`hooks/implementations/`)**

```python
# audit_hook.py
class AuditHook(BaseHook):
    """Log all tool executions for audit trail."""

    async def execute(self, input_data, tool_use_id, context):
        # Persist to audit_log table
        await self.audit_service.log_hook_execution(...)
        return {"continue_": True}


# tool_tracking_hook.py
class ToolTrackingHook(PostToolUseHook):
    """Track tool usage statistics."""

    async def execute(self, input_data, tool_use_id, context):
        # Save to tool_call table
        await self.tool_call_repo.create(...)
        return {"continue_": True}


# metrics_hook.py
class MetricsHook(BaseHook):
    """Collect cost and performance metrics."""

    async def execute(self, input_data, tool_use_id, context):
        # Update session metrics
        await self.metrics_collector.update(...)
        return {"continue_": True}


# persistence_hook.py
class PersistenceHook(BaseHook):
    """Persist messages and tool calls to database."""

    async def execute(self, input_data, tool_use_id, context):
        # Save to messages/tool_calls tables
        await self.persister.save(...)
        return {"continue_": True}


# notification_hook.py
class NotificationHook(BaseHook):
    """Send real-time notifications on events."""

    async def execute(self, input_data, tool_use_id, context):
        # Broadcast via WebSocket
        await self.broadcaster.notify(...)
        return {"continue_": True}
```

---

### 5. Permission System (`permissions/`)

#### **5.1 PermissionManager (`permissions/permission_manager.py`)**

```python
class PermissionManager:
    """Orchestrate permission checking with policy engine.

    Features:
    - Execute permission policies
    - Cache permission decisions
    - Audit permission denials
    - Support custom policies
    """

    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine
        self.permission_log: List[PermissionDecision] = []

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ToolPermissionContext
    ) -> PermissionResult:
        """Main permission callback for SDK."""

        # Execute all policies
        for policy in self.policy_engine.get_policies(tool_name):
            result = await policy.evaluate(tool_name, input_data, context)
            if isinstance(result, PermissionResultDeny):
                self.permission_log.append(
                    PermissionDecision(
                        tool_name=tool_name,
                        input_data=input_data,
                        decision="deny",
                        reason=result.message
                    )
                )
                return result

        # Default allow
        self.permission_log.append(
            PermissionDecision(
                tool_name=tool_name,
                input_data=input_data,
                decision="allow",
                reason="no_policy_matched"
            )
        )
        return PermissionResultAllow()

    def get_permission_log(self) -> List[PermissionDecision]:
        """Get permission audit log."""
        return self.permission_log
```

#### **5.2 PolicyEngine (`permissions/policy_engine.py`)**

```python
class PermissionPolicy(ABC):
    """Base class for permission policies."""

    @abstractmethod
    async def evaluate(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ToolPermissionContext
    ) -> PermissionResult:
        """Evaluate if tool usage is permitted."""
        pass


class PolicyEngine:
    """Manage and execute permission policies.

    Supports:
    - Built-in policies (file access, command filtering)
    - Custom user-defined policies
    - Policy composition (AND/OR logic)
    """

    def __init__(self):
        self.policies: Dict[str, List[PermissionPolicy]] = {}

    def register_policy(
        self,
        tool_pattern: str,  # e.g., "read_file", "bash", "*"
        policy: PermissionPolicy
    ) -> None:
        """Register policy for tool pattern."""

    def get_policies(self, tool_name: str) -> List[PermissionPolicy]:
        """Get all policies matching tool name."""
```

#### **5.3 Built-in Policies (`permissions/policies/`)**

```python
# file_access_policy.py
class FileAccessPolicy(PermissionPolicy):
    """Restrict file system access.

    Blocks:
    - Sensitive system files (/etc/passwd, SSH keys, etc.)
    - Files outside allowed directories
    - Hidden files (unless explicitly allowed)
    """

    def __init__(self, restricted_paths: List[str], allowed_paths: List[str]):
        self.restricted_paths = restricted_paths
        self.allowed_paths = allowed_paths

    async def evaluate(self, tool_name, input_data, context):
        if tool_name in ["read_file", "Read", "write_file", "Write"]:
            file_path = input_data.get("file_path") or input_data.get("path")

            # Check if restricted
            for restricted in self.restricted_paths:
                if str(Path(file_path).expanduser()).startswith(restricted):
                    return PermissionResultDeny(
                        message=f"Access denied: {file_path} is restricted",
                        interrupt=False
                    )

        return PermissionResultAllow()


# command_policy.py
class CommandPolicy(PermissionPolicy):
    """Filter dangerous bash commands.

    Blocks:
    - Destructive commands (rm -rf, dd, mkfs)
    - Privilege escalation (sudo, su)
    - Network access (curl, wget) if configured
    """

    def __init__(self, blocked_patterns: List[str]):
        self.blocked_patterns = blocked_patterns

    async def evaluate(self, tool_name, input_data, context):
        if tool_name in ["bash", "Bash"]:
            command = input_data.get("command", "")

            for pattern in self.blocked_patterns:
                if pattern in command:
                    return PermissionResultDeny(
                        message=f"Command blocked: contains '{pattern}'",
                        interrupt=False
                    )

        return PermissionResultAllow()
```

---

### 6. MCP Integration (`mcp/`)

#### **6.1 ServerManager (`mcp/server_manager.py`)**

```python
class MCPServerManager:
    """Manage MCP server lifecycle.

    Features:
    - Configure SDK MCP servers (in-process)
    - Configure external MCP servers (subprocess)
    - Validate MCP configurations
    - Health check MCP servers
    - Tool discovery
    """

    async def create_sdk_server(
        self,
        name: str,
        tools: List[SdkMcpTool]
    ) -> McpSdkServerConfig:
        """Create in-process SDK MCP server."""

    async def create_external_server(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str]
    ) -> McpServerConfig:
        """Configure external MCP server (subprocess)."""

    async def discover_tools(
        self,
        server_config: McpServerConfig
    ) -> List[ToolDefinition]:
        """Discover available tools from MCP server."""
```

---

### 7. Persistence Layer (`persistence/`)

#### **7.1 SessionPersister (`persistence/session_persister.py`)**

```python
class SessionPersister:
    """Persist session state, messages, and metadata.

    Responsibilities:
    - Save session configuration
    - Persist messages and tool calls
    - Update session status
    - Link all data to session_id
    """

    async def save_session(self, session: AgentSession) -> None:
        """Persist session to database."""

    async def save_message(self, message: AgentMessage) -> None:
        """Persist message to database."""

    async def save_tool_execution(self, execution: ToolExecution) -> None:
        """Persist tool execution to database."""

    async def save_hook_execution(self, execution: HookExecution) -> None:
        """Persist hook execution for audit trail."""

    async def update_session_status(
        self,
        session_id: UUID,
        status: SessionStatus
    ) -> None:
        """Update session status."""
```

#### **7.2 StorageArchiver (`persistence/storage_archiver.py`)**

```python
class StorageArchiver:
    """Archive working directories to S3/file storage.

    Features:
    - Compress working directory
    - Upload to S3/MinIO/local storage
    - Generate archive manifest
    - Track archive status
    - Support archive retrieval for session resumption
    """

    async def archive_working_directory(
        self,
        session_id: UUID,
        working_dir: Path
    ) -> ArchiveMetadata:
        """Archive working directory to storage."""

    async def retrieve_archive(
        self,
        session_id: UUID,
        extract_to: Path
    ) -> Path:
        """Retrieve and extract archived working directory."""

    async def delete_archive(self, session_id: UUID) -> None:
        """Delete archived working directory."""


@dataclass
class ArchiveMetadata:
    """Archive metadata."""
    session_id: UUID
    archive_path: str  # S3 path or local path
    size_bytes: int
    compression: str  # "gzip", "zip"
    archived_at: datetime
    manifest: Dict[str, Any]  # File listing
```

---

### 8. Execution Strategies (`execution/`)

#### **8.1 ExecutorFactory (`execution/executor_factory.py`)**

```python
class ExecutorFactory:
    """Create appropriate executor based on session mode."""

    @staticmethod
    def create_executor(
        session: AgentSession,
        client: EnhancedClaudeClient,
        **kwargs
    ) -> BaseExecutor:
        """Factory method to create executor."""

        if session.mode == SessionMode.INTERACTIVE:
            return InteractiveExecutor(session, client, **kwargs)
        elif session.mode == SessionMode.BACKGROUND:
            return BackgroundExecutor(session, client, **kwargs)
        elif session.mode == SessionMode.FORKED:
            return ForkedExecutor(session, client, **kwargs)
        else:
            raise ValueError(f"Unknown session mode: {session.mode}")
```

#### **8.2 InteractiveExecutor (`execution/interactive_executor.py`)**

```python
class InteractiveExecutor(BaseExecutor):
    """Execute interactive chat sessions.

    Features:
    - Real-time streaming to WebSocket
    - Partial message support
    - User can interrupt/pause
    - Session continuation support
    """

    async def execute(
        self,
        prompt: str
    ) -> AsyncIterator[AgentMessage]:
        """Execute query and stream responses."""

        # Enable partial messages for real-time UI
        self.client.config.include_partial_messages = True

        await self.client.query(prompt)

        async for message in self.client.receive_response():
            # Process and broadcast to WebSocket
            agent_message = await self.message_handler.handle(message)
            await self.broadcaster.broadcast(agent_message)
            yield agent_message
```

#### **8.3 BackgroundExecutor (`execution/background_executor.py`)**

```python
class BackgroundExecutor(BaseExecutor):
    """Execute background automation tasks.

    Features:
    - No real-time streaming (batch mode)
    - Automatic retry on failures
    - Result notification on completion
    - Error recovery
    """

    async def execute(
        self,
        prompt: str
    ) -> ExecutionResult:
        """Execute task and return final result."""

        # No partial messages for background tasks
        self.client.config.include_partial_messages = False

        # Execute with retry logic
        result = await self.retry_manager.execute_with_retry(
            lambda: self._execute_query(prompt)
        )

        # Send completion notification
        await self.notification_service.notify_completion(
            session_id=self.session.id,
            result=result
        )

        return result
```

#### **8.4 ForkedExecutor (`execution/forked_executor.py`)**

```python
class ForkedExecutor(BaseExecutor):
    """Execute forked session (continue existing conversation).

    Features:
    - Restore context from parent session
    - Resume from specific message
    - Inherit configuration from parent
    - Maintain separate working directory
    """

    async def execute(
        self,
        prompt: str
    ) -> AsyncIterator[AgentMessage]:
        """Execute in forked session with restored context."""

        # Restore context from parent session
        await self._restore_context()

        # Continue conversation
        async for message in self.client.receive_response():
            yield await self.message_handler.handle(message)

    async def _restore_context(self) -> None:
        """Restore conversation history from parent session."""

        # Retrieve parent session messages
        parent_messages = await self.message_repo.get_session_messages(
            self.session.parent_session_id
        )

        # Replay messages to establish context
        # (Implementation depends on SDK's session continuation support)
```

---

### 9. Monitoring & Observability (`monitoring/`)

#### **9.1 MetricsCollector (`monitoring/metrics_collector.py`)**

```python
class MetricsCollector:
    """Collect runtime metrics for observability.

    Metrics:
    - Request/response latency
    - Tool execution duration
    - API costs per session
    - Token usage
    - Error rates
    - Concurrent sessions
    """

    async def record_query_duration(
        self,
        session_id: UUID,
        duration_ms: int
    ) -> None:
        """Record query execution time."""

    async def record_tool_execution(
        self,
        session_id: UUID,
        tool_name: str,
        duration_ms: int,
        success: bool
    ) -> None:
        """Record tool execution metrics."""

    async def record_api_cost(
        self,
        session_id: UUID,
        cost_usd: Decimal,
        tokens: TokenUsage
    ) -> None:
        """Record API usage cost."""

    async def get_session_metrics(
        self,
        session_id: UUID
    ) -> SessionMetrics:
        """Get current session metrics."""
```

#### **9.2 CostTracker (`monitoring/cost_tracker.py`)**

```python
class CostTracker:
    """Track API costs and enforce budgets.

    Features:
    - Per-session cost tracking
    - Per-user budget enforcement
    - Cost alerts
    - Token usage breakdown
    """

    async def track_cost(
        self,
        session_id: UUID,
        user_id: UUID,
        cost_usd: Decimal,
        tokens: TokenUsage
    ) -> None:
        """Track cost for session and user."""

    async def check_budget(
        self,
        user_id: UUID
    ) -> BudgetStatus:
        """Check if user has exceeded budget."""

    async def get_user_costs(
        self,
        user_id: UUID,
        period: TimePeriod
    ) -> CostSummary:
        """Get user costs for time period."""
```

---

### 10. Retry & Resilience (`retry/`)

#### **10.1 RetryManager (`retry/retry_manager.py`)**

```python
class RetryManager:
    """Manage retry logic with exponential backoff.

    Features:
    - Configurable retry policies
    - Exponential backoff
    - Jitter for distributed systems
    - Circuit breaker integration
    - Retry budget tracking
    """

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
                    raise CircuitBreakerOpenError()

                # Execute operation
                result = await operation(*args, **kwargs)

                # Success - close circuit breaker
                self.circuit_breaker.record_success()
                return result

            except CLIConnectionError as e:
                # Transient error - retry
                if attempt < self.policy.max_retries:
                    delay = self.policy.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.circuit_breaker.record_failure()
                    raise

            except ClaudeSDKError as e:
                # Non-retryable error
                self.circuit_breaker.record_failure()
                raise
```

---

## Data Flow Diagrams

### Interactive Session Flow

```
User Request (UI)
      ↓
API Endpoint
      ↓
InteractiveExecutor
      ↓
EnhancedClaudeClient.query()
      ↓
ClaudeSDKClient (official SDK)
      ↓
[Streaming Loop]
      ↓
AssistantMessage → MessageHandler → SessionPersister → Database
      ↓                                   ↓
ToolUseBlock → HookManager (PreToolUse) → AuditHook → Database
      ↓                                   ↓
ToolResultBlock → HookManager (PostToolUse) → MetricsHook → Database
      ↓
StreamEvent → StreamHandler → EventBroadcaster → WebSocket → UI
      ↓
ResultMessage → ResultHandler → MetricsCollector → Database
      ↓
Final Metrics → StorageArchiver → S3
```

### Background Task Flow

```
Task Trigger (Scheduler/API)
      ↓
BackgroundExecutor
      ↓
EnhancedClaudeClient.query()
      ↓
[Batch Processing Loop]
      ↓
AssistantMessage → MessageHandler → SessionPersister → Database
      ↓
ToolUseBlock → PermissionManager → PolicyEngine → Allow/Deny
      ↓
ToolResultBlock → ToolTrackingHook → Database
      ↓
ResultMessage → NotificationService → User Notification (Email/Webhook)
      ↓
StorageArchiver → Archive to S3 → Update Archive Status
```

### Session Fork Flow

```
User Request (Fork Session X at Message N)
      ↓
SessionManager.fork_session(parent_id=X, fork_at_message=N)
      ↓
1. Create new session (mode=FORKED)
2. Copy configuration from parent
3. Create new working directory
4. Retrieve messages 1..N from parent
5. Restore context in ForkedExecutor
      ↓
ForkedExecutor.execute(new_prompt)
      ↓
Continue as Interactive/Background session
```

---

## Database Schema Updates

### New Tables

```sql
-- Hook executions audit trail
CREATE TABLE hook_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    hook_type VARCHAR(50) NOT NULL,
    tool_use_id VARCHAR(255),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_hook_executions_session (session_id),
    INDEX idx_hook_executions_type (hook_type)
);

-- Permission decisions audit trail
CREATE TABLE permission_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL,
    decision VARCHAR(20) NOT NULL,  -- 'allow' or 'deny'
    reason TEXT,
    decided_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_permission_decisions_session (session_id)
);

-- Working directory archives
CREATE TABLE working_directory_archives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    archive_path TEXT NOT NULL,  -- S3 URI or local path
    size_bytes BIGINT NOT NULL,
    compression VARCHAR(20) NOT NULL,  -- 'gzip', 'zip'
    manifest JSONB NOT NULL,  -- File listing
    status VARCHAR(50) NOT NULL,  -- 'pending', 'in_progress', 'completed', 'failed'
    archived_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_archives_status (status)
);

-- Session metrics snapshots (for historical tracking)
CREATE TABLE session_metrics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    snapshot_at TIMESTAMP NOT NULL DEFAULT NOW(),
    total_messages INT NOT NULL,
    total_tool_calls INT NOT NULL,
    total_cost_usd NUMERIC(10, 6) NOT NULL,
    total_input_tokens INT NOT NULL,
    total_output_tokens INT NOT NULL,
    duration_ms BIGINT NOT NULL,
    INDEX idx_metrics_session (session_id),
    INDEX idx_metrics_snapshot_at (snapshot_at)
);
```

### Updated Tables

```sql
-- Add columns to sessions table
ALTER TABLE sessions
ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'interactive',  -- 'interactive', 'background', 'forked'
ADD COLUMN include_partial_messages BOOLEAN DEFAULT FALSE,
ADD COLUMN max_retries INT DEFAULT 3,
ADD COLUMN retry_delay FLOAT DEFAULT 2.0,
ADD COLUMN hooks_enabled JSONB DEFAULT '[]',  -- List of enabled hook types
ADD COLUMN custom_policies JSONB DEFAULT '[]';  -- List of custom policy names

-- Add indexes for new columns
CREATE INDEX idx_sessions_mode ON sessions(mode);
```

---

## API Endpoints Design

### Session Management

```
POST   /api/v1/sessions                          # Create new session
GET    /api/v1/sessions/{id}                     # Get session details
PATCH  /api/v1/sessions/{id}                     # Update session (pause, resume)
DELETE /api/v1/sessions/{id}                     # Terminate session
GET    /api/v1/sessions                          # List sessions (with filters)

POST   /api/v1/sessions/{id}/fork                # Fork session
POST   /api/v1/sessions/{id}/resume              # Resume paused session
POST   /api/v1/sessions/{id}/archive             # Archive session
GET    /api/v1/sessions/{id}/metrics             # Get session metrics
GET    /api/v1/sessions/{id}/audit-trail         # Get audit trail
```

### Message & Execution

```
POST   /api/v1/sessions/{id}/query               # Send message (interactive)
GET    /api/v1/sessions/{id}/messages            # Get conversation history
GET    /api/v1/sessions/{id}/tool-calls          # Get tool execution history
GET    /api/v1/sessions/{id}/hooks               # Get hook execution history
GET    /api/v1/sessions/{id}/permissions         # Get permission decisions

WS     /ws/sessions/{id}                         # WebSocket for real-time streaming
```

### Background Tasks

```
POST   /api/v1/tasks                             # Create background task
GET    /api/v1/tasks/{id}                        # Get task status
GET    /api/v1/tasks/{id}/result                 # Get task result
GET    /api/v1/tasks                             # List tasks
```

### Archives

```
GET    /api/v1/sessions/{id}/archive             # Get archive info
GET    /api/v1/sessions/{id}/archive/download    # Download archive
POST   /api/v1/sessions/{id}/archive/restore     # Restore from archive
```

---

## Configuration

### Environment Variables

```bash
# Claude SDK
CLAUDE_SDK_DEFAULT_MODEL=claude-sonnet-4-5
CLAUDE_SDK_MAX_RETRIES=3
CLAUDE_SDK_RETRY_DELAY=2.0
CLAUDE_SDK_TIMEOUT_SECONDS=120

# Storage
STORAGE_PROVIDER=s3  # 's3', 'minio', 'local'
AWS_S3_BUCKET=ai-agent-archives
AWS_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Session Limits
MAX_CONCURRENT_INTERACTIVE_SESSIONS=10
MAX_CONCURRENT_BACKGROUND_SESSIONS=50
SESSION_IDLE_TIMEOUT_MINUTES=30

# Metrics & Monitoring
ENABLE_METRICS_COLLECTION=true
METRICS_EXPORT_INTERVAL_SECONDS=60
ENABLE_COST_TRACKING=true
USER_MONTHLY_BUDGET_USD=100.0

# Permissions
DEFAULT_PERMISSION_MODE=default  # 'default', 'acceptEdits', 'bypassPermissions'
ENABLE_CUSTOM_POLICIES=true

# Hooks
ENABLE_AUDIT_HOOK=true
ENABLE_METRICS_HOOK=true
ENABLE_PERSISTENCE_HOOK=true
ENABLE_NOTIFICATION_HOOK=true
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Core SDK integration (`core/`)
- [ ] Domain models (`domain/`)
- [ ] Basic handlers (`handlers/`)
- [ ] Database migrations

### Phase 2: Advanced Features (Week 3-4)
- [ ] Hook system (`hooks/`)
- [ ] Permission system (`permissions/`)
- [ ] MCP integration (`mcp/`)
- [ ] Retry & resilience (`retry/`)

### Phase 3: Execution & Streaming (Week 5-6)
- [ ] Execution strategies (`execution/`)
- [ ] Streaming orchestration (`streaming/`)
- [ ] Session continuation & forking
- [ ] Interactive vs background modes

### Phase 4: Persistence & Observability (Week 7-8)
- [ ] Persistence layer (`persistence/`)
- [ ] Storage archival to S3
- [ ] Monitoring & metrics (`monitoring/`)
- [ ] Comprehensive logging

### Phase 5: Testing & Documentation (Week 9-10)
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E tests for key flows
- [ ] API documentation
- [ ] Developer guides

### Phase 6: Production Hardening (Week 11-12)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Load testing
- [ ] Deployment automation
- [ ] Monitoring dashboards

---

## Use Case Examples

### Use Case 1: Kubernetes Cluster Monitoring (Background Task)

```python
# User creates background task via API
POST /api/v1/tasks
{
    "name": "K8s Cluster Health Check",
    "mode": "background",
    "mcp_servers": {
        "kubernetes": {
            "type": "external",
            "command": "npx",
            "args": ["-y", "@your-org/mcp-kubernetes"],
            "env": {"KUBECONFIG": "/path/to/kubeconfig"}
        }
    },
    "prompt": "Check the status of all pods, services, and deployments. Report any issues found.",
    "hooks_enabled": ["PreToolUse", "PostToolUse", "Stop"],
    "notification_webhook": "https://api.example.com/webhooks/task-complete"
}

# System flow:
# 1. Create session (mode=BACKGROUND)
# 2. Configure Kubernetes MCP server
# 3. BackgroundExecutor runs query
# 4. Claude uses Kubernetes tools (kubectl commands via MCP)
# 5. All tool calls logged to database
# 6. Hooks execute (audit, metrics tracking)
# 7. Final result saved
# 8. Working directory archived to S3
# 9. Webhook notification sent to user
# 10. User retrieves result via API
```

### Use Case 2: Interactive Code Review (Interactive Session)

```python
# User starts interactive session
POST /api/v1/sessions
{
    "name": "Code Review",
    "mode": "interactive",
    "include_partial_messages": true,
    "mcp_servers": {
        "filesystem": {
            "type": "external",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/repo"]
        }
    }
}

# WebSocket connection for real-time streaming
WS /ws/sessions/{session_id}

# User sends queries:
# "Review the authentication module"
# "Check for security vulnerabilities"
# "Suggest improvements"

# System streams responses in real-time:
# - Partial text updates (like ChatGPT)
# - Tool execution notifications
# - File read/write operations
# - All persisted to database
```

### Use Case 3: Session Forking (Urgent Investigation)

```python
# User sees concerning info in background task result
# Forks session to investigate interactively

POST /api/v1/sessions/{background_session_id}/fork
{
    "name": "Investigation - Pod Crash",
    "mode": "interactive",
    "fork_at_message": 15  # Fork from message that reported error
}

# System:
# 1. Creates new session (mode=FORKED)
# 2. Copies configuration from parent
# 3. Restores context up to message 15
# 4. User can now interactively ask questions:
#    "Show me the pod logs"
#    "What caused the crash?"
#    "How can we prevent this?"
```

---

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock all dependencies
- Focus on business logic
- Target: 80%+ coverage

### Integration Tests
- Test component interactions
- Use real database (test DB)
- Test SDK integration
- Verify persistence

### E2E Tests
- Full workflow tests
- Interactive session flow
- Background task flow
- Session forking flow
- Archive & restore flow

### Performance Tests
- Concurrent session handling
- Message throughput
- Storage archival speed
- API response times

---

## Migration Strategy

### Gradual Migration Plan

1. **Phase 1**: Build new module alongside existing one
2. **Phase 2**: Migrate background tasks to new module
3. **Phase 3**: Migrate interactive sessions to new module
4. **Phase 4**: Deprecate old module
5. **Phase 5**: Remove old code

### Backward Compatibility

- Maintain existing API endpoints during migration
- Support both old and new session formats
- Provide data migration scripts
- Document breaking changes

---

## Open Questions & Future Enhancements

### Open Questions
1. Session continuation: How to restore exact SDK state?
2. Long-running sessions: How to handle memory/resource limits?
3. Multi-tenant isolation: Separate working directories per tenant?
4. Cost optimization: Token caching strategies?

### Future Enhancements
1. **Plugin System**: Load custom hooks/policies at runtime
2. **Session Templates**: Pre-configured session types for common use cases
3. **Workflow Engine**: Chain multiple sessions together
4. **Distributed Execution**: Run sessions across multiple workers
5. **Advanced Analytics**: Session analytics, cost optimization insights
6. **AI Agent Marketplace**: Share and discover custom MCP servers

---

## Appendix

### A. Key Interfaces

```python
# IExecutor
class IExecutor(ABC):
    @abstractmethod
    async def execute(self, prompt: str) -> Any:
        pass


# IHook
class IHook(ABC):
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        pass


# IPermissionPolicy
class IPermissionPolicy(ABC):
    @abstractmethod
    async def evaluate(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ToolPermissionContext
    ) -> PermissionResult:
        pass


# IPersister
class IPersister(ABC):
    @abstractmethod
    async def save(self, entity: Any) -> None:
        pass


# IArchiver
class IArchiver(ABC):
    @abstractmethod
    async def archive(self, session_id: UUID, path: Path) -> ArchiveMetadata:
        pass

    @abstractmethod
    async def retrieve(self, session_id: UUID) -> Path:
        pass
```

### B. Common Patterns

**Repository Pattern**: All data access through repositories
**Strategy Pattern**: Different executors for different session modes
**Observer Pattern**: Event broadcasting to WebSocket subscribers
**Factory Pattern**: Create components based on configuration
**Chain of Responsibility**: Hook execution chain
**Decorator Pattern**: Enhance SDK client with retry logic

### C. Error Handling

```python
# Domain exceptions
class SessionNotFoundError(Exception): pass
class SessionNotActiveError(Exception): pass
class PermissionDeniedError(Exception): pass
class QuotaExceededError(Exception): pass
class ArchiveNotFoundError(Exception): pass

# SDK exceptions
class SDKConnectionError(Exception): pass
class SDKTimeoutError(Exception): pass
class SDKExecutionError(Exception): pass

# All exceptions logged and persisted to audit_log table
```

---

**End of Architecture Document**

This comprehensive design provides a solid foundation for building an enterprise-grade Claude SDK integration that supports hundreds of use cases while maintaining extensibility, observability, and production-readiness.
