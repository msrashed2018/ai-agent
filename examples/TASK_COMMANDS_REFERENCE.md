# Task Commands - Complete Reference with Curl Equivalents

This document shows all task management commands with their parameters and backend API calls.

**Table of Contents:**
1. [Authentication Setup](#authentication-setup)
2. [Create Task](#create-task-post-apiv1tasks)
3. [List Tasks](#list-tasks-get-apiv1tasks)
4. [Get Task Details](#get-task-details-get-apiv1taskstask_id)
5. [Update Task](#update-task-patch-apiv1taskstask_id)
6. [Delete Task](#delete-task-delete-apiv1taskstask_id)
7. [Execute Task](#execute-task-post-apiv1taskstask_idexecute)
8. [Get Execution Status](#get-execution-status-get-apiv1tasksexecutionsexecution_id)
9. [List Executions](#list-executions-get-apiv1taskstask_idexecutions)
10. [Retry Execution](#retry-execution-post-apiv1tasksexecutionsexecution_idretry)

---

## Authentication Setup

Before running any commands, you need to authenticate and get a token.

### Login Command

```bash
ai-agent auth login --email user@example.com --password yourpassword
```

### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "user",
    "role": "user"
  }
}
```

### Get Current User

```bash
ai-agent auth whoami
```

### Backend API Call (Curl)

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## CREATE TASK - `POST /api/v1/tasks`

### 1. Minimal Task Creation

#### CLI Command

```bash
ai-agent tasks create \
  --name "Simple Task" \
  --prompt-template "Hello {name}"
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Simple Task",
    "prompt_template": "Hello {name}",
    "allowed_tools": [],
    "sdk_options": {},
    "is_scheduled": false,
    "schedule_enabled": false,
    "generate_report": false,
    "tags": []
  }'
```

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Simple Task",
  "description": null,
  "prompt_template": "Hello {name}",
  "allowed_tools": [],
  "is_scheduled": false,
  "schedule_cron": null,
  "schedule_enabled": false,
  "generate_report": false,
  "report_format": null,
  "tags": [],
  "created_at": "2025-10-25T10:00:00Z",
  "updated_at": "2025-10-25T10:00:00Z",
  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute",
    "executions": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions"
  }
}
```

---

### 2. Task with Description

#### CLI Command

```bash
ai-agent tasks create \
  --name "Analytics Task" \
  --description "Analyzes deployment metrics and generates insights" \
  --prompt-template "Analyze {metric_type} for {environment}"
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Analytics Task",
    "description": "Analyzes deployment metrics and generates insights",
    "prompt_template": "Analyze {metric_type} for {environment}",
    "allowed_tools": [],
    "sdk_options": {},
    "is_scheduled": false,
    "schedule_enabled": false,
    "generate_report": false,
    "tags": []
  }'
```

---

### 3. Task with Tool Access Control

#### CLI Command

```bash
ai-agent tasks create \
  --name "Cloud Operations" \
  --prompt-template "Deploy {service} to {region}" \
  --allowed-tools "kubernetes" "aws-cli" "terraform" "helm"
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Cloud Operations",
    "prompt_template": "Deploy {service} to {region}",
    "allowed_tools": ["kubernetes", "aws-cli", "terraform", "helm"],
    "sdk_options": {},
    "is_scheduled": false,
    "schedule_enabled": false,
    "generate_report": false,
    "tags": []
  }'
```

---

### 4. Scheduled Task (Cron-based)

#### CLI Command

```bash
ai-agent tasks create \
  --name "Daily Health Check" \
  --prompt-template "Run health check for {environment}" \
  --is-scheduled \
  --schedule-cron "0 9 * * *" \
  --schedule-enabled
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Daily Health Check",
    "prompt_template": "Run health check for {environment}",
    "allowed_tools": [],
    "sdk_options": {},
    "is_scheduled": true,
    "schedule_cron": "0 9 * * *",
    "schedule_enabled": true,
    "generate_report": false,
    "tags": []
  }'
```

**Cron Examples:**
```
"0 9 * * *"           - Every day at 9:00 AM
"0 */6 * * *"         - Every 6 hours
"0 0 * * 0"           - Every Sunday at midnight
"0 0 1 * *"           - First day of every month
"*/15 * * * *"        - Every 15 minutes
"0 9-17 * * 1-5"      - Every hour 9 AM-5 PM, Monday-Friday
```

---

### 5. Task with Report Generation

#### CLI Command

```bash
ai-agent tasks create \
  --name "Compliance Report" \
  --prompt-template "Generate compliance report for {region}" \
  --generate-report \
  --report-format html
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Compliance Report",
    "prompt_template": "Generate compliance report for {region}",
    "allowed_tools": [],
    "sdk_options": {},
    "is_scheduled": false,
    "schedule_enabled": false,
    "generate_report": true,
    "report_format": "html",
    "tags": []
  }'
```

**Report Formats Available:**
- `html` - HTML report
- `pdf` - PDF document (requires WeasyPrint)
- `json` - JSON structured data
- `markdown` - Markdown format

---

### 6. Task with SDK Options

#### CLI Command

```bash
ai-agent tasks create \
  --name "Advanced AI Task" \
  --prompt-template "Analyze {data_set} with {model}" \
  --allowed-tools "python" "pandas" "jupyter"
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Advanced AI Task",
    "prompt_template": "Analyze {data_set} with {model}",
    "allowed_tools": ["python", "pandas", "jupyter"],
    "sdk_options": {
      "model": "claude-3-5-sonnet-20241022",
      "max_turns": 15,
      "permission_mode": "acceptEdits"
    },
    "is_scheduled": false,
    "schedule_enabled": false,
    "generate_report": false,
    "tags": []
  }'
```

**SDK Options Available:**
```json
{
  "model": "claude-3-5-sonnet-20241022",        // Claude model to use
  "max_turns": 10,                              // Max conversation turns (default: 10)
  "permission_mode": "acceptEdits",             // acceptEdits, askUser, rejectEdits
  "cwd": "/path/to/working/directory"           // Working directory for operations
}
```

---

### 7. Complete Task with All Parameters

#### CLI Command

```bash
ai-agent tasks create \
  --name "Production Deployment Validator" \
  --description "Validates and deploys services to production environment" \
  --prompt-template "Deploy {service} to {environment} with config {config_type}" \
  --allowed-tools "kubernetes" "aws-cli" "terraform" "helm" "docker" \
  --is-scheduled \
  --schedule-cron "0 */6 * * *" \
  --schedule-enabled \
  --generate-report \
  --report-format pdf \
  --tags "deployment" "production" "critical" "automation"
```

#### Backend API Call (Curl)

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Production Deployment Validator",
    "description": "Validates and deploys services to production environment",
    "prompt_template": "Deploy {service} to {environment} with config {config_type}",
    "allowed_tools": [
      "kubernetes",
      "aws-cli",
      "terraform",
      "helm",
      "docker"
    ],
    "sdk_options": {
      "model": "claude-3-5-sonnet-20241022",
      "max_turns": 20,
      "permission_mode": "acceptEdits"
    },
    "is_scheduled": true,
    "schedule_cron": "0 */6 * * *",
    "schedule_enabled": true,
    "generate_report": true,
    "report_format": "pdf",
    "tags": ["deployment", "production", "critical", "automation"]
  }'
```

---

## LIST TASKS - `GET /api/v1/tasks`

### 1. List All Tasks

#### CLI Command

```bash
ai-agent tasks list --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Simple Task",
      "description": null,
      "prompt_template": "Hello {name}",
      "allowed_tools": [],
      "is_scheduled": false,
      "schedule_cron": null,
      "schedule_enabled": false,
      "generate_report": false,
      "report_format": null,
      "tags": [],
      "created_at": "2025-10-25T10:00:00Z",
      "updated_at": "2025-10-25T10:00:00Z",
      "_links": {
        "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
        "execute": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute"
      }
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "_links": {
    "self": "/api/v1/tasks?page=1&page_size=20",
    "first": "/api/v1/tasks?page=1&page_size=20",
    "last": "/api/v1/tasks?page=1&page_size=20"
  }
}
```

---

### 2. List with Pagination

#### CLI Command

```bash
ai-agent tasks list --page 2 --page-size 10 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks?page=2&page_size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 3. Filter by Scheduled Status

#### CLI Command

```bash
ai-agent tasks list --is-scheduled true --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks?is_scheduled=true&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 4. Filter by Tags

#### CLI Command

```bash
ai-agent tasks list --tags "production" "critical" --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks?tags=production&tags=critical&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 5. List in Table Format

#### CLI Command

```bash
ai-agent tasks list --format table
```

**Output:**
```
┌────────────────────────────────────────────────────────────┐
│ Tasks                                                      │
├──────────────┬─────────────────────┬──────────┬────────────┤
│ ID           │ Name                │ Tags     │ Created    │
├──────────────┼─────────────────────┼──────────┼────────────┤
│ 550e8400...  │ Simple Task         │          │ 2025-10-25 │
│ 660e8400...  │ Daily Health Check  │ health   │ 2025-10-25 │
│ 770e8400...  │ Compliance Report   │ audit    │ 2025-10-25 │
└──────────────┴─────────────────────┴──────────┴────────────┘
```

---

## GET TASK DETAILS - `GET /api/v1/tasks/{task_id}`

### 1. Get Task by ID

#### CLI Command

```bash
ai-agent tasks get 550e8400-e29b-41d4-a716-446655440000 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Simple Task",
  "description": null,
  "prompt_template": "Hello {name}",
  "allowed_tools": [],
  "disallowed_tools": [],
  "sdk_options": {},
  "is_scheduled": false,
  "schedule_cron": null,
  "schedule_enabled": false,
  "generate_report": false,
  "report_format": null,
  "notification_config": null,
  "tags": [],
  "is_public": false,
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

---

### 2. Get Task in Table Format

#### CLI Command

```bash
ai-agent tasks get 550e8400-e29b-41d4-a716-446655440000 --format table
```

**Output:**
```
┌─────────────────────┬────────────────────────────────────┐
│ Task Details        │ 550e8400-e29b-41d4-a716-446655440  │
├─────────────────────┼────────────────────────────────────┤
│ Name                │ Simple Task                        │
│ Description         │ None                               │
│ Prompt Template     │ Hello {name}                       │
│ Allowed Tools       │ []                                 │
│ Is Scheduled        │ False                              │
│ Schedule Cron       │ None                               │
│ Schedule Enabled    │ False                              │
│ Generate Report     │ False                              │
│ Tags                │ []                                 │
│ Active              │ True                               │
│ Created             │ 2025-10-25T10:00:00Z               │
│ Updated             │ 2025-10-25T10:00:00Z               │
└─────────────────────┴────────────────────────────────────┘
```

---

### 3. Error Case - Task Not Found

#### Response (404 Not Found)

```json
{
  "detail": "Task 550e8400-e29b-41d4-a716-446655440999 not found"
}
```

---

## UPDATE TASK - `PATCH /api/v1/tasks/{task_id}`

### 1. Update Task Name

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --name "Updated Task Name" \
  --format json
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Updated Task Name"
  }'
```

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Task Name",
  "prompt_template": "Hello {name}",
  "updated_at": "2025-10-25T11:30:00Z",
  "...": "...other fields..."
}
```

---

### 2. Update Prompt Template

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --prompt-template "Updated: Analyze {service} status on {date}" \
  --format json
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "prompt_template": "Updated: Analyze {service} status on {date}"
  }'
```

---

### 3. Update Description

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --description "This task analyzes service status and generates reports"
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "description": "This task analyzes service status and generates reports"
  }'
```

---

### 4. Enable Report Generation

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --generate-report true
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "generate_report": true,
    "report_format": "pdf"
  }'
```

---

### 5. Update Scheduling

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --schedule-enabled true
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "schedule_enabled": true
  }'
```

---

### 6. Update Multiple Fields

#### CLI Command

```bash
ai-agent tasks update 550e8400-e29b-41d4-a716-446655440000 \
  --name "Production Health Check" \
  --description "Daily health check for production" \
  --schedule-enabled true
```

#### Backend API Call (Curl)

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Production Health Check",
    "description": "Daily health check for production",
    "schedule_enabled": true
  }'
```

---

## DELETE TASK - `DELETE /api/v1/tasks/{task_id}`

### 1. Delete Task with Confirmation

#### CLI Command

```bash
ai-agent tasks delete 550e8400-e29b-41d4-a716-446655440000
```

**Output:**
```
Are you sure you want to delete task 550e8400-e29b-41d4-a716-446655440000? [y/N]: y
Task 550e8400-e29b-41d4-a716-446655440000 deleted
```

#### Backend API Call (Curl)

```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (204 No Content)

```
(Empty response)
```

---

### 2. Delete Task without Confirmation

#### CLI Command

```bash
ai-agent tasks delete 550e8400-e29b-41d4-a716-446655440000 --yes
```

---

### 3. Error Case - Unauthorized Delete

#### Response (403 Forbidden)

```json
{
  "detail": "Not authorized to delete this task"
}
```

---

## EXECUTE TASK - `POST /api/v1/tasks/{task_id}/execute`

### 1. Simple Execution

#### CLI Command

```bash
ai-agent tasks execute 550e8400-e29b-41d4-a716-446655440000 --format json
```

#### Backend API Call (Curl)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "variables": {}
  }'
```

#### Response (202 Accepted)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": null,
  "report_id": null,
  "trigger_type": "manual",
  "status": "running",
  "prompt_variables": {},
  "result_data": {},
  "error_message": null,
  "created_at": "2025-10-25T11:45:00Z",
  "started_at": "2025-10-25T11:45:00Z",
  "completed_at": null,
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

### 2. Execute with Single Variable

#### CLI Command

```bash
ai-agent tasks execute 550e8400-e29b-41d4-a716-446655440000 \
  --variables '{"name": "World"}' \
  --format json
```

#### Backend API Call (Curl)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "variables": {
      "name": "World"
    }
  }'
```

---

### 3. Execute with Multiple Variables

#### CLI Command

```bash
ai-agent tasks execute 550e8400-e29b-41d4-a716-446655440000 \
  --variables '{
    "environment": "production",
    "service": "api-gateway",
    "region": "us-east-1",
    "timeout": 300
  }' \
  --format json
```

#### Backend API Call (Curl)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "variables": {
      "environment": "production",
      "service": "api-gateway",
      "region": "us-east-1",
      "timeout": 300
    }
  }'
```

---

### 4. Execute with Complex Variables

#### CLI Command

```bash
ai-agent tasks execute 550e8400-e29b-41d4-a716-446655440000 \
  --variables '{
    "services": ["api", "web", "worker"],
    "config": {
      "replicas": 3,
      "cpu": "500m",
      "memory": "512Mi"
    },
    "tags": ["production", "critical"]
  }' \
  --format json
```

#### Backend API Call (Curl)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "variables": {
      "services": ["api", "web", "worker"],
      "config": {
        "replicas": 3,
        "cpu": "500m",
        "memory": "512Mi"
      },
      "tags": ["production", "critical"]
    }
  }'
```

---

### 5. Error Case - Task Not Found

#### Response (404 Not Found)

```json
{
  "detail": "Task 550e8400-e29b-41d4-a716-446655440999 not found"
}
```

---

### 6. Error Case - Unauthorized Execution

#### Response (403 Forbidden)

```json
{
  "detail": "Not authorized to execute this task"
}
```

---

## GET EXECUTION STATUS - `GET /api/v1/tasks/executions/{execution_id}`

### 1. Get Execution Status (Running)

#### CLI Command

```bash
ai-agent tasks execution-status 660e8400-e29b-41d4-a716-446655440111 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/executions/660e8400-e29b-41d4-a716-446655440111" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (200 OK) - While Running

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "880e8400-e29b-41d4-a716-446655440222",
  "report_id": null,
  "trigger_type": "manual",
  "status": "running",
  "prompt_variables": {"name": "World"},
  "result_data": {},
  "error_message": null,
  "created_at": "2025-10-25T11:45:00Z",
  "started_at": "2025-10-25T11:45:00Z",
  "completed_at": null,
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "session": "/api/v1/sessions/880e8400-e29b-41d4-a716-446655440222"
  }
}
```

---

### 2. Get Execution Status (Completed)

#### CLI Command

```bash
ai-agent tasks execution-status 660e8400-e29b-41d4-a716-446655440111 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/executions/660e8400-e29b-41d4-a716-446655440111" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (200 OK) - Completed

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "880e8400-e29b-41d4-a716-446655440222",
  "report_id": "990e8400-e29b-41d4-a716-446655440333",
  "trigger_type": "manual",
  "status": "completed",
  "prompt_variables": {"name": "World"},
  "result_data": {
    "final_text": "Hello World! The task has completed successfully.",
    "total_messages": 3,
    "total_tool_uses": 1,
    "duration_ms": 45000,
    "cost_usd": 0.12,
    "num_turns": 2,
    "working_dir": "/tmp/agent-workdirs/active/550e8400-e29b-41d4-a716-446655440000"
  },
  "error_message": null,
  "created_at": "2025-10-25T11:45:00Z",
  "started_at": "2025-10-25T11:45:00Z",
  "completed_at": "2025-10-25T11:45:45Z",
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000",
    "session": "/api/v1/sessions/880e8400-e29b-41d4-a716-446655440222",
    "report": "/api/v1/reports/990e8400-e29b-41d4-a716-446655440333"
  }
}
```

---

### 3. Get Execution Status (Failed)

#### Response (200 OK) - Failed

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "880e8400-e29b-41d4-a716-446655440222",
  "report_id": null,
  "trigger_type": "manual",
  "status": "failed",
  "prompt_variables": {"name": "World"},
  "result_data": {},
  "error_message": "Claude API returned error: Context length exceeded. Max tokens: 4096, Requested: 5000",
  "created_at": "2025-10-25T11:45:00Z",
  "started_at": "2025-10-25T11:45:00Z",
  "completed_at": "2025-10-25T11:46:15Z",
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

### 4. In Table Format

#### CLI Command

```bash
ai-agent tasks execution-status 660e8400-e29b-41d4-a716-446655440111 --format table
```

**Output:**
```
┌─────────────────────┬──────────────────────────────────────┐
│ Execution Status    │ 660e8400-e29b-41d4-a716-446655440111 │
├─────────────────────┼──────────────────────────────────────┤
│ Task ID             │ 550e8400-e29b-41d4-a716-446655440000 │
│ Status              │ completed                            │
│ Trigger Type        │ manual                               │
│ Created             │ 2025-10-25T11:45:00Z                 │
│ Started             │ 2025-10-25T11:45:00Z                 │
│ Completed           │ 2025-10-25T11:45:45Z                 │
│ Duration (ms)       │ 45000                                │
│ Messages            │ 3                                    │
│ Tool Uses           │ 1                                    │
│ Cost (USD)          │ 0.12                                 │
│ Result              │ Hello World! The task has comple...  │
└─────────────────────┴──────────────────────────────────────┘
```

---

## LIST EXECUTIONS - `GET /api/v1/tasks/{task_id}/executions`

### 1. List All Executions for a Task

#### CLI Command

```bash
ai-agent tasks executions 550e8400-e29b-41d4-a716-446655440000 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440111",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "trigger_type": "manual",
      "created_at": "2025-10-25T11:45:00Z",
      "started_at": "2025-10-25T11:45:00Z",
      "completed_at": "2025-10-25T11:45:45Z",
      "_links": {
        "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
        "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
      }
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440222",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "trigger_type": "scheduled",
      "created_at": "2025-10-24T09:00:00Z",
      "started_at": "2025-10-24T09:00:00Z",
      "completed_at": "2025-10-24T09:01:30Z",
      "_links": {
        "self": "/api/v1/task-executions/770e8400-e29b-41d4-a716-446655440222",
        "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
      }
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "_links": {
    "self": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=1&page_size=20",
    "first": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=1&page_size=20",
    "last": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=1&page_size=20"
  }
}
```

---

### 2. List with Pagination

#### CLI Command

```bash
ai-agent tasks executions 550e8400-e29b-41d4-a716-446655440000 \
  --page 2 --page-size 10 --format json
```

#### Backend API Call (Curl)

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=2&page_size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 3. List in Table Format

#### CLI Command

```bash
ai-agent tasks executions 550e8400-e29b-41d4-a716-446655440000 --format table
```

**Output:**
```
┌────────────────────────────────────────────────────────────────┐
│ Executions for Task 550e8400-e29b-41d4-a716-446655440000       │
├──────────────┬──────────┬────────────┬────────────────────┬─────┤
│ ID           │ Status   │ Type       │ Started            │ Dur │
├──────────────┼──────────┼────────────┼────────────────────┼─────┤
│ 660e8400...  │ completed│ manual     │ 2025-10-25 11:45   │ 45s │
│ 770e8400...  │ completed│ scheduled  │ 2025-10-24 09:00   │ 90s │
│ 880e8400...  │ failed   │ manual     │ 2025-10-24 15:30   │ 120s│
└──────────────┴──────────┴────────────┴────────────────────┴─────┘
```

---

## RETRY EXECUTION - `POST /api/v1/tasks/executions/{execution_id}/retry`

### 1. Retry Failed Execution

#### CLI Command

```bash
# Note: No CLI command yet - use curl directly
```

#### Backend API Call (Curl)

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/executions/660e8400-e29b-41d4-a716-446655440111/retry" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{}'
```

#### Response (202 Accepted)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "trigger_type": "manual",
  "created_at": "2025-10-25T11:45:00Z",
  "started_at": "2025-10-25T11:50:00Z",
  "retry_count": 1,
  "_links": {
    "self": "/api/v1/task-executions/660e8400-e29b-41d4-a716-446655440111",
    "task": "/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

### 2. Error Case - Cannot Retry Completed Execution

#### Response (400 Bad Request)

```json
{
  "detail": "Cannot retry execution with status 'completed'. Only queued, pending, or failed executions can be retried."
}
```

---

## Execution Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

                           ┌──────────────┐
                           │  Task API    │
                           │ POST /execute│
                           └──────┬───────┘
                                  │
                                  ↓
                          ┌─────────────────┐
                          │ Create Execution │
                          │ Status: PENDING  │
                          └────────┬────────┘
                                   │
                                   ↓
                          ┌─────────────────┐
                          │ Update Status   │
                          │ Status: RUNNING │
                          └────────┬────────┘
                                   │
                    ┌──────────────┬──────────────┐
                    │              │              │
                    ↓              ↓              ↓
            ┌──────────────┐ ┌──────────┐ ┌──────────────┐
            │  Render      │ │ Execute  │ │ Alternative │
            │  Prompt      │ │ with SDK │ │ Path: Manual│
            │  Template    │ │          │ │ Cancellation│
            └──────┬───────┘ └────┬─────┘ └──────┬───────┘
                   │              │              │
                   └──────────┬───┴─────┬────────┘
                              │         │
                       ┌──────┴──┐   ┌──┴───────┐
                       │         │   │          │
                       ↓         ↓   ↓          ↓
            ┌───────────────┐ ┌──────────┐ ┌─────────┐
            │  COMPLETED    │ │  FAILED  │ │CANCELLED│
            │ Update with   │ │ Update   │ │ Status: │
            │ results & cost│ │ with err │ │CANCELLED│
            └───────────────┘ └──────────┘ └─────────┘
                   │
                   ↓
            ┌──────────────────┐
            │ Generate Report  │
            │ (if configured)  │
            └──────────────────┘
```

---

## Common Patterns

### Pattern 1: Create → Execute → Monitor

```bash
#!/bin/bash

# 1. Create task
TASK=$(ai-agent tasks create \
  --name "Daily Check" \
  --prompt-template "Check {environment}" \
  --format json)

TASK_ID=$(echo $TASK | jq -r '.id')
echo "Created task: $TASK_ID"

# 2. Execute task
EXEC=$(ai-agent tasks execute $TASK_ID \
  --variables '{"environment": "prod"}' \
  --format json)

EXEC_ID=$(echo $EXEC | jq -r '.id')
echo "Execution started: $EXEC_ID"

# 3. Monitor execution
for i in {1..60}; do
  STATUS=$(ai-agent tasks execution-status $EXEC_ID --format json | jq -r '.status')

  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    echo "Execution $STATUS"
    ai-agent tasks execution-status $EXEC_ID --format json | jq '.result_data'
    break
  fi

  echo "Status: $STATUS (attempt $i/60)"
  sleep 2
done
```

---

### Pattern 2: Scheduled Task Setup

```bash
# Create scheduled task that runs daily at 9 AM
ai-agent tasks create \
  --name "Production Health Check" \
  --prompt-template "Run health check for {environment}" \
  --is-scheduled \
  --schedule-cron "0 9 * * *" \
  --schedule-enabled \
  --tags "health-check" "production" \
  --format json
```

---

### Pattern 3: Batch Execution with Variables

```bash
#!/bin/bash

TASK_ID="550e8400-e29b-41d4-a716-446655440000"

for env in prod staging dev; do
  echo "Executing for $env..."

  EXEC=$(ai-agent tasks execute $TASK_ID \
    --variables "{\"environment\": \"$env\"}" \
    --format json)

  EXEC_ID=$(echo $EXEC | jq -r '.id')
  echo "  Execution: $EXEC_ID"
done

echo "All executions started. Monitor with: ai-agent tasks execution-status <id>"
```

---

## Variable Substitution Examples

**Prompt Template:**
```
Deploy {service} to {environment} using {deployment_type} strategy
```

**Variables:**
```json
{
  "service": "api-gateway",
  "environment": "production",
  "deployment_type": "blue-green"
}
```

**Result:**
```
Deploy api-gateway to production using blue-green strategy
```

---

## Status Codes Reference

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Task retrieved successfully |
| 201 | Created | Task created |
| 202 | Accepted | Execution started (async) |
| 204 | No Content | Task deleted |
| 400 | Bad Request | Invalid variables JSON |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Not task owner |
| 404 | Not Found | Task/execution doesn't exist |
| 422 | Unprocessable Entity | Invalid field values |
| 500 | Server Error | Backend error |

---

**End of Reference Document**

For more help, run:
```bash
ai-agent tasks --help
ai-agent tasks create --help
ai-agent tasks execute --help
```
