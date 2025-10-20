# Monitoring Management APIs

**Base URL:** `http://localhost:8000/api/v1/monitoring`
**Authentication:** Health check endpoints do not require auth; Cost and metrics endpoints require Bearer token

---

## Table of Contents

1. [Health Check - Overall](#1-health-check---overall)
2. [Health Check - Database](#2-health-check---database)
3. [Health Check - SDK](#3-health-check---sdk)
4. [Health Check - Storage](#4-health-check---storage)
5. [Get User Costs](#5-get-user-costs)
6. [Get Budget Status](#6-get-budget-status)
7. [Get Session Metrics](#7-get-session-metrics)

---

## 1. Health Check - Overall

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/health` |
| **Status Code** | 200 OK |
| **Authentication** | Not Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/health
```

### Response Example

```json
{
  "status": "healthy",
  "checks": {
    "claude_sdk": true,
    "database": true,
    "s3_storage": true,
    "mcp_servers": {}
  },
  "timestamp": "2025-10-19T12:00:00Z"
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `health_check()` in `app/api/v1/monitoring.py:24` |
| 2 | Dependency Injection | Get HealthChecker | `get_health_checker()` dependency provides HealthChecker instance |
| 3 | Health Checker | Check All Components | Calls `get_health_status()` which checks database, SDK, storage, MCP servers |
| 4 | Database Check | Test Connection | Attempts simple database query to verify connectivity |
| 5 | SDK Check | Test Claude SDK | Verifies Claude SDK is properly configured and accessible |
| 6 | Storage Check | Test Storage | Checks S3 or filesystem storage availability |
| 7 | MCP Servers Check | Test MCP Servers | Iterates through configured MCP servers and checks health |
| 8 | Response Aggregation | Build Response | Aggregates all health check results into single response |
| 9 | Return | Send Response | FastAPI returns 200 with health status |

---

## 2. Health Check - Database

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/health/database` |
| **Status Code** | 200 OK |
| **Authentication** | Not Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/health/database
```

### Response Example

```json
{
  "healthy": true
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `database_health()` in `app/api/v1/monitoring.py:41` |
| 2 | Dependency Injection | Get HealthChecker | `get_health_checker()` provides HealthChecker instance |
| 3 | Database Check | Execute Query | Calls `check_database()` which runs simple SELECT query |
| 4 | Connection Test | Verify Result | Confirms database connection is working |
| 5 | Return | Send Response | Returns boolean indicating database health |

---

## 3. Health Check - SDK

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/health/sdk` |
| **Status Code** | 200 OK |
| **Authentication** | Not Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/health/sdk
```

### Response Example

```json
{
  "available": true
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `sdk_health()` in `app/api/v1/monitoring.py:50` |
| 2 | Dependency Injection | Get HealthChecker | `get_health_checker()` provides HealthChecker instance |
| 3 | SDK Check | Verify Configuration | Calls `check_sdk_availability()` to verify Anthropic API key configured |
| 4 | API Test | Test Connection | May perform lightweight API call to verify SDK is working |
| 5 | Return | Send Response | Returns boolean indicating SDK availability |

---

## 4. Health Check - Storage

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/health/storage` |
| **Status Code** | 200 OK |
| **Authentication** | Not Required |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/health/storage
```

### Response Example

```json
{
  "healthy": true
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `storage_health()` in `app/api/v1/monitoring.py:59` |
| 2 | Dependency Injection | Get HealthChecker | `get_health_checker()` provides HealthChecker instance |
| 3 | Storage Check | Test Access | Calls `check_s3_storage()` to verify storage accessibility |
| 4 | Provider Detection | Check Type | Tests either S3 bucket access or filesystem directory access |
| 5 | Access Test | Verify Permissions | Confirms read/write permissions to storage |
| 6 | Return | Send Response | Returns boolean indicating storage health |

---

## 5. Get User Costs

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/costs/user/{user_id}` |
| **Query Parameters** | `period` (optional: hourly, daily, weekly, monthly - default: monthly) |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/costs/user/94d9f5a2-1257-43ac-9de2-6d86421455a6?period=monthly" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "period": "monthly",
  "total_cost_usd": 0.0,
  "total_sessions": 2,
  "total_messages": 0,
  "total_tool_calls": 0,
  "total_tokens": 0,
  "average_cost_per_session": 0.0,
  "start_date": "2025-10-01T00:00:00",
  "end_date": "2025-10-19T23:08:31.107129"
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_user_costs()` in `app/api/v1/monitoring.py:68` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency extracts authenticated user |
| 3 | Authorization | Check Access | Verify user_id matches current user OR current user is admin |
| 4 | Authorization Fail | Reject Request | If unauthorized, raise 403 Forbidden error |
| 5 | Dependency Injection | Get CostTracker | `get_cost_tracker()` provides CostTracker instance |
| 6 | Period Parsing | Parse Period | Convert period parameter to TimePeriod enum |
| 7 | Date Calculation | Calculate Range | Determine start_date and end_date based on period |
| 8 | Database Query | Fetch Cost Data | Query sessions, messages, tool_calls for user in period |
| 9 | Cost Calculation | Aggregate Costs | Sum token usage and calculate USD costs |
| 10 | Response Mapping | Build Response | Create CostSummary with all metrics |
| 11 | Return | Send Response | FastAPI returns 200 with cost summary |

### Authorization Rules

- **Own Data:** Users can view their own costs
- **Admin Access:** Admins can view any user's costs
- **Others:** Regular users cannot view other users' costs (403 Forbidden)

---

## 6. Get Budget Status

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/costs/budget/{user_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/costs/budget/94d9f5a2-1257-43ac-9de2-6d86421455a6 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "user_id": "94d9f5a2-1257-43ac-9de2-6d86421455a6",
  "monthly_budget_usd": 100.0,
  "current_month_cost_usd": 0.0,
  "remaining_budget_usd": 100.0,
  "percent_used": 0.0,
  "is_over_budget": false,
  "days_remaining": 12
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_budget_status()` in `app/api/v1/monitoring.py:113` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency extracts authenticated user |
| 3 | Authorization | Check Access | Verify user_id matches current user OR current user is admin |
| 4 | Authorization Fail | Reject Request | If unauthorized, raise 403 Forbidden error |
| 5 | Dependency Injection | Get CostTracker | `get_cost_tracker()` provides CostTracker instance |
| 6 | Budget Lookup | Fetch User Budget | Query user's monthly budget limit from database |
| 7 | Current Cost Lookup | Fetch Month Costs | Get current month's total costs for user |
| 8 | Calculation | Calculate Remaining | remaining = budget - current_cost |
| 9 | Calculation | Calculate Percentage | percent_used = (current_cost / budget) * 100 |
| 10 | Calculation | Days Remaining | Calculate days left in current month |
| 11 | Over Budget Check | Check Limit | is_over_budget = current_cost > budget |
| 12 | Response Mapping | Build Response | Create BudgetStatus with all calculations |
| 13 | Return | Send Response | FastAPI returns 200 with budget status |

### Budget Fields Explained

| Field | Description |
|-------|-------------|
| `monthly_budget_usd` | User's configured monthly budget limit |
| `current_month_cost_usd` | Total costs incurred this month so far |
| `remaining_budget_usd` | Budget remaining (can be negative if over) |
| `percent_used` | Percentage of budget consumed (0-100+) |
| `is_over_budget` | Boolean flag if costs exceed budget |
| `days_remaining` | Days left in current month |

---

## 7. Get Session Metrics

### API Endpoint
| Field | Value |
|-------|-------|
| **Method** | GET |
| **Path** | `/monitoring/metrics/session/{session_id}` |
| **Status Code** | 200 OK |
| **Authentication** | Required (Bearer Token) |

### cURL Command

```bash
curl -X GET http://localhost:8000/api/v1/monitoring/metrics/session/dbd2a3b8-7da3-4b23-bb28-b6b8ce34f78e \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Response Example

```json
{
  "session_id": "dbd2a3b8-7da3-4b23-bb28-b6b8ce34f78e",
  "total_messages": 0,
  "total_tool_calls": 0,
  "total_errors": 0,
  "total_retries": 0,
  "total_cost_usd": 0.0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "total_cache_creation_tokens": 0,
  "total_cache_read_tokens": 0,
  "total_duration_ms": 0
}
```

### Backend Processing Steps

| Step | Component | Action | Details |
|------|-----------|--------|---------|
| 1 | API Endpoint Handler | Receive Request | `get_session_metrics()` in `app/api/v1/monitoring.py:153` |
| 2 | Authentication | Validate Token | `get_current_active_user` dependency extracts authenticated user |
| 3 | Repository Query | Fetch Session | `SessionRepository.get_by_id()` queries session |
| 4 | Session Validation | Check Existence | If session not found, raise 404 Not Found |
| 5 | Authorization | Check Ownership | Verify session.user_id matches current user OR current user is admin |
| 6 | Authorization Fail | Reject Request | If unauthorized, raise 403 Forbidden error |
| 7 | Dependency Injection | Get MetricsCollector | `get_metrics_collector()` provides MetricsCollector instance |
| 8 | Metrics Query | Fetch Metrics | `get_session_metrics()` queries metrics data for session |
| 9 | Metrics Validation | Check Existence | If metrics not found, raise 404 Not Found |
| 10 | Response Mapping | Build Response | Return SessionMetrics with all statistics |
| 11 | Return | Send Response | FastAPI returns 200 with session metrics |

### Metrics Fields Explained

| Field | Description |
|-------|-------------|
| `session_id` | UUID of the session |
| `total_messages` | Number of messages exchanged in session |
| `total_tool_calls` | Number of tool executions |
| `total_errors` | Number of errors encountered |
| `total_retries` | Number of operation retries |
| `total_cost_usd` | Total cost in USD |
| `total_input_tokens` | Input tokens consumed |
| `total_output_tokens` | Output tokens generated |
| `total_cache_creation_tokens` | Tokens used for cache creation |
| `total_cache_read_tokens` | Tokens read from cache |
| `total_duration_ms` | Total duration in milliseconds |

---

## Error Responses

### 401 Unauthorized - Missing/Invalid Token

```json
{
  "detail": "Not authenticated"
}
```

**Triggered When:**
- No Authorization header provided
- Invalid or expired JWT token
- Applicable to: Cost and metrics endpoints

### 403 Forbidden - Unauthorized Access

```json
{
  "detail": "Not authorized to view these costs"
}
```

**Triggered When:**
- User tries to view another user's costs/budget/metrics
- User is not admin
- Applicable to: `/costs/user/{user_id}`, `/costs/budget/{user_id}`, `/metrics/session/{session_id}`

### 404 Not Found - Session Not Found

```json
{
  "detail": "Session <session_id> not found"
}
```

**Triggered When:**
- Session ID doesn't exist in database
- Applicable to: `/metrics/session/{session_id}`

### 404 Not Found - Metrics Not Found

```json
{
  "detail": "Metrics not found for session"
}
```

**Triggered When:**
- Session exists but has no metrics data
- Applicable to: `/metrics/session/{session_id}`

---

## Related Files

### Core Implementation
- **API Endpoints:** `app/api/v1/monitoring.py` (202 lines)
- **Health Checker:** `app/claude_sdk/monitoring/health_checker.py`
- **Cost Tracker:** `app/claude_sdk/monitoring/cost_tracker.py`
- **Metrics Collector:** `app/claude_sdk/monitoring/metrics_collector.py`

### Dependencies
- **User Repository:** `app/repositories/user_repository.py`
- **Session Repository:** `app/repositories/session_repository.py`
- **Dependencies:** `app/api/dependencies.py` (lines 262-268)

### Database Models
- **User Model:** `app/models/user.py`
- **Session Model:** `app/models/session.py`

---

## Summary Table

| # | Operation | Method | Endpoint | Auth Required | Response Time |
|---|-----------|--------|----------|---------------|---------------|
| 1 | Health Check | GET | `/monitoring/health` | No | ~15ms |
| 2 | Database Health | GET | `/monitoring/health/database` | No | ~10ms |
| 3 | SDK Health | GET | `/monitoring/health/sdk` | No | ~5ms |
| 4 | Storage Health | GET | `/monitoring/health/storage` | No | ~20ms |
| 5 | User Costs | GET | `/monitoring/costs/user/{user_id}` | Yes | ~50ms |
| 6 | Budget Status | GET | `/monitoring/costs/budget/{user_id}` | Yes | ~40ms |
| 7 | Session Metrics | GET | `/monitoring/metrics/session/{session_id}` | Yes | ~35ms |

---

## Usage Examples

### Health Monitoring

```bash
# Quick health check
curl http://localhost:8000/api/v1/monitoring/health | jq .

# Check specific component
curl http://localhost:8000/api/v1/monitoring/health/database | jq .
```

### Cost Tracking

```bash
# Get token for authentication
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@default.org", "password": "admin123"}' \
  | jq -r '.access_token')

# Get monthly costs
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/monitoring/costs/user/YOUR_USER_ID?period=monthly" \
  | jq .

# Check budget status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/monitoring/costs/budget/YOUR_USER_ID" \
  | jq .
```

### Session Metrics

```bash
# Get session metrics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/monitoring/metrics/session/SESSION_ID" \
  | jq .
```

---

## TimePeriod Values

The `period` parameter in `/costs/user/{user_id}` accepts:

| Value | Description | Time Range |
|-------|-------------|------------|
| `hourly` | Last hour | Current hour only |
| `daily` | Last 24 hours | Current day |
| `weekly` | Last 7 days | Current week |
| `monthly` | Current month | Month-to-date (default) |

---

## Monitoring Best Practices

### 1. Health Checks
- Use `/monitoring/health` for overall system status
- Check individual components (`/health/database`, `/health/sdk`, `/health/storage`) for detailed diagnostics
- Set up automated health monitoring (every 60 seconds)

### 2. Cost Tracking
- Monitor costs daily to avoid budget overruns
- Set up alerts when `percent_used` > 80%
- Track `average_cost_per_session` to optimize usage

### 3. Session Metrics
- Monitor `total_errors` and `total_retries` for quality
- Track token usage to optimize prompts
- Use `total_duration_ms` for performance analysis

---

**Last Updated:** October 20, 2025
**API Version:** v1
**Reviewed By:** Claude AI Agent
**Review Status:** ✅ Complete

**Test Results:**
- ✅ All 7 endpoints tested and working
- ✅ Authorization checks verified
- ✅ Error scenarios validated
- ✅ No issues found

**Fixed During Review:**
- Monitoring router was not registered in API v1 router - Fixed by adding `monitoring` import and `api_v1_router.include_router(monitoring.router)` in `app/api/v1/__init__.py`
