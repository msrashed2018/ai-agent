# Hook System

## Purpose

The Hook System provides lifecycle event interception for Claude SDK sessions, enabling observability, auditing, validation, and custom logic at specific points in the execution flow. It implements an extensible hook architecture where custom hooks can be registered to execute before/after tool usage, on prompt submission, session stop, and other SDK events.

The system has two implementations:

1. **Phase 1 (Legacy)**: `hook_handlers.py` - Factory functions creating standalone hooks
2. **Phase 3 (NEW)**: `HookManager` + `BaseHook` - Class-based architecture with registration and orchestration

Both integrate with the Claude SDK's `hooks` parameter in `ClaudeAgentOptions`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  ExecutorFactory.create_executor()                           │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 3 (NEW - Class-Based)                    │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  HookManager                                     │ │ │
│  │  │    • register_hook(hook_type, hook, priority)   │ │ │
│  │  │    • execute_hooks(hook_type, input, context)   │ │ │
│  │  │    • build_hook_matchers() → SDK format         │ │ │
│  │  │    • Log all hook executions to DB              │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │    ↓                                                  │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  HookRegistry                                    │ │ │
│  │  │    • Maintains hooks by type and priority       │ │ │
│  │  │    • get_hooks(type) → sorted by priority       │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │    ↓                                                  │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  BaseHook (Abstract)                             │ │ │
│  │  │    • execute(input_data, tool_use_id, context)  │ │ │
│  │  │    • hook_type property                          │ │ │
│  │  │    • priority property                           │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │         ↑         ↑           ↑            ↑          │ │
│  │  ┌──────┴──┬──────┴───┬───────┴──┬─────────┴───┐    │ │
│  │  │ Audit   │ Metrics  │Validation│Notification │    │ │
│  │  │  Hook   │  Hook    │  Hook    │    Hook     │    │ │
│  │  └─────────┴──────────┴──────────┴─────────────┘    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 1 (Legacy - Factory Functions)           │ │
│  │  hook_handlers.py                                      │ │
│  │    • create_audit_hook()                               │ │
│  │    • create_tool_tracking_hook()                       │ │
│  │    • create_cost_tracking_hook()                       │ │
│  │    • create_validation_hook()                          │ │
│  │    • create_rate_limit_hook()                          │ │
│  │    • create_notification_hook()                        │ │
│  │    • create_webhook_hook()                             │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Claude SDK                                                  │
│  └─> ClaudeAgentOptions(hooks={...})                        │
└─────────────────────────────────────────────────────────────┘
```

## Hook Types

Based on the official Claude SDK, there are **6 hook types**:

```python
# From app/claude_sdk/hooks/base_hook.py:7-24
class HookType(str, Enum):
    """Available hook types in Claude SDK."""

    PRE_TOOL_USE = "PreToolUse"        # Before tool execution
    POST_TOOL_USE = "PostToolUse"      # After tool execution
    USER_PROMPT_SUBMIT = "UserPromptSubmit"  # When user submits prompt
    STOP = "Stop"                      # Before Claude concludes response
    SUBAGENT_STOP = "SubagentStop"     # Before subagent concludes
    PRE_COMPACT = "PreCompact"         # Before conversation compaction
```

## Key Classes & Interfaces

### Phase 3: BaseHook (Abstract Interface)

**File**: [app/claude_sdk/hooks/base_hook.py](../../app/claude_sdk/hooks/base_hook.py)

```python
# Lines 26-94
class BaseHook(ABC):
    """Abstract base for all hooks."""

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Execute hook logic.

        Args:
            input_data: Hook-specific input (tool info, prompt, etc.)
            tool_use_id: Tool use ID if applicable
            context: SDK context object

        Returns:
            Dictionary with at minimum:
            - continue_: bool - Whether to continue execution
            - hookSpecificOutput: dict (optional) - Additional data

        Example returns:
            # Allow and continue
            {"continue_": True}

            # Block execution
            {"continue_": False, "reason": "Validation failed"}

            # Allow with metadata
            {
                "continue_": True,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow"
                }
            }
        """

    @property
    @abstractmethod
    def hook_type(self) -> HookType:
        """Return hook type this implements."""

    @property
    def priority(self) -> int:
        """Execution priority (lower = higher priority). Default: 100"""
        return 100
```

### Phase 3: HookManager

**File**: [app/claude_sdk/hooks/hook_manager.py](../../app/claude_sdk/hooks/hook_manager.py)

```python
# Lines 19-312
class HookManager:
    """Orchestrate hook execution across all hook types."""

    def __init__(
        self,
        db: AsyncSession,
        hook_execution_repo: HookExecutionRepository
    ):
        self.db = db
        self.hook_execution_repo = hook_execution_repo
        self.registry = HookRegistry()

    async def register_hook(
        self,
        hook_type: HookType,
        hook: BaseHook,
        priority: Optional[int] = None
    ) -> None:
        """Register a hook for execution."""
        actual_priority = priority if priority is not None else hook.priority
        self.registry.register(hook_type, hook, actual_priority)

    async def execute_hooks(
        self,
        hook_type: HookType,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any,
        session_id: UUID
    ) -> Dict[str, Any]:
        """Execute all hooks for type in priority order.

        Returns merged result with at least {"continue_": bool}
        """
        hooks = self.registry.get_hooks(hook_type)

        if not hooks:
            return {"continue_": True}

        merged_result = {"continue_": True}

        for hook in hooks:
            start_time = time.time()

            try:
                # Execute hook
                hook_result = await hook.execute(input_data, tool_use_id, context)

                # Log execution
                execution_time_ms = int((time.time() - start_time) * 1000)
                await self._log_hook_execution(
                    session_id, hook_type, hook.__class__.__name__,
                    tool_use_id, input_data, hook_result, execution_time_ms, None
                )

                # Merge results
                merged_result.update(hook_result)

                # Stop if hook blocked execution
                if not hook_result.get("continue_", True):
                    break

            except Exception as e:
                # Log error and continue with other hooks
                await self._log_hook_execution(
                    session_id, hook_type, hook.__class__.__name__,
                    tool_use_id, input_data, {}, execution_time_ms,
                    f"{type(e).__name__}: {str(e)}"
                )

        return merged_result

    def build_hook_matchers(
        self,
        session_id: UUID,
        enabled_hook_types: List[HookType]
    ) -> Dict[str, List[HookMatcher]]:
        """Build SDK-compatible HookMatcher configuration.

        SDK expects:
        {
            "PreToolUse": [HookMatcher(hooks=[...])],
            "PostToolUse": [HookMatcher(hooks=[...])],
            ...
        }
        """
        hook_matchers = {}

        for hook_type in enabled_hook_types:
            hooks = self.registry.get_hooks(hook_type)

            if hooks:
                # Create wrapper that calls execute_hooks
                def create_callback(ht: HookType):
                    async def callback(input_data, tool_use_id, context):
                        return await self.execute_hooks(
                            ht, input_data, tool_use_id, context, session_id
                        )
                    return callback

                callback = create_callback(hook_type)
                matcher = HookMatcher(hooks=[callback])
                hook_matchers[hook_type.value] = [matcher]

        return hook_matchers
```

### Phase 3: HookRegistry

**File**: [app/claude_sdk/hooks/hook_registry.py](../../app/claude_sdk/hooks/hook_registry.py)

```python
# Lines 14-79
class HookRegistry:
    """Registry for managing hooks across types."""

    def __init__(self):
        self._hooks: Dict[HookType, List[RegisteredHook]] = {
            hook_type: [] for hook_type in HookType
        }

    def register(self, hook_type: HookType, hook: BaseHook, priority: int = 100):
        """Register hook for type."""
        registered_hook = RegisteredHook(hook=hook, priority=priority)
        self._hooks[hook_type].append(registered_hook)

    def get_hooks(self, hook_type: HookType) -> List[BaseHook]:
        """Get all hooks for type, sorted by priority (ascending)."""
        registered_hooks = self._hooks.get(hook_type, [])
        sorted_hooks = sorted(registered_hooks, key=lambda rh: rh.priority)
        return [rh.hook for rh in sorted_hooks]

    def clear(self, hook_type: Optional[HookType] = None):
        """Clear hooks for type or all types."""
        if hook_type:
            self._hooks[hook_type] = []
        else:
            self._hooks = {ht: [] for ht in HookType}
```

## Built-in Hook Implementations

### AuditHook

**File**: [app/claude_sdk/hooks/implementations/audit_hook.py](../../app/claude_sdk/hooks/implementations/audit_hook.py)

**Purpose**: Comprehensive audit logging of all tool executions.

```python
# Lines 12-89
class AuditHook(BaseHook):
    """Audit hook for tool execution logging."""

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        return 10  # High priority to log before other hooks

    async def execute(self, input_data, tool_use_id, context):
        tool_name = input_data.get("name") or input_data.get("tool_name", "unknown")
        tool_input = input_data.get("input", {})
        session_id = getattr(context, "session_id", None)

        await self.audit_service.log_event(
            event_type="tool_execution_attempt",
            event_category="tool",
            resource_type="tool",
            resource_id=tool_name,
            session_id=session_id,
            details={
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "tool_input": tool_input,
                "hook": "AuditHook"
            }
        )

        return {"continue_": True}
```

### MetricsHook

**File**: [app/claude_sdk/hooks/implementations/metrics_hook.py](../../app/claude_sdk/hooks/implementations/metrics_hook.py)

**Purpose**: Collect tool usage statistics.

```python
# Lines 11-104
class MetricsHook(BaseHook):
    """Metrics hook for tool usage statistics."""

    def __init__(self):
        self.tool_execution_count: Dict[str, int] = {}
        self.tool_error_count: Dict[str, int] = {}

    @property
    def hook_type(self) -> HookType:
        return HookType.POST_TOOL_USE

    @property
    def priority(self) -> int:
        return 100  # Normal priority

    async def execute(self, input_data, tool_use_id, context):
        tool_name = input_data.get("name") or input_data.get("tool_name", "unknown")
        is_error = input_data.get("is_error", False)

        # Track counts
        self.tool_execution_count[tool_name] = (
            self.tool_execution_count.get(tool_name, 0) + 1
        )
        if is_error:
            self.tool_error_count[tool_name] = (
                self.tool_error_count.get(tool_name, 0) + 1
            )

        return {
            "continue_": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "metricsCollected": {
                    "tool_name": tool_name,
                    "execution_count": self.tool_execution_count[tool_name],
                    "error_count": self.tool_error_count.get(tool_name, 0)
                }
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get collected statistics."""
        return {
            "tool_executions": self.tool_execution_count.copy(),
            "tool_errors": self.tool_error_count.copy()
        }
```

### ValidationHook

**File**: [app/claude_sdk/hooks/implementations/validation_hook.py](../../app/claude_sdk/hooks/implementations/validation_hook.py)

**Purpose**: Validate prompts for security issues.

```python
class ValidationHook(BaseHook):
    """Validation hook for prompt security."""

    def __init__(self):
        self.dangerous_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "you are now",
            "pretend you are",
            "disregard",
            "forget everything",
            # ... more patterns
        ]

    @property
    def hook_type(self) -> HookType:
        return HookType.USER_PROMPT_SUBMIT

    async def execute(self, input_data, tool_use_id, context):
        prompt = input_data.get("prompt", "")
        prompt_lower = prompt.lower()

        # Check for prompt injection
        for pattern in self.dangerous_patterns:
            if pattern in prompt_lower:
                return {
                    "decision": "block",
                    "systemMessage": "Prompt blocked: potential security issue",
                    "reason": f"Detected suspicious pattern: {pattern}"
                }

        # Check length
        if len(prompt) > 50000:
            return {
                "decision": "block",
                "systemMessage": "Prompt too long",
                "reason": f"Prompt length: {len(prompt)} exceeds limit"
            }

        return {"continue_": True}
```

### NotificationHook

**File**: [app/claude_sdk/hooks/implementations/notification_hook.py](../../app/claude_sdk/hooks/implementations/notification_hook.py)

**Purpose**: Send notifications on specific events.

```python
class NotificationHook(BaseHook):
    """Notification hook for important events."""

    def __init__(self, notification_service):
        self.notification_service = notification_service

    @property
    def hook_type(self) -> HookType:
        return HookType.POST_TOOL_USE

    async def execute(self, input_data, tool_use_id, context):
        tool_name = input_data.get("name")
        tool_response = input_data.get("tool_response", {})

        # Notify on errors
        if tool_response.get("is_error"):
            error_msg = tool_response.get("error", "Unknown error")
            user_id = getattr(context, "user_id", None)

            await self.notification_service.send_alert(
                user_id=user_id,
                title=f"Tool Error: {tool_name}",
                message=f"Tool {tool_name} failed: {error_msg[:100]}",
                severity="warning"
            )

        return {"continue_": True}
```

## Hook Execution Flow

```
SDK event occurs (PreToolUse, PostToolUse, etc.)
  ↓
SDK calls registered hook callback
  ↓
HookManager.execute_hooks(hook_type, input_data, tool_use_id, context, session_id)
  ↓
1. Get registered hooks for type
   hooks = registry.get_hooks(hook_type)
   # Returns hooks sorted by priority (ascending)
  ↓
2. Initialize merged result
   merged_result = {"continue_": True}
  ↓
3. Execute each hook in priority order
   for hook in hooks:
       ├─> Start timer
       │
       ├─> Execute hook
       │     hook_result = await hook.execute(input_data, tool_use_id, context)
       │
       ├─> Log hook execution to database
       │     _log_hook_execution(session_id, hook_type, hook_name, ...)
       │       └─> Create HookExecutionModel record
       │
       ├─> Merge results
       │     merged_result.update(hook_result)
       │
       └─> Check if should continue
             if not hook_result.get("continue_", True):
                 break  # Stop hook chain
  ↓
4. Return merged result to SDK
   return merged_result  # {"continue_": True/False, ...}
```

## Hook Registration in ExecutorFactory

From [app/claude_sdk/execution/executor_factory.py:82-127](../../app/claude_sdk/execution/executor_factory.py:82-127):

```python
# Initialize HookManager
hook_manager = HookManager(db, hook_execution_repo)

# Register hooks based on session.hooks_enabled
if session.hooks_enabled:
    for hook_type_name in session.hooks_enabled:
        hook_type = HookType(hook_type_name)

        # Register PreToolUse hooks
        if hook_type == HookType.PRE_TOOL_USE:
            audit_hook = AuditHook(db)
            await hook_manager.register_hook(hook_type, audit_hook, priority=10)

            validation_hook = ValidationHook(db)
            await hook_manager.register_hook(hook_type, validation_hook, priority=20)

        # Register PostToolUse hooks
        elif hook_type == HookType.POST_TOOL_USE:
            metrics_hook = MetricsHook(db)
            await hook_manager.register_hook(hook_type, metrics_hook, priority=10)

        # Register Stop hooks
        elif hook_type == HookType.STOP:
            notification_hook = NotificationHook(db)
            await hook_manager.register_hook(hook_type, notification_hook, priority=10)

# Build SDK-compatible hook matchers
hooks_dict = hook_manager.build_hook_matchers(session.id, enabled_hook_types)

# Use in ClaudeAgentOptions
client_config = ClientConfig(
    session_id=session.id,
    hooks=hooks_dict,  # {"PreToolUse": [HookMatcher(...)], ...}
    # ... other config
)
```

## Configuration

### Enabling Hooks in Session

```python
# Create session with hooks enabled
session = Session(
    hooks_enabled=["PreToolUse", "PostToolUse", "Stop"],
    # ... other config
)
```

### Hook Priorities

Lower priority number = executed first:

| Priority | Typical Usage |
|----------|---------------|
| 1-10 | Security-critical hooks (audit, validation) |
| 11-50 | Important business logic |
| 51-100 | Normal hooks (metrics, notifications) |
| 100+ | Low-priority hooks |

## Common Tasks

### How to Create a Custom Hook

```python
from app.claude_sdk.hooks.base_hook import BaseHook, HookType

class MyCustomHook(BaseHook):
    @property
    def hook_type(self) -> HookType:
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        return 50  # Medium priority

    async def execute(self, input_data, tool_use_id, context):
        # Your custom logic
        tool_name = input_data.get("name")

        if should_block:
            return {
                "continue_": False,
                "reason": "Custom validation failed"
            }

        return {
            "continue_": True,
            "hookSpecificOutput": {
                "customData": "your data here"
            }
        }
```

### How to Register Hooks

```python
# 1. Initialize HookManager
hook_manager = HookManager(db, hook_execution_repo)

# 2. Register hooks (in priority order)
await hook_manager.register_hook(HookType.PRE_TOOL_USE, AuditHook(db), priority=10)
await hook_manager.register_hook(HookType.PRE_TOOL_USE, ValidationHook(), priority=20)
await hook_manager.register_hook(HookType.PRE_TOOL_USE, MyCustomHook(), priority=50)

await hook_manager.register_hook(HookType.POST_TOOL_USE, MetricsHook(), priority=10)
await hook_manager.register_hook(HookType.POST_TOOL_USE, NotificationHook(svc), priority=20)

# 3. Build SDK hook matchers
hooks_dict = hook_manager.build_hook_matchers(
    session_id=session_id,
    enabled_hook_types=[HookType.PRE_TOOL_USE, HookType.POST_TOOL_USE]
)

# 4. Use in ClaudeAgentOptions
options = ClaudeAgentOptions(hooks=hooks_dict, ...)
```

### How to View Hook Execution History

```python
from app.repositories.hook_execution_repository import HookExecutionRepository

hook_exec_repo = HookExecutionRepository(db)

# Get all hook executions for session
executions = await hook_exec_repo.get_by_session(session_id)

for execution in executions:
    print(f"{execution.hook_name}: {execution.execution_time_ms}ms")
    if execution.error_message:
        print(f"  Error: {execution.error_message}")
```

## Hook Execution Persistence

All hook executions are logged:

```python
# From app/models/hook_execution.py
class HookExecutionModel:
    id: UUID
    session_id: UUID
    tool_call_id: Optional[UUID]
    hook_name: str  # "PreToolUse_AuditHook"
    tool_use_id: str
    tool_name: str
    input_data: dict  # Hook input
    output_data: dict  # Hook output
    context_data: dict  # SDK context
    execution_time_ms: int  # Duration
    error_message: Optional[str]  # If hook failed
    created_at: datetime
```

## Phase 1: Legacy Hook Handlers

**File**: [app/claude_sdk/hook_handlers.py](../../app/claude_sdk/hook_handlers.py)

Factory functions for creating standalone hooks:

```python
# Lines 28-92
def create_audit_hook(session_id: UUID, audit_service: AuditService):
    """Create audit logging hook."""
    async def audit_hook(input_data, tool_use_id, context):
        # Log tool execution
        await audit_service.log_tool_executed(...)
        return {"continue_": True}
    return audit_hook

# Lines 95-149
def create_tool_tracking_hook(session_id: UUID, db: AsyncSession, tool_call_repo):
    """Create hook for tracking tool execution times."""
    tool_start_times = {}
    async def tracking_hook(input_data, tool_use_id, context):
        # Track start/end times
        return {"continue_": True}
    return tracking_hook

# Lines 152-196
def create_cost_tracking_hook(session_id: UUID, db: AsyncSession, session_repo):
    """Create hook for tracking API costs."""

# Lines 199-258
def create_validation_hook():
    """Create prompt validation hook."""

# Lines 261-310
def create_rate_limit_hook(user_id: UUID, rate_limiter):
    """Create rate limiting hook."""

# Lines 313-369
def create_notification_hook(user_id: UUID, notification_service):
    """Create notification hook."""

# Lines 372-431
def create_webhook_hook(webhook_config: dict):
    """Create webhook hook for external integrations."""
```

## Related Files

**Phase 3 (NEW - Class-Based)**:
- [app/claude_sdk/hooks/base_hook.py](../../app/claude_sdk/hooks/base_hook.py) - Base hook interface, HookType enum
- [app/claude_sdk/hooks/hook_manager.py](../../app/claude_sdk/hooks/hook_manager.py) - Hook orchestration
- [app/claude_sdk/hooks/hook_registry.py](../../app/claude_sdk/hooks/hook_registry.py) - Hook registration
- [app/claude_sdk/hooks/hook_context.py](../../app/claude_sdk/hooks/hook_context.py) - Hook context dataclass
- [app/claude_sdk/hooks/implementations/audit_hook.py](../../app/claude_sdk/hooks/implementations/audit_hook.py) - Audit logging
- [app/claude_sdk/hooks/implementations/metrics_hook.py](../../app/claude_sdk/hooks/implementations/metrics_hook.py) - Metrics collection
- [app/claude_sdk/hooks/implementations/validation_hook.py](../../app/claude_sdk/hooks/implementations/validation_hook.py) - Prompt validation
- [app/claude_sdk/hooks/implementations/notification_hook.py](../../app/claude_sdk/hooks/implementations/notification_hook.py) - Event notifications

**Phase 1 (Legacy)**:
- [app/claude_sdk/hook_handlers.py](../../app/claude_sdk/hook_handlers.py) - Factory functions

**Dependencies**:
- [app/claude_sdk/execution/executor_factory.py](../../app/claude_sdk/execution/executor_factory.py) - Where hooks are registered
- [app/repositories/hook_execution_repository.py](../../app/repositories/hook_execution_repository.py) - Hook execution persistence
- [app/models/hook_execution.py](../../app/models/hook_execution.py) - Hook execution model
- [app/services/audit_service.py](../../app/services/audit_service.py) - Audit logging service

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [PERMISSION_SYSTEM.md](./PERMISSION_SYSTEM.md) - Permission policies (complementary to hooks)
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - How hooks integrate with executors

## Keywords

hook-system, lifecycle-hooks, base-hook, hook-manager, hook-registry, hook-types, pre-tool-use, post-tool-use, user-prompt-submit, stop-hook, subagent-stop, pre-compact, audit-hook, metrics-hook, validation-hook, notification-hook, rate-limit-hook, webhook-hook, hook-execution, hook-persistence, hook-priority, hook-matchers, event-interception, observability, audit-logging, tool-tracking, cost-tracking, prompt-validation, security-hooks, custom-hooks, extensible-hooks
