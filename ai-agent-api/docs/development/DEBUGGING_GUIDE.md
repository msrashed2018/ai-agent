# Debugging Guide

**Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Common issues, debugging techniques, and troubleshooting for AI-Agent-API

---

## Overview

This guide provides practical debugging techniques, common issues, and their solutions for the AI-Agent-API service. Use this as your first resource when encountering problems.

---

## Debugging Tools

### 1. Python Debugger (pdb/ipdb)

**Set Breakpoints in Code**:

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Python 3.7+ built-in
breakpoint()  # Calls pdb.set_trace()
```

**Common pdb Commands**:
- `n` (next) - Execute next line
- `s` (step) - Step into function
- `c` (continue) - Continue execution
- `l` (list) - Show code context
- `p variable` - Print variable
- `pp variable` - Pretty print
- `w` (where) - Show stack trace
- `q` (quit) - Exit debugger

### 2. VSCode Debugger

**Configuration** (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "ENVIRONMENT": "development",
        "DEBUG": "true"
      }
    },
    {
      "name": "Pytest: Debug Current File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v",
        "-s"
      ]
    }
  ]
}
```

**Using Breakpoints**:
1. Click in line gutter to set breakpoint
2. Press F5 to start debugging
3. Use Debug toolbar (Step Over, Step Into, Continue)

**Conditional Breakpoints**:
- Right-click breakpoint → Edit Breakpoint
- Add condition: `session_id == "abc123"`

### 3. Logging for Debugging

**Increase Log Level**:

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart service
make stop
make run
```

**Add Debug Logs Temporarily**:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Add detailed debug logging
logger.debug(
    "Session state before transition",
    extra={
        "session_id": str(session.id),
        "current_status": session.status.value,
        "target_status": new_status.value,
        "can_transition": session.can_transition_to(new_status),
    }
)
```

**View Logs**:

```bash
# Tail API logs
tail -f logs/api.log

# Filter by session ID
grep "session_id.*abc123" logs/api.log

# Filter by error level
grep "ERROR" logs/api.log
```

### 4. Database Query Logging

**Enable SQLAlchemy Echo**:

```python
# In app/database/session.py
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Enable SQL query logging
)
```

**Or set environment variable**:

```bash
# In .env
DATABASE_ECHO=true
```

### 5. FastAPI Debug Mode

```bash
# Run with --reload for auto-restart
uvicorn main:app --reload --log-level debug

# Or use Makefile
make run
```

---

## Common Issues and Solutions

### 1. Database Connection Errors

#### Error: "Connection refused" or "FATAL: password authentication failed"

**Symptoms**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Diagnosis**:
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection manually
psql -h localhost -p 5432 -U aiagent -d aiagent_db
```

**Solutions**:

**If PostgreSQL not running**:
```bash
# Using Docker Compose
make docker-dev-up

# Or start PostgreSQL service
sudo systemctl start postgresql
# macOS: brew services start postgresql
```

**If authentication fails**:
```bash
# Verify credentials in .env
DATABASE_URL=postgresql+asyncpg://aiagent:password@localhost:5432/aiagent_db

# Check PostgreSQL user
psql -U postgres -c "\du"

# Reset password
psql -U postgres -c "ALTER USER aiagent WITH PASSWORD 'password';"
```

**If database doesn't exist**:
```bash
# Create database
psql -U postgres -c "CREATE DATABASE aiagent_db OWNER aiagent;"

# Run migrations
make migrate
```

### 2. Migration Errors

#### Error: "Can't locate revision identified by 'xxxxx'"

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Diagnosis**:
```bash
# Check current migration state
alembic current

# Show migration history
alembic history
```

**Solutions**:

**Option 1: Reset to head**
```bash
# Stamp to head (mark as migrated without running)
alembic stamp head

# Re-run migrations
alembic upgrade head
```

**Option 2: Reset database**
```bash
# WARNING: This destroys all data!
make db-reset
```

**Option 3: Manual fix**
```bash
# Check alembic_version table
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# Delete version if corrupted
psql $DATABASE_URL -c "DELETE FROM alembic_version;"

# Re-stamp
alembic stamp head
```

#### Error: "Target database is not up to date"

**Solution**:
```bash
# Upgrade to latest migration
alembic upgrade head

# Or use Makefile
make migrate
```

### 3. Import Errors

#### Error: "ModuleNotFoundError: No module named 'app'"

**Symptoms**:
```
ModuleNotFoundError: No module named 'app'
ImportError: attempted relative import with no known parent package
```

**Diagnosis**:
```bash
# Check if in poetry environment
poetry env info

# Check PYTHONPATH
echo $PYTHONPATH
```

**Solutions**:

**Enter poetry shell**:
```bash
# Activate poetry environment
poetry shell

# Or prefix commands with poetry run
poetry run python main.py
poetry run pytest tests/
```

**Fix PYTHONPATH**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/ai-agent-api"

# Or run from project root
cd /path/to/ai-agent-api
python main.py
```

**Reinstall dependencies**:
```bash
# Clear cache and reinstall
poetry cache clear --all pypi
poetry install --with dev,test
```

### 4. Session Errors

#### Error: "Session not in active status"

**Symptoms**:
```
SessionNotActiveError: Cannot query session in 'created' status
```

**Diagnosis**:
```bash
# Check session status in database
make db-list TABLE=sessions

# Or query directly
psql $DATABASE_URL -c "SELECT id, status FROM sessions WHERE id = '<session_id>';"
```

**Solutions**:

**Activate session first**:
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/activate \
  -H "Authorization: Bearer $TOKEN"

# Or via database (for testing only)
psql $DATABASE_URL -c "UPDATE sessions SET status = 'active' WHERE id = '<session_id>';"
```

**Check state transition logic**:
```python
# app/domain/entities/session.py
# Verify valid transitions
valid_transitions = {
    SessionStatus.CREATED: [SessionStatus.CONNECTING, SessionStatus.TERMINATED],
    SessionStatus.CONNECTING: [SessionStatus.ACTIVE, SessionStatus.FAILED],
    # ...
}
```

#### Error: "Session working directory not found"

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/test-workdir'
```

**Diagnosis**:
```bash
# Check if directory exists
ls -la /tmp/test-workdir

# Check session working_directory_path
psql $DATABASE_URL -c "SELECT id, working_directory_path FROM sessions WHERE id = '<session_id>';"
```

**Solutions**:

**Create working directory**:
```bash
# Create directories manually (for testing)
mkdir -p data/agent-workdirs/active
mkdir -p data/agent-workdirs/archives

# Or use Makefile
make initial-setup
```

**Recreate session with valid workdir**:
```bash
# Delete old session
curl -X DELETE http://localhost:8000/api/v1/sessions/{session_id}

# Create new session (workdir created automatically)
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "New Session", "mode": "interactive", ...}'
```

### 5. Permission Denied Errors

#### Error: "User does not have permission to access this session"

**Symptoms**:
```
PermissionDeniedError: User abc123 does not have permission for session xyz789
```

**Diagnosis**:
```bash
# Check session ownership
psql $DATABASE_URL -c "SELECT id, user_id FROM sessions WHERE id = '<session_id>';"

# Check user roles
psql $DATABASE_URL -c "SELECT id, username, role FROM users WHERE id = '<user_id>';"
```

**Solutions**:

**Use correct user token**:
```bash
# Login as session owner
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"username": "owner", "password": "password"}'

# Use returned token
TOKEN="<new_token>"
```

**Grant admin access** (if admin):
```bash
# Update user role to admin
psql $DATABASE_URL -c "UPDATE users SET role = 'admin' WHERE id = '<user_id>';"
```

### 6. Tool Call Failures

#### Error: "Permission denied for tool execution"

**Symptoms**:
```
PermissionDeniedError: Tool 'bash' execution denied by policy
```

**Diagnosis**:
```bash
# Check permission decisions
psql $DATABASE_URL -c "SELECT * FROM permission_decisions WHERE session_id = '<session_id>' ORDER BY created_at DESC LIMIT 10;"

# Check custom policies
psql $DATABASE_URL -c "SELECT * FROM sessions WHERE id = '<session_id>';" | grep policies
```

**Solutions**:

**Adjust permission mode**:
```python
# When creating session, use appropriate permission mode
sdk_options = {
    "permission_mode": "allow_all",  # or "default", "custom"
    "allowed_tools": ["Read", "Write", "Bash"],
}
```

**Update blocked commands** (in .env):
```bash
DEFAULT_BLOCKED_COMMANDS=["rm -rf /","sudo rm"]
DEFAULT_RESTRICTED_PATHS=["/etc/passwd","/etc/shadow"]
```

#### Error: "Tool input validation failed"

**Diagnosis**:
```bash
# Check tool call details
psql $DATABASE_URL -c "SELECT * FROM tool_calls WHERE session_id = '<session_id>' ORDER BY created_at DESC LIMIT 5;"
```

**Solution**:
```python
# Ensure tool input matches expected schema
tool_input = {
    "command": "ls -la",  # Required for Bash tool
    "path": "/tmp",       # Required for file tools
}
```

### 7. API 500 Errors

#### Error: "Internal Server Error"

**Symptoms**:
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred"
  }
}
```

**Diagnosis**:

**Check API logs**:
```bash
# View recent errors
tail -n 100 logs/api.log | grep ERROR

# Filter by request ID (from error response)
grep "request_id.*req_12345" logs/api.log
```

**Check for stack traces**:
```bash
# Full stack trace
grep -A 20 "ERROR" logs/api.log
```

**Solutions**:

**Enable debug mode**:
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart
make stop && make run
```

**Check database connectivity**:
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"
```

**Check for unhandled exceptions**:
```python
# Add try-catch in API endpoint
@router.post("/endpoint")
async def endpoint(...)
    try:
        result = await service.method()
        return result
    except Exception as e:
        logger.error("Unhandled error", exc_info=e)
        raise
```

### 8. SDK Connection Errors

#### Error: "Failed to connect to Claude SDK"

**Symptoms**:
```
SDKConnectionError: Failed to initialize Claude SDK client
```

**Diagnosis**:

**Check Claude CLI installation**:
```bash
# Verify claude CLI installed
claude --version

# Check PATH
which claude
```

**Check API key**:
```bash
# Verify API key in .env
echo $ANTHROPIC_API_KEY

# Test API key manually
claude --api-key $ANTHROPIC_API_KEY query "Hello"
```

**Solutions**:

**Install Claude CLI**:
```bash
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

**Set API key**:
```bash
# In .env
ANTHROPIC_API_KEY=sk-ant-api03-...

# Restart service
make stop && make run
```

**Check network connectivity**:
```bash
# Test connection to Anthropic API
curl -I https://api.anthropic.com

# Check firewall/proxy settings
```

### 9. Redis Connection Errors

#### Error: "Error 61 connecting to localhost:6379. Connection refused"

**Diagnosis**:
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG
```

**Solutions**:

**Start Redis**:
```bash
# Using Docker Compose
make docker-dev-up

# Or start Redis service
redis-server

# Or as daemon
redis-server --daemonize yes
```

**Verify Redis URL**:
```bash
# In .env
REDIS_URL=redis://localhost:6379/0

# Test connection
redis-cli -u $REDIS_URL ping
```

### 10. Rate Limit Errors

#### Error: "429 Too Many Requests"

**Symptoms**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded"
  }
}
```

**Diagnosis**:
```bash
# Check rate limit settings
grep RATE_LIMIT .env

# Check user request history
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_logs WHERE user_id = '<user_id>' AND created_at > NOW() - INTERVAL '1 minute';"
```

**Solutions**:

**Adjust rate limits** (in .env):
```bash
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000
```

**Wait and retry**:
```bash
# Wait 60 seconds
sleep 60

# Retry request
```

**Use exponential backoff**:
```python
import asyncio

max_retries = 3
for i in range(max_retries):
    try:
        response = await client.post(...)
        break
    except HTTPException as e:
        if e.status_code == 429 and i < max_retries - 1:
            await asyncio.sleep(2 ** i)  # 1s, 2s, 4s
        else:
            raise
```

---

## Debugging Specific Components

### Debugging Repository Layer

**Check SQL queries**:
```python
# Enable SQL echo
engine = create_async_engine(DATABASE_URL, echo=True)
```

**Test repository directly**:
```python
# In Python shell
from app.repositories.session_repository import SessionRepository
from app.database.session import async_session_maker

async with async_session_maker() as db:
    repo = SessionRepository(db)
    session = await repo.get_by_id(session_id)
    print(session)
```

### Debugging Service Layer

**Use breakpoints**:
```python
# app/services/session_service.py
async def create_session(self, ...):
    breakpoint()  # Execution pauses here
    session = Session(...)
    return session
```

**Add verbose logging**:
```python
logger.debug("Before quota validation", extra={"user_id": str(user_id)})
await self._validate_user_quotas(user_id)
logger.debug("After quota validation")
```

### Debugging API Endpoints

**Use TestClient for debugging**:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

response = client.post(
    "/api/v1/sessions",
    json={"name": "Test", ...},
)
print(response.status_code)
print(response.json())
```

**Check request validation**:
```python
# See validation errors
try:
    response = client.post("/api/v1/sessions", json={})
except RequestValidationError as e:
    print(e.errors())
```

### Debugging SDK Integration

**Mock SDK for testing**:
```python
from unittest.mock import AsyncMock

mock_client = AsyncMock()
mock_client.query.return_value = {"type": "assistant", "content": [...]}

# Use mock in service
service = SDKSessionService(sdk_client=mock_client)
```

**Enable SDK debug logs**:
```bash
# In .env
CLAUDE_SDK_LOG_LEVEL=DEBUG
```

---

## Database Debugging

### View Table Data

```bash
# List all sessions
make db-list TABLE=sessions

# List all users
make db-list TABLE=users

# List messages for session
psql $DATABASE_URL -c "SELECT * FROM messages WHERE session_id = '<session_id>' ORDER BY sequence_number;"

# List tool calls
psql $DATABASE_URL -c "SELECT * FROM tool_calls WHERE session_id = '<session_id>' ORDER BY created_at;"
```

### Inspect Table Schema

```bash
# Describe table
psql $DATABASE_URL -c "\d+ sessions"

# List all tables
psql $DATABASE_URL -c "\dt"

# List all indexes
psql $DATABASE_URL -c "\di"
```

### Check Query Performance

```bash
# Explain query
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM sessions WHERE user_id = '<user_id>';"
```

### Manual Data Fixes

```bash
# Update session status (testing only!)
psql $DATABASE_URL -c "UPDATE sessions SET status = 'active' WHERE id = '<session_id>';"

# Delete test data
psql $DATABASE_URL -c "DELETE FROM sessions WHERE name LIKE 'Test%';"

# Reset sequence
psql $DATABASE_URL -c "SELECT setval('sessions_id_seq', 1, false);"
```

---

## Performance Debugging

### Profiling with cProfile

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = await service.create_session(...)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()

# Code to profile
result = await service.create_session(...)

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

### Query Performance

```bash
# Enable slow query logging in PostgreSQL
psql $DATABASE_URL -c "ALTER DATABASE aiagent_db SET log_min_duration_statement = 100;"

# View slow queries
tail -f /var/log/postgresql/postgresql-15-main.log | grep "duration:"
```

---

## Environment Issues

### Check Python Version

```bash
python --version  # Should be 3.12+
poetry run python --version
```

### Check Dependencies

```bash
# List installed packages
poetry show

# Check for outdated packages
poetry show --outdated

# Verify specific package
poetry show sqlalchemy
```

### Rebuild Environment

```bash
# Remove virtual environment
poetry env remove python3.12

# Recreate
poetry install --with dev,test

# Verify
poetry env info
```

### Clear Caches

```bash
# Clear Poetry cache
poetry cache clear --all pypi

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clear pytest cache
rm -rf .pytest_cache/
```

---

## Useful Commands

### Service Management

```bash
# Check status
make status

# View logs
make logs

# Stop all services
make stop

# Restart API
make stop && make run-bg
```

### Database Management

```bash
# Connect to database
psql $DATABASE_URL

# List tables
make db-list TABLE=sessions

# Run migration
make migrate

# Reset database (WARNING: destroys data)
make db-reset
```

### Testing

```bash
# Run specific test
pytest tests/unit/test_session_service.py::test_create_session_success -v

# Run with breakpoint
pytest tests/unit/test_session_service.py -s

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Debugging Checklist

When encountering an issue, follow this checklist:

1. **Read Error Message Carefully**
   - What is the exact error?
   - What is the stack trace?
   - What operation was being performed?

2. **Check Logs**
   - `tail -f logs/api.log`
   - Look for ERROR or WARNING messages
   - Check for related request_id

3. **Verify Configuration**
   - Is .env file correct?
   - Are all required environment variables set?
   - Is DEBUG mode enabled?

4. **Test Dependencies**
   - Is PostgreSQL running? `pg_isready`
   - Is Redis running? `redis-cli ping`
   - Is Claude CLI installed? `claude --version`

5. **Check Service Status**
   - `make status`
   - `docker ps` (if using Docker)

6. **Review Recent Changes**
   - `git diff`
   - `git log -5`
   - Did you add/update dependencies?

7. **Search Documentation**
   - Check this debugging guide
   - Search docs/ directory
   - Check GitHub issues

8. **Reproduce in Isolation**
   - Can you reproduce with minimal code?
   - Does it work in tests?
   - Try with fresh database

---

## Getting Help

If you're still stuck after trying these steps:

1. **Check Logs**:
   ```bash
   # Collect relevant logs
   tail -n 500 logs/api.log > debug.log
   ```

2. **Document the Issue**:
   - What you were trying to do
   - Exact error message and stack trace
   - Steps to reproduce
   - Environment details (Python version, OS, etc.)

3. **Create Minimal Reproduction**:
   - Simplify to smallest failing case
   - Remove unrelated code
   - Use test data

4. **Search Similar Issues**:
   - GitHub issues
   - Documentation
   - Stack Overflow

---

## Related Files

**Logging Configuration**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/core/logging.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/core/config.py`

**Exception Handlers**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/app/api/exception_handlers.py`

**Test Configuration**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/conftest.py`

---

## Keywords

debugging, troubleshooting, common-issues, error-diagnosis, pdb, breakpoints, logging, database-debugging, migration-errors, connection-errors, import-errors, session-errors, permission-errors, api-errors, sdk-errors, redis-errors, rate-limiting, debugging-tools, vscode-debugger, query-logging, performance-debugging, profiling, environment-issues, service-management, debugging-checklist

---

**Related Documentation**:
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup and configuration
- [ERROR_HANDLING.md](./ERROR_HANDLING.md) - Exception hierarchy
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Testing and debugging tests
- [CODE_PATTERNS.md](./CODE_PATTERNS.md) - Code patterns and best practices
