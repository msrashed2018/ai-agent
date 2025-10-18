"""Claude SDK integration layer.

Integration components for the official claude-agent-sdk package.
Provides business logic, permission callbacks, and hooks for our service.

Phase 1 (Legacy): client_manager, permission_service, hook_handlers, message_processor
Phase 2 (NEW): core, handlers, execution, retry components
Phase 3 (NEW): hooks, permissions, mcp, persistence components
"""

# Phase 1 - Legacy components (still in use)
from app.claude_sdk.client_manager import ClaudeSDKClientManager
from app.claude_sdk.permission_service import PermissionService
from app.claude_sdk.exceptions import (
    ClientAlreadyExistsError,
    ClientNotFoundError,
    SDKConnectionError,
    SDKError,
    SDKRuntimeError,
    PermissionDeniedError,
    CircuitBreakerOpenError,
)
from app.claude_sdk.hook_handlers import (
    create_audit_hook,
    create_tool_tracking_hook,
    create_cost_tracking_hook,
    create_validation_hook,
    create_rate_limit_hook,
    create_notification_hook,
    create_webhook_hook,
)
from app.claude_sdk.message_processor import (
    MessageProcessor,
    EventBroadcaster,
)

# Phase 2 - NEW Core components
from app.claude_sdk.core import (
    ClientConfig,
    ClientMetrics,
    ClientState,
    OptionsBuilder,
    EnhancedClaudeClient,
    SessionManager,
)

# Phase 2 - NEW Handlers
from app.claude_sdk.handlers import (
    MessageHandler,
    StreamHandler,
    ResultHandler,
    ErrorHandler,
)

# Phase 2 - NEW Execution strategies
from app.claude_sdk.execution import (
    BaseExecutor,
    InteractiveExecutor,
    BackgroundExecutor,
    ExecutionResult,
    ForkedExecutor,
    ExecutorFactory,
)

# Phase 2 - NEW Retry and resilience
from app.claude_sdk.retry import (
    RetryManager,
    RetryPolicy,
    CircuitBreaker,
    CircuitBreakerState,
)

# Phase 3 - NEW Hook System
from app.claude_sdk.hooks import (
    BaseHook,
    HookType,
    HookContext,
    HookManager,
    HookRegistry,
    AuditHook,
    MetricsHook,
    ValidationHook,
    NotificationHook,
)

# Phase 3 - NEW Permission System
from app.claude_sdk.permissions import (
    BasePolicy,
    PermissionContext,
    PolicyEngine,
    PermissionManager,
    FileAccessPolicy,
    CommandPolicy,
    NetworkPolicy,
    ToolWhitelistPolicy,
    ToolBlacklistPolicy,
)

# Phase 3 - NEW MCP Integration
from app.claude_sdk.mcp import (
    MCPServerConfig,
    MCPServerType,
    MCPServerManager,
    ToolRegistry,
)

# Phase 3 - NEW Persistence Layer
from app.claude_sdk.persistence import (
    SessionPersister,
    MetricsPersister,
    StorageArchiver,
)

__all__ = [
    # Phase 1 - Client Manager (Legacy)
    "ClaudeSDKClientManager",

    # Phase 1 - Permission Service (Legacy)
    "PermissionService",

    # Phase 1 - Message Processing (Legacy)
    "MessageProcessor",
    "EventBroadcaster",

    # Exceptions (Phase 1 + Phase 2)
    "ClientAlreadyExistsError",
    "ClientNotFoundError",
    "SDKConnectionError",
    "SDKError",
    "SDKRuntimeError",
    "PermissionDeniedError",
    "CircuitBreakerOpenError",

    # Phase 1 - Hook Handlers (Legacy)
    "create_audit_hook",
    "create_tool_tracking_hook",
    "create_cost_tracking_hook",
    "create_validation_hook",
    "create_rate_limit_hook",
    "create_notification_hook",
    "create_webhook_hook",

    # Phase 2 - Core Components
    "ClientConfig",
    "ClientMetrics",
    "ClientState",
    "OptionsBuilder",
    "EnhancedClaudeClient",
    "SessionManager",

    # Phase 2 - Handlers
    "MessageHandler",
    "StreamHandler",
    "ResultHandler",
    "ErrorHandler",

    # Phase 2 - Execution Strategies
    "BaseExecutor",
    "InteractiveExecutor",
    "BackgroundExecutor",
    "ExecutionResult",
    "ForkedExecutor",
    "ExecutorFactory",

    # Phase 2 - Retry & Resilience
    "RetryManager",
    "RetryPolicy",
    "CircuitBreaker",
    "CircuitBreakerState",

    # Phase 3 - Hook System
    "BaseHook",
    "HookType",
    "HookContext",
    "HookManager",
    "HookRegistry",
    "AuditHook",
    "MetricsHook",
    "ValidationHook",
    "NotificationHook",

    # Phase 3 - Permission System
    "BasePolicy",
    "PermissionContext",
    "PolicyEngine",
    "PermissionManager",
    "FileAccessPolicy",
    "CommandPolicy",
    "NetworkPolicy",
    "ToolWhitelistPolicy",
    "ToolBlacklistPolicy",

    # Phase 3 - MCP Integration
    "MCPServerConfig",
    "MCPServerType",
    "MCPServerManager",
    "ToolRegistry",

    # Phase 3 - Persistence Layer
    "SessionPersister",
    "MetricsPersister",
    "StorageArchiver",
]

