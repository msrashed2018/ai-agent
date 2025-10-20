# Session Management APIs Documentation

**Last Updated:** October 20, 2025
**API Version:** v1
**Base Path:** `/api/v1/sessions`

---

## Overview

Session Management APIs provide complete lifecycle management for Claude Code sessions, including:
- **17 Total Endpoints** across 4 functional groups
- **Stateful Execution**: Each session maintains conversation context and working directory
- **SDK Integration**: Direct integration with official Claude SDK
- **Permission Management**: Fine-grained tool access control
- **Cost Tracking**: Automatic token and cost calculation
- **Forking Support**: Branch sessions for experimentation

---

## Table of Contents

### Core Session Operations (5 endpoints)
1. [POST /sessions](#1-post-sessions) - Create new session
2. [GET /sessions/{session_id}](#2-get-sessionssession_id) - Get session details
3. [GET /sessions](#3-get-sessions) - List user's sessions
4. [POST /sessions/{session_id}/query](#4-post-sessionssession_idquery) - Send message
5. [DELETE /sessions/{session_id}](#5-delete-sessionssession_id) - Terminate session

### Session Control (2 endpoints)
6. [POST /sessions/{session_id}/resume](#6-post-sessionssession_idresume) - Resume session
7. [POST /sessions/{session_id}/pause](#7-post-sessionssession_idpause) - Pause session

### Data Access (3 endpoints)
8. [GET /sessions/{session_id}/messages](#8-get-sessionssession_idmessages) - List messages
9. [GET /sessions/{session_id}/tool-calls](#9-get-sessionssession_idtool-calls) - List tool calls
10. [GET /sessions/{session_id}/workdir/download](#10-get-sessionssession_idworkdirdownload) - Download working directory

### Advanced Operations (7 endpoints)
11. [POST /sessions/{session_id}/fork](#11-post-sessionssession_idfork) - Fork session
12. [POST /sessions/{session_id}/archive](#12-post-sessionssession_idarchive) - Archive working directory
13. [GET /sessions/{session_id}/archive](#13-get-sessionssession_idarchive) - Get archive metadata
14. [GET /sessions/{session_id}/hooks](#14-get-sessionssession_idhooks) - Get hook executions
15. [GET /sessions/{session_id}/permissions](#15-get-sessionssession_idpermissions) - Get permission decisions
16. [GET /sessions/{session_id}/metrics/snapshots](#16-get-sessionssession_idmetricssnapshots) - Get metrics history
17. [GET /sessions/{session_id}/metrics/current](#17-get-sessionssession_idmetricscurrent) - Get current metrics

---

## Authentication

All endpoints require JWT authentication via Bearer token in Authorization header:

```bash
Authorization: Bearer <access_token>
```

Get access token from `/api/v1/auth/login` endpoint.

---

## Common Response Fields

All session responses include these HATEOAS links:

```json
{
  "_links": {
    "self": "/api/v1/sessions/{session_id}",
    "query": "/api/v1/sessions/{session_id}/query",
    "messages": "/api/v1/sessions/{session_id}/messages",
    "tool_calls": "/api/v1/sessions/{session_id}/tool-calls",
    "stream": "/api/v1/sessions/{session_id}/stream"
  }
}
```

---

# Core Session Operations

## 1. POST /sessions

**Create a new Claude Code session**

Creates an isolated execution environment with working directory, SDK client configuration, and optional template-based setup.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions`
- **Auth Required**: Yes
- **Request Body**: `SessionCreateRequest` (all fields optional)
- **Success Response**: `201 Created` with `SessionResponse`
- **Error Responses**: `400 Bad Request`, `401 Unauthorized`, `429 Too Many Requests`

### cURL Examples

**Success - Minimal request:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{}'
```

**Success - With name and custom configuration:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Debug API Issue",
    "description": "Investigating authentication bug",
    "allowed_tools": ["bash*", "read*", "write*"],
    "system_prompt": "You are an expert Python developer helping debug API issues.",
    "sdk_options": {
      "model": "claude-3-5-sonnet-20241022",
      "max_turns": 30
    },
    "metadata": {
      "project": "ai-agent-api",
      "issue_id": "BUG-123"
    }
  }'
```

**Success - From template:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "template_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "name": "Custom Session from Template"
  }'
```

**Error - Quota exceeded:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_USER_ACCESS_TOKEN" \
  -d '{}'

# Response: 429 Too Many Requests
# {"detail": "User has 5 active sessions (limit: 5)"}
```

**Error - Invalid template:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "template_id": "00000000-0000-0000-0000-000000000000"
  }'

# Response: 400 Bad Request
# {"detail": "Failed to create session from template: Template not found"}
```

### Request Schema

```json
{
  "template_id": "uuid (optional)",
  "name": "string (optional, max 255 chars)",
  "description": "string (optional)",
  "working_directory": "string (optional, path)",
  "allowed_tools": ["string (optional, glob patterns)"],
  "system_prompt": "string (optional)",
  "sdk_options": {
    "model": "string (optional, default: claude-3-5-sonnet-20241022)",
    "max_turns": "integer (optional, default: 20)",
    "permission_mode": "string (optional, default: default)",
    "disallowed_tools": ["string (optional)"],
    "mcp_servers": {}
  },
  "metadata": {}
}
```

### Response Schema

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "string|null",
  "description": "string|null",
  "status": "created",
  "working_directory": "string (path)",
  "allowed_tools": ["string (glob patterns)"],
  "system_prompt": "string|null",
  "sdk_options": {},
  "parent_session_id": "uuid|null",
  "is_fork": false,
  "message_count": 0,
  "tool_call_count": 0,
  "total_cost_usd": 0.0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T10:30:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "metadata": {},
  "_links": {
    "self": "/api/v1/sessions/{id}",
    "query": "/api/v1/sessions/{id}/query",
    "messages": "/api/v1/sessions/{id}/messages",
    "tool_calls": "/api/v1/sessions/{id}/tool-calls",
    "stream": "/api/v1/sessions/{id}/stream"
  }
}
```

### Backend Processing Steps

1. **Quota Validation**
   - Query `sessions` table: COUNT active sessions for user
   - Check against `users.max_concurrent_sessions` limit
   - If exceeded → 429 error with audit log

2. **Template Loading** (if `template_id` provided)
   - Query `session_templates` table for template
   - Verify user has access (owner or public template)
   - Increment `usage_count` on template
   - Merge template config with request overrides

3. **SDK Options Construction**
   - Create `SDKOptions` value object with defaults:
     - model: "claude-3-5-sonnet-20241022"
     - max_turns: 20
     - allowed_tools: ["*"] (all tools)
     - permission_mode: "default"
   - Override with template config (if any)
   - Override with request params (final precedence)
   - Add system_prompt if provided

4. **Session Entity Creation**
   - Generate new UUID
   - Set mode = SessionMode.INTERACTIVE
   - Set status = SessionStatus.CREATED
   - Set user_id = current_user.id

5. **Working Directory Creation**
   - Call `StorageManager.create_working_directory(session_id)`
   - Create directory at `data/agent-workdirs/active/{session_id}`
   - Set proper permissions (755)
   - Store path in session entity

6. **Database Persistence**
   - Convert Session entity to SessionModel (SQLAlchemy)
   - Insert into `sessions` table
   - Flush transaction (get DB-generated values)
   - Commit transaction

7. **Audit Logging**
   - Call `AuditService.log_session_created()`
   - Record: session_id, user_id, mode, sdk_options
   - Insert into `audit_logs` table

8. **Response Building**
   - Convert Session entity to SessionResponse
   - Add HATEOAS links
   - Return with 201 Created status

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Quota Exceeded | 429 | User has max concurrent sessions | `{"detail": "User has X active sessions (limit: Y)"}` |
| Invalid Template | 400 | template_id not found or no access | `{"detail": "Failed to create session from template: ..."}` |
| Unauthorized | 401 | Missing or invalid token | `{"detail": "Not authenticated"}` |
| Validation Error | 422 | Invalid request fields | `{"detail": [{"loc": [...], "msg": "..."}]}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:56-232`
- **Service**: `app/services/session_service.py:51-107`
- **Repository**: `app/repositories/session_repository.py`
- **Schema**: `app/schemas/session.py:13-46` (request), `48-76` (response)
- **Domain Entity**: `app/domain/entities/session.py`

---

## 2. GET /sessions/{session_id}

**Get detailed information about a specific session**

Retrieves complete session state including metrics, configuration, and current status.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `200 OK` with `SessionResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Error - Session not found:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 404 Not Found
# {"detail": "Session 00000000-0000-0000-0000-000000000000 not found"}
```

**Error - Not authorized (regular user accessing other user's session):**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/{admin_session_id} \
  -H "Authorization: Bearer $AI_AGENT_USER_ACCESS_TOKEN"

# Response: 403 Forbidden
# {"detail": "Not authorized to access this session"}
```

### Response Schema

Same as POST /sessions response, but with updated metrics:

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Debug API Issue",
  "status": "active",
  "working_directory": "/data/agent-workdirs/active/f47ac10b-...",
  "message_count": 12,
  "tool_call_count": 8,
  "total_cost_usd": 0.0456,
  "total_input_tokens": 1250,
  "total_output_tokens": 890,
  "started_at": "2025-10-20T10:31:15Z",
  "...": "..."
}
```

### Backend Processing Steps

1. **Database Query**
   - SELECT from `sessions` WHERE id = {session_id} AND deleted_at IS NULL
   - If not found → 404 error

2. **Authorization Check**
   - If session.user_id == current_user.id → Allow
   - Else if current_user.role == "admin" → Allow
   - Else → 403 Forbidden

3. **Entity to Response Conversion**
   - Call `session_to_response(session)` mapper
   - Convert status Enum to string
   - Parse sdk_options for display fields
   - Convert Decimal total_cost_usd to float

4. **HATEOAS Links**
   - Add self, query, messages, tool-calls, stream links

5. **Return Response**
   - 200 OK with SessionResponse body

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist or is deleted | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session and not admin | `{"detail": "Not authorized to access this session"}` |
| Unauthorized | 401 | Missing or invalid token | `{"detail": "Not authenticated"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:235-272`
- **Service**: `app/services/session_service.py:109-122`
- **Repository**: `app/repositories/session_repository.py:17-27`
- **Mapper**: `app/schemas/mappers.py:26-73`

---

## 3. GET /sessions

**List all sessions for the authenticated user**

Retrieves paginated list of sessions with optional filtering by status and fork status.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions`
- **Auth Required**: Yes
- **Query Parameters**:
  - `status` (optional): Filter by status (created/active/paused/completed/failed/terminated)
  - `is_fork` (optional): Filter by fork status (true/false)
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 10, max: 100)
- **Success Response**: `200 OK` with `SessionListResponse`
- **Error Responses**: `401 Unauthorized`

### cURL Examples

**Success - Default (first page):**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Success - With filters:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions?status=active&page=1&page_size=20" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Success - Only forked sessions:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions?is_fork=true" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
{
  "items": [
    {
      "id": "...",
      "user_id": "...",
      "name": "...",
      "status": "active",
      "...": "...",
      "_links": {
        "self": "/api/v1/sessions/{id}",
        "query": "/api/v1/sessions/{id}/query"
      }
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 10,
  "pages": 3,
  "_links": {
    "self": "/api/v1/sessions?page=1&page_size=10",
    "next": "/api/v1/sessions?page=2&page_size=10",
    "prev": null,
    "first": "/api/v1/sessions?page=1&page_size=10",
    "last": "/api/v1/sessions?page=3&page_size=10"
  }
}
```

### Backend Processing Steps

1. **Pagination Parsing**
   - Extract page, page_size from query params
   - Calculate offset = (page - 1) * page_size
   - Calculate limit = page_size

2. **Database Query**
   - SELECT from `sessions`
   - WHERE user_id = {current_user_id} AND deleted_at IS NULL
   - ORDER BY created_at DESC
   - OFFSET {offset} LIMIT {limit}

3. **In-Memory Filtering** (if filters provided)
   - Filter by status (exact match)
   - Filter by is_fork (boolean match)

4. **Total Count**
   - COUNT matching sessions for pagination metadata
   - (Note: Current implementation counts filtered results, not total in DB)

5. **Response Building**
   - Convert each session to SessionResponse
   - Add minimal HATEOAS links (self, query)
   - Wrap in PaginatedResponse with pagination metadata

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Unauthorized | 401 | Missing or invalid token | `{"detail": "Not authenticated"}` |
| Validation Error | 422 | Invalid query params (e.g., page_size > 100) | `{"detail": [...]}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:275-321`
- **Service**: `app/services/session_service.py:124-132`
- **Repository**: `app/repositories/session_repository.py:29-48`
- **Schema**: `app/schemas/session.py:78-80`, `app/schemas/common.py` (PaginatedResponse)

---

## 4. POST /sessions/{session_id}/query

**Send a message to Claude Code and receive responses**

Sends user message through Claude SDK, processes responses, and returns message ID. This is the core interaction endpoint.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions/{session_id}/query`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Request Body**: `SessionQueryRequest`
- **Success Response**: `200 OK` with `SessionQueryResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`

### cURL Examples

**Success - Send message:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "message": "Create a Python Flask REST API with user authentication"
  }'
```

**Success - Fork before sending:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "message": "Try a different approach using FastAPI instead",
    "fork": true
  }'
```

**Error - Session not active:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{paused_session_id}/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{"message": "Continue work"}'

# Response: 409 Conflict
# {"detail": "Session {id} is not in a valid state for messaging"}
```

**Error - Message too long:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-.../query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{"message": "..."}'  # > 50,000 chars

# Response: 422 Unprocessable Entity
# {"detail": [{"loc": ["body", "message"], "msg": "ensure this value has at most 50000 characters"}]}
```

### Request Schema

```json
{
  "message": "string (required, 1-50000 chars)",
  "fork": "boolean (optional, default: false)"
}
```

### Response Schema

```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "active",
  "parent_session_id": null,
  "is_fork": false,
  "message_id": "b8e5c3a1-9d7f-4e6b-8c3a-1f2e3d4c5b6a",
  "_links": {
    "self": "/api/v1/sessions/f47ac10b-...",
    "message": "/api/v1/sessions/f47ac10b-.../messages/b8e5c3a1-...",
    "stream": "/api/v1/sessions/f47ac10b-.../stream"
  }
}
```

### Backend Processing Steps

#### First Message (status = CREATED):

1. **Status Transition: CREATED → CONNECTING**
   - Update sessions table: status = "connecting"
   - Commit transaction

2. **SDK Client Setup**
   - **MCP Configuration**:
     - Query MCP servers: SDK tools + user servers + global servers
     - Build merged MCP config dictionary
     - Update session.sdk_options with mcp_servers
     - Persist to database, commit
   - **Permission Callback**:
     - Create callback function linked to PermissionService
     - Callback evaluates tool access against allowed_tools patterns
   - **Hooks Installation**:
     - PreToolUse: audit_hook, tool_tracking_hook
     - PostToolUse: audit_hook, tool_tracking_hook, cost_tracking_hook
   - **Create SDK Client**:
     - Initialize ClaudeSDKClient with session config
     - Store in ClientManager cache by session_id

3. **Status Transition: CONNECTING → ACTIVE**
   - Update sessions table: status = "active", started_at = now()
   - Commit transaction

#### Every Message:

4. **Status Transition: ACTIVE → PROCESSING**
   - Update sessions table: status = "processing"
   - Commit transaction

5. **Send Message to SDK**
   - Get cached SDK client by session_id
   - Call `client.query(message_text)`
   - SDK sends to Claude API

6. **Process Response Stream**
   - MessageProcessor.process_message_stream():
     - Read SDK response stream (async generator)
     - Parse message types (user, assistant, tool_use, tool_result)
     - Create Message value objects
     - Insert into `messages` table
     - Update session metrics (total_messages++, token counts, costs)
     - Broadcast to WebSocket subscribers (if any)
     - Yield messages to API caller
   - Continue until stream complete

7. **Status Transition: PROCESSING → ACTIVE**
   - Update sessions table: status = "active"
   - Commit transaction

8. **Build Response**
   - Get last message ID from stream
   - Construct SessionQueryResponse
   - Add HATEOAS links

#### Error Handling:

If any exception during steps 5-7:
- Catch exception
- Transition status to FAILED
- Set error_message field
- Commit transaction
- Re-raise exception → 500 Internal Server Error

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |
| Conflict | 409 | Session not in valid state (paused/completed/failed/terminated) | `{"detail": "Session {id} is not in a valid state for messaging"}` |
| Validation Error | 422 | Message empty or > 50000 chars | `{"detail": [...]}` |
| Internal Error | 500 | SDK error, network error, etc. | `{"detail": "Internal server error"}` (session.status→FAILED) |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:324-423`
- **Service**: `app/services/sdk_session_service.py:83-186`
- **SDK Setup**: `app/services/sdk_session_service.py:188-275`
- **Message Processor**: `app/claude_sdk/message_processor.py`
- **Schema**: `app/schemas/session.py:83-100`

---

## 5. DELETE /sessions/{session_id}

**Terminate a session and clean up resources**

Permanently ends the session, disconnects SDK client, and optionally archives working directory.

### Endpoint Details

- **Method**: `DELETE`
- **Path**: `/api/v1/sessions/{session_id}`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `204 No Content`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 204 No Content (empty body)
```

**Error - Not found:**
```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 404 Not Found
# {"detail": "Session 00000000-0000-0000-0000-000000000000 not found"}
```

### Backend Processing Steps

1. **Get Session**
   - Query sessions table by ID
   - If not found → 404 error

2. **Authorization Check**
   - Verify ownership or admin role
   - If not authorized → 403 error

3. **SDK Client Cleanup**
   - Call `SDKIntegratedSessionService.cleanup_session_client()`
   - Get SDK client from ClientManager cache
   - Call `client.disconnect()` if exists
   - Remove from cache
   - Log any errors (don't fail if cleanup error)

4. **Working Directory Archival** (if exists)
   - Check if session.working_directory_path exists
   - If yes: Call `StorageManager.archive_working_directory()`
     - Create tar.gz of directory
     - Move to archives/ folder
     - Record archive metadata
   - Continue even if archival fails

5. **Soft Delete**
   - Update sessions table: deleted_at = now()
   - Session record kept for audit/recovery
   - Excluded from future queries (WHERE deleted_at IS NULL)
   - Commit transaction

6. **Return**
   - 204 No Content (successful deletion, no body)

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |
| Unauthorized | 401 | Missing or invalid token | `{"detail": "Not authenticated"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:604-635`
- **Service**: `app/services/sdk_session_service.py:383-389`
- **SDK Cleanup**: `app/services/sdk_session_service.py:357-368`
- **Repository**: `app/repositories/session_repository.py` (soft_delete method)

---

# Session Control

## 6. POST /sessions/{session_id}/resume

**Resume a paused or completed session**

Reactivates a session for continued interaction, or optionally forks it before resuming.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions/{session_id}/resume`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Request Body**: `SessionResumeRequest`
- **Success Response**: `200 OK` with `SessionResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`

### cURL Examples

**Success - Resume paused session:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{"fork": false}'
```

**Success - Fork before resuming:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{"fork": true}'

# Returns new forked session with status="created"
```

**Error - Session already active:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{active_session_id}/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{}'

# Response: 409 Conflict
# {"detail": "Session is already active"}
```

**Error - Cannot resume terminal state:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{failed_session_id}/resume \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{"fork": false}'

# Response: 409 Conflict
# {"detail": "Cannot resume terminal session"}
```

### Request Schema

```json
{
  "fork": "boolean (optional, default: false)"
}
```

### Response Schema

If `fork=false`: Returns original session with status="active"

If `fork=true`: Returns new forked session with status="created", parent_session_id set, is_fork=true

### Backend Processing Steps

#### If fork=false (Resume in-place):

1. **Get Session**
   - Query sessions table
   - If not found → 404 error

2. **Authorization Check**
   - Verify ownership or admin role

3. **Validate State**
   - If status == "active" → 409 Conflict
   - If status in [completed, failed, terminated, archived] → 409 Conflict ("Cannot resume terminal session")
   - Otherwise (paused) → Proceed

4. **Status Transition**
   - Call `session.transition_to(SessionStatus.ACTIVE)`
   - Validates transition is allowed
   - Update status, updated_at timestamp

5. **Update Database**
   - Update sessions table: status = "active", updated_at = now()
   - Commit transaction

6. **Return Response**
   - Convert session to SessionResponse
   - Add HATEOAS links (self, query, messages)

#### If fork=true (Fork before resuming):

1. **Get Parent Session** (same as above)

2. **Call `fork_session_advanced()`**
   - Create new session with mode=FORKED
   - Copy SDK options from parent
   - Set parent_session_id and is_fork=true
   - Create new working directory
   - Copy all files from parent working directory
   - Log fork action to audit
   - Return new session

3. **Return Response**
   - New session has status="created"
   - Can immediately send messages

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |
| Conflict | 409 | Session already active | `{"detail": "Session is already active"}` |
| Conflict | 409 | Session in terminal state (failed/terminated/archived) | `{"detail": "Cannot resume terminal session"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:505-558`
- **Service**: `app/services/session_service.py:168-200`
- **Domain Entity**: `app/domain/entities/session.py` (transition_to, can_transition_to methods)

---

## 7. POST /sessions/{session_id}/pause

**Pause an active session**

Temporarily halts session activity without terminating. Session can be resumed later.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions/{session_id}/pause`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `200 OK` with `SessionResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`

### cURL Examples

**Success:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/pause \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Error - Session not active:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{paused_session_id}/pause \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 409 Conflict (or 400 Bad Request)
# {"detail": "Cannot transition from paused to paused"}
```

### Response Schema

Same as SessionResponse with status="paused" and HATEOAS links including "resume":

```json
{
  "id": "...",
  "status": "paused",
  "...": "...",
  "_links": {
    "self": "/api/v1/sessions/{id}",
    "resume": "/api/v1/sessions/{id}/resume"
  }
}
```

### Backend Processing Steps

1. **Get Session**
   - Query sessions table
   - If not found → 404 error

2. **Authorization Check**
   - Verify ownership or admin role

3. **Status Transition**
   - Call `session.transition_to(SessionStatus.PAUSED)`
   - Validates transition from ACTIVE to PAUSED
   - If invalid (e.g., already paused) → raises InvalidStateTransitionError → 409 or 400

4. **Update Database**
   - Update sessions table: status = "paused", updated_at = now()
   - Commit transaction

5. **Return Response**
   - Convert session to SessionResponse
   - Add HATEOAS links (self, resume)

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |
| Conflict | 409 | Invalid state transition | `{"detail": "Cannot transition from {from} to paused"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:561-601`
- **Service**: `app/services/session_service.py:164-166`
- **Domain Entity**: `app/domain/entities/session.py:93-125` (state machine)

---

# Data Access

## 8. GET /sessions/{session_id}/messages

**List all messages in a session**

Retrieves conversation history in reverse chronological order (newest first).

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/messages`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Query Parameters**:
  - `limit` (optional): Number of messages to return (1-100, default: 50)
  - `before_id` (optional): Return messages before this message ID
- **Success Response**: `200 OK` with array of `MessageResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success - Get last 50 messages:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/messages" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Success - Get last 10 messages:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/messages?limit=10" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Success - Pagination with before_id:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-.../messages?limit=20&before_id={message_uuid}" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
[
  {
    "id": "b8e5c3a1-9d7f-4e6b-8c3a-1f2e3d4c5b6a",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "message_type": "assistant",
    "content": {
      "text": "I'll help you create a Flask REST API...",
      "type": "text"
    },
    "token_count": 150,
    "cost_usd": 0.0045,
    "created_at": "2025-10-20T10:35:22Z",
    "metadata": {}
  },
  {
    "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "message_type": "user",
    "content": {
      "text": "Create a Python Flask REST API...",
      "type": "text"
    },
    "token_count": 25,
    "cost_usd": 0.000075,
    "created_at": "2025-10-20T10:35:15Z",
    "metadata": {}
  }
]
```

### Message Types

- **user**: User-sent messages
- **assistant**: Claude's text responses
- **system**: System messages
- **result**: Final execution results

### Backend Processing Steps

1. **Get Session and Authorize**
   - Query sessions table
   - If not found → 404
   - Check ownership or admin role
   - If not authorized → 403

2. **Query Messages**
   - SELECT from `messages` table
   - WHERE session_id = {session_id}
   - AND (before_id condition if provided)
   - ORDER BY created_at DESC
   - LIMIT {limit}

3. **Convert to Response**
   - For each message model:
     - Convert to MessageResponse using `MessageResponse.model_validate()`
     - Includes all fields (id, type, content, tokens, cost, timestamp)

4. **Return Array**
   - 200 OK with array of MessageResponse

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |
| Validation Error | 422 | Invalid limit (< 1 or > 100) | `{"detail": [...]}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:426-463`
- **Repository**: `app/repositories/message_repository.py`
- **Schema**: `app/schemas/session.py:109-122`

---

## 9. GET /sessions/{session_id}/tool-calls

**List all tool executions in a session**

Retrieves history of tool calls with execution details, permission decisions, and results.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/tool-calls`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Query Parameters**:
  - `limit` (optional): Number of tool calls to return (1-100, default: 50)
- **Success Response**: `200 OK` with array of `ToolCallResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/tool-calls" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Success - Limit to 10:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-.../tool-calls?limit=10" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
[
  {
    "id": "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "tool_use_message_id": "...",
    "tool_result_message_id": "...",
    "tool_name": "bash",
    "tool_input": {
      "command": "ls -la",
      "cwd": "/workspace"
    },
    "tool_output": {
      "stdout": "total 24\ndrwxr-xr-x...",
      "stderr": "",
      "exit_code": 0
    },
    "status": "success",
    "error_message": null,
    "started_at": "2025-10-20T10:36:10Z",
    "completed_at": "2025-10-20T10:36:11Z",
    "duration_ms": 1234,
    "created_at": "2025-10-20T10:36:10Z"
  }
]
```

### Tool Call Status Values

- **pending**: Tool execution started but not complete
- **success**: Tool executed successfully
- **error**: Tool execution failed

### Backend Processing Steps

1. **Get Session and Authorize**
   - Query sessions table
   - Authorization check (same as messages endpoint)

2. **Query Tool Calls**
   - SELECT from `tool_calls` table
   - WHERE session_id = {session_id}
   - ORDER BY created_at DESC
   - LIMIT {limit}

3. **Convert to Response**
   - For each tool call model:
     - Convert to ToolCallResponse using `ToolCallResponse.model_validate()`
     - Includes input, output, status, timing, error details

4. **Return Array**
   - 200 OK with array of ToolCallResponse

### Error Scenarios

Same as messages endpoint (404, 403, 422)

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:466-502`
- **Repository**: `app/repositories/tool_call_repository.py`
- **Schema**: `app/schemas/session.py:124-142`

---

## 10. GET /sessions/{session_id}/workdir/download

**Download session's working directory as tar.gz archive**

Creates compressed archive of all files in session's working directory and streams to client.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/workdir/download`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `200 OK` with binary tar.gz stream
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/workdir/download \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -o session-workdir.tar.gz
```

**Error - Working directory not found:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/{new_session_id}/workdir/download \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 404 Not Found
# {"detail": "Working directory not found"}
```

### Response Headers

```
Content-Type: application/gzip
Content-Disposition: attachment; filename="f47ac10b-58cc-4372-a567-0e02b2c3d479-workdir.tar.gz"
```

### Backend Processing Steps

1. **Get Session and Authorize**
   - Query sessions table
   - Authorization check

2. **Verify Working Directory Exists**
   - Check `Path(session.working_directory).exists()`
   - If not exists → 404 Not Found

3. **Create Temporary Archive**
   - Create temporary file with `.tar.gz` suffix
   - Open tarfile in write:gz mode
   - Add entire working directory recursively
   - Use directory name as archive root (arcname)
   - Close tarfile

4. **Stream Response**
   - Define generator function to read temp file in chunks
   - Create StreamingResponse:
     - media_type = "application/gzip"
     - Content-Disposition header with filename
     - Stream from temp file

5. **Schedule Cleanup**
   - Create async task to delete temp file after 10 seconds
   - Allows download to complete before cleanup
   - Ignore errors if cleanup fails

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Not Found | 404 | Working directory doesn't exist | `{"detail": "Working directory not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized to access this session"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:638-707`
- **Cleanup Function**: `app/api/v1/sessions.py:700-706`

---

# Advanced Operations

## 11. POST /sessions/{session_id}/fork

**Create a new session forked from existing session**

Creates independent copy of session with same configuration, optionally copying working directory files.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions/{session_id}/fork`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID - parent session)
- **Request Body**: `SessionForkRequest`
- **Success Response**: `201 Created` with `SessionResponse` (new session)
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success - Fork with working directory copy:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/fork \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Experiment with alternative approach",
    "include_working_directory": true
  }'
```

**Success - Fork without files:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-.../fork \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Clean fork",
    "include_working_directory": false
  }'
```

**Success - Fork at specific message:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-.../fork \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "fork_at_message": 5,
    "include_working_directory": true
  }'
```

### Request Schema

```json
{
  "name": "string (optional)",
  "fork_at_message": "integer (optional, message index to fork from)",
  "include_working_directory": "boolean (optional, default: true)"
}
```

### Response Schema

New session with:
- New UUID
- status = "created"
- parent_session_id = original session ID
- is_fork = true
- All other config copied from parent

```json
{
  "id": "new-uuid-...",
  "user_id": "same-as-parent",
  "name": "Experiment with alternative approach",
  "status": "created",
  "parent_session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "is_fork": true,
  "message_count": 0,
  "...": "...",
  "_links": {
    "self": "/api/v1/sessions/{new-id}",
    "parent": "/api/v1/sessions/f47ac10b-...",
    "query": "/api/v1/sessions/{new-id}/query"
  }
}
```

### Backend Processing Steps

1. **Get Parent Session and Authorize**
   - Query sessions table for parent
   - Authorization check

2. **Create Forked Session**
   - Call `SessionService.fork_session_advanced()`
   - Generate new UUID
   - Create Session entity with:
     - mode = SessionMode.FORKED
     - sdk_options = copy of parent's sdk_options
     - parent_session_id = parent.id
     - is_fork = true
     - name = provided or "{parent.name} (fork)"

3. **Create New Working Directory**
   - Call `StorageManager.create_working_directory(new_session_id)`
   - Create at `data/agent-workdirs/active/{new-id}`

4. **Copy Working Directory Files** (if include_working_directory=true)
   - Check if parent.working_directory_path exists
   - If yes:
     - Recursively iterate all files in parent workdir
     - Copy each file to corresponding path in new workdir
     - Preserve directory structure
     - Use shutil.copy2 (preserves metadata)
   - Log success/failure (don't fail fork if copy fails)

5. **Audit Logging**
   - Call `AuditService.log_session_forked()`
   - Record: new session_id, parent_session_id, user_id, fork_at_message

6. **Commit Transaction**

7. **Return Response**
   - Convert new session to SessionResponse
   - Add HATEOAS links including "parent" link
   - 201 Created status

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | Parent session doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own parent session | `{"detail": "Not authorized to access this session"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:711-765`
- **Service**: `app/services/session_service.py:351-403`

---

## 12. POST /sessions/{session_id}/archive

**Archive session's working directory to storage**

Compresses working directory and uploads to S3 or local filesystem for long-term storage.

### Endpoint Details

- **Method**: `POST`
- **Path**: `/api/v1/sessions/{session_id}/archive`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Request Body**: `SessionArchiveRequest`
- **Success Response**: `200 OK` with `ArchiveMetadataResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `400 Bad Request`

### cURL Examples

**Success - Archive to S3:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/archive \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "upload_to_s3": true,
    "compression": "gzip"
  }'
```

**Success - Archive to local filesystem:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/f47ac10b-.../archive \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{
    "upload_to_s3": false
  }'
```

**Error - No working directory:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{new_session_id}/archive \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN" \
  -d '{}'

# Response: 400 Bad Request
# {"detail": "Session {id} has no working directory"}
```

### Request Schema

```json
{
  "upload_to_s3": "boolean (optional, default: true)",
  "compression": "string (optional, default: 'gzip')"
}
```

### Response Schema

```json
{
  "id": "archive-uuid",
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "archive_path": "s3://bucket/archives/session-f47ac10b-....tar.gz",
  "size_bytes": 1048576,
  "compression": "gzip",
  "manifest": {
    "files": [
      {"path": "main.py", "size": 1024},
      {"path": "requirements.txt", "size": 128},
      {"path": "data/output.json", "size": 512}
    ],
    "total_files": 3,
    "total_size": 1664
  },
  "status": "completed",
  "error_message": null,
  "archived_at": "2025-10-20T11:00:00Z",
  "created_at": "2025-10-20T11:00:00Z",
  "updated_at": "2025-10-20T11:00:00Z"
}
```

### Backend Processing Steps

1. **Get Session and Authorize**
   - Query sessions table
   - Authorization check

2. **Validate Working Directory**
   - Check session.working_directory_path is set
   - If not → 400 Bad Request
   - Check Path(working_directory).exists()
   - If not → 400 Bad Request

3. **Create StorageArchiver**
   - Determine provider:
     - If upload_to_s3=true AND settings.storage_provider="s3" → "s3"
     - Otherwise → "filesystem"
   - Create StorageArchiver instance:
     - For S3: Configure bucket, region from settings
     - For filesystem: Use local path

4. **Archive Working Directory**
   - Call `archiver.archive_working_directory()`:
     - Create tar.gz of all files
     - Generate manifest (list of files with sizes)
     - Calculate total size in bytes
     - Upload to storage:
       - S3: PUT object to s3://bucket/archives/session-{id}.tar.gz
       - Filesystem: Write to data/archives/session-{id}.tar.gz
     - Return ArchiveMetadata with path, size, manifest

5. **Persist Archive Metadata**
   - Insert into `working_directory_archives` table:
     - session_id
     - archive_path (S3 URL or file path)
     - size_bytes
     - compression
     - manifest (JSON)
     - status = "completed"
     - archived_at = now()

6. **Audit Logging**
   - Call `AuditService.log_session_archived()`
   - Record: session_id, user_id, archive_path, size

7. **Commit Transaction**

8. **Return Response**
   - Convert ArchiveMetadata to ArchiveMetadataResponse

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | session_id doesn't exist | `{"detail": "Session {id} not found"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized"}` |
| Bad Request | 400 | No working directory | `{"detail": "Session {id} has no working directory"}` |
| Bad Request | 400 | Working directory doesn't exist | `{"detail": "Working directory {path} does not exist"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:768-825`
- **Service**: `app/services/session_service.py:405-464`
- **Archiver**: `app/claude_sdk/persistence/storage_archiver.py`

---

## 13. GET /sessions/{session_id}/archive

**Get archive metadata for a session**

Retrieves information about session's archived working directory.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/archive`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `200 OK` with `ArchiveMetadataResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/archive \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Error - No archive exists:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/{session_id}/archive \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 404 Not Found
# {"detail": "No archive found for session {id}"}
```

### Response Schema

Same as POST /archive response (ArchiveMetadataResponse)

### Backend Processing Steps

1. **Get Session and Authorize**
   - Query sessions table
   - Authorization check

2. **Query Archive Metadata**
   - SELECT from `working_directory_archives` table
   - WHERE session_id = {session_id}
   - ORDER BY created_at DESC (get most recent)

3. **Check If Exists**
   - If no archives found → 404 Not Found

4. **Return Response**
   - Take first archive (most recent)
   - Convert to ArchiveMetadataResponse
   - Return with 200 OK

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | Session doesn't exist | `{"detail": "Session {id} not found"}` |
| Not Found | 404 | No archive for session | `{"detail": "No archive found for session {id}"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:828-872`
- **Repository**: `app/repositories/working_directory_archive_repository.py`

---

## 14. GET /sessions/{session_id}/hooks

**Get hook execution history for a session**

Retrieves list of all hook callbacks that executed during session, with input/output data.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/hooks`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Query Parameters**:
  - `limit` (optional): Number of hooks to return (1-100, default: 50)
- **Success Response**: `200 OK` with array of `HookExecutionResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/hooks?limit=20" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
[
  {
    "id": "hook-uuid",
    "session_id": "f47ac10b-...",
    "hook_type": "PreToolUse",
    "hook_name": "audit_hook",
    "tool_use_id": "tool_use_abc123",
    "input_data": {
      "tool_name": "bash",
      "tool_input": {"command": "ls -la"}
    },
    "output_data": {
      "logged": true,
      "audit_id": "..."
    },
    "continue_execution": true,
    "executed_at": "2025-10-20T10:36:10Z",
    "duration_ms": 12
  },
  {
    "id": "hook-uuid-2",
    "session_id": "f47ac10b-...",
    "hook_type": "PostToolUse",
    "hook_name": "cost_tracking_hook",
    "tool_use_id": "tool_use_abc123",
    "input_data": {
      "tool_result": {...},
      "usage": {"input_tokens": 100, "output_tokens": 50}
    },
    "output_data": {
      "cost_added": 0.0045,
      "total_cost": 0.0123
    },
    "continue_execution": true,
    "executed_at": "2025-10-20T10:36:11Z",
    "duration_ms": 8
  }
]
```

### Hook Types

- **PreToolUse**: Executed before tool runs
- **PostToolUse**: Executed after tool completes

### Backend Processing Steps

1. **Get Session and Authorize**
2. **Query Hook Executions**
   - SELECT from `hook_executions` table
   - WHERE session_id = {session_id}
   - ORDER BY executed_at DESC
   - LIMIT {limit}
3. **Convert and Return**
   - Convert each to HookExecutionResponse
   - Return array

### Error Scenarios

Same as other data access endpoints (404, 403)

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:875-911`
- **Repository**: `app/repositories/hook_execution_repository.py`
- **Schema**: `app/schemas/session.py:159-174`

---

## 15. GET /sessions/{session_id}/permissions

**Get permission decision history for a session**

Retrieves list of all permission decisions made during tool execution.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/permissions`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Query Parameters**:
  - `limit` (optional): Number of decisions to return (1-100, default: 50)
- **Success Response**: `200 OK` with array of `PermissionDecisionResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/permissions" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
[
  {
    "id": "perm-uuid",
    "session_id": "f47ac10b-...",
    "tool_name": "bash",
    "input_data": {
      "command": "rm -rf /",
      "cwd": "/workspace"
    },
    "context": {
      "allowed_tools": ["bash*"],
      "permission_mode": "default"
    },
    "decision": "deny",
    "reason": "Dangerous command pattern detected",
    "interrupted": true,
    "decided_at": "2025-10-20T10:37:00Z"
  },
  {
    "id": "perm-uuid-2",
    "session_id": "f47ac10b-...",
    "tool_name": "read_file",
    "input_data": {
      "path": "/workspace/main.py"
    },
    "context": {
      "allowed_tools": ["*"],
      "permission_mode": "default"
    },
    "decision": "allow",
    "reason": "Tool matches allowed pattern",
    "interrupted": false,
    "decided_at": "2025-10-20T10:36:55Z"
  }
]
```

### Decision Values

- **allow**: Tool execution permitted
- **deny**: Tool execution blocked

### Backend Processing Steps

1. **Get Session and Authorize**
2. **Query Permission Decisions**
   - SELECT from `permission_decisions` table
   - WHERE session_id = {session_id}
   - ORDER BY decided_at DESC
   - LIMIT {limit}
3. **Convert and Return**
   - Convert each to PermissionDecisionResponse
   - Return array

### Error Scenarios

Same as other data access endpoints (404, 403)

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:914-950`
- **Repository**: `app/repositories/permission_decision_repository.py`
- **Schema**: `app/schemas/session.py:176-190`

---

## 16. GET /sessions/{session_id}/metrics/snapshots

**Get historical metrics snapshots for a session**

Retrieves time-series data showing how session metrics evolved over time.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/metrics/snapshots`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Query Parameters**:
  - `limit` (optional): Number of snapshots to return (1-100, default: 50)
- **Success Response**: `200 OK` with array of `MetricsSnapshotResponse`
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET "http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/metrics/snapshots" \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

### Response Schema

```json
[
  {
    "id": "snapshot-uuid-3",
    "session_id": "f47ac10b-...",
    "total_messages": 12,
    "total_tool_calls": 8,
    "total_errors": 0,
    "total_retries": 0,
    "total_cost_usd": 0.0456,
    "total_input_tokens": 1250,
    "total_output_tokens": 890,
    "total_cache_creation_tokens": 0,
    "total_cache_read_tokens": 0,
    "total_duration_ms": 45000,
    "created_at": "2025-10-20T10:40:00Z"
  },
  {
    "id": "snapshot-uuid-2",
    "session_id": "f47ac10b-...",
    "total_messages": 8,
    "total_tool_calls": 5,
    "total_cost_usd": 0.0312,
    "...": "...",
    "created_at": "2025-10-20T10:35:00Z"
  },
  {
    "id": "snapshot-uuid-1",
    "session_id": "f47ac10b-...",
    "total_messages": 4,
    "total_tool_calls": 2,
    "total_cost_usd": 0.0156,
    "...": "...",
    "created_at": "2025-10-20T10:32:00Z"
  }
]
```

### Use Cases

- Track cost accumulation over time
- Identify when most tokens were consumed
- Monitor session performance trends
- Debug cost spikes

### Backend Processing Steps

1. **Get Session and Authorize**
2. **Query Metrics Snapshots**
   - SELECT from `session_metrics_snapshots` table
   - WHERE session_id = {session_id}
   - ORDER BY created_at DESC
   - LIMIT {limit}
3. **Convert and Return**
   - Convert each to MetricsSnapshotResponse
   - Return array (newest first)

### Error Scenarios

Same as other data access endpoints (404, 403)

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:953-991`
- **Repository**: `app/repositories/session_metrics_snapshot_repository.py`
- **Schema**: `app/schemas/session.py:210-228`

---

## 17. GET /sessions/{session_id}/metrics/current

**Get current real-time metrics for a session**

Retrieves up-to-date metrics from MetricsCollector, not from database.

### Endpoint Details

- **Method**: `GET`
- **Path**: `/api/v1/sessions/{session_id}/metrics/current`
- **Auth Required**: Yes
- **Path Parameters**: `session_id` (UUID)
- **Success Response**: `200 OK` with metrics object
- **Error Responses**: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`

### cURL Examples

**Success:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/f47ac10b-58cc-4372-a567-0e02b2c3d479/metrics/current \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"
```

**Error - Metrics not available:**
```bash
curl -X GET http://localhost:8000/api/v1/sessions/{new_session_id}/metrics/current \
  -H "Authorization: Bearer $AI_AGENT_ADMIN_ACCESS_TOKEN"

# Response: 404 Not Found
# {"detail": "Metrics not found for session"}
```

### Response Schema

```json
{
  "session_id": "f47ac10b-...",
  "total_messages": 12,
  "total_tool_calls": 8,
  "total_errors": 0,
  "total_retries": 0,
  "total_cost_usd": 0.0456,
  "total_input_tokens": 1250,
  "total_output_tokens": 890,
  "total_cache_creation_tokens": 0,
  "total_cache_read_tokens": 320,
  "duration_ms": 45000,
  "status": "active",
  "last_updated": "2025-10-20T10:40:15Z"
}
```

### Backend Processing Steps

1. **Get Session and Authorize**
2. **Get Real-Time Metrics**
   - Call `MetricsCollector.get_session_metrics(session_id)`
   - Retrieves from in-memory cache or computes from database
3. **Check If Available**
   - If metrics not found → 404 Not Found
4. **Return Metrics**
   - Return raw metrics dictionary

### Error Scenarios

| Error | Status | Condition | Response |
|-------|--------|-----------|----------|
| Not Found | 404 | Session doesn't exist | `{"detail": "Session {id} not found"}` |
| Not Found | 404 | Metrics not available | `{"detail": "Metrics not found for session"}` |
| Forbidden | 403 | User doesn't own session | `{"detail": "Not authorized"}` |

### Related Files

- **API Endpoint**: `app/api/v1/sessions.py:994-1034`
- **Metrics Collector**: `app/services/metrics_collector.py`

---

## Common Error Responses

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

**Cause**: Missing or invalid Bearer token

**Solution**: Include valid access token from `/api/v1/auth/login`

### 403 Forbidden

```json
{
  "detail": "Not authorized to access this session"
}
```

**Cause**: User doesn't own session and is not admin

**Solution**: Verify session belongs to authenticated user

### 404 Not Found

```json
{
  "detail": "Session {session_id} not found"
}
```

**Cause**: Session doesn't exist or was deleted (soft-deleted)

**Solution**: Verify session_id is correct

### 409 Conflict

```json
{
  "detail": "Session {session_id} is not in a valid state for messaging"
}
```

**Cause**: Attempting invalid operation for current session state

**Solution**: Check session status, resume/fork if needed

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "ensure this value has at most 50000 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

**Cause**: Request validation failed (invalid field values)

**Solution**: Check request body against schema requirements

### 429 Too Many Requests

```json
{
  "detail": "User has 5 active sessions (limit: 5)"
}
```

**Cause**: User exceeded concurrent session quota

**Solution**: Delete or terminate unused sessions

---

## Testing Strategy

### Basic Flow

1. **Login**: Get access token
2. **Create Session**: POST /sessions
3. **Send Message**: POST /sessions/{id}/query
4. **Check Status**: GET /sessions/{id}
5. **View Messages**: GET /sessions/{id}/messages
6. **View Tool Calls**: GET /sessions/{id}/tool-calls
7. **Cleanup**: DELETE /sessions/{id}

### Advanced Flow

1. Create session
2. Send multiple messages
3. Fork session: POST /sessions/{id}/fork
4. Test both branches independently
5. Compare results
6. Archive both: POST /sessions/{id}/archive
7. Download archives: GET /sessions/{id}/workdir/download

### Permission Testing

1. Create session as user
2. Try accessing as different user → 403
3. Try accessing as admin → 200 (success)
4. Verify admin can access any session
5. Verify users can only access own sessions

---

## Related Documentation

- **Feature Overview**: `/docs/features/sessions.md` - Comprehensive feature documentation
- **Authentication**: `/docs/apis/authentication/authentication-management.md`
- **WebSocket Streaming**: `/docs/apis/websocket/websocket-management.md` (coming soon)
- **API Inventory**: `/docs/apis/api-inventory.md` - Complete endpoint list

---

**Document Version:** 1.0
**Last Updated:** October 20, 2025
**Next Review:** After Phase 2 testing completion
