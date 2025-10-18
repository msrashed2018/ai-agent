# Session Management Commands

Complete guide for session commands with detailed backend flow and Claude Code SDK integration based on actual implementation.

---

## Command: `sessions create`

### CLI Command
```bash
ai-agent sessions create \
  --name "Investigation Session" \
  --description "Investigating production issue" \
  --allowed-tools "Read" \
  --allowed-tools "Bash" \
  --working-directory "/workspace/project"
```

### What Happens in the Backend

#### Step 1: HTTP Request to API
```http
POST /api/v1/sessions HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Investigation Session",
  "description": "Investigating production issue",
  "working_directory": "/workspace/project",
  "allowed_tools": ["Read", "Bash"],
  "system_prompt": null,
  "sdk_options": null,
  "metadata": null
}
```

#### Step 2: API Processing Flow

**Route Handler:** `app/api/v1/sessions.py:create_session()`

**Service:** `app/services/sdk_session_service.py:SDKIntegratedSessionService`

1. **User Authentication**
   - JWT token validation (via `get_current_active_user` dependency)
   - Extracts user_id from token

2. **Working Directory Creation**
   ```python
   # StorageManager creates isolated directory
   working_dir = storage_manager.create_session_directory(session_id)
   # Result: /data/sessions/{session_id}/
   ```

3. **Database Insert**
   ```sql
   INSERT INTO sessions (
       id, user_id, name, description, status,
       working_directory, allowed_tools, system_prompt,
       sdk_options, metadata, created_at
   ) VALUES (
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       '550e8400-e29b-41d4-a716-446655440000',
       'Investigation Session',
       'Investigating production issue',
       'created',
       '/data/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       '["Read", "Bash"]'::jsonb,
       NULL,
       '{}'::jsonb,
       '{}'::jsonb,
       CURRENT_TIMESTAMP
   );
   ```

4. **Audit Log Entry**
   ```sql
   INSERT INTO audit_logs (
       id, user_id, session_id, action,
       resource_type, resource_id, timestamp
   ) VALUES (
       uuid_generate_v4(),
       '550e8400-e29b-41d4-a716-446655440000',
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       'SESSION_CREATED',
       'session',
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       CURRENT_TIMESTAMP
   );
   ```

#### Step 3: API Response
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Investigation Session",
  "description": "Investigating production issue",
  "status": "created",
  "working_directory": "/data/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "allowed_tools": ["Read", "Bash"],
  "system_prompt": null,
  "sdk_options": {},
  "parent_session_id": null,
  "is_fork": false,
  "message_count": 0,
  "tool_call_count": 0,
  "total_cost_usd": 0.0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "created_at": "2025-10-18T11:00:00",
  "updated_at": "2025-10-18T11:00:00",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "metadata": {},
  "_links": {
    "self": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "query": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/query",
    "messages": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages",
    "tool_calls": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/tool-calls",
    "stream": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/stream"
  }
}
```

#### Step 4: Claude SDK Integration
**Not Yet** - SDK client is created lazily on first query, not at session creation.

### Expected CLI Output
```
✓ Session created: a1b2c3d4-e5f6-7890-abcd-ef1234567890

┌─────────────────┬────────────────────────────────────────┐
│             Key │ Value                                  │
├─────────────────┼────────────────────────────────────────┤
│              Id │ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│         User Id │ 550e8400-e29b-41d4-a716-446655440000   │
│            Name │ Investigation Session                  │
│     Description │ Investigating production issue         │
│          Status │ created                                │
│ Working Dir     │ /data/sessions/a1b2c3d4                │
│   Allowed Tools │ ["Read", "Bash"]                       │
│      Created At │ 2025-10-18T11:00:00                    │
└─────────────────┴────────────────────────────────────────┘
```

---

## Command: `sessions query` (Send Message)

### CLI Command
```bash
ai-agent sessions query a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  "What files are in the current directory?"
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
POST /api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/query HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": "What files are in the current directory?",
  "fork": false
}
```

#### Step 2: Session Validation & Status Update

**Service:** `SDKIntegratedSessionService.send_message()`

1. **Load Session from Database**
   ```sql
   SELECT * FROM sessions
   WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
   ```

2. **Validate Status** (must be `created` or `active`)

3. **Update Session Status**
   ```sql
   UPDATE sessions
   SET status = 'active', started_at = CURRENT_TIMESTAMP
   WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

   UPDATE sessions
   SET status = 'processing'
   WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
   ```

#### Step 3: Claude SDK Client Setup (First Query Only)

**Method:** `SDKIntegratedSessionService._setup_sdk_client()`

This happens ONLY on the first query to the session.

##### 3.1: Build MCP Configuration

**Service:** `MCPConfigBuilder.build_session_mcp_config()`

Builds complete MCP config by merging three sources:

1. **SDK MCP Tools** (Python in-process tools from `app/mcp/sdk_tools.py`)
   ```python
   SDK_MCP_SERVERS = {
       "kubernetes_readonly": {
           "type": "sdk",
           "tools": ["list_pods", "get_pod_logs", "describe_pod"]
       },
       "database": {
           "type": "sdk",
           "tools": ["query_database", "get_schema"]
       },
       "monitoring": {
           "type": "sdk",
           "tools": ["get_metrics", "check_alerts"]
       }
   }
   ```

2. **User's External MCP Servers** (from database)
   ```sql
   SELECT name, server_type, config, is_enabled
   FROM mcp_servers
   WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
   AND is_enabled = true;
   ```

3. **Global MCP Servers** (from database)
   ```sql
   SELECT name, server_type, config, is_enabled
   FROM mcp_servers
   WHERE is_global = true
   AND is_enabled = true;
   ```

**Merged MCP Config Result:**
```python
mcp_servers = {
    # SDK Tools (in-process Python)
    "kubernetes_readonly": {
        "type": "sdk",
        "tools": ["list_pods", "get_pod_logs", "describe_pod"]
    },
    "database": {
        "type": "sdk",
        "tools": ["query_database", "get_schema"]
    },
    "monitoring": {
        "type": "sdk",
        "tools": ["get_metrics", "check_alerts"]
    },

    # User's External Servers (stdio/http)
    "user-filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
        "env": {}
    },
    "user-postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."],
        "env": {}
    },

    # Global External Servers
    "global-github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": "..."}
    }
}
```

##### 3.2: Update Session with MCP Config
```sql
UPDATE sessions
SET sdk_options = '{
  "mcp_servers": {
    "kubernetes_readonly": {...},
    "database": {...},
    "monitoring": {...},
    "user-filesystem": {...},
    "user-postgres": {...},
    "global-github": {...}
  }
}'::jsonb
WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
```

##### 3.3: Create Permission Callback

**Service:** `PermissionService.create_permission_callback()`

```python
async def permission_callback(tool_name: str) -> bool:
    """Check if session can use this tool."""
    # Check against session.allowed_tools
    # Check user permissions
    # Log permission request in audit_log
    return True/False
```

##### 3.4: Create Hook Handlers

```python
hooks = {
    "PreToolUse": [
        # Audit logging hook
        lambda event: audit_service.log_tool_use(session_id, tool_name),

        # Tool tracking hook
        lambda event: tool_call_repo.create({
            "session_id": session_id,
            "tool_name": tool_name,
            "tool_input": input,
            "status": "pending"
        })
    ],
    "PostToolUse": [
        # Update tool call with result
        lambda event: tool_call_repo.update(tool_call_id, {
            "tool_output": output,
            "status": "success",
            "duration_ms": duration
        }),

        # Cost tracking hook
        lambda event: session_repo.update(session_id, {
            "total_cost_usd": session.total_cost_usd + cost
        })
    ]
}
```

##### 3.5: Create Claude SDK Client

**Service:** `ClaudeSDKClientManager.create_client()`

```python
# Build ClaudeAgentOptions from session
options = ClaudeAgentOptions(
    # Tool configuration
    allowed_tools=["Read", "Bash"],  # from session
    disallowed_tools=[],

    # Permission mode
    permission_mode="default",

    # Working directory
    cwd="/data/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",

    # MCP servers (merged config)
    mcp_servers=mcp_servers,

    # System prompt
    system_prompt=None,

    # Model settings
    model="claude-sonnet-4-5",
    max_turns=25,

    # Additional settings
    env={},
    add_dirs=[],

    # Permission callback
    can_use_tool=permission_callback,
    permission_prompt_tool_name="stdio",

    # Hooks
    hooks=hooks
)

# Create official SDK client
client = ClaudeSDKClient(options=options)
await client.connect(prompt=None)
```

#### Step 4: Claude Code CLI Invocation

**What the SDK Actually Calls:**

The `ClaudeSDKClient.connect()` spawns a subprocess that runs the Claude Code CLI:

```bash
claude \
  --model claude-sonnet-4-5 \
  --cwd /data/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --permission-mode default \
  --mcp-server kubernetes_readonly:sdk \
  --mcp-server database:sdk \
  --mcp-server monitoring:sdk \
  --mcp-server user-filesystem:npx:-y:@modelcontextprotocol/server-filesystem:/workspace \
  --mcp-server user-postgres:npx:-y:@modelcontextprotocol/server-postgres:postgresql://... \
  --mcp-server global-github:npx:-y:@modelcontextprotocol/server-github \
  --allowed-tools "Read,Bash"
```

**Note:** The actual command format varies based on SDK implementation, but conceptually:
- Spawns `claude` CLI process
- Passes working directory
- Configures MCP servers (both SDK tools and external servers)
- Sets permission callback for tool approval
- Establishes stdin/stdout communication

#### Step 5: Send Message to Claude

```python
# Send user message through SDK
await client.query("What files are in the current directory?")
```

**This internally sends to Claude Code CLI:**
```
USER MESSAGE: What files are in the current directory?
```

Claude Code CLI then:
1. Receives message
2. Processes with Claude API
3. May invoke tools (Bash: `ls -la`)
4. Returns response stream

#### Step 6: Process Response Stream

**Service:** `MessageProcessor.process_message_stream()`

For each message in the stream:

1. **User Message** - Store in database
   ```sql
   INSERT INTO messages (
       id, session_id, message_type, content,
       token_count, cost_usd, created_at
   ) VALUES (
       uuid_generate_v4(),
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       'user',
       '{"text": "What files are in the current directory?"}',
       12,
       0.0001,
       CURRENT_TIMESTAMP
   );
   ```

2. **Assistant Message** - Store response
   ```sql
   INSERT INTO messages (
       id, session_id, message_type, content,
       token_count, cost_usd, created_at
   ) VALUES (
       uuid_generate_v4(),
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       'assistant',
       '{"text": "I''ll check the directory for you.", "tool_uses": [...]}',
       145,
       0.0015,
       CURRENT_TIMESTAMP
   );
   ```

3. **Tool Use** - Track tool execution
   ```sql
   INSERT INTO tool_calls (
       id, session_id, tool_name, tool_input,
       tool_output, status, started_at, completed_at,
       duration_ms
   ) VALUES (
       uuid_generate_v4(),
       'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
       'Bash',
       '{"command": "ls -la"}',
       '{"stdout": "total 24\ndrwxr-xr-x ..."}',
       'success',
       CURRENT_TIMESTAMP,
       CURRENT_TIMESTAMP,
       125
   );
   ```

4. **Update Session Metrics**
   ```sql
   UPDATE sessions
   SET
       message_count = message_count + 2,
       tool_call_count = tool_call_count + 1,
       total_input_tokens = total_input_tokens + 157,
       total_output_tokens = total_output_tokens + 245,
       total_cost_usd = total_cost_usd + 0.0016,
       updated_at = CURRENT_TIMESTAMP
   WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
   ```

#### Step 7: Return to Active Status
```sql
UPDATE sessions
SET status = 'active'
WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
```

#### Step 8: API Response
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "active",
  "parent_session_id": null,
  "is_fork": false,
  "message_id": "d4e5f6a7-b8c9-0123-defg-456789012345",
  "_links": {
    "self": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages/d4e5f6a7-b8c9-0123-defg-456789012345",
    "stream": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/stream"
  }
}
```

### Complete Flow Diagram

```
CLI Command
    │
    ▼
HTTP POST /api/v1/sessions/{id}/query
    │
    ▼
API Route Handler
    │
    ├─► Validate Session
    ├─► Update Status: processing
    │
    ├─► First Query? ──► YES ──► Setup SDK Client
    │                            │
    │                            ├─► Build MCP Config
    │                            │   ├─► SDK Tools (Python)
    │                            │   ├─► User MCP Servers (DB query)
    │                            │   └─► Global MCP Servers (DB query)
    │                            │
    │                            ├─► Update Session.sdk_options (DB)
    │                            │
    │                            ├─► Create Permission Callback
    │                            ├─► Create Hook Handlers
    │                            │
    │                            └─► Create ClaudeSDKClient
    │                                    │
    │                                    ▼
    │                            Spawn Claude Code CLI subprocess
    │                            with all MCP servers configured
    │
    ├─► Send Message to SDK
    │       │
    │       ▼
    │   Claude Code CLI Process
    │       ├─► Claude API
    │       ├─► Execute Tools (if needed)
    │       │   ├─► SDK Tools (Python functions)
    │       │   └─► External MCP Servers (stdio/http)
    │       └─► Return Response Stream
    │
    ├─► Process Response Stream
    │   ├─► Store User Message (DB)
    │   ├─► Store Assistant Messages (DB)
    │   ├─► Track Tool Calls (DB)
    │   └─► Update Session Metrics (DB)
    │
    ├─► Update Status: active
    │
    └─► Return Response to CLI
```

### Expected CLI Output
```
✓ Message sent to session a1b2c3d4-e5f6-7890-abcd-ef1234567890

┌──────────────────────┬────────────────────────────────────────┐
│                  Key │ Value                                  │
├──────────────────────┼────────────────────────────────────────┤
│                   Id │ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│               Status │ active                                 │
│           Message Id │ d4e5f6a7-b8c9-0123-defg-456789012345   │
└──────────────────────┴────────────────────────────────────────┘
```

### Claude Code CLI Command Breakdown

When the SDK creates the client, it effectively runs:

```bash
# Simplified representation of what happens internally
claude \
  # Working directory
  --cwd /data/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \

  # Model selection
  --model claude-sonnet-4-5 \

  # Tool permissions
  --allowed-tools "Read,Bash" \
  --permission-mode default \

  # SDK MCP Tools (in-process Python)
  --mcp-server kubernetes_readonly:sdk \
  --mcp-server database:sdk \
  --mcp-server monitoring:sdk \

  # User's External MCP Servers
  --mcp-server user-filesystem \
    --command npx \
    --args "-y,@modelcontextprotocol/server-filesystem,/workspace" \

  --mcp-server user-postgres \
    --command npx \
    --args "-y,@modelcontextprotocol/server-postgres,postgresql://..." \

  # Global External MCP Servers
  --mcp-server global-github \
    --command npx \
    --args "-y,@modelcontextprotocol/server-github" \
    --env "GITHUB_TOKEN=..."
```

**Available Tools to Claude:**
- `Read` (SDK built-in)
- `Bash` (SDK built-in)
- `list_pods` (SDK MCP Tool - Python)
- `get_pod_logs` (SDK MCP Tool - Python)
- `describe_pod` (SDK MCP Tool - Python)
- `query_database` (SDK MCP Tool - Python)
- `get_schema` (SDK MCP Tool - Python)
- `get_metrics` (SDK MCP Tool - Python)
- `check_alerts` (SDK MCP Tool - Python)
- All tools from `user-filesystem` MCP server
- All tools from `user-postgres` MCP server
- All tools from `global-github` MCP server

---

## Command: `sessions list`

### CLI Command
```bash
ai-agent sessions list --status active --page 1 --page-size 20
```

### What Happens in the Backend

#### HTTP Request
```http
GET /api/v1/sessions?status=active&page=1&page_size=20 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Database Query
```sql
SELECT
    id, user_id, name, status, message_count,
    tool_call_count, total_cost_usd, created_at
FROM sessions
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
AND status = 'active'
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

#### Claude SDK Integration
**None** - Simple database query, no SDK involved.

---

## Command: `sessions terminate`

### CLI Command
```bash
ai-agent sessions terminate a1b2c3d4-e5f6-7890-abcd-ef1234567890 --yes
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
DELETE /api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890 HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 2: Disconnect SDK Client

**Service:** `SDKIntegratedSessionService.terminate_session()`

```python
# Disconnect Claude SDK client
await client.disconnect()
```

**This closes the Claude Code CLI subprocess:**
- Sends shutdown signal to CLI process
- Waits for graceful termination
- Cleans up stdio connections
- Removes client from manager pool

#### Step 3: Update Database
```sql
UPDATE sessions
SET
    status = 'terminated',
    completed_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
```

#### Step 4: Audit Log
```sql
INSERT INTO audit_logs (
    id, user_id, session_id, action, timestamp
) VALUES (
    uuid_generate_v4(),
    '550e8400-e29b-41d4-a716-446655440000',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'SESSION_TERMINATED',
    CURRENT_TIMESTAMP
);
```

### Expected Output
```
✓ Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 terminated
```

---

## Test Data

### Create Session
```bash
ai-agent sessions create \
  --name "Test Session" \
  --description "Testing CLI" \
  --allowed-tools "Read" \
  --allowed-tools "Bash" \
  --allowed-tools "Grep"
```

### Send Queries
```bash
# Simple file listing
ai-agent sessions query <session-id> "List files in current directory"

# Code analysis
ai-agent sessions query <session-id> "Analyze the main.py file and summarize its functionality"

# Log investigation
ai-agent sessions query <session-id> "Search for ERROR in application.log from the last hour"

# Multi-step task
ai-agent sessions query <session-id> "Find all Python files, count lines of code, and create a summary report"
```

### With MCP Tools
```bash
# Using Kubernetes MCP tools
ai-agent sessions query <session-id> "List all pods in the default namespace"

# Using Database MCP tools
ai-agent sessions query <session-id> "Show me the schema for the users table"

# Using External MCP servers
ai-agent sessions query <session-id> "Search GitHub for examples of FastAPI authentication"
```
