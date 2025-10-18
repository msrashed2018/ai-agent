# Quick Start Guide

Get started with AI Agent CLI in 5 minutes.

## Installation

```bash
cd ai-agent-cli
poetry install
poetry shell
```

## First-Time Setup

### 1. Configure API URL

```bash
ai-agent config set-api-url http://localhost:8000
```

### 2. Login

```bash
ai-agent auth login
# Enter email: user@example.com
# Enter password: ********
```

### 3. Verify Authentication

```bash
ai-agent auth whoami
```

## Basic Operations

### Create and Use a Session

```bash
# Create session
ai-agent sessions create --name "Quick Test"

# Copy the session ID from output, then query it
ai-agent sessions query <session-id> "List files in current directory"

# View messages
ai-agent sessions messages <session-id>

# Terminate when done
ai-agent sessions terminate <session-id>
```

### Create and Run a Task

```bash
# Create a task
ai-agent tasks create \
  --name "System Check" \
  --prompt-template "Check system status for {{service}}"

# Execute it
ai-agent tasks execute <task-id> --variables '{"service": "nginx"}'

# Check status
ai-agent tasks execution-status <execution-id>
```

### Manage MCP Servers

```bash
# List available servers
ai-agent mcp list

# Import from Claude Desktop
ai-agent mcp import ~/.config/Claude/claude_desktop_config.json
```

## Common Commands

```bash
# List all sessions
ai-agent sessions list

# List all tasks
ai-agent tasks list

# List all reports
ai-agent reports list

# Get system stats (admin only)
ai-agent admin stats
```

## Tips

1. **Use JSON output for scripting**: Add `--format json` to any command
2. **Skip confirmations**: Add `--yes` to delete commands
3. **Get help anytime**: Add `--help` to any command
4. **Use environment variables**: Set `AI_AGENT_API_URL` in your shell profile

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [examples/](examples/) for more use cases
- Configure scheduled tasks for automation
- Set up MCP servers for extended capabilities

## Troubleshooting

### Can't connect to API

```bash
# Check API URL
ai-agent config get-api-url

# Test API connectivity
curl $(ai-agent config get-api-url)/health
```

### Token expired

```bash
# Refresh token
ai-agent auth refresh

# Or login again
ai-agent auth login
```

### Command not found

```bash
# Ensure you're in poetry shell
poetry shell

# Or use poetry run
poetry run ai-agent --help
```

## Support

For issues, check:
- API service is running at the configured URL
- You're authenticated (`ai-agent auth status`)
- You have necessary permissions for admin commands
