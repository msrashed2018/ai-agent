# AI Agent API - Complete API Inventory

> **Version:** 1.0  
> **Last Updated:** October 19, 2025  
> **Base URL:** `/api/v1`

This document provides a complete inventory of all REST API endpoints and WebSocket connections available in the AI Agent API.

---

## Table of Contents

1. [Authentication APIs](#1-authentication-apis)
2. [Session APIs](#2-session-apis)
3. [Session Template APIs](#3-session-template-apis)
4. [Task APIs](#4-task-apis)
5. [Report APIs](#5-report-apis)
6. [MCP Server APIs](#6-mcp-server-apis)
7. [Admin APIs](#7-admin-apis)
8. [WebSocket APIs](#8-websocket-apis)
9. [Monitoring APIs](#9-monitoring-apis)

---

## 1. Authentication APIs

**Base Path:** `/api/v1/auth`  
**File:** `app/api/v1/auth.py`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | Authenticate user and return JWT tokens | No |
| POST | `/auth/refresh` | Get new access token using refresh token | No |
| GET | `/auth/me` | Get current authenticated user information | Yes |

---

## 2. Session APIs

**Base Path:** `/api/v1/sessions`  
**File:** `app/api/v1/sessions.py`

### Core Session Operations

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/sessions` | Create a new interactive session | Yes |
| GET | `/sessions/{session_id}` | Get session details by ID | Yes |
| GET | `/sessions` | List user's sessions with pagination and filtering | Yes |
| POST | `/sessions/{session_id}/query` | Send a message to the session | Yes |
| DELETE | `/sessions/{session_id}` | Terminate a session and clean up resources | Yes |

### Session Control

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/sessions/{session_id}/resume` | Resume a paused or completed session | Yes |
| POST | `/sessions/{session_id}/pause` | Pause an active session | Yes |

### Session Data Access

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/sessions/{session_id}/messages` | List messages in a session | Yes |
| GET | `/sessions/{session_id}/tool-calls` | List tool calls in a session | Yes |
| GET | `/sessions/{session_id}/workdir/download` | Download working directory as tar.gz | Yes |

### Advanced Session Operations (Phase 4)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/sessions/{session_id}/fork` | Fork an existing session | Yes |
| POST | `/sessions/{session_id}/archive` | Archive session's working directory | Yes |
| GET | `/sessions/{session_id}/archive` | Get archive metadata for a session | Yes |
| GET | `/sessions/{session_id}/hooks` | Get hook execution history for a session | Yes |
| GET | `/sessions/{session_id}/permissions` | Get permission decision history for a session | Yes |
| GET | `/sessions/{session_id}/metrics/snapshots` | Get historical metrics snapshots | Yes |
| GET | `/sessions/{session_id}/metrics/current` | Get current session metrics | Yes |

**Total Session Endpoints:** 17

---

## 3. Session Template APIs

**Base Path:** `/api/v1/session-templates`  
**File:** `app/api/v1/session_templates.py`

### Template Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/session-templates` | Create a new session template | Yes |
| GET | `/session-templates/{template_id}` | Get session template by ID | Yes |
| GET | `/session-templates` | List session templates with filtering | Yes |
| PUT | `/session-templates/{template_id}` | Update session template | Yes |
| DELETE | `/session-templates/{template_id}` | Delete session template (soft delete) | Yes |

### Template Discovery

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/session-templates/search` | Search session templates | Yes |
| GET | `/session-templates/popular/top` | Get most frequently used templates | Yes |

### Template Sharing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| PATCH | `/session-templates/{template_id}/sharing` | Update template sharing settings | Yes |

**Total Template Endpoints:** 8

---

## 4. Task APIs

**Base Path:** `/api/v1/tasks`  
**File:** `app/api/v1/tasks.py`

### Task Definition Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/tasks` | Create a new task definition (template) | Yes |
| GET | `/tasks/{task_id}` | Get task details by ID | Yes |
| GET | `/tasks` | List user's tasks with pagination and filtering | Yes |
| PATCH | `/tasks/{task_id}` | Update task configuration | Yes |
| DELETE | `/tasks/{task_id}` | Delete a task | Yes |

### Task Execution

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/tasks/{task_id}/execute` | Manually execute a task | Yes |
| GET | `/tasks/{task_id}/executions` | List executions for a specific task | Yes |
| GET | `/tasks/executions/{execution_id}` | Get task execution status and details | Yes |

**Total Task Endpoints:** 8

---

## 5. Report APIs

**Base Path:** `/api/v1/reports`  
**File:** `app/api/v1/reports.py`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/reports/{report_id}` | Get report details by ID | Yes |
| GET | `/reports` | List user's reports with pagination and filtering | Yes |
| GET | `/reports/{report_id}/download` | Download report in specified format (html/pdf/json) | Yes |

**Total Report Endpoints:** 3

---

## 6. MCP Server APIs

**Base Path:** `/api/v1/mcp-servers`  
**File:** `app/api/v1/mcp_servers.py` & `app/api/v1/mcp_import_export.py`

### MCP Server Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/mcp-servers` | List all available MCP servers for user | Yes |
| POST | `/mcp-servers` | Register a new MCP server | Yes |
| GET | `/mcp-servers/{server_id}` | Get MCP server details by ID | Yes |
| PATCH | `/mcp-servers/{server_id}` | Update MCP server configuration | Yes |
| DELETE | `/mcp-servers/{server_id}` | Delete an MCP server | Yes |

### MCP Server Operations

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/mcp-servers/{server_id}/health-check` | Perform health check on MCP server | Yes |
| GET | `/mcp-servers/templates` | Get pre-configured templates for popular MCP servers | Yes |

### Claude Desktop Integration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/mcp-servers/import` | Import MCP servers from Claude Desktop config file | Yes |
| GET | `/mcp-servers/export` | Export user's MCP servers to Claude Desktop config format | Yes |

**Total MCP Endpoints:** 9

---

## 7. Admin APIs

**Base Path:** `/api/v1/admin`  
**File:** `app/api/v1/admin.py`

| Method | Endpoint | Description | Auth Required | Admin Only |
|--------|----------|-------------|---------------|------------|
| GET | `/admin/stats` | Get system-wide statistics | Yes | Yes |
| GET | `/admin/sessions` | List all sessions across all users | Yes | Yes |
| GET | `/admin/users` | List all users | Yes | Yes |

**Total Admin Endpoints:** 3

---

## 8. WebSocket APIs

**Base Path:** `/api/v1`  
**File:** `app/api/v1/websocket.py`

| Protocol | Endpoint | Description | Auth Required |
|----------|----------|-------------|---------------|
| WebSocket | `/sessions/{session_id}/stream` | Real-time session message streaming | Yes (via query param) |

### WebSocket Message Types

**Client → Server:**
- `query` - Send a message to Claude
- `ping` - Heartbeat keepalive

**Server → Client:**
- `connected` - Connection confirmation
- `message` - New message received
- `message_sent` - Confirmation message sent
- `status_change` - Session status changed
- `tool_call_started` - Tool execution started
- `tool_call_completed` - Tool execution completed
- `error` - Error occurred
- `pong` - Heartbeat response

**Total WebSocket Endpoints:** 1

---

## 9. Monitoring APIs

**Base Path:** `/api/v1/monitoring`  
**File:** `app/api/v1/monitoring.py`

### Health Check Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/monitoring/health` | Overall system health check | No |
| GET | `/monitoring/health/database` | Check database connectivity | No |
| GET | `/monitoring/health/sdk` | Check Claude SDK availability | No |
| GET | `/monitoring/health/storage` | Check storage availability | No |

### Cost Tracking Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/monitoring/costs/user/{user_id}` | Get user costs for a time period | Yes |
| GET | `/monitoring/costs/budget/{user_id}` | Get user budget status | Yes |

### Metrics Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/monitoring/metrics/session/{session_id}` | Get current metrics for a session | Yes |

**Total Monitoring Endpoints:** 7

---

## Summary Statistics

| Category | Endpoint Count |
|----------|----------------|
| Authentication | 3 |
| Sessions | 17 |
| Session Templates | 8 |
| Tasks | 8 |
| Reports | 3 |
| MCP Servers | 9 |
| Admin | 3 |
| WebSocket | 1 |
| Monitoring | 7 |
| **TOTAL** | **59** |

---

## API Review Status

- [ ] **1. Authentication APIs** - Pending Review
- [ ] **2. Session APIs** - Pending Review
- [ ] **3. Session Template APIs** - Pending Review
- [ ] **4. Task APIs** - Pending Review
- [ ] **5. Report APIs** - Pending Review
- [ ] **6. MCP Server APIs** - Pending Review
- [ ] **7. Admin APIs** - Pending Review
- [ ] **8. WebSocket APIs** - Pending Review
- [ ] **9. Monitoring APIs** - Pending Review

---

## Next Steps

Each API group will be reviewed for:
1. **Code Quality** - Structure, readability, best practices
2. **Error Handling** - Proper exception handling and status codes
3. **Security** - Authentication, authorization, input validation
4. **Performance** - Database queries, N+1 problems, caching
5. **Documentation** - Docstrings, comments, type hints
6. **Testing** - Test coverage and edge cases
7. **Architecture** - Separation of concerns, dependency injection
8. **Enhancements** - Suggested improvements and optimizations

---

**Generated:** October 19, 2025  
**Total APIs:** 59 REST endpoints + 1 WebSocket endpoint = **60 total endpoints**

