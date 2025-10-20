"""Application configuration using Pydantic settings."""
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Service Configuration
    project_name: str = "AI-Agent-API-Service"
    version: str = "1.0.0"
    service_name: str = "ai-agent-api-service"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: str = "logs/api.log"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Database Configuration
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis Configuration
    redis_url: str
    
    # Celery Configuration
    celery_broker_url: str
    celery_result_backend: str
    
    # Security Configuration
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 360  # 6 hours
    jwt_refresh_token_expire_days: int = 1  # 24 hours
    
    # Claude Configuration
    anthropic_api_key: str
    claude_cli_path: str = "claude"
    
    # Storage Configuration
    storage_base_path: Path = Path("/data")
    max_storage_mb: int = 10240
    max_working_dir_size_mb: int = 1024
    
    # Agent Working Directories
    agent_workdir_base: Path = Path("/tmp/ai-agent-service/sessions")
    agent_workdir_archive: Path = Path("/tmp/ai-agent-service/archives")
    reports_dir: Path = Path("/tmp/ai-agent-service/reports")
    
    # Session Configuration
    max_concurrent_sessions: int = 5
    session_timeout_hours: int = 24
    session_archive_days: int = 180
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Monitoring Configuration
    prometheus_enabled: bool = True
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@example.com"
    
    # Slack Configuration
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    
    # Feature Flags
    enable_websocket: bool = True
    enable_scheduled_tasks: bool = True
    enable_report_generation: bool = True

    # Phase 4: Claude SDK Settings
    claude_sdk_default_model: str = "claude-sonnet-4-5"
    claude_sdk_max_retries: int = 3
    claude_sdk_retry_delay: float = 2.0
    claude_sdk_timeout_seconds: int = 120
    claude_sdk_default_permission_mode: str = "default"

    # Phase 4: Storage & Archival Settings
    storage_provider: str = "filesystem"  # 'filesystem' or 's3'
    aws_s3_bucket: str = "ai-agent-archives"
    aws_s3_region: str = "us-east-1"
    aws_s3_archive_prefix: str = "archives/"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    archive_compression: str = "gzip"
    archive_auto_cleanup: bool = True
    archive_retention_days: int = 90

    # Phase 4: Session Limits
    max_concurrent_interactive_sessions: int = 10
    max_concurrent_background_sessions: int = 50
    session_idle_timeout_minutes: int = 30
    session_auto_archive_days: int = 180

    # Phase 4: Metrics & Monitoring
    enable_metrics_collection: bool = True
    metrics_snapshot_interval_seconds: int = 60
    enable_cost_tracking: bool = True
    user_monthly_budget_usd: float = 100.0
    enable_performance_monitoring: bool = True

    # Phase 4: Hooks Settings
    enable_audit_hook: bool = True
    enable_metrics_hook: bool = True
    enable_validation_hook: bool = True
    enable_notification_hook: bool = False
    hook_execution_timeout_ms: int = 5000

    # Phase 4: Permissions Settings
    enable_custom_policies: bool = True
    permission_cache_ttl_seconds: int = 300
    default_blocked_commands: List[str] = Field(
        default=["rm -rf /", "sudo rm", "format", "mkfs", "dd if="]
    )
    default_restricted_paths: List[str] = Field(
        default=["/etc/passwd", "/etc/shadow", "~/.ssh", "~/.aws/credentials"]
    )


# Global settings instance
settings = Settings()
