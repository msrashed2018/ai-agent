# AI Agent CLI

A command-line interface tool for interacting with the AI-Agent-API-Service. Manage Claude Code sessions, tasks, reports, and MCP servers through a powerful and intuitive CLI.

## Features

- 🔐 **Authentication** - Login, token management, and user information
- 💬 **Session Management** - Create and manage Claude Code sessions via REST API
- 📋 **Task Automation** - Define, schedule, and execute automated tasks
- 📊 **Report Generation** - List and download session reports in multiple formats
- 🔌 **MCP Server Management** - Register and configure Model Context Protocol servers
- 👑 **Admin Tools** - System statistics and user management (admin only)
- 🎨 **Rich Output** - Beautiful formatted tables and JSON output
- ⚙️ **Configuration** - Flexible configuration with environment variable support

## Installation

### Prerequisites

- Python 3.10 or higher
- Access to a running AI-Agent-API-Service instance

### Install from source

```bash
cd ai-agent-cli
poetry install
```

### Install in development mode

```bash
poetry install
poetry shell
```

## Configuration

### Setting the API URL

```bash
# Set API URL
ai-agent config set-api-url http://localhost:8000

# Or use environment variable
export AI_AGENT_API_URL=http://localhost:8000
```

### Configuration file

Configuration is stored in `~/.ai-agent-cli/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "access_token": "<your-token>",
  "refresh_token": "<your-refresh-token>",
  "default_output_format": "table",
  "timeout": 30
}
```

## Usage

### Authentication

```bash
# Login
ai-agent auth login --email user@example.com --password yourpassword

# Check authentication status
ai-agent auth status

# Get current user info
ai-agent auth whoami

# Refresh access token
ai-agent auth refresh

# Logout
ai-agent auth logout
```

### Session Management

```bash
# Create a new session
ai-agent sessions create \
  --name "My Investigation" \
  --description "Investigating production issue" \
  --allowed-tools "Read" --allowed-tools "Bash"

# List all sessions
ai-agent sessions list --status active --format table

# Get session details
ai-agent sessions get <session-id>

# Send a message to a session
ai-agent sessions query <session-id> "What files are in the current directory?"

# Fork a session before querying
ai-agent sessions query <session-id> "Make changes" --fork

# List messages in a session
ai-agent sessions messages <session-id> --limit 50

# List tool calls in a session
ai-agent sessions tool-calls <session-id>

# Pause a session
ai-agent sessions pause <session-id>

# Resume a session
ai-agent sessions resume <session-id>

# Terminate a session
ai-agent sessions terminate <session-id> --yes

# Download session working directory
ai-agent sessions download-workdir <session-id> --output session-workdir.tar.gz
```

### Task Automation

```bash
# Create a new task
ai-agent tasks create \
  --name "Daily Health Check" \
  --description "Check system health" \
  --prompt-template "Check the health of {{service_name}}" \
  --is-scheduled \
  --schedule-cron "0 9 * * *" \
  --schedule-enabled \
  --generate-report \
  --tags monitoring

# List all tasks
ai-agent tasks list --is-scheduled true

# Get task details
ai-agent tasks get <task-id>

# Update a task
ai-agent tasks update <task-id> --schedule-enabled false

# Execute a task manually
ai-agent tasks execute <task-id> --variables '{"service_name": "nginx"}'

# List task executions
ai-agent tasks executions <task-id>

# Get execution status
ai-agent tasks execution-status <execution-id>

# Delete a task
ai-agent tasks delete <task-id> --yes
```

### Report Management

```bash
# List all reports
ai-agent reports list --session-id <session-id>

# Get report details
ai-agent reports get <report-id>

# Download report in different formats
ai-agent reports download <report-id> --format html --output report.html
ai-agent reports download <report-id> --format pdf --output report.pdf
ai-agent reports download <report-id> --format json --output report.json
```

### MCP Server Management

```bash
# List all MCP servers
ai-agent mcp list

# Create a new MCP server
ai-agent mcp create \
  --name "kubernetes-mcp" \
  --description "Kubernetes cluster access" \
  --server-type stdio \
  --config '{"command": "npx", "args": ["@modelcontextprotocol/server-kubernetes"]}' \
  --enabled

# Get MCP server details
ai-agent mcp get <server-id>

# Update MCP server
ai-agent mcp update <server-id> --enabled false

# Health check
ai-agent mcp health-check <server-id>

# Delete MCP server
ai-agent mcp delete <server-id> --yes

# Import from Claude Desktop config
ai-agent mcp import ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Export to Claude Desktop config format
ai-agent mcp export --output exported-config.json --include-global

# List available templates
ai-agent mcp templates
```

### Admin Commands (Admin users only)

```bash
# Get system statistics
ai-agent admin stats

# List all sessions across all users
ai-agent admin sessions --user-id <user-id> --status active

# List all users
ai-agent admin users --include-deleted
```

### Configuration Management

```bash
# Show current configuration
ai-agent config show

# Set API URL
ai-agent config set-api-url http://api.example.com

# Get current API URL
ai-agent config get-api-url

# Reset configuration to defaults
ai-agent config reset --yes
```

## Output Formats

The CLI supports two output formats:

### Table Format (Default)

Pretty-printed tables with rich formatting:

```bash
ai-agent sessions list --format table
```

### JSON Format

Raw JSON output for scripting:

```bash
ai-agent sessions list --format json
```

## Environment Variables

- `AI_AGENT_API_URL` - Override API base URL
- `AI_AGENT_ACCESS_TOKEN` - Override access token (for CI/CD)

## Examples

### Complete Workflow Example

```bash
# 1. Configure CLI
ai-agent config set-api-url http://localhost:8000

# 2. Login
ai-agent auth login --email admin@example.com

# 3. Create a session
SESSION_ID=$(ai-agent sessions create \
  --name "Code Review" \
  --format json | jq -r '.id')

# 4. Send a query
ai-agent sessions query $SESSION_ID "Review the authentication logic in this codebase"

# 5. Check messages
ai-agent sessions messages $SESSION_ID --format json

# 6. Download working directory
ai-agent sessions download-workdir $SESSION_ID --output review-workdir.tar.gz

# 7. Terminate session
ai-agent sessions terminate $SESSION_ID --yes
```

### Automated Task Example

```bash
# Create a scheduled task for daily backups
ai-agent tasks create \
  --name "Daily Backup Check" \
  --prompt-template "Verify backup status for {{environment}}" \
  --is-scheduled \
  --schedule-cron "0 2 * * *" \
  --schedule-enabled \
  --generate-report \
  --report-format pdf \
  --tags backup,automation

# Execute manually with variables
ai-agent tasks execute <task-id> \
  --variables '{"environment": "production"}'
```

### MCP Server Import Example

```bash
# Import MCP servers from Claude Desktop
ai-agent mcp import \
  ~/Library/Application\ Support/Claude/claude_desktop_config.json \
  --override

# List imported servers
ai-agent mcp list --format table

# Health check all servers
for SERVER_ID in $(ai-agent mcp list --format json | jq -r '.items[].id'); do
  ai-agent mcp health-check $SERVER_ID
done
```

## Documentation

### Comprehensive Command Documentation

Detailed documentation for each command group with **complete backend API processing flows**:

- **[Command Documentation Index](docs/commands/INDEX.md)** - Overview and reading guide
- **[Authentication Commands](docs/commands/01-authentication.md)** - Login, tokens, JWT flow
- **[Session Management](docs/commands/02-sessions.md)** - Sessions, Claude SDK integration, MCP config merging
- **[Task Automation](docs/commands/03-tasks.md)** - Task creation, execution, template rendering
- **[Reports](docs/commands/04-reports.md)** - Report generation and download
- **[MCP Servers](docs/commands/05-mcp-servers.md)** - MCP server management, import/export
- **[Admin Commands](docs/commands/06-admin.md)** - System statistics, monitoring
- **[Config Commands](docs/commands/07-config.md)** - Local CLI configuration

Each documentation file includes:
- ✅ CLI command syntax and examples
- ✅ Step-by-step backend API processing
- ✅ Actual SQL queries executed
- ✅ Claude Code CLI subprocess commands (where applicable)
- ✅ Source file references with line numbers
- ✅ Complete request/response examples

### Quick Links

**Getting Started**:
1. [Set API URL](docs/commands/07-config.md#2-set-api-url)
2. [Login](docs/commands/01-authentication.md#1-login)
3. [Create Session](docs/commands/02-sessions.md#1-create-session)

**Understanding the System**:
- [How Sessions Work](docs/commands/02-sessions.md#4-query-session) - See the complete Claude SDK flow
- [How MCP Servers Are Used](docs/commands/05-mcp-servers.md#how-mcp-servers-are-used-in-sessions) - Config merging explained
- [Task Execution Flow](docs/commands/03-tasks.md#6-execute-task) - From template to Claude Code CLI

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ai_agent_cli --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_client.py
```

### Code Quality

```bash
# Format code
poetry run black ai_agent_cli/

# Lint code
poetry run ruff check ai_agent_cli/

# Type checking
poetry run mypy ai_agent_cli/
```

## Architecture

The CLI is built with a clean architecture:

```
ai_agent_cli/
├── cli.py              # Main CLI entry point
├── core/               # Core functionality
│   ├── config.py       # Configuration management
│   ├── client.py       # HTTP API client
│   └── exceptions.py   # Custom exceptions
├── commands/           # Command modules
│   ├── auth.py         # Authentication commands
│   ├── sessions.py     # Session management
│   ├── tasks.py        # Task automation
│   ├── reports.py      # Report management
│   ├── mcp.py          # MCP server management
│   ├── admin.py        # Admin commands
│   └── config.py       # Config commands
└── utils/              # Utility functions
    └── output.py       # Output formatting
```

## API Communication

The CLI communicates with the AI-Agent-API-Service exclusively through REST API endpoints:

- All operations use HTTP/HTTPS
- JWT-based authentication with access and refresh tokens
- Automatic token refresh on expiration
- Configurable timeout and retry logic
- Support for file uploads and downloads

## Troubleshooting

### Authentication Issues

```bash
# Check authentication status
ai-agent auth status

# Try refreshing token
ai-agent auth refresh

# If refresh fails, login again
ai-agent auth login
```

### API Connection Issues

```bash
# Verify API URL
ai-agent config get-api-url

# Test with health endpoint
curl $(ai-agent config get-api-url)/health

# Update API URL if needed
ai-agent config set-api-url http://correct-url:8000
```

### Debug Mode

Set debug logging for detailed output:

```bash
export LOG_LEVEL=DEBUG
ai-agent sessions list
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]

## Support

- Documentation: See this README and API documentation
- Issues: GitHub Issues
- Email: support@example.com

## Related Projects

- [AI-Agent-API-Service](../ai-agent-api/) - The backend API service
- [Claude Code Agent SDK](https://github.com/anthropics/claude-agent-sdk) - Official SDK
