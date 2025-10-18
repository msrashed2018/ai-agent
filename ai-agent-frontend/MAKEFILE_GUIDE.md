# AI Agent Frontend Makefile Commands

This document describes all available Makefile commands for the AI Agent Frontend service.

## Quick Start

```bash
# Navigate to frontend directory
cd ai-agent-frontend

# Install dependencies
make install

# Start development server (foreground)
make dev

# OR start in background
make dev-bg

# Check status
make status

# View logs (if running in background)
make logs

# Stop background server
make stop
```

## Command Reference

### Setup Commands

| Command | Description |
|---------|-------------|
| `make install` | Install npm dependencies |
| `make setup` | Complete initial setup (runs install) |

### Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start Next.js dev server in **foreground** |
| `make dev-bg` | Start Next.js dev server in **background** |
| `make stop` | Stop background development server |
| `make restart` | Restart background server |
| `make logs` | Tail development server logs |
| `make status` | Check if server is running |

### Build Commands

| Command | Description |
|---------|-------------|
| `make build` | Build for production |
| `make start` | Start production server |
| `make preview` | Preview production build |

### Code Quality Commands

| Command | Description |
|---------|-------------|
| `make lint` | Run ESLint |
| `make lint-fix` | Auto-fix ESLint issues |
| `make type-check` | Run TypeScript type checking |
| `make format` | Format code with Prettier |
| `make format-check` | Check code formatting |
| `make check` | Run all checks (lint + type-check) |

### Testing Commands

| Command | Description |
|---------|-------------|
| `make test` | Run tests |
| `make test-watch` | Run tests in watch mode |
| `make test-coverage` | Run tests with coverage |

### Cleanup Commands

| Command | Description |
|---------|-------------|
| `make clean` | Clean build artifacts and caches |
| `make clean-all` | Clean everything including node_modules |

### Utility Commands

| Command | Description |
|---------|-------------|
| `make info` | Display project information |
| `make deps-update` | Update dependencies |
| `make deps-check` | Check for outdated dependencies |
| `make open` | Open frontend in browser |
| `make help` | Display help message |

### Quick Start Aliases

| Command | Description |
|---------|-------------|
| `make run` | Alias for `dev-bg` (background mode) |
| `make run-fg` | Alias for `dev` (foreground mode) |
| `make all` | Install, check, and build |

## Usage Examples

### Starting Development

**Foreground mode (recommended for active development):**
```bash
make dev
```
Output will stream to your terminal. Press Ctrl+C to stop.

**Background mode (for running alongside other tasks):**
```bash
make dev-bg
```
Server runs in background. Use `make logs` to view output.

### Checking Service Status

```bash
make status
```

Example output:
```
AI Agent Frontend Status:

  ✓ Running (PID: 12345)
  → http://localhost:3000
```

### Viewing Logs

```bash
make logs
```
Press Ctrl+C to stop tailing.

### Stopping Background Server

```bash
make stop
```

### Before Committing Code

```bash
# Check code quality
make check

# Or run individual checks
make lint
make type-check
```

### Building for Production

```bash
# Build
make build

# Start production server
make start
```

## Configuration

### Port Configuration

Default port is 3000. To change:

```bash
# In the frontend directory
FRONTEND_PORT=3001 make dev
```

Or modify the Makefile:
```makefile
FRONTEND_PORT ?= 3001
```

### Log Directory

Logs are stored in `./logs/` by default. To change:

```bash
LOG_DIR=/path/to/logs make dev-bg
```

## Background Process Management

When running in background mode (`make dev-bg`):

- **PID file**: `logs/dev.pid` - Contains process ID
- **Log file**: `logs/dev.log` - Contains server output
- **Port**: 3000 (default)

The `stop` command will:
1. Read PID from `logs/dev.pid`
2. Send SIGTERM to gracefully stop
3. Force kill with SIGKILL if needed
4. Clean up any processes on port 3000

## Environment Variables

The frontend uses `.env.local` for configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8888
```

No need to configure this in the Makefile - Next.js handles it automatically.

## Integration with Root Makefile

This frontend has its own dedicated Makefile. To use it:

```bash
# From repository root
cd ai-agent-frontend
make dev

# OR directly
make -C ai-agent-frontend dev
```

The root Makefile focuses on KubeMind services. This frontend Makefile provides focused, service-specific commands.

## Troubleshooting

### Port Already in Use

```bash
# Stop will clean up port 3000
make stop
```

### Dependencies Not Found

```bash
make clean-all
make install
```

### Build Failures

```bash
# Clean and rebuild
make clean
make build
```

### Logs Not Available

If running in foreground mode (`make dev`), logs go directly to terminal, not to file.

For background logs:
```bash
# Check if running in background
make status

# View logs
make logs
```

## Development Workflow

**Typical workflow:**

```bash
# 1. Initial setup (first time only)
make setup

# 2. Start development
make dev-bg

# 3. Check it's running
make status

# 4. Make changes (hot reload is automatic)

# 5. Check code quality before committing
make check

# 6. Stop when done
make stop
```

**For multiple services:**

```bash
# Terminal 1: Start API
cd ../ai-agent-api
make run-bg

# Terminal 2: Start Frontend
cd ai-agent-frontend
make dev-bg

# Terminal 3: View frontend logs
cd ai-agent-frontend
make logs

# When done, stop all
make stop
cd ../ai-agent-api
make stop-bg
```

## Comparison with npm Scripts

| npm Command | Makefile Equivalent | Notes |
|-------------|---------------------|-------|
| `npm run dev` | `make dev` | Foreground mode |
| `npm run build` | `make build` | Production build |
| `npm run start` | `make start` | Production server |
| `npm run lint` | `make lint` | ESLint |
| `npm run type-check` | `make type-check` | TypeScript |
| - | `make dev-bg` | Background mode (Makefile only) |
| - | `make status` | Status check (Makefile only) |
| - | `make logs` | Log viewing (Makefile only) |

The Makefile adds conveniences like:
- Background process management
- Status checking
- Log tailing
- Automatic port cleanup
- Combined workflows

## Getting Help

```bash
# Display all commands
make help

# Display project info
make info
```

## Related Documentation

- Frontend README: `./README.md`
- Package.json: `./package.json`
- Next.js Config: `./next.config.js`
- TypeScript Config: `./tsconfig.json`
