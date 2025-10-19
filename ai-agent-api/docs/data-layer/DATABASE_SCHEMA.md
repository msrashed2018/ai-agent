# Database Schema

## Purpose

Complete documentation of the PostgreSQL database schema, including all tables, columns, relationships, indexes, and constraints.

##  Overview

The database uses **PostgreSQL 15+** with:
- **UUID primary keys** for all tables
- **JSONB** columns for flexible data (sdk_options, metadata)
- **Foreign keys** for referential integrity
- **Cascade deletes** where appropriate
- **Indexes** on frequently queried columns
- **Check constraints** for data validation

---

## Entity Relationship Diagram

```
users (1) ──────────< (N) sessions
                         │
                         ├────< (N) messages
                         ├────< (N) tool_calls
                         ├────< (N) hook_executions
                         ├────< (N) permission_decisions
                         ├────< (N) task_executions
                         ├────< (N) reports
                         ├────< (N) metrics_snapshots
                         ├────< (N) audit_logs
                         ├────< (1) working_directory
                         └────< (1) working_directory_archive

users (1) ──────────< (N) tasks
                         │
                         └────< (N) task_executions
                                     │
                                     └────< (1) session

users (1) ──────────< (N) mcp_servers
users (1) ──────────< (N) session_templates
                         │
                         └────< (N) sessions (via template_id)
```

---

## Core Tables

### 1. users

**Purpose**: User accounts with authentication and authorization

**File**: [models/user.py](../../app/models/user.py)

**Schema**:
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| organization_id | UUID | NOT NULL, INDEX | Organization/tenant ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Username |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| full_name | VARCHAR(255) | | User's full name |
| avatar_url | TEXT | | Profile picture URL |
| role | VARCHAR(50) | NOT NULL | User role: admin, user, viewer |
| is_active | BOOLEAN | DEFAULT true | Account active status |
| is_superuser | BOOLEAN | DEFAULT false | Superuser flag |
| max_concurrent_sessions | INTEGER | DEFAULT 5 | Session quota |
| max_api_calls_per_hour | INTEGER | DEFAULT 1000 | API rate limit |
| max_storage_mb | INTEGER | DEFAULT 10240 | Storage quota (MB) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| last_login_at | TIMESTAMP | | Last login timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |

**Indexes**:
- `idx_users_email` on `email`
- `idx_users_organization_id` on `organization_id`

**Relationships**:
- `sessions`: One-to-Many
- `tasks`: One-to-Many
- `mcp_servers`: One-to-Many
- `session_templates`: One-to-Many

---

### 2. sessions

**Purpose**: Claude Code agent sessions with state and metrics

**File**: [models/session.py:11-100](../../app/models/session.py:11-100)

**Schema**:
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Session identifier |
| user_id | UUID | FK(users.id) CASCADE, NOT NULL, INDEX | Session owner |
| name | VARCHAR(255) | | Session name |
| description | TEXT | | Session description |
| mode | VARCHAR(50) | NOT NULL, CHECK | interactive \| non_interactive \| forked |
| status | VARCHAR(50) | NOT NULL, INDEX | Session status (state machine) |
| sdk_options | JSONB | NOT NULL, DEFAULT {} | Claude SDK configuration |
| include_partial_messages | BOOLEAN | DEFAULT false | Stream partial messages |
| max_retries | INTEGER | DEFAULT 3 | Max retry attempts |
| retry_delay | NUMERIC(10,2) | DEFAULT 2.0 | Retry delay (seconds) |
| timeout_seconds | INTEGER | DEFAULT 120 | Query timeout |
| hooks_enabled | JSONB | DEFAULT [] | Enabled hook names |
| permission_mode | VARCHAR(50) | DEFAULT 'default' | Permission mode |
| custom_policies | JSONB | DEFAULT [] | Custom policy list |
| working_directory_path | TEXT | | File system path |
| parent_session_id | UUID | FK(sessions.id), INDEX | Parent session (for forks) |
| is_fork | BOOLEAN | DEFAULT false | Is forked session |
| total_messages | INTEGER | DEFAULT 0 | Message count |
| total_tool_calls | INTEGER | DEFAULT 0 | Tool call count |
| total_cost_usd | NUMERIC(10,6) | DEFAULT 0 | Total API cost |
| duration_ms | BIGINT | | Session duration (milliseconds) |
| total_hook_executions | INTEGER | DEFAULT 0 | Hook execution count |
| total_permission_checks | INTEGER | DEFAULT 0 | Permission check count |
| total_errors | INTEGER | DEFAULT 0 | Error count |
| total_retries | INTEGER | DEFAULT 0 | Retry count |
| api_input_tokens | INTEGER | DEFAULT 0 | Input token usage |
| api_output_tokens | INTEGER | DEFAULT 0 | Output token usage |
| api_cache_creation_tokens | INTEGER | DEFAULT 0 | Cache creation tokens |
| api_cache_read_tokens | INTEGER | DEFAULT 0 | Cache read tokens |
| result_data | JSONB | | Final result data |
| error_message | TEXT | | Error message |
| archive_id | UUID | FK(working_directory_archives.id), INDEX | Archive reference |
| template_id | UUID | FK(session_templates.id), INDEX | Template reference |
| created_at | TIMESTAMP | NOT NULL, INDEX | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| started_at | TIMESTAMP | | Start timestamp |
| completed_at | TIMESTAMP | | Completion timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |

**Status Values**: created, connecting, active, paused, waiting, processing, completed, failed, terminated, archived

**Indexes**:
- `idx_sessions_user_id` on `user_id`
- `idx_sessions_status` on `status`
- `idx_sessions_parent_session_id` on `parent_session_id`
- `idx_sessions_created_at` on `created_at`

**Relationships**:
- `user`: Many-to-One (UserModel)
- `messages`: One-to-Many (MessageModel, cascade delete)
- `tool_calls`: One-to-Many (ToolCallModel, cascade delete)
- `hook_executions`: One-to-Many (HookExecutionModel, cascade delete)
- `permission_decisions`: One-to-Many (PermissionDecisionModel, cascade delete)
- `task_executions`: One-to-Many (TaskExecutionModel)
- `reports`: One-to-Many (ReportModel)
- `working_directory`: One-to-One (WorkingDirectoryModel)
- `audit_logs`: One-to-Many (AuditLogModel)
- `metrics_snapshots`: One-to-Many (SessionMetricsSnapshotModel, cascade delete)
- `archive`: One-to-One (WorkingDirectoryArchiveModel)
- `template`: Many-to-One (SessionTemplateModel)

---

### 3. messages

**Purpose**: Chat messages in a session

**File**: [models/message.py](../../app/models/message.py)

**Schema**:
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Message identifier |
| session_id | UUID | FK(sessions.id) CASCADE, NOT NULL, INDEX | Parent session |
| message_type | VARCHAR(50) | NOT NULL | user \| assistant \| system \| result |
| content | JSONB | NOT NULL | Message content (flexible structure) |
| sequence_number | INTEGER | NOT NULL | Message order in session |
| model | VARCHAR(100) | | Claude model used |
| parent_tool_use_id | VARCHAR(255) | | Related tool use ID |
| created_at | TIMESTAMP | NOT NULL, INDEX | Creation timestamp |

**Indexes**:
- `idx_messages_session_id` on `session_id`
- `idx_messages_created_at` on `created_at`
- `idx_messages_session_sequence` on `(session_id, sequence_number)` UNIQUE

**Relationships**:
- `session`: Many-to-One (SessionModel)

---

### 4. tool_calls

**Purpose**: Tool execution records

**File**: [models/tool_call.py](../../app/models/tool_call.py)

**Schema**:
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Tool call identifier |
| session_id | UUID | FK(sessions.id) CASCADE, NOT NULL, INDEX | Parent session |
| message_id | UUID | FK(messages.id), INDEX | Related message |
| tool_name | VARCHAR(255) | NOT NULL | Tool name (Read, Write, Bash, etc.) |
| tool_use_id | VARCHAR(255) | NOT NULL | SDK tool use ID |
| tool_input | JSONB | NOT NULL | Tool input parameters |
| tool_output | JSONB | | Tool output |
| status | VARCHAR(50) | NOT NULL | pending \| running \| success \| error \| denied |
| is_error | BOOLEAN | DEFAULT false | Error flag |
| error_message | TEXT | | Error details |
| permission_decision | VARCHAR(50) | | allow \| deny \| ask |
| permission_reason | TEXT | | Permission decision reason |
| started_at | TIMESTAMP | | Execution start |
| completed_at | TIMESTAMP | | Execution end |
| duration_ms | BIGINT | | Execution duration |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_tool_calls_session_id` on `session_id`
- `idx_tool_calls_message_id` on `message_id`

**Relationships**:
- `session`: Many-to-One (SessionModel)
- `message`: Many-to-One (MessageModel)

---

### 5. tasks

**Purpose**: Automated task templates

**File**: [models/task.py](../../app/models/task.py)

**Schema**:
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Task identifier |
| user_id | UUID | FK(users.id) CASCADE, NOT NULL, INDEX | Task owner |
| name | VARCHAR(255) | NOT NULL | Task name |
| description | TEXT | | Task description |
| prompt_template | TEXT | NOT NULL | Jinja2 template |
| allowed_tools | JSONB | DEFAULT [] | Allowed tool list |
| disallowed_tools | JSONB | DEFAULT [] | Disallowed tool list |
| sdk_options | JSONB | DEFAULT {} | SDK configuration |
| working_directory_path | TEXT | | Working directory |
| is_scheduled | BOOLEAN | DEFAULT false | Scheduled flag |
| schedule_cron | VARCHAR(100) | | Cron expression |
| schedule_enabled | BOOLEAN | DEFAULT false | Schedule enabled |
| generate_report | BOOLEAN | DEFAULT false | Auto-report flag |
| report_format | VARCHAR(50) | | json \| markdown \| html \| pdf |
| notification_config | JSONB | | Notification settings |
| tags | JSONB | DEFAULT [] | Task tags |
| is_public | BOOLEAN | DEFAULT false | Public visibility |
| is_active | BOOLEAN | DEFAULT true | Active status |
| is_deleted | BOOLEAN | DEFAULT false | Soft delete flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update |
| deleted_at | TIMESTAMP | | Soft delete timestamp |

**Indexes**:
- `idx_tasks_user_id` on `user_id`

**Relationships**:
- `user`: Many-to-One (UserModel)
- `task_executions`: One-to-Many (TaskExecutionModel)

---

## Supporting Tables

### 6. session_templates

**Purpose**: Reusable session configurations

**File**: [models/session_template.py](../../app/models/session_template.py)

**Columns**: id, user_id, name, description, category, sdk_options, default_mode, tags, is_public, created_at, updated_at

**Category Values**: GENERAL, DEVOPS, DATA_ANALYSIS, SECURITY, DEVELOPMENT, TESTING

---

### 7. mcp_servers

**Purpose**: MCP server configurations

**File**: [models/mcp_server.py](../../app/models/mcp_server.py)

**Columns**: id, user_id, name, description, server_type (BUILTIN, STDIO, SSE), command, args, env, is_enabled, is_global, created_at, updated_at

---

### 8. task_executions

**Purpose**: Task execution history

**File**: [models/task_execution.py](../../app/models/task_execution.py)

**Columns**: id, task_id, session_id, status, trigger_type, triggered_by, started_at, completed_at, duration_ms, result_data, error_message, created_at

---

### 9. reports

**Purpose**: Generated reports

**File**: [models/report.py](../../app/models/report.py)

**Columns**: id, session_id, user_id, report_type, format, file_path, file_size_bytes, generated_at, created_at

---

### 10. hook_executions

**Purpose**: Hook execution tracking

**File**: [models/hook_execution.py](../../app/models/hook_execution.py)

**Columns**: id, session_id, hook_type, hook_name, status, input_data, output_data, error_message, started_at, completed_at, duration_ms, created_at

---

### 11. permission_decisions

**Purpose**: Permission check records

**File**: [models/permission_decision.py](../../app/models/permission_decision.py)

**Columns**: id, session_id, resource_type, resource_identifier, policy_name, decision (ALLOW, DENY, ASK), reason, checked_at, created_at

---

### 12. working_directory_archives

**Purpose**: Session working directory archives

**File**: [models/working_directory_archive.py](../../app/models/working_directory_archive.py)

**Columns**: id, session_id, archive_path, compression_format, archive_size_bytes, file_count, created_at

---

### 13. session_metrics_snapshots

**Purpose**: Periodic session metrics snapshots

**File**: [models/session_metrics_snapshot.py](../../app/models/session_metrics_snapshot.py)

**Columns**: id, session_id, snapshot_type, metrics_data (JSONB), snapshot_at, created_at

---

### 14. audit_logs

**Purpose**: Comprehensive audit trail

**File**: [models/audit_log.py](../../app/models/audit_log.py)

**Columns**: id, user_id, session_id, action, resource_type, resource_id, metadata, ip_address, user_agent, created_at

---

## Alembic Migrations

**Location**: [alembic/versions/](../../alembic/versions/)

**Migration History**:

1. **20251018_0230_initial_database_schema.py**
   - Created all core tables
   - users, sessions, messages, tool_calls, tasks, mcp_servers

2. **20251018_0355_add_session_templates.py**
   - Added session_templates table
   - Added template_id FK to sessions

3. **20251019_0058_phase1_claude_sdk_v2.py**
   - Added SDK v2 fields to sessions
   - Added hook_executions, permission_decisions tables
   - Added working_directory_archives table
   - Added session_metrics_snapshots table
   - Enhanced metrics columns

**Creating Migrations**:
```bash
# Auto-generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Data Types

### JSONB Columns

**Purpose**: Store flexible, structured data

**Examples**:
- `sessions.sdk_options`: `{"allowed_tools": ["Read", "Write"], "permission_mode": "default"}`
- `messages.content`: `{"content": "Hello", "metadata": {...}}`
- `tool_calls.tool_input`: `{"path": "/app/test.py"}`

**Benefits**:
- Flexible schema
- Indexable (GIN indexes)
- Query with JSON operators

### UUID Columns

**Purpose**: Globally unique identifiers

**Benefits**:
- No collisions in distributed systems
- Hard to guess (security)
- 128-bit (16 bytes)

---

## Constraints

### Foreign Keys

All foreign keys use **CASCADE DELETE** where appropriate:
- `sessions.user_id` → CASCADE (delete user sessions with user)
- `messages.session_id` → CASCADE (delete messages with session)
- `tool_calls.session_id` → CASCADE

### Check Constraints

**sessions table**:
- `chk_mode`: mode IN ('interactive', 'non_interactive', 'forked')
- `chk_status`: status IN (valid status values)

**tasks table**:
- `chk_report_format`: report_format IN ('json', 'markdown', 'html', 'pdf')

---

## Indexes

**Performance-critical indexes**:
- `sessions.user_id` - User session queries
- `sessions.status` - Status filtering
- `messages.session_id` - Message retrieval
- `tool_calls.session_id` - Tool call retrieval
- `sessions.created_at` - Time-based queries

---

## Related Documentation

- **ORM Models**: [ORM_MODELS.md](ORM_MODELS.md) - SQLAlchemy models
- **Repositories**: [REPOSITORIES.md](REPOSITORIES.md) - Data access layer
- **Migrations**: [MIGRATIONS.md](MIGRATIONS.md) - Migration workflow
- **Domain Model**: [../architecture/DOMAIN_MODEL.md](../architecture/DOMAIN_MODEL.md) - Domain entities

## Keywords

`database`, `schema`, `tables`, `columns`, `relationships`, `postgresql`, `sql`, `foreign-keys`, `indexes`, `constraints`, `jsonb`, `uuid`, `migrations`, `alembic`, `orm`, `sessions-table`, `users-table`, `messages-table`, `tool-calls-table`
