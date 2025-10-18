# Phase 4: API Layer, Monitoring & Production Features

**Epic**: Claude SDK Module Rebuild - API Integration & Production Hardening
**Phase**: 4 of 4 (Final)
**Status**: Pending Phase 3 Completion
**Estimated Effort**: 1.5 weeks

---

## User Story

**As a** Frontend Developer and Operations Engineer
**I want** REST API endpoints, monitoring dashboards, and production-ready features
**So that** users can interact with the new SDK module via UI/API, and operators can monitor system health, costs, and performance

---

## Business Value

- **User-Facing Features**: API endpoints enable UI development and external integrations
- **Operational Visibility**: Monitoring and metrics enable proactive issue detection
- **Cost Management**: Budget tracking and alerts prevent cost overruns
- **Production Readiness**: Complete the transformation into enterprise-grade service
- **Developer Experience**: Clean API documentation enables rapid integration

---

## Acceptance Criteria

### ✅ API Endpoints (Update `app/api/v1/sessions.py`)
- [ ] `POST /sessions/{id}/fork` - Fork existing session
- [ ] `POST /sessions/{id}/archive` - Archive session to S3
- [ ] `GET /sessions/{id}/archive` - Get archive metadata
- [ ] `GET /sessions/{id}/archive/download` - Download archive
- [ ] `GET /sessions/{id}/hooks` - Get hook execution history
- [ ] `GET /sessions/{id}/permissions` - Get permission decision history
- [ ] `GET /sessions/{id}/metrics/history` - Get metrics snapshots
- [ ] `POST /sessions` - Updated to support new session modes (interactive, background, forked)
- [ ] All endpoints return proper HTTP status codes
- [ ] All endpoints have OpenAPI documentation
- [ ] All endpoints support pagination where applicable

### ✅ Pydantic Schemas (Update `app/schemas/session.py`)
- [ ] `SessionCreateRequest` updated with new fields (mode, parent_session_id, hooks_enabled, etc.)
- [ ] `SessionResponse` updated with new fields (mode, metrics, archive_id, etc.)
- [ ] New schemas created: `SessionForkRequest`, `SessionArchiveRequest`, `HookExecutionResponse`, `PermissionDecisionResponse`, `ArchiveMetadataResponse`
- [ ] All schemas have proper validation
- [ ] All schemas have field descriptions for API docs

### ✅ Service Layer (Update `app/services/session_service.py`)
- [ ] `fork_session()` method implemented
- [ ] `archive_session()` method implemented
- [ ] `retrieve_archive()` method implemented
- [ ] Integration with new `claude_sdk` module components
- [ ] All service methods are async
- [ ] All service methods have proper error handling

### ✅ Monitoring (`app/claude_sdk/monitoring/`)
- [ ] `MetricsCollector` tracks runtime metrics
- [ ] `PerformanceTracker` tracks latency and throughput
- [ ] `CostTracker` tracks API costs and enforces budgets
- [ ] `HealthChecker` monitors SDK health
- [ ] Metrics exposed via Prometheus endpoint (optional)
- [ ] Grafana dashboard JSON template created

### ✅ Configuration (`app/core/config.py`)
- [ ] All new environment variables added to Settings class
- [ ] Default values provided for all settings
- [ ] Settings validation implemented
- [ ] `.env.example` updated with all new variables

### ✅ Dependencies (`app/api/dependencies.py`)
- [ ] Dependency injection for new SDK components
- [ ] `get_session_manager()` dependency
- [ ] `get_hook_manager()` dependency
- [ ] `get_permission_manager()` dependency
- [ ] `get_storage_archiver()` dependency

### ✅ Testing
- [ ] API endpoint tests (all new endpoints)
- [ ] Integration tests for service layer updates
- [ ] E2E tests for complete workflows (fork, archive, retrieve)
- [ ] Load tests for monitoring components
- [ ] Test coverage ≥ 80%

### ✅ Documentation
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] CLAUDE.md updated with new features
- [ ] README.md updated with usage examples
- [ ] Environment variable documentation updated
- [ ] Deployment guide created

---

## Technical Tasks

### 1. API Endpoints

#### 1.1 Update Sessions Router (`app/api/v1/sessions.py`)

Add all new endpoints from INTEGRATION_CHANGES_REQUIRED.md section 7.1:

```python
@router.post("/{session_id}/fork", response_model=SessionResponse)
async def fork_session(...):
    """Fork an existing session."""

@router.post("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def archive_session(...):
    """Archive session's working directory."""

@router.get("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def get_session_archive(...):
    """Get archive metadata."""

@router.get("/{session_id}/archive/download")
async def download_session_archive(...):
    """Download archived working directory."""

@router.get("/{session_id}/hooks", response_model=List[HookExecutionResponse])
async def get_session_hooks(...):
    """Get hook execution history."""

@router.get("/{session_id}/permissions", response_model=List[PermissionDecisionResponse])
async def get_session_permissions(...):
    """Get permission decision history."""

@router.get("/{session_id}/metrics/history")
async def get_session_metrics_history(...):
    """Get historical metrics snapshots."""
```

#### 1.2 Update Create Session Endpoint

```python
@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,  # Updated schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Create new session with support for:
    - Interactive mode (real-time chat)
    - Background mode (automation tasks)
    - Forked mode (continuation of existing session)
    - Session templates
    - Custom hooks and permissions
    """
    # Implementation using new SessionService methods
```

### 2. Pydantic Schemas

#### 2.1 Update `SessionCreateRequest` (`app/schemas/session.py`)

```python
class SessionCreateRequest(BaseModel):
    """Create session request with new fields."""

    # Existing fields
    template_id: Optional[UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    working_directory: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    sdk_options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    # NEW: Session mode
    mode: Optional[str] = Field("interactive", description="Session mode: interactive, background, forked")

    # NEW: Parent session (for forking)
    parent_session_id: Optional[UUID] = Field(None, description="Parent session ID (for forking)")
    fork_at_message: Optional[int] = Field(None, description="Fork from message index")

    # NEW: Streaming configuration
    include_partial_messages: Optional[bool] = Field(False, description="Enable real-time streaming")

    # NEW: Retry configuration
    max_retries: Optional[int] = Field(3, description="Max retry attempts")
    retry_delay: Optional[float] = Field(2.0, description="Retry delay in seconds")
    timeout_seconds: Optional[int] = Field(120, description="Timeout in seconds")

    # NEW: Hooks configuration
    hooks_enabled: Optional[List[str]] = Field([], description="Enabled hook types")

    # NEW: Permission configuration
    permission_mode: Optional[str] = Field("default", description="Permission mode")
    custom_policies: Optional[List[str]] = Field([], description="Custom policy names")
```

#### 2.2 Create New Schemas

```python
class SessionForkRequest(BaseModel):
    """Fork session request."""
    name: Optional[str] = None
    fork_at_message: Optional[int] = None
    include_working_directory: bool = True


class SessionArchiveRequest(BaseModel):
    """Archive session request."""
    upload_to_s3: bool = True
    compression: str = "gzip"


class HookExecutionResponse(BaseModel):
    """Hook execution response."""
    id: UUID
    session_id: UUID
    hook_type: str
    tool_use_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    continue_execution: bool
    executed_at: datetime


class PermissionDecisionResponse(BaseModel):
    """Permission decision response."""
    id: UUID
    session_id: UUID
    tool_name: str
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    decision: str
    reason: Optional[str]
    interrupted: bool
    decided_at: datetime


class ArchiveMetadataResponse(BaseModel):
    """Archive metadata response."""
    id: UUID
    session_id: UUID
    archive_path: str
    size_bytes: int
    compression: str
    manifest: Dict[str, Any]
    status: str
    error_message: Optional[str]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### 3. Service Layer Updates

#### 3.1 Update SessionService (`app/services/session_service.py`)

Add new methods from INTEGRATION_CHANGES_REQUIRED.md section 5.1:

```python
async def fork_session(
    self,
    parent_session_id: UUID,
    user_id: UUID,
    fork_at_message: Optional[int] = None,
    name: Optional[str] = None
) -> Session:
    """Fork an existing session."""

async def archive_session(
    self,
    session_id: UUID,
    user_id: UUID,
    upload_to_s3: bool = True
) -> ArchiveMetadata:
    """Archive a session's working directory."""

async def retrieve_archive(
    self,
    session_id: UUID,
    user_id: UUID,
    extract_to: Optional[Path] = None
) -> Path:
    """Retrieve and extract archived working directory."""
```

#### 3.2 Update TaskService (`app/services/task_service.py`)

```python
async def execute_task_as_background_session(
    self,
    task_id: UUID,
    user_id: UUID,
    variables: Optional[Dict[str, Any]] = None
) -> Session:
    """Execute a task as a background Claude SDK session."""
    # Use new BackgroundExecutor from claude_sdk.execution
```

### 4. Monitoring Components

#### 4.1 Create `MetricsCollector` (`app/claude_sdk/monitoring/metrics_collector.py`)

```python
class MetricsCollector:
    """Collect runtime metrics for observability."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_repo = SessionMetricsSnapshotRepository(db)

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

    async def create_snapshot(
        self,
        session_id: UUID
    ) -> None:
        """Create metrics snapshot for historical tracking."""
```

#### 4.2 Create `CostTracker` (`app/claude_sdk/monitoring/cost_tracker.py`)

```python
class CostTracker:
    """Track API costs and enforce budgets."""

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

    async def alert_if_over_budget(
        self,
        user_id: UUID,
        threshold_percent: float = 80.0
    ) -> None:
        """Send alert if user is approaching budget limit."""
```

#### 4.3 Create `HealthChecker` (`app/claude_sdk/monitoring/health_checker.py`)

```python
class HealthChecker:
    """Monitor SDK health."""

    async def check_sdk_availability(self) -> bool:
        """Check if Claude SDK CLI is available."""

    async def check_mcp_servers(self) -> Dict[str, bool]:
        """Check health of all MCP servers."""

    async def check_database(self) -> bool:
        """Check database connectivity."""

    async def check_s3_storage(self) -> bool:
        """Check S3 storage availability."""

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
```

### 5. Configuration

#### 5.1 Update Settings (`app/core/config.py`)

Add all new settings from INTEGRATION_CHANGES_REQUIRED.md section 8.2:

```python
class Settings(BaseSettings):
    """Application configuration."""

    # ... existing settings ...

    # Claude SDK settings
    claude_sdk_default_model: str = "claude-sonnet-4-5"
    claude_sdk_max_retries: int = 3
    claude_sdk_retry_delay: float = 2.0
    claude_sdk_timeout_seconds: int = 120
    claude_sdk_default_permission_mode: str = "default"

    # Storage settings
    storage_provider: str = "s3"
    aws_s3_bucket: str = "ai-agent-archives"
    aws_s3_region: str = "us-east-1"
    aws_s3_archive_prefix: str = "archives/"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # Archival settings
    archive_compression: str = "gzip"
    archive_auto_cleanup: bool = True
    archive_retention_days: int = 90

    # Session limits
    max_concurrent_interactive_sessions: int = 10
    max_concurrent_background_sessions: int = 50
    session_idle_timeout_minutes: int = 30
    session_auto_archive_days: int = 180

    # Metrics settings
    enable_metrics_collection: bool = True
    metrics_snapshot_interval_seconds: int = 60
    enable_cost_tracking: bool = True
    user_monthly_budget_usd: float = 100.0

    # Hooks settings
    enable_audit_hook: bool = True
    enable_metrics_hook: bool = True
    enable_persistence_hook: bool = True
    enable_notification_hook: bool = True

    # Permissions settings
    enable_custom_policies: bool = True
    default_blocked_commands: List[str] = ["rm -rf", "sudo rm", "format"]
    default_restricted_paths: List[str] = ["/etc/passwd", "~/.ssh", "~/.aws/credentials"]
```

#### 5.2 Update `.env.example`

Add all new environment variables.

### 6. Dependencies

#### 6.1 Update Dependencies (`app/api/dependencies.py`)

```python
from app.claude_sdk.core import SessionManager
from app.claude_sdk.hooks import HookManager
from app.claude_sdk.permissions import PermissionManager
from app.claude_sdk.persistence import StorageArchiver
from app.claude_sdk.monitoring import MetricsCollector, CostTracker


async def get_session_manager(db: AsyncSession = Depends(get_db_session)) -> SessionManager:
    """Get Session Manager instance."""
    return SessionManager(db)


async def get_hook_manager(db: AsyncSession = Depends(get_db_session)) -> HookManager:
    """Get Hook Manager instance."""
    return HookManager(db, HookExecutionRepository(db))


async def get_permission_manager(db: AsyncSession = Depends(get_db_session)) -> PermissionManager:
    """Get Permission Manager instance."""
    from app.claude_sdk.permissions import PolicyEngine
    policy_engine = PolicyEngine()
    # Register default policies
    return PermissionManager(db, policy_engine, PermissionDecisionRepository(db))


async def get_storage_archiver() -> StorageArchiver:
    """Get Storage Archiver instance."""
    from app.core.config import settings
    return StorageArchiver(
        provider=settings.storage_provider,
        bucket=settings.aws_s3_bucket,
        region=settings.aws_s3_region
    )


async def get_metrics_collector(db: AsyncSession = Depends(get_db_session)) -> MetricsCollector:
    """Get Metrics Collector instance."""
    return MetricsCollector(db)


async def get_cost_tracker(db: AsyncSession = Depends(get_db_session)) -> CostTracker:
    """Get Cost Tracker instance."""
    return CostTracker(db)
```

---

## File Structure (What Gets Updated/Created)

```
app/
├── api/
│   └── v1/
│       └── sessions.py                   [UPDATED] - Add 7 new endpoints
│
├── schemas/
│   └── session.py                        [UPDATED] - Update request/response schemas, add new schemas
│
├── services/
│   ├── session_service.py                [UPDATED] - Add fork_session, archive_session, retrieve_archive
│   └── task_service.py                   [UPDATED] - Add execute_task_as_background_session
│
├── claude_sdk/
│   └── monitoring/
│       ├── __init__.py                   [NEW]
│       ├── metrics_collector.py          [NEW] - MetricsCollector
│       ├── performance_tracker.py        [NEW] - PerformanceTracker
│       ├── cost_tracker.py               [NEW] - CostTracker
│       └── health_checker.py             [NEW] - HealthChecker
│
├── core/
│   └── config.py                         [UPDATED] - Add all new settings
│
└── api/
    └── dependencies.py                   [UPDATED] - Add dependency injection for new components

.env.example                              [UPDATED] - Add all new environment variables

docs/
├── API.md                                [UPDATED] - Document new endpoints
├── DEPLOYMENT.md                         [NEW]     - Deployment guide
└── MONITORING.md                         [NEW]     - Monitoring guide

tests/
├── integration/
│   └── api/
│       ├── test_fork_session.py          [NEW]
│       ├── test_archive_session.py       [NEW]
│       └── test_hooks_api.py             [NEW]
│
└── e2e/
    ├── test_interactive_workflow.py      [NEW] - Complete interactive session flow
    ├── test_background_workflow.py       [NEW] - Complete background task flow
    └── test_fork_workflow.py             [NEW] - Complete fork session flow
```

---

## Dependencies

**Prerequisites**:
- Phase 3 completed (hooks, permissions, MCP, persistence)
- AWS credentials configured for S3
- All Phase 1-3 tests passing

**Blocking**:
- Phase 3: Advanced Features

**Blocked By**:
- None (This is the final phase)

---

## Reference Materials for Implementers

### Claude SDK Documentation
- **All previous phase references apply**
- Focus on integration patterns from all POC scripts

### Example Usage Scripts
- **Script Directory**: `/workspace/me/repositories/claude-code-sdk-tests/claude-code-sdk-usage-poc/`
- **Review ALL scripts** to ensure correct integration:
  - `01_basic_hello_world.py` - Basic patterns
  - `02_interactive_chat.py` - Interactive flow
  - `03_custom_permissions.py` - Permissions with logging
  - `04_hook_system.py` - All hooks
  - `05_mcp_sdk_servers.py` - SDK MCP
  - `06_external_mcp_servers.py` - External MCP
  - `07_advanced_streaming.py` - Streaming
  - `08_production_ready.py` - Production patterns

**Critical**: All API endpoints must correctly use the new `claude_sdk` module components built in Phases 1-3.

---

## Testing Strategy

### API Tests
- Test all new endpoints with various inputs
- Test error scenarios (unauthorized, not found, validation errors)
- Test pagination for list endpoints

### Integration Tests
- Test service layer integration with SDK module
- Test fork, archive, retrieve workflows end-to-end

### E2E Tests
- **Interactive workflow**: Create session, send messages, fork session, continue conversation
- **Background workflow**: Create task, execute as background session, retrieve results, archive
- **Monitoring**: Verify metrics collection, cost tracking, budget alerts

### Load Tests
- Concurrent session creation
- Concurrent API requests
- Archive upload/download performance

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All technical tasks completed
- [ ] All tests passing (unit + integration + E2E)
- [ ] Test coverage ≥ 80%
- [ ] API documentation complete (OpenAPI/Swagger)
- [ ] All environment variables documented
- [ ] Deployment guide created
- [ ] Code reviewed and approved
- [ ] Performance benchmarks meet targets
- [ ] Ready for production deployment

---

## Success Metrics

- ✅ All API endpoints return correct responses
- ✅ Session forking works correctly with context restoration
- ✅ Archive/retrieval completes in < 10 seconds
- ✅ Metrics collection overhead < 5% of request time
- ✅ Budget alerts trigger correctly
- ✅ API response times < 200ms (excluding SDK execution)
- ✅ Test coverage ≥ 80%
- ✅ Zero breaking changes to existing API

---

## Post-Phase 4: Production Deployment

After Phase 4 completion:

1. **Staging Deployment**
   - Deploy to staging environment
   - Run smoke tests
   - Test with real Claude API calls
   - Verify S3 archival works
   - Load test with realistic traffic

2. **Production Deployment**
   - Deploy to production with feature flags
   - Gradual rollout (10% → 50% → 100%)
   - Monitor error rates and performance
   - Verify cost tracking and budgets

3. **Monitoring Setup**
   - Configure Grafana dashboards
   - Set up alerts (errors, latency, budget)
   - Configure log aggregation

4. **Documentation**
   - User guide for new features
   - Migration guide for existing users
   - Troubleshooting guide

---

## Completion Celebration

🎉 **Congratulations!** Upon completing Phase 4, the Claude SDK Module v2.0 transformation is complete!

**What we've built**:
- ✅ Modern database schema supporting all advanced features
- ✅ Clean domain-driven architecture with separation of concerns
- ✅ Robust SDK integration with retry logic and error handling
- ✅ Multiple execution strategies (interactive, background, forked)
- ✅ Extensible hook system for customization
- ✅ Policy-based permission system for security
- ✅ MCP integration for external tools
- ✅ S3 archival for cost savings
- ✅ Comprehensive monitoring and cost tracking
- ✅ Production-ready REST API
- ✅ Complete audit trails for compliance
- ✅ 80%+ test coverage

**Impact**:
- 🚀 Support hundreds of use cases across industries
- 🔒 Enterprise-grade security and compliance
- 📊 Complete observability and cost control
- ⚡ Production-ready reliability and performance
- 🔌 Extensible architecture for future growth

**Next Steps**: Production deployment, user training, and feature iterations based on feedback!
