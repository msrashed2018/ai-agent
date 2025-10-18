# AI-Agent-API-Service - API Documentation

Complete reference for all API endpoints with curl examples and backend flow explanation.

**Base URL**: `http://localhost:8000`

**Authentication**: Most endpoints require Bearer token authentication (obtained via `/api/v1/auth/login`)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Session Management](#session-management)
3. [Task Management](#task-management)
4. [MCP Server Management](#mcp-server-management)
5. [Report Management](#report-management)
6. [Admin Endpoints](#admin-endpoints)
7. [Health Check](#health-check)

---

## Authentication

### 1. Login

**Endpoint**: `POST /api/v1/auth/login`

**Description**: Authenticate user and obtain JWT tokens (access token + refresh token).

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@default.org",
    "password": "admin123"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Backend Flow**:
1. Receive email and password from request body
2. Query `users` table to find user by email (`UserRepository.get_by_email()`)
3. If user not found, return 401 Unauthorized error
4. Verify password hash using bcrypt (`bcrypt.checkpw()`)
5. If password incorrect, return 401 Unauthorized error
6. Check if user account is deleted (`user.deleted_at is not None`)
7. If deleted, return 403 Forbidden error
8. Generate JWT access token with user_id, expiration (default 60 minutes), and type="access"
9. Generate JWT refresh token with user_id, expiration (default 7 days), and type="refresh"
10. Return both tokens with token type and expiration time

**Notes**:
- Access token expires in 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh token expires in 7 days (configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS`)
- Use access token in `Authorization: Bearer <token>` header for subsequent requests

---

### 2. Refresh Access Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Description**: Obtain a new access token using a valid refresh token (without re-entering credentials).

**curl Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Backend Flow**:
1. Receive refresh token from request body
2. Decode JWT refresh token using secret key and algorithm
3. Verify token type is "refresh" (not "access")
4. If wrong type, return 401 Unauthorized error
5. Extract user_id from token payload (`sub` claim)
6. If JWT is expired, catch `ExpiredSignatureError` and return 401 error
7. If JWT is invalid, catch `InvalidTokenError` and return 401 error
8. Query `users` table to verify user still exists (`UserRepository.get_by_id()`)
9. Check if user is deleted (`user.is_deleted`)
10. If user not found or deleted, return 401 Unauthorized error
11. Generate new JWT access token with same user_id
12. Return new access token with expiration time

**Notes**:
- Refresh tokens are long-lived (7 days default)
- Use this endpoint when access token expires to avoid requiring user to log in again
- Refresh token itself is not refreshed (use same refresh token until it expires)

---

### 3. Get Current User Info

**Endpoint**: `GET /api/v1/auth/me`

**Description**: Get information about the currently authenticated user.

**curl Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "id": "99b3e8d2-a046-4acb-8936-bcece726a92c",
  "email": "admin@default.org",
  "role": "admin",
  "created_at": "2025-10-17T20:50:47.412917+00:00"
}
```

**Backend Flow**:
1. Extract JWT access token from `Authorization: Bearer <token>` header
2. Decode and verify JWT token (handled by `get_current_active_user` dependency)
3. Extract user_id from token payload
4. Query `users` table to get full user object
5. Verify user is active (`is_active = true`) and not deleted
6. If user inactive or deleted, return 403 Forbidden error
7. Return user information (id, email, role, created_at)

**Notes**:
- Requires valid access token in Authorization header
- Used to verify authentication status and get user details
- User role is returned (admin, user, viewer) for frontend permission checks

---

## Session Management

Sessions represent persistent Claude Code interactions with their own working directories, message history, and tool call tracking.

### 1. Create Session

**Endpoint**: `POST /api/v1/sessions`

**Description**: Create a new Claude Code session with specified configuration.

**curl Example**:
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review Session",
    "description": "Review security vulnerabilities in authentication module",
    "working_directory": null,
    "allowed_tools": ["Read", "Grep", "Bash"],
    "system_prompt": "You are a security expert. Focus on finding vulnerabilities.",
    "sdk_options": {},
    "metadata": {"project": "auth-service"}
  }'
```

**Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "99b3e8d2-a046-4acb-8936-bcece726a92c",
  "name": "Code Review Session",
  "description": "Review security vulnerabilities in authentication module",
  "status": "created",
  "working_directory": "/data/agent-workdirs/active/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "allowed_tools": ["Read", "Grep", "Bash"],
  "system_prompt": "You are a security expert. Focus on finding vulnerabilities.",
  "sdk_options": {},
  "parent_session_id": null,
  "is_fork": false,
  "message_count": 0,
  "tool_call_count": 0,
  "total_cost_usd": 0.0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "created_at": "2025-10-18T03:00:00Z",
  "updated_at": "2025-10-18T03:00:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "metadata": {"project": "auth-service"},
  "_links": {
    "self": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "query": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/query",
    "messages": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages",
    "tool_calls": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/tool-calls",
    "stream": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/stream"
  }
}
```

**Backend Flow**:
1. Extract and verify JWT token from Authorization header
2. Get current user from token (user_id, permissions)
3. Parse request body (name, description, working_directory, allowed_tools, system_prompt, sdk_options, metadata)
4. Call `SDKIntegratedSessionService.create_session()` with user_id and configuration
5. Validate user quotas (check `max_concurrent_sessions` limit)
6. If quota exceeded, return 429 Too Many Requests error
7. Create Session domain entity with unique UUID, user_id, mode="interactive", status="created"
8. If parent_session_id provided, mark as fork and set parent reference
9. Create working directory on filesystem (`/data/agent-workdirs/active/{session_id}`)
10. Convert domain entity to SessionModel (ORM model)
11. Insert SessionModel into `sessions` table via database session
12. Create audit log entry for session creation (`audit_logs` table)
13. Commit database transaction
14. Build HATEOAS links (self, query, messages, tool_calls, stream)
15. Return SessionResponse with all session details

**Notes**:
- Session is created but NOT started (status="created")
- Claude SDK client is initialized on first message, not at creation
- Working directory is created immediately and persists throughout session lifecycle
- All fields except name are optional
- System prompt overrides default Claude Code system prompt if provided

---

### 2. Get Session

**Endpoint**: `GET /api/v1/sessions/{session_id}`

**Description**: Retrieve detailed information about a specific session.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X GET "http://localhost:8000/api/v1/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: Same structure as Create Session response

**Backend Flow**:
1. Extract session_id from URL path parameter
2. Extract and verify JWT token, get current user
3. Query `sessions` table by session_id (`SessionRepository.get_by_id()`)
4. If session not found, return 404 Not Found error
5. Check ownership: compare session.user_id with current_user.id
6. If user is not owner AND not admin, return 403 Forbidden error
7. Convert SessionModel to SessionResponse (domain entity to DTO)
8. Build HATEOAS links based on session status
9. Return session details

**Notes**:
- Only session owner or admin users can access session details
- Includes full statistics (message_count, tool_call_count, tokens, cost)
- HATEOAS links guide next possible actions based on session state

---

### 3. List Sessions

**Endpoint**: `GET /api/v1/sessions`

**Description**: List all sessions for the authenticated user with pagination and filtering.

**curl Example**:
```bash
TOKEN="your_access_token_here"

# List all sessions (first page)
curl -X GET "http://localhost:8000/api/v1/sessions?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/sessions?status=active&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Filter by fork status
curl -X GET "http://localhost:8000/api/v1/sessions?is_fork=true&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "items": [
    {
      "id": "session-1-uuid",
      "name": "Session 1",
      "status": "active",
      "_links": {
        "self": "/api/v1/sessions/session-1-uuid",
        "query": "/api/v1/sessions/session-1-uuid/query"
      }
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Backend Flow**:
1. Extract and verify JWT token, get current user
2. Parse query parameters: status, is_fork, page, page_size
3. Calculate offset from page number: `offset = (page - 1) * page_size`
4. Query `sessions` table filtered by user_id with offset and limit
5. Apply additional filters (status, is_fork) in memory or database
6. Get total count of matching sessions
7. Convert each SessionModel to SessionResponse
8. Build HATEOAS links for each session (self, query)
9. Build pagination metadata (total, page, page_size, total_pages)
10. Return paginated response with items and metadata

**Notes**:
- Default page_size is 20, maximum is 100
- Only returns sessions owned by authenticated user (unless admin)
- Filters are optional and can be combined

---

### 4. Send Message (Query Session)

**Endpoint**: `POST /api/v1/sessions/{session_id}/query`

**Description**: Send a user message to Claude Code SDK and get AI response. This is the main endpoint for interacting with Claude.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X POST "http://localhost:8000/api/v1/sessions/$SESSION_ID/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please analyze the authentication code for SQL injection vulnerabilities",
    "fork": false
  }'
```

**Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "processing",
  "parent_session_id": null,
  "is_fork": false,
  "message_id": "msg-uuid-1234",
  "_links": {
    "self": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/messages/msg-uuid-1234",
    "stream": "/api/v1/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/stream"
  }
}
```

**Backend Flow**:
1. Extract session_id from URL and JWT token for user authentication
2. Parse request body: message (required, 1-50000 chars), fork (optional, default false)
3. Query `sessions` table to get session by ID
4. If session not found, return 404 Not Found error
5. Check ownership (session.user_id == current_user.id OR user is admin)
6. If not authorized, return 403 Forbidden error
7. If fork=true, call `SDKIntegratedSessionService.fork_session()`:
   - Create new session as child of current session
   - Copy working directory to new location
   - Copy all messages and tool calls to new session
   - Set parent_session_id and is_fork=true
8. Call `SDKIntegratedSessionService.send_message()` with session_id and message_content
9. Get or create Claude SDK client for this session
10. Initialize SDK client if first message (load MCP servers, set working directory)
11. Create MessageModel with type="user", content=message, save to `messages` table
12. Send message to Claude SDK via subprocess/CLI
13. Stream response from Claude SDK
14. For each response chunk, parse and process:
    - Text content: add to message buffer
    - Tool use: create ToolCallModel, save to `tool_calls` table
    - Tool result: update ToolCallModel with output
15. Save complete AI response as MessageModel with type="assistant"
16. Update session metrics (total_messages, total_tool_calls, total_cost_usd, tokens)
17. Update session status to "processing" during execution, "active" when complete
18. Broadcast to WebSocket subscribers if any connected
19. Return SessionQueryResponse with new message_id and updated session status

**Notes**:
- This is the PRIMARY endpoint for Claude Code interaction
- Message is REQUIRED (cannot be empty)
- If fork=true, creates new session before sending message
- Response is asynchronous - use WebSocket stream or polling messages endpoint for real-time updates
- Claude SDK executes in subprocess, communicates via stdio
- All tool calls are logged and tracked

---

### 5. List Messages

**Endpoint**: `GET /api/v1/sessions/{session_id}/messages`

**Description**: Retrieve message history for a session in reverse chronological order.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Get latest 50 messages
curl -X GET "http://localhost:8000/api/v1/sessions/$SESSION_ID/messages?limit=50" \
  -H "Authorization: Bearer $TOKEN"

# Get messages before specific message ID (pagination)
curl -X GET "http://localhost:8000/api/v1/sessions/$SESSION_ID/messages?limit=50&before_id=msg-uuid" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
[
  {
    "id": "msg-uuid-2",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message_type": "assistant",
    "content": {"text": "I found 3 SQL injection vulnerabilities..."},
    "model": "claude-sonnet-4-5-20250929",
    "parent_tool_use_id": null,
    "sequence_number": 2,
    "created_at": "2025-10-18T03:05:00Z"
  },
  {
    "id": "msg-uuid-1",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message_type": "user",
    "content": {"text": "Please analyze the authentication code for SQL injection vulnerabilities"},
    "model": null,
    "parent_tool_use_id": null,
    "sequence_number": 1,
    "created_at": "2025-10-18T03:02:00Z"
  }
]
```

**Backend Flow**:
1. Extract session_id from URL, JWT token for authentication
2. Parse query parameters: limit (default 50, max 100), before_id (optional)
3. Query `sessions` table to verify session exists
4. If session not found, return 404 Not Found error
5. Check ownership (session.user_id == current_user.id OR user is admin)
6. If not authorized, return 403 Forbidden error
7. Query `messages` table filtered by session_id, ordered by created_at DESC
8. If before_id provided, add filter: created_at < (message with before_id).created_at
9. Apply limit to query
10. Convert each MessageModel to MessageResponse
11. Return array of messages (newest first)

**Notes**:
- Messages ordered by newest first (reverse chronological)
- Use before_id for cursor-based pagination
- message_type can be: "user", "assistant", "system", "result"
- Content is JSONB and can contain text, tool_use, tool_result structures

---

### 6. List Tool Calls

**Endpoint**: `GET /api/v1/sessions/{session_id}/tool-calls`

**Description**: Retrieve all tool calls made during a session.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X GET "http://localhost:8000/api/v1/sessions/$SESSION_ID/tool-calls?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
[
  {
    "id": "tool-call-uuid-1",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message_id": "msg-uuid-2",
    "tool_name": "Read",
    "tool_use_id": "toolu_123abc",
    "tool_input": {"file_path": "/src/auth.py"},
    "tool_output": {"content": "def authenticate(user, password):\n  query = f\"SELECT * FROM users WHERE name='{user}'\"..."},
    "status": "success",
    "is_error": false,
    "error_message": null,
    "permission_decision": "allow",
    "permission_reason": null,
    "started_at": "2025-10-18T03:03:00Z",
    "completed_at": "2025-10-18T03:03:01Z",
    "duration_ms": 1000,
    "created_at": "2025-10-18T03:03:00Z",
    "updated_at": "2025-10-18T03:03:01Z"
  }
]
```

**Backend Flow**:
1. Extract session_id from URL, verify JWT token
2. Parse query parameter: limit (default 50, max 100)
3. Query `sessions` table to verify session exists
4. Check ownership authorization
5. Query `tool_calls` table filtered by session_id, ordered by created_at DESC
6. Apply limit to query
7. Convert each ToolCallModel to ToolCallResponse
8. Return array of tool calls

**Notes**:
- Tool calls ordered by newest first
- Includes input, output, status, duration, permission decisions
- status values: "pending", "running", "success", "error", "denied"
- permission_decision values: "allow", "deny", "ask"

---

### 7. Pause Session

**Endpoint**: `POST /api/v1/sessions/{session_id}/pause`

**Description**: Pause an active session temporarily (stops Claude SDK execution).

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X POST "http://localhost:8000/api/v1/sessions/$SESSION_ID/pause" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: Session object with status="paused"

**Backend Flow**:
1. Extract session_id from URL, verify JWT token
2. Query `sessions` table to get session
3. If session not found, return 404 Not Found error
4. Check ownership authorization
5. Call `SDKIntegratedSessionService.pause_session()` with session_id
6. Validate current status allows pausing (must be "active" or "processing")
7. If invalid status, return 409 Conflict error
8. Send pause/stop signal to Claude SDK subprocess if running
9. Update session status to "paused" in database
10. Update updated_at timestamp
11. Commit database transaction
12. Build HATEOAS links (self, resume)
13. Return updated session

**Notes**:
- Can only pause active or processing sessions
- SDK subprocess is stopped but not terminated
- Working directory and message history preserved
- Use resume endpoint to continue

---

### 8. Resume Session

**Endpoint**: `POST /api/v1/sessions/{session_id}/resume`

**Description**: Resume a paused or completed session.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X POST "http://localhost:8000/api/v1/sessions/$SESSION_ID/resume" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fork": false
  }'
```

**Response**: Session object with status="active"

**Backend Flow**:
1. Extract session_id from URL, verify JWT token
2. Parse request body: fork (optional, default false)
3. Query `sessions` table to get session
4. If session not found, return 404 Not Found error
5. Check ownership authorization
6. If fork=true, call `fork_session()` and return new forked session
7. If fork=false, validate session is paused or completed (not already active)
8. If already active, return 409 Conflict error
9. Call `SDKIntegratedSessionService.resume_session()` with session_id
10. Reinitialize Claude SDK client with existing session context
11. Reload message history into SDK client
12. Update session status to "active" in database
13. Update updated_at timestamp
14. Commit database transaction
15. Build HATEOAS links (self, query, messages)
16. Return updated session

**Notes**:
- Can resume paused or completed sessions
- If fork=true, creates new session instead of resuming existing
- Message history is preserved and reloaded
- Working directory remains the same

---

### 9. Terminate Session

**Endpoint**: `DELETE /api/v1/sessions/{session_id}`

**Description**: Permanently terminate a session and clean up resources.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X DELETE "http://localhost:8000/api/v1/sessions/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: 204 No Content (empty body)

**Backend Flow**:
1. Extract session_id from URL, verify JWT token
2. Query `sessions` table to get session
3. If session not found, return 404 Not Found error
4. Check ownership authorization
5. Call `SDKIntegratedSessionService.terminate_session()` with session_id
6. Stop Claude SDK subprocess if running (send SIGTERM, then SIGKILL if needed)
7. Close WebSocket connections for this session
8. Update session status to "terminated" in database
9. Set deleted_at timestamp (soft delete)
10. Archive working directory (move from active/ to archives/)
11. Commit database transaction
12. Return 204 No Content

**Notes**:
- Permanently ends the session (cannot be resumed)
- Working directory is archived, not deleted
- Messages and tool calls remain in database (soft delete)
- SDK subprocess is forcefully terminated

---

### 10. Download Working Directory

**Endpoint**: `GET /api/v1/sessions/{session_id}/workdir/download`

**Description**: Download session working directory as tar.gz archive.

**curl Example**:
```bash
TOKEN="your_access_token_here"
SESSION_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"

curl -X GET "http://localhost:8000/api/v1/sessions/$SESSION_ID/workdir/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o session-workdir.tar.gz
```

**Response**: Binary tar.gz file stream

**Backend Flow**:
1. Extract session_id from URL, verify JWT token
2. Query `sessions` table to get session
3. If session not found, return 404 Not Found error
4. Check ownership authorization
5. Get working directory path from session.working_directory_path
6. Check if working directory exists on filesystem
7. If directory not found, return 404 Not Found error
8. Create temporary tar.gz file
9. Add all files from working directory to tar archive with compression
10. Create StreamingResponse with tar.gz file
11. Set Content-Disposition header: `attachment; filename="{session_id}-workdir.tar.gz"`
12. Stream file contents to client
13. Schedule cleanup of temporary file after 10 seconds
14. Return streaming response

**Notes**:
- Working directory contains all files created/modified by Claude during session
- Archive preserves directory structure
- Large directories may take time to compress
- Temporary file is automatically cleaned up after download

---

## Task Management

Tasks are reusable templates with prompt templates that can be executed manually or scheduled. Unlike sessions which require direct user messages, tasks use pre-defined prompts with variable substitution.

### 1. Create Task

**Endpoint**: `POST /api/v1/tasks`

**Description**: Create a new task template with prompt template and configuration.

**curl Example**:
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Security Audit Task",
    "description": "Automated security audit for codebase",
    "prompt_template": "Analyze {{directory}} for security vulnerabilities. Focus on {{vulnerability_type}}.",
    "allowed_tools": ["Read", "Grep", "Bash"],
    "sdk_options": {},
    "is_scheduled": true,
    "schedule_cron": "0 2 * * *",
    "schedule_enabled": true,
    "generate_report": true,
    "report_format": "html",
    "notification_config": {"email": "security@company.com"},
    "tags": ["security", "automated"],
    "metadata": {"priority": "high"}
  }'
```

**Response**:
```json
{
  "id": "task-uuid-1234",
  "user_id": "99b3e8d2-a046-4acb-8936-bcece726a92c",
  "name": "Security Audit Task",
  "description": "Automated security audit for codebase",
  "prompt_template": "Analyze {{directory}} for security vulnerabilities. Focus on {{vulnerability_type}}.",
  "allowed_tools": ["Read", "Grep", "Bash"],
  "sdk_options": {},
  "is_scheduled": true,
  "schedule_cron": "0 2 * * *",
  "schedule_enabled": true,
  "last_executed_at": null,
  "next_scheduled_at": "2025-10-19T02:00:00Z",
  "execution_count": 0,
  "success_count": 0,
  "failure_count": 0,
  "generate_report": true,
  "report_format": "html",
  "notification_config": {"email": "security@company.com"},
  "tags": ["security", "automated"],
  "created_at": "2025-10-18T04:00:00Z",
  "updated_at": "2025-10-18T04:00:00Z",
  "metadata": {"priority": "high"},
  "_links": {
    "self": "/api/v1/tasks/task-uuid-1234",
    "execute": "/api/v1/tasks/task-uuid-1234/execute",
    "executions": "/api/v1/tasks/task-uuid-1234/executions"
  }
}
```

**Backend Flow**:
1. Extract and verify JWT token from Authorization header
2. Get current user from token
3. Parse request body (name, prompt_template, allowed_tools, schedule settings, etc.)
4. Call `TaskService.create_task()` with user_id and task configuration
5. Create Task domain entity with unique UUID, user_id, and all configuration
6. If is_scheduled=true, validate schedule_cron expression format
7. Calculate next_scheduled_at from cron expression
8. Convert domain entity to TaskModel (ORM model)
9. Insert TaskModel into `tasks` table
10. If schedule_enabled=true, register task with Celery Beat scheduler
11. Commit database transaction
12. Build HATEOAS links (self, execute, executions)
13. Return TaskResponse with task details

**Notes**:
- prompt_template uses {{variable}} syntax for substitution
- Tasks can be manual-only (is_scheduled=false) or scheduled
- Cron expression follows standard format: `minute hour day month weekday`
- Schedule can be disabled without deleting task (schedule_enabled=false)
- generate_report=true creates report after each execution

---

### 2. Get Task

**Endpoint**: `GET /api/v1/tasks/{task_id}`

**Description**: Retrieve task details and statistics.

**curl Example**:
```bash
TOKEN="your_access_token_here"
TASK_ID="task-uuid-1234"

curl -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: Same structure as Create Task response

**Backend Flow**:
1. Extract task_id from URL path parameter
2. Extract and verify JWT token, get current user
3. Query `tasks` table by task_id (`TaskRepository.get_by_id()`)
4. If task not found, return 404 Not Found error
5. Check ownership: compare task.user_id with current_user.id
6. If user is not owner AND not admin, return 403 Forbidden error
7. Convert TaskModel to TaskResponse
8. Build HATEOAS links (self, execute, executions)
9. Return task details with execution statistics

**Notes**:
- Only task owner or admin can access task details
- Includes execution statistics (execution_count, success_count, failure_count)
- Shows next scheduled execution time if scheduled

---

### 3. List Tasks

**Endpoint**: `GET /api/v1/tasks`

**Description**: List all tasks for authenticated user with filtering and pagination.

**curl Example**:
```bash
TOKEN="your_access_token_here"

# List all tasks
curl -X GET "http://localhost:8000/api/v1/tasks?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Filter by scheduled status
curl -X GET "http://localhost:8000/api/v1/tasks?is_scheduled=true&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Filter by tags
curl -X GET "http://localhost:8000/api/v1/tasks?tags=security&tags=automated&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "items": [
    {
      "id": "task-uuid-1",
      "name": "Security Audit Task",
      "is_scheduled": true,
      "tags": ["security", "automated"],
      "_links": {
        "self": "/api/v1/tasks/task-uuid-1",
        "execute": "/api/v1/tasks/task-uuid-1/execute"
      }
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Backend Flow**:
1. Extract and verify JWT token, get current user
2. Parse query parameters: tags (array), is_scheduled (boolean), page, page_size
3. Calculate offset from page: `offset = (page - 1) * page_size`
4. Query `tasks` table filtered by user_id with offset and limit
5. Apply additional filters:
   - If is_scheduled provided, filter by is_scheduled field
   - If tags provided, filter tasks that contain any of the specified tags
6. Get total count of matching tasks
7. Convert each TaskModel to TaskResponse
8. Build HATEOAS links for each task (self, execute)
9. Build pagination metadata (total, page, page_size, total_pages)
10. Return paginated response with items and metadata

**Notes**:
- Default page_size is 20, maximum is 100
- Only returns tasks owned by authenticated user (unless admin)
- Tags filter uses OR logic (matches any tag)
- is_scheduled filter is exact match

---

### 4. Update Task

**Endpoint**: `PATCH /api/v1/tasks/{task_id}`

**Description**: Update task configuration (all fields optional).

**curl Example**:
```bash
TOKEN="your_access_token_here"
TASK_ID="task-uuid-1234"

curl -X PATCH "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_enabled": false,
    "tags": ["security", "paused"]
  }'
```

**Response**: Updated TaskResponse object

**Backend Flow**:
1. Extract task_id from URL and JWT token
2. Parse request body (only fields to update)
3. Query `tasks` table to get task by ID
4. If task not found, return 404 Not Found error
5. Check ownership authorization
6. If not authorized, return 403 Forbidden error
7. Call `TaskService.update_task()` with task_id and update fields
8. Extract only provided fields using `model_dump(exclude_unset=True)`
9. Update TaskModel with new values
10. If schedule_cron changed, recalculate next_scheduled_at
11. If schedule_enabled changed, register/unregister with Celery Beat
12. Update updated_at timestamp
13. Commit database transaction
14. Build HATEOAS links
15. Return updated task

**Notes**:
- All fields are optional (PATCH semantics)
- Only provided fields are updated
- Changing schedule_cron automatically recalculates next_scheduled_at
- Disabling schedule (schedule_enabled=false) doesn't delete task

---

### 5. Delete Task

**Endpoint**: `DELETE /api/v1/tasks/{task_id}`

**Description**: Soft delete a task (marks as deleted but preserves data).

**curl Example**:
```bash
TOKEN="your_access_token_here"
TASK_ID="task-uuid-1234"

curl -X DELETE "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**: 204 No Content (empty body)

**Backend Flow**:
1. Extract task_id from URL, verify JWT token
2. Query `tasks` table to get task
3. If task not found, return 404 Not Found error
4. Check ownership authorization
5. If not authorized, return 403 Forbidden error
6. Call `TaskService.delete_task()` with task_id
7. Set is_deleted=true and deleted_at=current_timestamp in TaskModel
8. If task is scheduled, unregister from Celery Beat scheduler
9. Cancel any pending scheduled executions
10. Commit database transaction
11. Return 204 No Content

**Notes**:
- Soft delete preserves task and execution history
- Task won't appear in list endpoints after deletion
- Scheduled executions are cancelled
- Execution history remains accessible

---

### 6. Execute Task (Manual)

**Endpoint**: `POST /api/v1/tasks/{task_id}/execute`

**Description**: Manually trigger task execution with optional variable values. This is the KEY endpoint where Claude SDK is invoked WITHOUT direct user message.

**curl Example**:
```bash
TOKEN="your_access_token_here"
TASK_ID="task-uuid-1234"

curl -X POST "http://localhost:8000/api/v1/tasks/$TASK_ID/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "directory": "/src/authentication",
      "vulnerability_type": "SQL injection"
    }
  }'
```

**Response**:
```json
{
  "id": "execution-uuid-5678",
  "task_id": "task-uuid-1234",
  "session_id": "session-uuid-created-for-execution",
  "status": "pending",
  "trigger_type": "manual",
  "trigger_metadata": {},
  "prompt_variables": {
    "directory": "/src/authentication",
    "vulnerability_type": "SQL injection"
  },
  "error_message": null,
  "result_data": null,
  "total_messages": 0,
  "total_tool_calls": 0,
  "duration_seconds": null,
  "created_at": "2025-10-18T04:30:00Z",
  "started_at": null,
  "completed_at": null,
  "_links": {
    "self": "/api/v1/task-executions/execution-uuid-5678",
    "task": "/api/v1/tasks/task-uuid-1234",
    "session": "/api/v1/sessions/session-uuid-created-for-execution"
  }
}
```

**Backend Flow (IMPORTANT - No User Message Required)**:
1. Extract task_id from URL and JWT token
2. Parse request body: variables (optional dictionary for template substitution)
3. Query `tasks` table to get task
4. If task not found, return 404 Not Found error
5. Check ownership authorization
6. Call `TaskService.execute_task()` with task_id, trigger_type="manual", variables
7. Create TaskExecution domain entity with status="pending"
8. Create new session for this execution (`SDKIntegratedSessionService.create_session()`)
9. Insert TaskExecutionModel into `task_executions` table with session_id
10. Render prompt template with variables: replace {{variable}} with values from variables dict
   - Example: "Analyze {{directory}}" + {"directory": "/src"} → "Analyze /src"
11. Call `SDKIntegratedSessionService.send_message()` with rendered prompt
12. Initialize Claude SDK client for the session
13. Send rendered prompt to Claude SDK (NOT user message - template-generated!)
14. Update execution status to "running"
15. Process SDK response asynchronously:
    - Stream tool calls and results
    - Update execution metrics (total_messages, total_tool_calls)
    - Calculate duration
16. When complete, update execution status to "completed" or "failed"
17. If generate_report=true, create report from execution results
18. If notification_config set, send notification
19. Return TaskExecutionResponse with execution ID and session link

**Notes**:
- **NO USER MESSAGE REQUIRED** - prompt comes from template
- Variables are optional - template used as-is if not provided
- Creates dedicated session for each execution
- Execution is asynchronous - use execution ID to poll status
- Returns 202 Accepted immediately, actual execution runs in background
- Session can be accessed via session_id to see real-time progress

---

### 7. List Task Executions

**Endpoint**: `GET /api/v1/tasks/{task_id}/executions`

**Description**: Get execution history for a specific task.

**curl Example**:
```bash
TOKEN="your_access_token_here"
TASK_ID="task-uuid-1234"

curl -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID/executions?page=1&page_size=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "items": [
    {
      "id": "execution-uuid-latest",
      "task_id": "task-uuid-1234",
      "session_id": "session-uuid",
      "status": "completed",
      "trigger_type": "manual",
      "created_at": "2025-10-18T04:30:00Z",
      "started_at": "2025-10-18T04:30:05Z",
      "completed_at": "2025-10-18T04:32:00Z",
      "duration_seconds": 115,
      "_links": {
        "self": "/api/v1/task-executions/execution-uuid-latest",
        "task": "/api/v1/tasks/task-uuid-1234",
        "session": "/api/v1/sessions/session-uuid",
        "report": "/api/v1/reports/report-uuid"
      }
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

**Backend Flow**:
1. Extract task_id from URL, verify JWT token
2. Parse query parameters: page, page_size
3. Query `tasks` table to verify task exists
4. If task not found, return 404 Not Found error
5. Check ownership authorization for task
6. Query `task_executions` table filtered by task_id, ordered by created_at DESC
7. Apply pagination (offset and limit)
8. Get total count of executions for task
9. Convert each TaskExecutionModel to TaskExecutionResponse
10. Build HATEOAS links for each execution (self, task, session, report if exists)
11. Build pagination metadata
12. Return paginated response

**Notes**:
- Executions ordered by newest first
- Includes all trigger types (manual, scheduled, webhook, api)
- Links to associated session and report if generated

---

### 8. Get Task Execution

**Endpoint**: `GET /api/v1/tasks/executions/{execution_id}`

**Description**: Get detailed status and results of a specific task execution.

**curl Example**:
```bash
TOKEN="your_access_token_here"
EXECUTION_ID="execution-uuid-5678"

curl -X GET "http://localhost:8000/api/v1/tasks/executions/$EXECUTION_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "id": "execution-uuid-5678",
  "task_id": "task-uuid-1234",
  "session_id": "session-uuid",
  "report_id": "report-uuid",
  "trigger_type": "manual",
  "trigger_metadata": {},
  "prompt_variables": {
    "directory": "/src/authentication",
    "vulnerability_type": "SQL injection"
  },
  "status": "completed",
  "error_message": null,
  "result_data": {
    "vulnerabilities_found": 3,
    "files_analyzed": 15
  },
  "total_messages": 8,
  "total_tool_calls": 12,
  "duration_seconds": 115,
  "created_at": "2025-10-18T04:30:00Z",
  "started_at": "2025-10-18T04:30:05Z",
  "completed_at": "2025-10-18T04:32:00Z",
  "_links": {
    "self": "/api/v1/task-executions/execution-uuid-5678",
    "task": "/api/v1/tasks/task-uuid-1234",
    "session": "/api/v1/sessions/session-uuid",
    "report": "/api/v1/reports/report-uuid"
  }
}
```

**Backend Flow**:
1. Extract execution_id from URL, verify JWT token
2. Query `task_executions` table by execution_id
3. If execution not found, return 404 Not Found error
4. Query `tasks` table to get associated task
5. Check ownership authorization via task.user_id
6. If not authorized, return 403 Forbidden error
7. Convert TaskExecutionModel to TaskExecutionResponse
8. Build HATEOAS links (self, task, session)
9. If report_id exists, add report link
10. Return execution details

**Notes**:
- status values: "pending", "running", "completed", "failed", "cancelled"
- result_data contains custom data stored during execution
- duration_seconds is null until execution completes
- Access session via session_id link to see detailed conversation history

---

## MCP Server Management

MCP (Model Context Protocol) servers provide external tools and capabilities to Claude Code. Servers can be configured per-user or globally.

### 1. Create MCP Server

**Endpoint**: `POST /api/v1/mcp-servers`

**curl Example**:
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/mcp-servers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "filesystem-server",
    "description": "File system operations server",
    "server_type": "stdio",
    "config": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "env": {}
    },
    "is_enabled": true,
    "is_global": false
  }'
```

**Backend Flow**:
1. Verify JWT token and get current user
2. Parse MCP server configuration (name, server_type, config, is_global)
3. Validate server_type is one of: stdio, sse, http, sdk
4. If is_global=true, verify user has admin role
5. Create MCPServerModel with user_id (or null if global)
6. Insert into `mcp_servers` table
7. Return server configuration with health_status="unknown"

**Notes**:
- Global servers (is_global=true) available to all users, require admin
- server_type determines how SDK communicates with server
- config structure varies by server_type

---

### 2. List MCP Servers

**Endpoint**: `GET /api/v1/mcp-servers`

**Backend Flow**:
1. Query `mcp_servers` table for user's servers (user_id = current_user.id)
2. Include global servers (is_global=true)
3. Filter by is_enabled if provided
4. Return list of server configurations

---

### 3. Update MCP Server

**Endpoint**: `PATCH /api/v1/mcp-servers/{server_id}`

**Backend Flow**:
1. Get server by ID, check ownership
2. Update allowed fields (config, is_enabled, description)
3. Return updated server configuration

---

### 4. Delete MCP Server

**Endpoint**: `DELETE /api/v1/mcp-servers/{server_id}`

**Backend Flow**:
1. Soft delete server (set deleted_at)
2. Remove from active sessions using this server

---

### 5. Health Check MCP Server

**Endpoint**: `POST /api/v1/mcp-servers/{server_id}/health-check`

**Backend Flow**:
1. Get server configuration
2. Attempt to initialize MCP server connection
3. Send ping/health check request
4. Update health_status field (healthy/degraded/unhealthy/unknown)
5. Update last_health_check_at timestamp
6. Return health status

---

## Report Management

Reports are generated from task executions or sessions, supporting multiple formats (JSON, Markdown, HTML, PDF).

### 1. Create Report

**Endpoint**: `POST /api/v1/reports`

**curl Example**:
```bash
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-uuid",
    "title": "Security Audit Report",
    "description": "SQL injection vulnerabilities found",
    "report_type": "custom",
    "content": {
      "summary": "Found 3 vulnerabilities",
      "details": ["..."]
    },
    "file_format": "html",
    "template_name": "security-audit",
    "tags": ["security", "sql-injection"]
  }'
```

**Backend Flow**:
1. Verify session exists and user has access
2. Create ReportModel with content (JSONB)
3. If template_name provided, render template with content
4. Generate file in specified format (JSON/Markdown/HTML/PDF)
5. Save file to storage, record file_path and file_size_bytes
6. Insert into `reports` table
7. If task_execution_id provided, link report to execution
8. Return report details with download link

**Notes**:
- content is JSONB allowing flexible report structure
- file_format determines output format
- template_name loads Jinja2 template for rendering
- PDF generation uses WeasyPrint

---

### 2. Get Report

**Endpoint**: `GET /api/v1/reports/{report_id}`

**Backend Flow**:
1. Query `reports` table by report_id
2. Check ownership via session.user_id or task.user_id
3. Return report metadata (title, description, file_path, tags, etc.)

---

### 3. List Reports

**Endpoint**: `GET /api/v1/reports`

**Backend Flow**:
1. Query `reports` table filtered by user_id (via sessions or tasks)
2. Apply pagination and filters (tags, report_type, created_at range)
3. Return paginated list of reports

---

### 4. Download Report

**Endpoint**: `GET /api/v1/reports/{report_id}/download`

**curl Example**:
```bash
TOKEN="your_access_token_here"
REPORT_ID="report-uuid"

curl -X GET "http://localhost:8000/api/v1/reports/$REPORT_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.html
```

**Backend Flow**:
1. Get report by ID, check ownership
2. Verify file_path exists on filesystem
3. Stream file contents as response
4. Set Content-Disposition header with filename
5. Set appropriate Content-Type based on file_format

**Notes**:
- Supports JSON, Markdown, HTML, PDF formats
- Content-Type headers: application/json, text/markdown, text/html, application/pdf

---

## Admin Endpoints

Admin-only endpoints for system monitoring and management. Require user role="admin".

### 1. Get System Stats

**Endpoint**: `GET /api/v1/admin/stats`

**curl Example**:
```bash
TOKEN="admin_access_token"

curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "Authorization: Bearer $TOKEN"
```

**Response**:
```json
{
  "total_users": 25,
  "active_users": 20,
  "total_sessions": 150,
  "active_sessions": 12,
  "total_tasks": 45,
  "total_task_executions": 320,
  "total_reports": 180,
  "total_mcp_servers": 8,
  "total_storage_mb": 2048,
  "system_health": "healthy"
}
```

**Backend Flow**:
1. Verify user is admin (role="admin")
2. Query counts from all tables:
   - Count users (total and is_active=true)
   - Count sessions (total and status='active')
   - Count tasks, task_executions, reports, mcp_servers
3. Calculate total storage usage from working directories
4. Determine system_health based on thresholds
5. Return aggregated statistics

---

### 2. List All Sessions (Admin)

**Endpoint**: `GET /api/v1/admin/sessions`

**Backend Flow**:
1. Verify user is admin
2. Query all sessions (not filtered by user_id)
3. Apply filters: status, user_id, created_at range
4. Return paginated list with user information

**Notes**:
- Returns sessions from all users
- Useful for monitoring active sessions system-wide

---

### 3. List All Users (Admin)

**Endpoint**: `GET /api/v1/admin/users`

**Backend Flow**:
1. Verify user is admin
2. Query `users` table with pagination
3. Include user statistics (session_count, task_count, storage_used)
4. Return paginated list of users

**Notes**:
- Includes inactive and deleted users
- Shows quota usage per user

---

## Health Check

### Health Check Endpoint

**Endpoint**: `GET /health`

**curl Example**:
```bash
curl -X GET "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "service": "AI-Agent-API-Service",
  "version": "1.0.0",
  "environment": "development"
}
```

**Backend Flow**:
1. Return simple health status (no authentication required)
2. Always returns 200 OK if service is running
3. Includes service name, version, environment

**Notes**:
- Public endpoint (no authentication)
- Used by load balancers and monitoring systems
- Returns immediately (no database checks)

---

## Summary of Key Differences

### Session vs Task Execution

| Feature | Session (`/sessions/{id}/query`) | Task (`/tasks/{id}/execute`) |
|---------|----------------------------------|------------------------------|
| **User Input** | ✅ Required | ❌ Not Required |
| **Prompt Source** | User provides message directly | Template with variable substitution |
| **Use Case** | Interactive conversations | Automated/scheduled workflows |
| **Scheduling** | Not schedulable | Can be scheduled (cron) |
| **Persistence** | Long-lived, resumable | One-time execution per trigger |

### Authentication Flow

1. Login → Get access_token + refresh_token
2. Use access_token in `Authorization: Bearer <token>` header
3. When access_token expires (60 min), use refresh_token to get new access_token
4. When refresh_token expires (7 days), login again

### Common Error Responses

- **401 Unauthorized**: Missing or invalid/expired JWT token
- **403 Forbidden**: Valid token but insufficient permissions (wrong user or not admin)
- **404 Not Found**: Resource doesn't exist (session, task, report, etc.)
- **409 Conflict**: Invalid state transition (e.g., resume already active session)
- **422 Unprocessable Entity**: Validation error (invalid request body)
- **429 Too Many Requests**: Rate limit or quota exceeded

---

## Complete Workflow Example

### Creating and Executing a Security Audit Task

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@default.org","password":"admin123"}' \
  | jq -r '.access_token')

# 2. Create MCP server for filesystem access
MCP_ID=$(curl -s -X POST "http://localhost:8000/api/v1/mcp-servers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "filesystem",
    "server_type": "stdio",
    "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]},
    "is_enabled": true
  }' | jq -r '.id')

# 3. Create security audit task
TASK_ID=$(curl -s -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Security Audit",
    "prompt_template": "Analyze {{directory}} for security vulnerabilities. Focus on {{type}}.",
    "is_scheduled": true,
    "schedule_cron": "0 2 * * *",
    "schedule_enabled": true,
    "generate_report": true,
    "report_format": "html"
  }' | jq -r '.id')

# 4. Execute task manually
EXEC_ID=$(curl -s -X POST "http://localhost:8000/api/v1/tasks/$TASK_ID/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "directory": "/src/auth",
      "type": "SQL injection"
    }
  }' | jq -r '.id')

# 5. Check execution status
curl -s -X GET "http://localhost:8000/api/v1/tasks/executions/$EXEC_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.status'

# 6. Download report when complete
REPORT_ID=$(curl -s -X GET "http://localhost:8000/api/v1/tasks/executions/$EXEC_ID" \
  -H "Authorization: Bearer $TOKEN" | jq -r '._links.report' | cut -d'/' -f5)

curl -X GET "http://localhost:8000/api/v1/reports/$REPORT_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o security-audit-report.html
```

---

**END OF DOCUMENTATION**
