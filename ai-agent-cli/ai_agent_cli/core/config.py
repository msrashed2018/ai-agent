"""Configuration management for CLI."""

import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class CLIConfig(BaseModel):
    """CLI configuration."""

    api_url: str = Field(default="http://localhost:8000", description="API base URL")
    access_token: Optional[str] = Field(default=None, description="JWT access token")
    refresh_token: Optional[str] = Field(default=None, description="JWT refresh token")
    default_output_format: str = Field(default="table", description="Default output format")
    timeout: int = Field(default=30, description="HTTP request timeout in seconds")


class ConfigManager:
    """Manages CLI configuration and token storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager."""
        if config_dir is None:
            config_dir = Path.home() / ".ai-agent-cli"

        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self._config: Optional[CLIConfig] = None

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> CLIConfig:
        """Load configuration from file."""
        if self._config is not None:
            return self._config

        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self._config = CLIConfig(**data)
        else:
            self._config = CLIConfig()

        # Allow environment variable overrides
        if env_url := os.getenv("AI_AGENT_API_URL"):
            self._config.api_url = env_url
        if env_token := os.getenv("AI_AGENT_ACCESS_TOKEN"):
            self._config.access_token = env_token

        return self._config

    def save(self, config: Optional[CLIConfig] = None) -> None:
        """Save configuration to file."""
        if config is not None:
            self._config = config

        if self._config is None:
            return

        with open(self.config_file, "w") as f:
            json.dump(self._config.model_dump(), f, indent=2)

    def get_api_url(self) -> str:
        """Get API base URL."""
        config = self.load()
        return config.api_url.rstrip("/")

    def get_access_token(self) -> Optional[str]:
        """Get access token."""
        config = self.load()
        return config.access_token

    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token."""
        config = self.load()
        return config.refresh_token

    def set_tokens(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Set authentication tokens."""
        config = self.load()
        config.access_token = access_token
        if refresh_token:
            config.refresh_token = refresh_token
        self.save(config)

    def clear_tokens(self) -> None:
        """Clear authentication tokens."""
        config = self.load()
        config.access_token = None
        config.refresh_token = None
        self.save(config)

    def set_api_url(self, url: str) -> None:
        """Set API base URL."""
        config = self.load()
        config.api_url = url.rstrip("/")
        self.save(config)

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.get_access_token() is not None


# Global config manager instance
config_manager = ConfigManager()
