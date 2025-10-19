# Data Flow

## Purpose

This document describes how data flows through the AI-Agent-API system, from HTTP requests through all layers to external systems and back. Understanding these flows is critical for debugging, extending, and optimizing the system.

## Overview

Data flows through the system in a **unidirectional manner** from API → Service → SDK → Domain → Repository → Database, with responses flowing back up through the same layers.

```
CLIENT
  ↓ HTTP Request
API LAYER (FastAPI)
  ↓ DTO → Domain
SERVICE LAYER (Business Logic)
  ↓ Orchestration
SDK INTEGRATION LAYER (Claude SDK)
  ↓ Domain Rules
DOMAIN LAYER (Entities)
  ↓ Persistence
REPOSITORY LAYER (Data Access)
  ↓ ORM
INFRASTRUCTURE LAYER (PostgreSQL, Redis)
  ↑ Data
REPOSITORY LAYER
  ↑ Entities
SERVICE LAYER
  ↑ Entities → DTO
API LAYER
  ↑ HTTP Response
CLIENT
```

---

## Flow 1: Create Session

### Request Path

**Endpoint**: `POST /api/v1/sessions`

**Flow Diagram**:
```
1. Client → HTTP POST /api/v1/sessions
   Body: {name, mode, sdk_options, template_id?}

2. API Layer [sessions.py:56-100]
   ↓ Authentication (JWT validation)
   ↓ Request validation (Pydantic)
   ↓ Extract current_user from token

3. Service Initialization [sessions.py:72-96]
   ↓ Create all repository instances
   ↓ Create StorageManager, AuditService
   ↓ Create ClaudeSDKClientManager
   ↓ Create PermissionService
   ↓ Create SDKIntegratedSessionService

4. Service Layer [sdk_session_service.py]
   ├── 4a. Template Resolution (if template_id provided)
   │   ↓ session_template_repo.get_by_id(template_id)
   │   ↓ Merge template sdk_options with request sdk_options
   │
   ├── 4b. Quota Validation
   │   ↓ user_repo.get_by_id(user_id)
   │   ↓ session_repo.count_active_for_user(user_id)
   │   ↓ Check: active_count < user.max_concurrent_sessions
   │   ↓ Raise QuotaExceededError if exceeded
   │
   ├── 4c. Create Domain Entity [session_service.py:51-100]
   │   ↓ session = Session(
   │        id=uuid4(),
   │        user_id=user_id,
   │        mode=SessionMode(mode),
   │        status=SessionStatus.CREATED,
   │        sdk_options=sdk_options,
   │      )
   │
   ├── 4d. Create Working Directory [storage_manager.py]
   │   ↓ workdir = await storage_manager.create_working_directory(session.id)
   │   ↓ session.working_directory_path = str(workdir)
   │   ↓ Creates: /tmp/ai-agent-service/sessions/{session_id}/
   │
   ├── 4e. Initialize SDK Client [client_manager.py]
   │   ↓ sdk_client = await sdk_client_manager.create_client(
   │        session_id=session.id,
   │        working_directory=workdir,
   │        sdk_options=session.sdk_options
   │      )
   │   ↓ Starts claude-code CLI subprocess
   │
   ├── 4f. Persist to Database [session_repository.py]
   │   ↓ Convert domain Session → SessionModel (ORM)
   │   ↓ session_model = SessionModel(
   │        id=session.id,
   │        user_id=session.user_id,
   │        status=session.status.value,  # Enum → string
   │        sdk_options=session.sdk_options,
   │        ...
   │      )
   │   ↓ db.add(session_model)
   │   ↓ await db.flush()
   │   ↓ PostgreSQL INSERT into sessions table
   │
   └── 4g. Audit Logging [audit_service.py]
       ↓ audit_service.log_session_created(
            session_id=session.id,
            user_id=user_id,
            metadata={...}
          )
       ↓ PostgreSQL INSERT into audit_logs table

5. Response Transform [mappers.py]
   ↓ session_to_response(session)
   ↓ Convert Session entity → SessionResponse DTO
   ↓ SessionResponse(
        id=session.id,
        name=session.name,
        mode=session.mode.value,
        status=session.status.value,
        ...
      )

6. API Layer Returns
   ↓ HTTP 201 Created
   ↓ JSON body: SessionResponse
```

**Key Files**:
- API: [sessions.py:56-100](../../app/api/v1/sessions.py:56-100)
- Service: [sdk_session_service.py](../../app/services/sdk_session_service.py)
- Domain: [session.py:29-92](../../app/domain/entities/session.py:29-92)
- Repository: [session_repository.py](../../app/repositories/session_repository.py)
- Storage: [storage_manager.py](../../app/services/storage_manager.py)

---

## Flow 2: Execute Query (Interactive Mode)

### Request Path

**Endpoint**: `POST /api/v1/sessions/{session_id}/query`

**Flow Diagram**:
```
1. Client → HTTP POST /api/v1/sessions/{session_id}/query
   Body: {message: "Analyze the logs"}

2. API Layer [sessions.py]
   ↓ Authentication
   ↓ Session existence check
   ↓ User authorization (can_access_session)

3. Service Layer [sdk_session_service.py]
   ├── 3a. Retrieve Session
   │   ↓ session = await session_repo.get_by_id(session_id)
   │   ↓ Convert SessionModel → Session entity
   │
   ├── 3b. Validate Session State
   │   ↓ if not session.is_active():
   │       raise SessionNotActiveError()
   │
   ├── 3c. Select Execution Strategy [execution/executor_factory.py]
   │   ↓ executor = ExecutorFactory.create_executor(
   │        mode=session.mode,
   │        client_manager=sdk_client_manager,
   │        ...
   │      )
   │   ↓ For INTERACTIVE mode → InteractiveExecutor
   │   ↓ For NON_INTERACTIVE mode → BackgroundExecutor
   │   ↓ For FORKED mode → ForkedExecutor
   │
   └── 3d. Execute Query [execution/interactive_executor.py]

4. SDK Integration Layer [interactive_executor.py]
   ├── 4a. Transition Session State
   │   ↓ session.transition_to(SessionStatus.PROCESSING)
   │   ↓ await session_repo.update(session)
   │   ↓ PostgreSQL UPDATE sessions SET status='processing'
   │
   ├── 4b. Execute Pre-Query Hooks [hooks/hook_manager.py]
   │   ↓ hook_manager.execute_hooks(
   │        hook_type=HookType.BEFORE_QUERY,
   │        context={session, message}
   │      )
   │   ├── AuditHook → Log query start
   │   ├── MetricsHook → Record timestamp
   │   └── ValidationHook → Validate message format
   │
   ├── 4c. Create Message Value Object [value_objects/message.py]
   │   ↓ message_vo = Message.from_user_text(
   │        session_id=session.id,
   │        text=query_message,
   │        sequence=session.total_messages + 1
   │      )
   │   ↓ await message_repo.save(message_vo)
   │   ↓ session.increment_message_count()
   │
   ├── 4d. Permission Checks [permissions/permission_manager.py]
   │   ↓ For each potential tool call:
   │   ├── policy_engine.evaluate(
   │   │     tool_name=tool_name,
   │   │     context=PermissionContext(session, user, ...)
   │   │   )
   │   ├── FileAccessPolicy.check(path)
   │   ├── CommandPolicy.check(command)
   │   └── NetworkPolicy.check(url)
   │   ↓ If DENY → raise PermissionDeniedError
   │   ↓ If ASK → Prompt user (WebSocket callback)
   │
   ├── 4e. Send to Claude SDK [client_manager.py]
   │   ↓ sdk_client = await client_manager.get_client(session.id)
   │   ↓ response_stream = sdk_client.send_message(
   │        message=query_message,
   │        stream=True
   │      )
   │   ↓ Sends to claude-code CLI process
   │   ↓ claude-code → Anthropic Claude API
   │
   ├── 4f. Process Streaming Response [handlers/stream_handler.py]
   │   ↓ async for chunk in response_stream:
   │   │   ├── Parse chunk (text, tool_use, tool_result)
   │   │   ├── Store partial message
   │   │   └── Broadcast via WebSocket (if enabled)
   │   ↓ Build complete response
   │
   ├── 4g. Handle Tool Calls [handlers/message_handler.py]
   │   ↓ For each tool_use in response:
   │   │   ├── Create ToolCall value object
   │   │   │   tool_call = ToolCall.create_pending(
   │   │   │     session_id=session.id,
   │   │   │     tool_name=tool_use.name,
   │   │   │     tool_use_id=tool_use.id,
   │   │   │     tool_input=tool_use.input
   │   │   │   )
   │   │   │
   │   │   ├── Check Permission
   │   │   │   decision = await permission_manager.check_tool_call(tool_call)
   │   │   │   tool_call = tool_call.with_permission(decision)
   │   │   │
   │   │   ├── Execute Tool (if ALLOW)
   │   │   │   tool_call = tool_call.with_started()
   │   │   │   result = await sdk_client.execute_tool(tool_call)
   │   │   │   tool_call = tool_call.with_output(result)
   │   │   │
   │   │   ├── Persist Tool Call
   │   │   │   await tool_call_repo.save(tool_call)
   │   │   │   session.increment_tool_call_count()
   │   │   │
   │   │   └── Create Result Message
   │   │       result_msg = Message.from_result(
   │   │         session_id=session.id,
   │   │         content={"result": tool_call.tool_output},
   │   │         sequence=session.total_messages + 1
   │   │       )
   │   │       await message_repo.save(result_msg)
   │
   ├── 4h. Save Assistant Response [message_repo.py]
   │   ↓ assistant_msg = Message.from_assistant(
   │        session_id=session.id,
   │        content=response.content,
   │        sequence=session.total_messages + 1,
   │        model=response.model
   │      )
   │   ↓ await message_repo.save(assistant_msg)
   │   ↓ session.increment_message_count()
   │
   ├── 4i. Update Session Metrics [session.py:149-161]
   │   ↓ session.update_api_tokens(
   │        input_tokens=response.usage.input_tokens,
   │        output_tokens=response.usage.output_tokens,
   │        cache_creation_tokens=response.usage.cache_creation_tokens,
   │        cache_read_tokens=response.usage.cache_read_tokens
   │      )
   │   ↓ session.add_cost(calculated_cost)
   │   ↓ await session_repo.update(session)
   │
   ├── 4j. Execute Post-Query Hooks [hooks/hook_manager.py]
   │   ↓ hook_manager.execute_hooks(
   │        hook_type=HookType.AFTER_QUERY,
   │        context={session, response, duration}
   │      )
   │   ├── AuditHook → Log query completion
   │   ├── MetricsHook → Record duration, tokens
   │   ├── CostTrackingHook → Update billing
   │   └── NotificationHook → Send notifications (if configured)
   │
   └── 4k. Transition Session State
       ↓ session.transition_to(SessionStatus.ACTIVE)
       ↓ await session_repo.update(session)

5. Response Transform
   ↓ query_result = SessionQueryResponse(
        session_id=session.id,
        message_id=assistant_msg.id,
        content=assistant_msg.content,
        tool_calls=[...],
        metrics={tokens, cost, duration},
        status=session.status.value
      )

6. API Layer Returns
   ↓ HTTP 200 OK
   ↓ JSON body: SessionQueryResponse
```

**Key Files**:
- API: [sessions.py](../../app/api/v1/sessions.py)
- Service: [sdk_session_service.py](../../app/services/sdk_session_service.py)
- Executor: [execution/interactive_executor.py](../../app/claude_sdk/execution/)
- Hooks: [hooks/hook_manager.py](../../app/claude_sdk/hooks/)
- Permissions: [permissions/permission_manager.py](../../app/claude_sdk/permissions/)
- Handlers: [handlers/stream_handler.py](../../app/claude_sdk/handlers/)

---

## Flow 3: WebSocket Streaming

### Connection Flow

**Endpoint**: `WS /api/v1/sessions/{session_id}/stream`

**Flow Diagram**:
```
1. Client → WebSocket CONNECT ws://localhost:8000/api/v1/sessions/{session_id}/stream

2. WebSocket Handler [websocket/handler.py]
   ↓ Authentication (JWT in query params or headers)
   ↓ Session validation
   ↓ Accept WebSocket connection

3. Client Sends Message
   ↓ WebSocket frame: {"type": "query", "message": "Help me debug"}

4. Server Processing (same as Flow 2)
   ↓ Execute query via InteractiveExecutor

5. Streaming Response [handlers/stream_handler.py]
   ├── Event: text_delta
   │   ↓ WebSocket send: {"type": "text_delta", "delta": "Here's"}
   │   ↓ Client updates UI incrementally
   │
   ├── Event: tool_use
   │   ↓ WebSocket send: {"type": "tool_use", "tool": "Read", "input": {...}}
   │   ↓ Client shows tool execution
   │
   ├── Event: tool_result
   │   ↓ WebSocket send: {"type": "tool_result", "output": {...}}
   │   ↓ Client shows tool output
   │
   ├── Event: message_complete
   │   ↓ WebSocket send: {"type": "message_complete", "message_id": "..."}
   │   ↓ Client finalizes message display
   │
   └── Event: error
       ↓ WebSocket send: {"type": "error", "error": "..."}
       ↓ Client shows error

6. Connection Management
   ↓ Heartbeat every 30s
   ↓ Client → {"type": "ping"}
   ↓ Server → {"type": "pong"}
   ↓ Disconnect on timeout or client close
```

**Key Files**:
- WebSocket: [websocket/handler.py](../../app/websocket/)
- Stream Handler: [handlers/stream_handler.py](../../app/claude_sdk/handlers/)

---

## Flow 4: Session Forking

### Request Path

**Endpoint**: `POST /api/v1/sessions/{session_id}/fork`

**Flow Diagram**:
```
1. Client → POST /api/v1/sessions/{session_id}/fork
   Body: {name: "Forked Session"}

2. Service Layer [sdk_session_service.py]
   ├── 2a. Retrieve Parent Session
   │   ↓ parent_session = await session_repo.get_by_id(session_id)
   │
   ├── 2b. Create Forked Session
   │   ↓ forked_session = Session(
   │        id=uuid4(),
   │        user_id=parent_session.user_id,
   │        mode=SessionMode.FORKED,
   │        sdk_options=parent_session.sdk_options.copy(),
   │        parent_session_id=parent_session.id,
   │        is_fork=True
   │      )
   │
   ├── 2c. Clone Working Directory [storage_manager.py]
   │   ↓ parent_dir = Path(parent_session.working_directory_path)
   │   ↓ forked_dir = await storage_manager.create_working_directory(forked_session.id)
   │   ↓ Copy files: shutil.copytree(parent_dir, forked_dir)
   │   ↓ forked_session.working_directory_path = str(forked_dir)
   │
   ├── 2d. Clone Message History
   │   ↓ parent_messages = await message_repo.get_by_session_id(parent_session.id)
   │   ↓ for msg in parent_messages:
   │   │     cloned_msg = Message(
   │   │       id=uuid4(),
   │   │       session_id=forked_session.id,
   │   │       message_type=msg.message_type,
   │   │       content=msg.content,
   │   │       sequence_number=msg.sequence_number
   │   │     )
   │   │     await message_repo.save(cloned_msg)
   │
   ├── 2e. Initialize SDK Client
   │   ↓ sdk_client = await sdk_client_manager.create_client(
   │        session_id=forked_session.id,
   │        working_directory=forked_dir,
   │        sdk_options=forked_session.sdk_options,
   │        message_history=cloned_messages  # Restore context
   │      )
   │
   └── 2f. Persist Forked Session
       ↓ await session_repo.save(forked_session)

3. Response
   ↓ HTTP 201 Created
   ↓ SessionResponse(forked_session)
```

---

## Flow 5: Authentication

### Login Flow

**Endpoint**: `POST /api/v1/auth/login`

**Flow Diagram**:
```
1. Client → POST /api/v1/auth/login
   Body: {email: "user@example.com", password: "secret"}

2. API Layer [auth.py]
   ↓ Request validation

3. Service Layer (UserRepository)
   ├── 3a. Retrieve User
   │   ↓ user = await user_repo.get_by_email(email)
   │   ↓ if not user: raise HTTPException(401, "Invalid credentials")
   │
   ├── 3b. Verify Password
   │   ↓ from passlib.hash import bcrypt
   │   ↓ is_valid = bcrypt.verify(password, user.password_hash)
   │   ↓ if not is_valid: raise HTTPException(401, "Invalid credentials")
   │
   ├── 3c. Check User Status
   │   ↓ if not user.is_active: raise HTTPException(403, "Account disabled")
   │
   ├── 3d. Generate JWT Token
   │   ↓ from jose import jwt
   │   ↓ payload = {
   │        "sub": str(user.id),
   │        "email": user.email,
   │        "role": user.role,
   │        "exp": datetime.utcnow() + timedelta(minutes=60)
   │      }
   │   ↓ token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
   │
   ├── 3e. Update Last Login
   │   ↓ user.update_last_login()
   │   ↓ await user_repo.update(user)
   │
   └── 3f. Audit Log
       ↓ await audit_service.log_login(user_id=user.id)

4. Response
   ↓ HTTP 200 OK
   ↓ {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "bearer",
       "expires_in": 3600
     }
```

### Authenticated Request Flow

**All Protected Endpoints**:
```
1. Client → GET /api/v1/sessions
   Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

2. API Layer [dependencies.py:21-78]
   ↓ HTTPBearer security scheme extracts token
   ↓ get_current_user(credentials, db):
   ├── 2a. Decode JWT
   │   ↓ payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
   │   ↓ user_id = payload.get("sub")
   │   ↓ Exceptions:
   │   │   - ExpiredSignatureError → HTTP 401
   │   │   - InvalidTokenError → HTTP 401
   │
   ├── 2b. Retrieve User
   │   ↓ user_repo = UserRepository(db)
   │   ↓ user = await user_repo.get_by_id(user_id)
   │   ↓ if not user: raise HTTPException(401, "User not found")
   │
   └── 2c. Return User Entity
       ↓ return user  # Injected into endpoint handler

3. Endpoint Handler
   ↓ Has access to current_user: User
   ↓ Can check roles, quotas, permissions
```

**Key Files**:
- Auth API: [auth.py](../../app/api/v1/auth.py)
- Dependencies: [dependencies.py:21-78](../../app/api/dependencies.py:21-78)

---

## Data Transform Flow

### Request → Domain → Database

```
1. HTTP Request (JSON)
   ↓
2. Pydantic Schema (DTO) [schemas/session.py]
   SessionCreateRequest(
     name: str,
     mode: str,
     sdk_options: dict
   )
   ↓
3. Domain Entity [entities/session.py]
   Session(
     id: UUID,
     mode: SessionMode,  # ← Enum
     status: SessionStatus,
     ...
   )
   ↓
4. ORM Model [models/session.py]
   SessionModel(
     id: UUID,
     mode: str,  # ← Enum.value
     status: str,
     ...
   )
   ↓
5. PostgreSQL Row
   sessions table:
   | id | mode | status | sdk_options (JSONB) | ... |
```

### Database → Domain → Response

```
1. PostgreSQL Row
   ↓
2. ORM Model [models/session.py]
   SessionModel(mode="interactive", status="active")
   ↓
3. Domain Entity [entities/session.py]
   Session(
     mode=SessionMode.INTERACTIVE,  # ← String → Enum
     status=SessionStatus.ACTIVE
   )
   ↓
4. Pydantic Schema (DTO) [schemas/session.py]
   SessionResponse(
     mode="interactive",  # ← Enum → String
     status="active"
   )
   ↓
5. HTTP Response (JSON)
```

---

## Error Flow

### Domain Exception → HTTP Error

```
1. Service Layer
   ↓ session.transition_to(SessionStatus.ACTIVE)
   ↓ Raises: InvalidStateTransitionError

2. Exception Propagates
   ↓ Service layer catches and wraps
   ↓ raise SessionCannotActivateError(...) from e

3. API Layer
   ↓ Exception propagates to FastAPI

4. Exception Handler [exception_handlers.py]
   ↓ Catches SessionCannotActivateError
   ↓ Converts to HTTPException(400, detail="Cannot activate session")

5. FastAPI
   ↓ Returns HTTP 400 Bad Request
   ↓ {
       "detail": "Cannot activate session in current state",
       "error_code": "SESSION_CANNOT_ACTIVATE"
     }
```

---

## Async Flow Patterns

### Concurrent Database Operations

```python
# Good: Parallel independent queries
messages, tool_calls, metrics = await asyncio.gather(
    message_repo.get_by_session_id(session_id),
    tool_call_repo.get_by_session_id(session_id),
    metrics_repo.get_by_session_id(session_id),
)

# Good: Sequential dependent operations
session = await session_repo.get_by_id(session_id)
user = await user_repo.get_by_id(session.user_id)  # Depends on session

# Bad: Sequential when could be parallel
messages = await message_repo.get_by_session_id(session_id)  # ❌
tool_calls = await tool_call_repo.get_by_session_id(session_id)  # ❌ Could be parallel
```

---

## Caching Flow

### Redis Caching (if implemented)

```
1. API Request
   ↓
2. Service Layer
   ↓ cache_key = f"session:{session_id}"
   ↓ cached = await redis.get(cache_key)
   ↓ if cached:
   │     return json.loads(cached)  # ← Cache hit
   │
   ↓ # Cache miss
   ↓ session = await session_repo.get_by_id(session_id)
   ↓ await redis.setex(cache_key, 300, json.dumps(session))
   ↓ return session
```

---

## Related Documentation

- **Architecture Overview**: [OVERVIEW.md](OVERVIEW.md)
- **Layered Architecture**: [LAYERED_ARCHITECTURE.md](LAYERED_ARCHITECTURE.md)
- **API Endpoints**: [../components/api/REST_API_ENDPOINTS.md](../components/api/REST_API_ENDPOINTS.md)
- **Session Lifecycle**: [../components/sessions/SESSION_LIFECYCLE.md](../components/sessions/SESSION_LIFECYCLE.md)

## Keywords

`data-flow`, `request-flow`, `response-flow`, `api-flow`, `session-creation`, `query-execution`, `authentication-flow`, `websocket-streaming`, `session-forking`, `error-handling`, `async-flow`, `caching`, `data-transform`, `dto`, `orm`, `domain-entity`, `flow-diagram`, `sequence-diagram`
