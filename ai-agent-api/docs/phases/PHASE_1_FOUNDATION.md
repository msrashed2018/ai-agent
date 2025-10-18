# Phase 1: Core Foundation & Domain Layer

**Epic**: Claude SDK Module Rebuild - Foundation Layer
**Phase**: 1 of 4
**Status**: Ready for Implementation
**Estimated Effort**: 1.5 weeks

---

## User Story

**As a** Platform Engineer
**I want** a solid foundation with updated database schema, domain entities, and base repositories
**So that** the new Claude SDK module has a robust data layer supporting all advanced features (session modes, forking, hooks, permissions, archival)

---

## Business Value

- **Foundation for advanced features**: Enables session forking, background tasks, comprehensive audit trails
- **Data integrity**: Proper schema design ensures data consistency and referential integrity
- **Scalability**: Domain-driven design allows easy extension for future features
- **Observability**: Audit tables provide complete visibility into system behavior

---

## Acceptance Criteria

### ✅ Database Schema
- [ ] New tables created: `hook_executions`, `permission_decisions`, `working_directory_archives`, `session_metrics_snapshots`
- [ ] `sessions` table updated with new columns: `mode`, `include_partial_messages`, retry config, hooks config, permissions config, metrics fields, `archive_id`, `template_id`
- [ ] `messages` table updated: `is_partial`, `parent_message_id`, `model`, `thinking_content`
- [ ] `tool_calls` table updated: `duration_ms`, `retries`, `hook_pre_data`, `hook_post_data`, `permission_decision`, `permission_reason`
- [ ] All indexes created for optimal query performance
- [ ] All foreign key relationships established
- [ ] Database migration successfully runs without errors
- [ ] Migration can be rolled back cleanly

### ✅ Domain Entities
- [ ] `SessionMode` enum added: `INTERACTIVE`, `BACKGROUND`, `FORKED`
- [ ] `Session` entity updated with new fields and methods: `increment_hook_execution_count()`, `increment_permission_check_count()`, `increment_error_count()`, `increment_retry_count()`
- [ ] New domain entities created: `HookExecution`, `PermissionDecision`, `ArchiveMetadata`
- [ ] `ArchiveStatus` enum created: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`
- [ ] All domain entities are immutable (dataclasses)
- [ ] Domain entities contain only business logic, no infrastructure concerns

### ✅ Database Models (ORM)
- [ ] `SessionModel` updated with all new columns
- [ ] New models created: `HookExecutionModel`, `PermissionDecisionModel`, `WorkingDirectoryArchiveModel`, `SessionMetricsSnapshotModel`
- [ ] `MessageModel` updated with streaming support fields
- [ ] `ToolCallModel` updated with execution metrics fields
- [ ] All relationships properly configured (back_populates, cascade rules)
- [ ] All constraints added (CHECK constraints for enums, UNIQUE constraints)

### ✅ Base Repositories
- [ ] New repositories created: `HookExecutionRepository`, `PermissionDecisionRepository`, `WorkingDirectoryArchiveRepository`, `SessionMetricsSnapshotRepository`
- [ ] `SessionRepository` extended with methods: `get_by_mode()`, `get_forked_sessions()`, `get_sessions_with_archives()`
- [ ] All repositories inherit from `BaseRepository`
- [ ] All repository methods are async
- [ ] Repositories handle database exceptions gracefully

### ✅ Testing
- [ ] Unit tests for domain entities (Session methods, state transitions)
- [ ] Unit tests for new domain entities (HookExecution, PermissionDecision, ArchiveMetadata)
- [ ] Integration tests for database migrations (up and down)
- [ ] Integration tests for repositories (CRUD operations, queries)
- [ ] Test coverage ≥ 80% for all new code

### ✅ Documentation
- [ ] Database schema documented (ERD diagram updated)
- [ ] Domain entity relationships documented
- [ ] Migration guide updated with rollback instructions
- [ ] Repository methods documented with examples

---

## Technical Tasks

### 1. Database Schema Updates

#### 1.1 Create Migration
```bash
cd /workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api
poetry run alembic revision -m "Phase 1: Add Claude SDK v2 tables and columns"
```

#### 1.2 New Tables SQL
- Create `hook_executions` table with indexes
- Create `permission_decisions` table with indexes
- Create `working_directory_archives` table with indexes
- Create `session_metrics_snapshots` table with indexes

#### 1.3 Alter Existing Tables
- Add columns to `sessions` table
- Add columns to `messages` table
- Add columns to `tool_calls` table
- Create indexes on new columns

#### 1.4 Test Migration
- Test upgrade: `poetry run alembic upgrade head`
- Test downgrade: `poetry run alembic downgrade -1`
- Verify schema in test database

### 2. Domain Layer

#### 2.1 Update Session Entity (`app/domain/entities/session.py`)
```python
# Add to SessionMode enum
class SessionMode(str, Enum):
    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    FORKED = "forked"

# Add to Session class
def __init__(self, ...):
    # ... existing fields ...
    self.include_partial_messages: bool = False
    self.max_retries: int = 3
    self.retry_delay: float = 2.0
    self.timeout_seconds: int = 120
    self.hooks_enabled: List[str] = []
    self.permission_mode: str = "default"
    self.custom_policies: List[str] = []
    self.total_hook_executions: int = 0
    self.total_permission_checks: int = 0
    self.total_errors: int = 0
    self.total_retries: int = 0
    self.archive_id: Optional[UUID] = None
    self.template_id: Optional[UUID] = None

# Add new methods
def increment_hook_execution_count(self) -> None: ...
def increment_permission_check_count(self) -> None: ...
def increment_error_count(self) -> None: ...
def increment_retry_count(self) -> None: ...
```

#### 2.2 Create New Domain Entities
- `app/domain/entities/hook_execution.py`
- `app/domain/entities/permission_decision.py`
- `app/domain/entities/archive_metadata.py`

#### 2.3 Create New Enums
- `app/domain/enums.py`: Add `ArchiveStatus` enum

### 3. Database Models (ORM)

#### 3.1 Update Existing Models
- `app/models/session.py`: Add new columns, relationships, constraints
- `app/models/message.py`: Add streaming fields
- `app/models/tool_call.py`: Add metrics fields

#### 3.2 Create New Models
- `app/models/hook_execution.py`
- `app/models/permission_decision.py`
- `app/models/working_directory_archive.py`
- `app/models/session_metrics_snapshot.py`

#### 3.3 Update Model Relationships
- Add relationships in `SessionModel` for new tables
- Update `app/models/__init__.py` to export new models

### 4. Repositories

#### 4.1 Create New Repositories
- `app/repositories/hook_execution_repository.py`
- `app/repositories/permission_decision_repository.py`
- `app/repositories/working_directory_archive_repository.py`
- `app/repositories/session_metrics_snapshot_repository.py`

#### 4.2 Update SessionRepository
- Add `get_by_mode()` method
- Add `get_forked_sessions()` method
- Add `get_sessions_with_archives()` method

#### 4.3 Update Repository Exports
- Update `app/repositories/__init__.py` to export new repositories

### 5. Testing

#### 5.1 Unit Tests
- `tests/unit/domain/test_session_entity.py`: Test new Session methods
- `tests/unit/domain/test_hook_execution.py`: Test HookExecution entity
- `tests/unit/domain/test_permission_decision.py`: Test PermissionDecision entity
- `tests/unit/domain/test_archive_metadata.py`: Test ArchiveMetadata entity

#### 5.2 Integration Tests
- `tests/integration/database/test_migration.py`: Test migration up/down
- `tests/integration/repositories/test_hook_execution_repository.py`
- `tests/integration/repositories/test_permission_decision_repository.py`
- `tests/integration/repositories/test_archive_repository.py`
- `tests/integration/repositories/test_session_repository_extended.py`

### 6. Documentation
- Update `docs/database/ERD.md` with new schema
- Create `docs/database/MIGRATION_GUIDE.md`
- Update `CLAUDE.md` with new domain entities

---

## File Structure (What Gets Created/Updated)

```
app/
├── domain/
│   ├── entities/
│   │   ├── session.py                    [UPDATED] - Add new fields, methods
│   │   ├── hook_execution.py             [NEW]     - HookExecution entity
│   │   ├── permission_decision.py        [NEW]     - PermissionDecision entity
│   │   └── archive_metadata.py           [NEW]     - ArchiveMetadata entity
│   └── enums.py                          [UPDATED] - Add ArchiveStatus enum
│
├── models/
│   ├── session.py                        [UPDATED] - Add columns, relationships
│   ├── message.py                        [UPDATED] - Add streaming fields
│   ├── tool_call.py                      [UPDATED] - Add metrics fields
│   ├── hook_execution.py                 [NEW]     - HookExecutionModel
│   ├── permission_decision.py            [NEW]     - PermissionDecisionModel
│   ├── working_directory_archive.py      [NEW]     - WorkingDirectoryArchiveModel
│   ├── session_metrics_snapshot.py       [NEW]     - SessionMetricsSnapshotModel
│   └── __init__.py                       [UPDATED] - Export new models
│
├── repositories/
│   ├── session_repository.py             [UPDATED] - Add new query methods
│   ├── hook_execution_repository.py      [NEW]     - CRUD for hook executions
│   ├── permission_decision_repository.py [NEW]     - CRUD for permissions
│   ├── working_directory_archive_repository.py [NEW] - CRUD for archives
│   ├── session_metrics_snapshot_repository.py  [NEW] - CRUD for metrics
│   └── __init__.py                       [UPDATED] - Export new repositories
│
alembic/
└── versions/
    └── xxxx_phase1_claude_sdk_v2.py      [NEW]     - Database migration

tests/
├── unit/
│   └── domain/
│       ├── test_session_entity.py        [UPDATED] - Test new methods
│       ├── test_hook_execution.py        [NEW]     - Test HookExecution
│       ├── test_permission_decision.py   [NEW]     - Test PermissionDecision
│       └── test_archive_metadata.py      [NEW]     - Test ArchiveMetadata
│
└── integration/
    ├── database/
    │   └── test_migration.py             [NEW]     - Test migration up/down
    └── repositories/
        ├── test_hook_execution_repository.py       [NEW]
        ├── test_permission_decision_repository.py  [NEW]
        ├── test_archive_repository.py              [NEW]
        └── test_session_repository_extended.py     [UPDATED]

docs/
├── database/
│   ├── ERD.md                            [UPDATED] - Updated schema diagram
│   └── MIGRATION_GUIDE.md                [NEW]     - Migration instructions
└── CLAUDE.md                             [UPDATED] - Document new entities
```

---

## Dependencies

**Prerequisites**:
- PostgreSQL 15+ running
- Alembic configured
- Poetry dependencies installed

**Blocking**:
- None (This is Phase 1 - Foundation)

**Blocked By**:
- None

---

## Reference Materials for Implementers

### Claude SDK Documentation
- **SDK Installation Path**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/`
- **SDK Types Reference**: `/home/msalah/.cache/pypoetry/virtualenvs/claude-code-sdk-tests-UHfvQJRu-py3.12/lib/python3.12/site-packages/claude_agent_sdk/types.py`
- **Check this file** to understand:
  - `SessionStatus`, `SessionMode` enums
  - `Message` types (AssistantMessage, UserMessage, SystemMessage, ResultMessage)
  - `ContentBlock` types (TextBlock, ToolUseBlock, ToolResultBlock, ThinkingBlock)
  - `HookInput`, `ToolPermissionContext` structures

### Example Usage Scripts
- **Script Directory**: `/workspace/me/repositories/claude-code-sdk-tests/claude-code-sdk-usage-poc/`
- **Key Scripts to Reference**:
  - `01_basic_hello_world.py` - Basic SDK usage
  - `03_custom_permissions.py` - Permission handling with full context logging
  - `04_hook_system.py` - All hook types with logging
  - `08_production_ready.py` - Production patterns with metrics, retry logic

**Important**: These scripts show the correct SDK patterns. Use them as examples when implementing database persistence and domain entities.

---

## Testing Strategy

### Unit Tests
- **Domain Entities**: Test business logic in isolation
  - Session state transitions with new statuses
  - Counter increment methods
  - Validation rules

- **Domain Entities (New)**: Test immutability and structure
  - HookExecution creation and validation
  - PermissionDecision decision logic
  - ArchiveMetadata status transitions

### Integration Tests
- **Database Migration**: Verify schema changes
  - Run migration up successfully
  - Verify all tables created
  - Verify all columns added
  - Verify indexes created
  - Run migration down successfully
  - Verify clean rollback

- **Repositories**: Test database operations
  - CRUD operations for all new repositories
  - Query methods return correct results
  - Filtering and pagination work
  - Relationships properly loaded
  - Foreign key constraints enforced

### Manual Testing
- Run migration on local dev database
- Inspect schema with pgAdmin/psql
- Verify no breaking changes to existing data
- Test migration rollback

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All technical tasks completed
- [ ] Code reviewed and approved
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥ 80%
- [ ] Migration tested on staging database
- [ ] Documentation updated
- [ ] No breaking changes to existing API
- [ ] CI/CD pipeline green

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Migration fails on production | High | Low | Test thoroughly on staging; have rollback plan ready |
| Breaking changes to existing sessions | High | Medium | Add defaults for all new columns; make everything optional |
| Performance degradation from new tables | Medium | Low | Create proper indexes; monitor query performance |
| Data type mismatches | Medium | Low | Use Alembic autogenerate; manually review SQL |

---

## Rollback Plan

If issues arise after deployment:

1. **Database Rollback**:
   ```bash
   poetry run alembic downgrade -1
   ```

2. **Code Rollback**:
   ```bash
   git revert <commit-hash>
   ```

3. **Verify**: Existing sessions still work
4. **Communicate**: Notify team of rollback

---

## Success Metrics

- ✅ Migration runs in < 5 seconds on production database
- ✅ Zero downtime during migration
- ✅ All existing sessions remain functional
- ✅ Test coverage ≥ 80%
- ✅ All repository queries execute in < 100ms
- ✅ No errors in application logs post-deployment

---

## Notes

- This phase is **purely foundational** - no API changes, no user-facing features
- Existing functionality remains unchanged
- All new columns have defaults to maintain backward compatibility
- New tables are empty initially - populated in later phases
- Domain entities use dataclasses for immutability and clarity
- Repositories follow existing patterns (BaseRepository, async/await)

---

## Next Phase

After Phase 1 completion, proceed to **Phase 2: SDK Core Integration & Execution** which builds the core Claude SDK wrapper, message handlers, and execution strategies on top of this foundation.
