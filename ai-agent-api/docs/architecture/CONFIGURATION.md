# Configuration Management

The AI-Agent-API service uses **Pydantic Settings** for comprehensive configuration management with environment variable support and validation.

## Configuration Architecture

### Settings Class

**File**: `app/core/config.py`

The service uses a centralized `Settings` class with over 80 configuration parameters organized into logical groups:

```python
class Settings(BaseSettings):
    """Comprehensive application settings with environment variable support"""
    
    # Service Identity
    service_name: str = "ai-agent-api"
    version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Environment-based Configuration

**Configuration Sources** (in order of priority):

1. **Environment Variables**: Runtime environment variables
2. **`.env` File**: Local development configuration file  
3. **Default Values**: Fallback defaults defined in Settings class
4. **Docker Secrets**: Mounted secret files (production)

## Core Configuration Groups

### Database Configuration

```python
# Database Connection
database_url: str
database_pool_size: int = 20
database_max_overflow: int = 30
database_pool_timeout: int = 30
database_pool_recycle: int = 3600
database_echo: bool = False  # SQL query logging

# Test Database (SQLite for testing)
test_database_url: str = "sqlite+aiosqlite:///./test.db"
```

**Example Environment Variables**:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ai_agent_api
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

### Redis Configuration

```python
# Redis Connection
redis_url: str = "redis://localhost:6379/0"
redis_password: Optional[str] = None
redis_ssl: bool = False
redis_ssl_cert_reqs: Optional[str] = None

# Redis Pool Settings
redis_max_connections: int = 100
redis_retry_on_timeout: bool = True
redis_socket_connect_timeout: float = 5.0
redis_socket_timeout: float = 5.0
```

### Celery Configuration

```python
# Celery Broker and Backend
celery_broker_url: str = "redis://localhost:6379/1"
celery_result_backend: str = "redis://localhost:6379/2"

# Celery Worker Settings
celery_task_always_eager: bool = False  # Sync execution for testing
celery_task_routes: Dict[str, str] = {}
celery_worker_concurrency: int = 4
```

### Security Configuration

```python
# JWT Authentication
secret_key: str  # Required for JWT signing
jwt_algorithm: str = "HS256"
jwt_expire_minutes: int = 60 * 24  # 24 hours
jwt_refresh_expire_minutes: int = 60 * 24 * 7  # 7 days

# Password Hashing
password_hash_schemes: List[str] = ["bcrypt"]
password_hash_deprecated: List[str] = ["auto"]

# CORS Settings
cors_origins: List[str] = ["http://localhost:3000"]
cors_allow_credentials: bool = True
cors_allow_methods: List[str] = ["*"]
cors_allow_headers: List[str] = ["*"]
```

**Security Environment Variables**:
```bash
SECRET_KEY=your-secret-key-here-must-be-secure
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=["http://localhost:3000","https://app.example.com"]
```

### Claude Integration Configuration

```python
# Claude API
anthropic_api_key: str  # Required
claude_model: str = "claude-3-5-sonnet-20241022"
claude_max_tokens: int = 4000
claude_temperature: float = 0.7
claude_timeout_seconds: float = 60.0

# Claude SDK Options
claude_sdk_options: Dict[str, Any] = {}

# API Rate Limiting
claude_requests_per_minute: int = 60
claude_tokens_per_minute: int = 100000
```

### Storage Configuration

```python
# File Storage
storage_type: str = "local"  # Options: local, s3
storage_base_path: str = "/data"

# Local Storage Settings
local_storage_path: str = "/data"

# S3 Storage Settings (when storage_type="s3")
s3_bucket_name: Optional[str] = None
s3_region: Optional[str] = None
s3_access_key_id: Optional[str] = None
s3_secret_access_key: Optional[str] = None
s3_endpoint_url: Optional[str] = None

# Storage Limits
max_file_size_mb: int = 100
max_total_storage_gb: int = 10
storage_cleanup_days: int = 30
```

### Session Management Configuration

```python
# Session Limits
default_max_concurrent_sessions: int = 5
default_max_api_calls_per_hour: int = 1000
default_max_storage_mb: int = 10240

# Session Timeouts
session_timeout_minutes: int = 60
session_cleanup_interval_minutes: int = 15
session_archive_days: int = 90

# WebSocket Settings
websocket_heartbeat_interval: int = 30
websocket_max_connections_per_user: int = 5
```

### Rate Limiting Configuration

```python
# API Rate Limits
rate_limit_requests_per_minute: int = 60
rate_limit_burst_size: int = 100
rate_limit_window_seconds: int = 60

# Per-User Rate Limits
rate_limit_per_user: bool = True
rate_limit_exempt_roles: List[str] = ["admin"]

# Rate Limiting Backend
rate_limit_backend: str = "memory"  # Options: memory, redis
rate_limit_redis_url: Optional[str] = None
```

### Monitoring and Observability Configuration

```python
# Prometheus Metrics
enable_metrics: bool = True
metrics_path: str = "/metrics"

# Sentry Error Tracking
sentry_dsn: Optional[str] = None
sentry_environment: str = "development"
sentry_traces_sample_rate: float = 0.1

# Logging Configuration
log_level: str = "INFO"
log_format: str = "json"  # Options: json, text
log_file: Optional[str] = None
log_max_size_mb: int = 100
log_backup_count: int = 5
```

### Email Configuration

```python
# SMTP Settings
smtp_server: Optional[str] = None
smtp_port: int = 587
smtp_username: Optional[str] = None
smtp_password: Optional[str] = None
smtp_tls: bool = True
smtp_ssl: bool = False

# Email Templates
email_from_address: str = "noreply@example.com"
email_from_name: str = "AI Agent API"
```

### Slack Integration Configuration

```python
# Slack Bot Settings
slack_bot_token: Optional[str] = None
slack_signing_secret: Optional[str] = None

# Slack Notifications
slack_default_channel: str = "#alerts"
slack_error_notifications: bool = True
slack_webhook_url: Optional[str] = None
```

### Feature Flags Configuration

```python
# Feature Toggles
enable_task_scheduling: bool = True
enable_report_generation: bool = True
enable_mcp_servers: bool = True
enable_websocket_streaming: bool = True
enable_audit_logging: bool = True

# Experimental Features
enable_experimental_features: bool = False
experimental_claude_caching: bool = False
experimental_tool_suggestions: bool = False
```

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://dev:dev@localhost:5432/ai_agent_api_dev
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-dev-key
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
ENABLE_METRICS=false
CELERY_TASK_ALWAYS_EAGER=true
```

### Production Environment

```bash
# .env.production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
DATABASE_URL=postgresql+asyncpg://prod_user:secure_pass@db:5432/ai_agent_api
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
SECRET_KEY=production-secret-key-very-secure
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
ENABLE_METRICS=true
STORAGE_TYPE=s3
S3_BUCKET_NAME=ai-agent-api-storage
```

### Testing Environment

```bash
# .env.test
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./test.db
REDIS_URL=redis://localhost:6379/15
CELERY_TASK_ALWAYS_EAGER=true
ANTHROPIC_API_KEY=test-key
ENABLE_AUDIT_LOGGING=false
RATE_LIMIT_BACKEND=memory
```

## Configuration Validation

### Pydantic Validators

The Settings class includes custom validators for configuration integrity:

```python
@validator('database_url')
def validate_database_url(cls, v):
    if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite://')):
        raise ValueError('Invalid database URL scheme')
    return v

@validator('redis_url')  
def validate_redis_url(cls, v):
    if not v.startswith('redis://'):
        raise ValueError('Redis URL must start with redis://')
    return v

@validator('jwt_expire_minutes')
def validate_jwt_expire_minutes(cls, v):
    if v <= 0:
        raise ValueError('JWT expiration must be positive')
    return v
```

### Required Settings Validation

**Critical settings that must be provided**:

```python
# Required in all environments
secret_key: str                    # JWT signing key
database_url: str                  # Database connection
anthropic_api_key: str            # Claude API access

# Required in production
@validator('secret_key')
def validate_secret_key_production(cls, v):
    if not cls.debug and len(v) < 32:
        raise ValueError('Production secret key must be at least 32 characters')
    return v
```

## Docker Configuration

### Docker Environment Variables

```dockerfile
# Dockerfile environment setup
ENV DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/ai_agent_api
ENV REDIS_URL=redis://redis:6379/0
ENV SECRET_KEY=${SECRET_KEY}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  ai-agent-api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ai_agent_api
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    env_file:
      - .env.production
```

## Configuration Management Best Practices

### Security Considerations

1. **Never commit secrets**: Use environment variables or secret management
2. **Use strong secret keys**: Minimum 32 characters for production  
3. **Rotate credentials**: Regular rotation of API keys and secrets
4. **Encrypt sensitive data**: Use encrypted storage for production secrets

### Performance Optimization

1. **Connection pooling**: Optimize database and Redis connection pools
2. **Cache configuration**: Use Redis for configuration caching in large deployments
3. **Resource limits**: Set appropriate limits for memory and storage usage
4. **Monitoring**: Enable metrics and monitoring in production

### Deployment Strategies

1. **Environment separation**: Clear separation between dev/staging/production
2. **Configuration validation**: Validate all settings on application startup
3. **Graceful degradation**: Handle missing optional configurations gracefully
4. **Hot reloading**: Support configuration updates without service restart where possible

## Configuration Schema Export

The service can export its configuration schema for documentation and validation:

```bash
# Generate configuration schema
python -m app.core.config --export-schema > config-schema.json

# Validate configuration
python -m app.core.config --validate-config .env.production
```