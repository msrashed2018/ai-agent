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
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7
    
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


# Global settings instance
settings = Settings()
