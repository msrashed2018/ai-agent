# Command Documentation Index

Complete documentation for all CLI commands with detailed backend processing flows.

Each document explains:
- CLI command syntax and options
- Step-by-step backend API processing
- Database queries executed
- The actual Claude Code CLI commands spawned (where applicable)
- Complete request/response examples
- Key backend source files with line numbers

---

## Documentation Structure

### 1. [Authentication Commands](01-authentication.md)
**Commands**: `login`, `logout`, `whoami`, `refresh`, `status`

Core authentication flow including:
- JWT token generation with HS256 algorithm
- Bcrypt password verification
- Token refresh mechanism
- User session management

### 2. [Session Management Commands](02-sessions.md)
**Commands**: `create`, `list`, `get`, `query`, `messages`, `tool-calls`, `pause`, `resume`, `terminate`, `download-workdir`

Complete session lifecycle including:
- Session creation with working directory setup
- MCP server configuration merging (SDK tools + User servers + Global servers)
- Claude SDK client initialization
- Claude Code CLI subprocess spawning with MCP servers
- Message handling and tool call tracking
- Session state management

**Key Details**: Shows the actual `claude` command that gets spawned with all MCP server configurations.

### 3. [Task Automation Commands](03-tasks.md)
**Commands**: `create`, `list`, `get`, `update`, `delete`, `execute`, `executions`, `execution-status`

Task automation and scheduling:
- Task creation with cron schedule validation
- Prompt template rendering with variable substitution
- Task execution flow (creates new session per execution)
- Report generation (HTML/PDF/JSON)
- Execution history tracking

**Key Details**: Shows how task execution creates sessions and the complete template rendering process.

### 4. [Report Commands](04-reports.md)
**Commands**: `list`, `get`, `download`

Report generation and retrieval:
- Report content building from session data
- Multi-format support (HTML, PDF, JSON, Markdown)
- File storage management
- Report metadata and tagging
- Authorization checks

**Key Details**: Explains report generation flow from session messages and tool calls.

### 5. [MCP Server Commands](05-mcp-servers.md)
**Commands**: `list`, `create`, `get`, `update`, `delete`, `health-check`, `import`, `export`, `templates`

Model Context Protocol server management:
- MCP server types (stdio, SSE, HTTP)
- Server configuration validation
- Claude Desktop config import/export
- Pre-configured templates for popular servers
- How MCP servers are merged and used in sessions

**Key Details**: Complete explanation of MCP config merging and how servers get passed to Claude SDK.

### 6. [Admin Commands](06-admin.md)
**Commands**: `stats`, `sessions`, `users`

Administrative monitoring (admin role required):
- System-wide statistics aggregation
- Cross-user session monitoring
- User management overview
- Cost tracking and analysis
- Admin authorization flow

**Key Details**: Shows admin-only database queries and authorization checks.

### 7. [Config Commands](07-config.md)
**Commands**: `show`, `set-api-url`, `get-api-url`, `reset`

Local CLI configuration management:
- Config file structure and location
- API URL management
- Environment variable overrides
- Security best practices
- Multi-environment setup

**Key Details**: Local-only commands that don't interact with API service.

---

## Quick Reference

### By Complexity

**Beginner**:
- [Authentication](01-authentication.md) - Login and token management
- [Config](07-config.md) - CLI setup and configuration

**Intermediate**:
- [Sessions](02-sessions.md) - Interactive Claude sessions
- [Reports](04-reports.md) - View and download reports

**Advanced**:
- [Tasks](03-tasks.md) - Automated task execution
- [MCP Servers](05-mcp-servers.md) - External tool integration
- [Admin](06-admin.md) - System administration

### By Use Case

**Getting Started**:
1. [Config: set-api-url](07-config.md#2-set-api-url) - Point CLI to API service
2. [Auth: login](01-authentication.md#1-login) - Authenticate
3. [Sessions: create](02-sessions.md#1-create-session) - Start your first session

**Daily Usage**:
- [Sessions: query](02-sessions.md#4-query-session) - Ask Claude questions
- [Sessions: list](02-sessions.md#2-list-sessions) - See your sessions
- [Reports: download](04-reports.md#3-download-report-file) - Get session reports

**Automation**:
- [Tasks: create](03-tasks.md#1-create-task) - Set up automated tasks
- [Tasks: execute](03-tasks.md#6-execute-task) - Run tasks on demand
- [MCP: import](05-mcp-servers.md#6-import-claude-desktop-config) - Import Claude Desktop servers

**Administration**:
- [Admin: stats](06-admin.md#1-system-statistics) - Monitor system health
- [Admin: sessions](06-admin.md#2-list-all-sessions-admin) - View all users' sessions
- [Admin: users](06-admin.md#3-list-all-users) - Manage users

---

## Understanding Backend Processing

Each command documentation includes:

### 1. Database Queries
Actual SQL queries executed in PostgreSQL:
```sql
SELECT * FROM sessions WHERE id = 'session-uuid';
UPDATE sessions SET status = 'active' WHERE id = 'session-uuid';
INSERT INTO messages (id, session_id, role, content) VALUES (...);
```

### 2. Business Logic
Step-by-step processing in service layer:
- Validation
- Authorization checks
- Entity transformations
- State management

### 3. Claude SDK Integration
How commands interact with Claude Agent SDK:
- ClaudeAgentOptions configuration
- MCP server merging
- Permission callbacks
- Hook handlers

### 4. Claude Code CLI
The actual subprocess commands spawned:
```bash
claude \
  --cwd /data/sessions/abc123 \
  --model claude-sonnet-4-5 \
  --allowed-tools "Bash,Read" \
  --mcp-server kubernetes:sdk \
  --mcp-server my-server:npx:"-y":"@modelcontextprotocol/server-kubernetes"
```

### 5. Source File References
Direct links to implementation with line numbers:
- [app/api/v1/sessions.py:45-67](../../ai-agent-api/app/api/v1/sessions.py#L45-L67)
- [app/services/sdk_session_service.py:89-120](../../ai-agent-api/app/services/sdk_session_service.py#L89-L120)

---

## Reading Guide

### For End Users
Focus on:
- Command syntax examples
- Use case examples at the end of each section
- Quick reference tables

### For Developers
Focus on:
- "What Happens in Backend API" sections
- Database query examples
- Source file references
- Flow diagrams

### For DevOps/SRE
Focus on:
- Admin commands documentation
- System statistics and monitoring
- Authorization flows
- Multi-environment configuration

---

## Conventions Used

### Command Syntax
```bash
# Required argument
ai-agent sessions create --name session-name

# Optional argument
ai-agent sessions list [--page 1]

# Multiple options
ai-agent tasks create --name task-name --prompt "..." [--schedule "0 * * * *"]
```

### Database Queries
```sql
-- Comment explaining what this does
SELECT * FROM table_name
WHERE condition = 'value';
```

### Python Code
```python
# Business logic example
def process_session(session_id: UUID) -> Session:
    session = await session_repo.get_by_id(session_id)
    # ... processing
    return session
```

### JSON Responses
```json
{
  "id": "uuid",
  "field": "value",
  "nested": {
    "key": "value"
  }
}
```

### File References
Format: `[description](relative/path/to/file.py:start_line-end_line)`

Example: [Session creation logic](../../ai-agent-api/app/services/sdk_session_service.py:45-120)

---

## Documentation Updates

When updating command documentation:

1. **Read Implementation First**: Always read the actual backend code before documenting
2. **Include SQL Queries**: Show the actual database queries executed
3. **Show Claude CLI Commands**: For session-related commands, show the subprocess command
4. **Link Source Files**: Reference implementation with line numbers
5. **Add Examples**: Include practical usage examples
6. **Update This Index**: Add new commands to appropriate sections

---

## Related Documentation

- **API Service**: [ai-agent-api/README.md](../../ai-agent-api/README.md)
- **Architecture**: [ai-agent-api/ARCHITECTURE.md](../../ai-agent-api/ARCHITECTURE.md)
- **CLI Tool**: [ai-agent-cli/README.md](../../README.md)
- **Quick Start**: [ai-agent-cli/QUICKSTART.md](../../QUICKSTART.md)

---

## Feedback

Found an issue or have suggestions for documentation improvements?
- Check actual implementation in [ai-agent-api](../../ai-agent-api/)
- Verify SQL queries match database schema
- Test commands against running API service
- Update documentation to reflect actual behavior
