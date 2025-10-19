# REST API Endpoints

## Purpose

Complete reference for all REST API endpoints in the AI-Agent-API service. Use this document to understand available operations, request/response formats, and authentication requirements.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## API Version

All endpoints are under `/api/v1/`

## Authentication

Most endpoints require **JWT Bearer Token** authentication.

**Header Format**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Obtaining Token**: Use the `/api/v1/auth/login` endpoint.

---

## Endpoint Categories

1. [Authentication](#authentication-endpoints) - Login, token management
2. [Sessions](#session-endpoints) - Session CRUD and query execution
3. [Session Templates](#session-template-endpoints) - Reusable session configs
4. [Tasks](#task-endpoints) - Automated task management
5. [Reports](#report-endpoints) - Report generation
6. [MCP Servers](#mcp-server-endpoints) - MCP server management
7. [Admin](#admin-endpoints) - Admin operations
8. [Monitoring](#monitoring-endpoints) - Health and metrics

---

## Authentication Endpoints

### POST /api/v1/auth/login

**Purpose**: Authenticate user and obtain JWT token

**File**: [auth.py](../../app/api/v1/auth.py)

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors**:
- `401`: Invalid credentials
- `403`: Account disabled

---

### POST /api/v1/auth/register

**Purpose**: Register new user account

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "secret123",
  "full_name": "John Doe"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

### POST /api/v1/auth/refresh

**Purpose**: Refresh access token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:
```json
{
  "access_token": "new_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Session Endpoints

### POST /api/v1/sessions

**Purpose**: Create a new Claude Code session

**File**: [sessions.py:56-100](../../app/api/v1/sessions.py:56-100)

**Authentication**: Required

**Request Body**:
```json
{
  "name": "My Investigation Session",
  "mode": "interactive",
  "sdk_options": {
    "allowed_tools": ["Read", "Write", "Bash"],
    "permission_mode": "default"
  },
  "template_id": "uuid" // Optional
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "My Investigation Session",
  "mode": "interactive",
  "status": "created",
  "sdk_options": {...},
  "working_directory_path": "/tmp/ai-agent-service/sessions/uuid",
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/sessions

**Purpose**: List user's sessions

**Authentication**: Required

**Query Parameters**:
- `skip`: int (default: 0) - Pagination offset
- `limit`: int (default: 100, max: 100) - Page size
- `status`: string - Filter by status
- `mode`: string - Filter by mode

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Session 1",
      "status": "active",
      "mode": "interactive",
      "created_at": "2025-10-19T12:00:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

---

### GET /api/v1/sessions/{session_id}

**Purpose**: Get session details

**Authentication**: Required

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "name": "My Session",
  "status": "active",
  "mode": "interactive",
  "total_messages": 15,
  "total_tool_calls": 8,
  "total_cost_usd": 0.0523,
  "api_input_tokens": 1200,
  "api_output_tokens": 850,
  "created_at": "2025-10-19T12:00:00Z",
  "started_at": "2025-10-19T12:01:00Z"
}
```

---

### POST /api/v1/sessions/{session_id}/query

**Purpose**: Execute query in a session

**File**: [sessions.py](../../app/api/v1/sessions.py)

**Authentication**: Required

**Request Body**:
```json
{
  "message": "Analyze the error logs in /var/log/app.log"
}
```

**Response (200 OK)**:
```json
{
  "session_id": "uuid",
  "message_id": "uuid",
  "content": {
    "type": "text",
    "text": "I'll analyze the error logs for you..."
  },
  "tool_calls": [
    {
      "tool_name": "Read",
      "tool_input": {"path": "/var/log/app.log"},
      "status": "success"
    }
  ],
  "metrics": {
    "duration_ms": 3250,
    "input_tokens": 150,
    "output_tokens": 420,
    "cost_usd": 0.0012
  }
}
```

---

### POST /api/v1/sessions/{session_id}/fork

**Purpose**: Fork (clone) a session

**File**: [sessions.py](../../app/api/v1/sessions.py)

**Authentication**: Required

**Request Body**:
```json
{
  "name": "Forked Session"
}
```

**Response (201 Created)**:
```json
{
  "id": "new_uuid",
  "parent_session_id": "original_uuid",
  "is_fork": true,
  "name": "Forked Session",
  "status": "created",
  "mode": "forked"
}
```

---

### POST /api/v1/sessions/{session_id}/archive

**Purpose**: Archive session working directory

**Request Body**:
```json
{
  "compression": "gzip"
}
```

**Response (200 OK)**:
```json
{
  "archive_id": "uuid",
  "archive_path": "/archives/uuid.tar.gz",
  "archive_size_bytes": 1048576,
  "file_count": 42
}
```

---

### DELETE /api/v1/sessions/{session_id}

**Purpose**: Terminate and delete session

**Authentication**: Required

**Response (204 No Content)**

---

### GET /api/v1/sessions/{session_id}/messages

**Purpose**: Get session message history

**Query Parameters**:
- `skip`, `limit`: Pagination

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "message_type": "user",
      "content": {"content": "Hello"},
      "sequence_number": 1,
      "created_at": "2025-10-19T12:00:00Z"
    },
    {
      "id": "uuid",
      "message_type": "assistant",
      "content": {"content": "Hi there!"},
      "sequence_number": 2,
      "model": "claude-sonnet-4-5",
      "created_at": "2025-10-19T12:00:05Z"
    }
  ],
  "total": 10
}
```

---

### GET /api/v1/sessions/{session_id}/tool-calls

**Purpose**: Get session tool call history

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "tool_name": "Read",
      "tool_input": {"path": "/app/test.py"},
      "tool_output": {"content": "def test():\n    pass"},
      "status": "success",
      "duration_ms": 120,
      "created_at": "2025-10-19T12:00:10Z"
    }
  ],
  "total": 5
}
```

---

## Session Template Endpoints

### POST /api/v1/session-templates

**Purpose**: Create reusable session template

**File**: [session_templates.py](../../app/api/v1/session_templates.py)

**Authentication**: Required

**Request Body**:
```json
{
  "name": "DevOps Investigation Template",
  "description": "Pre-configured for infrastructure debugging",
  "category": "DEVOPS",
  "sdk_options": {
    "allowed_tools": ["Bash", "Read", "Write"],
    "permission_mode": "default"
  },
  "default_mode": "interactive",
  "is_public": false
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "name": "DevOps Investigation Template",
  "category": "DEVOPS",
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/session-templates

**Purpose**: List session templates

**Query Parameters**:
- `category`: Filter by category
- `is_public`: boolean

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "DevOps Template",
      "category": "DEVOPS",
      "is_public": false
    }
  ],
  "total": 5
}
```

---

### GET /api/v1/session-templates/{template_id}

**Purpose**: Get template details

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "name": "DevOps Template",
  "description": "...",
  "sdk_options": {...},
  "default_mode": "interactive",
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

## Task Endpoints

### POST /api/v1/tasks

**Purpose**: Create automated task

**File**: [tasks.py](../../app/api/v1/tasks.py)

**Authentication**: Required

**Request Body**:
```json
{
  "name": "Daily Log Analysis",
  "description": "Analyze application logs",
  "prompt_template": "Analyze logs from {{date}}",
  "allowed_tools": ["Read", "Bash"],
  "sdk_options": {},
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "generate_report": true,
  "report_format": "markdown"
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "name": "Daily Log Analysis",
  "is_scheduled": true,
  "schedule_cron": "0 9 * * *",
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/tasks

**Purpose**: List tasks

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Daily Log Analysis",
      "is_active": true,
      "is_scheduled": true,
      "schedule_cron": "0 9 * * *"
    }
  ],
  "total": 3
}
```

---

### POST /api/v1/tasks/{task_id}/execute

**Purpose**: Execute task immediately

**Request Body**:
```json
{
  "variables": {
    "date": "2025-10-19"
  }
}
```

**Response (200 OK)**:
```json
{
  "execution_id": "uuid",
  "session_id": "uuid",
  "status": "running",
  "started_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/tasks/{task_id}/executions

**Purpose**: List task execution history

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "status": "completed",
      "started_at": "2025-10-19T09:00:00Z",
      "completed_at": "2025-10-19T09:05:30Z",
      "duration_ms": 330000
    }
  ],
  "total": 15
}
```

---

## Report Endpoints

### POST /api/v1/reports

**Purpose**: Generate session report

**File**: [reports.py](../../app/api/v1/reports.py)

**Authentication**: Required

**Request Body**:
```json
{
  "session_id": "uuid",
  "format": "pdf",
  "include_messages": true,
  "include_tool_calls": true,
  "include_metrics": true
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "format": "pdf",
  "file_path": "/reports/uuid.pdf",
  "file_size_bytes": 245760,
  "generated_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/reports/{report_id}/download

**Purpose**: Download generated report

**Response**: File download (application/pdf, text/markdown, etc.)

---

## MCP Server Endpoints

### POST /api/v1/mcp-servers

**Purpose**: Register MCP server

**File**: [mcp_servers.py](../../app/api/v1/mcp_servers.py)

**Authentication**: Required

**Request Body**:
```json
{
  "name": "Kubernetes MCP",
  "description": "Kubernetes cluster management",
  "server_type": "STDIO",
  "command": "kubectl-mcp-server",
  "args": ["--cluster", "production"],
  "env": {
    "KUBECONFIG": "/path/to/kubeconfig"
  },
  "is_enabled": true,
  "is_global": false
}
```

**Response (201 Created)**:
```json
{
  "id": "uuid",
  "name": "Kubernetes MCP",
  "server_type": "STDIO",
  "is_enabled": true,
  "created_at": "2025-10-19T12:00:00Z"
}
```

---

### GET /api/v1/mcp-servers

**Purpose**: List MCP servers

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Kubernetes MCP",
      "server_type": "STDIO",
      "is_enabled": true,
      "is_global": false
    }
  ],
  "total": 3
}
```

---

### POST /api/v1/mcp-servers/import

**Purpose**: Import MCP servers from config file

**Request Body (multipart/form-data)**:
- `file`: YAML/JSON file with server configs

**Response (200 OK)**:
```json
{
  "imported_count": 5,
  "skipped_count": 1,
  "errors": []
}
```

---

### GET /api/v1/mcp-servers/export

**Purpose**: Export MCP servers to config file

**Query Parameters**:
- `format`: "yaml" | "json"

**Response**: File download

---

## Admin Endpoints

### GET /api/v1/admin/stats

**Purpose**: System statistics (admin only)

**File**: [admin.py](../../app/api/v1/admin.py)

**Authentication**: Required (admin role)

**Response (200 OK)**:
```json
{
  "total_users": 42,
  "total_sessions": 156,
  "active_sessions": 12,
  "total_api_calls_today": 1234,
  "total_cost_today_usd": 15.67
}
```

---

### GET /api/v1/admin/users

**Purpose**: List all users (admin only)

**Query Parameters**:
- `skip`, `limit`, `role`, `is_active`

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user",
      "is_active": true,
      "last_login_at": "2025-10-19T10:00:00Z"
    }
  ],
  "total": 42
}
```

---

## Monitoring Endpoints

### GET /health

**Purpose**: Health check

**File**: [main.py:120-128](../../main.py:120-128)

**Authentication**: Not required

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "AI-Agent-API-Service",
  "version": "1.0.0",
  "environment": "production"
}
```

---

### GET /metrics

**Purpose**: Prometheus metrics

**File**: [monitoring.py](../../app/api/v1/monitoring.py)

**Authentication**: Not required

**Response**: Prometheus text format

```
# HELP sessions_total Total number of sessions
# TYPE sessions_total counter
sessions_total{status="active"} 12
sessions_total{status="completed"} 156

# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="POST",path="/api/v1/sessions"} 234
```

---

## Common Response Schemas

### Error Response

```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-10-19T12:00:00Z"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 20,
  "links": {
    "next": "/api/v1/sessions?skip=20&limit=20",
    "prev": null
  }
}
```

---

## HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `204 No Content`: Successful deletion
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limiting

**Default Limits**:
- 60 requests per minute
- 1000 requests per hour

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1234567890
```

**Exceeded Response (429)**:
```json
{
  "detail": "Rate limit exceeded. Please try again in 30 seconds.",
  "retry_after": 30
}
```

---

## API Documentation

**Interactive Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

---

## Related Documentation

- **WebSocket API**: [WEBSOCKET_API.md](WEBSOCKET_API.md) - Real-time streaming
- **Authentication**: [AUTHENTICATION.md](AUTHENTICATION.md) - Auth details
- **Data Flow**: [../../architecture/DATA_FLOW.md](../../architecture/DATA_FLOW.md) - Request flow
- **Schemas**: [../../app/schemas/](../../app/schemas/) - Pydantic models

## Keywords

`api`, `rest`, `endpoints`, `routes`, `fastapi`, `http`, `sessions`, `tasks`, `reports`, `mcp`, `authentication`, `crud`, `queries`, `websocket`, `pagination`, `rate-limiting`, `swagger`, `openapi`
