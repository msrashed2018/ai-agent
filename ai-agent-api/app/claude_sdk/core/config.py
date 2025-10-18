"""Core configuration and metrics for Claude SDK client."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pathlib import Path


class ClientState(str, Enum):
    """Client connection state enumeration."""
    CREATED = "created"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


@dataclass
class ClientConfig:
    """Configuration for enhanced Claude client.

    This configuration is built from domain Session entity and contains
    all necessary settings for establishing a Claude SDK session.
    """
    session_id: UUID
    model: str = "claude-sonnet-4-5"
    permission_mode: str = "default"
    max_turns: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout_seconds: int = 120
    include_partial_messages: bool = False
    working_directory: Path = field(default_factory=lambda: Path.cwd())
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: Optional[List[str]] = None
    hooks: Optional[Dict[str, List[Any]]] = None  # HookMatcher
    can_use_tool: Optional[Callable] = None


@dataclass
class ClientMetrics:
    """Session metrics tracking for performance and cost monitoring.

    These metrics are collected during session execution and persisted
    to the database for reporting and analytics.
    """
    session_id: UUID
    total_messages: int = 0
    total_tool_calls: int = 0
    total_errors: int = 0
    total_retries: int = 0
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal("0.0"))
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_creation_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_duration_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def increment_messages(self) -> None:
        """Increment message count."""
        self.total_messages += 1

    def increment_tool_calls(self) -> None:
        """Increment tool call count."""
        self.total_tool_calls += 1

    def increment_errors(self) -> None:
        """Increment error count."""
        self.total_errors += 1

    def increment_retries(self) -> None:
        """Increment retry count."""
        self.total_retries += 1

    def add_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Add token usage from API response."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cache_creation_tokens += cache_creation_tokens
        self.total_cache_read_tokens += cache_read_tokens

    def add_cost(self, cost_usd: Decimal) -> None:
        """Add to total cost."""
        self.total_cost_usd += cost_usd

    def mark_started(self) -> None:
        """Mark session start time."""
        if not self.started_at:
            self.started_at = datetime.utcnow()

    def mark_completed(self) -> None:
        """Mark session completion and calculate duration."""
        self.completed_at = datetime.utcnow()
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.total_duration_ms = int(duration * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for persistence."""
        return {
            "session_id": str(self.session_id),
            "total_messages": self.total_messages,
            "total_tool_calls": self.total_tool_calls,
            "total_errors": self.total_errors,
            "total_retries": self.total_retries,
            "total_cost_usd": float(self.total_cost_usd),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_creation_tokens": self.total_cache_creation_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_duration_ms": self.total_duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
