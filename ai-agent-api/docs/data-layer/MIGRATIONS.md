# Database Migrations

## Purpose

Complete documentation of Alembic database migrations workflow, history, and best practices for evolving the database schema safely and reversibly.

---

## Migration Overview

### What are Database Migrations?

Migrations are **version-controlled database schema changes** that allow:
- **Evolution**: Gradually evolve schema as requirements change
- **Reversibility**: Rollback changes if needed
- **Team Synchronization**: All developers work with same schema version
- **Deployment Safety**: Apply changes systematically in production
- **Audit Trail**: Track what changed, when, and why

### Why Use Alembic?

**Alembic** is the standard migration tool for SQLAlchemy:
- Auto-generates migrations from model changes
- Supports both upgrade and downgrade operations
- Handles complex schema changes (renames, data migrations)
- Integrates seamlessly with SQLAlchemy 2.0 async

---

## Alembic Setup

### Directory Structure

```
ai-agent-api/
├── alembic/
│   ├── versions/
│   │   ├── 20251018_0230_972fc63ffb69_initial_database_schema.py
│   │   ├── 20251018_0355_567cc0f251e5_add_session_templates_table.py
│   │   └── 20251019_0058_c0b7d0e366e7_phase1_claude_sdk_v2_foundation.py
│   ├── env.py          # Alembic environment configuration
│   └── script.py.mako  # Migration template
├── alembic.ini          # Alembic configuration
└── app/
    ├── models/          # SQLAlchemy models
    └── database/
        └── base.py      # Declarative base
```

### Configuration File

**File**: [alembic.ini:1-50](../../alembic.ini#L1-50)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .

# Template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Maximum length of characters to apply to the "slug" field
# truncate_slug_length = 40

# Version path separator
version_path_separator = os  # Use os.pathsep

# Database URL (overridden in env.py from settings)
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dbname
```

**Key Settings**:
- `script_location`: Where migration scripts are stored
- `file_template`: Migration filename format (includes timestamp)
- `version_path_separator`: Path separator for multiple version directories

### Environment Configuration

**File**: [alembic/env.py](../../alembic/env.py)

```python
"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models for autogenerate support
from app.core.config import settings
from app.database.base import Base
from app.models.user import UserModel, OrganizationModel
from app.models.session import SessionModel
from app.models.message import MessageModel
# ... all other models

# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set target metadata for autogenerate
target_metadata = Base.metadata
```

**Key Components**:

#### Model Imports

All models must be imported for autogenerate to detect changes:

```python
from app.models.user import UserModel, OrganizationModel
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.tool_call import ToolCallModel
# ... import all models
```

#### Custom Type Rendering

Handle custom JSONB, ARRAY, INET types:

```python
def render_item(type_, obj, autogen_context):
    """Render custom types without module prefix."""
    from app.database.base import JSONB, ARRAY, INET

    if type_ == "type":
        if isinstance(obj, JSONB):
            return "JSONB()"
        elif isinstance(obj, INET):
            return "INET()"
        elif isinstance(obj, ARRAY):
            item_type = getattr(obj, 'item_type', String)
            item_type_name = item_type.__name__ if hasattr(item_type, '__name__') else "String"
            return f"ARRAY(sa.{item_type_name})"
    return False
```

#### Async Migration Support

Run migrations with async engine:

```python
async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())
```

---

## Migration History

### Migration 1: Initial Database Schema

**File**: [alembic/versions/20251018_0230_972fc63ffb69_initial_database_schema.py](../../alembic/versions/20251018_0230_972fc63ffb69_initial_database_schema.py)

**Revision**: 972fc63ffb69
**Down Revision**: None (initial)
**Created**: 2025-10-18 02:30

**What it Does**:

Creates all core tables:

1. **organizations** - Multi-tenant organization table
   - Columns: id, name, slug, plan, quotas, timestamps
   - Check constraint on plan

2. **users** - User authentication and authorization
   - Columns: id, organization_id, email, username, password_hash, role, quotas, timestamps
   - Foreign key to organizations (CASCADE)
   - Unique constraints on email, username
   - Check constraints on role and quotas

3. **hooks** - Hook configuration
   - Columns: id, user_id, name, hook_event, implementation_type, config, timestamps
   - Foreign key to users (CASCADE)

4. **mcp_servers** - MCP server configurations
   - Columns: id, user_id, name, server_type, config, health_status, timestamps
   - Foreign key to users (CASCADE)

5. **tasks** - Task templates
   - Columns: id, user_id, name, prompt_template, tools, scheduling, timestamps
   - Foreign key to users (CASCADE)

6. **sessions** - Agent sessions
   - Columns: id, user_id, name, mode, status, sdk_options, metrics, timestamps
   - Foreign key to users (CASCADE)
   - Self-referencing foreign key (parent_session_id)

7. **messages** - Chat messages
   - Columns: id, session_id, message_type, content (JSONB), sequence_number, timestamps
   - Foreign key to sessions (CASCADE)
   - Unique composite index on (session_id, sequence_number)

8. **tool_calls** - Tool execution records
   - Columns: id, session_id, message_id, tool_name, tool_use_id, input/output (JSONB), status, timestamps
   - Foreign keys to sessions (CASCADE) and messages (SET NULL)

9. **task_executions** - Task execution history
   - Columns: id, task_id, session_id, status, trigger_type, results, timestamps
   - Foreign keys to tasks (CASCADE) and sessions (SET NULL)

10. **reports** - Generated reports
    - Columns: id, session_id, user_id, task_execution_id, content (JSONB), file_path, timestamps
    - Foreign keys to sessions, users, task_executions

11. **working_directories** - Session working directories
    - Columns: id, session_id, directory_path, stats, archive_status, timestamps
    - Foreign key to sessions (CASCADE)

12. **audit_logs** - Audit trail
    - Columns: id, user_id, session_id, action_type, resource_type, details (JSONB), ip_address (INET), timestamps
    - Foreign keys to users and sessions (SET NULL)

**Example Upgrade Code**:

```python
def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        # ... more columns
        sa.CheckConstraint("role IN ('admin', 'user', 'viewer')", name='ck_users_chk_role'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
```

---

### Migration 2: Add Session Templates

**File**: [alembic/versions/20251018_0355_567cc0f251e5_add_session_templates_table.py](../../alembic/versions/20251018_0355_567cc0f251e5_add_session_templates_table.py)

**Revision**: 567cc0f251e5
**Down Revision**: 972fc63ffb69
**Created**: 2025-10-18 03:55

**What it Does**:

1. **Creates session_templates table**:
   - Columns: id, user_id, name, description, category, system_prompt, sdk_options, mcp_server_ids, visibility flags, tags (ARRAY), metadata (JSONB), usage stats, timestamps
   - Foreign key to users (CASCADE)
   - Check constraint on category
   - GIN index on tags for array searches
   - Partial indexes for performance

2. **Adds template_id to sessions**:
   - New foreign key column linking sessions to templates

3. **Fixes audit_logs indexes**:
   - Adds descending order operators on created_at columns
   - Improves query performance for time-based filtering

**Example Upgrade Code**:

```python
def upgrade() -> None:
    op.create_table('session_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('sdk_options', JSONB(), nullable=True),
        # ... more columns
        sa.CheckConstraint("category IN ('development', 'security', 'production', 'debugging', 'performance', 'custom') OR category IS NULL"),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_templates_tags', 'session_templates', ['tags'], postgresql_using='gin')
```

---

### Migration 3: Phase 1 Claude SDK v2 Foundation

**File**: [alembic/versions/20251019_0058_c0b7d0e366e7_phase1_claude_sdk_v2_foundation.py](../../alembic/versions/20251019_0058_c0b7d0e366e7_phase1_claude_sdk_v2_foundation.py)

**Revision**: c0b7d0e366e7
**Down Revision**: 567cc0f251e5
**Created**: 2025-10-19 00:58

**What it Does**:

Major update to support Claude SDK v2 features:

1. **Creates working_directory_archives table**:
   - Archive session working directories to S3 or filesystem
   - Columns: id, session_id, archive_path, storage_backend, compression_type, size_bytes, status, error_message, metadata (JSONB), timestamps
   - Check constraints on status, storage_backend, size_bytes
   - Composite indexes for efficient queries

2. **Creates session_metrics_snapshots table**:
   - Point-in-time metrics for sessions
   - Columns: id, session_id, snapshot_type, all metric fields (messages, tokens, costs, hooks, permissions), metrics_data (JSONB), timestamps
   - Composite indexes on (session_id, created_at), (snapshot_type, created_at)

3. **Creates hook_executions table**:
   - Track hook executions
   - Columns: id, session_id, tool_call_id, hook_name, tool_use_id, tool_name, input_data (JSONB), output_data (JSONB), context_data (JSONB), execution_time_ms, error_message, timestamps
   - Foreign keys to sessions (CASCADE) and tool_calls (SET NULL)
   - GIN indexes on JSONB columns

4. **Creates permission_decisions table**:
   - Track permission check decisions
   - Columns: id, session_id, tool_call_id, tool_use_id, tool_name, input_data (JSONB), context_data (JSONB), decision, reason, policy_applied, timestamps
   - Check constraint on decision values
   - GIN index on input_data

5. **Adds columns to sessions table**:
   - SDK v2 configuration: include_partial_messages, max_retries, retry_delay, timeout_seconds, hooks_enabled (JSONB), permission_mode, custom_policies (JSONB)
   - Advanced metrics: total_hook_executions, total_permission_checks, total_errors, total_retries
   - References: archive_id, template_id

6. **Adds columns to messages table**:
   - Streaming support: is_partial, parent_message_id, thinking_content
   - Self-referencing foreign key for partial message tracking

7. **Adds columns to tool_calls table**:
   - Advanced metrics: retries, hook_pre_data (JSONB), hook_post_data (JSONB)

**Example Upgrade Code**:

```python
def upgrade() -> None:
    # Create working_directory_archives table
    op.create_table('working_directory_archives',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('archive_path', sa.Text(), nullable=False),
        sa.Column('storage_backend', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed')"),
        sa.CheckConstraint("storage_backend IN ('s3', 'filesystem')"),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add columns to sessions
    op.add_column('sessions', sa.Column('include_partial_messages', sa.Boolean(), nullable=True))
    op.add_column('sessions', sa.Column('max_retries', sa.Integer(), nullable=True))
    op.add_column('sessions', sa.Column('hooks_enabled', JSONB(), nullable=True))
    # ... more columns
```

---

## Creating Migrations

### Auto-Generate from Model Changes

**Step 1**: Modify your SQLAlchemy models

```python
# app/models/my_model.py
class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    new_field = Column(String(100))  # New field added
```

**Step 2**: Generate migration

```bash
alembic revision --autogenerate -m "add new_field to my_table"
```

This creates a new file:
```
alembic/versions/20251019_1430_abc123_add_new_field_to_my_table.py
```

**Step 3**: Review generated migration

```python
def upgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.add_column('my_table', sa.Column('new_field', sa.String(length=100), nullable=True))
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.drop_column('my_table', 'new_field')
    # ### end Alembic commands ###
```

**IMPORTANT**: Always review auto-generated migrations! They may be incomplete or incorrect.

### Manual Migration Creation

Create empty migration template:

```bash
alembic revision -m "custom migration description"
```

Write upgrade and downgrade manually:

```python
def upgrade() -> None:
    # Add custom SQL or operations
    op.execute("UPDATE sessions SET status = 'archived' WHERE completed_at < NOW() - INTERVAL '90 days'")

def downgrade() -> None:
    # Reverse the operation
    op.execute("UPDATE sessions SET status = 'completed' WHERE status = 'archived'")
```

---

## Applying Migrations

### Upgrade to Latest

Apply all pending migrations:

```bash
alembic upgrade head
```

Output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 972fc63ffb69, initial database schema
INFO  [alembic.runtime.migration] Running upgrade 972fc63ffb69 -> 567cc0f251e5, add session_templates table
INFO  [alembic.runtime.migration] Running upgrade 567cc0f251e5 -> c0b7d0e366e7, phase1 claude sdk v2 foundation
```

### Upgrade to Specific Version

```bash
alembic upgrade 567cc0f251e5
```

### Upgrade One Step

```bash
alembic upgrade +1
```

### Downgrade

Rollback one migration:

```bash
alembic downgrade -1
```

Rollback to specific version:

```bash
alembic downgrade 972fc63ffb69
```

Rollback all migrations:

```bash
alembic downgrade base
```

### Check Current Version

```bash
alembic current
```

Output:
```
c0b7d0e366e7 (head)
```

### View Migration History

```bash
alembic history
```

Output:
```
972fc63ffb69 -> 567cc0f251e5 (head), add session_templates table
<base> -> 972fc63ffb69, initial database schema
```

Verbose with details:

```bash
alembic history --verbose
```

---

## Migration File Structure

### Migration Template

```python
"""<migration description>

Revision ID: <revision_id>
Revises: <previous_revision_id>
Create Date: <timestamp>

"""
from alembic import op
import sqlalchemy as sa
from app.database.base import JSONB, ARRAY, INET

# revision identifiers, used by Alembic.
revision = '<revision_id>'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
```

### Key Components

- **Revision ID**: Unique identifier for this migration
- **Down Revision**: Previous migration (forms chain)
- **upgrade()**: Apply changes
- **downgrade()**: Reverse changes

---

## Common Migration Tasks

### Adding a New Table

```python
def upgrade() -> None:
    op.create_table('new_table',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('new_table')
```

### Adding a Column

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

### Modifying Column Type

```python
def upgrade() -> None:
    # Change column type
    op.alter_column('sessions', 'timeout_seconds',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)

def downgrade() -> None:
    op.alter_column('sessions', 'timeout_seconds',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)
```

### Adding an Index

```python
def upgrade() -> None:
    op.create_index('idx_sessions_user_status', 'sessions', ['user_id', 'status'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_sessions_user_status', table_name='sessions')
```

### Adding a Foreign Key

```python
def upgrade() -> None:
    op.add_column('sessions', sa.Column('template_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_sessions_template_id_session_templates',
                          'sessions', 'session_templates',
                          ['template_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('fk_sessions_template_id_session_templates', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'template_id')
```

### Data Migration

Insert, update, or delete data:

```python
from sqlalchemy import table, column

def upgrade() -> None:
    # Get table reference
    sessions_table = table('sessions',
        column('id', sa.UUID),
        column('status', sa.String)
    )

    # Update data
    op.execute(
        sessions_table.update()
        .where(sessions_table.c.status == 'old_status')
        .values(status='new_status')
    )

def downgrade() -> None:
    sessions_table = table('sessions',
        column('id', sa.UUID),
        column('status', sa.String)
    )

    op.execute(
        sessions_table.update()
        .where(sessions_table.c.status == 'new_status')
        .values(status='old_status')
    )
```

---

## Migration Best Practices

### DO

1. **Always Review Auto-Generated Migrations**
   - Autogenerate is a starting point, not the final version
   - Check for missing indexes, constraints, or data migrations

2. **Test Migrations on Staging First**
   - Never run untested migrations in production
   - Verify both upgrade and downgrade work

3. **Write Reversible Downgrades**
   - Every upgrade should have a working downgrade
   - Test downgrades as thoroughly as upgrades

4. **Handle Data Migrations Separately**
   - Don't mix schema changes with data migrations
   - Use separate migrations for complex data transformations

5. **Backup Database Before Migrations**
   - Always have a rollback plan
   - Test restore procedures

6. **Use Transactions**
   - Alembic uses transactions by default
   - Ensure migrations are atomic

7. **Document Complex Migrations**
   - Add comments explaining why changes were made
   - Document any manual steps required

### DON'T

1. **Don't Edit Applied Migrations**
   - Once a migration is applied, create a new migration to change it
   - Editing applied migrations breaks version control

2. **Don't Skip Migrations**
   - Always apply migrations in order
   - Don't cherry-pick migrations

3. **Don't Delete Migrations**
   - Migrations are the history of your schema
   - Keep all migrations even if no longer needed

4. **Don't Use Blocking Operations on Large Tables**
   - Avoid ALTER TABLE on tables with millions of rows
   - Use online schema change tools for large tables

5. **Don't Ignore Migration Warnings**
   - Alembic warnings indicate potential issues
   - Fix warnings before applying migrations

---

## Production Migration Workflow

### Zero-Downtime Migrations

1. **Make changes backward compatible**:
   ```python
   # Step 1: Add new column (nullable)
   op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))

   # Step 2: Deploy code that writes to both old and new fields

   # Step 3: Backfill data
   op.execute("UPDATE users SET new_field = old_field WHERE new_field IS NULL")

   # Step 4: Make column non-nullable
   op.alter_column('users', 'new_field', nullable=False)

   # Step 5: Deploy code that only uses new field

   # Step 6: Drop old column
   op.drop_column('users', 'old_field')
   ```

2. **Deploy in stages**:
   - Deploy migration separately from code
   - Monitor for errors before proceeding

3. **Use feature flags**:
   - Gradually roll out changes
   - Quick rollback if issues arise

### Rolling Back Failed Migrations

```bash
# If migration fails mid-way, rollback
alembic downgrade -1

# Fix the migration
# Edit the migration file

# Reapply
alembic upgrade head
```

---

## Troubleshooting

### Migration Conflicts

**Problem**: Two developers create migrations with same down_revision

**Solution**: Merge migrations manually
```bash
# Create merge migration
alembic merge -m "merge heads" <revision1> <revision2>
```

### Schema Drift

**Problem**: Database schema doesn't match migrations

**Solution**: Generate migration to sync
```bash
# This will detect differences
alembic revision --autogenerate -m "sync schema"
```

### Manual Fixes

**Problem**: Need to manually fix database

**Solution**: Mark migration as applied without running it
```bash
# Mark migration as applied (dangerous!)
alembic stamp <revision_id>
```

---

## Related Documentation

- **Database Schema**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Current schema reference
- **ORM Models**: [ORM_MODELS.md](ORM_MODELS.md) - Model definitions
- **Alembic Documentation**: https://alembic.sqlalchemy.org/

---

## Keywords

`migrations`, `alembic`, `database`, `schema-evolution`, `version-control`, `upgrade`, `downgrade`, `rollback`, `autogenerate`, `data-migration`, `zero-downtime`, `production`, `sqlalchemy`, `async`, `postgresql`, `schema-changes`, `backward-compatibility`, `deployment`
