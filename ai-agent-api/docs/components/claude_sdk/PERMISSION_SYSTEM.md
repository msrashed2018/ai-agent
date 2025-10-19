# Permission System

## Purpose

The Permission System provides policy-based access control for tool execution in Claude SDK sessions. It implements a flexible, extensible framework where custom policies can be registered to evaluate and control which tools can be executed and under what conditions.

The system has two implementations:

1. **Phase 1 (Legacy)**: `PermissionService` - Direct permission checking with hardcoded rules
2. **Phase 3 (NEW)**: `PermissionManager` + `PolicyEngine` - Policy-based architecture with extensible policies

Both integrate with the Claude SDK's `can_use_tool` callback mechanism.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  ExecutorFactory.create_executor()                           │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 3 (NEW - Policy-Based)                   │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  PermissionManager                               │ │ │
│  │  │    • create_callback() → permission_callback     │ │ │
│  │  │    • can_use_tool() → evaluate all policies      │ │ │
│  │  │    • Log all permission decisions to DB          │ │ │
│  │  │    • Optional caching                             │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │    ↓                                                  │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  PolicyEngine                                    │ │ │
│  │  │    • register_policy(policy)                     │ │ │
│  │  │    • evaluate(tool_name, input, context)         │ │ │
│  │  │    • Evaluate policies in priority order         │ │ │
│  │  │    • First DENY stops evaluation                 │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │    ↓                                                  │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  BasePolicy (Abstract)                           │ │ │
│  │  │    • evaluate() → Allow/Deny                     │ │ │
│  │  │    • applies_to_tool() → bool                    │ │ │
│  │  │    • priority property                           │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │         ↑           ↑            ↑         ↑          │ │
│  │  ┌──────┴───┬──────┴───┬────────┴───┬─────┴───────┐ │ │
│  │  │FileAccess│ Command  │  Network   │  Tool       │ │ │
│  │  │  Policy  │  Policy  │  Policy    │Whitelist/   │ │ │
│  │  │          │          │            │Blacklist    │ │ │
│  │  └──────────┴──────────┴────────────┴─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Phase 1 (Legacy - Rule-Based)                  │ │
│  │  PermissionService                                     │ │
│  │    • create_permission_callback()                      │ │
│  │    • check_tool_permission()                           │ │
│  │    • Hardcoded checks:                                 │ │
│  │      - _check_bash_permission()                        │ │
│  │      - _check_file_write_permission()                  │ │
│  │      - _check_mcp_tool_permission()                    │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Claude SDK                                                  │
│  └─> ClaudeAgentOptions(can_use_tool=permission_callback)   │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes & Interfaces

### Phase 3: BasePolicy (Abstract Interface)

**File**: [app/claude_sdk/permissions/base_policy.py](../../app/claude_sdk/permissions/base_policy.py)

```python
# Lines 8-92
class BasePolicy(ABC):
    """Abstract base for permission policies."""

    @abstractmethod
    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate permission for tool execution.

        Returns:
            PermissionResultAllow() to allow
            PermissionResultDeny(message="...", interrupt=False) to deny
        """

    @property
    def priority(self) -> int:
        """Execution priority (lower = higher priority). Default: 100"""
        return 100

    @property
    @abstractmethod
    def policy_name(self) -> str:
        """Unique policy name."""

    def applies_to_tool(self, tool_name: str) -> bool:
        """Check if policy applies to tool. Default: all tools"""
        return True
```

### Phase 3: PolicyEngine

**File**: [app/claude_sdk/permissions/policy_engine.py](../../app/claude_sdk/permissions/policy_engine.py)

```python
# Lines 12-117
class PolicyEngine:
    """Evaluate policies in priority order.

    First policy that denies stops evaluation and returns denial.
    If no policies deny, access is allowed.
    """

    def __init__(self):
        self._policies: List[BasePolicy] = []

    def register_policy(self, policy: BasePolicy) -> None:
        """Register policy and sort by priority."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority)

    def get_policies(self, tool_name: str) -> List[BasePolicy]:
        """Get policies that apply to tool."""
        return [p for p in self._policies if p.applies_to_tool(tool_name)]

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate all applicable policies.

        Returns first denial or allow if all policies allow.
        """
        applicable_policies = self.get_policies(tool_name)

        if not applicable_policies:
            return PermissionResultAllow()  # No policies = allow

        for policy in applicable_policies:
            result = await policy.evaluate(tool_name, input_data, context)
            if isinstance(result, PermissionResultDeny):
                return result  # First denial stops evaluation

        return PermissionResultAllow()  # All policies allowed
```

### Phase 3: PermissionManager

**File**: [app/claude_sdk/permissions/permission_manager.py](../../app/claude_sdk/permissions/permission_manager.py)

```python
# Lines 18-264
class PermissionManager:
    """Orchestrate permission checking with policy engine and logging."""

    def __init__(
        self,
        db: AsyncSession,
        policy_engine: PolicyEngine,
        permission_decision_repo: PermissionDecisionRepository,
        enable_cache: bool = True
    ):
        self.policy_engine = policy_engine
        self._decision_cache: Dict[str, PermissionResult] = {}

    def create_callback(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        working_directory: Optional[str] = None
    ) -> Callable:
        """Create permission callback for SDK.

        Returns async callback: (tool_name, input_data, context) → PermissionResult
        """
        async def permission_callback(tool_name, input_data, context):
            return await self.can_use_tool(
                tool_name, input_data, context, session_id, user_id
            )
        return permission_callback

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext,
        session_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Main permission check method.

        1. Check cache (if enabled)
        2. Evaluate policies via PolicyEngine
        3. Log decision to database
        4. Cache decision (if enabled)
        5. Return result
        """
        # Check cache
        if self.enable_cache:
            cache_key = self._make_cache_key(tool_name, input_data)
            if cache_key in self._decision_cache:
                return self._decision_cache[cache_key]

        # Evaluate policies
        result = await self.policy_engine.evaluate(tool_name, input_data, context)

        # Log decision
        await self._log_decision(session_id, tool_name, input_data, context, result, user_id)

        # Cache result
        if self.enable_cache:
            self._decision_cache[cache_key] = result

        return result
```

## Built-in Policies

### FileAccessPolicy

**File**: [app/claude_sdk/permissions/policies/file_access_policy.py](../../app/claude_sdk/permissions/policies/file_access_policy.py)

**Purpose**: Restricts file read/write operations to allowed paths.

```python
# Lines 13-132
class FileAccessPolicy(BasePolicy):
    """Restrict file system access."""

    def __init__(
        self,
        restricted_read_paths: List[str],  # Paths that cannot be read
        allowed_write_paths: List[str]      # Paths where writes allowed
    ):
        self.restricted_read_paths = [Path(p).expanduser() for p in restricted_read_paths]
        self.allowed_write_paths = [Path(p).expanduser() for p in allowed_write_paths]

    @property
    def policy_name(self) -> str:
        return "file_access_policy"

    @property
    def priority(self) -> int:
        return 10  # High priority for security

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name in ["read_file", "Read", "write_file", "Write", "Edit"]

    async def evaluate(self, tool_name, input_data, context):
        file_path = input_data.get("file_path") or input_data.get("path", "")
        expanded_path = Path(file_path).expanduser()

        # Check read restrictions
        if tool_name in ["read_file", "Read"]:
            for restricted in self.restricted_read_paths:
                if str(expanded_path).startswith(str(restricted)):
                    return PermissionResultDeny(
                        message=f"Reading restricted file blocked: {file_path}",
                        interrupt=False
                    )

        # Check write restrictions
        elif tool_name in ["write_file", "Write", "Edit"]:
            is_allowed = any(
                str(expanded_path).startswith(str(allowed))
                for allowed in self.allowed_write_paths
            )
            if not is_allowed:
                return PermissionResultDeny(
                    message=f"File write not allowed in: {file_path}",
                    interrupt=False
                )

        return PermissionResultAllow()
```

**Example Usage**:
```python
policy = FileAccessPolicy(
    restricted_read_paths=["/etc/passwd", "~/.ssh/", "~/.aws/credentials"],
    allowed_write_paths=["/tmp/", "/workspace/session_123/"]
)
policy_engine.register_policy(policy)
```

### CommandPolicy

**File**: [app/claude_sdk/permissions/policies/command_policy.py](../../app/claude_sdk/permissions/policies/command_policy.py)

**Purpose**: Whitelists or blacklists specific bash commands.

```python
class CommandPolicy(BasePolicy):
    """Whitelist or blacklist commands."""

    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,  # Whitelist
        blocked_commands: Optional[List[str]] = None   # Blacklist
    ):
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or []

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name == "Bash"

    async def evaluate(self, tool_name, input_data, context):
        command = input_data.get("command", "")
        cmd_name = command.split()[0] if command.strip() else ""

        # Blacklist check
        if cmd_name in self.blocked_commands:
            return PermissionResultDeny(
                message=f"Command blocked: {cmd_name}",
                interrupt=False
            )

        # Whitelist check (if enabled)
        if self.allowed_commands and cmd_name not in self.allowed_commands:
            return PermissionResultDeny(
                message=f"Command not in whitelist: {cmd_name}",
                interrupt=False
            )

        return PermissionResultAllow()
```

**Example Usage**:
```python
# Whitelist approach
policy = CommandPolicy(
    allowed_commands=["ls", "cat", "grep", "find", "echo"]
)

# Blacklist approach
policy = CommandPolicy(
    blocked_commands=["rm", "dd", "mkfs", "chmod", "chown"]
)
```

### NetworkPolicy

**File**: [app/claude_sdk/permissions/policies/network_policy.py](../../app/claude_sdk/permissions/policies/network_policy.py)

**Purpose**: Restricts network access to allowed domains.

```python
class NetworkPolicy(BasePolicy):
    """Restrict network access."""

    def __init__(
        self,
        allowed_domains: List[str],  # Whitelist of domains
        blocked_domains: List[str] = []  # Blacklist
    ):
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name in ["WebFetch", "fetch", "curl", "wget"]

    async def evaluate(self, tool_name, input_data, context):
        url = input_data.get("url", "")
        domain = self._extract_domain(url)

        # Check blacklist
        if domain in self.blocked_domains:
            return PermissionResultDeny(
                message=f"Access to blocked domain: {domain}",
                interrupt=False
            )

        # Check whitelist
        if not any(domain.endswith(allowed) for allowed in self.allowed_domains):
            return PermissionResultDeny(
                message=f"Domain not in whitelist: {domain}",
                interrupt=False
            )

        return PermissionResultAllow()
```

### ToolWhitelistPolicy

**File**: [app/claude_sdk/permissions/policies/tool_whitelist_policy.py](../../app/claude_sdk/permissions/policies/tool_whitelist_policy.py)

**Purpose**: Only allows explicitly whitelisted tools.

```python
class ToolWhitelistPolicy(BasePolicy):
    """Only allow whitelisted tools."""

    def __init__(self, allowed_tools: List[str]):
        self.allowed_tools = allowed_tools

    @property
    def policy_name(self) -> str:
        return "tool_whitelist_policy"

    @property
    def priority(self) -> int:
        return 5  # Very high priority

    def applies_to_tool(self, tool_name: str) -> bool:
        return True  # Applies to all tools

    async def evaluate(self, tool_name, input_data, context):
        if tool_name not in self.allowed_tools:
            return PermissionResultDeny(
                message=f"Tool not in whitelist: {tool_name}",
                interrupt=False
            )
        return PermissionResultAllow()
```

### ToolBlacklistPolicy

**File**: [app/claude_sdk/permissions/policies/tool_blacklist_policy.py](../../app/claude_sdk/permissions/policies/tool_blacklist_policy.py)

**Purpose**: Blocks specific tools.

```python
class ToolBlacklistPolicy(BasePolicy):
    """Block specific tools."""

    def __init__(self, blocked_tools: List[str]):
        self.blocked_tools = blocked_tools

    def applies_to_tool(self, tool_name: str) -> bool:
        return tool_name in self.blocked_tools

    async def evaluate(self, tool_name, input_data, context):
        return PermissionResultDeny(
            message=f"Tool is blacklisted: {tool_name}",
            interrupt=False
        )
```

## Phase 1: PermissionService (Legacy)

**File**: [app/claude_sdk/permission_service.py](../../app/claude_sdk/permission_service.py)

**Purpose**: Legacy permission service with hardcoded rules.

```python
# Lines 32-371
class PermissionService:
    """Centralized tool permission management (Legacy)."""

    def __init__(
        self,
        db: AsyncSession,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        mcp_server_repo: MCPServerRepository,
        audit_service: AuditService,
    ):
        # Dangerous bash command patterns
        self.dangerous_commands = [
            r"rm\s+-rf\s+/",  # Delete root
            r"mkfs",  # Format filesystem
            r"dd\s+if=.*of=/dev/",  # Direct disk write
            # ... more patterns
        ]

        # System paths blocked from write
        self.blocked_paths = ["/etc", "/usr", "/bin", "/sbin", "/sys", "/proc", "/boot", "/dev", "/root"]

    async def check_tool_permission(
        self,
        session_id: UUID,
        user_id: UUID,
        tool_name: str,
        tool_input: dict,
        context: Optional[ToolPermissionContext] = None,
    ) -> PermissionResult:
        """Check permission with hardcoded rules."""

        # Route to specific checker
        if tool_name == "Bash":
            return await self._check_bash_permission(...)
        elif tool_name in ["Write", "Edit", "MultiEdit"]:
            return await self._check_file_write_permission(...)
        elif tool_name.startswith("mcp__"):
            return await self._check_mcp_tool_permission(...)
        else:
            return PermissionResultAllow()

    def create_permission_callback(self, session_id: UUID, user_id: UUID):
        """Create callback for SDK."""
        async def permission_callback(tool_name, tool_input, context):
            return await self.check_tool_permission(
                session_id, user_id, tool_name, tool_input, context
            )
        return permission_callback
```

## Policy Evaluation Flow

```
SDK calls can_use_tool callback
  ↓
PermissionManager.can_use_tool(tool_name, input_data, context, session_id)
  ↓
1. Check cache (if enabled)
   if cache_key in _decision_cache:
       return cached_result
  ↓
2. Evaluate policies via PolicyEngine
   PolicyEngine.evaluate(tool_name, input_data, context)
     ↓
     Get applicable policies for tool_name
       applicable_policies = [p for p in _policies if p.applies_to_tool(tool_name)]
     ↓
     Evaluate in priority order (lowest priority number first)
       for policy in sorted(applicable_policies, key=lambda p: p.priority):
           result = await policy.evaluate(tool_name, input_data, context)
           if isinstance(result, PermissionResultDeny):
               return result  # STOP - first denial wins
     ↓
     All policies allowed
       return PermissionResultAllow()
  ↓
3. Log decision to database
   _log_decision(session_id, tool_name, decision, reason)
     └─> Create PermissionDecisionModel record
  ↓
4. Cache decision (if enabled)
   _decision_cache[cache_key] = result
  ↓
5. Return result to SDK
   return PermissionResultAllow() or PermissionResultDeny(...)
```

## Configuration

### Registering Policies in ExecutorFactory

From [app/claude_sdk/execution/executor_factory.py:129-142](../../app/claude_sdk/execution/executor_factory.py:129-142):

```python
# Initialize PermissionManager and PolicyEngine
policy_engine = PolicyEngine()
permission_manager = PermissionManager(db, policy_engine, permission_decision_repo)

# Register policies based on session configuration
# Example: Register FileAccessPolicy
from app.claude_sdk.permissions.policies.file_access_policy import FileAccessPolicy

file_policy = FileAccessPolicy(
    restricted_read_paths=["/etc/passwd", "~/.ssh/"],
    allowed_write_paths=[session.working_directory_path]
)
policy_engine.register_policy(file_policy)

# Create permission callback
permission_callback = permission_manager.create_callback(
    session_id=session.id,
    user_id=session.user_id,
    working_directory=session.working_directory_path
)
```

## Common Tasks

### How to Create a Custom Policy

```python
from app.claude_sdk.permissions.base_policy import BasePolicy
from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

class MyCustomPolicy(BasePolicy):
    @property
    def policy_name(self) -> str:
        return "my_custom_policy"

    @property
    def priority(self) -> int:
        return 50  # Medium priority

    def applies_to_tool(self, tool_name: str) -> bool:
        # Limit to specific tools
        return tool_name in ["Bash", "Write"]

    async def evaluate(self, tool_name, input_data, context):
        # Your custom logic
        if should_deny:
            return PermissionResultDeny(
                message="Custom policy violation",
                interrupt=False
            )
        return PermissionResultAllow()
```

### How to Register and Use Policies

```python
# 1. Create policy engine
policy_engine = PolicyEngine()

# 2. Register policies (in priority order)
policy_engine.register_policy(ToolWhitelistPolicy(["Bash", "Read", "Write"]))  # Priority 5
policy_engine.register_policy(FileAccessPolicy(...))  # Priority 10
policy_engine.register_policy(CommandPolicy(...))  # Priority 100
policy_engine.register_policy(MyCustomPolicy())  # Priority 50

# 3. Create permission manager
permission_manager = PermissionManager(db, policy_engine, permission_decision_repo)

# 4. Create callback for SDK
permission_callback = permission_manager.create_callback(
    session_id=session_id,
    user_id=user_id
)

# 5. Use in ClaudeAgentOptions
options = ClaudeAgentOptions(
    can_use_tool=permission_callback,
    # ... other options
)
```

### How to View Permission Decisions

```python
# Query from database
from app.repositories.permission_decision_repository import PermissionDecisionRepository

permission_repo = PermissionDecisionRepository(db)

# Get all decisions for session
decisions = await permission_repo.get_by_session(session_id)

for decision in decisions:
    print(f"{decision.tool_name}: {decision.decision} - {decision.reason}")
```

## Permission Decision Persistence

All permission decisions are logged to the database:

```python
# From app/models/permission_decision.py
class PermissionDecisionModel:
    id: UUID
    session_id: UUID
    tool_call_id: Optional[UUID]
    tool_use_id: str
    tool_name: str
    input_data: dict  # Tool input parameters
    context_data: dict  # SDK context
    decision: str  # "allowed" | "denied"
    reason: str  # Decision reason
    policy_applied: Optional[str]  # Which policy made decision
    created_at: datetime
```

## Related Files

**Phase 3 (NEW - Policy-Based)**:
- [app/claude_sdk/permissions/base_policy.py](../../app/claude_sdk/permissions/base_policy.py) - Base policy interface
- [app/claude_sdk/permissions/policy_engine.py](../../app/claude_sdk/permissions/policy_engine.py) - Policy evaluation engine
- [app/claude_sdk/permissions/permission_manager.py](../../app/claude_sdk/permissions/permission_manager.py) - Permission orchestration
- [app/claude_sdk/permissions/policies/file_access_policy.py](../../app/claude_sdk/permissions/policies/file_access_policy.py) - File access restrictions
- [app/claude_sdk/permissions/policies/command_policy.py](../../app/claude_sdk/permissions/policies/command_policy.py) - Command whitelist/blacklist
- [app/claude_sdk/permissions/policies/network_policy.py](../../app/claude_sdk/permissions/policies/network_policy.py) - Network restrictions
- [app/claude_sdk/permissions/policies/tool_whitelist_policy.py](../../app/claude_sdk/permissions/policies/tool_whitelist_policy.py) - Tool whitelist
- [app/claude_sdk/permissions/policies/tool_blacklist_policy.py](../../app/claude_sdk/permissions/policies/tool_blacklist_policy.py) - Tool blacklist

**Phase 1 (Legacy)**:
- [app/claude_sdk/permission_service.py](../../app/claude_sdk/permission_service.py) - Legacy permission service

**Dependencies**:
- [app/claude_sdk/execution/executor_factory.py](../../app/claude_sdk/execution/executor_factory.py) - Where policies are registered
- [app/repositories/permission_decision_repository.py](../../app/repositories/permission_decision_repository.py) - Permission decision persistence
- [app/models/permission_decision.py](../../app/models/permission_decision.py) - Permission decision model

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [HOOK_SYSTEM.md](./HOOK_SYSTEM.md) - Lifecycle hooks (complementary to permissions)
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - How permissions integrate with executors

## Keywords

permission-system, policy-engine, base-policy, permission-manager, access-control, tool-permissions, file-access-policy, command-policy, network-policy, tool-whitelist, tool-blacklist, policy-based-access-control, permission-callback, can-use-tool, permission-result, permission-decision, policy-evaluation, priority-based-evaluation, extensible-policies, custom-policies, permission-logging, permission-caching, security-policies, tool-access-control
