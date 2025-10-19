# Task Management APIs - Complete Analysis

**Status:** Ready to Test ✅  
**Date:** October 19, 2025  
**Base URL:** `http://localhost:8000/api/v1/tasks`

---

## Executive Summary

The Task Management system is **fully self-contained** and does NOT require creation of separate lookup/child entities first. Tasks can be created and used immediately with minimal configuration.

### Key Points:
- ✅ **No external dependencies required** - Tasks don't depend on pre-existing entities
- ✅ **Automatic session creation** - Sessions are created on-the-fly during task execution
- ✅ **Optional features** - Scheduling and reporting are optional
- ✅ **Flexible SDK configuration** - Tasks inherit SDK options or provide their own

---

## Architecture Overview

```
Task Management System
│
├── Task Definition (Template)
│   ├── Name & Description
│   ├── Prompt Template with {{variables}}
│   ├── Allowed/Disallowed Tools
│   ├── SDK Options (model, turns, etc.)
│   ├── Scheduling Config (optional)
│   └── Report Config (optional)
│
├── Task Execution (Runtime)
│   ├── Created on-demand when executed
│   ├── Creates temporary Session automatically
│   ├── Renders prompt with variables
│   ├── Executes via Claude SDK
│   ├── Optionally generates Report
│   └── Tracks execution history
│
└── Supporting Models
    ├── TaskExecutionModel - Stores execution records
    ├── SessionModel - Created per execution
    └── ReportModel - Optional, created if enabled
```

---

## Database Schema & Relationships

### Tasks Table

```
┌─ tasks ─────────────────────────────────────────┐
│ id (UUID)                      Primary Key      │
│ user_id (UUID)                 FK → users       │
│ name (String)                  Required         │
│ description (Text)             Optional         │
│ prompt_template (Text)         Required         │
│ allowed_tools (Array)          Optional         │
│ disallowed_tools (Array)       Optional         │
│ sdk_options (JSONB)            Optional         │
│ working_directory_path (String) Optional        │
│ is_scheduled (Boolean)         Default: False   │
│ schedule_cron (String)         Conditional      │
│ schedule_enabled (Boolean)     Default: False   │
│ generate_report (Boolean)      Default: False   │
│ report_format (String)         Enum: json/html  │
│ notification_config (JSONB)    Optional         │
│ tags (Array)                   Optional         │
│ is_public (Boolean)            Default: False   │
│ is_active (Boolean)            Default: True    │
│ is_deleted (Boolean)           Soft Delete      │
│ created_at (DateTime)          Auto-set         │
│ updated_at (DateTime)          Auto-update      │
│ deleted_at (DateTime)          Soft Delete      │
└─────────────────────────────────────────────────┘
```

### Task Executions Table

```
┌─ task_executions ─────────────────────────────┐
│ id (UUID)                  Primary Key         │
│ task_id (UUID)             FK → tasks (CASCADE)│
│ session_id (UUID)          FK → sessions       │
│ report_id (UUID)           FK → reports        │
│ trigger_type (String)      manual/scheduled    │
│ trigger_metadata (JSONB)   Optional            │
│ prompt_variables (JSONB)   Substituted vars    │
│ status (String)            pending/running...  │
│ error_message (String)     If failed           │
│ result_data (JSONB)        Execution results   │
│ total_messages (Integer)   Count               │
│ total_tool_calls (Integer) Count               │
│ duration_seconds (Integer) Execution time      │
│ created_at (DateTime)      Auto-set            │
│ started_at (DateTime)      When started        │
│ completed_at (DateTime)    When completed      │
└───────────────────────────────────────────────┘
```

---

## Dependencies & Requirements

### What's Required to Create a Task ✅

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | String | ✅ Yes | 1-255 chars, must be unique per user |
| `prompt_template` | String | ✅ Yes | Can contain `{{variable_name}}` placeholders |
| `allowed_tools` | Array | ✅ Yes | List of tool names (e.g., `["bash", "read_file"]`) |
| `sdk_options` | Object | ✅ Yes | Model, max_turns, permission_mode, etc. |
| `description` | String | ❌ No | Optional description |
| `is_scheduled` | Boolean | ❌ No | Default: false |
| `schedule_cron` | String | ❌ No | Required ONLY if `is_scheduled=true` |
| `generate_report` | Boolean | ❌ No | Default: false |
| `report_format` | String | ❌ No | Required ONLY if `generate_report=true` |
| `tags` | Array | ❌ No | Optional metadata |

### What's NOT Required ❌

- **Session** - Created automatically during execution
- **Report** - Only created if `generate_report=true`
- **MCP Servers** - Optional in SDK options
- **Working Directory** - Optional, defaults to system temp
- **Notifications** - Optional feature
- **Public Visibility** - Defaults to private

---

## Complete API Workflow

### 1️⃣ Create Task Definition

```
Request: POST /api/v1/tasks
├─ Input: Name, Prompt Template, Tools, SDK Options
├─ Processing:
│  ├─ Validate inputs (Pydantic)
│  ├─ Create Task entity
│  ├─ Validate schedule (if scheduled)
│  ├─ Validate report format (if reports enabled)
│  ├─ Persist to database
│  └─ Log to audit trail
└─ Response: TaskResponse (201 Created)
```

### 2️⃣ List/Search Tasks

```
Request: GET /api/v1/tasks?tags=&is_scheduled=&page=1
├─ Query filters: tags, is_scheduled, pagination
├─ Processing:
│  ├─ Get user's tasks from database
│  ├─ Apply filters (tags, scheduled status)
│  ├─ Apply pagination
│  └─ Build response with HATEOAS links
└─ Response: PaginatedResponse[TaskResponse]
```

### 3️⃣ Get Task Details

```
Request: GET /api/v1/tasks/{task_id}
├─ Processing:
│  ├─ Fetch from database
│  ├─ Verify user ownership
│  └─ Return full details
└─ Response: TaskResponse (200 OK)
```

### 4️⃣ Update Task

```
Request: PATCH /api/v1/tasks/{task_id}
├─ Input: Partial updates (name, schedule, etc.)
├─ Processing:
│  ├─ Fetch existing task
│  ├─ Verify ownership
│  ├─ Validate updates
│  ├─ Re-validate schedule (if changed)
│  ├─ Re-validate report format (if changed)
│  ├─ Persist changes
│  └─ Log audit trail
└─ Response: TaskResponse (200 OK)
```

### 5️⃣ Execute Task

```
Request: POST /api/v1/tasks/{task_id}/execute
├─ Input: Optional {{variables}} for template
├─ Processing:
│  ├─ Fetch task from database
│  ├─ Verify user ownership
│  ├─ Create TaskExecution record (PENDING)
│  │
│  ├─ CREATE SESSION (automatic!)
│  │  ├─ Use task's SDK options
│  │  ├─ Create working directory
│  │  └─ Initialize Claude SDK client
│  │
│  ├─ RENDER PROMPT
│  │  └─ Substitute {{variables}} in template
│  │
│  ├─ SEND MESSAGE
│  │  ├─ Send to Claude SDK
│  │  ├─ Process tool calls
│  │  └─ Get response message
│  │
│  ├─ UPDATE EXECUTION (COMPLETED)
│  │  ├─ Store result message ID
│  │  ├─ Record duration
│  │  └─ Count messages/tool calls
│  │
│  ├─ GENERATE REPORT (if enabled)
│  │  ├─ Collect session data
│  │  ├─ Generate HTML/PDF/JSON
│  │  └─ Link to execution
│  │
│  └─ LOG AUDIT TRAIL
│     └─ Record task execution
│
└─ Response: TaskExecutionResponse (202 Accepted)
```

### 6️⃣ List Task Executions

```
Request: GET /api/v1/tasks/{task_id}/executions?page=1
├─ Processing:
│  ├─ Verify task ownership
│  ├─ Get executions from database
│  ├─ Apply pagination
│  └─ Build response with links
└─ Response: PaginatedResponse[TaskExecutionResponse]
```

### 7️⃣ Get Execution Details

```
Request: GET /api/v1/task-executions/{execution_id}
├─ Processing:
│  ├─ Fetch execution
│  ├─ Verify user ownership (via task)
│  └─ Return details with session/report links
└─ Response: TaskExecutionResponse (200 OK)
```

### 8️⃣ Delete Task

```
Request: DELETE /api/v1/tasks/{task_id}
├─ Processing:
│  ├─ Fetch task
│  ├─ Verify ownership
│  ├─ Soft delete (set deleted_at)
│  ├─ Cascade: Link executions but don't delete
│  └─ Log audit trail
└─ Response: 204 No Content
```

---

## What Gets Created Automatically

### On Task Execution (`POST /tasks/{id}/execute`)

1. **TaskExecution Record**
   - Created immediately in PENDING status
   - Tracks: trigger_type, variables, start/end times
   - Linked to Task and Session

2. **Session (AUTO-CREATED)**
   - New session created per execution
   - Named: `"Task: {task_name} ({trigger_type})"`
   - Uses task's SDK options
   - Gets own working directory
   - Auto-cleaned on execution end

3. **Report (Optional)**
   - Generated if `generate_report=true`
   - Format: HTML/PDF/JSON (task.report_format)
   - Created from session data
   - Linked to execution

---

## Data Flow Example

### Scenario: Execute Task with Variables

```
1. API Request:
   POST /api/v1/tasks/abc123/execute
   {
     "variables": {
       "environment": "production",
       "service": "api-gateway"
     }
   }

2. Task Definition (from database):
   {
     "name": "Check Deployment Status",
     "prompt_template": "Check {{environment}} deployment for {{service}}",
     "allowed_tools": ["ssh", "curl", "bash"],
     "sdk_options": {
       "model": "claude-3-5-sonnet-20241022",
       "max_turns": 10
     },
     "generate_report": true
   }

3. Backend Processing:
   ✓ Create TaskExecution (PENDING)
   ✓ Create Session with SDK options
   ✓ Render prompt:
     "Check production deployment for api-gateway"
   ✓ Send to Claude SDK
   ✓ Process tool calls (SSH, curl, bash)
   ✓ Get response
   ✓ Update TaskExecution (COMPLETED)
   ✓ Generate HTML report
   ✓ Return execution ID

4. Response:
   {
     "id": "exec-456",
     "task_id": "abc123",
     "session_id": "sess-789",
     "status": "completed",
     "trigger_type": "manual",
     "started_at": "2025-10-19T12:00:00Z",
     "completed_at": "2025-10-19T12:05:30Z",
     "report_id": "rpt-012",
     "_links": {
       "self": "/api/v1/task-executions/exec-456",
       "task": "/api/v1/tasks/abc123",
       "session": "/api/v1/sessions/sess-789",
       "report": "/api/v1/reports/rpt-012"
     }
   }
```

---

## Entity Creation Checklist

### ✅ To Create a Task - ONLY Need:

- [x] User ID (automatically from JWT token)
- [x] Task name
- [x] Prompt template string
- [x] List of allowed tools
- [x] SDK options (model, max_turns, etc.)

### ❌ Do NOT Need to Create First:

- ❌ Sessions - Created automatically on execution
- ❌ Reports - Created automatically if enabled
- ❌ MCP Servers - Optional in SDK options
- ❌ Working directories - Created per session
- ❌ Audit logs - Created automatically
- ❌ Execution records - Created per execution

---

## Important Validations

### When Creating Task

1. **Schedule Validation** (if `is_scheduled=true`)
   ```python
   - Requires: schedule_cron must be provided
   - Validates: Cron expression format using croniter
   - Raises: ValidationError if invalid
   ```

2. **Report Format Validation** (if `generate_report=true`)
   ```python
   - Allowed values: "html", "pdf", "json", "markdown"
   - Raises: ValidationError if invalid format
   ```

### When Executing Task

1. **Task Must Be Active**
   ```python
   - is_active must be True
   - Raises: ValidationError if inactive
   ```

2. **Variable Substitution**
   ```python
   - Uses regex: r'\{(\w+)\}'
   - Replaces: {{variable_name}} → value
   - Missing vars: Leave as-is
   ```

---

## HATEOAS Links for Task Operations

### Task Response Links

```json
"_links": {
  "self": "/api/v1/tasks/{task_id}",
  "execute": "/api/v1/tasks/{task_id}/execute",
  "executions": "/api/v1/tasks/{task_id}/executions"
}
```

### Execution Response Links

```json
"_links": {
  "self": "/api/v1/task-executions/{execution_id}",
  "task": "/api/v1/tasks/{task_id}",
  "session": "/api/v1/sessions/{session_id}",
  "report": "/api/v1/reports/{report_id}"
}
```

---

## Recommended Testing Sequence

### Phase 1: Basic CRUD
1. ✅ Create task (no scheduling, no reports)
2. ✅ Get task by ID
3. ✅ List tasks
4. ✅ Update task
5. ✅ Delete task (soft delete)

### Phase 2: Advanced Features
6. ✅ Create scheduled task (with cron)
7. ✅ Create task with report generation
8. ✅ Execute task (manual trigger)
9. ✅ Get execution details
10. ✅ List executions

### Phase 3: Edge Cases
11. ⚠️ Execute with variables
12. ⚠️ Invalid schedule (bad cron)
13. ⚠️ Invalid report format
14. ⚠️ Permission denied (wrong user)
15. ⚠️ Task not found (404)

---

## Known Quirks & Issues

### Issue #1: HATEOAS Links Using `_links` (Template API Issue)
**File:** `app/api/v1/tasks.py`  
**Status:** ⚠️ Same as Template API  
**Lines:** 70, 106, 108, 148, 150, 199, 201, 279, 283, 330, 336, 378, 382, 384

**Problem:**
```python
response._links = Links(...)  # ❌ Wrong approach
```

**Should be:**
```python
response.links = Links(...)  # ✅ Correct approach
```

**Impact:** HATEOAS links will be `null` in responses

---

## Recommended Approach to Fix

Since Task API has the same `_links` issue as Template API, we should:

1. ✅ Test Task APIs first (with null links - expected)
2. ✅ Document all findings
3. ✅ Fix all `_links` issues together across all APIs
4. ✅ Re-test after fixes

---

## Summary: Ready to Test? ✅ YES

**Task Management APIs are production-ready for testing:**

✅ No external dependencies  
✅ Auto-creates sessions  
✅ Auto-creates reports (if enabled)  
✅ Proper error handling  
✅ Comprehensive validation  
✅ Audit logging  
✅ Authorization checks  
✅ Soft deletes  
⚠️ Minor HATEOAS link issue (known, same as Templates)

---

**Next Steps:**
1. Proceed with Task API testing
2. Document all curl examples
3. Fix HATEOAS link issue across all APIs
4. Re-test after fixes

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Status:** Analysis Complete ✅
