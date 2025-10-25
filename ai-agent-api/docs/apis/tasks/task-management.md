# Task Management APIs

**Base URL:** `http://localhost:8000/api/v1/tasks`
**Authentication:** Required (Bearer Token)

---

## Table of Contents

1. [Create Task](#1-create-task)
2. [Get Task (Detailed)](#2-get-task-detailed)
3. [List Tasks](#3-list-tasks)
4. [Update Task](#4-update-task)
5. [Delete Task](#5-delete-task)
6. [Execute Task](#6-execute-task)
7. [List Task Executions](#7-list-task-executions)
8. [Get Task Execution](#8-get-task-execution)
9. [Retry Task Execution](#9-retry-task-execution)
10. [Get Execution Tool Calls](#10-get-execution-tool-calls) ⭐ NEW
11. [Cancel Execution](#11-cancel-execution) ⭐ NEW
12. [Get Execution Files](#12-get-execution-files) ⭐ NEW
13. [Download Execution File](#13-download-execution-file) ⭐ NEW
14. [Archive Execution Directory](#14-archive-execution-directory) ⭐ NEW
15. [Download Archive](#15-download-archive) ⭐ NEW

---

## 1. Create Task

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/tasks` |
| **Status Code** | 201 Created |
| **Authentication** | Required |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily K8s Health Check",
    "description": "Check Kubernetes cluster health",
    "prompt_template": "Check the health of {{cluster}} cluster. Run kubectl get nodes, kubectl get pods --all-namespaces, and kubectl top nodes. Provide a summary report.",
    "allowed_tools": [
      "Bash(kubectl get:*)",
      "Bash(kubectl describe:*)",
      "Bash(kubectl top:*)",
      "Read"
    ],
    "sdk_options": {
      "model": "claude-sonnet-4-5",
      "max_turns": 10
    },
    "is_scheduled": true,
    "schedule_cron": "0 9 * * *",
    "generate_report": true,
    "report_format": "html",
    "tags": ["monitoring", "kubernetes"]
  }'
```

### Request Body

```json
{
  "name": "Daily K8s Health Check",
  "description": "Check Kubernetes cluster health",
  "prompt_template": "Check the health of {{cluster}} cluster",
  "allowed_tools": [
    "Bash(kubectl get:*)",
    "Bash(kubectl describe:*)",
    "Bash(kubectl top:*)"
  ],
  "disallowed_tools": [
    "Bash(kubectl delete:*)",
    "Bash(kubectl apply:*)"
  ],
  "sdk_options": {
    "model": "claude-sonnet-4-5",
    "max_turns": 10
  },
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "schedule_enabled": false,
  "generate_report": true,
  "report_format": "html",
  "tags": ["monitoring", "kubernetes"]
}
```

### Response Example

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Daily K8s Health Check",
  "description": "Check Kubernetes cluster health",
  "prompt_template": "Check the health of {{cluster}} cluster",
  "allowed_tools": [
    "Bash(kubectl get:*)",
    "Bash(kubectl describe:*)",
    "Bash(kubectl top:*)"
  ],
  "disallowed_tools": [
    "Bash(kubectl delete:*)",
    "Bash(kubectl apply:*)"
  ],
  "sdk_options": {
    "model": "claude-sonnet-4-5",
    "max_turns": 10
  },
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "schedule_enabled": false,
  "generate_report": true,
  "report_format": "html",
  "tags": ["monitoring", "kubernetes"],
  "is_active": true,
  "created_at": "2025-10-25T10:00:00Z",
  "updated_at": "2025-10-25T10:00:00Z",
  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute",
    "executions": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `create_task()` in `app/api/v1/tasks.py:51` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency extracts authenticated user |
| 3 | Validation Layer | Validate Task Definition | `_validate_task_definition()` in `app/services/task_service.py:1452` |
| 4 | Prompt Validation | Check Jinja2 Syntax | Validates prompt template is valid Jinja2 with no syntax errors |
| 5 | Tools Validation | Check Tool Patterns | Validates `allowed_tools` and `disallowed_tools` match valid patterns |
| 6 | SDK Options Validation | Validate Model & Settings | Checks model name, max_turns range, removes forbidden `permission_mode` |
| 7 | Schedule Validation | Validate Cron | If `is_scheduled=true`, validates cron expression |
| 8 | Report Validation | Validate Format | If `generate_report=true`, validates format (html/pdf/json/markdown) |
| 9 | Task Entity Creation | Create Domain Entity | Create `Task` entity with validated data via `create_task()` in `app/services/task_service.py:36` |
| 10 | Database Persistence | Save to Database | Insert into `tasks` table |
| 11 | Audit Logging | Log Creation | Create audit log entry for `task.created` action |
| 12 | Response Building | Build HATEOAS Links | Add links for execute, executions, self |
| 13 | Return | Send Response | FastAPI returns 201 Created with task data |

### Validation Rules

| Field | Rule | Details |
|-------|------|---------|
| `name` | Required | 1-255 characters |
| `prompt_template` | Required, Jinja2 valid | Must be valid Jinja2 syntax, cannot be empty |
| `allowed_tools` | Required, Valid patterns | Must contain at least one valid tool pattern |
| `sdk_options.model` | Valid model name | Must be one of: `claude-sonnet-4-5`, `claude-3-5-sonnet-20241022`, etc. |
| `sdk_options.max_turns` | 1-50 | Integer between 1 and 50 |
| `sdk_options.permission_mode` | **System-controlled** | User-provided value is removed (always `acceptEdits` for tasks) |
| `schedule_cron` | Valid cron | Required if `is_scheduled=true`, must be valid cron expression |
| `report_format` | Valid format | Required if `generate_report=true`, must be `html`/`pdf`/`json`/`markdown` |

### Tool Pattern Examples

| Pattern | Example | Meaning |
|---------|---------|---------|
| Tool name | `"Bash"` | Allow ALL bash commands |
| Command prefix | `"Bash(kubectl:*)"` | Allow all kubectl commands |
| Specific command | `"Bash(kubectl get:*)"` | Allow only `kubectl get` |
| Read-only tools | `"Read"`, `"Glob"`, `"Grep"` | File read operations |
| MCP tools | `"mcp__kubernetes__list_pods"` | Specific MCP tool |
| Wildcard | `"*"` | Allow all tools |

---

## 2. Get Task (Detailed)

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/{task_id}` |
| **Query Parameters** | `detailed` (boolean, default: true), `include_executions`, `include_working_dirs`, `include_audit`, `include_reports` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
# Get detailed task information (default)
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get basic task information only
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000?detailed=false" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get task with selective details
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000?include_audit=false&include_reports=false" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example (Detailed)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Daily K8s Health Check",
  "description": "Check Kubernetes cluster health",
  "prompt_template": "Check the health of {{cluster}} cluster",
  "allowed_tools": [
    "Bash(kubectl get:*)",
    "Bash(kubectl describe:*)"
  ],
  "disallowed_tools": ["Bash(kubectl delete:*)"],
  "sdk_options": {
    "model": "claude-sonnet-4-5",
    "max_turns": 10
  },
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "generate_report": true,
  "report_format": "html",
  "tags": ["monitoring", "kubernetes"],
  "created_at": "2025-10-25T10:00:00Z",
  "updated_at": "2025-10-25T10:00:00Z",

  "execution_summary": {
    "total_executions": 45,
    "successful": 42,
    "failed": 3,
    "cancelled": 0,
    "avg_duration_seconds": 18.5,
    "success_rate": 0.93,
    "last_execution": {
      "id": "exec-123",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "trigger_type": "manual",
      "created_at": "2025-10-25T09:00:00Z",
      "completed_at": "2025-10-25T09:00:15Z",
      "duration_ms": 15000
    }
  },

  "recent_executions": [
    {
      "id": "exec-123",
      "status": "completed",
      "session_id": "sess-789",
      "trigger_type": "manual",
      "duration_ms": 15000,
      "created_at": "2025-10-25T09:00:00Z",
      "_links": {
        "self": "/api/v1/task-executions/exec-123",
        "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
      }
    }
  ],

  "working_directories": {
    "active": [
      {
        "execution_id": "exec-124",
        "session_id": "sess-790",
        "path": "/workspace/.../active/sess-790/",
        "size_bytes": 1024000,
        "created_at": "2025-10-25T10:00:00Z",
        "is_archived": false
      }
    ],
    "archived": [
      {
        "execution_id": "exec-120",
        "session_id": "sess-785",
        "path": "/workspace/.../active/sess-785/",
        "size_bytes": 512000,
        "created_at": "2025-10-20T15:00:00Z",
        "is_archived": true,
        "archive_id": "arch-456"
      }
    ]
  },

  "mcp_tools": [
    {
      "server_name": "kubernetes_readonly",
      "tools": ["list_pods", "get_deployments", "get_namespaces"],
      "enabled": true,
      "config": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-kubernetes"]
      }
    }
  ],

  "permission_policies": {
    "allowed_tools": ["Bash(kubectl get:*)", "Bash(kubectl describe:*)"],
    "disallowed_tools": ["Bash(kubectl delete:*)"]
  },

  "audit_summary": {
    "total_audit_logs": 90,
    "recent_actions": [
      {
        "action_type": "task.executed",
        "status": "success",
        "created_at": "2025-10-25T09:00:15Z",
        "details": {"execution_id": "exec-123"}
      }
    ],
    "_links": {
      "audit_logs": "/api/v1/audit-logs?resource_type=task&resource_id=550e8400-e29b-41d4-a716-446655440000"
    }
  },

  "reports_summary": {
    "total": 42,
    "recent": [
      {
        "id": "report-101",
        "title": "Task Execution Report: Daily K8s Health Check",
        "format": "html",
        "created_at": "2025-10-25T09:00:16Z",
        "file_path": "/workspace/.../reports/report-101.html"
      }
    ],
    "_links": {
      "reports": "/api/v1/reports?task_id=550e8400-e29b-41d4-a716-446655440000"
    }
  },

  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute",
    "executions": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions",
    "audit_logs": "/api/v1/audit-logs?resource_type=task&resource_id=550e8400-e29b-41d4-a716-446655440000",
    "reports": "/api/v1/reports?task_id=550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_task()` in `app/api/v1/tasks.py:97` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency validates user |
| 3 | Task Service | Get Task Details | `get_task_with_details()` in `app/services/task_service.py:1142` |
| 4 | Authorization | Check Ownership | Verify task.user_id matches current user OR current user is admin |
| 5 | Base Task Query | Fetch Task | Query `tasks` table by ID |
| 6 | Execution Stats Query | Calculate Statistics | Count executions by status, calculate avg duration, success rate |
| 7 | Recent Executions Query | Fetch Last 5 | Query `task_executions` ordered by created_at DESC LIMIT 5 |
| 8 | Working Directories Query | Fetch Directories | Join `task_executions` with `sessions` to get working directory paths |
| 9 | Directory Size Calculation | Calculate Sizes | Walk directory tree to calculate total size for each directory |
| 10 | MCP Tools Extraction | Parse SDK Options | Extract MCP server configs from `task.sdk_options.mcp_servers` |
| 11 | Audit Summary Query | Fetch Audit Logs | Count and query recent audit logs for this task |
| 12 | Reports Summary Query | Fetch Reports | Count and query recent reports for this task's executions |
| 13 | Response Building | Aggregate Data | Build comprehensive response with all child objects |
| 14 | HATEOAS Links | Build Links | Add links to all related resources |
| 15 | Return | Send Response | FastAPI returns 200 with detailed task data |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `detailed` | boolean | `true` | Include aggregated child data |
| `include_executions` | boolean | `true` | Include execution summary and recent executions |
| `include_working_dirs` | boolean | `true` | Include working directory information |
| `include_audit` | boolean | `true` | Include audit trail summary |
| `include_reports` | boolean | `true` | Include reports summary |

---

## 3. List Tasks

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks` |
| **Query Parameters** | `tags` (array), `is_scheduled` (boolean), `page` (int), `page_size` (int) |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
# List all tasks
curl -X GET http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Filter by scheduled tasks
curl -X GET "http://localhost:8000/api/v1/tasks?is_scheduled=true" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Filter by tags
curl -X GET "http://localhost:8000/api/v1/tasks?tags=monitoring&tags=kubernetes" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Pagination
curl -X GET "http://localhost:8000/api/v1/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Daily K8s Health Check",
      "description": "Check Kubernetes cluster health",
      "is_scheduled": true,
      "schedule_cron": "0 9 * * *",
      "tags": ["monitoring", "kubernetes"],
      "is_active": true,
      "created_at": "2025-10-25T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `list_tasks()` in `app/api/v1/tasks.py:340` |
| 2 | Authentication | Validate Token | `get_current_active_user` validates user |
| 3 | Query Building | Build Filters | Apply `is_scheduled`, `tags` filters |
| 4 | Repository Query | Fetch Tasks | `TaskRepository.get_by_user()` with filters |
| 5 | Pagination | Apply Pagination | Skip and limit based on page/page_size |
| 6 | Response Mapping | Map to Response | Convert task models to TaskResponse |
| 7 | Return | Send Response | FastAPI returns 200 with paginated list |

---

## 4. Update Task

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | PATCH |
| **Path** | `/tasks/{task_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X PATCH http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Task Name",
    "description": "New description",
    "is_scheduled": false,
    "schedule_enabled": true
  }'
```

### Request Body (All Fields Optional)

```json
{
  "name": "Updated Task Name",
  "description": "New description",
  "prompt_template": "New template with {{variables}}",
  "allowed_tools": ["Bash", "Read"],
  "is_scheduled": false,
  "schedule_cron": "0 10 * * *",
  "schedule_enabled": true
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `update_task()` in `app/api/v1/tasks.py:387` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 4 | Validation | Validate Changes | Validate updated fields (cron, report format, etc.) via `update_task()` in `app/services/task_service.py:989` |
| 5 | Repository Update | Update Task | `TaskRepository.update()` persists changes |
| 6 | Audit Logging | Log Update | Create audit log for `task.updated` |
| 7 | Return | Send Response | FastAPI returns 200 with updated task |

---

## 5. Delete Task

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | DELETE |
| **Path** | `/tasks/{task_id}` |
| **Status Code** | 204 No Content |
| **Authentication** | Required |

### cURL Command

```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `delete_task()` in `app/api/v1/tasks.py:440` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 4 | Soft Delete | Mark as Deleted | Set `is_deleted=true`, `deleted_at=NOW()` via `delete_task()` in `app/services/task_service.py:1021` |
| 5 | Audit Logging | Log Deletion | Create audit log for `task.deleted` |
| 6 | Return | Send Response | FastAPI returns 204 No Content |

---

## 6. Execute Task

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/tasks/{task_id}/execute` |
| **Status Code** | 202 Accepted (async mode), 200 OK (sync mode) |
| **Authentication** | Required |

### cURL Command

```bash
# Async execution (default - returns immediately)
curl -X POST http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "cluster": "production",
      "namespace": "default"
    }
  }'

# Sync execution (waits for completion - DEPRECATED)
curl -X POST "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute?execution_mode=sync" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "cluster": "production"
    }
  }'
```

### Request Body

```json
{
  "variables": {
    "cluster": "production",
    "namespace": "default"
  }
}
```

### Response Example (Async Mode - Default)

```json
{
  "id": "exec-789",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": null,
  "status": "running",
  "trigger_type": "manual",
  "prompt_variables": {
    "cluster": "production",
    "namespace": "default"
  },
  "created_at": "2025-10-25T10:30:00Z",
  "started_at": "2025-10-25T10:30:01Z",
  "_links": {
    "self": "/api/v1/task-executions/exec-789",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Backend Processing Steps - Async Mode (Default)

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `execute_task()` in `app/api/v1/tasks.py:479` |
| 2 | Authentication | Validate Token | Validate user authentication via `get_current_active_user` |
| 3 | Task Validation | Check Task Exists | Verify task exists via `TaskRepository.get_by_id()` |
| 4 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 5 | Service Execution | Execute Task | Call `TaskService.execute_task()` in `app/services/task_service.py:173` |
| 6 | Task Execution Creation | Create Execution Record | Insert into `task_executions` with `status=pending` |
| 7 | Background Async Trigger | Schedule Async Execution | `_execute_task_async()` in `app/services/task_service.py:258` |
| 8 | Immediate Return | HTTP 202 Accepted | Return execution object with status=pending/running (non-blocking) |
| 9 | Background - Render | Render Prompt Template | Replace `{{variables}}` with actual values via `_render_prompt_template()` in `app/services/task_service.py:910` |
| 10 | Background - SDK Setup | Create SDK Options | Build options with `permission_mode='acceptEdits'` (system-controlled) |
| 11 | Background - Execute | Call Claude SDK | `_execute_with_claude_sdk()` in `app/services/task_service.py:341` |
| 12 | Background - Stream | Collect Messages | Iterate through SDK response messages |
| 13 | Background - Complete | Update Execution | Set `status=completed`, save `result_data` with metrics |
| 14 | Background - Audit | Log Execution | Create audit log for `task.executed` |

### Backend Processing Steps - Sync Mode (DEPRECATED)

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1-4 | Same as Async | Create Execution | Same steps 1-4 from execute_task |
| 5 | Session Creation | Create Session | Create dedicated session for execution |
| 6 | Execution Link | Link to Session | Update execution with `session_id` |
| 7 | SDK Setup | Setup SDK Client | Initialize SDK client with MCP servers, hooks, permissions via `_execute_task_sync()` in `app/services/task_service.py:744` |
| 8 | Message Send | Send to Claude | Blocks until completion |
| 9 | Message Processing | Process Stream | Save each message and tool call to database |
| 10 | Report Generation | Generate Report | If `generate_report=true`, create HTML/PDF report |
| 11 | Complete | Update Status | Set `status=completed` |
| 12 | Return | HTTP 200 OK | Return completed execution |

### Execution Modes Comparison

| Aspect | Async Mode (Default) | Sync Mode (DEPRECATED) |
|--------|---------------------|------------------------|
| **Response Time** | Immediate (<1s) | Waits for completion (10s-5m) |
| **HTTP Status** | 202 Accepted | 200 OK |
| **Database Objects** | 2-3 tables | 7-9 tables |
| **Session Created** | ❌ No | ✅ Yes |
| **Messages Stored** | ❌ No | ✅ Yes |
| **Tool Calls Tracked** | ❌ No (summary only) | ✅ Yes (full detail) |
| **Working Directory** | `/tmp/agent-workdirs/{task_id}/` | `/workspace/.../active/{session_id}/` |
| **Report Generation** | ❌ Not supported | ✅ Supported |
| **Real-time Monitoring** | ❌ No | ✅ WebSocket support |

### Permission Mode (System-Controlled)

**IMPORTANT:** Tasks always use `permission_mode="acceptEdits"` (system-forced):
- ✅ Auto-approves all tools without manual intervention
- ✅ Respects `allowed_tools` and `disallowed_tools` lists
- ✅ Cannot be overridden by users (security requirement)
- ✅ Enables automated task execution

**Example:** If `allowed_tools=["Bash(kubectl get:*)"]`:
- ✅ `kubectl get nodes` → Executes automatically
- ✅ `kubectl get pods` → Executes automatically
- ❌ `kubectl delete pod` → Blocked (not in allowed_tools)

---

## 7. List Task Executions

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/{task_id}/executions` |
| **Query Parameters** | `page` (int), `page_size` (int) |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "items": [
    {
      "id": "exec-789",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "sess-456",
      "status": "completed",
      "trigger_type": "manual",
      "prompt_variables": {"cluster": "production"},
      "duration_ms": 15000,
      "created_at": "2025-10-25T10:30:00Z",
      "completed_at": "2025-10-25T10:30:15Z",
      "_links": {
        "self": "/api/v1/task-executions/exec-789",
        "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
        "session": "/api/v1/sessions/sess-456"
      }
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `list_task_executions()` in `app/api/v1/tasks.py:599` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Authorization | Check Task Ownership | Verify task belongs to user OR user is admin |
| 4 | Repository Query | Fetch Executions | `TaskExecutionRepository.get_by_task()` with pagination |
| 5 | Response Mapping | Map to Response | Convert models to `TaskExecutionResponse` |
| 6 | HATEOAS Links | Build Links | Add links to execution, task, session |
| 7 | Return | Send Response | FastAPI returns 200 with paginated executions |

---

## 8. Get Task Execution

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/task-executions/{execution_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/task-executions/exec-789 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "id": "exec-789",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "sess-456",
  "report_id": "report-123",
  "status": "completed",
  "trigger_type": "manual",
  "prompt_variables": {
    "cluster": "production",
    "namespace": "default"
  },
  "result_data": {
    "final_text": "Health check completed successfully. All nodes are Ready. 45 pods running across all namespaces.",
    "total_messages": 5,
    "total_tool_uses": 3,
    "duration_ms": 15000,
    "cost_usd": 0.05,
    "num_turns": 2,
    "working_dir": "/tmp/agent-workdirs/active/550e8400-e29b-41d4-a716-446655440000/"
  },
  "error_message": null,
  "duration_ms": 15000,
  "created_at": "2025-10-25T10:30:00Z",
  "started_at": "2025-10-25T10:30:01Z",
  "completed_at": "2025-10-25T10:30:16Z",
  "_links": {
    "self": "/api/v1/task-executions/exec-789",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "session": "/api/v1/sessions/sess-456",
    "report": "/api/v1/reports/report-123"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_task_execution()` in `app/api/v1/tasks.py:791` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Repository Query | Fetch Execution | `TaskExecutionRepository.get_by_id()` |
| 4 | Execution Validation | Check Existence | If not found, raise 404 Not Found |
| 5 | Task Query | Fetch Task | Get task to verify ownership |
| 6 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 7 | Response Mapping | Map to Response | Convert to `TaskExecutionResponse` |
| 8 | HATEOAS Links | Build Links | Add links to task, session, report |
| 9 | Return | Send Response | FastAPI returns 200 with execution details |

### Execution Status Values

| Status | Description | Next Steps |
|--------|-------------|------------|
| `pending` | Created, not yet started | Will transition to `running` |
| `running` | Currently executing | Monitor via GET endpoint |
| `completed` | Finished successfully | View `result_data` for output |
| `failed` | Failed with error | Check `error_message` |
| `cancelled` | Manually cancelled | N/A |

---

## 9. Retry Task Execution

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/task-executions/{execution_id}/retry` |
| **Status Code** | 202 Accepted |
| **Authentication** | Required |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/task-executions/exec-789/retry \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "id": "exec-790",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "trigger_type": "manual",
  "prompt_variables": {
    "cluster": "production"
  },
  "created_at": "2025-10-25T11:00:00Z",
  "_links": {
    "self": "/api/v1/task-executions/exec-790",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "original": "/api/v1/task-executions/exec-789"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `retry_task_execution()` in `app/api/v1/tasks.py:659` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Fetch Original | Get Execution | `TaskExecutionRepository.get_by_id()` |
| 4 | Status Check | Validate Retryable | Must be `failed`, `pending`, or `queued` |
| 5 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 6 | Status Reset | Reset Execution | Update execution to `status=pending`, clear celery_task_id and errors |
| 7 | Re-Execute | Trigger Async Execution | Call `_execute_task_async()` in `app/services/task_service.py:258` |
| 8 | Audit Logging | Log Retry | Create audit log for `task.retried` |
| 9 | Return | Send Response | FastAPI returns 202 Accepted with new execution details |

### Retryable Statuses

| Original Status | Can Retry? | Behavior |
|----------------|------------|----------|
| `pending` | ✅ Yes | Creates new execution |
| `queued` | ✅ Yes | Creates new execution |
| `failed` | ✅ Yes | Creates new execution with same variables |
| `running` | ❌ No | Returns 400 Bad Request |
| `completed` | ❌ No | Returns 400 Bad Request |
| `cancelled` | ❌ No | Returns 400 Bad Request |

---

## 10. Get Execution Tool Calls

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/executions/{execution_id}/tool-calls` |
| **Query Parameters** | `page` (int), `page_size` (int) |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/executions/exec-789/tool-calls?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "items": [
    {
      "id": "tool-123",
      "execution_id": "exec-789",
      "session_id": "sess-456",
      "tool_name": "Bash",
      "tool_use_id": "toolu_123",
      "input": {
        "command": "kubectl get nodes"
      },
      "output": "NAME     STATUS ROLES AGE\nnode-1   Ready  worker 5d"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_execution_tool_calls()` in `app/api/v1/tasks.py:836` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Service Query | Fetch Tool Calls | `TaskService.get_execution_tool_calls()` in `app/services/task_service.py:1590` |
| 4 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 5 | Pagination | Apply Pagination | Skip and limit based on page/page_size |
| 6 | Response Mapping | Map to Response | Convert models to `ToolCallResponse` |
| 7 | HATEOAS Links | Build Links | Add links to execution, session, self |
| 8 | Return | Send Response | FastAPI returns 200 with paginated tool calls |

### Note
Tool calls are only available for **sync mode** executions (with sessions). Async mode executions don't store individual tool call records.

---

## 11. Cancel Execution

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/tasks/executions/{execution_id}/cancel` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/tasks/executions/exec-789/cancel \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "User requested cancellation"
  }'
```

### Request Body

```json
{
  "reason": "User requested cancellation"
}
```

### Response Example

```json
{
  "id": "exec-789",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "trigger_type": "manual",
  "created_at": "2025-10-25T10:30:00Z",
  "cancelled_at": "2025-10-25T10:30:30Z",
  "_links": {
    "self": "/api/v1/task-executions/exec-789",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `cancel_execution()` in `app/api/v1/tasks.py:901` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Service Call | Cancel Execution | `TaskService.cancel_execution()` in `app/services/task_service.py:1670` |
| 4 | Status Validation | Check Cancelable | Verify execution is in cancelable state |
| 5 | Update Status | Mark Cancelled | Set `status=cancelled`, `cancelled_at=NOW()` |
| 6 | Audit Logging | Log Cancellation | Create audit log for `task.cancelled` |
| 7 | Response Mapping | Map to Response | Convert to `TaskExecutionResponse` |
| 8 | Return | Send Response | FastAPI returns 200 with cancelled execution |

### Cancellation Rules

| Status | Can Cancel? | Behavior |
|--------|-------------|----------|
| `pending` | ✅ Yes | Cancelled immediately |
| `queued` | ✅ Yes | Cancelled immediately |
| `running` (async) | ✅ Yes | Cancellation flag set, background task will stop |
| `running` (sync) | ❌ No | Not supported (requires subprocess kill) |
| `completed` | ❌ No | Already finished |
| `failed` | ❌ No | Already finished |
| `cancelled` | ❌ No | Already cancelled |

---

## 12. Get Execution Files

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/executions/{execution_id}/files` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/tasks/executions/exec-789/files \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "execution_id": "exec-789",
  "total_files": 5,
  "total_size": 1024000,
  "files": [
    {
      "path": "output.txt",
      "size": 512000,
      "modified": "2025-10-25T10:30:15Z"
    },
    {
      "path": "logs/debug.log",
      "size": 256000,
      "modified": "2025-10-25T10:30:10Z"
    }
  ],
  "_links": {
    "self": "/api/v1/task-executions/exec-789/files",
    "execution": "/api/v1/task-executions/exec-789",
    "download": "/api/v1/task-executions/exec-789/files/download",
    "archive": "/api/v1/task-executions/exec-789/archive"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_execution_files()` in `app/api/v1/tasks.py:955` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Service Call | Get Files | `TaskService.get_execution_files()` in `app/services/task_service.py:1774` |
| 4 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 5 | Working Dir | Get Directory Path | Fetch from session or result_data |
| 6 | Directory Scan | List Files | Walk directory tree and collect file metadata |
| 7 | Size Calculation | Calculate Sizes | Calculate individual file sizes and total |
| 8 | Response Building | Build Response | Create `WorkingDirectoryManifest` |
| 9 | HATEOAS Links | Build Links | Add download and archive links |
| 10 | Return | Send Response | FastAPI returns 200 with file manifest |

### Note
Working directory must still exist (not yet archived or cleaned up).

---

## 13. Download Execution File

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/executions/{execution_id}/files/download` |
| **Query Parameters** | `file_path` (string, required) |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/executions/exec-789/files/download?file_path=output.txt" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o output.txt
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `download_execution_files()` in `app/api/v1/tasks.py:1015` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 4 | Working Dir | Get Directory Path | Fetch from session or result_data |
| 5 | Path Validation | Verify File | Check file exists and is within working directory (prevent traversal) |
| 6 | File Response | Stream File | Return file via `FileResponse` |

---

## 14. Archive Execution Directory

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/tasks/executions/{execution_id}/archive` |
| **Status Code** | 200 OK |
| **Authentication** | Required |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/tasks/executions/exec-789/archive \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "execution_id": "exec-789",
  "archive_path": "/workspace/archives/exec-789_2025-10-25.tar.gz",
  "archive_size": 512000,
  "created_at": "2025-10-25T10:31:00Z",
  "_links": {
    "self": "/api/v1/task-executions/exec-789/archive",
    "execution": "/api/v1/task-executions/exec-789",
    "download": "/api/v1/archives/exec-789/download"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `archive_execution_directory()` in `app/api/v1/tasks.py:1109` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Service Call | Archive | `TaskService.archive_execution_directory()` in `app/services/task_service.py:1866` |
| 4 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 5 | Working Dir | Get Directory Path | Fetch from session or result_data |
| 6 | Compression | Create tar.gz | Compress working directory to tar.gz format |
| 7 | Storage | Save Archive | Save to archive directory |
| 8 | Cleanup | Delete Original | Delete original working directory (irreversible) |
| 9 | Response Building | Build Response | Create `ArchiveResponse` with archive metadata |
| 10 | Return | Send Response | FastAPI returns 200 with archive details |

### Note
This operation is **irreversible**. The original working directory is deleted after archiving.

---

## 15. Download Archive

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/tasks/archives/{archive_id}/download` |
| **Status Code** | 200 OK (file download) |
| **Authentication** | Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/tasks/archives/exec-789/download \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o archive.tar.gz
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `download_archive()` in `app/api/v1/tasks.py:1163` |
| 2 | Authentication | Validate Token | Validate user authentication |
| 3 | Authorization | Check Ownership | Verify task belongs to user OR user is admin |
| 4 | Archive Lookup | Find Archive | Search for archive files matching execution_id |
| 5 | File Response | Stream Archive | Return tar.gz file via `FileResponse` |

---

## Error Responses

### 400 Bad Request - Invalid Tool Pattern

```json
{
  "detail": "Invalid tool pattern 'InvalidTool'. Must be a valid Claude Code tool (Bash, Read, Write, etc.) or MCP tool (mcp__server__tool) or wildcard (*)"
}
```

**Triggered When:**
- `allowed_tools` or `disallowed_tools` contains invalid pattern
- Applicable to: POST `/tasks`, PATCH `/tasks/{task_id}`

---

### 400 Bad Request - Invalid Prompt Template

```json
{
  "detail": "Invalid prompt template syntax: unexpected 'end of template'"
}
```

**Triggered When:**
- `prompt_template` has invalid Jinja2 syntax
- Applicable to: POST `/tasks`, PATCH `/tasks/{task_id}`

---

### 400 Bad Request - Invalid Cron Expression

```json
{
  "detail": "Invalid cron expression: 0 25 * * *"
}
```

**Triggered When:**
- `schedule_cron` is not a valid cron expression
- Applicable to: POST `/tasks`, PATCH `/tasks/{task_id}`

---

### 400 Bad Request - Cannot Retry

```json
{
  "detail": "Can only retry executions with status: pending, queued, failed. Current status: completed"
}
```

**Triggered When:**
- Attempting to retry execution that is not in retryable state
- Applicable to: POST `/task-executions/{execution_id}/retry`

---

### 401 Unauthorized - Missing/Invalid Token

```json
{
  "detail": "Not authenticated"
}
```

**Triggered When:**
- No Authorization header provided
- Invalid or expired JWT token
- Applicable to: All endpoints

---

### 403 Forbidden - Not Owner

```json
{
  "detail": "Not authorized to access this task"
}
```

**Triggered When:**
- User tries to access another user's task
- User is not admin
- Applicable to: All task and execution endpoints

---

### 404 Not Found - Task Not Found

```json
{
  "detail": "Task 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Triggered When:**
- Task ID doesn't exist in database
- Task is soft-deleted (`is_deleted=true`)
- Applicable to: GET/PATCH/DELETE `/tasks/{task_id}`, POST `/tasks/{task_id}/execute`

---

### 404 Not Found - Execution Not Found

```json
{
  "detail": "Execution exec-789 not found"
}
```

**Triggered When:**
- Execution ID doesn't exist in database
- Applicable to: GET `/task-executions/{execution_id}`, POST `/task-executions/{execution_id}/retry`

---

## Related Files

### Core Implementation
- **API Endpoints:** `app/api/v1/tasks.py` (650+ lines)
- **Task Service:** `app/services/task_service.py` (1564 lines)
- **Task Repository:** `app/repositories/task_repository.py`
- **Task Execution Repository:** `app/repositories/task_execution_repository.py`

### Domain Layer
- **Task Entity:** `app/domain/entities/task.py`
- **Task Execution Entity:** `app/domain/entities/task_execution.py`

### Database Models
- **Task Model:** `app/models/task.py`
- **Task Execution Model:** `app/models/task_execution.py`

### Schemas
- **Task Schemas:** `app/schemas/task.py` (includes TaskCreateRequest, TaskUpdateRequest, TaskResponse, TaskExecuteRequest, TaskExecutionResponse, ToolCallResponse, ExecutionCancelRequest, WorkingDirectoryManifest, ArchiveResponse, etc.)

### Dependencies
- **Authentication:** `app/api/dependencies.py`
- **Audit Service:** `app/services/audit_service.py`

---

## Summary Table

| # | Operation | Method | Endpoint | Response Time | Status | Notes |
|---|-----------|--------|----------|---------------|--------|-------|
| 1 | Create Task | POST | `/tasks` | ~50ms | 201 Created | Sync |
| 2 | Get Task (Detailed) | GET | `/tasks/{task_id}` | ~100ms | 200 OK | Sync, includes aggregated child data |
| 3 | List Tasks | GET | `/tasks` | ~40ms | 200 OK | Sync, supports filtering & pagination |
| 4 | Update Task | PATCH | `/tasks/{task_id}` | ~45ms | 200 OK | Sync |
| 5 | Delete Task | DELETE | `/tasks/{task_id}` | ~35ms | 204 No Content | Soft delete |
| 6 | Execute Task | POST | `/tasks/{task_id}/execute` | ~5ms | 202 Accepted | Async, returns immediately |
| 7 | List Executions | GET | `/tasks/{task_id}/executions` | ~50ms | 200 OK | Sync, supports pagination |
| 8 | Get Execution | GET | `/task-executions/{execution_id}` | ~30ms | 200 OK | Sync |
| 9 | Retry Execution | POST | `/task-executions/{execution_id}/retry` | ~5ms | 202 Accepted | Async, for failed/pending executions |
| 10 | Get Tool Calls ⭐ NEW | GET | `/tasks/executions/{execution_id}/tool-calls` | ~40ms | 200 OK | Sync mode only, pagination support |
| 11 | Cancel Execution ⭐ NEW | POST | `/tasks/executions/{execution_id}/cancel` | ~10ms | 200 OK | Cancels running/pending executions |
| 12 | Get Files ⭐ NEW | GET | `/tasks/executions/{execution_id}/files` | ~100ms | 200 OK | Scans working directory |
| 13 | Download File ⭐ NEW | GET | `/tasks/executions/{execution_id}/files/download` | Variable | 200 OK | Streams file with directory traversal protection |
| 14 | Archive Directory ⭐ NEW | POST | `/tasks/executions/{execution_id}/archive` | ~500ms | 200 OK | Compresses and deletes original (irreversible) |
| 15 | Download Archive ⭐ NEW | GET | `/tasks/archives/{archive_id}/download` | Variable | 200 OK | Streams tar.gz archive file |

---

## Usage Examples

### Complete Task Lifecycle

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@default.org", "password": "admin123"}' \
  | jq -r '.access_token')

# 2. Create task
TASK_ID=$(curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily K8s Health Check",
    "prompt_template": "Check {{cluster}} cluster health",
    "allowed_tools": ["Bash(kubectl get:*)", "Bash(kubectl describe:*)"],
    "sdk_options": {"model": "claude-sonnet-4-5", "max_turns": 10},
    "tags": ["monitoring"]
  }' | jq -r '.id')

echo "Created task: $TASK_ID"

# 3. Execute task
EXEC_ID=$(curl -s -X POST http://localhost:8000/api/v1/tasks/$TASK_ID/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variables": {"cluster": "production"}}' \
  | jq -r '.id')

echo "Started execution: $EXEC_ID"

# 4. Monitor execution (poll every 5 seconds)
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/task-executions/$EXEC_ID \
    -H "Authorization: Bearer $TOKEN" \
    | jq -r '.status')

  echo "Execution status: $STATUS"

  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    break
  fi

  sleep 5
done

# 5. Get final results
curl http://localhost:8000/api/v1/task-executions/$EXEC_ID \
  -H "Authorization: Bearer $TOKEN" | jq .

# 6. Get detailed task info with all executions
curl "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Filter and Pagination

```bash
# Get scheduled tasks only
curl "http://localhost:8000/api/v1/tasks?is_scheduled=true" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Get tasks by tags
curl "http://localhost:8000/api/v1/tasks?tags=monitoring&tags=kubernetes" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Paginate results
curl "http://localhost:8000/api/v1/tasks?page=2&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Best Practices

### 1. Task Design
- **Specific allowed_tools:** Use command-level patterns like `Bash(kubectl get:*)` instead of `Bash`
- **Clear prompt templates:** Make templates self-documenting with clear variable names
- **Appropriate max_turns:** Set based on task complexity (simple: 5, complex: 20)
- **Use disallowed_tools:** For allowlist approach with specific exclusions

### 2. Execution Monitoring
- **Use async mode:** Default async mode for better performance
- **Poll execution status:** Check every 5-10 seconds for completion
- **Check result_data:** Contains final text, metrics, and cost information
- **Monitor failures:** Set up alerts for `status=failed`

### 3. Resource Management
- **Archive working directories:** Implement archival for completed executions
- **Set execution retention:** Delete old executions after 90 days
- **Monitor costs:** Track `result_data.cost_usd` in execution summary
- **Clean up sessions:** For sync mode, archive or delete old sessions

### 4. Security
- **Principle of least privilege:** Only allow minimum required tools
- **Read-only for monitoring:** Use `Bash(kubectl get:*)` not `Bash(kubectl:*)`
- **Validate variables:** Sanitize user-provided variables before execution
- **Audit trail:** Review `audit_summary` for security events

---

**Last Updated:** October 25, 2025
**API Version:** v1
**Reviewed By:** Claude AI Agent

**Documentation Coverage:**
- ✅ All 9 task endpoints documented
- ✅ Backend processing steps detailed
- ✅ Request/response examples provided
- ✅ Error scenarios covered
- ✅ Best practices included
