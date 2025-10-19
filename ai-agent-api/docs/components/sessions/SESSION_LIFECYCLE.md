# Session Lifecycle

## Purpose

This document describes the complete lifecycle of a Claude Code agent session, from creation through execution to termination and archival. Understanding the session lifecycle is critical for working with the AI-Agent-API.

## State Machine

Sessions follow a strict state machine with 10 possible states:

```
          ┌─────────────┐
          │   CREATED   │ ← Initial state
          └──────┬──────┘
                 │
          ┌──────▼──────────┐
          │   CONNECTING    │ ← SDK initialization
          └──────┬──────────┘
                 │
          ┌──────▼──────┐
          │   ACTIVE    │ ← Running, accepting queries
          └──────┬──────┘
                 │
         ┌───────┼───────┐
         │       │       │
    ┌────▼──┐ ┌─▼─────┐ ┌▼────────┐
    │WAITING│ │PAUSED │ │PROCESSING│
    └───┬───┘ └──┬────┘ └─┬───────┘
        │        │         │
        └────────┼─────────┘
                 │
        ┌────────┼────────┐
        │        │        │
   ┌────▼───┐ ┌─▼───┐ ┌──▼──────┐
   │COMPLETED│ │FAILED│ │TERMINATED│
   └────┬───┘ └──┬──┘ └──┬──────┘
        │        │        │
        └────────┼────────┘
                 │
          ┌──────▼──────┐
          │   ARCHIVED  │ ← Final state
          └─────────────┘
```

**State Definitions**:

| State | Description | Can Accept Queries | Next States |
|-------|-------------|-------------------|-------------|
| CREATED | Session created, not yet initialized | No | CONNECTING, TERMINATED |
| CONNECTING | Initializing Claude SDK client | No | ACTIVE, FAILED |
| ACTIVE | Running, ready for queries | Yes | WAITING, PROCESSING, PAUSED, COMPLETED, FAILED, TERMINATED |
| WAITING | Waiting for user input (interactive) | Yes | ACTIVE, PROCESSING, TERMINATED |
| PROCESSING | Executing a query | No | ACTIVE, COMPLETED, FAILED |
| PAUSED | Temporarily suspended | No | ACTIVE, TERMINATED |
| COMPLETED | Successfully finished | No | ARCHIVED |
| FAILED | Failed with error | No | ARCHIVED |
| TERMINATED | Manually terminated | No | ARCHIVED |
| ARCHIVED | Archived (final state) | No | None |

**Implementation**: [session.py:8-19, 93-114](../../app/domain/entities/session.py:8-19)

---

## Lifecycle Phases

### Phase 1: Creation

**Trigger**: `POST /api/v1/sessions`

**Process**:
1. **User Authentication** - Verify JWT token
2. **Quota Validation** - Check user's max_concurrent_sessions
3. **Create Domain Entity** - Initialize Session object
   ```python
   session = Session(
       id=uuid4(),
       user_id=user.id,
       mode=SessionMode.INTERACTIVE,
       status=SessionStatus.CREATED,
       sdk_options={...}
   )
   ```
4. **Create Working Directory** - `/tmp/ai-agent-service/sessions/{session_id}/`
5. **Persist to Database** - Save SessionModel
6. **Audit Log** - Record session creation

**Files**:
- API: [sessions.py:56-100](../../app/api/v1/sessions.py:56-100)
- Service: [session_service.py:51-100](../../app/services/session_service.py:51-100)

**Result**: Session in `CREATED` state

---

### Phase 2: Initialization

**Trigger**: First query to session

**Process**:
1. **Transition to CONNECTING** - `session.transition_to(SessionStatus.CONNECTING)`
2. **Initialize SDK Client** - Start claude-code CLI subprocess
   ```python
   client = await sdk_client_manager.create_client(
       session_id=session.id,
       working_directory=workdir,
       sdk_options=session.sdk_options
   )
   ```
3. **Setup Hooks** - Register lifecycle hooks (audit, metrics)
4. **Configure Permissions** - Load permission policies
5. **Transition to ACTIVE** - `session.transition_to(SessionStatus.ACTIVE)`
6. **Set started_at** - Record session start time

**Files**:
- SDK Manager: [client_manager.py](../../app/claude_sdk/client_manager.py)
- Service: [sdk_session_service.py](../../app/services/sdk_session_service.py)

**Result**: Session in `ACTIVE` state, ready for queries

---

### Phase 3: Execution (Active Usage)

#### 3a. Query Execution

**Trigger**: `POST /api/v1/sessions/{id}/query`

**Process**:
1. **Validate Session State** - Must be ACTIVE, WAITING, or PROCESSING
2. **Transition to PROCESSING** - `session.transition_to(SessionStatus.PROCESSING)`
3. **Create User Message** - Save to database
   ```python
   message = Message.from_user_text(
       session_id=session.id,
       text=query_text,
       sequence=session.total_messages + 1
   )
   ```
4. **Execute Hooks (Before)** - AuditHook, MetricsHook, ValidationHook
5. **Send to Claude SDK** - Execute query via SDK client
6. **Process Response** - Handle streaming response
7. **Execute Tools** - Run tool calls with permission checks
8. **Save Assistant Message** - Store Claude's response
9. **Update Metrics** - Increment counters, update token usage
10. **Execute Hooks (After)** - CostTrackingHook, NotificationHook
11. **Transition to ACTIVE** - Ready for next query

**Files**:
- Executor: [execution/interactive_executor.py](../../app/claude_sdk/execution/)
- Handlers: [handlers/message_handler.py](../../app/claude_sdk/handlers/)

**State Transitions**:
```
ACTIVE → PROCESSING → ACTIVE (success)
ACTIVE → PROCESSING → FAILED (error)
```

#### 3b. Tool Execution

**For each tool call in Claude's response**:

1. **Create ToolCall Value Object**
   ```python
   tool_call = ToolCall.create_pending(
       session_id=session.id,
       tool_name="Read",
       tool_use_id="toolu_123",
       tool_input={"path": "/app/test.py"}
   )
   ```
2. **Check Permissions** - Evaluate policies
   ```python
   decision = await permission_manager.check_tool_call(tool_call)
   # decision: ALLOW, DENY, or ASK
   ```
3. **Execute Tool** (if allowed)
   ```python
   tool_call = tool_call.with_started()
   result = await sdk_client.execute_tool(tool_call)
   tool_call = tool_call.with_output(result)
   ```
4. **Save Tool Call** - Persist to database
5. **Update Session Metrics** - `session.increment_tool_call_count()`

#### 3c. Pausing

**Trigger**: `POST /api/v1/sessions/{id}/pause`

**Process**:
1. **Validate State** - Must be ACTIVE or WAITING
2. **Transition to PAUSED** - `session.transition_to(SessionStatus.PAUSED)`
3. **Save State** - Persist session

**Resume**: `POST /api/v1/sessions/{id}/resume`
- Transition: `PAUSED → ACTIVE`

---

### Phase 4: Completion

#### 4a. Successful Completion

**Trigger**: Natural completion (session reaches goal) or manual completion

**Process**:
1. **Transition to COMPLETED** - `session.transition_to(SessionStatus.COMPLETED)`
2. **Set completed_at** - Record completion timestamp
3. **Calculate Duration** - `duration_ms = completed_at - started_at`
4. **Generate Report** (optional) - Create session summary
5. **Audit Log** - Record completion

**Result**: Session in `COMPLETED` state

#### 4b. Failure

**Trigger**: Unrecoverable error

**Process**:
1. **Capture Error** - `session.set_error(error_message)`
2. **Transition to FAILED** - `session.transition_to(SessionStatus.FAILED)`
3. **Set completed_at** - Record failure time
4. **Audit Log** - Record failure with error details

**Result**: Session in `FAILED` state

#### 4c. Manual Termination

**Trigger**: `DELETE /api/v1/sessions/{id}`

**Process**:
1. **Kill SDK Process** - Stop claude-code subprocess
2. **Transition to TERMINATED** - `session.transition_to(SessionStatus.TERMINATED)`
3. **Set completed_at** - Record termination time
4. **Cleanup Resources** - Close connections, release locks

**Result**: Session in `TERMINATED` state

---

### Phase 5: Archival

**Trigger**: Background job or explicit archive request

**Process**:
1. **Validate State** - Must be COMPLETED, FAILED, or TERMINATED
2. **Archive Working Directory** - Create compressed archive
   ```python
   archive = await storage_manager.archive_working_directory(
       session_id=session.id,
       compression="gzip"
   )
   ```
3. **Create Archive Metadata**
   ```python
   archive_metadata = ArchiveMetadata(
       id=uuid4(),
       session_id=session.id,
       archive_path="/archives/uuid.tar.gz",
       archive_size_bytes=1048576,
       file_count=42
   )
   ```
4. **Transition to ARCHIVED** - `session.transition_to(SessionStatus.ARCHIVED)`
5. **Optional: Delete Working Directory** - Free disk space
6. **Audit Log** - Record archival

**Files**:
- Storage: [storage_manager.py](../../app/services/storage_manager.py)

**Result**: Session in `ARCHIVED` state (final)

---

## Special Operations

### Session Forking

**Purpose**: Clone a session with its working directory and message history

**Trigger**: `POST /api/v1/sessions/{id}/fork`

**Process**:
1. **Retrieve Parent Session** - Load from database
2. **Create Forked Session**
   ```python
   forked_session = Session(
       id=uuid4(),
       user_id=parent.user_id,
       mode=SessionMode.FORKED,
       parent_session_id=parent.id,
       is_fork=True,
       sdk_options=parent.sdk_options.copy()
   )
   ```
3. **Clone Working Directory** - `cp -r parent_dir forked_dir`
4. **Clone Message History** - Copy all messages with new session_id
5. **Initialize SDK Client** - With cloned context
6. **Persist Forked Session** - Save to database

**Files**:
- Service: [sdk_session_service.py](../../app/services/sdk_session_service.py)

**Result**: New session in `CREATED` state, linked to parent

---

### Session Resumption

**Purpose**: Continue a paused or waiting session

**Trigger**: `POST /api/v1/sessions/{id}/resume`

**Process**:
1. **Validate State** - Must be PAUSED
2. **Transition to ACTIVE** - `session.transition_to(SessionStatus.ACTIVE)`
3. **Reattach SDK Client** - Reconnect to claude-code process
4. **Restore Context** - Load message history

**Result**: Session returns to `ACTIVE` state

---

## Metrics Tracking

Throughout the lifecycle, sessions automatically track:

**Message Metrics**:
- `total_messages`: Total message count (user + assistant)
- Incremented via: `session.increment_message_count()`

**Tool Call Metrics**:
- `total_tool_calls`: Total tool executions
- Incremented via: `session.increment_tool_call_count()`

**Cost Metrics**:
- `total_cost_usd`: Accumulated API cost
- Updated via: `session.add_cost(cost)`

**Token Metrics**:
- `api_input_tokens`, `api_output_tokens`
- `api_cache_creation_tokens`, `api_cache_read_tokens`
- Updated via: `session.update_api_tokens(...)`

**SDK Metrics** (Phase 1+):
- `total_hook_executions`: Hook execution count
- `total_permission_checks`: Permission check count
- `total_errors`: Error count
- `total_retries`: Retry attempt count

**Time Metrics**:
- `created_at`: Session creation
- `started_at`: First query execution
- `completed_at`: Termination/completion
- `duration_ms`: Total execution time (calculated)

**Implementation**: [session.py:134-208](../../app/domain/entities/session.py:134-208)

---

## Error Handling

### Session State Errors

**InvalidStateTransitionError**:
- Raised when invalid state transition attempted
- Example: `ARCHIVED → ACTIVE` (not allowed)

**SessionNotActiveError**:
- Raised when query sent to non-active session
- Example: Query to COMPLETED session

**SessionCannotResumeError**:
- Raised when resume attempted from invalid state
- Example: Resume from COMPLETED session

### Recovery

**Automatic Retry**:
- Transient SDK errors trigger automatic retry (up to `max_retries`)
- Retry delay: `retry_delay` seconds (configurable)

**Manual Recovery**:
- FAILED sessions cannot be recovered
- TERMINATED sessions cannot be restarted
- Create new session or fork existing one

---

## Database Operations

### Creation
```sql
INSERT INTO sessions (
    id, user_id, mode, status, sdk_options, working_directory_path, created_at
) VALUES (?, ?, ?, 'created', ?, ?, NOW());
```

### State Transition
```sql
UPDATE sessions
SET status = ?, updated_at = NOW()
WHERE id = ? AND status IN (valid_previous_states);
```

### Metrics Update
```sql
UPDATE sessions
SET total_messages = total_messages + 1,
    total_tool_calls = total_tool_calls + 1,
    total_cost_usd = total_cost_usd + ?,
    api_input_tokens = api_input_tokens + ?,
    updated_at = NOW()
WHERE id = ?;
```

### Archival
```sql
UPDATE sessions
SET status = 'archived',
    archive_id = ?,
    updated_at = NOW()
WHERE id = ? AND status IN ('completed', 'failed', 'terminated');
```

---

## Best Practices

1. **Always Check State Before Operations**
   ```python
   if not session.is_active():
       raise SessionNotActiveError()
   ```

2. **Use Domain Entity Methods for State Changes**
   ```python
   # Good
   session.transition_to(SessionStatus.ACTIVE)

   # Bad
   session.status = SessionStatus.ACTIVE  # Bypasses validation
   ```

3. **Track Metrics Automatically**
   ```python
   # After each message
   session.increment_message_count()

   # After API call
   session.update_api_tokens(input=150, output=420)
   ```

4. **Archive Completed Sessions**
   - Prevents disk space exhaustion
   - Preserves session data for compliance

5. **Handle Errors Gracefully**
   ```python
   try:
       await session_service.execute_query(session_id, query)
   except SessionNotActiveError:
       # Handle inactive session
   except QuotaExceededError:
       # Handle quota limits
   ```

---

## Related Documentation

- **Domain Model**: [../../architecture/DOMAIN_MODEL.md](../../architecture/DOMAIN_MODEL.md) - Session entity details
- **Session Modes**: [SESSION_MODES.md](SESSION_MODES.md) - Interactive vs Background
- **Session Forking**: [SESSION_FORKING.md](SESSION_FORKING.md) - Fork operation details
- **Data Flow**: [../../architecture/DATA_FLOW.md](../../architecture/DATA_FLOW.md) - Complete request flow
- **API Endpoints**: [../api/REST_API_ENDPOINTS.md](../api/REST_API_ENDPOINTS.md) - Session API reference

## Keywords

`session`, `lifecycle`, `state-machine`, `states`, `transitions`, `created`, `active`, `completed`, `failed`, `terminated`, `archived`, `session-status`, `metrics`, `initialization`, `execution`, `archival`, `state-transitions`, `session-management`
