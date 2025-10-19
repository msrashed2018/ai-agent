# Redis Caching

## Purpose

Documentation of Redis caching strategy for improving performance, rate limiting, and real-time features in the AI-Agent-API service.

---

## Redis Overview

### What is Redis?

**Redis** (Remote Dictionary Server) is an in-memory data structure store used as:
- **Cache**: Fast key-value storage for frequently accessed data
- **Message Broker**: Pub/Sub for real-time event broadcasting
- **Rate Limiter**: Atomic counters for quota enforcement
- **Session Store**: Temporary state for WebSocket connections

### Why Use Redis?

**Benefits**:
- **Speed**: Sub-millisecond latency (1000x faster than database)
- **Scalability**: Horizontal scaling with Redis Cluster
- **Atomic Operations**: INCR, DECR for race-free counters
- **TTL Support**: Automatic expiration of cached data
- **Pub/Sub**: Real-time event broadcasting

**Use Cases in AI-Agent-API**:
- Cache session data for quick access
- Track active WebSocket connections
- Enforce user rate limits
- Cache user permissions
- Store temporary session state

---

## Redis Configuration

### Settings

**File**: [app/core/config.py:36-37](../../app/core/config.py#L36-37)

```python
class Settings(BaseSettings):
    # Redis Configuration
    redis_url: str  # Example: redis://localhost:6379/0
```

**Environment Variable**:
```bash
REDIS_URL=redis://localhost:6379/0
```

**Docker Compose**:
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

---

## Implementation Status

### Current Implementation

Based on the codebase analysis, Redis is **configured but not yet actively used** for caching in the current implementation. The infrastructure is in place:

**Configuration**: Redis URL is configured in settings
```python
# app/core/config.py
redis_url: str
```

**Dependencies**: Redis client libraries are available
```toml
# pyproject.toml or requirements.txt
redis = "^5.0.0"
hiredis = "^2.2.0"  # C parser for performance
```

**Future Use Cases**: Based on the architecture, Redis would be ideal for:

1. **Session State Caching**
2. **Rate Limiting**
3. **WebSocket Connection Registry**
4. **Permission Cache**
5. **Pub/Sub for Real-time Events**

---

## Recommended Caching Strategy

### What to Cache

#### 1. Session Data (High Priority)

**Key Pattern**: `session:{session_id}`
**TTL**: 1 hour (refresh on access)
**Value**: JSON-serialized session metadata

```python
import json
from redis.asyncio import Redis

async def cache_session(redis: Redis, session_id: str, session_data: dict):
    """Cache session data in Redis."""
    key = f"session:{session_id}"
    value = json.dumps(session_data)
    await redis.setex(key, 3600, value)  # 1 hour TTL

async def get_cached_session(redis: Redis, session_id: str) -> dict | None:
    """Get cached session data."""
    key = f"session:{session_id}"
    value = await redis.get(key)
    if value:
        return json.loads(value)
    return None
```

**Example Data**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user_123",
  "status": "active",
  "mode": "interactive",
  "working_directory_path": "/tmp/sessions/123",
  "total_messages": 42,
  "total_tool_calls": 15
}
```

**Benefits**:
- Avoid database query for every session check
- Fast status lookups for active sessions
- Reduce database load by 70-80%

---

#### 2. Active Session Tracking

**Key Pattern**: `user:{user_id}:active_sessions`
**TTL**: 5 minutes
**Value**: SET of session IDs

```python
async def add_active_session(redis: Redis, user_id: str, session_id: str):
    """Add session to user's active sessions."""
    key = f"user:{user_id}:active_sessions"
    await redis.sadd(key, session_id)
    await redis.expire(key, 300)  # 5 minutes

async def get_active_sessions(redis: Redis, user_id: str) -> list[str]:
    """Get all active sessions for user."""
    key = f"user:{user_id}:active_sessions"
    return await redis.smembers(key)

async def count_active_sessions(redis: Redis, user_id: str) -> int:
    """Count active sessions for quota enforcement."""
    key = f"user:{user_id}:active_sessions"
    return await redis.scard(key)
```

**Use Case**: Enforce max_concurrent_sessions quota without database query

---

#### 3. User Permissions

**Key Pattern**: `user:{user_id}:permissions`
**TTL**: 10 minutes
**Value**: JSON-serialized permissions

```python
async def cache_user_permissions(redis: Redis, user_id: str, permissions: dict):
    """Cache user permissions."""
    key = f"user:{user_id}:permissions"
    value = json.dumps(permissions)
    await redis.setex(key, 600, value)  # 10 minutes

async def get_cached_permissions(redis: Redis, user_id: str) -> dict | None:
    """Get cached user permissions."""
    key = f"user:{user_id}:permissions"
    value = await redis.get(key)
    if value:
        return json.loads(value)
    return None
```

**Example Data**:
```json
{
  "role": "admin",
  "max_concurrent_sessions": 10,
  "max_api_calls_per_hour": 5000,
  "allowed_tools": ["Read", "Write", "Bash"],
  "is_active": true
}
```

**Benefits**:
- Fast authorization checks
- Reduce database load for permission lookups
- Update cache on permission changes

---

#### 4. WebSocket Connection Registry

**Key Pattern**: `ws:connections`
**TTL**: None (manual cleanup)
**Value**: HASH of connection_id -> user_id

```python
async def register_websocket(redis: Redis, connection_id: str, user_id: str):
    """Register WebSocket connection."""
    await redis.hset("ws:connections", connection_id, user_id)

async def unregister_websocket(redis: Redis, connection_id: str):
    """Unregister WebSocket connection."""
    await redis.hdel("ws:connections", connection_id)

async def get_user_connections(redis: Redis, user_id: str) -> list[str]:
    """Get all connection IDs for user."""
    all_connections = await redis.hgetall("ws:connections")
    return [conn_id for conn_id, uid in all_connections.items() if uid == user_id]
```

**Benefits**:
- Track active WebSocket connections
- Broadcast messages to specific users
- Cleanup stale connections

---

### What NOT to Cache

1. **Write-Heavy Data**:
   - Messages (constantly being added)
   - Tool calls (high write frequency)
   - Audit logs (append-only)

2. **Large Data**:
   - Full conversation history
   - Report content
   - File contents

3. **Critical Data**:
   - Password hashes
   - API keys
   - Financial data

**Rule**: Cache read-heavy, relatively static data. Don't cache write-heavy or large data.

---

## Rate Limiting

### Token Bucket Algorithm

**Key Pattern**: `ratelimit:{user_id}:{window}`
**TTL**: Window duration
**Value**: Counter (INCR)

```python
async def check_rate_limit(
    redis: Redis,
    user_id: str,
    limit: int,
    window_seconds: int
) -> bool:
    """Check if user is within rate limit."""
    key = f"ratelimit:{user_id}:{window_seconds}"

    # Get current count
    count = await redis.incr(key)

    # Set expiry on first request
    if count == 1:
        await redis.expire(key, window_seconds)

    # Check if over limit
    return count <= limit
```

**Usage Example**:

```python
# API endpoint rate limiting
@app.post("/api/sessions")
async def create_session(
    user_id: str,
    redis: Redis = Depends(get_redis)
):
    # Check rate limit (1000 requests per hour)
    if not await check_rate_limit(redis, user_id, limit=1000, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Create session...
```

### Per-Endpoint Rate Limits

```python
async def check_endpoint_rate_limit(
    redis: Redis,
    user_id: str,
    endpoint: str,
    limit: int,
    window_seconds: int
) -> bool:
    """Check rate limit for specific endpoint."""
    key = f"ratelimit:{user_id}:{endpoint}:{window_seconds}"

    count = await redis.incr(key)

    if count == 1:
        await redis.expire(key, window_seconds)

    return count <= limit
```

**Example**:

```python
# Limit session creation: 50 per hour
if not await check_endpoint_rate_limit(
    redis, user_id, "create_session", limit=50, window_seconds=3600
):
    raise HTTPException(status_code=429, detail="Too many sessions created")
```

---

## Cache Invalidation

### When to Invalidate

**On Session Update**:
```python
async def update_session_status(session_id: str, status: str, redis: Redis):
    """Update session status and invalidate cache."""
    # Update database
    await session_repo.update(session_id, status=status)

    # Invalidate cache
    await redis.delete(f"session:{session_id}")
```

**On User Permission Change**:
```python
async def update_user_permissions(user_id: str, permissions: dict, redis: Redis):
    """Update user permissions and invalidate cache."""
    # Update database
    await user_repo.update(user_id, **permissions)

    # Invalidate cache
    await redis.delete(f"user:{user_id}:permissions")
```

**On Session Completion**:
```python
async def complete_session(session_id: str, user_id: str, redis: Redis):
    """Complete session and remove from active set."""
    # Update database
    await session_repo.update(session_id, status="completed", completed_at=datetime.utcnow())

    # Remove from active sessions
    await redis.srem(f"user:{user_id}:active_sessions", session_id)

    # Invalidate session cache
    await redis.delete(f"session:{session_id}")
```

### Cache-Aside Pattern

**Always check cache first, fallback to database**:

```python
async def get_session(session_id: str, redis: Redis, db: AsyncSession) -> dict:
    """Get session with cache-aside pattern."""
    # Try cache first
    cached = await get_cached_session(redis, session_id)
    if cached:
        return cached

    # Cache miss - query database
    session = await session_repo.get_by_id(session_id)
    if not session:
        return None

    # Populate cache for next time
    session_data = {
        "id": str(session.id),
        "user_id": str(session.user_id),
        "status": session.status,
        "mode": session.mode,
        # ... other fields
    }
    await cache_session(redis, session_id, session_data)

    return session_data
```

---

## Redis Client Setup

### Async Redis Client

```python
from redis.asyncio import Redis, ConnectionPool

# Create connection pool
redis_pool = ConnectionPool.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    max_connections=50
)

# Create Redis client
redis_client = Redis(connection_pool=redis_pool)

# Dependency injection
async def get_redis() -> Redis:
    """Get Redis client."""
    return redis_client
```

### Usage in Services

```python
from fastapi import Depends

async def create_session(
    session_data: SessionCreate,
    user_id: str,
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db)
):
    # Check rate limit
    if not await check_rate_limit(redis, user_id, limit=1000, window_seconds=3600):
        raise HTTPException(status_code=429)

    # Create session in database
    session = await session_repo.create(**session_data.dict())

    # Add to active sessions
    await add_active_session(redis, user_id, str(session.id))

    # Cache session data
    await cache_session(redis, str(session.id), session_data.dict())

    return session
```

---

## Pub/Sub for Real-time Events

### Event Broadcasting

**Use Case**: Broadcast session status updates to WebSocket clients

```python
async def broadcast_session_event(
    redis: Redis,
    session_id: str,
    event_type: str,
    data: dict
):
    """Broadcast session event to all subscribers."""
    channel = f"session:{session_id}:events"
    message = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })
    await redis.publish(channel, message)
```

**Example Events**:
```python
# Session status changed
await broadcast_session_event(
    redis,
    session_id,
    "status_changed",
    {"old_status": "active", "new_status": "completed"}
)

# New message received
await broadcast_session_event(
    redis,
    session_id,
    "message_received",
    {"message_id": "msg_123", "content": "Hello"}
)

# Tool call completed
await broadcast_session_event(
    redis,
    session_id,
    "tool_call_completed",
    {"tool_name": "Bash", "status": "success"}
)
```

### Subscribing to Events

```python
async def subscribe_to_session_events(
    redis: Redis,
    session_id: str,
    websocket: WebSocket
):
    """Subscribe to session events and forward to WebSocket."""
    pubsub = redis.pubsub()
    channel = f"session:{session_id}:events"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message["type"] == "message":
                # Forward to WebSocket client
                await websocket.send_text(message["data"])
    finally:
        await pubsub.unsubscribe(channel)
```

---

## Performance Optimization

### Connection Pooling

**Configure connection pool for optimal performance**:

```python
redis_pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,          # Maximum connections in pool
    socket_timeout=5,             # Socket timeout (seconds)
    socket_connect_timeout=5,     # Connection timeout (seconds)
    retry_on_timeout=True,        # Retry on timeout
    health_check_interval=30,     # Health check interval (seconds)
)
```

### Pipelining

**Batch multiple commands for better throughput**:

```python
async def cache_multiple_sessions(redis: Redis, sessions: list[dict]):
    """Cache multiple sessions in one roundtrip."""
    pipe = redis.pipeline()

    for session in sessions:
        key = f"session:{session['id']}"
        value = json.dumps(session)
        pipe.setex(key, 3600, value)

    await pipe.execute()
```

### Lua Scripts

**Atomic operations with Lua**:

```python
# Rate limiting with Lua (atomic)
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('incr', key)
if current == 1 then
    redis.call('expire', key, window)
end

if current > limit then
    return 0
else
    return 1
end
"""

async def check_rate_limit_atomic(
    redis: Redis,
    user_id: str,
    limit: int,
    window_seconds: int
) -> bool:
    """Atomic rate limit check using Lua."""
    key = f"ratelimit:{user_id}:{window_seconds}"
    result = await redis.eval(RATE_LIMIT_SCRIPT, 1, key, limit, window_seconds)
    return bool(result)
```

---

## Error Handling

### Graceful Degradation

**Fallback to database if Redis is unavailable**:

```python
async def get_session_safe(
    session_id: str,
    redis: Redis,
    db: AsyncSession
) -> dict | None:
    """Get session with Redis fallback."""
    try:
        # Try Redis first
        cached = await get_cached_session(redis, session_id)
        if cached:
            return cached
    except Exception as e:
        logger.warning(f"Redis error, falling back to database: {e}")

    # Fallback to database
    session = await session_repo.get_by_id(session_id)
    return session.to_dict() if session else None
```

### Circuit Breaker

**Stop trying Redis if it's consistently failing**:

```python
class RedisCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def can_attempt(self) -> bool:
        if not self.is_open:
            return True

        # Check if timeout has passed
        if time.time() - self.last_failure_time > self.timeout:
            self.is_open = False
            return True

        return False
```

---

## Monitoring

### Key Metrics

1. **Cache Hit Rate**: Percentage of successful cache lookups
   ```python
   cache_hits / (cache_hits + cache_misses) * 100
   ```

2. **Latency**: Response time for cache operations
   - Target: < 5ms for GET operations

3. **Memory Usage**: Redis memory consumption
   ```bash
   redis-cli INFO memory
   ```

4. **Eviction Rate**: How often keys are evicted
   ```bash
   redis-cli INFO stats | grep evicted_keys
   ```

### Logging

```python
import structlog

logger = structlog.get_logger()

async def get_cached_session_with_logging(redis: Redis, session_id: str) -> dict | None:
    """Get cached session with metrics logging."""
    start_time = time.time()

    try:
        result = await get_cached_session(redis, session_id)
        duration = (time.time() - start_time) * 1000

        logger.info(
            "cache_lookup",
            session_id=session_id,
            hit=result is not None,
            duration_ms=duration
        )

        return result
    except Exception as e:
        logger.error("cache_error", session_id=session_id, error=str(e))
        raise
```

---

## Configuration Best Practices

### Memory Eviction Policy

**Configure in redis.conf or docker-compose**:

```yaml
services:
  redis:
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

**Eviction Policies**:
- `allkeys-lru`: Evict least recently used keys (recommended)
- `volatile-lru`: Evict LRU keys with TTL only
- `allkeys-lfu`: Evict least frequently used keys
- `volatile-ttl`: Evict keys with shortest TTL

### Persistence

**Enable AOF (Append-Only File) for durability**:

```yaml
services:
  redis:
    command: redis-server --appendonly yes --appendfsync everysec
    volumes:
      - redis_data:/data
```

**Persistence Options**:
- `appendfsync always`: Fsync every write (slow, safe)
- `appendfsync everysec`: Fsync every second (recommended)
- `appendfsync no`: Let OS decide (fast, risky)

---

## Security

### Authentication

**Set Redis password**:

```bash
# redis.conf
requirepass your_strong_password_here
```

**Connect with password**:

```python
redis_url = "redis://:your_strong_password_here@localhost:6379/0"
```

### Network Security

**Bind to localhost only** (if not using Redis Cluster):

```bash
# redis.conf
bind 127.0.0.1
```

**Use TLS for production**:

```python
redis_url = "rediss://username:password@hostname:6380/0"  # Note: rediss://
```

---

## Troubleshooting

### Cache Stampede Prevention

**Problem**: Many requests simultaneously query database when cache expires

**Solution**: Use lock to prevent stampede

```python
import asyncio

async def get_session_with_lock(
    session_id: str,
    redis: Redis,
    db: AsyncSession
) -> dict | None:
    """Prevent cache stampede with distributed lock."""
    cache_key = f"session:{session_id}"
    lock_key = f"lock:session:{session_id}"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Acquire lock
    lock_acquired = await redis.set(lock_key, "1", nx=True, ex=10)

    if lock_acquired:
        try:
            # Query database
            session = await session_repo.get_by_id(session_id)
            if session:
                # Cache result
                session_data = session.to_dict()
                await redis.setex(cache_key, 3600, json.dumps(session_data))
                return session_data
        finally:
            # Release lock
            await redis.delete(lock_key)
    else:
        # Wait for lock holder to populate cache
        await asyncio.sleep(0.1)
        return await get_session_with_lock(session_id, redis, db)
```

### Memory Issues

**Check memory usage**:

```bash
redis-cli INFO memory
```

**Find large keys**:

```bash
redis-cli --bigkeys
```

**Solution**: Reduce TTL or increase memory

### Connection Issues

**Check connectivity**:

```bash
redis-cli ping
# Should return: PONG
```

**Check connection pool**:

```python
async def check_redis_health(redis: Redis) -> bool:
    """Check if Redis is accessible."""
    try:
        await redis.ping()
        return True
    except Exception:
        return False
```

---

## Related Documentation

- **Database Schema**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure
- **Configuration**: [app/core/config.py](../../app/core/config.py) - Settings

---

## Keywords

`redis`, `caching`, `cache`, `rate-limiting`, `pub-sub`, `performance`, `in-memory`, `key-value`, `session-cache`, `websocket`, `real-time`, `cache-invalidation`, `cache-aside`, `connection-pool`, `ttl`, `eviction`, `monitoring`, `distributed-lock`, `atomic-operations`
