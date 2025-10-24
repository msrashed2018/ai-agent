# AI Agent API - Quick Start Guide

## 🚀 First Time Setup

```bash
# 1. Install dependencies and setup
make setup

# 2. Start everything (one command!)
make start-all

# 3. Login as admin
make login
```

That's it! API is now running at http://localhost:8000

**Architecture**:
- API runs **locally** (for Claude Code CLI access)
- Postgres, Redis, Celery run in Docker (using official images with volume mounts)

---

## 📋 Common Commands

### Service Management

```bash
# Combined commands
make start-all      # Start everything (infra + API) - ONE COMMAND
make stop-all       # Stop everything
make restart-all    # Restart everything
make status         # Show all service status

# Infrastructure only (Docker: Postgres, Redis, Celery)
make infra-start    # Start Docker infrastructure
make infra-stop     # Stop Docker infrastructure
make infra-restart  # Restart infrastructure
make infra-logs     # View infrastructure logs
make infra-status   # Show Docker container status

# API only (Local service)
make api-start      # Start API server locally
make api-stop       # Stop API server
make api-restart    # Restart API server
make api-logs       # View API logs

# Health check
make health         # Check if API is healthy
```

### Task Management

```bash
make task-list                              # List all tasks
make task-create                            # Create new task (interactive)
make task-execute TASK_ID=<id>              # Execute a task
make task-status TASK_ID=<id>               # Get task details
```

### Execution Monitoring

```bash
make execution-status EXEC_ID=<id>          # Check execution status
make execution-monitor EXEC_ID=<id>         # Monitor with live updates
make execution-logs EXEC_ID=<id>            # View execution logs
```

### Session Monitoring

```bash
make session-monitor SESSION_ID=<id>        # Monitor session
make session-messages SESSION_ID=<id>       # View session messages
```

---

## 🔧 Development

```bash
make test           # Run all tests
make test-unit      # Unit tests only
make lint           # Run linters
make format         # Format code
make migrate        # Run DB migrations
```

---

## 🐳 Docker Architecture

### Development Setup
- **Configuration**: `docker-compose.dev.yml`
- **API runs locally** - Required for Claude Code CLI access
- **Infrastructure in Docker** - Postgres, Redis, Celery workers
- **Uses official Python images** - No custom builds needed!
- **Volume mounts** - Code changes reflected immediately

```bash
# All commands use docker-compose.dev.yml automatically
make start-all      # Start everything (RECOMMENDED)
make infra-start    # Start Docker infrastructure only
make infra-stop     # Stop Docker infrastructure
make infra-logs     # View Docker logs
make infra-status   # Check container status
```

**Benefits**:
- No build time - starts immediately
- Code changes reflected in Celery workers without restart
- Uses official Python 3.12 image
- Separate dev/test/prod configurations

---

## 📖 Python CLI (Advanced)

The unified CLI tool: `scripts/aiagent.py`

```bash
# Task operations
python3 scripts/aiagent.py task list
python3 scripts/aiagent.py task create "Your prompt" --name "Task Name"
python3 scripts/aiagent.py task execute <task-id>

# Execution monitoring
python3 scripts/aiagent.py execution status <exec-id>
python3 scripts/aiagent.py execution monitor <exec-id> --watch
python3 scripts/aiagent.py execution logs <exec-id>

# Session operations
python3 scripts/aiagent.py session monitor <session-id>
python3 scripts/aiagent.py session messages <session-id>

# Health check
python3 scripts/aiagent.py health
```

---

## 🎯 Example Workflow

```bash
# 1. Start everything (no build needed!)
make start-all

# 2. Login
make login

# 3. Create a K8s health check task
make task-create
# Enter: "K8s Health Check"
# Enter prompt, tags, etc.

# 4. List tasks to get ID
make task-list

# 5. Execute task
make task-execute TASK_ID=e65a456f-7841-4397-be65-e2c694ee2a80

# 6. Monitor execution (live updates)
make execution-monitor EXEC_ID=55f10fb9-3ecd-4ada-ab97-5f7174579cb7

# 7. View results
make execution-logs EXEC_ID=55f10fb9-3ecd-4ada-ab97-5f7174579cb7
```

---

## 🔍 Troubleshooting

**API not starting?**
```bash
make status          # Check what's running
make logs            # View error logs
make docker-ps       # Check Docker containers
```

**Database issues?**
```bash
make migrate         # Run migrations
make db-reset        # Reset DB (WARNING: deletes data)
```

**Celery not working?**
```bash
make celery-inspect  # Check Celery worker status
make celery-logs     # View Celery logs
```

---

## 📚 More Help

```bash
make help            # Show all available commands
```

See `CLAUDE.md` for detailed architecture and development guide.
