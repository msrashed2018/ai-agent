# Phase 3: Advanced Features (Hooks, Permissions, MCP & Persistence)

**Epic**: Claude SDK Module Rebuild - Extensibility & Security Layer
**Phase**: 3 of 4
**Status**: Pending Phase 2 Completion
**Estimated Effort**: 2 weeks

---

## User Story

**As a** Platform Engineer and Security Administrator
**I want** a comprehensive hook system, permission policies, MCP server integration, and persistence layer
**So that** I can customize SDK behavior, enforce security policies, integrate external tools, and maintain complete audit trails of all interactions

---

## Business Value

- **Extensibility**: Plugin architecture allows custom hooks without modifying core code
- **Security**: Policy-based permissions prevent unauthorized operations
- **Tool Integration**: MCP servers enable Kubernetes, databases, APIs, and custom tools
- **Audit Compliance**: Complete audit trail of hooks, permissions, tool usage
- **Storage Management**: Automatic archival to S3 for cost savings and retention

---

## Acceptance Criteria

### ✅ Hook System (`app/claude_sdk/hooks/`)
- [ ] `HookManager` orchestrates hook execution across all hook types
- [ ] `HookRegistry` discovers and registers hooks dynamically
- [ ] `BaseHook` abstract class for all hooks
- [ ] Built-in hooks implemented: `AuditHook`, `ToolTrackingHook`, `MetricsHook`, `PersistenceHook`, `NotificationHook`
- [ ] All 6 SDK hook types supported: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact
- [ ] Hook execution logged to `hook_executions` table
- [ ] Hook errors handled gracefully without breaking execution
- [ ] Hook chaining and priority ordering works correctly

### ✅ Permission System (`app/claude_sdk/permissions/`)
- [ ] `PermissionManager` orchestrates permission checking
- [ ] `PolicyEngine` evaluates permission policies
- [ ] `PermissionPolicy` abstract class for custom policies
- [ ] Built-in policies implemented: `FileAccessPolicy`, `CommandPolicy`, `MCPPolicy`
- [ ] All permission decisions logged to `permission_decisions` table
- [ ] Permission cache for performance
- [ ] Permission denials include clear reason messages

### ✅ MCP Integration (`app/claude_sdk/mcp/`)
- [ ] `MCPServerManager` manages MCP server lifecycle
- [ ] `ServerConfigBuilder` builds SDK vs External MCP configs
- [ ] `ToolRegistry` discovers available tools from MCP servers
- [ ] Support SDK MCP servers (in-process with `@tool` decorator)
- [ ] Support External MCP servers (subprocess: filesystem, kubernetes, etc.)
- [ ] MCP tool calls tracked in `tool_calls` table
- [ ] MCP server health checks

### ✅ Persistence Layer (`app/claude_sdk/persistence/`)
- [ ] `SessionPersister` saves session state, messages, metrics
- [ ] `MetricsPersister` persists performance and cost metrics
- [ ] `ArtifactPersister` saves tool outputs, files, logs
- [ ] `StorageArchiver` archives working directories to S3
- [ ] All persistence operations are async
- [ ] Persistence errors logged but don't break execution
- [ ] Archives compressed and uploaded to S3 with manifest

### ✅ Testing
- [ ] Unit tests for all hooks (execution, error handling, chaining)
- [ ] Unit tests for all policies (allow, deny, edge cases)
- [ ] Unit tests for MCP integration (SDK and External servers)
- [ ] Unit tests for persistence layer (save, archive, retrieve)
- [ ] Integration tests for hook system with real database
- [ ] Integration tests for permission system with real policies
- [ ] Integration tests for S3 archival (using localstack or moto)
- [ ] Test coverage ≥ 80%

### ✅ Documentation
- [ ] Hook development guide (creating custom hooks)
- [ ] Permission policy development guide
- [ ] MCP server integration guide
- [ ] Archive and retrieval usage guide

---

## Technical Tasks

### 1. Hook System

#### 1.1 Create `HookManager` (`app/claude_sdk/hooks/hook_manager.py`)

```python
class HookManager:
    """Orchestrate hook execution across all hook types."""

    def __init__(self, db: AsyncSession, hook_execution_repo: HookExecutionRepository):
        self.db = db
        self.hook_execution_repo = hook_execution_repo
        self.registry = HookRegistry()

    async def register_hook(
        self,
        hook_type: HookType,
        hook: BaseHook,
        priority: int = 100
    ) -> None:
        """Register hook with priority (lower number = higher priority)."""
        self.registry.register(hook_type, hook, priority)

    async def execute_hooks(
        self,
        hook_type: HookType,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Execute all hooks for given type in priority order."""

        hooks = self.registry.get_hooks(hook_type)
        result = {"continue_": True}

        for hook in sorted(hooks, key=lambda h: h.priority):
            try:
                hook_result = await hook.execute(input_data, tool_use_id, context)

                # Log hook execution
                await self._log_hook_execution(
                    hook_type=hook_type,
                    hook_name=type(hook).__name__,
                    input_data=input_data,
                    output_data=hook_result,
                    tool_use_id=tool_use_id
                )

                # Merge results
                result.update(hook_result)

                # Stop if hook says to not continue
                if not hook_result.get("continue_", True):
                    break

            except Exception as e:
                logger.error(f"Hook {type(hook).__name__} failed: {e}")
                # Continue with other hooks
                continue

        return result

    def build_hook_matchers(
        self,
        session_id: UUID,
        enabled_hooks: List[HookType]
    ) -> Dict[str, List[HookMatcher]]:
        """Build SDK HookMatcher configuration."""

        hook_matchers = {}

        for hook_type in enabled_hooks:
            matchers = []
            for hook in self.registry.get_hooks(hook_type):
                matcher = HookMatcher(
                    hook_id=f"{hook_type.value}_{type(hook).__name__}",
                    callback=lambda input_data, tool_use_id, context:
                        self.execute_hooks(hook_type, input_data, tool_use_id, context)
                )
                matchers.append(matcher)

            hook_matchers[hook_type.value] = matchers

        return hook_matchers

    async def _log_hook_execution(
        self,
        hook_type: HookType,
        hook_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        tool_use_id: Optional[str]
    ) -> None:
        """Log hook execution to database."""
        # Implementation uses hook_execution_repo.create()
```

#### 1.2 Create Built-in Hooks (`app/claude_sdk/hooks/implementations/`)

```python
# audit_hook.py
class AuditHook(BaseHook):
    """Log all tool executions for audit trail."""
    hook_type = HookType.PRE_TOOL_USE

    async def execute(self, input_data, tool_use_id, context):
        await self.audit_service.log_tool_execution(
            session_id=context.session_id,
            tool_name=input_data.get("tool_name"),
            input_data=input_data
        )
        return {"continue_": True}


# tool_tracking_hook.py
class ToolTrackingHook(PostToolUseHook):
    """Track tool usage statistics."""

    async def execute(self, input_data, tool_use_id, context):
        await self.tool_call_repo.create(
            session_id=context.session_id,
            tool_name=input_data.get("tool_name"),
            input_params=input_data.get("input"),
            output=input_data.get("output"),
            is_error=input_data.get("is_error", False)
        )
        return {"continue_": True}


# metrics_hook.py
class MetricsHook(BaseHook):
    """Collect cost and performance metrics."""

    async def execute(self, input_data, tool_use_id, context):
        # Update session metrics
        await self.metrics_collector.record_tool_execution(
            session_id=context.session_id,
            tool_name=input_data.get("tool_name"),
            duration_ms=input_data.get("duration_ms", 0)
        )
        return {"continue_": True}


# persistence_hook.py
class PersistenceHook(BaseHook):
    """Persist messages and tool calls to database."""

    async def execute(self, input_data, tool_use_id, context):
        await self.persister.save_tool_call(
            session_id=context.session_id,
            tool_use_id=tool_use_id,
            data=input_data
        )
        return {"continue_": True}
```

### 2. Permission System

#### 2.1 Create `PermissionManager` (`app/claude_sdk/permissions/permission_manager.py`)

```python
@dataclass
class PermissionDecisionLog:
    """Permission decision for audit."""
    tool_name: str
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    decision: str  # 'allow' or 'deny'
    reason: str
    timestamp: datetime


class PermissionManager:
    """Orchestrate permission checking with policy engine."""

    def __init__(
        self,
        db: AsyncSession,
        policy_engine: PolicyEngine,
        permission_decision_repo: PermissionDecisionRepository
    ):
        self.db = db
        self.policy_engine = policy_engine
        self.permission_decision_repo = permission_decision_repo
        self.decision_cache: Dict[str, PermissionResult] = {}

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ToolPermissionContext
    ) -> PermissionResult:
        """Main permission callback for SDK."""

        # Check cache first
        cache_key = self._make_cache_key(tool_name, input_data)
        if cache_key in self.decision_cache:
            return self.decision_cache[cache_key]

        # Execute all policies
        for policy in self.policy_engine.get_policies(tool_name):
            result = await policy.evaluate(tool_name, input_data, context)

            if isinstance(result, PermissionResultDeny):
                # Log denial
                await self._log_decision(
                    session_id=context.session_id,
                    tool_name=tool_name,
                    input_data=input_data,
                    context=context,
                    decision="deny",
                    reason=result.message
                )

                # Cache denial
                self.decision_cache[cache_key] = result
                return result

        # Default allow
        allow_result = PermissionResultAllow()

        await self._log_decision(
            session_id=context.session_id,
            tool_name=tool_name,
            input_data=input_data,
            context=context,
            decision="allow",
            reason="no_policy_matched"
        )

        self.decision_cache[cache_key] = allow_result
        return allow_result

    async def _log_decision(
        self,
        session_id: UUID,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ToolPermissionContext,
        decision: str,
        reason: str
    ) -> None:
        """Log permission decision to database."""
        await self.permission_decision_repo.create(
            session_id=session_id,
            tool_name=tool_name,
            input_data=input_data,
            context=self._serialize_context(context),
            decision=decision,
            reason=reason,
            interrupted=False
        )
```

#### 2.2 Create Built-in Policies (`app/claude_sdk/permissions/policies/`)

```python
# file_access_policy.py
class FileAccessPolicy(PermissionPolicy):
    """Restrict file system access."""

    def __init__(self, restricted_paths: List[str], allowed_paths: List[str]):
        self.restricted_paths = [Path(p).expanduser() for p in restricted_paths]
        self.allowed_paths = [Path(p).expanduser() for p in allowed_paths]

    async def evaluate(self, tool_name, input_data, context):
        if tool_name in ["read_file", "Read", "write_file", "Write"]:
            file_path = Path(input_data.get("file_path") or input_data.get("path", "")).expanduser()

            # Check if restricted
            for restricted in self.restricted_paths:
                if str(file_path).startswith(str(restricted)):
                    return PermissionResultDeny(
                        message=f"Access denied: {file_path} is in restricted path {restricted}",
                        interrupt=False
                    )

            # Check if in allowed paths
            if self.allowed_paths:
                allowed = any(str(file_path).startswith(str(allowed)) for allowed in self.allowed_paths)
                if not allowed:
                    return PermissionResultDeny(
                        message=f"Access denied: {file_path} not in allowed paths",
                        interrupt=False
                    )

        return PermissionResultAllow()


# command_policy.py
class CommandPolicy(PermissionPolicy):
    """Filter dangerous bash commands."""

    def __init__(self, blocked_patterns: List[str]):
        self.blocked_patterns = blocked_patterns

    async def evaluate(self, tool_name, input_data, context):
        if tool_name in ["bash", "Bash"]:
            command = input_data.get("command", "")

            for pattern in self.blocked_patterns:
                if pattern in command:
                    return PermissionResultDeny(
                        message=f"Command blocked: contains dangerous pattern '{pattern}'",
                        interrupt=False
                    )

        return PermissionResultAllow()
```

### 3. MCP Integration

#### 3.1 Create `MCPServerManager` (`app/claude_sdk/mcp/server_manager.py`)

```python
class MCPServerManager:
    """Manage MCP server lifecycle."""

    def __init__(self):
        self.sdk_servers: Dict[str, McpSdkServerConfig] = {}
        self.external_servers: Dict[str, McpServerConfig] = {}

    async def create_sdk_server(
        self,
        name: str,
        tools: List[SdkMcpTool]
    ) -> McpSdkServerConfig:
        """Create in-process SDK MCP server."""

        server_config = create_sdk_mcp_server(
            name=name,
            version="1.0.0",
            tools=tools
        )

        self.sdk_servers[name] = server_config
        return server_config

    async def create_external_server(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str]
    ) -> Dict[str, Any]:
        """Configure external MCP server (subprocess)."""

        server_config = {
            "command": command,
            "args": args,
            "env": env
        }

        self.external_servers[name] = server_config
        return server_config

    async def discover_tools(
        self,
        server_name: str
    ) -> List[str]:
        """Discover available tools from MCP server."""
        # For SDK servers, get tools from config
        # For external servers, this would need MCP protocol communication
        if server_name in self.sdk_servers:
            # Return tool names from SDK server
            pass

        return []

    def get_all_servers(self) -> Dict[str, Any]:
        """Get all configured servers."""
        return {
            **self.sdk_servers,
            **self.external_servers
        }
```

### 4. Persistence Layer

#### 4.1 Create `StorageArchiver` (`app/claude_sdk/persistence/storage_archiver.py`)

```python
class StorageArchiver:
    """Archive working directories to S3/file storage."""

    def __init__(
        self,
        provider: str = "s3",  # 's3', 'local'
        bucket: Optional[str] = None,
        region: Optional[str] = None
    ):
        self.provider = provider
        self.bucket = bucket
        self.region = region

        if provider == "s3":
            import boto3
            self.s3_client = boto3.client('s3', region_name=region)

    async def archive_working_directory(
        self,
        session_id: UUID,
        working_dir: Path
    ) -> ArchiveMetadata:
        """Archive working directory to storage."""

        # 1. Create tar.gz archive
        archive_path = Path(f"/tmp/{session_id}.tar.gz")
        manifest = await self._create_archive(working_dir, archive_path)

        # 2. Upload to storage
        if self.provider == "s3":
            s3_path = f"archives/{session_id}.tar.gz"
            await self._upload_to_s3(archive_path, s3_path)
            final_path = f"s3://{self.bucket}/{s3_path}"
        else:
            final_path = str(archive_path)

        # 3. Create metadata
        return ArchiveMetadata(
            id=uuid4(),
            session_id=session_id,
            archive_path=final_path,
            size_bytes=archive_path.stat().st_size,
            compression="gzip",
            manifest=manifest,
            status=ArchiveStatus.COMPLETED,
            error_message=None,
            archived_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    async def _create_archive(
        self,
        source_dir: Path,
        archive_path: Path
    ) -> Dict[str, Any]:
        """Create compressed archive and generate manifest."""

        import tarfile

        manifest = {"files": [], "total_size": 0}

        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    tar.add(file_path, arcname=arcname)

                    manifest["files"].append({
                        "path": str(arcname),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
                    manifest["total_size"] += file_path.stat().st_size

        manifest["file_count"] = len(manifest["files"])
        return manifest

    async def _upload_to_s3(self, local_path: Path, s3_key: str) -> None:
        """Upload file to S3."""
        self.s3_client.upload_file(str(local_path), self.bucket, s3_key)

    async def retrieve_archive(
        self,
        session_id: UUID,
        extract_to: Path
    ) -> Path:
        """Retrieve and extract archived working directory."""

        # Download from S3 if needed
        # Extract archive
        # Return extracted path
        pass
```

---

## File Structure (What Gets Created)

```
app/claude_sdk/
├── hooks/
│   ├── __init__.py                       [NEW]
│   ├── hook_manager.py                   [NEW] - HookManager, HookRegistry
│   ├── base_hooks.py                     [NEW] - BaseHook, PreToolUseHook, PostToolUseHook
│   └── implementations/
│       ├── __init__.py                   [NEW]
│       ├── audit_hook.py                 [NEW] - AuditHook
│       ├── tool_tracking_hook.py         [NEW] - ToolTrackingHook
│       ├── metrics_hook.py               [NEW] - MetricsHook
│       ├── persistence_hook.py           [NEW] - PersistenceHook
│       └── notification_hook.py          [NEW] - NotificationHook
│
├── permissions/
│   ├── __init__.py                       [NEW]
│   ├── permission_manager.py             [NEW] - PermissionManager
│   ├── policy_engine.py                  [NEW] - PolicyEngine, PermissionPolicy
│   ├── validators.py                     [NEW] - Input validation
│   └── policies/
│       ├── __init__.py                   [NEW]
│       ├── file_access_policy.py         [NEW] - FileAccessPolicy
│       ├── command_policy.py             [NEW] - CommandPolicy
│       └── mcp_policy.py                 [NEW] - MCPPolicy
│
├── mcp/
│   ├── __init__.py                       [NEW]
│   ├── server_manager.py                 [NEW] - MCPServerManager
│   ├── server_config_builder.py          [NEW] - Build SDK vs External configs
│   └── tool_registry.py                  [NEW] - Tool discovery
│
├── persistence/
│   ├── __init__.py                       [NEW]
│   ├── session_persister.py              [NEW] - SessionPersister
│   ├── metrics_persister.py              [NEW] - MetricsPersister
│   ├── artifact_persister.py             [NEW] - ArtifactPersister
│   └── storage_archiver.py               [NEW] - StorageArchiver
│
└── __init__.py                           [UPDATED] - Export all components

tests/
├── unit/
│   └── claude_sdk/
│       ├── hooks/
│       │   ├── test_hook_manager.py      [NEW]
│       │   ├── test_audit_hook.py        [NEW]
│       │   └── test_metrics_hook.py      [NEW]
│       ├── permissions/
│       │   ├── test_permission_manager.py [NEW]
│       │   ├── test_file_access_policy.py [NEW]
│       │   └── test_command_policy.py    [NEW]
│       ├── mcp/
│       │   └── test_server_manager.py    [NEW]
│       └── persistence/
│           └── test_storage_archiver.py  [NEW]
│
└── integration/
    └── claude_sdk/
        ├── test_hooks_integration.py     [NEW] - E2E hook execution
        ├── test_permissions_integration.py [NEW] - E2E permission checking
        └── test_s3_archival.py           [NEW] - E2E S3 upload/download
```

---

## Dependencies

**Prerequisites**:
- Phase 2 completed (SDK core, handlers, executors)
- AWS credentials configured (for S3 archival)
- boto3 installed for S3 integration

**Blocking**:
- Phase 2: SDK Core Integration & Execution

**Blocked By**:
- None

---

## Reference Materials for Implementers

### Claude SDK Documentation
- **SDK Hooks Reference**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/types.py`
- **Check HookInput types**:
  - `PreToolUseHookInput`, `PostToolUseHookInput`, `UserPromptSubmitHookInput`
  - `StopHookInput`, `SubagentStopHookInput`, `PreCompactHookInput`
- **Check ToolPermissionContext** structure

### Example Usage Scripts
- **Script Directory**: `/workspace/me/repositories/claude-code-sdk-tests/claude-code-sdk-usage-poc/`
- **Critical Scripts to Reference**:
  - `03_custom_permissions.py` - **ESSENTIAL** - Shows permission callback with full context, logging all permission decisions to JSON
  - `04_hook_system.py` - **ESSENTIAL** - Shows all 6 hook types with clean JSON logging
  - `05_mcp_sdk_servers.py` - SDK MCP servers with `@tool` decorator
  - `06_external_mcp_servers.py` - External MCP servers (filesystem example)

**Implementation Notes**:
- Hook execution must match `04_hook_system.py` pattern (log all inputs/outputs)
- Permission logging must match `03_custom_permissions.py` (save to `permission_log.json` equivalent)
- MCP SDK servers: Follow `05_mcp_sdk_servers.py` with `@tool` decorator and `create_sdk_mcp_server()`
- MCP External servers: Follow `06_external_mcp_servers.py` with command/args configuration

---

## Testing Strategy

### Unit Tests
- **Hooks**: Test execution, error handling, chaining, priority
- **Permissions**: Test allow/deny decisions, caching, logging
- **MCP**: Test SDK and external server configuration
- **Persistence**: Test archival, manifest generation, S3 upload (mocked)

### Integration Tests
- **Hooks**: Test with real database, verify hook_executions table
- **Permissions**: Test with real policies, verify permission_decisions table
- **S3**: Test with localstack or moto for S3 operations

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All technical tasks completed
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥ 80%
- [ ] S3 archival tested with real AWS or localstack
- [ ] Documentation complete
- [ ] Code reviewed and approved

---

## Success Metrics

- ✅ All hooks execute without errors
- ✅ Permission policies correctly allow/deny operations
- ✅ MCP servers successfully integrate (SDK and External)
- ✅ Archives uploaded to S3 in < 10 seconds
- ✅ Complete audit trail in database
- ✅ Test coverage ≥ 80%

---

## Next Phase

After Phase 3 completion, proceed to **Phase 4: API Layer, Monitoring & Production Features** which exposes the new SDK module via REST API and adds production-grade monitoring.
