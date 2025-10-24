# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **monorepo** containing three interconnected components that form a complete AI agent platform:

1. **ai-agent-api** - FastAPI backend service wrapping Claude Code Agent SDK
2. **ai-agent-cli** - Python CLI tool for interacting with the API
3. **ai-agent-frontend** - Next.js 14 web interface (in development)

## Critical: Documentation-First Workflow

**ALWAYS start by reading documentation before making changes:**

1. Navigate to the component's `docs/` directory
2. For **ai-agent-api**: Start with `ai-agent-api/docs/INDEX.md` - search for keywords related to your task
3. Read the relevant documentation to understand existing patterns
4. Read ONLY the source files listed in the doc's "Related Files" section
5. Follow existing patterns when implementing changes

**Why**: The ai-agent-api has extensive documentation (31+ docs) that prevents reading entire codebases and saves 90%+ of context.

## Component-Specific Commands

### AI-Agent-API (Backend Service)

**Location**: `ai-agent-api/`

**Prerequisites**: Python 3.12+, PostgreSQL 15+, Redis 7+, Poetry

**Development Setup**:
```bash
cd ai-agent-api
make setup              # Complete setup: install, migrate, seed DB
make docker-dev-up      # Start PostgreSQL + Redis
make run                # Run API (foreground)
make run-bg             # Run API (background)
```

**Testing**:
```bash
make test               # Full test suite with coverage
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e           # End-to-end tests only
make test-sessions      # Test specific functionality
```

**Code Quality**:
```bash
make lint               # Run ruff linter
make format             # Format with black + ruff
make type-check         # Run mypy
make quality            # lint + type-check
make ci                 # Full CI pipeline
```

**Database**:
```bash
make migrate            # Apply migrations
make migrate-create     # Create new migration
make seed-db            # Seed default admin user + test data
make db-list TABLE=sessions  # View table contents
```

**Running Services**:
```bash
make run                # API server (foreground)
make run-worker         # Celery worker (foreground)
make run-beat           # Celery beat scheduler (foreground)
make run-bg             # API server (background)
make run-worker-bg      # Celery worker (background)
make run-beat-bg        # Celery beat (background)
make stop               # Stop all background services
make status             # Check service status
make logs               # Tail all logs
```

**Authentication Helpers**:
```bash
make login-admin        # Login as admin, save tokens to .env.tokens
make login-user         # Login as regular user
```

### AI-Agent-CLI

**Location**: `ai-agent-cli/`

**Prerequisites**: Python 3.10+, Poetry

**Installation**:
```bash
cd ai-agent-cli
poetry install
poetry shell
```

**Common Commands**:
```bash
# Configuration
ai-agent config set-api-url http://localhost:8000

# Authentication
ai-agent auth login --email user@example.com --password yourpassword
ai-agent auth whoami

# Sessions
ai-agent sessions create --name "My Session"
ai-agent sessions list
ai-agent sessions query <session-id> "Your message here"
ai-agent sessions messages <session-id>

# Tasks
ai-agent tasks create --name "Daily Task" --prompt-template "Check {{service}}"
ai-agent tasks execute <task-id> --variables '{"service": "nginx"}'

# MCP Servers
ai-agent mcp list
ai-agent mcp import ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Output Formats**: Use `--format json` or `--format table` (default)

### AI-Agent-Frontend

**Location**: `ai-agent-frontend/`

**Prerequisites**: Node.js 18+, npm

**Development**:
```bash
cd ai-agent-frontend
npm install
npm run dev              # Start dev server on http://localhost:3000
npm run build            # Production build
npm run lint             # ESLint
```

**Status**: Foundation complete (API client, auth, types). UI implementation in progress.

## Architecture: AI-Agent-API

**Critical Pattern: Layered Clean Architecture**

The API follows strict layered architecture with unidirectional dependencies:

```
API Layer (app/api/)
  ↓
Service Layer (app/services/)
  ↓
SDK Integration Layer (app/claude_sdk/)
  ↓
Domain Layer (app/domain/)
  ↓
Repository Layer (app/repositories/)
  ↓
Infrastructure (app/models/, app/database/)
```

**Key Rules**:
- API layer handles HTTP, calls services
- Service layer contains business logic, orchestrates repositories
- SDK Integration wraps claude-agent-sdk with business features
- Domain layer defines entities and business rules (framework-agnostic)
- Repository layer abstracts data access
- Lower layers never depend on upper layers

**When working with sessions**:
1. Read `ai-agent-api/docs/components/sessions/SESSION_LIFECYCLE.md`
2. Check `ai-agent-api/docs/components/claude_sdk/SDK_INTEGRATION_OVERVIEW.md`
3. Service layer: `app/services/sdk_session_service.py`
4. API endpoints: `app/api/v1/sessions.py`

**When adding features**:
1. Search `ai-agent-api/docs/INDEX.md` for related keywords
2. Read component documentation first
3. Follow existing patterns in similar components
4. Update documentation after changes

## Key Patterns and Conventions

### API Service (Python/FastAPI)

**Import Style**:
- Use absolute imports: `from app.services.session_service import SessionService`
- Never use `src.*` imports

**Async Everywhere**:
- ALL I/O operations must be async (database, HTTP, file system)
- Use `asyncio.gather()` for parallel operations
- Never use blocking I/O (requests, time.sleep, etc.)

**Error Handling**:
- Use specific exception types from `app/core/exceptions.py`
- Never use bare `except`
- Log errors with context: `logger.error("msg", extra={session_id=..., user_id=...})`

**Testing**:
- Follow Arrange-Act-Assert pattern
- Mock external dependencies
- Tests location: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- Use fixtures from `tests/conftest.py`

**Repository Pattern**:
- All database access through repositories (never raw SQL in services)
- Convert ORM models to domain entities in repository layer
- Service layer works with domain entities, not ORM models

**Session Working Directories**:
- Each session gets isolated working directory in `data/agent-workdirs/active/{session_id}/`
- Archived sessions move to `data/agent-workdirs/archives/{session_id}/`
- IMPORTANT: Always use StorageManager service for directory operations

**Claude SDK Integration**:
- Three execution strategies: InteractiveExecutor, BackgroundExecutor, ForkedExecutor
- Strategy selection based on SessionMode (INTERACTIVE, NON_INTERACTIVE, FORKED)
- SDK clients managed by ClaudeSDKClientManager
- Permission system enforces file/command access policies
- Hook system provides lifecycle events for audit/metrics

### CLI Tool (Python/Click)

**API Communication**:
- All operations use HTTP/HTTPS via `ai_agent_cli/core/client.py`
- JWT-based authentication with automatic token refresh
- Tokens stored in `~/.ai-agent-cli/config.json`

**Output Formatting**:
- Use `rich` library for tables
- Support both `--format table` and `--format json`

### Frontend (Next.js/TypeScript)

**Import Style**:
- Use `@/` alias for src imports: `import { apiClient } from '@/lib/api-client'`

**Data Fetching**:
- Use React Query (TanStack Query) for all API calls
- Custom hooks in `src/hooks/` (e.g., `useSessions.ts`)
- API client in `src/lib/api-client.ts`

**State Management**:
- Zustand for global state (auth)
- React Query for server state

**UI Components**:
- Use shadcn/ui components from `src/components/ui/`
- Tailwind CSS for styling

## Common Workflows

### Creating a New API Endpoint

1. **Check documentation**: Search `ai-agent-api/docs/INDEX.md` for similar endpoints
2. **Define schema**: Add request/response schemas in `app/schemas/`
3. **Add domain logic**: Update entities in `app/domain/entities/` if needed
4. **Create/update repository**: Add data access methods in `app/repositories/`
5. **Implement service**: Add business logic in `app/services/`
6. **Add API endpoint**: Create route in `app/api/v1/`
7. **Write tests**: Add unit, integration, and E2E tests
8. **Update documentation**: Add to relevant doc in `docs/components/` or `docs/features/`

### Adding a New MCP Server Integration

1. Read `ai-agent-api/docs/INDEX.md` → search "mcp"
2. Check existing MCP implementations in `app/mcp/`
3. Add server config via API or CLI
4. Server configs merge with session SDK options automatically

### Running End-to-End Tests

1. Start test infrastructure: `cd ai-agent-api && make docker-test-up`
2. Run tests: `make test-e2e`
3. Stop infrastructure: `make docker-test-down`

## Database Schema

**Main Tables** (PostgreSQL):
- `users` - User accounts with roles (admin, user, viewer)
- `sessions` - Claude Code sessions with state machine
- `messages` - Session messages (user/assistant)
- `tool_calls` - Tool execution records
- `tasks` - Task templates for automation
- `task_executions` - Task execution history
- `reports` - Generated reports (JSON/Markdown/HTML/PDF)
- `mcp_servers` - MCP server configurations
- `session_templates` - Reusable session configurations
- `audit_logs` - Compliance and audit trail
- `working_directories` - Session working directory metadata

**Relationships**:
- User → Sessions (one-to-many)
- Session → Messages (one-to-many)
- Session → ToolCalls (one-to-many)
- Session → Reports (one-to-many)

See full schema: `ai-agent-api/docs/data-layer/DATABASE_SCHEMA.md`

## Environment Variables

**API (.env in ai-agent-api/)**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aiagent_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
AGENT_WORKDIRS_PATH=./data/agent-workdirs
REPORTS_PATH=./data/reports
```

**CLI (.env or env vars)**:
```bash
AI_AGENT_API_URL=http://localhost:8000
AI_AGENT_ACCESS_TOKEN=<token>  # Optional, for CI/CD
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Important: Module Structure Changes

**CRITICAL: Package-by-Feature Migration**

The API is migrating from layered-by-type to package-by-feature architecture:

**Old Structure** (being phased out):
```
app/
  api/v1/
  services/
  repositories/
  models/
  schemas/
```

**New Structure** (implement new features here):
```
app/modules/
  session_management/
    api/
    services/
    repositories/
    models/
    schemas/
  notification_and_reporting/
    notification/
    reporting/
```

**When implementing NEW features**: Use package-by-feature in `app/modules/`
**When modifying EXISTING features**: Update in current location (don't migrate yet)

See: `ai-agent-api/docs/architecture/HYBRID_ARCHITECTURE_MIGRATION.md`

## Troubleshooting

### API won't start
- Check PostgreSQL/Redis: `docker ps`
- Check logs: `tail -f ai-agent-api/logs/api.log`
- Verify migrations: `cd ai-agent-api && make migrate`

### Tests failing
- Check test DB: `make docker-test-up`
- Run specific test: `pytest tests/unit/test_file.py::test_name -v`
- Check fixtures: `tests/conftest.py`

### CLI authentication issues
- Check API URL: `ai-agent config get-api-url`
- Try login again: `ai-agent auth login`
- Check token: `ai-agent auth status`

### Database query needed
```bash
cd ai-agent-api
make db-list TABLE=sessions     # List all sessions
make db-list TABLE=users        # List all users
make db-list TABLE=messages     # List all messages
```

## Additional Resources

- **API Documentation**: Interactive docs at http://localhost:8000/docs (Swagger) or /redoc
- **CLI Documentation**: `ai-agent-cli/docs/commands/INDEX.md` with complete API flows
- **Architecture Docs**: `ai-agent-api/docs/INDEX.md` - comprehensive technical documentation
