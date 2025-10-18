# API Endpoints

The AI-Agent-API service provides a comprehensive REST API with WebSocket support for real-time communication. All endpoints follow RESTful conventions with proper HTTP status codes and error handling.

## API Overview

### Base Configuration

- **Base URL**: `http://localhost:8000` (development) / `https://api.example.com` (production)
- **API Prefix**: `/api/v1`
- **Authentication**: JWT Bearer tokens
- **Content Type**: `application/json`
- **Documentation**: `/docs` (Swagger UI), `/redoc` (ReDoc)

### Response Format

**Standard Response Structure**:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "timestamp": "2025-10-18T10:30:00Z"
}
```

**Error Response Structure**:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {...},
    "field_errors": {...}
  },
  "timestamp": "2025-10-18T10:30:00Z"
}
```

## Authentication Endpoints

### POST /api/v1/auth/login

**Purpose**: Authenticate user and obtain JWT token

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "username": "johndoe",
      "role": "user"
    }
  }
}
```

**Status Codes**:
- `200 OK`: Authentication successful
- `401 Unauthorized`: Invalid credentials
- `422 Unprocessable Entity`: Invalid request format

### POST /api/v1/auth/logout

**Purpose**: Invalidate current JWT token

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### GET /api/v1/auth/me

**Purpose**: Get current user information

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true,
    "quotas": {
      "max_concurrent_sessions": 5,
      "max_api_calls_per_hour": 1000,
      "max_storage_mb": 10240
    },
    "created_at": "2025-01-15T09:00:00Z"
  }
}
```

## Session Management Endpoints

### POST /api/v1/sessions

**Purpose**: Create a new AI conversation session

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "name": "Code Review Session",
  "mode": "interactive",
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "parent_session_id": null
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Code Review Session",
    "mode": "interactive",
    "status": "created",
    "sdk_options": {...},
    "working_directory_path": "/data/sessions/456e7890-e89b-12d3-a456-426614174000",
    "created_at": "2025-10-18T10:30:00Z",
    "metrics": {
      "total_messages": 0,
      "total_tool_calls": 0,
      "total_cost_usd": 0.0
    }
  }
}
```

**Status Codes**:
- `201 Created`: Session created successfully
- `400 Bad Request`: Invalid session parameters
- `403 Forbidden`: Quota exceeded
- `422 Unprocessable Entity`: Validation errors

### GET /api/v1/sessions

**Purpose**: List all sessions for the authenticated user

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `skip` (int, default: 0): Number of sessions to skip
- `limit` (int, default: 50, max: 100): Number of sessions to return
- `status` (string, optional): Filter by session status
- `mode` (string, optional): Filter by session mode

**Response**:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": "456e7890-e89b-12d3-a456-426614174000",
        "name": "Code Review Session",
        "status": "active",
        "mode": "interactive",
        "created_at": "2025-10-18T10:30:00Z",
        "metrics": {...}
      }
    ],
    "total": 25,
    "skip": 0,
    "limit": 50
  }
}
```

### GET /api/v1/sessions/{session_id}

**Purpose**: Get detailed information about a specific session

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Code Review Session",
    "mode": "interactive",
    "status": "active",
    "sdk_options": {...},
    "working_directory_path": "/data/sessions/456e7890-e89b-12d3-a456-426614174000",
    "parent_session_id": null,
    "is_fork": false,
    "metrics": {
      "total_messages": 15,
      "total_tool_calls": 8,
      "total_cost_usd": 2.45,
      "duration_ms": 125000,
      "api_tokens": {
        "input": 1250,
        "output": 890,
        "cache_creation": 200,
        "cache_read": 50
      }
    },
    "created_at": "2025-10-18T10:30:00Z",
    "started_at": "2025-10-18T10:31:00Z"
  }
}
```

**Status Codes**:
- `200 OK`: Session found and accessible
- `404 Not Found`: Session does not exist
- `403 Forbidden`: No permission to access session

### PATCH /api/v1/sessions/{session_id}/status

**Purpose**: Update session status (pause, resume, terminate)

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "status": "paused",
  "reason": "Taking a break"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "status": "paused",
    "updated_at": "2025-10-18T11:00:00Z"
  }
}
```

### POST /api/v1/sessions/{session_id}/fork

**Purpose**: Create a new session based on an existing session

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "name": "Code Review Session (Fork)",
  "fork_from_message": 10
}
```

**Response**: Same as POST `/api/v1/sessions` with `parent_session_id` set and `is_fork: true`

### DELETE /api/v1/sessions/{session_id}

**Purpose**: Soft delete a session

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

## Session Messages and Communication

### GET /api/v1/sessions/{session_id}/messages

**Purpose**: Retrieve messages from a session

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `skip` (int, default: 0): Number of messages to skip
- `limit` (int, default: 100): Number of messages to return
- `message_type` (string, optional): Filter by message type

**Response**:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "789e0123-e89b-12d3-a456-426614174000",
        "session_id": "456e7890-e89b-12d3-a456-426614174000",
        "message_type": "human",
        "content": "Please review this Python code for security issues.",
        "sequence_number": 1,
        "created_at": "2025-10-18T10:31:00Z"
      },
      {
        "id": "890e1234-e89b-12d3-a456-426614174000",
        "session_id": "456e7890-e89b-12d3-a456-426614174000", 
        "message_type": "assistant",
        "content": "I'll analyze your Python code for security vulnerabilities...",
        "sequence_number": 2,
        "model": "claude-3-5-sonnet-20241022",
        "created_at": "2025-10-18T10:31:15Z"
      }
    ],
    "total": 15,
    "skip": 0,
    "limit": 100
  }
}
```

### GET /api/v1/sessions/{session_id}/tool-calls

**Purpose**: Retrieve tool calls from a session

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "tool_calls": [
      {
        "id": "901e2345-e89b-12d3-a456-426614174000",
        "session_id": "456e7890-e89b-12d3-a456-426614174000",
        "tool_name": "file_read",
        "tool_use_id": "toolu_abc123",
        "tool_input": {
          "file_path": "/src/main.py"
        },
        "tool_output": {
          "content": "import os\nfrom flask import Flask...",
          "file_size": 1024
        },
        "status": "completed",
        "permission_decision": "auto_approved",
        "duration_ms": 150,
        "created_at": "2025-10-18T10:31:30Z"
      }
    ],
    "total": 8,
    "skip": 0,
    "limit": 100
  }
}
```

## Task Management Endpoints

### POST /api/v1/tasks

**Purpose**: Create a new reusable task definition

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "name": "Security Code Review",
  "description": "Automated security analysis of Python code",
  "prompt_template": "Analyze the {{language}} code in {{file_path}} for {{issue_type}} issues. Focus on: {{focus_areas}}",
  "allowed_tools": ["file_read", "directory_list", "git_status"],
  "disallowed_tools": ["file_write", "system_command"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4000
  },
  "generate_report": true,
  "report_format": "markdown",
  "tags": ["security", "python", "automation"]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "012e3456-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Security Code Review",
    "description": "Automated security analysis of Python code",
    "prompt_template": "Analyze the {{language}} code...",
    "allowed_tools": ["file_read", "directory_list", "git_status"],
    "is_active": true,
    "created_at": "2025-10-18T11:00:00Z"
  }
}
```

### GET /api/v1/tasks

**Purpose**: List user's task definitions

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `skip`, `limit`: Pagination
- `is_active` (boolean): Filter by active status
- `tags` (string): Filter by tags (comma-separated)

### POST /api/v1/tasks/{task_id}/execute

**Purpose**: Execute a task with provided variables

**Headers**: `Authorization: Bearer <token>`

**Request**:
```json
{
  "variables": {
    "language": "Python",
    "file_path": "/src/main.py",
    "issue_type": "security",
    "focus_areas": "SQL injection, XSS, authentication"
  },
  "generate_report": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "234e5678-e89b-12d3-a456-426614174000",
    "task_id": "012e3456-e89b-12d3-a456-426614174000",
    "session_id": "345e6789-e89b-12d3-a456-426614174000",
    "status": "running",
    "created_at": "2025-10-18T11:15:00Z",
    "estimated_duration_seconds": 120
  }
}
```

### GET /api/v1/tasks/executions/{execution_id}

**Purpose**: Get task execution status and results

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "234e5678-e89b-12d3-a456-426614174000",
    "task_id": "012e3456-e89b-12d3-a456-426614174000",
    "session_id": "345e6789-e89b-12d3-a456-426614174000",
    "status": "completed",
    "result": {
      "summary": "Found 3 security issues",
      "issues": [...],
      "recommendations": [...]
    },
    "duration_ms": 95000,
    "cost_usd": 0.85,
    "report": {
      "id": "567e8901-e89b-12d3-a456-426614174000",
      "format": "markdown",
      "download_url": "/api/v1/reports/567e8901-e89b-12d3-a456-426614174000/download"
    },
    "created_at": "2025-10-18T11:15:00Z",
    "completed_at": "2025-10-18T11:16:35Z"
  }
}
```

## WebSocket Endpoints

### WebSocket /ws/sessions/{session_id}

**Purpose**: Real-time bidirectional communication with AI session

**Authentication**: Query parameter `token=<jwt_token>`

**Connection**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}?token=${jwtToken}`);
```

**Outgoing Message Format** (Client → Server):
```json
{
  "type": "message",
  "content": "Analyze this code for bugs",
  "message_id": "client_msg_123"
}
```

**Incoming Message Format** (Server → Client):
```json
{
  "type": "message",
  "data": {
    "id": "890e1234-e89b-12d3-a456-426614174000",
    "message_type": "assistant",
    "content": "I'll analyze your code...",
    "sequence_number": 5,
    "created_at": "2025-10-18T11:30:00Z"
  }
}
```

**Event Types**:
- `message`: New conversation message
- `tool_call_started`: Tool execution began
- `tool_call_completed`: Tool execution finished
- `session_status_changed`: Session state transition
- `error`: Error occurred
- `permission_request`: Tool permission required

**Permission Request Format**:
```json
{
  "type": "permission_request",
  "data": {
    "tool_call_id": "901e2345-e89b-12d3-a456-426614174000",
    "tool_name": "file_write",
    "tool_input": {
      "file_path": "/src/config.py",
      "content": "DATABASE_URL = 'sqlite:///app.db'"
    },
    "risk_level": "medium",
    "explanation": "This will modify a configuration file"
  }
}
```

**Permission Response Format**:
```json
{
  "type": "permission_response",
  "tool_call_id": "901e2345-e89b-12d3-a456-426614174000",
  "decision": "approved",
  "reason": "User approved file modification"
}
```

## Administrative Endpoints

### GET /api/v1/admin/users

**Purpose**: List all users (admin only)

**Headers**: `Authorization: Bearer <admin_token>`

**Query Parameters**: Pagination and filtering options

### PATCH /api/v1/admin/users/{user_id}/quotas

**Purpose**: Update user quotas (admin only)

**Request**:
```json
{
  "max_concurrent_sessions": 10,
  "max_api_calls_per_hour": 2000,
  "max_storage_mb": 20480
}
```

## Health and Monitoring Endpoints

### GET /health

**Purpose**: Service health check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-18T11:45:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "claude_api": "healthy"
  }
}
```

### GET /metrics

**Purpose**: Prometheus metrics (operations team)

**Response**: Prometheus format metrics

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions or quota exceeded
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Examples

**Validation Error**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "field_errors": {
      "email": "Invalid email format",
      "password": "Password must be at least 8 characters"
    }
  }
}
```

**Quota Exceeded**:
```json
{
  "success": false,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Maximum concurrent sessions exceeded",
    "details": {
      "current_sessions": 5,
      "max_allowed": 5,
      "quota_type": "concurrent_sessions"
    }
  }
}
```

## Rate Limiting

### Rate Limit Headers

All responses include rate limiting headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1634567890
X-RateLimit-Window: 3600
```

### Rate Limit Policies

- **Authentication**: 10 requests/minute per IP
- **API Calls**: User-specific quota (default: 1000/hour)
- **WebSocket Messages**: 60 messages/minute per session
- **File Uploads**: 10 uploads/minute per user