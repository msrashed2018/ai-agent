# AI-Agent-API Service Architecture Documentation

This directory contains comprehensive documentation for the AI-Agent-API service, a FastAPI-based service that provides Claude SDK integration with Model Context Protocol (MCP) framework support.

## Documentation Structure

### Core Architecture
- **[SERVICE_OVERVIEW.md](SERVICE_OVERVIEW.md)** - High-level service description and capabilities
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and design patterns
- **[DATABASE_DESIGN.md](DATABASE_DESIGN.md)** - Database schema and relationships
- **[API_ENDPOINTS.md](API_ENDPOINTS.md)** - REST API and WebSocket endpoint specifications

### Domain Layer
- **[DOMAIN_ENTITIES.md](DOMAIN_ENTITIES.md)** - Core business entities and their behaviors
- **[VALUE_OBJECTS.md](VALUE_OBJECTS.md)** - Immutable value objects and data structures
- **[DOMAIN_EXCEPTIONS.md](DOMAIN_EXCEPTIONS.md)** - Custom exception hierarchy

### Service Layer
- **[BUSINESS_SERVICES.md](BUSINESS_SERVICES.md)** - Business logic services and workflows
- **[SDK_INTEGRATION.md](SDK_INTEGRATION.md)** - Claude SDK integration and MCP framework
- **[STORAGE_MANAGEMENT.md](STORAGE_MANAGEMENT.md)** - File system and storage operations

### Infrastructure Layer
- **[DATA_REPOSITORIES.md](DATA_REPOSITORIES.md)** - Database access patterns and repositories
- **[MIDDLEWARE_STACK.md](MIDDLEWARE_STACK.md)** - Request/response processing pipeline
- **[SECURITY_SYSTEM.md](SECURITY_SYSTEM.md)** - Authentication, authorization, and security

### Configuration & Operations
- **[CONFIGURATION.md](CONFIGURATION.md)** - Environment variables and settings management
- **[MONITORING.md](MONITORING.md)** - Metrics, logging, and observability
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker and production deployment

## Service Overview

The AI-Agent-API service is a production-ready FastAPI application that provides:

- **Claude SDK Integration**: Official Claude Agent SDK with streaming responses
- **Model Context Protocol**: MCP framework for tool integration and external server management
- **Session Management**: Stateful conversation sessions with persistence
- **Task Automation**: Repeatable agent operations with scheduling
- **Real-time Communication**: WebSocket streaming with authentication
- **Multi-tenancy**: Organization and user-based isolation
- **Security**: JWT authentication with role-based access control

## Key Components Summary

### Component Count
- **74 Python files** across clean architecture layers
- **12 database tables** with proper relationships
- **80+ configuration parameters** for comprehensive customization
- **Multiple middleware layers** for request processing
- **WebSocket support** for real-time communication

### Technology Stack
- **FastAPI** with async/await support
- **SQLAlchemy 2.x** with async engine
- **PostgreSQL** with JSONB support
- **Redis** for caching and session state
- **Celery** for background task processing
- **Claude Agent SDK** for AI integration
- **MCP Framework** for tool management

### Service Architecture Pattern
The service follows **Clean Architecture** principles with clear separation of concerns:

```
API Layer (FastAPI) → Service Layer (Business Logic) → Domain Layer (Entities) → Infrastructure (Database/External)
```

Each layer has well-defined responsibilities and dependency injection for testability.

## Getting Started

1. Read **[SERVICE_OVERVIEW.md](SERVICE_OVERVIEW.md)** for capabilities and use cases
2. Review **[ARCHITECTURE.md](ARCHITECTURE.md)** for technical design
3. Examine **[API_ENDPOINTS.md](API_ENDPOINTS.md)** for integration details
4. Check **[CONFIGURATION.md](CONFIGURATION.md)** for deployment setup
