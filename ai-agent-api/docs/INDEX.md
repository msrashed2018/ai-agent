# AI-Agent-API Documentation Index

## Purpose

This INDEX serves as the **primary entry point** for all documentation. Use Ctrl+F to search for keywords and quickly locate the documentation you need.

---

## Quick Start

**New to the project?** Start here:
1. [Architecture Overview](architecture/OVERVIEW.md) - Understand the system
2. [Setup Guide](development/SETUP_GUIDE.md) - Get the service running
3. [Quick Start Guide](guides/QUICK_START.md) - Make your first API call
4. [REST API Endpoints](components/api/REST_API_ENDPOINTS.md) - Available APIs

**Working on a specific feature?** Search the keyword table below.

---

## Documentation Sections

### 📐 Architecture

High-level system design and architectural patterns.

| Document | Description | Keywords |
|----------|-------------|----------|
| [OVERVIEW.md](architecture/OVERVIEW.md) | System architecture, components, and interactions | `architecture`, `overview`, `layers`, `components`, `system-design` |
| [LAYERED_ARCHITECTURE.md](architecture/LAYERED_ARCHITECTURE.md) | Layer separation, dependencies, and responsibilities | `layers`, `api-layer`, `service-layer`, `repository-layer`, `domain-layer`, `clean-architecture` |
| [DOMAIN_MODEL.md](architecture/DOMAIN_MODEL.md) | Domain entities, value objects, business rules | `domain`, `entities`, `value-objects`, `session`, `user`, `task`, `state-machine`, `ddd` |
| [DATA_FLOW.md](architecture/DATA_FLOW.md) | Request-response flow through all layers | `data-flow`, `request-flow`, `session-creation`, `query-execution`, `authentication-flow` |
| [TECHNOLOGY_STACK.md](architecture/TECHNOLOGY_STACK.md) | All technologies, libraries, and tools | `technologies`, `fastapi`, `postgresql`, `redis`, `celery`, `sqlalchemy`, `dependencies` |

---

### 🔧 Core Components

Fundamental infrastructure services used throughout the application.

| Document | Description | Keywords |
|----------|-------------|----------|
| [CONFIGURATION.md](components/core/CONFIGURATION.md) | Settings, environment variables, config management | `configuration`, `settings`, `environment`, `env-vars`, `config` |
| [LOGGING_MONITORING.md](components/core/LOGGING_MONITORING.md) | Structured logging, metrics, health checks | `logging`, `monitoring`, `metrics`, `prometheus`, `structlog`, `health` |
| [STORAGE_MANAGEMENT.md](components/core/STORAGE_MANAGEMENT.md) | File storage, working directories, archival | `storage`, `files`, `working-directory`, `archive`, `filesystem` |

---

### 🌐 API Layer

REST and WebSocket endpoints for external clients.

| Document | Description | Keywords |
|----------|-------------|----------|
| [REST_API_ENDPOINTS.md](components/api/REST_API_ENDPOINTS.md) | All REST endpoints with schemas | `api`, `endpoints`, `rest`, `routes`, `fastapi`, `sessions`, `tasks`, `reports` |
| [WEBSOCKET_API.md](components/api/WEBSOCKET_API.md) | WebSocket streaming endpoints | `websocket`, `streaming`, `real-time`, `ws`, `sse` |
| [AUTHENTICATION.md](components/api/AUTHENTICATION.md) | JWT authentication, token management | `auth`, `authentication`, `jwt`, `token`, `login`, `security` |
| [MIDDLEWARE.md](components/api/MIDDLEWARE.md) | CORS, rate limiting, error handling | `middleware`, `cors`, `rate-limit`, `error-handling`, `request-id` |

---

### 📦 Sessions

Core session management functionality.

| Document | Description | Keywords |
|----------|-------------|----------|
| [SESSION_LIFECYCLE.md](components/sessions/SESSION_LIFECYCLE.md) | Creation, activation, termination, archival | `session`, `lifecycle`, `states`, `create`, `activate`, `terminate`, `archive` |
| [SESSION_MODES.md](components/sessions/SESSION_MODES.md) | Interactive vs Background execution | `session-mode`, `interactive`, `background`, `non-interactive`, `forked` |
| [SESSION_FORKING.md](components/sessions/SESSION_FORKING.md) | Fork/clone sessions with working directory | `fork`, `clone`, `session-fork`, `copy`, `duplicate` |
| [WORKING_DIRECTORIES.md](components/sessions/WORKING_DIRECTORIES.md) | Session working directory management | `workdir`, `working-directory`, `isolation`, `cleanup`, `filesystem` |

---

### 🤖 Claude SDK Integration

Integration with official claude-agent-sdk.

| Document | Description | Keywords |
|----------|-------------|----------|
| [SDK_INTEGRATION_OVERVIEW.md](components/claude_sdk/SDK_INTEGRATION_OVERVIEW.md) | SDK architecture, phases, components | `claude-sdk`, `sdk`, `integration`, `phases`, `client-manager` |
| [CLIENT_MANAGEMENT.md](components/claude_sdk/CLIENT_MANAGEMENT.md) | SDK client lifecycle, connection pooling | `client`, `client-manager`, `connection`, `lifecycle`, `pool` |
| [EXECUTION_STRATEGIES.md](components/claude_sdk/EXECUTION_STRATEGIES.md) | Interactive/Background/Forked executors | `executor`, `execution`, `interactive`, `background`, `forked`, `strategy` |
| [PERMISSION_SYSTEM.md](components/claude_sdk/PERMISSION_SYSTEM.md) | Policy engine, access control | `permissions`, `policy`, `whitelist`, `blacklist`, `file-access`, `command-policy` |
| [HOOK_SYSTEM.md](components/claude_sdk/HOOK_SYSTEM.md) | Lifecycle hooks, audit, metrics | `hooks`, `lifecycle`, `events`, `audit`, `metrics`, `callbacks` |
| [RETRY_RESILIENCE.md](components/claude_sdk/RETRY_RESILIENCE.md) | Circuit breakers, retry policies | `retry`, `circuit-breaker`, `resilience`, `error-handling`, `backoff` |
| [MESSAGE_PROCESSING.md](components/claude_sdk/MESSAGE_PROCESSING.md) | Message handling, streaming | `message`, `processing`, `streaming`, `handler`, `broadcast` |

---

### 🔌 MCP (Model Context Protocol)

External tool and server integration.

| Document | Description | Keywords |
|----------|-------------|----------|
| [MCP_OVERVIEW.md](components/mcp/MCP_OVERVIEW.md) | MCP architecture and purpose | `mcp`, `tools`, `servers`, `model-context-protocol` |
| [MCP_SERVER_MANAGEMENT.md](components/mcp/MCP_SERVER_MANAGEMENT.md) | Add, configure, manage MCP servers | `mcp-server`, `server-management`, `config`, `enable`, `disable` |
| [SDK_TOOLS.md](components/mcp/SDK_TOOLS.md) | Built-in SDK tools | `sdk-tools`, `builtin-tools`, `kubernetes`, `k8s` |
| [TOOL_CONFIGURATION.md](components/mcp/TOOL_CONFIGURATION.md) | Tool registry, config builder | `tool-config`, `registry`, `config-builder`, `tool-registry` |

---

### ⚙️ Tasks & Automation

Task templates and scheduling.

| Document | Description | Keywords |
|----------|-------------|----------|
| [TASK_AUTOMATION.md](components/tasks/TASK_AUTOMATION.md) | Task templates, scheduling, execution | `task`, `automation`, `template`, `schedule`, `cron` |
| [TEMPLATE_SYSTEM.md](components/tasks/TEMPLATE_SYSTEM.md) | Session templates, reusable configs | `template`, `session-template`, `jinja2`, `variables` |
| [CELERY_BACKGROUND_JOBS.md](components/tasks/CELERY_BACKGROUND_JOBS.md) | Async task execution with Celery | `celery`, `background`, `async-tasks`, `queue`, `worker` |

---

### 📊 Reporting

Report generation in multiple formats.

| Document | Description | Keywords |
|----------|-------------|----------|
| [REPORT_GENERATION.md](components/reporting/REPORT_GENERATION.md) | Generate reports from sessions | `report`, `generation`, `export`, `pdf`, `markdown` |
| [REPORT_TYPES.md](components/reporting/REPORT_TYPES.md) | JSON, Markdown, HTML, PDF formats | `report-format`, `json`, `markdown`, `html`, `pdf`, `weasyprint` |

---

### 🔒 Security

Authentication, authorization, and audit logging.

| Document | Description | Keywords |
|----------|-------------|----------|
| [AUTHENTICATION_AUTHORIZATION.md](components/security/AUTHENTICATION_AUTHORIZATION.md) | JWT auth, RBAC, user roles | `auth`, `jwt`, `rbac`, `roles`, `permissions`, `authorization` |
| [AUDIT_LOGGING.md](components/security/AUDIT_LOGGING.md) | Audit trail, compliance logging | `audit`, `logging`, `compliance`, `audit-log`, `trail` |
| [SECURITY_POLICIES.md](components/security/SECURITY_POLICIES.md) | File access, command, network policies | `security-policy`, `file-access`, `command-policy`, `network-policy` |

---

### 🎯 Features

High-level user-facing features.

| Document | Description | Keywords |
|----------|-------------|----------|
| [USER_MANAGEMENT.md](features/USER_MANAGEMENT.md) | User CRUD, roles, quotas | `user`, `user-management`, `roles`, `quotas`, `permissions` |
| [SESSION_TEMPLATES.md](features/SESSION_TEMPLATES.md) | Creating and using session templates | `session-template`, `template`, `reusable`, `presets` |
| [MULTI_TENANCY.md](features/MULTI_TENANCY.md) | Tenant isolation, resource quotas | `multi-tenant`, `tenancy`, `isolation`, `quotas`, `organization` |
| [REAL_TIME_STREAMING.md](features/REAL_TIME_STREAMING.md) | WebSocket streaming implementation | `streaming`, `websocket`, `real-time`, `sse`, `push` |
| [METRICS_MONITORING.md](features/METRICS_MONITORING.md) | Prometheus metrics, session metrics | `metrics`, `monitoring`, `prometheus`, `session-metrics`, `observability` |

---

### 💾 Data Layer

Database schema, ORM, and persistence.

| Document | Description | Keywords |
|----------|-------------|----------|
| [DATABASE_SCHEMA.md](data-layer/DATABASE_SCHEMA.md) | Complete database schema (all tables) | `database`, `schema`, `tables`, `columns`, `relationships`, `postgresql` |
| [ORM_MODELS.md](data-layer/ORM_MODELS.md) | SQLAlchemy model mapping | `orm`, `sqlalchemy`, `models`, `relationships`, `mapping` |
| [REPOSITORIES.md](data-layer/REPOSITORIES.md) | Repository pattern implementation | `repository`, `data-access`, `crud`, `queries`, `pattern` |
| [MIGRATIONS.md](data-layer/MIGRATIONS.md) | Alembic migration workflow | `migrations`, `alembic`, `database-migration`, `schema-changes` |
| [REDIS_CACHING.md](data-layer/REDIS_CACHING.md) | Caching strategy, invalidation | `redis`, `cache`, `caching`, `invalidation`, `performance` |

---

### 🔗 Integration

External systems and dependencies.

| Document | Description | Keywords |
|----------|-------------|----------|
| [EXTERNAL_DEPENDENCIES.md](integration/EXTERNAL_DEPENDENCIES.md) | PostgreSQL, Redis, Celery setup | `dependencies`, `postgresql`, `redis`, `celery`, `setup`, `external` |
| [CLAUDE_API.md](integration/CLAUDE_API.md) | Anthropic API integration | `claude-api`, `anthropic`, `api-key`, `sdk`, `claude` |
| [KUBERNETES_MCP.md](integration/KUBERNETES_MCP.md) | Kubernetes MCP tool integration | `kubernetes`, `k8s`, `mcp`, `kubectl`, `pods` |

---

### 🛠️ Development

Developer guides and best practices.

| Document | Description | Keywords |
|----------|-------------|----------|
| [SETUP_GUIDE.md](development/SETUP_GUIDE.md) | Local development setup | `setup`, `install`, `local-dev`, `dependencies`, `getting-started` |
| [CODE_PATTERNS.md](development/CODE_PATTERNS.md) | Coding standards, naming conventions | `code-patterns`, `standards`, `conventions`, `best-practices`, `style` |
| [TESTING_STRATEGY.md](development/TESTING_STRATEGY.md) | Unit, integration, E2E testing | `testing`, `pytest`, `unit-tests`, `integration-tests`, `e2e`, `fixtures` |
| [ERROR_HANDLING.md](development/ERROR_HANDLING.md) | Exception hierarchy, error patterns | `errors`, `exceptions`, `error-handling`, `exception-hierarchy` |
| [DEBUGGING_GUIDE.md](development/DEBUGGING_GUIDE.md) | Common issues, troubleshooting | `debugging`, `troubleshooting`, `issues`, `problems`, `solutions` |

---

### 🚀 Deployment

Production deployment and configuration.

| Document | Description | Keywords |
|----------|-------------|----------|
| [DOCKER_DEPLOYMENT.md](deployment/DOCKER_DEPLOYMENT.md) | Docker Compose setup | `docker`, `docker-compose`, `containers`, `deployment` |
| [PRODUCTION_CHECKLIST.md](deployment/PRODUCTION_CHECKLIST.md) | Pre-deployment validation | `production`, `checklist`, `deployment`, `validation`, `launch` |
| [ENVIRONMENT_CONFIGURATION.md](deployment/ENVIRONMENT_CONFIGURATION.md) | .env variables, secrets | `environment`, `env`, `config`, `secrets`, `variables` |

---

### 📚 Guides

Step-by-step tutorials and workflows.

| Document | Description | Keywords |
|----------|-------------|----------|
| [QUICK_START.md](guides/QUICK_START.md) | Get running in 5 minutes | `quick-start`, `getting-started`, `first-steps`, `tutorial` |
| [CREATING_A_SESSION.md](guides/CREATING_A_SESSION.md) | Step-by-step session creation | `create-session`, `session`, `tutorial`, `walkthrough` |
| [ADDING_MCP_SERVERS.md](guides/ADDING_MCP_SERVERS.md) | How to add MCP servers | `mcp`, `add-server`, `tutorial`, `how-to` |
| [IMPLEMENTING_CUSTOM_HOOKS.md](guides/IMPLEMENTING_CUSTOM_HOOKS.md) | Custom hook development | `hooks`, `custom-hooks`, `development`, `extend`, `how-to` |
| [IMPLEMENTING_CUSTOM_POLICIES.md](guides/IMPLEMENTING_CUSTOM_POLICIES.md) | Custom permission policy development | `policies`, `permissions`, `custom-policy`, `development`, `how-to` |
| [COMMON_WORKFLOWS.md](guides/COMMON_WORKFLOWS.md) | Typical use cases and flows | `workflows`, `use-cases`, `examples`, `scenarios` |

---

## Quick Keyword Reference Table

Use this table to quickly find documentation by keyword. Press Ctrl+F and search for your keyword.

| Keyword | Related Documents |
|---------|-------------------|
| **architecture** | [OVERVIEW](architecture/OVERVIEW.md), [LAYERED_ARCHITECTURE](architecture/LAYERED_ARCHITECTURE.md) |
| **api** | [REST_API_ENDPOINTS](components/api/REST_API_ENDPOINTS.md), [WEBSOCKET_API](components/api/WEBSOCKET_API.md), [MIDDLEWARE](components/api/MIDDLEWARE.md) |
| **authentication** | [AUTHENTICATION](components/api/AUTHENTICATION.md), [AUTHENTICATION_AUTHORIZATION](components/security/AUTHENTICATION_AUTHORIZATION.md) |
| **audit** | [AUDIT_LOGGING](components/security/AUDIT_LOGGING.md), [HOOK_SYSTEM](components/claude_sdk/HOOK_SYSTEM.md) |
| **background** | [SESSION_MODES](components/sessions/SESSION_MODES.md), [EXECUTION_STRATEGIES](components/claude_sdk/EXECUTION_STRATEGIES.md), [CELERY_BACKGROUND_JOBS](components/tasks/CELERY_BACKGROUND_JOBS.md) |
| **cache** | [REDIS_CACHING](data-layer/REDIS_CACHING.md) |
| **celery** | [CELERY_BACKGROUND_JOBS](components/tasks/CELERY_BACKGROUND_JOBS.md), [TECHNOLOGY_STACK](architecture/TECHNOLOGY_STACK.md) |
| **circuit-breaker** | [RETRY_RESILIENCE](components/claude_sdk/RETRY_RESILIENCE.md) |
| **claude-sdk** | [SDK_INTEGRATION_OVERVIEW](components/claude_sdk/SDK_INTEGRATION_OVERVIEW.md), [CLIENT_MANAGEMENT](components/claude_sdk/CLIENT_MANAGEMENT.md) |
| **configuration** | [CONFIGURATION](components/core/CONFIGURATION.md), [ENVIRONMENT_CONFIGURATION](deployment/ENVIRONMENT_CONFIGURATION.md) |
| **database** | [DATABASE_SCHEMA](data-layer/DATABASE_SCHEMA.md), [ORM_MODELS](data-layer/ORM_MODELS.md), [MIGRATIONS](data-layer/MIGRATIONS.md) |
| **deployment** | [DOCKER_DEPLOYMENT](deployment/DOCKER_DEPLOYMENT.md), [PRODUCTION_CHECKLIST](deployment/PRODUCTION_CHECKLIST.md) |
| **docker** | [DOCKER_DEPLOYMENT](deployment/DOCKER_DEPLOYMENT.md) |
| **domain** | [DOMAIN_MODEL](architecture/DOMAIN_MODEL.md), [LAYERED_ARCHITECTURE](architecture/LAYERED_ARCHITECTURE.md) |
| **entities** | [DOMAIN_MODEL](architecture/DOMAIN_MODEL.md) |
| **errors** | [ERROR_HANDLING](development/ERROR_HANDLING.md), [RETRY_RESILIENCE](components/claude_sdk/RETRY_RESILIENCE.md) |
| **executor** | [EXECUTION_STRATEGIES](components/claude_sdk/EXECUTION_STRATEGIES.md) |
| **fastapi** | [TECHNOLOGY_STACK](architecture/TECHNOLOGY_STACK.md), [REST_API_ENDPOINTS](components/api/REST_API_ENDPOINTS.md) |
| **fork** | [SESSION_FORKING](components/sessions/SESSION_FORKING.md) |
| **hooks** | [HOOK_SYSTEM](components/claude_sdk/HOOK_SYSTEM.md), [IMPLEMENTING_CUSTOM_HOOKS](guides/IMPLEMENTING_CUSTOM_HOOKS.md) |
| **interactive** | [SESSION_MODES](components/sessions/SESSION_MODES.md), [EXECUTION_STRATEGIES](components/claude_sdk/EXECUTION_STRATEGIES.md) |
| **jwt** | [AUTHENTICATION](components/api/AUTHENTICATION.md), [AUTHENTICATION_AUTHORIZATION](components/security/AUTHENTICATION_AUTHORIZATION.md) |
| **kubernetes** | [KUBERNETES_MCP](integration/KUBERNETES_MCP.md), [SDK_TOOLS](components/mcp/SDK_TOOLS.md) |
| **logging** | [LOGGING_MONITORING](components/core/LOGGING_MONITORING.md), [AUDIT_LOGGING](components/security/AUDIT_LOGGING.md) |
| **mcp** | [MCP_OVERVIEW](components/mcp/MCP_OVERVIEW.md), [MCP_SERVER_MANAGEMENT](components/mcp/MCP_SERVER_MANAGEMENT.md), [ADDING_MCP_SERVERS](guides/ADDING_MCP_SERVERS.md) |
| **message** | [MESSAGE_PROCESSING](components/claude_sdk/MESSAGE_PROCESSING.md), [DOMAIN_MODEL](architecture/DOMAIN_MODEL.md) |
| **metrics** | [LOGGING_MONITORING](components/core/LOGGING_MONITORING.md), [METRICS_MONITORING](features/METRICS_MONITORING.md) |
| **middleware** | [MIDDLEWARE](components/api/MIDDLEWARE.md) |
| **migrations** | [MIGRATIONS](data-layer/MIGRATIONS.md) |
| **monitoring** | [LOGGING_MONITORING](components/core/LOGGING_MONITORING.md), [METRICS_MONITORING](features/METRICS_MONITORING.md) |
| **multi-tenant** | [MULTI_TENANCY](features/MULTI_TENANCY.md) |
| **orm** | [ORM_MODELS](data-layer/ORM_MODELS.md) |
| **permissions** | [PERMISSION_SYSTEM](components/claude_sdk/PERMISSION_SYSTEM.md), [SECURITY_POLICIES](components/security/SECURITY_POLICIES.md), [IMPLEMENTING_CUSTOM_POLICIES](guides/IMPLEMENTING_CUSTOM_POLICIES.md) |
| **postgresql** | [DATABASE_SCHEMA](data-layer/DATABASE_SCHEMA.md), [EXTERNAL_DEPENDENCIES](integration/EXTERNAL_DEPENDENCIES.md), [TECHNOLOGY_STACK](architecture/TECHNOLOGY_STACK.md) |
| **query** | [DATA_FLOW](architecture/DATA_FLOW.md), [EXECUTION_STRATEGIES](components/claude_sdk/EXECUTION_STRATEGIES.md) |
| **redis** | [REDIS_CACHING](data-layer/REDIS_CACHING.md), [EXTERNAL_DEPENDENCIES](integration/EXTERNAL_DEPENDENCIES.md) |
| **report** | [REPORT_GENERATION](components/reporting/REPORT_GENERATION.md), [REPORT_TYPES](components/reporting/REPORT_TYPES.md) |
| **repository** | [REPOSITORIES](data-layer/REPOSITORIES.md), [LAYERED_ARCHITECTURE](architecture/LAYERED_ARCHITECTURE.md) |
| **retry** | [RETRY_RESILIENCE](components/claude_sdk/RETRY_RESILIENCE.md) |
| **security** | [AUTHENTICATION_AUTHORIZATION](components/security/AUTHENTICATION_AUTHORIZATION.md), [SECURITY_POLICIES](components/security/SECURITY_POLICIES.md) |
| **session** | [SESSION_LIFECYCLE](components/sessions/SESSION_LIFECYCLE.md), [SESSION_MODES](components/sessions/SESSION_MODES.md), [SESSION_FORKING](components/sessions/SESSION_FORKING.md), [CREATING_A_SESSION](guides/CREATING_A_SESSION.md) |
| **setup** | [SETUP_GUIDE](development/SETUP_GUIDE.md), [QUICK_START](guides/QUICK_START.md) |
| **sqlalchemy** | [ORM_MODELS](data-layer/ORM_MODELS.md), [TECHNOLOGY_STACK](architecture/TECHNOLOGY_STACK.md) |
| **storage** | [STORAGE_MANAGEMENT](components/core/STORAGE_MANAGEMENT.md), [WORKING_DIRECTORIES](components/sessions/WORKING_DIRECTORIES.md) |
| **streaming** | [WEBSOCKET_API](components/api/WEBSOCKET_API.md), [REAL_TIME_STREAMING](features/REAL_TIME_STREAMING.md), [MESSAGE_PROCESSING](components/claude_sdk/MESSAGE_PROCESSING.md) |
| **task** | [TASK_AUTOMATION](components/tasks/TASK_AUTOMATION.md), [TEMPLATE_SYSTEM](components/tasks/TEMPLATE_SYSTEM.md) |
| **template** | [TEMPLATE_SYSTEM](components/tasks/TEMPLATE_SYSTEM.md), [SESSION_TEMPLATES](features/SESSION_TEMPLATES.md) |
| **testing** | [TESTING_STRATEGY](development/TESTING_STRATEGY.md) |
| **tools** | [SDK_TOOLS](components/mcp/SDK_TOOLS.md), [TOOL_CONFIGURATION](components/mcp/TOOL_CONFIGURATION.md) |
| **user** | [USER_MANAGEMENT](features/USER_MANAGEMENT.md), [DOMAIN_MODEL](architecture/DOMAIN_MODEL.md) |
| **websocket** | [WEBSOCKET_API](components/api/WEBSOCKET_API.md), [REAL_TIME_STREAMING](features/REAL_TIME_STREAMING.md) |
| **working-directory** | [WORKING_DIRECTORIES](components/sessions/WORKING_DIRECTORIES.md), [STORAGE_MANAGEMENT](components/core/STORAGE_MANAGEMENT.md) |
| **debugging** | [DEBUGGING_GUIDE](development/DEBUGGING_GUIDE.md) |
| **troubleshooting** | [DEBUGGING_GUIDE](development/DEBUGGING_GUIDE.md) |
| **code-patterns** | [CODE_PATTERNS](development/CODE_PATTERNS.md) |
| **best-practices** | [CODE_PATTERNS](development/CODE_PATTERNS.md) |
| **pytest** | [TESTING_STRATEGY](development/TESTING_STRATEGY.md) |
| **unit-tests** | [TESTING_STRATEGY](development/TESTING_STRATEGY.md) |
| **integration-tests** | [TESTING_STRATEGY](development/TESTING_STRATEGY.md) |
| **exception-hierarchy** | [ERROR_HANDLING](development/ERROR_HANDLING.md) |
| **pdb** | [DEBUGGING_GUIDE](development/DEBUGGING_GUIDE.md) |

---

## How to Use This Index

### For AI Agents

1. **Search by keyword**: Use Ctrl+F to find keywords in the Quick Keyword Reference Table
2. **Navigate to document**: Click the link to open the relevant documentation
3. **Read related files**: Each document lists "Related Files" with source code references
4. **Follow cross-references**: Documents link to related documentation

### For Developers

1. **Start with architecture**: Understand the system before diving into specifics
2. **Use keyword search**: Find documentation quickly by topic
3. **Follow code references**: Each document includes file paths and line numbers
4. **Check guides for tutorials**: Step-by-step instructions for common tasks

### Search Strategy

**Example**: Need to add a custom hook?
1. Search for "hooks" → Find [HOOK_SYSTEM](components/claude_sdk/HOOK_SYSTEM.md)
2. Read hook architecture and types
3. Follow to [IMPLEMENTING_CUSTOM_HOOKS](guides/IMPLEMENTING_CUSTOM_HOOKS.md)
4. Check source code: `app/claude_sdk/hooks/`

---

## Documentation Standards

All documentation follows these standards:

1. **File References**: Include actual file paths with line numbers (e.g., `app/services/session_service.py:30-50`)
2. **Code Examples**: Show real code from the codebase, not generic examples
3. **Cross-References**: Link to related documentation
4. **Keywords**: Each document ends with searchable keywords
5. **Structure**: Purpose → Architecture → Implementation → Common Tasks → Keywords

---

## Contributing to Documentation

When adding or modifying documentation:

1. **Update this INDEX.md**: Add new documents to the appropriate section
2. **Add keywords**: Update the Quick Keyword Reference Table
3. **Follow standards**: Use the same structure as existing docs
4. **Include code references**: Always reference actual source files
5. **Cross-link**: Link to related documentation

---

## Document Status

| Section | Status | Files |
|---------|--------|-------|
| Architecture | ✅ Complete | 5/5 |
| Components/Core | ⏳ Pending | 0/3 |
| Components/API | 🔄 In Progress | 1/4 (REST_API_ENDPOINTS) |
| Components/Sessions | ✅ Complete | 4/4 |
| Components/Claude SDK | ✅ Complete | 7/7 |
| Components/MCP | ⏳ Pending | 0/4 |
| Components/Tasks | ⏳ Pending | 0/3 |
| Components/Reporting | ⏳ Pending | 0/2 |
| Components/Security | ⏳ Pending | 0/3 |
| Features | ⏳ Pending | 0/5 |
| Data Layer | ✅ Complete | 5/5 |
| Integration | ⏳ Pending | 0/3 |
| Development | ✅ Complete | 5/5 |
| Deployment | ⏳ Pending | 0/3 |
| Guides | ⏳ Pending | 0/6 |

**Summary**: 31 of 57 planned documents completed (54%)

**✅ Completed Sections** (100%):
- Architecture (5 docs) - System design, layers, domain model, data flow, tech stack
- Claude SDK Integration (7 docs) - SDK wrapper, executors, permissions, hooks, retry, messages
- Sessions (4 docs) - Lifecycle, modes, forking, working directories
- Data Layer (5 docs) - Schema, ORM models, repositories, migrations, caching
- Development (5 docs) - Setup guide, code patterns, testing strategy, error handling, debugging

**🔄 In Progress** (25%):
- Components/API (1/4) - REST endpoints documented

**⏳ Remaining Priority**:
1. API components (WEBSOCKET_API, AUTHENTICATION, MIDDLEWARE) - 3 files
2. Security components (AUTHENTICATION_AUTHORIZATION, AUDIT_LOGGING, SECURITY_POLICIES) - 3 files
3. Core components (CONFIGURATION, LOGGING_MONITORING, STORAGE_MANAGEMENT) - 3 files
4. MCP components (MCP_OVERVIEW, MCP_SERVER_MANAGEMENT, SDK_TOOLS, TOOL_CONFIGURATION) - 4 files

---

## Quick Navigation

- **🏠 [Architecture Overview](architecture/OVERVIEW.md)** - Start here for system understanding
- **🚀 [Quick Start Guide](guides/QUICK_START.md)** - Get running quickly
- **📡 [REST API Endpoints](components/api/REST_API_ENDPOINTS.md)** - API reference
- **💾 [Database Schema](data-layer/DATABASE_SCHEMA.md)** - Complete schema documentation
- **🔧 [Setup Guide](development/SETUP_GUIDE.md)** - Development environment setup
