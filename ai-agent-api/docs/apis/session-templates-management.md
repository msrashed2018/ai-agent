# Session Template Management APIs

**Base URL:** `http://localhost:8000/api/v1/session-templates`  
**Authentication:** All endpoints require Bearer token in `Authorization` header

---

## Table of Contents

1. [Create Template](#1-create-template)
2. [Get Template by ID](#2-get-template-by-id)
3. [List Templates](#3-list-templates)
4. [Search Templates](#4-search-templates)
5. [Get Most Used Templates](#5-get-most-used-templates)
6. [Update Template](#6-update-template)
7. [Update Sharing Settings](#7-update-sharing-settings)
8. [Delete Template](#8-delete-template)

---

## 1. Create Template

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/session-templates` |
| **Status Code** | 201 Created |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/session-templates \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Development Template",
    "description": "Template for Python development with common tools",
    "category": "development",
    "system_prompt": "You are a helpful Python development assistant.",
    "working_directory": "/workspace/python-projects",
    "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
    "sdk_options": {
      "model": "claude-3-5-sonnet-20241022",
      "max_turns": 20,
      "permission_mode": "default"
    },
    "tags": ["python", "development", "coding"],
    "is_public": false,
    "is_organization_shared": false
  }'
```

### Response Example

```json
{
  "id": "79277700-4856-4281-b743-29445311f207",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Python Development Template",
  "description": "Template for Python development with common tools",
  "category": "development",
  "system_prompt": "You are a helpful Python development assistant.",
  "working_directory": "/workspace/python-projects",
  "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_turns": 20,
    "permission_mode": "default"
  },
  "mcp_server_ids": [],
  "is_public": false,
  "is_organization_shared": false,
  "version": "1.0.0",
  "tags": ["python", "development", "coding"],
  "template_metadata": {},
  "usage_count": 0,
  "last_used_at": null,
  "created_at": "2025-10-19T11:36:56.649628",
  "updated_at": "2025-10-19T11:36:56.649633",
  "_links": {
    "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `create_template()` in `app/api/v1/session_templates.py` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency extracts user from JWT token |
| 3 | Validation | Validate Request | Pydantic schema validates all required fields and data types |
| 4 | Domain Logic | Create Entity | `SessionTemplateService.create_template()` creates domain entity |
| 5 | Repository | Persist Data | `SessionTemplateRepository.create()` saves to PostgreSQL database |
| 6 | Audit Log | Record Action | `AuditService.log()` records template creation for compliance |
| 7 | Response Mapping | Convert to DTO | Template entity converted to `SessionTemplateResponse` schema |
| 8 | HATEOAS | Add Links | Response links generated with template ID |
| 9 | Return | Send Response | FastAPI returns 201 with response body |

---

## 2. Get Template by ID

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/session-templates/{template_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/session-templates/79277700-4856-4281-b743-29445311f207 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "id": "79277700-4856-4281-b743-29445311f207",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Python Development Template",
  "description": "Template for Python development with common tools",
  "category": "development",
  "system_prompt": "You are a helpful Python development assistant.",
  "working_directory": "/workspace/python-projects",
  "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_turns": 20,
    "permission_mode": "default"
  },
  "mcp_server_ids": [],
  "is_public": false,
  "is_organization_shared": false,
  "version": "1.0.0",
  "tags": ["python", "development", "coding"],
  "template_metadata": {},
  "usage_count": 0,
  "last_used_at": null,
  "created_at": "2025-10-19T08:36:56.649628Z",
  "updated_at": "2025-10-19T08:36:56.649633Z",
  "_links": {
    "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207",
    "update": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207",
    "delete": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207",
    "create_session": "/api/v1/sessions?template_id=79277700-4856-4281-b743-29445311f207"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_template()` handler receives template_id as UUID |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Repository Query | Fetch Template | `SessionTemplateRepository.get_by_id(template_id)` queries database |
| 4 | Validation | Check Existence | If template_id not found, raise 404 TemplateNotFoundError |
| 5 | Authorization | Check Access | `SessionTemplateService.get_template()` validates user has access (owner, public, or org-shared) |
| 6 | Response Mapping | Convert to DTO | Template entity converted to `SessionTemplateResponse` |
| 7 | HATEOAS | Build Links | All available action links added (self, update, delete, create_session) |
| 8 | Return | Send Response | FastAPI returns 200 with full template details |

---

## 3. List Templates

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/session-templates` |
| **Query Parameters** | `scope`, `category`, `page`, `page_size` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/session-templates?scope=accessible&category=development&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "items": [
    {
      "id": "79277700-4856-4281-b743-29445311f207",
      "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
      "name": "Python Development Template",
      "description": "Template for Python development with common tools",
      "category": "development",
      "system_prompt": "You are a helpful Python development assistant.",
      "working_directory": "/workspace/python-projects",
      "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
      "sdk_options": {
        "model": "claude-3-5-sonnet-20241022",
        "max_turns": 20,
        "permission_mode": "default"
      },
      "mcp_server_ids": [],
      "is_public": false,
      "is_organization_shared": false,
      "version": "1.0.0",
      "tags": ["python", "development", "coding"],
      "template_metadata": {},
      "usage_count": 0,
      "last_used_at": null,
      "created_at": "2025-10-19T08:36:56.649628Z",
      "updated_at": "2025-10-19T08:36:56.649633Z",
      "_links": {
        "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Parse Parameters | Extract `scope`, `category`, `page`, `page_size` from query string |
| 2 | Authentication | Validate Token | Current user extracted from JWT token |
| 3 | Scope Logic | Determine Query Type | Based on scope param: "my" (own), "public" (all public), or "accessible" (all user can see) |
| 4 | Repository Query | Fetch Templates | Call appropriate service method based on scope |
| 5 | Filtering | Apply Category Filter | If category provided, filter results by category enum |
| 6 | Pagination | Apply Offset/Limit | Calculate offset from page: `(page - 1) * page_size` |
| 7 | Database Query | Execute Query | PostgreSQL query with filters and pagination |
| 8 | Response Mapping | Convert All | Each template entity converted to `SessionTemplateResponse` |
| 9 | Pagination Info | Calculate Totals | `total_pages = (total + page_size - 1) // page_size` |
| 10 | HATEOAS | Add Links | Each item gets self link with template ID |
| 11 | Return | Send Response | FastAPI returns paginated response with items array |

---

## 4. Search Templates

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | POST |
| **Path** | `/session-templates/search` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X POST http://localhost:8000/api/v1/session-templates/search \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Python",
    "category": "development",
    "tags": ["python", "coding"],
    "page": 1,
    "page_size": 10
  }'
```

### Response Example

```json
{
  "items": [
    {
      "id": "79277700-4856-4281-b743-29445311f207",
      "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
      "name": "Python Development Template",
      "description": "Template for Python development with common tools",
      "category": "development",
      "system_prompt": "You are a helpful Python development assistant.",
      "working_directory": "/workspace/python-projects",
      "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
      "sdk_options": {
        "model": "claude-3-5-sonnet-20241022",
        "max_turns": 20,
        "permission_mode": "default"
      },
      "mcp_server_ids": [],
      "is_public": false,
      "is_organization_shared": false,
      "version": "1.0.0",
      "tags": ["python", "development", "coding"],
      "template_metadata": {},
      "usage_count": 0,
      "last_used_at": null,
      "created_at": "2025-10-19T08:36:56.649628Z",
      "updated_at": "2025-10-19T08:36:56.649633Z",
      "_links": {
        "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `search_templates()` handler receives search criteria |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Validation | Parse Criteria | Pydantic validates search_term, category, tags, pagination |
| 4 | Category Enum | Parse Category | If category provided, convert to TemplateCategory enum |
| 5 | Service Logic | Call Search | `SessionTemplateService.search_templates()` performs search |
| 6 | Repository Query | Build Query | Repository builds SQL query with: name LIKE, category =, tags contains |
| 7 | Access Filter | Apply User Filter | Only return templates accessible to current user |
| 8 | Pagination | Apply Offset/Limit | Calculate offset from page and apply limit clause |
| 9 | Database Query | Execute Search | PostgreSQL executes combined WHERE clause with pagination |
| 10 | Response Mapping | Convert Results | Each template converted to `SessionTemplateResponse` |
| 11 | Pagination Info | Calculate Totals | Compute total pages based on total count and page size |
| 12 | Return | Send Response | FastAPI returns paginated search results |

---

## 5. Get Most Used Templates

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/session-templates/popular/top` |
| **Query Parameters** | `limit` (default: 10, max: 50) |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/session-templates/popular/top?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
[
  {
    "id": "79277700-4856-4281-b743-29445311f207",
    "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
    "name": "Python Development Template",
    "description": "Template for Python development with common tools",
    "category": "development",
    "system_prompt": "You are a helpful Python development assistant.",
    "working_directory": "/workspace/python-projects",
    "allowed_tools": ["bash", "edit_file", "read_file", "write_file"],
    "sdk_options": {
      "model": "claude-3-5-sonnet-20241022",
      "max_turns": 20,
      "permission_mode": "default"
    },
    "mcp_server_ids": [],
    "is_public": false,
    "is_organization_shared": false,
    "version": "1.0.0",
    "tags": ["python", "development", "coding"],
    "template_metadata": {},
    "usage_count": 15,
    "last_used_at": "2025-10-19T11:30:00Z",
    "created_at": "2025-10-19T08:36:56.649628Z",
    "updated_at": "2025-10-19T08:36:56.649633Z",
    "_links": {
      "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207",
      "create_session": "/api/v1/sessions?template_id=79277700-4856-4281-b743-29445311f207"
    }
  }
]
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_most_used_templates()` handler receives limit param |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Validation | Validate Limit | Ensure limit is between 1 and 50 |
| 4 | Service Logic | Call Method | `SessionTemplateService.get_most_used_templates(user_id, limit)` |
| 5 | Repository Query | Query Database | Query templates accessible to user, ordered by usage_count DESC |
| 6 | Access Control | Filter Results | Only return templates user has access to (owner, public, org-shared) |
| 7 | Sorting | Order Results | ORDER BY usage_count DESC to get most used first |
| 8 | Limit Results | Apply LIMIT | Apply LIMIT clause with provided limit parameter |
| 9 | Response Mapping | Convert Results | Each template converted to `SessionTemplateResponse` |
| 10 | HATEOAS | Add Links | Each result gets self and create_session links |
| 11 | Return | Send Response | FastAPI returns array of most used templates |

---

## 6. Update Template

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | PUT |
| **Path** | `/session-templates/{template_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X PUT http://localhost:8000/api/v1/session-templates/79277700-4856-4281-b743-29445311f207 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Development Template (Updated)",
    "description": "Updated template for Python development",
    "system_prompt": "You are an expert Python developer helping with code.",
    "tags": ["python", "development", "coding", "updated"],
    "allowed_tools": ["bash", "edit_file", "read_file", "write_file", "run_command"]
  }'
```

### Response Example

```json
{
  "id": "79277700-4856-4281-b743-29445311f207",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Python Development Template (Updated)",
  "description": "Updated template for Python development",
  "category": "development",
  "system_prompt": "You are an expert Python developer helping with code.",
  "working_directory": "/workspace/python-projects",
  "allowed_tools": ["bash", "edit_file", "read_file", "write_file", "run_command"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_turns": 20,
    "permission_mode": "default"
  },
  "mcp_server_ids": [],
  "is_public": false,
  "is_organization_shared": false,
  "version": "1.0.0",
  "tags": ["python", "development", "coding", "updated"],
  "template_metadata": {},
  "usage_count": 0,
  "last_used_at": null,
  "created_at": "2025-10-19T08:36:56.649628Z",
  "updated_at": "2025-10-19T11:52:14.420205",
  "_links": {
    "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `update_template()` handler receives template_id and update data |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Repository Query | Fetch Template | Query template by ID from database |
| 4 | Validation | Check Existence | If not found, raise 404 TemplateNotFoundError |
| 5 | Authorization | Verify Ownership | Only template owner can update (or admin) |
| 6 | Permission Check | Check Access | If user is not owner or admin, raise 403 PermissionDeniedError |
| 7 | Validation | Validate Updates | Pydantic validates all provided update fields |
| 8 | MCP Validation | Check Servers | If mcp_server_ids updated, verify all servers exist and are accessible |
| 9 | Domain Logic | Update Entity | Service updates template entity with new values |
| 10 | Timestamp | Set Updated At | `updated_at` timestamp set to current UTC time |
| 11 | Repository | Persist Changes | Repository saves updated template to database |
| 12 | Audit Log | Record Update | AuditService logs the update action with field changes |
| 13 | Response Mapping | Convert to DTO | Updated template converted to `SessionTemplateResponse` |
| 14 | HATEOAS | Add Links | Response links generated with updated template |
| 15 | Return | Send Response | FastAPI returns 200 with updated template details |

---

## 7. Update Sharing Settings

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | PATCH |
| **Path** | `/session-templates/{template_id}/sharing` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X PATCH http://localhost:8000/api/v1/session-templates/79277700-4856-4281-b743-29445311f207/sharing \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "is_public": true,
    "is_organization_shared": true
  }'
```

### Response Example

```json
{
  "id": "79277700-4856-4281-b743-29445311f207",
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "name": "Python Development Template (Updated)",
  "description": "Updated template for Python development",
  "category": "development",
  "system_prompt": "You are an expert Python developer helping with code.",
  "working_directory": "/workspace/python-projects",
  "allowed_tools": ["bash", "edit_file", "read_file", "write_file", "run_command"],
  "sdk_options": {
    "model": "claude-3-5-sonnet-20241022",
    "max_turns": 20,
    "permission_mode": "default"
  },
  "mcp_server_ids": [],
  "is_public": true,
  "is_organization_shared": true,
  "version": "1.0.0",
  "tags": ["python", "development", "coding", "updated"],
  "template_metadata": {},
  "usage_count": 0,
  "last_used_at": null,
  "created_at": "2025-10-19T08:36:56.649628Z",
  "updated_at": "2025-10-19T11:53:49.887054",
  "_links": {
    "self": "/api/v1/session-templates/79277700-4856-4281-b743-29445311f207"
  }
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `update_sharing_settings()` handler receives template_id and sharing flags |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Repository Query | Fetch Template | Query template by ID from database |
| 4 | Validation | Check Existence | If not found, raise 404 TemplateNotFoundError |
| 5 | Authorization | Verify Ownership | Only template owner can change sharing (or admin) |
| 6 | Permission Check | Check Access | If user is not owner or admin, raise 403 PermissionDeniedError |
| 7 | Validation | Validate Flags | Pydantic validates is_public and is_organization_shared booleans |
| 8 | Domain Logic | Update Sharing | Service updates template's sharing flags |
| 9 | Timestamp | Set Updated At | `updated_at` timestamp set to current UTC time |
| 10 | Repository | Persist Changes | Repository saves updated sharing settings to database |
| 11 | Audit Log | Record Change | AuditService logs sharing setting changes |
| 12 | Response Mapping | Convert to DTO | Updated template converted to `SessionTemplateResponse` |
| 13 | HATEOAS | Add Links | Response links generated |
| 14 | Return | Send Response | FastAPI returns 200 with updated template (sharing flags changed) |

---

## 8. Delete Template

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | DELETE |
| **Path** | `/session-templates/{template_id}` |
| **Status Code** | 204 No Content |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X DELETE http://localhost:8000/api/v1/session-templates/79277700-4856-4281-b743-29445311f207 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```
HTTP/1.1 204 No Content
```

(Empty response body - standard 204 No Content response)

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `delete_template()` handler receives template_id |
| 2 | Authentication | Validate Token | User extracted from JWT token |
| 3 | Repository Query | Fetch Template | Query template by ID from database |
| 4 | Validation | Check Existence | If not found, raise 404 TemplateNotFoundError |
| 5 | Authorization | Verify Ownership | Only template owner can delete (or admin) |
| 6. | Permission Check | Check Access | If user is not owner or admin, raise 403 PermissionDeniedError |
| 7 | Domain Logic | Mark Deleted | Service calls `delete_template()` with template_id |
| 8 | Soft Delete | Set Deleted At | `deleted_at` timestamp set to current UTC time (NOT hard delete) |
| 9 | Repository | Persist Changes | Repository saves soft delete to database |
| 10 | Audit Log | Record Deletion | AuditService logs the deletion action for compliance |
| 11 | Return | Send Response | FastAPI returns 204 No Content (standard DELETE response) |
| 12 | Future Queries | Excluded | Template filtered out in all LIST/GET queries (deleted_at IS NOT NULL) |

---

## Summary Table

| # | Operation | Method | Endpoint | Status | Key Features |
|---|-----------|--------|----------|--------|--------------|
| 1 | Create | POST | `/session-templates` | 201 | Validates input, creates entity, logs audit trail, returns with links |
| 2 | Read | GET | `/session-templates/{id}` | 200 | Checks access control, returns full details with HATEOAS links |
| 3 | List | GET | `/session-templates` | 200 | Filters by scope/category, applies pagination, builds links for each item |
| 4 | Search | POST | `/session-templates/search` | 200 | Full-text search, multiple filters, pagination support |
| 5 | Popular | GET | `/session-templates/popular/top` | 200 | Orders by usage_count, filters by access, returns top N |
| 6 | Update | PUT | `/session-templates/{id}` | 200 | Verifies ownership, validates fields, updates all fields, logs changes |
| 7 | Sharing | PATCH | `/session-templates/{id}/sharing` | 200 | Verifies ownership, updates is_public/is_organization_shared flags |
| 8 | Delete | DELETE | `/session-templates/{id}` | 204 | Soft delete only, sets deleted_at, logs deletion, returns no content |

---

## Common Error Responses

### 401 Unauthorized
**When:** No or invalid token in Authorization header

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
**When:** User tries to access/modify template they don't own

```json
{
  "detail": "Not authorized to access this template"
}
```

### 404 Not Found
**When:** Template ID doesn't exist or has been deleted

```json
{
  "detail": "Template <id> not found"
}
```

### 400 Bad Request
**When:** Invalid input data (validation error)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "string_type",
      "type": "type_error.string"
    }
  ]
}
```

---

## Authentication Setup

All endpoints require a Bearer token. Get token via login:

```bash
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@default.org", "password": "admin123"}' \
  -s | jq -r '.access_token')

# Use token in subsequent requests:
curl -H "Authorization: Bearer $TOKEN" ...
```

---

**Last Updated:** October 19, 2025  
**API Version:** v1  
**Environment:** Development
