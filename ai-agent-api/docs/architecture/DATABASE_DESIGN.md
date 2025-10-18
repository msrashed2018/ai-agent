# Database Design

The AI-Agent-API service uses **PostgreSQL** as the primary database with **SQLAlchemy 2.x async ORM** for data persistence. The database schema supports multi-tenancy, session management, and comprehensive audit trails.

## Database Architecture

### Connection Management

**File**: `app/database/session.py`

- **Async Engine**: SQLAlchemy async engine with connection pooling
- **Session Factory**: Async session factory with proper lifecycle management
- **Connection Pooling**: Configurable pool settings for production scaling
- **Transaction Management**: Automatic commit/rollback with error handling

### Cross-Platform Support

**File**: `app/database/base.py`

The service provides cross-platform database support with automatic type adaptation:

```python
# PostgreSQL-optimized types with SQLite fallbacks
JSONB = TypeDecorator()      # PostgreSQL JSONB -> SQLite JSON
INET = TypeDecorator()       # PostgreSQL INET -> SQLite String  
ARRAY = TypeDecorator()      # PostgreSQL ARRAY -> SQLite JSON
```

## Schema Overview

### Entity Relationship Diagram

```mermaid
erDiagram
    organizations ||--o{ users : contains
    users ||--o{ sessions : creates
    users ||--o{ tasks : defines
    users ||--o{ mcp_servers : configures
    
    sessions ||--o{ messages : contains
    sessions ||--o{ tool_calls : executes
    sessions }o--|| sessions : forks_from
    
    tasks ||--o{ task_executions : generates
    task_executions ||--o{ execution_reports : produces
    
    users ||--o{ audit_logs : generates
    sessions ||--o{ audit_logs : generates
```

## Core Tables

### organizations

**Purpose**: Multi-tenant organizational boundaries

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    feature_flags JSONB DEFAULT '{}',
    max_users INTEGER DEFAULT 100,
    max_sessions_per_user INTEGER DEFAULT 10,
    storage_limit_gb INTEGER DEFAULT 100,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    billing_contact JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE is_active = true;
```

### users

**Purpose**: User accounts with authentication and authorization

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    max_concurrent_sessions INTEGER DEFAULT 5,
    max_api_calls_per_hour INTEGER DEFAULT 1000,
    max_storage_mb INTEGER DEFAULT 10240,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
```

### sessions

**Purpose**: AI conversation sessions with state management

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255),
    mode VARCHAR(20) DEFAULT 'interactive' CHECK (mode IN ('interactive', 'non_interactive')),
    status VARCHAR(20) DEFAULT 'created' CHECK (status IN (
        'created', 'connecting', 'active', 'paused', 'waiting', 
        'processing', 'completed', 'failed', 'terminated', 'archived'
    )),
    sdk_options JSONB DEFAULT '{}',
    working_directory_path VARCHAR(1000),
    parent_session_id UUID REFERENCES sessions(id),
    is_fork BOOLEAN DEFAULT false,
    
    -- Metrics
    total_messages INTEGER DEFAULT 0,
    total_tool_calls INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0.0,
    duration_ms INTEGER,
    
    -- API Usage
    api_input_tokens INTEGER DEFAULT 0,
    api_output_tokens INTEGER DEFAULT 0,
    api_cache_creation_tokens INTEGER DEFAULT 0,
    api_cache_read_tokens INTEGER DEFAULT 0,
    
    -- Results
    result_data JSONB,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_active ON sessions(user_id, status) 
    WHERE status IN ('active', 'processing', 'waiting');
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id) 
    WHERE parent_session_id IS NOT NULL;
```

### tasks

**Purpose**: Reusable AI task definitions with scheduling

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_template TEXT NOT NULL,
    allowed_tools JSONB DEFAULT '[]',
    disallowed_tools JSONB DEFAULT '[]',
    sdk_options JSONB DEFAULT '{}',
    working_directory_path VARCHAR(1000),
    
    -- Scheduling
    is_scheduled BOOLEAN DEFAULT false,
    schedule_cron VARCHAR(100),
    schedule_enabled BOOLEAN DEFAULT false,
    
    -- Reporting
    generate_report BOOLEAN DEFAULT false,
    report_format VARCHAR(20) CHECK (report_format IN ('json', 'markdown', 'html', 'pdf')),
    notification_config JSONB,
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    is_deleted BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_active ON tasks(user_id, is_active, is_deleted) 
    WHERE is_active = true AND is_deleted = false;
CREATE INDEX idx_tasks_scheduled ON tasks(is_scheduled, schedule_enabled) 
    WHERE is_scheduled = true AND schedule_enabled = true;
```

## Message and Tool Call Tables

### messages

**Purpose**: Store conversation messages and AI responses

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN (
        'human', 'assistant', 'system', 'tool_result', 'error'
    )),
    content TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    model VARCHAR(100),
    parent_tool_use_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON messages(session_id, sequence_number);
CREATE INDEX idx_messages_type ON messages(session_id, message_type);
CREATE UNIQUE INDEX idx_messages_sequence ON messages(session_id, sequence_number);
```

### tool_calls

**Purpose**: Track AI tool execution requests and results

```sql
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),
    tool_name VARCHAR(100) NOT NULL,
    tool_use_id VARCHAR(100) NOT NULL,
    tool_input JSONB NOT NULL,
    tool_output JSONB,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'denied', 'executing', 'completed', 'failed'
    )),
    is_error BOOLEAN DEFAULT false,
    error_message TEXT,
    permission_decision VARCHAR(20) CHECK (permission_decision IN (
        'auto_approved', 'user_approved', 'user_denied', 'policy_denied'
    )),
    permission_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

CREATE INDEX idx_tool_calls_session ON tool_calls(session_id, created_at);
CREATE INDEX idx_tool_calls_status ON tool_calls(status);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);
```

## External Integration Tables

### mcp_servers

**Purpose**: User-configured Model Context Protocol servers

```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),  -- NULL for global servers
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    server_type VARCHAR(50) NOT NULL CHECK (server_type IN (
        'stdio', 'sse', 'websocket'
    )),
    config JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    is_global BOOLEAN DEFAULT false,  -- Available to all org users
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_mcp_servers_user_name ON mcp_servers(user_id, name) 
    WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX idx_mcp_servers_global_name ON mcp_servers(organization_id, name) 
    WHERE is_global = true;
CREATE INDEX idx_mcp_servers_enabled ON mcp_servers(is_enabled) WHERE is_enabled = true;
```

## Execution and Reporting Tables

### task_executions

**Purpose**: Track task execution instances and results

```sql
CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    session_id UUID NOT NULL REFERENCES sessions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    variables JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN (
        'running', 'completed', 'failed', 'cancelled'
    )),
    result JSONB,
    error_message TEXT,
    duration_ms INTEGER,
    cost_usd DECIMAL(10,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_task_executions_task ON task_executions(task_id, created_at);
CREATE INDEX idx_task_executions_user ON task_executions(user_id, created_at);
CREATE INDEX idx_task_executions_status ON task_executions(status);
```

### execution_reports

**Purpose**: Generated reports from task executions

```sql
CREATE TABLE execution_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_executions(id),
    format VARCHAR(20) NOT NULL CHECK (format IN ('json', 'markdown', 'html', 'pdf')),
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_execution_reports_execution ON execution_reports(execution_id);
CREATE INDEX idx_execution_reports_format ON execution_reports(format);
```

## Audit and Logging Tables

### audit_logs

**Purpose**: Comprehensive audit trail for compliance and debugging

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    organization_id UUID REFERENCES organizations(id),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30) NOT NULL CHECK (event_category IN (
        'authentication', 'authorization', 'session', 'task', 'tool', 'system'
    )),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_session ON audit_logs(session_id, created_at);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type, created_at);
CREATE INDEX idx_audit_logs_category ON audit_logs(event_category, created_at);
```

## Database Configuration

### Connection Settings

**Production Configuration**:

```python
# Database connection with pooling
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/dbname"
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

### Performance Optimizations

**Indexing Strategy**:

- **Primary Keys**: All UUIDs with btree indexes
- **Foreign Keys**: Indexes on all foreign key columns  
- **Query Patterns**: Indexes optimized for common query patterns
- **Partial Indexes**: Conditional indexes for filtered queries
- **Composite Indexes**: Multi-column indexes for complex queries

**Query Optimization**:

- **Eager Loading**: Strategic use of `selectinload()` and `joinedload()`
- **Pagination**: Efficient offset/limit with proper ordering
- **Bulk Operations**: Batch inserts/updates for large datasets
- **Connection Pooling**: Async connection pool management

### Data Retention Policies

**Archive Strategy**:

- **Completed Sessions**: Archive after 90 days
- **Audit Logs**: Retain for 1 year, archive older entries
- **Tool Call Data**: Compress after 30 days
- **File Storage**: Clean up working directories after archival

**Cleanup Procedures**:

```sql
-- Archive old sessions
UPDATE sessions 
SET status = 'archived', updated_at = NOW()
WHERE status IN ('completed', 'failed', 'terminated')
  AND completed_at < NOW() - INTERVAL '90 days';

-- Clean up old audit logs
DELETE FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '2 years';
```

## Migration Strategy

### Schema Migrations

Using **Alembic** for database schema migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations  
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Data Migration Patterns

- **Backward Compatible**: Additive changes that don't break existing code
- **Two-Phase Migrations**: Deploy code, then migrate data, then cleanup
- **Zero-Downtime**: Use database features for online schema changes
- **Rollback Safety**: All migrations must be reversible