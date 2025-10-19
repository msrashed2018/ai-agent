# Development Setup Guide

**Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Complete local development environment setup for AI-Agent-API

---

## Overview

This guide walks you through setting up the AI-Agent-API service for local development, from installing prerequisites to running your first API request.

**Estimated Setup Time**: 30-45 minutes

---

## Prerequisites

Before starting, ensure you have these tools installed:

### Required

1. **Python 3.12+**
   - Check version: `python --version` or `python3 --version`
   - Download: https://www.python.org/downloads/

2. **PostgreSQL 15+**
   - Check version: `psql --version`
   - Download: https://www.postgresql.org/download/
   - Required for database storage

3. **Redis 7+**
   - Check version: `redis-server --version`
   - Download: https://redis.io/download
   - Required for caching and Celery

4. **Poetry** (Python dependency manager)
   - Install: `curl -sSL https://install.python-poetry.org | python3 -`
   - Check version: `poetry --version`
   - Documentation: https://python-poetry.org/docs/

5. **Claude CLI** (Anthropic's Claude Code Agent)
   - Install: `npm install -g @anthropic-ai/claude-code`
   - Check version: `claude --version`
   - Required for SDK integration

6. **Anthropic API Key**
   - Get from: https://console.anthropic.com/
   - Required for Claude API access

### Optional (for Docker deployment)

- **Docker** and **Docker Compose**
- Check version: `docker --version && docker-compose --version`

---

## Step-by-Step Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd ai-agent-api

# Verify you're in the right directory
ls -la  # Should see: app/, tests/, pyproject.toml, Makefile, etc.
```

### 2. Install Dependencies

```bash
# Install all dependencies (production + dev + test)
make install

# Or manually with Poetry:
poetry install --with dev,test

# Verify installation
poetry show  # Lists all installed packages
```

**What this installs**:
- FastAPI, Uvicorn (web framework)
- SQLAlchemy, Asyncpg, Alembic (database)
- Redis, Celery (task queue)
- Claude Agent SDK (AI integration)
- Pytest, Black, Ruff (testing and code quality)

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables**:

```bash
# Service Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database (update credentials if needed)
DATABASE_URL=postgresql+asyncpg://aiagent:password@localhost:5432/aiagent_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Claude API (REQUIRED - get from console.anthropic.com)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security (CHANGE FOR PRODUCTION!)
SECRET_KEY=your_secret_key_here_minimum_32_characters_long_change_in_production

# Storage Paths
STORAGE_BASE_PATH=/data
```

**Optional Environment Variables**:
- `MAX_CONCURRENT_SESSIONS`: Default 5
- `SESSION_TIMEOUT_HOURS`: Default 24
- `RATE_LIMIT_PER_MINUTE`: Default 60
- See `.env.example` for full list

### 4. Set Up PostgreSQL Database

**Option A: Using Docker Compose (Recommended)**

```bash
# Start PostgreSQL and Redis services
make docker-dev-up

# Verify services are running
docker ps  # Should see aiagent-postgres and aiagent-redis
```

**Option B: Local PostgreSQL Installation**

```bash
# Create database and user
psql -U postgres -c "CREATE USER aiagent WITH PASSWORD 'password';"
psql -U postgres -c "CREATE DATABASE aiagent_db OWNER aiagent;"

# Grant privileges
psql -U postgres -d aiagent_db -c "GRANT ALL PRIVILEGES ON DATABASE aiagent_db TO aiagent;"

# Test connection
psql -h localhost -p 5432 -U aiagent -d aiagent_db
```

### 5. Run Database Migrations

```bash
# Run all migrations to create tables
make migrate

# Or manually:
alembic upgrade head

# Verify migrations
alembic current  # Should show current revision
```

**Common migration commands**:
- `alembic current` - Show current migration version
- `alembic history` - Show migration history
- `alembic upgrade head` - Upgrade to latest
- `alembic downgrade -1` - Downgrade one version
- `make migrate-create` - Create new migration (interactive)

### 6. Start Redis

**If using Docker Compose**: Already running from step 4

**If using local Redis**:

```bash
# Start Redis server
redis-server

# Or run in background
redis-server --daemonize yes

# Test connection
redis-cli ping  # Should return: PONG
```

### 7. Seed Database (Optional)

```bash
# Create default admin user and test data
make seed-db

# Default admin credentials:
# Email: admin@example.com
# Username: admin
# Password: admin123
```

### 8. Create Required Directories

```bash
# Create all required directories
mkdir -p data/agent-workdirs/active
mkdir -p data/agent-workdirs/archives
mkdir -p data/reports
mkdir -p data/backups/postgres
mkdir -p data/backups/redis
mkdir -p logs

# Or use make command:
make initial-setup
```

---

## Running the Service

### Development Server (Foreground)

```bash
# Run with auto-reload (recommended for development)
make run

# Or manually:
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc

### Background Mode

```bash
# Start API in background
make run-bg

# Check status
make status

# View logs
tail -f logs/api.log

# Stop background services
make stop
```

### Running Celery Workers (for async tasks)

```bash
# Start Celery worker (foreground)
make run-worker

# Start Celery beat scheduler (for scheduled tasks)
make run-beat

# Or run both in background:
make run-worker-bg
make run-beat-bg
```

### Using Docker Compose (Full Stack)

```bash
# Start all services (API, PostgreSQL, Redis, Celery)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Makefile Commands Reference

The project includes a comprehensive Makefile with useful commands:

### Installation & Setup
- `make install` - Install dependencies with Poetry
- `make dev` - Install dev dependencies + setup pre-commit hooks
- `make setup` - Complete setup (install, migrate, seed, create dirs)
- `make initial-setup` - Copy .env and create directories

### Testing
- `make test` - Run comprehensive test suite with coverage
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-e2e` - Run end-to-end tests only
- `make test-cov` - Run tests with coverage report only
- `make test-watch` - Run tests in watch mode
- `make test-sessions` - Test session functionality
- `make test-permissions` - Test permission system
- `make test-tasks` - Test task management
- `make test-api` - Test API endpoints

### Code Quality
- `make lint` - Run linters (ruff)
- `make format` - Format code (black + ruff)
- `make type-check` - Run type checking (mypy)
- `make quality` - Run all code quality checks
- `make ci` - Run CI pipeline (deps + quality + tests)
- `make clean` - Clean up generated files

### Running Services
- `make run` - Run API (foreground)
- `make run-bg` - Run API in background
- `make run-worker` - Run Celery worker (foreground)
- `make run-worker-bg` - Run Celery worker in background
- `make run-beat` - Run Celery beat (foreground)
- `make run-beat-bg` - Run Celery beat in background
- `make stop` - Stop all background services
- `make status` - Show status of background services
- `make logs` - Tail all logs

### Docker
- `make docker-dev-up` - Start dev infrastructure (postgres, redis)
- `make docker-dev-down` - Stop dev infrastructure
- `make docker-dev-logs` - Show dev infrastructure logs
- `make docker-test-up` - Start test infrastructure
- `make docker-test-down` - Stop test infrastructure
- `make docker-down-all` - Stop all docker services

### Database
- `make migrate` - Run database migrations
- `make migrate-create` - Create new migration (interactive)
- `make migrate-downgrade` - Downgrade one migration
- `make seed-db` - Seed database with default data
- `make db-reset` - Reset database (WARNING: destroys data!)
- `make db-list TABLE=users` - List all data from a table

### Help
- `make help` - Show all available commands

---

## Verification Steps

### 1. Check Health Endpoint

```bash
# Should return: {"status": "healthy"}
curl http://localhost:8000/health
```

### 2. Access API Documentation

Open in browser:
- Swagger UI: http://localhost:8000/docs
- Should see interactive API documentation

### 3. Check Database Connection

```bash
# List users table
make db-list TABLE=users

# Or manually:
PGPASSWORD=password psql -h localhost -p 5432 -U aiagent -d aiagent_db -c "SELECT * FROM users;"
```

### 4. Create Test User and Session

```bash
# Using the seeded admin user, get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Save the returned token
TOKEN="<your_token_here>"

# Create a test session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Session",
    "mode": "interactive",
    "sdk_options": {
      "model": "claude-sonnet-4-5",
      "permission_mode": "default"
    }
  }'
```

---

## Development Tools Setup

### VSCode Setup (Recommended)

**Install Extensions**:
1. Python (ms-python.python)
2. Pylance (ms-python.vscode-pylance)
3. Black Formatter (ms-python.black-formatter)
4. Ruff (charliermarsh.ruff)

**Workspace Settings** (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**Debug Configuration** (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
make dev

# Or manually:
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

---

## Common Issues and Solutions

### Issue: Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Issue: Database Connection Errors

**Error**: `FATAL: password authentication failed for user "aiagent"`

**Solution**:
```bash
# Verify DATABASE_URL in .env
# Ensure PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection manually
psql -h localhost -p 5432 -U aiagent -d aiagent_db

# If using Docker, check container status
docker ps | grep postgres
```

### Issue: Poetry Lock File Conflicts

**Error**: `The lock file is not compatible with the current version of Poetry`

**Solution**:
```bash
# Update Poetry
poetry self update

# Regenerate lock file
poetry lock --no-update

# Reinstall dependencies
poetry install
```

### Issue: Missing API Key

**Error**: `ANTHROPIC_API_KEY is required`

**Solution**:
- Ensure `.env` file exists in project root
- Add: `ANTHROPIC_API_KEY=sk-ant-api03-...`
- Get key from: https://console.anthropic.com/settings/keys
- Restart the server after updating `.env`

### Issue: Redis Connection Refused

**Error**: `redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
redis-server

# Or with Docker:
make docker-dev-up
```

### Issue: Alembic Migration Errors

**Error**: `Can't locate revision identified by 'xxxxx'`

**Solution**:
```bash
# Check current revision
alembic current

# Reset to head
alembic stamp head

# Re-run migrations
alembic upgrade head

# If still failing, reset database:
make db-reset
```

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in poetry shell
poetry shell

# Or prefix commands with poetry run:
poetry run python main.py

# Check PYTHONPATH
echo $PYTHONPATH
```

### Issue: Permission Denied (Working Directories)

**Error**: `PermissionError: [Errno 13] Permission denied: '/data'`

**Solution**:
```bash
# Create directories with correct permissions
mkdir -p data/agent-workdirs/active
chmod -R 755 data/

# Or update .env to use /tmp:
STORAGE_BASE_PATH=/tmp/ai-agent-service
```

---

## Next Steps

After successful setup:

1. **Read Code Patterns**: See [CODE_PATTERNS.md](./CODE_PATTERNS.md)
2. **Run Tests**: `make test` to ensure everything works
3. **Explore API**: Use Swagger UI at http://localhost:8000/docs
4. **Study Architecture**: Read [docs/architecture/LAYERED_ARCHITECTURE.md](../architecture/LAYERED_ARCHITECTURE.md)
5. **Try Examples**: Create sessions, send messages, execute tools

---

## Additional Resources

### Documentation
- [Architecture Overview](../architecture/OVERVIEW.md)
- [Domain Model](../architecture/DOMAIN_MODEL.md)
- [API Endpoints](../components/api/REST_API_ENDPOINTS.md)
- [Session Lifecycle](../components/sessions/SESSION_LIFECYCLE.md)

### External Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Claude API Docs](https://docs.anthropic.com/claude/reference)
- [Poetry Documentation](https://python-poetry.org/docs/)

---

## Keywords

setup, installation, environment, configuration, prerequisites, python, postgresql, redis, poetry, claude-cli, anthropic-api-key, makefile, docker, docker-compose, database-setup, migrations, alembic, dependencies, development-environment, local-setup, env-file, database-connection, troubleshooting, common-issues, vscode, debugging, pre-commit-hooks, verification, health-check

---

**Related Documentation**:
- [CODE_PATTERNS.md](./CODE_PATTERNS.md) - Coding standards and patterns
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - Testing approach
- [DEBUGGING_GUIDE.md](./DEBUGGING_GUIDE.md) - Debugging techniques
