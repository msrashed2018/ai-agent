# Admin Commands

Administrative commands for system monitoring and management. **Requires admin role.**

---

## Commands Overview

| CLI Command | API Endpoint | Description |
|------------|-------------|-------------|
| `ai-agent admin stats` | `GET /api/v1/admin/stats` | Get system-wide statistics |
| `ai-agent admin sessions` | `GET /api/v1/admin/sessions` | List all sessions (all users) |
| `ai-agent admin users` | `GET /api/v1/admin/users` | List all users |

---

## 1. System Statistics

### CLI Command
```bash
# Get system stats
ai-agent admin stats

# JSON output
ai-agent admin stats --output json

# Watch mode (refresh every 5 seconds)
ai-agent admin stats --watch
```

### What Happens in Backend API

**Step 1: Authentication & Authorization**
```sql
-- Validate JWT token
SELECT * FROM users
WHERE id = 'user-uuid'
  AND is_active = true;

-- Check admin role
IF user.role != 'admin':
    RAISE HTTPException(403, "Admin access required")
```

**Step 2: Query Session Statistics**
```sql
-- Total sessions
SELECT COUNT(*) FROM sessions;

-- Active sessions
SELECT COUNT(*) FROM sessions
WHERE status = 'active';

-- Completed today
SELECT COUNT(*) FROM sessions
WHERE status = 'completed'
  AND completed_at >= '2025-01-15T00:00:00Z';  -- today's start
```

**Step 3: Query Task Statistics**
```sql
-- Total tasks
SELECT COUNT(*) FROM tasks;

-- Scheduled and enabled tasks
SELECT COUNT(*) FROM tasks
WHERE is_scheduled = true
  AND schedule_enabled = true;
```

**Step 4: Query User Statistics**
```sql
-- Total active users
SELECT COUNT(*) FROM users
WHERE is_deleted = false;
```

**Step 5: Query Cost Statistics**
```sql
-- Total cost (all time)
SELECT SUM(total_cost_usd) FROM sessions;

-- Today's cost
SELECT SUM(total_cost_usd) FROM sessions
WHERE updated_at >= '2025-01-15T00:00:00Z';
```

**Step 6: Storage Statistics (Future)**
```python
# TODO: Implement filesystem scanning
storage = {
    "working_dirs_mb": 0,  # Would scan /data/sessions/
    "reports_mb": 0,        # Would scan /data/reports/
    "archives_mb": 0,       # Would scan /data/archives/
}
```

**Step 7: Return Aggregated Stats**
```json
{
  "sessions": {
    "total": 1247,
    "active": 23,
    "completed_today": 156
  },
  "tasks": {
    "total": 89,
    "scheduled_enabled": 34,
    "executions_today": 0
  },
  "users": {
    "total": 42,
    "active_today": 0
  },
  "cost": {
    "total_usd": 1234.56,
    "today_usd": 45.67
  },
  "storage": {
    "working_dirs_mb": 0,
    "reports_mb": 0,
    "archives_mb": 0
  }
}
```

### Key Backend Files
- Route handler: [app/api/v1/admin.py:33-109](../../ai-agent-api/app/api/v1/admin.py#L33-L109)
- Authorization: [app/api/dependencies.py](../../ai-agent-api/app/api/dependencies.py) (`require_admin` dependency)

---

## 2. List All Sessions (Admin)

### CLI Command
```bash
# List all sessions across all users
ai-agent admin sessions

# Filter by user
ai-agent admin sessions --user-id abc123

# Filter by status
ai-agent admin sessions --status active

# With pagination
ai-agent admin sessions --page 2 --page-size 50

# JSON output
ai-agent admin sessions --output json
```

### What Happens in Backend API

**Step 1: Authentication & Authorization**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;

-- Verify admin role
IF user.role != 'admin':
    RAISE HTTPException(403, "Admin access required")
```

**Step 2: Query Sessions**

If filtering by user:
```sql
SELECT * FROM sessions
WHERE user_id = 'filter-user-uuid'
  AND deleted_at IS NULL
ORDER BY created_at DESC
OFFSET 0 LIMIT 100;
```

If listing all sessions:
```sql
-- Get all sessions (across all users)
SELECT * FROM sessions
WHERE deleted_at IS NULL
ORDER BY created_at DESC
OFFSET 0 LIMIT 100;
```

**Step 3: Apply Status Filter (in memory)**
```python
if status_filter:
    sessions = [s for s in sessions if s.status == status_filter]
```

**Step 4: Build Response with Admin Links**

For each session:
```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "name": "Production debugging",
  "status": "active",
  "model": "claude-sonnet-4-5",
  "created_at": "2025-01-15T10:00:00Z",
  "_links": {
    "self": "/api/v1/sessions/session-uuid",
    "user": "/api/v1/admin/users/user-uuid"  // Admin-specific link
  }
}
```

**Step 5: Return Paginated Response**
```json
{
  "items": [...],
  "total": 1247,
  "page": 1,
  "page_size": 100,
  "total_pages": 13
}
```

### Use Cases

**1. Monitor Active Sessions**
```bash
# See all currently active sessions
ai-agent admin sessions --status active

# Find long-running sessions
ai-agent admin sessions --status active --output json | \
  jq '.items[] | select(.message_count > 100)'
```

**2. Investigate User Activity**
```bash
# See all sessions for specific user
ai-agent admin sessions --user-id abc123

# Get user's failed sessions
ai-agent admin sessions --user-id abc123 --status failed
```

**3. System Capacity Planning**
```bash
# Count sessions by status
ai-agent admin sessions --output json | \
  jq '.items | group_by(.status) | map({status: .[0].status, count: length})'
```

### Key Backend Files
- Route handler: [app/api/v1/admin.py:112-165](../../ai-agent-api/app/api/v1/admin.py#L112-L165)
- Session repository: [app/repositories/session_repository.py](../../ai-agent-api/app/repositories/session_repository.py)

---

## 3. List All Users

### CLI Command
```bash
# List all users
ai-agent admin users

# Include deleted users
ai-agent admin users --include-deleted

# With pagination
ai-agent admin users --page 1 --page-size 20

# JSON output
ai-agent admin users --output json
```

### What Happens in Backend API

**Step 1: Authentication & Authorization**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;

-- Verify admin role
IF user.role != 'admin':
    RAISE HTTPException(403, "Admin access required")
```

**Step 2: Build Query**

Exclude deleted users (default):
```sql
SELECT * FROM users
WHERE is_deleted = false
ORDER BY created_at DESC
OFFSET 0 LIMIT 100;
```

Include deleted users (if requested):
```sql
SELECT * FROM users
ORDER BY created_at DESC
OFFSET 0 LIMIT 100;
```

**Step 3: Get Total Count**
```sql
SELECT COUNT(*) FROM users
WHERE is_deleted = false;
```

**Step 4: Return User List**
```json
{
  "items": [
    {
      "id": "user-uuid-1",
      "email": "admin@example.com",
      "role": "admin",
      "is_deleted": false,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "user-uuid-2",
      "email": "user@example.com",
      "role": "user",
      "is_deleted": false,
      "created_at": "2025-01-10T12:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 100,
  "total_pages": 1
}
```

### Use Cases

**1. User Audit**
```bash
# List all users
ai-agent admin users

# Find admins
ai-agent admin users --output json | jq '.items[] | select(.role == "admin")'
```

**2. Cleanup Deleted Users**
```bash
# See deleted users
ai-agent admin users --include-deleted --output json | \
  jq '.items[] | select(.is_deleted == true)'
```

### Key Backend Files
- Route handler: [app/api/v1/admin.py:168-216](../../ai-agent-api/app/api/v1/admin.py#L168-L216)
- User repository: [app/repositories/user_repository.py](../../ai-agent-api/app/repositories/user_repository.py)

---

## Authorization Flow

All admin commands follow this authorization pattern:

```
1. CLI Command with JWT token
   ↓
2. API validates JWT token
   ↓
   SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;
   ↓
3. Check admin role
   ↓
   IF user.role != 'admin':
       RETURN 403 Forbidden
   ↓
4. Execute admin operation
   ↓
5. Return results
```

### Admin Dependency Implementation

From [app/api/dependencies.py](../../ai-agent-api/app/api/dependencies.py):

```python
async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user
```

---

## Examples

### Example 1: System Health Check

```bash
# Get current system stats
ai-agent admin stats

# Output:
# System Statistics
# ═══════════════════
#
# Sessions:
#   Total: 1,247
#   Active: 23
#   Completed Today: 156
#
# Tasks:
#   Total: 89
#   Scheduled (Enabled): 34
#
# Users:
#   Total: 42
#
# Cost:
#   Total: $1,234.56
#   Today: $45.67
```

### Example 2: Monitor Active Sessions

```bash
# List active sessions
ai-agent admin sessions --status active --output json | \
  jq '.items[] | {
    id: .id,
    user: .user_id,
    name: .name,
    messages: .message_count,
    cost: .total_cost_usd
  }'

# Output:
# {
#   "id": "session-abc",
#   "user": "user-123",
#   "name": "Production debugging",
#   "messages": 45,
#   "cost": 0.23
# }
```

### Example 3: User Activity Report

```bash
# Get user session count
for user_id in $(ai-agent admin users --output json | jq -r '.items[].id'); do
  count=$(ai-agent admin sessions --user-id $user_id --output json | jq '.total')
  echo "User: $user_id - Sessions: $count"
done

# Output:
# User: user-123 - Sessions: 45
# User: user-456 - Sessions: 23
# User: user-789 - Sessions: 12
```

### Example 4: Cost Analysis

```bash
# Get total cost by user (requires jq)
ai-agent admin sessions --output json | \
  jq 'group_by(.user_id) | map({
    user: .[0].user_id,
    sessions: length,
    total_cost: (map(.total_cost_usd // 0) | add)
  }) | sort_by(-.total_cost)'

# Output:
# [
#   {
#     "user": "user-123",
#     "sessions": 45,
#     "total_cost": 123.45
#   },
#   {
#     "user": "user-456",
#     "sessions": 23,
#     "total_cost": 67.89
#   }
# ]
```

---

## Notes

- **Admin Access Only**: All commands require `role: "admin"` in user record
- **Read-Only**: Current implementation provides monitoring only; no user/session management
- **Pagination**: Use `--page` and `--page-size` for large result sets
- **Performance**: Stats queries aggregate entire database; may be slow on large datasets
- **Future Enhancements**:
  - User management (create, update, delete, role changes)
  - Session management (force terminate, cleanup)
  - Storage cleanup commands
  - Audit log viewing
  - Real-time monitoring dashboard
