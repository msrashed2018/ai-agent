# ORM Models

## Purpose

Complete documentation of all SQLAlchemy ORM models that map Python classes to PostgreSQL database tables. This document covers the declarative base, model architecture, relationships, and type mappings.

---

## Overview

The ORM layer uses **SQLAlchemy 2.0** with async support to provide:
- **Declarative Base**: Single base class for all models
- **Async Operations**: Full async/await support via AsyncSession
- **Type Safety**: Strong typing with UUID, JSONB, ARRAY types
- **Relationships**: Bidirectional relationships with cascade behavior
- **Platform Independence**: Custom type decorators for PostgreSQL-specific types

**Total Models**: 17 (16 domain models + 1 organization model)

---

## Base Configuration

### Declarative Base

**File**: [app/database/base.py:19](../../app/database/base.py#L19)

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)
```

All models inherit from `Base` and get:
- Consistent constraint naming
- Automatic table name generation
- Metadata tracking
- Migration support

### Custom Type Decorators

**File**: [app/database/base.py:22-81](../../app/database/base.py#L22-81)

#### JSONB Type

Platform-independent JSONB type (PostgreSQL JSONB, fallback to JSON):

```python
class JSONB(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLJSONB())
        else:
            return dialect.type_descriptor(JSON())
```

#### ARRAY Type

Platform-independent ARRAY type (PostgreSQL ARRAY, fallback to JSON-encoded text):

```python
class ARRAY(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, item_type, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text())
```

#### INET Type

Platform-independent INET type (PostgreSQL INET, fallback to String):

```python
class INET(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQLINET())
        else:
            return dialect.type_descriptor(String(45))  # Max IPv6 length
```

---

## Core Domain Models

### 1. OrganizationModel

**Purpose**: Multi-tenant organization management

**Table**: `organizations`

**File**: [app/models/user.py:10-44](../../app/models/user.py#L10-44)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
name = Column(String(255), nullable=False)
slug = Column(String(100), unique=True, nullable=False, index=True)
primary_email = Column(String(255))
primary_contact_name = Column(String(255))
plan = Column(String(50), nullable=False, default="free")  # free, pro, enterprise
max_users = Column(Integer, default=10)
max_sessions_per_month = Column(Integer, default=1000)
max_storage_gb = Column(Integer, default=100)
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `users`: One-to-Many → UserModel

**Constraints**:
- `chk_plan`: plan IN ('free', 'pro', 'enterprise')

---

### 2. UserModel

**Purpose**: User authentication and authorization

**Table**: `users`

**File**: [app/models/user.py:47-96](../../app/models/user.py#L47-96)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
email = Column(String(255), unique=True, nullable=False, index=True)
username = Column(String(100), unique=True, nullable=False)
password_hash = Column(String(255), nullable=False)
full_name = Column(String(255))
avatar_url = Column(String)
role = Column(String(50), nullable=False, default="user")  # admin, user, viewer
is_active = Column(Boolean, nullable=False, default=True, index=True)
is_superuser = Column(Boolean, nullable=False, default=False)
max_concurrent_sessions = Column(Integer, default=5)
max_api_calls_per_hour = Column(Integer, default=1000)
max_storage_mb = Column(Integer, default=10240)
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
last_login_at = Column(DateTime(timezone=True))
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `organization`: Many-to-One → OrganizationModel
- `sessions`: One-to-Many → SessionModel
- `tasks`: One-to-Many → TaskModel
- `reports`: One-to-Many → ReportModel
- `mcp_servers`: One-to-Many → MCPServerModel
- `hooks`: One-to-Many → HookModel
- `session_templates`: One-to-Many → SessionTemplateModel

**Constraints**:
- `chk_role`: role IN ('admin', 'user', 'viewer')
- `chk_positive_quotas`: All quota columns > 0

---

### 3. SessionModel

**Purpose**: Claude Code agent sessions with state and metrics

**Table**: `sessions`

**File**: [app/models/session.py:11-105](../../app/models/session.py#L11-105)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

# Identity
name = Column(String(255))
description = Column(Text)

# Session Type
mode = Column(String(50), nullable=False)  # interactive, non_interactive, forked

# State Management
status = Column(String(50), nullable=False, default="created", index=True)
# Status: created, connecting, active, paused, waiting, processing, completed, failed, terminated, archived

# Claude SDK Configuration
sdk_options = Column(JSONB, nullable=False, default={})
include_partial_messages = Column(Boolean, default=False)
max_retries = Column(Integer, default=3)
retry_delay = Column(Numeric(10, 2), default=2.0)
timeout_seconds = Column(Integer, default=120)
hooks_enabled = Column(JSONB, default=[])
permission_mode = Column(String(50), default="default")
custom_policies = Column(JSONB, default=[])

# Working Directory
working_directory_path = Column(Text)

# Session Relationships
parent_session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
is_fork = Column(Boolean, default=False)

# Metrics & Cost
total_messages = Column(Integer, default=0)
total_tool_calls = Column(Integer, default=0)
total_cost_usd = Column(Numeric(10, 6), default=0)
duration_ms = Column(BigInteger)
total_hook_executions = Column(Integer, default=0)
total_permission_checks = Column(Integer, default=0)
total_errors = Column(Integer, default=0)
total_retries = Column(Integer, default=0)

# API Usage
api_input_tokens = Column(Integer, default=0)
api_output_tokens = Column(Integer, default=0)
api_cache_creation_tokens = Column(Integer, default=0)
api_cache_read_tokens = Column(Integer, default=0)

# Result
result_data = Column(JSONB)
error_message = Column(Text)

# References
archive_id = Column(UUID(as_uuid=True), ForeignKey("working_directory_archives.id"), index=True)
template_id = Column(UUID(as_uuid=True), ForeignKey("session_templates.id"), index=True)

# Audit
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
started_at = Column(DateTime(timezone=True))
completed_at = Column(DateTime(timezone=True))
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `user`: Many-to-One → UserModel
- `messages`: One-to-Many → MessageModel (CASCADE delete)
- `tool_calls`: One-to-Many → ToolCallModel (CASCADE delete)
- `task_executions`: One-to-Many → TaskExecutionModel
- `reports`: One-to-Many → ReportModel
- `working_directory`: One-to-One → WorkingDirectoryModel
- `audit_logs`: One-to-Many → AuditLogModel
- `hook_executions`: One-to-Many → HookExecutionModel (CASCADE delete)
- `permission_decisions`: One-to-Many → PermissionDecisionModel (CASCADE delete)
- `archive`: One-to-One → WorkingDirectoryArchiveModel
- `template`: Many-to-One → SessionTemplateModel
- `metrics_snapshots`: One-to-Many → SessionMetricsSnapshotModel (CASCADE delete)

**Constraints**:
- `chk_mode`: mode IN ('interactive', 'non_interactive', 'forked')
- `chk_status`: status IN (valid status values)

---

### 4. MessageModel

**Purpose**: Chat messages in a session

**Table**: `messages`

**File**: [app/models/message.py:11-49](../../app/models/message.py#L11-49)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
message_type = Column(String(50), nullable=False)  # user, assistant, system, result
content = Column(JSONB, nullable=False)
model = Column(String(100))  # AI model used
parent_tool_use_id = Column(String(255))

# Streaming Support
is_partial = Column(Boolean, default=False)
parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), index=True)
thinking_content = Column(Text)

# Sequence
sequence_number = Column(Integer, nullable=False)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
```

**Relationships**:
- `session`: Many-to-One → SessionModel

**Indexes**:
- GIN index on `content` for JSONB queries
- Unique composite index on `(session_id, sequence_number)`
- Partial index on result messages

**Constraints**:
- `chk_message_type`: message_type IN ('user', 'assistant', 'system', 'result')

---

### 5. ToolCallModel

**Purpose**: Tool execution records

**Table**: `tool_calls`

**File**: [app/models/tool_call.py:11-65](../../app/models/tool_call.py#L11-65)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))

# Tool Identity
tool_name = Column(String(255), nullable=False, index=True)
tool_use_id = Column(String(255), nullable=False, unique=True, index=True)

# Tool Invocation
tool_input = Column(JSONB, nullable=False)
tool_output = Column(JSONB)

# Execution Status
status = Column(String(50), nullable=False, default='pending', index=True)
# Status: pending, running, success, error, denied
is_error = Column(Boolean, default=False)
error_message = Column(String)

# Permission
permission_decision = Column(String(50))  # allow, deny, ask
permission_reason = Column(String)

# Execution Timing
started_at = Column(DateTime(timezone=True))
completed_at = Column(DateTime(timezone=True))
duration_ms = Column(Integer)

# Advanced Execution Metrics
retries = Column(Integer, default=0)
hook_pre_data = Column(JSONB)
hook_post_data = Column(JSONB)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships**:
- `session`: Many-to-One → SessionModel
- `message`: Many-to-One → MessageModel

**Indexes**:
- GIN indexes on `tool_input` and `tool_output` for JSONB queries
- Composite indexes on `(session_id, created_at)`, `(status, created_at)`, `(tool_name, created_at)`
- Partial index on permission decisions

**Constraints**:
- `chk_tool_call_status`: status IN ('pending', 'running', 'success', 'error', 'denied')
- `chk_permission_decision`: permission_decision IN ('allow', 'deny', 'ask') OR NULL

---

### 6. TaskModel

**Purpose**: Automated task templates

**Table**: `tasks`

**File**: [app/models/task.py:12-72](../../app/models/task.py#L12-72)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

# Basic Information
name = Column(String(255), nullable=False, index=True)
description = Column(Text)

# Prompt Configuration
prompt_template = Column(Text, nullable=False)  # Jinja2 template
default_variables = Column(JSONB)

# Allowed Tools
allowed_tools = Column(ARRAY(String), nullable=False, server_default='{}')
disallowed_tools = Column(ARRAY(String), server_default='{}')

# Session Configuration
sdk_options = Column(JSONB, server_default='{}')
working_directory_path = Column(String(1000))

# Scheduling
is_scheduled = Column(Boolean, default=False)
schedule_cron = Column(String(100))
schedule_enabled = Column(Boolean, default=False)

# Post-Execution Actions
generate_report = Column(Boolean, default=False)
report_format = Column(String(50))  # json, markdown, html, pdf

# Notifications
notification_config = Column(JSONB)

# Metadata
tags = Column(ARRAY(String))
is_public = Column(Boolean, default=False)

# Status
is_active = Column(Boolean, default=True, nullable=False)
is_deleted = Column(Boolean, default=False, nullable=False, index=True)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `user`: Many-to-One → UserModel
- `task_executions`: One-to-Many → TaskExecutionModel (CASCADE delete)

**Indexes**:
- GIN index on `tags`
- Composite indexes on `(user_id, is_deleted)`, `(is_scheduled, schedule_enabled)`
- Pattern matching index on `name`

**Constraints**:
- `chk_report_format`: report_format IN ('json', 'markdown', 'html', 'pdf') OR NULL

---

### 7. TaskExecutionModel

**Purpose**: Task execution history

**Table**: `task_executions`

**File**: [app/models/task_execution.py:11-59](../../app/models/task_execution.py#L11-59)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))
report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL", use_alter=True))

# Execution Context
trigger_type = Column(String(50), nullable=False)  # manual, scheduled, webhook, api
trigger_metadata = Column(JSONB)

# Execution Parameters
prompt_variables = Column(JSONB)

# Status
status = Column(String(50), nullable=False, default='pending', index=True)
# Status: pending, running, completed, failed, cancelled
error_message = Column(String)

# Results
result_data = Column(JSONB)

# Metrics
total_messages = Column(Integer, default=0)
total_tool_calls = Column(Integer, default=0)
duration_seconds = Column(Integer)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
started_at = Column(DateTime(timezone=True))
completed_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `task`: Many-to-One → TaskModel
- `session`: Many-to-One → SessionModel
- `report`: One-to-One → ReportModel

**Indexes**:
- Composite indexes on `(task_id, created_at)`, `(status, created_at)`
- Index on `trigger_type`

**Constraints**:
- `chk_trigger_type`: trigger_type IN ('manual', 'scheduled', 'webhook', 'api')
- `chk_task_execution_status`: status IN ('pending', 'running', 'completed', 'failed', 'cancelled')

---

### 8. ReportModel

**Purpose**: Generated reports

**Table**: `reports`

**File**: [app/models/report.py:12-63](../../app/models/report.py#L12-63)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
task_execution_id = Column(UUID(as_uuid=True), ForeignKey("task_executions.id", ondelete="SET NULL"))
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

# Identity
title = Column(String(255), nullable=False)
description = Column(Text)

# Report Type
report_type = Column(String(50), default='auto_generated')  # auto_generated, custom, template

# Content
content = Column(JSONB, nullable=False)

# File Outputs
file_path = Column(Text)
file_format = Column(String(50))  # json, markdown, html, pdf
file_size_bytes = Column(BigInteger)

# Metadata
template_name = Column(String(255))
tags = Column(ARRAY(String))

# Visibility
is_public = Column(Boolean, default=False)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `session`: Many-to-One → SessionModel
- `task_execution`: Many-to-One → TaskExecutionModel
- `user`: Many-to-One → UserModel

**Indexes**:
- GIN indexes on `tags` and `content`
- Descending index on `created_at`

**Constraints**:
- `chk_report_type`: report_type IN ('auto_generated', 'custom', 'template')
- `chk_file_format`: file_format IN ('json', 'markdown', 'html', 'pdf') OR NULL

---

### 9. MCPServerModel

**Purpose**: MCP server configurations

**Table**: `mcp_servers`

**File**: [app/models/mcp_server.py:11-54](../../app/models/mcp_server.py#L11-54)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))  # NULL = global

# Identity
name = Column(String(255), nullable=False)
description = Column(Text)

# Server Type
server_type = Column(String(50), nullable=False)  # stdio, sse, http, sdk

# Configuration
config = Column(JSONB, nullable=False)

# Availability
is_enabled = Column(Boolean, default=True)
is_global = Column(Boolean, default=False)

# Health
last_health_check_at = Column(DateTime(timezone=True))
health_status = Column(String(50))  # healthy, degraded, unhealthy, unknown

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `user`: Many-to-One → UserModel

**Indexes**:
- Partial indexes on `user_id`, `is_enabled`, `is_global` (where deleted_at IS NULL)

**Constraints**:
- `chk_server_type`: server_type IN ('stdio', 'sse', 'http', 'sdk')
- `chk_health_status`: health_status IN (valid values) OR NULL
- `uq_server_name_user`: Unique (name, user_id)

---

### 10. SessionTemplateModel

**Purpose**: Reusable session configurations

**Table**: `session_templates`

**File**: [app/models/session_template.py:10-64](../../app/models/session_template.py#L10-64)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

# Template Identity
name = Column(String(255), nullable=False, index=True)
description = Column(Text)
category = Column(String(100))  # development, security, production, debugging, performance, custom

# Template Configuration
system_prompt = Column(Text)
working_directory = Column(String(500))
allowed_tools = Column(ARRAY(String))
sdk_options = Column(JSONB, default={})

# MCP Server Configuration
mcp_server_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])

# Sharing and Access
is_public = Column(Boolean, default=False)
is_organization_shared = Column(Boolean, default=False)

# Versioning
version = Column(String(50), default="1.0.0")

# Metadata
tags = Column(ARRAY(String), default=[])
template_metadata = Column(JSONB, default={})

# Usage Statistics
usage_count = Column(Integer, default=0)
last_used_at = Column(DateTime(timezone=True))

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `user`: Many-to-One → UserModel
- `sessions`: One-to-Many → SessionModel

**Indexes**:
- GIN index on `tags`
- Partial indexes on `user_id`, `is_public`, `category`
- Pattern matching index on `name`

**Constraints**:
- `chk_template_category`: category IN (valid categories) OR NULL

---

### 11. HookModel

**Purpose**: Hook configuration for session events

**Table**: `hooks`

**File**: [app/models/hook.py:11-52](../../app/models/hook.py#L11-52)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

# Identity
name = Column(String(255), nullable=False)
description = Column(Text)

# Hook Configuration
hook_event = Column(String(50), nullable=False)
# Events: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop, PreCompact
matcher = Column(String(255))  # Tool name pattern

# Hook Implementation
implementation_type = Column(String(50), nullable=False)  # webhook, script, builtin
implementation_config = Column(JSONB, nullable=False)

# Execution
is_enabled = Column(Boolean, default=True)
execution_timeout_ms = Column(Integer, default=5000)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
deleted_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `user`: Many-to-One → UserModel

**Indexes**:
- Composite index on `(hook_event, is_enabled)`
- Partial index on `user_id` (where deleted_at IS NULL)

**Constraints**:
- `chk_hook_event`: hook_event IN (valid event types)
- `chk_implementation_type`: implementation_type IN ('webhook', 'script', 'builtin')

---

### 12. HookExecutionModel

**Purpose**: Hook execution tracking

**Table**: `hook_executions`

**File**: [app/models/hook_execution.py:11-50](../../app/models/hook_execution.py#L11-50)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
tool_call_id = Column(UUID(as_uuid=True), ForeignKey("tool_calls.id", ondelete="SET NULL"))

# Hook Identity
hook_name = Column(String(100), nullable=False, index=True)
tool_use_id = Column(String(255), nullable=False, index=True)
tool_name = Column(String(255), nullable=False)

# Hook Data
input_data = Column(JSONB, nullable=False)
output_data = Column(JSONB, nullable=False)
context_data = Column(JSONB, default={})

# Execution Metrics
execution_time_ms = Column(Integer, nullable=False)

# Error Handling
error_message = Column(Text)

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
```

**Relationships**:
- `session`: Many-to-One → SessionModel
- `tool_call`: Many-to-One → ToolCallModel

**Indexes**:
- GIN indexes on `input_data` and `output_data`
- Composite indexes on `(session_id, created_at)`, `(hook_name, created_at)`, `(tool_use_id, hook_name)`

---

### 13. PermissionDecisionModel

**Purpose**: Permission check records

**Table**: `permission_decisions`

**File**: [app/models/permission_decision.py:11-48](../../app/models/permission_decision.py#L11-48)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
tool_call_id = Column(UUID(as_uuid=True), ForeignKey("tool_calls.id", ondelete="SET NULL"))

# Tool Identity
tool_use_id = Column(String(255), nullable=False, index=True)
tool_name = Column(String(255), nullable=False, index=True)

# Permission Context
input_data = Column(JSONB, nullable=False)
context_data = Column(JSONB, default={})

# Decision
decision = Column(String(50), nullable=False, index=True)  # allowed, denied, bypassed
reason = Column(Text, nullable=False)
policy_applied = Column(String(255))

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
```

**Relationships**:
- `session`: Many-to-One → SessionModel
- `tool_call`: Many-to-One → ToolCallModel

**Indexes**:
- GIN index on `input_data`
- Composite indexes on `(session_id, created_at)`, `(decision, created_at)`, `(tool_use_id, decision)`, `(tool_name, decision)`

**Constraints**:
- `chk_permission_decision`: decision IN ('allowed', 'denied', 'bypassed')

---

### 14. WorkingDirectoryModel

**Purpose**: Session working directory tracking

**Table**: `working_directories`

**File**: [app/models/working_directory.py:11-46](../../app/models/working_directory.py#L11-46)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

# Paths
directory_path = Column(Text, nullable=False)
archive_path = Column(Text)

# Stats
total_files = Column(Integer, default=0)
total_size_bytes = Column(BigInteger, default=0)

# Archive Status
is_archived = Column(Boolean, default=False)
archived_at = Column(DateTime(timezone=True))

# Metadata
file_manifest = Column(JSONB)  # List of files created/modified

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships**:
- `session`: One-to-One → SessionModel

**Indexes**:
- Unique index on `session_id`
- Index on `is_archived`

---

### 15. WorkingDirectoryArchiveModel

**Purpose**: Session working directory archives

**Table**: `working_directory_archives`

**File**: [app/models/working_directory_archive.py:11-52](../../app/models/working_directory_archive.py#L11-52)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

# Archive Location
archive_path = Column(Text, nullable=False)
storage_backend = Column(String(50), nullable=False)  # s3, filesystem

# Archive Format
compression_type = Column(String(50), nullable=False)  # zip, tar.gz, tar.bz2

# Size Metrics
size_bytes = Column(BigInteger, nullable=False)

# Status
status = Column(String(50), nullable=False, default="pending", index=True)
# Status: pending, in_progress, completed, failed

# Error Handling
error_message = Column(Text)

# Additional Metadata
archive_metadata = Column(JSONB, default={})

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
completed_at = Column(DateTime(timezone=True))
```

**Relationships**:
- `session`: One-to-One → SessionModel

**Indexes**:
- Unique index on `session_id`
- Composite indexes on `(status, created_at)`, `(storage_backend, status)`

**Constraints**:
- `chk_archive_status`: status IN ('pending', 'in_progress', 'completed', 'failed')
- `chk_storage_backend`: storage_backend IN ('s3', 'filesystem')
- `chk_size_bytes`: size_bytes >= 0

---

### 16. SessionMetricsSnapshotModel

**Purpose**: Point-in-time session metrics

**Table**: `session_metrics_snapshots`

**File**: [app/models/session_metrics_snapshot.py:11-62](../../app/models/session_metrics_snapshot.py#L11-62)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)

# Snapshot Type
snapshot_type = Column(String(50), nullable=False)  # hourly, checkpoint, final

# Message Metrics
total_messages = Column(Integer, default=0)
total_tool_calls = Column(Integer, default=0)

# Advanced Metrics
total_hook_executions = Column(Integer, default=0)
total_permission_checks = Column(Integer, default=0)
total_errors = Column(Integer, default=0)
total_retries = Column(Integer, default=0)

# Token Usage
api_input_tokens = Column(Integer, default=0)
api_output_tokens = Column(Integer, default=0)
api_cache_creation_tokens = Column(Integer, default=0)
api_cache_read_tokens = Column(Integer, default=0)

# Cost Metrics
total_cost_usd = Column(Numeric(10, 6), default=0)

# Duration
duration_ms = Column(BigInteger)

# Additional Metrics
metrics_data = Column(JSONB, default={})

# Timestamps
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
```

**Relationships**:
- `session`: Many-to-One → SessionModel

**Indexes**:
- Composite indexes on `(session_id, created_at)`, `(snapshot_type, created_at)`, `(session_id, snapshot_type, created_at)`

---

### 17. AuditLogModel

**Purpose**: Comprehensive audit trail

**Table**: `audit_logs`

**File**: [app/models/audit_log.py:11-58](../../app/models/audit_log.py#L11-58)

**Columns**:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

# Actor
user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"))

# Action
action_type = Column(String(100), nullable=False)
# Examples: session.created, tool.executed, permission.denied, api.request
resource_type = Column(String(50))  # session, task, report, tool
resource_id = Column(UUID(as_uuid=True))

# Details
action_details = Column(JSONB)

# Request Context
ip_address = Column(INET)
user_agent = Column(Text)
request_id = Column(String(255))

# Result
status = Column(String(50))  # success, failure, denied
error_message = Column(Text)

# Timestamp
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
```

**Relationships**:
- `user`: Many-to-One → UserModel
- `session`: Many-to-One → SessionModel

**Indexes**:
- GIN index on `action_details`
- Descending composite indexes on `(user_id, created_at)`, `(session_id, created_at)`, `(action_type, created_at)`
- Composite index on `(resource_type, resource_id)`

**Constraints**:
- `chk_audit_status`: status IN ('success', 'failure', 'denied') OR NULL

---

## Relationship Patterns

### One-to-Many

```python
# Parent side (User → Sessions)
sessions = relationship("SessionModel", back_populates="user")

# Child side (Session → User)
user = relationship("UserModel", back_populates="sessions")
user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
```

### One-to-One

```python
# Session → WorkingDirectory (unique constraint on foreign key)
working_directory = relationship("WorkingDirectoryModel", back_populates="session", uselist=False)

# WorkingDirectory → Session
session = relationship("SessionModel", back_populates="working_directory", uselist=False)
session_id = Column(UUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
```

### Cascade Deletes

**CASCADE**: Delete related records when parent is deleted
```python
messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")
```

**SET NULL**: Set foreign key to NULL when parent is deleted
```python
session_id = Column(UUID, ForeignKey("sessions.id", ondelete="SET NULL"))
```

---

## Type Mappings

### Domain Entity to ORM Model

| Domain Type | ORM Column Type | Example |
|-------------|----------------|---------|
| UUID | UUID(as_uuid=True) | `id = Column(UUID(as_uuid=True))` |
| str | String(length) | `name = Column(String(255))` |
| int | Integer | `max_retries = Column(Integer)` |
| float | Numeric(precision, scale) | `retry_delay = Column(Numeric(10, 2))` |
| bool | Boolean | `is_active = Column(Boolean)` |
| datetime | DateTime(timezone=True) | `created_at = Column(DateTime(timezone=True))` |
| dict | JSONB | `sdk_options = Column(JSONB)` |
| list | ARRAY(item_type) | `tags = Column(ARRAY(String))` |
| IPv4/IPv6 | INET | `ip_address = Column(INET)` |
| Enum | String + CheckConstraint | `role = Column(String(50))` + constraint |

### Enum Handling

Enums are stored as strings with check constraints:

```python
role = Column(String(50), nullable=False, default="user")

__table_args__ = (
    CheckConstraint("role IN ('admin', 'user', 'viewer')", name="chk_role"),
)
```

### JSONB Usage

JSONB columns store flexible structured data:

```python
# Session configuration
sdk_options = Column(JSONB, nullable=False, default={})
# Example: {"allowed_tools": ["Read", "Write"], "permission_mode": "default"}

# Message content
content = Column(JSONB, nullable=False)
# Example: {"content": "Hello", "metadata": {...}}

# Tool input/output
tool_input = Column(JSONB, nullable=False)
# Example: {"path": "/app/test.py", "mode": "read"}
```

**Benefits**:
- Schema flexibility
- GIN indexing for fast queries
- JSON operators in WHERE clauses

---

## Common Model Patterns

### Soft Deletes

```python
deleted_at = Column(DateTime(timezone=True))

# Query only non-deleted records
result = await db.execute(
    select(SessionModel).where(
        and_(
            SessionModel.id == session_id,
            SessionModel.deleted_at.is_(None)
        )
    )
)
```

### Timestamps

```python
created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### UUID Primary Keys

```python
from uuid import uuid4
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
```

---

## Model Exports

**File**: [app/models/__init__.py](../../app/models/__init__.py)

All models are exported from the models package:

```python
__all__ = [
    "OrganizationModel",
    "UserModel",
    "SessionModel",
    "SessionTemplateModel",
    "MessageModel",
    "ToolCallModel",
    "TaskModel",
    "TaskExecutionModel",
    "ReportModel",
    "MCPServerModel",
    "HookModel",
    "WorkingDirectoryModel",
    "AuditLogModel",
    "HookExecutionModel",
    "PermissionDecisionModel",
    "WorkingDirectoryArchiveModel",
    "SessionMetricsSnapshotModel",
]
```

---

## Related Documentation

- **Database Schema**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Complete schema reference
- **Repositories**: [REPOSITORIES.md](REPOSITORIES.md) - Data access layer
- **Migrations**: [MIGRATIONS.md](MIGRATIONS.md) - Schema evolution
- **Base Configuration**: [app/database/base.py](../../app/database/base.py)

---

## Keywords

`orm`, `models`, `sqlalchemy`, `declarative-base`, `relationships`, `cascade`, `foreign-keys`, `jsonb`, `uuid`, `async`, `type-decorators`, `platform-independent`, `table-mapping`, `column-types`, `constraints`, `indexes`, `soft-delete`, `timestamps`, `database-models`, `entity-mapping`
