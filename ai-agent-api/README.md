# AI-Agent-API-Service

Enterprise-grade API service for Claude Code Agent SDK with comprehensive session management, business logic, and extensibility features.

## Overview

The AI-Agent-API-Service is a production-ready FastAPI wrapper around the Claude Code Agent SDK that transforms the SDK into a stateful, persistent, multi-tenant service.

### Key Features

- **Session Management** - Persistent sessions with full history
- **Task Automation** - Template-based tasks with scheduling
- **MCP Tool Integration** - SDK and external MCP servers
- **Security & Compliance** - JWT authentication, RBAC, comprehensive audit logging
- **Reporting** - Multi-format report generation (JSON, Markdown, HTML, PDF)
- **WebSocket Support** - Real-time streaming APIs

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Anthropic API Key

### Installation

```bash
# Clone repository
git clone <repository-url>
cd ai-agent-api

# Setup environment
make setup
# Edit .env file with your configuration

# Install dependencies
make install

# Run database migrations
make migrate

# Start services with Docker Compose
make docker-up
```

### Development Setup

```bash
# Install development dependencies
make dev

# Run tests
make test

# Run linters
make lint

# Format code
make format
```

## Architecture

### Directory Structure

```
ai-agent-api/
├── app/                    # Main application code
│   ├── api/               # API layer (FastAPI routes)
│   ├── domain/            # Domain layer (entities, value objects)
│   ├── services/          # Service layer (business logic)
│   ├── repositories/      # Data access layer
│   ├── models/            # SQLAlchemy ORM models
│   ├── claude_sdk/        # Claude SDK integration
│   ├── mcp_tools/         # MCP tool implementations
│   └── core/              # Core utilities
├── tests/                 # Test suite
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
└── data/                  # Runtime data
```

## API Documentation

Once the service is running, access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage Examples

### Create a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Investigation Session",
    "mode": "interactive",
    "sdk_options": {
      "permission_mode": "default",
      "allowed_tools": ["Read", "Write", "Bash"]
    }
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the status of the nginx pods?"
  }'
```

## Configuration

See `.env.example` for all available configuration options.

Key configuration areas:
- Database connection
- Redis connection
- Claude API key
- Security settings
- Storage paths
- Rate limiting

## Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Deployment

### Docker Compose (Development)

```bash
make docker-up
```

### Production Deployment

See `docs/DEPLOYMENT.md` for production deployment guides covering:
- Docker deployment
- Kubernetes with Helm
- Environment configuration
- Monitoring setup
- Backup procedures

## Contributing

1. Create a feature branch
2. Write code + tests (maintain 80%+ coverage)
3. Run linters and formatters
4. Submit pull request

## License

[Your License Here]

## Support

- Documentation: See `docs/` directory
- Issues: GitHub Issues
- Email: support@example.com
