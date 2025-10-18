# Task Automation Commands

Complete guide for task commands with detailed backend flow and Claude Code SDK integration based on actual implementation.

---

## Command: `tasks create`

### CLI Command
```bash
ai-agent tasks create \
  --name "Service Health Check" \
  --description "Check service health" \
  --prompt-template "Check the health status of {{service_name}} and report any issues" \
  --allowed-tools "Bash" \
  --allowed-tools "Read" \
  --is-scheduled \
  --schedule-cron "*/5 * * * *" \
  --schedule-enabled \
  --generate-report \
  --report-format html \
  --tags monitoring \
  --tags automation
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
POST /api/v1/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Service Health Check",
  "description": "Check service health",
  "prompt_template": "Check the health status of {{service_name}} and report any issues",
  "allowed_tools": ["Bash", "Read"],
  "sdk_options": {},
  "is_scheduled": true,
  "schedule_cron": "*/5 * * * *",
  "schedule_enabled": true,
  "generate_report": true,
  "report_format": "html",
  "notification_config": null,
  "tags": ["monitoring", "automation"],
  "metadata": {}
}
```

#### Step 2: API Processing

**Route Handler:** `app/api/v1/tasks.py:create_task()`

**Service:** `app/services/task_service.py:TaskService.create_task()`

1. **User Authentication**
   - JWT validation via dependency
   - Extract user_id from token

2. **Task Entity Creation**
   ```python
   task = Task(
       id=uuid4(),  # Generate UUID
       user_id=user_id,
       name="Service Health Check",
       prompt_template="Check health of {{service_name}}...",
       allowed_tools=["Bash", "Read"],
       sdk_options={},
   )
   ```

3. **Validation**
   - **Schedule Validation** (if `is_scheduled=true`):
     ```python
     # Validates cron expression format
     from croniter import croniter
     croniter(schedule_cron, datetime.now())  # Raises ValueError if invalid
     ```

   - **Report Format Validation** (if `generate_report=true`):
     ```python
     # Validates format is one of: html, pdf, json
     if report_format not in ["html", "pdf", "json"]:
         raise ValidationError("Invalid report format")
     ```

4. **Database Insert**
   ```sql
   INSERT INTO tasks (
       id, user_id, name, description,
       prompt_template, default_variables,
       allowed_tools, disallowed_tools,
       sdk_options, working_directory_path,
       is_scheduled, schedule_cron, schedule_enabled,
       last_executed_at, next_scheduled_at,
       execution_count, success_count, failure_count,
       generate_report, report_format,
       notification_config, tags,
       is_public, is_active, is_deleted,
       created_at, updated_at
   ) VALUES (
       't1a2b3c4-d5e6-7890-abcd-ef1234567890',
       '550e8400-e29b-41d4-a716-446655440000',
       'Service Health Check',
       'Check service health',
       'Check the health status of {{service_name}} and report any issues',
       NULL,
       '["Bash", "Read"]'::jsonb,
       '[]'::jsonb,
       '{}'::jsonb,
       NULL,
       true,
       '*/5 * * * *',
       true,
       NULL,
       NULL,  -- Calculated by scheduler
       0,
       0,
       0,
       true,
       'html',
       NULL,
       '["monitoring", "automation"]'::jsonb,
       false,
       true,
       false,
       CURRENT_TIMESTAMP,
       CURRENT_TIMESTAMP
   );
   ```

5. **Audit Log**
   ```sql
   INSERT INTO audit_logs (
       id, user_id, action, resource_type, resource_id,
       details, timestamp
   ) VALUES (
       uuid_generate_v4(),
       '550e8400-e29b-41d4-a716-446655440000',
       'TASK_CREATED',
       'task',
       't1a2b3c4-d5e6-7890-abcd-ef1234567890',
       '{"name": "Service Health Check", "is_scheduled": true}',
       CURRENT_TIMESTAMP
   );
   ```

#### Step 3: Claude SDK Integration
**None** - Task creation just stores the template. SDK is used during execution.

#### Step 4: API Response
```json
{
  "id": "t1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Service Health Check",
  "description": "Check service health",
  "prompt_template": "Check the health status of {{service_name}} and report any issues",
  "allowed_tools": ["Bash", "Read"],
  "sdk_options": {},
  "is_scheduled": true,
  "schedule_cron": "*/5 * * * *",
  "schedule_enabled": true,
  "last_executed_at": null,
  "next_scheduled_at": null,
  "execution_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "generate_report": true,
  "report_format": "html",
  "notification_config": null,
  "tags": ["monitoring", "automation"],
  "created_at": "2025-10-18T12:00:00",
  "updated_at": "2025-10-18T12:00:00",
  "metadata": {},
  "_links": {
    "self": "/api/v1/tasks/t1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "execute": "/api/v1/tasks/t1a2b3c4-d5e6-7890-abcd-ef1234567890/execute",
    "executions": "/api/v1/tasks/t1a2b3c4-d5e6-7890-abcd-ef1234567890/executions"
  }
}
```

### Expected CLI Output
```
✓ Task created: t1a2b3c4-d5e6-7890-abcd-ef1234567890

┌─────────────────────┬──────────────────────────────────────────┐
│                 Key │ Value                                    │
├─────────────────────┼──────────────────────────────────────────┤
│                  Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890     │
│                Name │ Service Health Check                     │
│         Description │ Check service health                     │
│   Prompt Template   │ Check health of {{service_name}}...      │
│       Is Scheduled  │ true                                     │
│      Schedule Cron  │ */5 * * * *                              │
│    Schedule Enabled │ true                                     │
│    Generate Report  │ true                                     │
│      Report Format  │ html                                     │
│                Tags │ ["monitoring", "automation"]             │
│          Created At │ 2025-10-18T12:00:00                      │
└─────────────────────┴──────────────────────────────────────────┘
```

---

## Command: `tasks execute`

### CLI Command
```bash
ai-agent tasks execute t1a2b3c4-d5e6-7890-abcd-ef1234567890 \
  --variables '{"service_name": "nginx", "threshold": "95"}'
```

### What Happens in the Backend

#### Step 1: HTTP Request
```http
POST /api/v1/tasks/t1a2b3c4-d5e6-7890-abcd-ef1234567890/execute HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "variables": {
    "service_name": "nginx",
    "threshold": "95"
  }
}
```

#### Step 2: Task Execution Flow

**Service:** `TaskService.execute_task()`

This is the COMPLETE flow - task execution creates a session and uses Claude SDK:

##### 2.1: Load Task from Database
```sql
SELECT * FROM tasks
WHERE id = 't1a2b3c4-d5e6-7890-abcd-ef1234567890';
```

Validates:
- Task exists
- Task is active (`is_active = true`)
- Task not deleted (`is_deleted = false`)

##### 2.2: Create Task Execution Record
```sql
INSERT INTO task_executions (
    id, task_id, user_id,
    trigger_type, prompt_variables,
    status, result_data,
    report_id, session_id,
    error_message, duration_ms,
    created_at, started_at, completed_at
) VALUES (
    'exec-1a2b-3c4d-5e6f-7890',
    't1a2b3c4-d5e6-7890-abcd-ef1234567890',
    '550e8400-e29b-41d4-a716-446655440000',
    'manual',
    '{"service_name": "nginx", "threshold": "95"}'::jsonb,
    'pending',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    CURRENT_TIMESTAMP,
    NULL,
    NULL
);
```

##### 2.3: Create Session for Execution

**Important:** Task execution creates a NEW session each time.

```python
# SDKIntegratedSessionService.create_session()
session = await session_service.create_session(
    user_id=task.user_id,
    name=f"Task: Service Health Check (manual)",
    description=f"Automated execution of task 'Service Health Check'",
    sdk_options=task.sdk_options,  # Uses task's SDK config
)
```

```sql
INSERT INTO sessions (
    id, user_id, name, description,
    status, working_directory, allowed_tools,
    sdk_options, is_fork, created_at
) VALUES (
    'sess-2b3c-4d5e-6f7a-8901',
    '550e8400-e29b-41d4-a716-446655440000',
    'Task: Service Health Check (manual)',
    'Automated execution of task ''Service Health Check''',
    'created',
    '/data/sessions/sess-2b3c-4d5e-6f7a-8901',
    '["Bash", "Read"]'::jsonb,
    '{}'::jsonb,
    false,
    CURRENT_TIMESTAMP
);
```

##### 2.4: Update Execution with Session ID
```sql
UPDATE task_executions
SET
    session_id = 'sess-2b3c-4d5e-6f7a-8901',
    status = 'running',
    started_at = CURRENT_TIMESTAMP
WHERE id = 'exec-1a2b-3c4d-5e6f-7890';
```

##### 2.5: Render Prompt Template

**Template Rendering Logic:**

```python
# TaskService._render_prompt_template()
template = "Check the health status of {{service_name}} and report any issues"
variables = {"service_name": "nginx", "threshold": "95"}

# Simple regex-based substitution
import re

def replace_var(match):
    var_name = match.group(1)  # e.g., "service_name"
    return str(variables.get(var_name, match.group(0)))

# Replace all {{variable}} with values
rendered = re.sub(r'\{\{(\w+)\}\}', replace_var, template)

# Result: "Check the health status of nginx and report any issues"
```

**Rendered Prompt:**
```
Check the health status of nginx and report any issues
```

##### 2.6: Send Message Through Session

**This triggers the FULL session query flow from sessions documentation!**

```python
# SDKIntegratedSessionService.send_message()
message = await session_service.send_message(
    session_id='sess-2b3c-4d5e-6f7a-8901',
    message_content='Check the health status of nginx and report any issues',
)
```

This internally:

1. **Setup SDK Client** (first query)
   - Build MCP config (SDK tools + user MCP servers + global MCP servers)
   - Create permission callbacks
   - Create hooks (audit, tracking, cost)
   - Create `ClaudeSDKClient`
   - Spawn Claude Code CLI subprocess:
     ```bash
     claude \
       --cwd /data/sessions/sess-2b3c-4d5e-6f7a-8901 \
       --allowed-tools "Bash,Read" \
       --mcp-server kubernetes_readonly:sdk \
       --mcp-server database:sdk \
       --mcp-server monitoring:sdk \
       --mcp-server user-filesystem:npx:... \
       --mcp-server user-postgres:npx:... \
       --mcp-server global-github:npx:...
     ```

2. **Send Query to Claude**
   ```python
   await client.query("Check the health status of nginx and report any issues")
   ```

3. **Claude Processing**
   - Claude receives message
   - Analyzes request
   - May decide to use tools:
     - `Bash` tool: `systemctl status nginx`
     - `Bash` tool: `curl -s http://localhost/health`
     - `Read` tool: Read nginx error logs
     - `get_metrics` tool (SDK MCP): Get nginx metrics
   - Generates response

4. **Tool Execution Tracking**
   - Each tool use creates a `tool_calls` record
   - Hooks track execution time and results
   - Costs are accumulated

5. **Store Messages**
   ```sql
   -- User message
   INSERT INTO messages (...)
   VALUES ('Check the health status of nginx and report any issues');

   -- Assistant messages
   INSERT INTO messages (...)
   VALUES ('I''ll check the nginx service health...', tool_uses);

   -- Tool results
   INSERT INTO messages (...)
   VALUES (tool_result_content);
   ```

##### 2.7: Update Execution as Completed
```sql
UPDATE task_executions
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP,
    duration_ms = 4523,
    result_message_id = 'd4e5f6a7-b8c9-0123-defg-456789012345'
WHERE id = 'exec-1a2b-3c4d-5e6f-7890';
```

##### 2.8: Generate Report (if requested)

**Service:** `ReportService.generate_from_session()`

If `task.generate_report = true`:

```python
report = await report_service.generate_from_session(
    session_id='sess-2b3c-4d5e-6f7a-8901',
    user_id=user_id,
    title=f"Task Execution Report: Service Health Check",
    format='html',  # From task.report_format
    auto_generated=True,
)
```

**Report Generation Process:**

1. **Query Session Data**
   ```sql
   SELECT * FROM sessions
   WHERE id = 'sess-2b3c-4d5e-6f7a-8901';

   SELECT * FROM messages
   WHERE session_id = 'sess-2b3c-4d5e-6f7a-8901'
   ORDER BY created_at;

   SELECT * FROM tool_calls
   WHERE session_id = 'sess-2b3c-4d5e-6f7a-8901'
   ORDER BY created_at;
   ```

2. **Build Report Content**
   ```python
   report_content = {
       "session_id": session_id,
       "task_name": "Service Health Check",
       "execution_id": execution_id,
       "messages": [...],
       "tool_calls": [...],
       "summary": {
           "total_messages": 5,
           "total_tool_calls": 3,
           "duration_ms": 4523,
           "cost_usd": 0.0025
       }
   }
   ```

3. **Generate HTML/PDF/JSON**
   - **HTML:** Uses Jinja2 template with report content
   - **PDF:** Uses WeasyPrint to convert HTML to PDF
   - **JSON:** Direct JSON serialization

4. **Store Report**
   ```sql
   INSERT INTO reports (
       id, session_id, title, description,
       report_type, content, file_format,
       file_size_bytes, storage_path, created_at
   ) VALUES (
       'rep-3c4d-5e6f-7a8b-9012',
       'sess-2b3c-4d5e-6f7a-8901',
       'Task Execution Report: Service Health Check',
       'Automated report',
       'auto_generated',
       '<report_content>'::jsonb,
       'html',
       45678,
       '/data/reports/rep-3c4d-5e6f-7a8b-9012.html',
       CURRENT_TIMESTAMP
   );
   ```

5. **Update Execution with Report ID**
   ```sql
   UPDATE task_executions
   SET report_id = 'rep-3c4d-5e6f-7a8b-9012'
   WHERE id = 'exec-1a2b-3c4d-5e6f-7890';
   ```

##### 2.9: Update Task Statistics
```sql
UPDATE tasks
SET
    execution_count = execution_count + 1,
    success_count = success_count + 1,
    last_executed_at = CURRENT_TIMESTAMP
WHERE id = 't1a2b3c4-d5e6-7890-abcd-ef1234567890';
```

##### 2.10: Audit Log
```sql
INSERT INTO audit_logs (
    id, user_id, action, resource_type,
    resource_id, details, timestamp
) VALUES (
    uuid_generate_v4(),
    '550e8400-e29b-41d4-a716-446655440000',
    'TASK_EXECUTED',
    'task_execution',
    'exec-1a2b-3c4d-5e6f-7890',
    '{"task_id": "t1a2b3c4...", "trigger_type": "manual", "status": "completed"}',
    CURRENT_TIMESTAMP
);
```

#### Step 3: API Response
```json
{
  "id": "exec-1a2b-3c4d-5e6f-7890",
  "task_id": "t1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "session_id": "sess-2b3c-4d5e-6f7a-8901",
  "status": "running",
  "trigger_type": "manual",
  "prompt_variables": {
    "service_name": "nginx",
    "threshold": "95"
  },
  "result_data": null,
  "report_id": null,
  "error_message": null,
  "duration_ms": null,
  "created_at": "2025-10-18T12:15:00",
  "started_at": "2025-10-18T12:15:01",
  "completed_at": null,
  "_links": {
    "self": "/api/v1/task-executions/exec-1a2b-3c4d-5e6f-7890",
    "task": "/api/v1/tasks/t1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "session": "/api/v1/sessions/sess-2b3c-4d5e-6f7a-8901"
  }
}
```

**Note:** Status is `running` because execution happens asynchronously.

### Complete Task Execution Flow Diagram

```
CLI: tasks execute
    │
    ▼
POST /api/v1/tasks/{id}/execute
    │
    ├─► Load Task (DB)
    ├─► Create TaskExecution record (DB) ──► Status: pending
    │
    ├─► Create Session for execution
    │   └─► INSERT INTO sessions
    │
    ├─► Update TaskExecution ──► Status: running, session_id
    │
    ├─► Render Prompt Template
    │   │   Template: "Check {{service_name}} health"
    │   │   Variables: {"service_name": "nginx"}
    │   └─► Result: "Check nginx health"
    │
    ├─► Send Message to Session ════════════════════════╗
    │                                                    ║
    │   ┌────────────────────────────────────────────────╝
    │   │
    │   ├─► Setup SDK Client (first query only)
    │   │   ├─► Build MCP Config
    │   │   │   ├─► SDK MCP Tools (Python in-process)
    │   │   │   ├─► User MCP Servers (DB query)
    │   │   │   └─► Global MCP Servers (DB query)
    │   │   ├─► Create Permission Callbacks
    │   │   ├─► Create Hook Handlers
    │   │   └─► Spawn Claude Code CLI subprocess
    │   │
    │   ├─► Send Query to Claude via SDK
    │   │       │
    │   │       ▼
    │   │   Claude Code CLI Process
    │   │       ├─► Claude API call
    │   │       ├─► Tool Use: Bash "systemctl status nginx"
    │   │       ├─► Tool Use: get_metrics (SDK MCP tool)
    │   │       └─► Return response stream
    │   │
    │   ├─► Process Response Stream
    │   │   ├─► Store user message (DB)
    │   │   ├─► Store assistant messages (DB)
    │   │   ├─► Track tool calls (DB)
    │   │   └─► Update session metrics (DB)
    │   │
    │   └─► Return message
    │
    ├─► Update TaskExecution ──► Status: completed
    │
    ├─► Generate Report? ──► YES
    │   ├─► Query session messages & tool calls
    │   ├─► Build report content
    │   ├─► Generate HTML/PDF/JSON file
    │   ├─► Store report (DB + filesystem)
    │   └─► Update TaskExecution.report_id
    │
    ├─► Update Task Statistics
    │   └─► execution_count++, success_count++
    │
    ├─► Audit Log
    │
    └─► Return Response to CLI
```

### Expected CLI Output
```
✓ Task execution started: exec-1a2b-3c4d-5e6f-7890

┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ exec-1a2b-3c4d-5e6f-7890               │
│          Task Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890   │
│       Session Id │ sess-2b3c-4d5e-6f7a-8901               │
│           Status │ running                                │
│     Trigger Type │ manual                                 │
│        Variables │ {"service_name": "nginx"}              │
│       Created At │ 2025-10-18T12:15:00                    │
└──────────────────┴────────────────────────────────────────┘
```

### Claude Code CLI Command (Internal)

When task execution triggers SDK client creation:

```bash
claude \
  --cwd /data/sessions/sess-2b3c-4d5e-6f7a-8901 \
  --model claude-sonnet-4-5 \
  --allowed-tools "Bash,Read" \
  --permission-mode default \
  --mcp-server kubernetes_readonly:sdk \
  --mcp-server database:sdk \
  --mcp-server monitoring:sdk \
  --mcp-server user-filesystem:npx:-y:@modelcontextprotocol/server-filesystem:/workspace \
  --mcp-server user-postgres:npx:-y:@modelcontextprotocol/server-postgres:postgresql://...
```

Then sends the rendered prompt:
```
USER: Check the health status of nginx and report any issues
```

Claude can use any of:
- `Bash` tool (SDK built-in)
- `Read` tool (SDK built-in)
- `get_metrics` (SDK MCP tool - Python function)
- `list_pods` (SDK MCP tool - Python function)
- `query_database` (SDK MCP tool - Python function)
- All tools from external MCP servers

---

## Command: `tasks execution-status`

### CLI Command
```bash
ai-agent tasks execution-status exec-1a2b-3c4d-5e6f-7890
```

### What Happens

#### HTTP Request
```http
GET /api/v1/tasks/executions/exec-1a2b-3c4d-5e6f-7890 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Database Query
```sql
SELECT * FROM task_executions
WHERE id = 'exec-1a2b-3c4d-5e6f-7890';
```

#### Claude SDK Integration
**None** - Just querying stored execution data.

### Expected Output
```
┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ exec-1a2b-3c4d-5e6f-7890               │
│          Task Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890   │
│       Session Id │ sess-2b3c-4d5e-6f7a-8901               │
│           Status │ completed                              │
│     Trigger Type │ manual                                 │
│        Variables │ {"service_name": "nginx"}              │
│      Result Data │ {"status": "healthy", "uptime": 99.9}  │
│        Report Id │ rep-3c4d-5e6f-7a8b-9012                │
│      Duration Ms │ 4523                                   │
│       Created At │ 2025-10-18T12:15:00                    │
│       Started At │ 2025-10-18T12:15:01                    │
│     Completed At │ 2025-10-18T12:15:05                    │
└──────────────────┴────────────────────────────────────────┘
```

---

## Test Data

### Create and Execute Task
```bash
# 1. Create task
TASK_ID=$(ai-agent tasks create \
  --name "Health Check" \
  --prompt-template "Check health of {{service}}" \
  --generate-report \
  --format json | jq -r '.id')

# 2. Execute task
EXEC_ID=$(ai-agent tasks execute $TASK_ID \
  --variables '{"service": "nginx"}' \
  --format json | jq -r '.id')

# 3. Wait for completion
sleep 5

# 4. Check status
ai-agent tasks execution-status $EXEC_ID

# 5. Download report if generated
REPORT_ID=$(ai-agent tasks execution-status $EXEC_ID --format json | jq -r '.report_id')
if [ "$REPORT_ID" != "null" ]; then
  ai-agent reports download $REPORT_ID --format html --output report.html
fi
```
