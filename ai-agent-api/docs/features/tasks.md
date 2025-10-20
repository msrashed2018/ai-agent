# Tasks API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Concepts](#core-concepts)
4. [API Endpoints](#api-endpoints)
5. [Data Models](#data-models)
6. [Execution Flow](#execution-flow)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

---

## Overview

The Tasks API enables developers to create reusable, automated agent workflows. Tasks are template-based definitions that can be executed manually or scheduled to run automatically. Each task execution creates a dedicated AI session, processes the task through Claude, and optionally generates reports.

### Key Features
- **Template-based prompts** with variable substitution
- **Manual and scheduled execution** with cron expressions
- **Tool access control** via allowed/disallowed tool lists
- **Automatic report generation** in multiple formats (JSON, HTML, Markdown, PDF)
- **Execution history tracking** with metrics and status
- **Session integration** - each execution creates a dedicated session
- **Audit logging** for compliance and debugging

### Use Cases
- Automated monitoring and health checks
- Scheduled data analysis and reporting
- Recurring administrative tasks
- Template-based agent workflows
- Batch processing operations

---

## Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  /api/v1/tasks/* endpoints                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Service Layer                               │
│  • TaskService (business logic)                              │
│  • SDKIntegratedSessionService                               │
│  • ReportService                                             │
│  • AuditService                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│               Repository Layer                               │
│  • TaskRepository                                            │
│  • TaskExecutionRepository                                   │
│  • SessionRepository                                         │
│  • MessageRepository                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                Database Layer                                │
│  • tasks table                                               │
│  • task_executions table                                     │
│  • sessions table                                            │
│  • reports table                                             │
└─────────────────────────────────────────────────────────────┘
```

### Domain Entities

**Task Entity** (`app/domain/entities/task.py`)
- Represents a task definition/template
- Contains prompt template, tool configuration, scheduling settings
- Validates cron expressions and report formats

**TaskExecution Entity** (`app/domain/entities/task_execution.py`)
- Represents a single execution instance of a task
- Tracks status, metrics, and execution lifecycle
- Links to session and optional report

---

## Core Concepts

### Task Definition
A Task is a reusable template that defines:
- **Prompt Template**: Text with `{variable}` placeholders
- **Tool Configuration**: Which tools Claude can use during execution
- **SDK Options**: Session configuration (MCP servers, permissions, etc.)
- **Scheduling**: Optional cron expression for automation
- **Reporting**: Whether to generate reports after execution

### Task Execution
When a task is executed:
1. A new execution record is created
2. A dedicated AI session is created
3. Variables are substituted into the prompt template
4. The rendered prompt is sent to Claude via the session
5. Claude processes the request (may use tools, MCP servers)
6. Execution status is tracked (pending → running → completed/failed)
7. Optional report is generated from session output

### Execution States

```
┌─────────┐
│ PENDING │  Initial state when execution is created
└────┬────┘
     │
     ▼
┌─────────┐
│ RUNNING │  Session created, prompt sent to Claude
└────┬────┘
     │
     ├──────────┐
     │          │
     ▼          ▼
┌───────────┐  ┌────────┐
│ COMPLETED │  │ FAILED │  Final states
└───────────┘  └────────┘
```

### Trigger Types
- **manual**: User-initiated execution via API
- **scheduled**: Automatic execution via cron scheduler
- **webhook**: Triggered by external webhook
- **api**: Programmatic execution

---

## API Endpoints

### 1. Create Task

**Endpoint**: `POST /api/v1/tasks`

**Purpose**: Create a new task definition

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "name": "Daily Health Check",
  "description": "Check system health and generate report",
  "prompt_template": "Check the health of {environment} environment",
  "allowed_tools": ["kubernetes_*", "database_*"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096
  },
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "generate_report": true,
  "report_format": "html",
  "tags": ["monitoring", "health"]
}
```

**Backend Flow**:

```
1. API Endpoint (tasks.py:create_task)
   │
   ├─► Authentication Check (get_current_active_user)
   │   └─► Validate JWT token
   │
   ├─► Initialize Dependencies
   │   ├─► TaskRepository
   │   ├─► TaskExecutionRepository
   │   ├─► UserRepository
   │   └─► AuditService
   │
   ├─► TaskService.create_task()
   │   │
   │   ├─► Create Task Entity
   │   │   ├─► Generate UUID
   │   │   ├─► Set user_id, name, prompt_template
   │   │   └─► Set tool configuration
   │   │
   │   ├─► Validate Configuration
   │   │   ├─► If scheduled: Validate cron expression
   │   │   └─► If generate_report: Validate report format
   │   │
   │   ├─► Persist to Database
   │   │   ├─► Create TaskModel instance
   │   │   ├─► db.add(task_model)
   │   │   ├─► db.flush()
   │   │   └─► db.commit()
   │   │
   │   └─► Audit Logging
   │       └─► AuditService.log_action("task.created")
   │
   └─► Build Response
       ├─► Create TaskResponse
       └─► Add HATEOAS links
           ├─► self: /api/v1/tasks/{id}
           ├─► execute: /api/v1/tasks/{id}/execute
           └─► executions: /api/v1/tasks/{id}/executions
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Daily Health Check",
  "description": "Check system health and generate report",
  "prompt_template": "Check the health of {environment} environment",
  "allowed_tools": ["kubernetes_*", "database_*"],
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "generate_report": true,
  "report_format": "html",
  "is_active": true,
  "created_at": "2025-10-20T10:00:00Z",
  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute",
    "executions": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions"
  }
}
```

---

### 2. Get Task

**Endpoint**: `GET /api/v1/tasks/{task_id}`

**Purpose**: Retrieve task details by ID

**Authentication**: Required (Bearer token)

**Backend Flow**:

```
1. API Endpoint (tasks.py:get_task)
   │
   ├─► Authentication Check
   │
   ├─► TaskRepository.get_by_id(task_id)
   │   └─► SELECT * FROM tasks WHERE id = ? AND is_deleted = false
   │
   ├─► Validation
   │   ├─► Check if task exists (404 if not)
   │   └─► Check ownership or admin role (403 if unauthorized)
   │
   └─► Build Response with HATEOAS links
```

**Response**: `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Daily Health Check",
  "is_active": true,
  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute",
    "executions": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions"
  }
}
```

---

### 3. List Tasks

**Endpoint**: `GET /api/v1/tasks`

**Purpose**: List all tasks for the current user with filtering and pagination

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `tags`: Filter by tags (optional, array)
- `is_scheduled`: Filter by scheduled status (optional, boolean)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Backend Flow**:

```
1. API Endpoint (tasks.py:list_tasks)
   │
   ├─► Authentication Check
   │
   ├─► Parse Query Parameters
   │   ├─► tags (optional)
   │   ├─► is_scheduled (optional)
   │   └─► PaginationParams (page, page_size)
   │
   ├─► TaskRepository.get_by_user(user_id, skip, limit)
   │   └─► SELECT * FROM tasks 
   │       WHERE user_id = ? AND is_deleted = false
   │       ORDER BY created_at DESC
   │       OFFSET ? LIMIT ?
   │
   ├─► Apply In-Memory Filters
   │   ├─► Filter by is_scheduled if provided
   │   └─► Filter by tags if provided
   │
   ├─► Build Response Items
   │   └─► For each task: Add HATEOAS links
   │
   └─► Return Paginated Response
       ├─► items: Array of TaskResponse
       ├─► total: Total count
       ├─► page: Current page
       └─► page_size: Items per page
```

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Daily Health Check",
      "_links": { ... }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 4. Update Task

**Endpoint**: `PATCH /api/v1/tasks/{task_id}`

**Purpose**: Update task configuration

**Authentication**: Required (Bearer token)

**Request Body** (all fields optional):
```json
{
  "name": "Updated Task Name",
  "description": "New description",
  "is_scheduled": false,
  "tags": ["updated", "monitoring"]
}
```

**Backend Flow**:

```
1. API Endpoint (tasks.py:update_task)
   │
   ├─► Authentication Check
   │
   ├─► Get Task
   │   ├─► TaskRepository.get_by_id(task_id)
   │   └─► Validate existence and ownership
   │
   ├─► TaskService.update_task()
   │   │
   │   ├─► Load Task Entity
   │   │
   │   ├─► Apply Updates
   │   │   └─► Only fields present in request (exclude_unset=True)
   │   │
   │   ├─► Validate Updates
   │   │   ├─► If is_scheduled changed: Validate cron
   │   │   └─► If generate_report changed: Validate format
   │   │
   │   ├─► Update Database
   │   │   ├─► TaskRepository.update(task_id, **updates)
   │   │   └─► db.commit()
   │   │
   │   └─► Return Updated Entity
   │
   └─► Build Response with HATEOAS links
```

**Response**: `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Task Name",
  "updated_at": "2025-10-20T11:00:00Z",
  "_links": { ... }
}
```

---

### 5. Delete Task

**Endpoint**: `DELETE /api/v1/tasks/{task_id}`

**Purpose**: Soft delete a task

**Authentication**: Required (Bearer token)

**Backend Flow**:

```
1. API Endpoint (tasks.py:delete_task)
   │
   ├─► Authentication Check
   │
   ├─► Get and Validate Task
   │   ├─► Check existence
   │   └─► Check ownership
   │
   ├─► TaskService.delete_task()
   │   │
   │   ├─► TaskRepository.soft_delete(task_id)
   │   │   └─► UPDATE tasks 
   │   │       SET is_deleted = true, 
   │   │           deleted_at = NOW(),
   │   │           updated_at = NOW()
   │   │       WHERE id = ?
   │   │
   │   └─► db.commit()
   │
   └─► Return 204 No Content
```

**Response**: `204 No Content`

---

### 6. Execute Task

**Endpoint**: `POST /api/v1/tasks/{task_id}/execute`

**Purpose**: Manually trigger task execution

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "variables": {
    "environment": "production",
    "region": "us-east-1"
  }
}
```

**Backend Flow** (Most Complex Endpoint):

```
1. API Endpoint (tasks.py:execute_task)
   │
   ├─► Authentication Check
   │
   ├─► Get and Validate Task
   │   ├─► Check existence
   │   ├─► Check ownership
   │   └─► Verify task is active
   │
   └─► TaskService.execute_task()
       │
       ├─► 1. Get and Validate Task
       │   ├─► TaskRepository.get_by_id(task_id)
       │   └─► Check is_active = true
       │
       ├─► 2. Create Task Execution Record
       │   ├─► Generate execution UUID
       │   ├─► Create TaskExecution entity
       │   │   ├─► task_id
       │   │   ├─► user_id
       │   │   ├─► trigger_type = "manual"
       │   │   ├─► variables (from request)
       │   │   └─► status = PENDING
       │   │
       │   ├─► Persist TaskExecutionModel
       │   │   ├─► db.add(execution_model)
       │   │   ├─► db.flush()
       │   │   └─► db.commit()
       │   │
       │   └─► Status: PENDING
       │
       ├─► 3. Create Session for Task Execution
       │   │
       │   ├─► Initialize SDKIntegratedSessionService
       │   │   ├─► SessionRepository
       │   │   ├─► MessageRepository
       │   │   ├─► ToolCallRepository
       │   │   ├─► UserRepository
       │   │   ├─► StorageManager
       │   │   └─► AuditService
       │   │
       │   ├─► SessionService.create_session()
       │   │   ├─► Name: "Task: {task.name} (manual)"
       │   │   ├─► Description: "Automated execution..."
       │   │   ├─► sdk_options: From task.sdk_options
       │   │   │   └─► Includes MCP config, tool permissions, etc.
       │   │   │
       │   │   ├─► Create Session Entity
       │   │   │   ├─► Generate UUID
       │   │   │   ├─► user_id
       │   │   │   ├─► status = CREATED
       │   │   │   └─► working_directory setup
       │   │   │
       │   │   └─► Persist to database
       │   │
       │   ├─► Update Execution with session_id
       │   │   ├─► execution.session_id = session.id
       │   │   ├─► execution.status = RUNNING
       │   │   └─► TaskExecutionRepository.update()
       │   │
       │   └─► Status: RUNNING
       │
       ├─► 4. Render Prompt Template
       │   │
       │   └─► _render_prompt_template()
       │       ├─► Template: "Check health of {environment}"
       │       ├─► Variables: {"environment": "production"}
       │       └─► Result: "Check health of production"
       │
       ├─► 5. Send Message Through Session
       │   │
       │   └─► SessionService.send_message(session_id, rendered_prompt)
       │       │
       │       ├─► Validate Session State
       │       │   └─► Must be CREATED, ACTIVE, or CONNECTING
       │       │
       │       ├─► Session State Transition: CREATED → CONNECTING
       │       │   └─► If first message to session
       │       │
       │       ├─► Setup SDK Client (if needed)
       │       │   │
       │       │   ├─► Build MCP Configuration
       │       │   │   ├─► Include SDK tools (kubernetes, database, monitoring)
       │       │   │   ├─► Include user's MCP servers
       │       │   │   └─► Merge into session.sdk_options
       │       │   │
       │       │   ├─► Create Permission Callback
       │       │   │   └─► For tool access control
       │       │   │
       │       │   ├─► Setup Hooks
       │       │   │   ├─► PreToolUse: Audit + Tracking
       │       │   │   └─► PostToolUse: Audit + Tracking + Cost
       │       │   │
       │       │   └─► SDKClientManager.create_client()
       │       │       └─► Initialize Claude SDK client with config
       │       │
       │       ├─► Session State Transition: CONNECTING → ACTIVE
       │       │
       │       ├─► Session State Transition: ACTIVE → PROCESSING
       │       │
       │       ├─► Send to Claude SDK
       │       │   ├─► client.query(rendered_prompt)
       │       │   └─► Start message stream
       │       │
       │       ├─► Process Response Stream
       │       │   │
       │       │   └─► MessageProcessor.process_message_stream()
       │       │       ├─► Receive SDK messages
       │       │       ├─► Convert to domain Message entities
       │       │       ├─► Persist messages to database
       │       │       ├─► Persist tool calls
       │       │       ├─► Update session metrics
       │       │       └─► Broadcast to WebSocket subscribers
       │       │
       │       └─► Session State Transition: PROCESSING → ACTIVE
       │
       ├─► 6. Mark Execution as Completed
       │   ├─► execution.status = COMPLETED
       │   ├─► execution.completed_at = NOW()
       │   ├─► execution.result_message_id = message.id
       │   └─► TaskExecutionRepository.update()
       │
       ├─► 7. Generate Report (if configured)
       │   │
       │   └─► If task.generate_report = true
       │       │
       │       ├─► Initialize ReportService
       │       │
       │       ├─► ReportService.generate_from_session()
       │       │   │
       │       │   ├─► Verify session access
       │       │   │
       │       │   ├─► Build report content
       │       │   │   └─► Aggregate session messages, tool calls, metrics
       │       │   │
       │       │   ├─► Create Report entity
       │       │   │   ├─► Title: "Task Execution Report: {task.name}"
       │       │   │   ├─► Format: task.report_format (html/json/markdown/pdf)
       │       │   │   └─► Content: Session data
       │       │   │
       │       │   ├─► Format and Save Report File
       │       │   │   ├─► Format content based on report_format
       │       │   │   └─► StorageManager.save_report()
       │       │   │
       │       │   ├─► Persist ReportModel
       │       │   │   └─► Link to session and execution
       │       │   │
       │       │   └─► Audit log
       │       │
       │       ├─► Update execution.report_id
       │       │
       │       └─► db.commit()
       │
       ├─► 8. Audit Logging
       │   └─► AuditService.log_task_executed()
       │       ├─► action_type: "task.executed"
       │       ├─► task_id, execution_id
       │       ├─► trigger_type: "manual"
       │       └─► status: "completed"
       │
       └─► Return TaskExecution entity

2. Error Handling
   │
   └─► On Any Exception:
       ├─► Mark execution as FAILED
       │   ├─► execution.status = FAILED
       │   ├─► execution.completed_at = NOW()
       │   └─► execution.error_message = str(e)
       │
       ├─► Audit log failure
       │   └─► status: "failed", error: str(e)
       │
       └─► Re-raise exception

3. API Response
   │
   └─► Build TaskExecutionResponse
       ├─► execution details
       └─► HATEOAS links
           ├─► self: /api/v1/task-executions/{id}
           ├─► task: /api/v1/tasks/{task_id}
           ├─► session: /api/v1/sessions/{session_id}
           └─► report: /api/v1/reports/{report_id} (if generated)
```

**Response**: `202 Accepted`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "running",
  "trigger_type": "manual",
  "prompt_variables": {
    "environment": "production"
  },
  "created_at": "2025-10-20T12:00:00Z",
  "started_at": "2025-10-20T12:00:01Z",
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440001",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "session": "/api/v1/sessions/770e8400-e29b-41d4-a716-446655440002"
  }
}
```

---

### 7. List Task Executions

**Endpoint**: `GET /api/v1/tasks/{task_id}/executions`

**Purpose**: Get execution history for a specific task

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)

**Backend Flow**:

```
1. API Endpoint (tasks.py:list_task_executions)
   │
   ├─► Authentication Check
   │
   ├─► Get and Validate Task
   │   ├─► TaskRepository.get_by_id(task_id)
   │   └─► Check ownership
   │
   ├─► TaskExecutionRepository.list_by_task()
   │   └─► SELECT * FROM task_executions
   │       WHERE task_id = ?
   │       ORDER BY created_at DESC
   │       OFFSET ? LIMIT ?
   │
   ├─► Build Response Items
   │   └─► For each execution: Add HATEOAS links
   │       ├─► self
   │       ├─► task
   │       ├─► session (if exists)
   │       └─► report (if exists)
   │
   └─► Return Paginated Response
```

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "trigger_type": "manual",
      "duration_ms": 15000,
      "_links": { ... }
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 8. Get Task Execution

**Endpoint**: `GET /api/v1/task-executions/{execution_id}`

**Purpose**: Get detailed status and results of a specific execution

**Authentication**: Required (Bearer token)

**Backend Flow**:

```
1. API Endpoint (tasks.py:get_task_execution)
   │
   ├─► Authentication Check
   │
   ├─► TaskExecutionRepository.get_by_id(execution_id)
   │
   ├─► Validate Ownership
   │   ├─► Get task via execution.task_id
   │   └─► Check task.user_id or admin role
   │
   └─► Build Response with HATEOAS links
```

**Response**: `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "trigger_type": "manual",
  "prompt_variables": {
    "environment": "production"
  },
  "result_data": {
    "summary": "Health check completed successfully"
  },
  "report_id": "880e8400-e29b-41d4-a716-446655440003",
  "duration_ms": 15000,
  "created_at": "2025-10-20T12:00:00Z",
  "started_at": "2025-10-20T12:00:01Z",
  "completed_at": "2025-10-20T12:00:16Z",
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440001",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "session": "/api/v1/sessions/770e8400-e29b-41d4-a716-446655440002",
    "report": "/api/v1/reports/880e8400-e29b-41d4-a716-446655440003"
  }
}
```

---

## Data Models

### Task Model (`tasks` table)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Owner (foreign key to users) |
| `name` | String(255) | Task name |
| `description` | Text | Optional description |
| `prompt_template` | Text | Prompt with {variable} placeholders |
| `default_variables` | JSONB | Default variable values |
| `allowed_tools` | String[] | Tool patterns allowed |
| `disallowed_tools` | String[] | Tool patterns disallowed |
| `sdk_options` | JSONB | Session SDK configuration |
| `working_directory_path` | String(1000) | Optional working directory |
| `is_scheduled` | Boolean | Whether task has schedule |
| `schedule_cron` | String(100) | Cron expression |
| `schedule_enabled` | Boolean | Whether schedule is active |
| `generate_report` | Boolean | Auto-generate report |
| `report_format` | String(50) | json/markdown/html/pdf |
| `notification_config` | JSONB | Notification settings |
| `tags` | String[] | Categorization tags |
| `is_public` | Boolean | Visible to organization |
| `is_active` | Boolean | Task can be executed |
| `is_deleted` | Boolean | Soft delete flag |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `deleted_at` | DateTime | Deletion timestamp |

**Indexes**:
- `idx_tasks_user` on (user_id, is_deleted)
- `idx_tasks_scheduled` on (is_scheduled, schedule_enabled) WHERE is_deleted = false
- `idx_tasks_tags` GIN index on tags array
- `idx_tasks_name` on name for pattern matching

---

### Task Execution Model (`task_executions` table)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `task_id` | UUID | Foreign key to tasks |
| `session_id` | UUID | Foreign key to sessions |
| `report_id` | UUID | Foreign key to reports |
| `trigger_type` | String(50) | manual/scheduled/webhook/api |
| `trigger_metadata` | JSONB | Additional trigger context |
| `prompt_variables` | JSONB | Variables used in execution |
| `status` | String(50) | pending/running/completed/failed/cancelled |
| `error_message` | String | Error details if failed |
| `result_data` | JSONB | Execution results |
| `total_messages` | Integer | Message count in session |
| `total_tool_calls` | Integer | Tool call count |
| `duration_seconds` | Integer | Execution duration |
| `created_at` | DateTime | Creation timestamp |
| `started_at` | DateTime | Execution start time |
| `completed_at` | DateTime | Completion time |

**Indexes**:
- `idx_task_executions_task` on (task_id, created_at)
- `idx_task_executions_session` on (session_id)
- `idx_task_executions_status` on (status, created_at)
- `idx_task_executions_trigger` on (trigger_type)

---

## Execution Flow

### Complete Task Execution Lifecycle

```
┌──────────────┐
│   CREATE     │  User creates task definition via POST /tasks
│     TASK     │  • Validates prompt template
└──────┬───────┘  • Validates cron if scheduled
       │          • Validates report format if enabled
       │          • Persists to database
       │          • Logs audit event
       │
       ▼
┌──────────────┐
│   EXECUTE    │  User or scheduler triggers execution
│     TASK     │  POST /tasks/{id}/execute
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   CREATE     │  1. Generate execution UUID
│  EXECUTION   │  2. Create TaskExecution entity
│   RECORD     │  3. Set status = PENDING
└──────┬───────┘  4. Persist to database
       │
       ▼
┌──────────────┐
│   CREATE     │  1. Generate session UUID
│   SESSION    │  2. Configure SDK options from task
└──────┬───────┘  3. Setup working directory
       │          4. Persist session
       │          5. Update execution.session_id
       │          6. Set status = RUNNING
       │
       ▼
┌──────────────┐
│   RENDER     │  1. Parse prompt template
│   PROMPT     │  2. Substitute variables
└──────┬───────┘  3. Validate rendered prompt
       │
       ▼
┌──────────────┐
│   SETUP      │  1. Build MCP configuration
│  SDK CLIENT  │     • Include SDK tools
└──────┬───────┘     • Include user MCP servers
       │          2. Create permission callbacks
       │          3. Setup audit/tracking hooks
       │          4. Initialize Claude SDK client
       │
       ▼
┌──────────────┐
│  SEND TO     │  1. client.query(rendered_prompt)
│   CLAUDE     │  2. Session: ACTIVE → PROCESSING
└──────┬───────┘  3. Stream begins
       │
       ▼
┌──────────────┐
│   PROCESS    │  1. Receive message chunks
│   RESPONSE   │  2. Convert to domain entities
│   STREAM     │  3. Persist messages
└──────┬───────┘  4. Persist tool calls
       │          5. Execute hooks
       │          6. Update metrics
       │          7. Broadcast to WebSocket
       │
       ▼
┌──────────────┐
│  COMPLETE    │  1. Set status = COMPLETED
│  EXECUTION   │  2. Set completed_at
└──────┬───────┘  3. Calculate duration
       │          4. Set result_message_id
       │          5. Session: PROCESSING → ACTIVE
       │
       ▼
┌──────────────┐
│  GENERATE    │  If task.generate_report = true:
│   REPORT     │  1. Aggregate session data
│  (optional)  │  2. Format report
└──────┬───────┘  3. Save report file
       │          4. Link to execution
       │          5. Update execution.report_id
       │
       ▼
┌──────────────┐
│   AUDIT      │  1. Log task execution event
│     LOG      │  2. Record metrics
└──────┬───────┘  3. Store execution details
       │
       ▼
┌──────────────┐
│   RETURN     │  202 Accepted
│   RESPONSE   │  • Execution details
└──────────────┘  • Status
                  • Links to session, report
```

### Error Handling Flow

```
┌─────────────┐
│   ERROR     │  Exception during execution
│  OCCURS     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   UPDATE    │  1. Set status = FAILED
│  EXECUTION  │  2. Set error_message
└──────┬──────┘  3. Set completed_at
       │          4. Calculate duration
       │
       ▼
┌─────────────┐
│   UPDATE    │  If session exists:
│  SESSION    │  1. Set status = FAILED
└──────┬──────┘  2. Set error_message
       │
       ▼
┌─────────────┐
│   AUDIT     │  1. Log failure event
│    LOG      │  2. Include error details
└──────┬──────┘  3. Record for debugging
       │
       ▼
┌─────────────┐
│  PROPAGATE  │  Re-raise exception
│   ERROR     │  API returns appropriate error
└─────────────┘  response (4xx or 5xx)
```

---

## Error Handling

### Domain Exceptions

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `TaskNotFoundError` | 404 | Task ID doesn't exist or is deleted |
| `PermissionDeniedError` | 403 | User doesn't own task (non-admin) |
| `ValidationError` | 400 | Invalid cron expression, report format, etc. |
| `SessionNotActiveError` | 409 | Session in invalid state for execution |

### API Error Responses

**404 Not Found**:
```json
{
  "detail": "Task 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**403 Forbidden**:
```json
{
  "detail": "Not authorized to access this task"
}
```

**400 Bad Request**:
```json
{
  "detail": "Invalid cron expression: 0 0 32 * *"
}
```

**409 Conflict**:
```json
{
  "detail": "Task is not active"
}
```

### Execution Failure States

When a task execution fails:
1. Execution status set to `FAILED`
2. Error message captured in `execution.error_message`
3. Session status set to `FAILED` (if session was created)
4. Audit log records failure with details
5. No report generated (even if configured)

---

## Examples

### Example 1: Simple Monitoring Task

**Create Task**:
```bash
POST /api/v1/tasks
Authorization: Bearer {token}

{
  "name": "Check Server Status",
  "prompt_template": "Check the status of server {hostname}",
  "allowed_tools": ["*"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

**Execute Task**:
```bash
POST /api/v1/tasks/{task_id}/execute
Authorization: Bearer {token}

{
  "variables": {
    "hostname": "api.example.com"
  }
}
```

Claude receives: "Check the status of server api.example.com"

---

### Example 2: Scheduled Report Task

**Create Task**:
```bash
POST /api/v1/tasks

{
  "name": "Daily Database Report",
  "description": "Generate daily database metrics report",
  "prompt_template": "Analyze database performance for {date} and provide recommendations",
  "allowed_tools": ["database_*"],
  "is_scheduled": true,
  "schedule_cron": "0 8 * * *",
  "schedule_enabled": true,
  "generate_report": true,
  "report_format": "html",
  "tags": ["database", "daily", "reports"]
}
```

This task will:
- Run automatically every day at 8:00 AM
- Execute with `{date}` filled in by scheduler
- Generate an HTML report after completion
- Be tagged for easy filtering

---

### Example 3: Multi-Tool Task with MCP

**Create Task**:
```bash
POST /api/v1/tasks

{
  "name": "Infrastructure Audit",
  "prompt_template": "Perform complete infrastructure audit for {environment}. Check:\n1. Kubernetes cluster health\n2. Database connections\n3. Monitoring alerts",
  "allowed_tools": ["kubernetes_*", "database_*", "monitoring_*"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 8192
  },
  "generate_report": true,
  "report_format": "pdf",
  "tags": ["infrastructure", "audit"]
}
```

**Execute**:
```bash
POST /api/v1/tasks/{task_id}/execute

{
  "variables": {
    "environment": "production"
  }
}
```

During execution, Claude will:
1. Use Kubernetes MCP tools to check cluster
2. Use Database MCP tools to check connections
3. Use Monitoring MCP tools to check alerts
4. Compile findings into comprehensive report
5. Generate PDF report automatically

---

### Example 4: Check Execution Status

```bash
# Get execution status
GET /api/v1/task-executions/{execution_id}
Authorization: Bearer {token}

# Response shows progress
{
  "status": "running",
  "started_at": "2025-10-20T12:00:01Z",
  "session_id": "...",
  "_links": {
    "session": "/api/v1/sessions/..."
  }
}

# Poll or check session for live updates
# Or use WebSocket connection to session for real-time updates
```

---

### Example 5: List Task Execution History

```bash
GET /api/v1/tasks/{task_id}/executions?page=1&page_size=10
Authorization: Bearer {token}

# Response
{
  "items": [
    {
      "id": "...",
      "status": "completed",
      "trigger_type": "scheduled",
      "duration_ms": 25000,
      "completed_at": "2025-10-20T08:00:25Z"
    },
    {
      "id": "...",
      "status": "failed",
      "trigger_type": "manual",
      "error_message": "Database connection timeout",
      "completed_at": "2025-10-19T15:30:10Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10
}
```

---

## Integration Points

### With Sessions API
- Each task execution creates a dedicated AI session
- Session ID is tracked in `execution.session_id`
- Session contains full conversation history
- Can access session WebSocket for real-time updates

### With Reports API
- Auto-generated reports linked via `execution.report_id`
- Reports aggregate session messages, tool calls, metrics
- Multiple format options: JSON, HTML, Markdown, PDF
- Reports accessible via `/api/v1/reports/{report_id}`

### With Audit Logs
- All task operations audited:
  - `task.created`
  - `task.updated`
  - `task.deleted`
  - `task.executed` (with success/failure)
- Audit logs include user, timestamp, details
- Used for compliance and debugging

### With MCP Servers
- Tasks can use MCP tools via `sdk_options`
- SDK tools automatically included (kubernetes, database, monitoring)
- User's personal MCP servers also available
- Tool access controlled via `allowed_tools` patterns

---

## Best Practices

### Task Design
1. **Keep prompts focused**: Each task should have single, clear purpose
2. **Use descriptive names**: Makes filtering and management easier
3. **Limit tool access**: Only allow tools needed for the task
4. **Test before scheduling**: Execute manually first to verify behavior
5. **Add tags**: Organize tasks by category, team, or purpose

### Variable Usage
1. **Document variables**: In description or comments
2. **Provide defaults**: In `default_variables` for common cases
3. **Validate input**: Ensure variables are provided when executing
4. **Use clear names**: `{environment}` not `{env}`, `{hostname}` not `{h}`

### Scheduling
1. **Use UTC times**: Cron expressions in UTC timezone
2. **Avoid overlaps**: Ensure task duration < schedule interval
3. **Monitor failures**: Set up alerts for failed scheduled tasks
4. **Test schedules**: Use cron validation tools before deployment

### Error Handling
1. **Check execution status**: Poll or use WebSocket for updates
2. **Review failed executions**: Check `error_message` field
3. **Access session logs**: Use session API for detailed debugging
4. **Set up notifications**: Configure alerts for failures

### Report Generation
1. **Choose appropriate format**: HTML for viewing, JSON for processing
2. **Consider file size**: PDF generation can be resource-intensive
3. **Tag reports**: Use same tags as task for easy finding
4. **Archive old reports**: Implement retention policies

---

## Security Considerations

### Authentication & Authorization
- All endpoints require valid JWT bearer token
- Users can only access their own tasks (unless admin)
- Task ownership verified on every operation
- Audit logs track all access attempts

### Tool Access Control
- `allowed_tools` and `disallowed_tools` enforce permissions
- Pattern matching supports wildcards: `kubernetes_*`
- Permissions evaluated during SDK client setup
- Permission decisions logged for audit

### Data Isolation
- Tasks scoped to user_id
- Executions inherit task ownership
- Sessions created with task owner's permissions
- Working directories isolated per session

### Rate Limiting
- Consider rate limits on task execution endpoint
- Prevent abuse of automated execution
- Monitor execution frequency per user
- Track resource usage via metrics

---

## Monitoring & Observability

### Metrics to Track
- Task execution count (by status, trigger type)
- Execution duration (average, percentiles)
- Failure rate per task
- Report generation success rate
- Tool usage during execution

### Logging
- All operations logged with structured data
- Execution lifecycle events tracked
- Error messages and stack traces captured
- Performance metrics recorded

### Audit Trail
- Complete audit log of all operations
- Includes user, timestamp, action, result
- Queryable for compliance and investigation
- Retention policies configurable

---

## Troubleshooting

### Common Issues

**Task Execution Fails Immediately**
- Check task.is_active = true
- Verify cron expression if scheduled
- Check tool permissions in allowed_tools
- Review SDK options configuration

**Session Creation Fails**
- Check user quotas and limits
- Verify MCP server configurations
- Check working directory permissions
- Review session service logs

**Report Generation Fails**
- Verify report_format is valid
- Check storage permissions
- Ensure session completed successfully
- Review ReportService logs

**Scheduled Tasks Not Running**
- Verify schedule_enabled = true
- Check cron expression validity
- Ensure scheduler service is running
- Review scheduler logs

### Debug Steps

1. **Check Execution Status**
   ```bash
   GET /api/v1/task-executions/{id}
   ```

2. **Review Session Logs**
   ```bash
   GET /api/v1/sessions/{session_id}/messages
   ```

3. **Check Audit Logs**
   ```bash
   GET /api/v1/admin/audit-logs?resource_type=task&resource_id={task_id}
   ```

4. **Verify Task Configuration**
   ```bash
   GET /api/v1/tasks/{task_id}
   ```

---

## Future Enhancements

### Planned Features
- **Webhook triggers**: Execute tasks via external webhooks
- **Task dependencies**: Chain tasks together
- **Conditional execution**: Skip based on previous results
- **Custom notification channels**: Email, Slack, etc.
- **Task templates**: Predefined task configurations
- **Execution replay**: Re-run with same parameters
- **Advanced scheduling**: Skip holidays, business hours only
- **Resource limits**: Per-task timeout, token limits

---

## Conclusion

The Tasks API provides a powerful framework for automating AI agent workflows. By combining template-based prompts, flexible scheduling, comprehensive reporting, and deep integration with the session and MCP systems, developers can create sophisticated automated solutions.

Key takeaways:
- Tasks are reusable templates for agent workflows
- Executions are tracked with full lifecycle management
- Integration with sessions enables powerful AI capabilities
- Reports provide actionable insights from executions
- Comprehensive audit logging ensures accountability

For more information, see:
- [Sessions API Documentation](./sessions.md)
- [Reports API Documentation](../apis/reports/)
- [MCP Integration Guide](../components/mcp-integration.md)
- [API Inventory](../apis/api-inventory.md)

