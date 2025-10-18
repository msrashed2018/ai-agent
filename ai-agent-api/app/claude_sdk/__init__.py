"""Claude SDK integration layer.

Integration components for the official claude-agent-sdk package.
Provides business logic, permission callbacks, and hooks for our service.
"""

from app.claude_sdk.client_manager import ClaudeSDKClientManager
from app.claude_sdk.permission_service import PermissionService
from app.claude_sdk.exceptions import (
    ClientAlreadyExistsError,
    ClientNotFoundError,
    SDKConnectionError,
    SDKError,
    SDKRuntimeError,
    PermissionDeniedError,
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

__all__ = [
    # Client Manager
    "ClaudeSDKClientManager",
    
    # Permission Service
    "PermissionService",
    
    # Message Processing
    "MessageProcessor",
    "EventBroadcaster",
    
    # Exceptions
    "ClientAlreadyExistsError",
    "ClientNotFoundError",
    "SDKConnectionError",
    "SDKError",
    "SDKRuntimeError",
    "PermissionDeniedError",
    
    # Hook Handlers
    "create_audit_hook",
    "create_tool_tracking_hook",
    "create_cost_tracking_hook",
    "create_validation_hook",
    "create_rate_limit_hook",
    "create_notification_hook",
    "create_webhook_hook",
]
