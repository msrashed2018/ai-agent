"""Session domain entity."""
from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID


class SessionStatus(str, Enum):
    """Session status enumeration."""
    CREATED = "created"
    CONNECTING = "connecting"
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING = "waiting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


class SessionMode(str, Enum):
    """Session mode enumeration."""
    INTERACTIVE = "interactive"
    NON_INTERACTIVE = "non_interactive"


class Session:
    """Session aggregate root."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        mode: SessionMode,
        sdk_options: dict,
        name: Optional[str] = None,
        status: SessionStatus = SessionStatus.CREATED,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.mode = mode
        self.status = status
        self.sdk_options = sdk_options
        self.working_directory_path: Optional[str] = None
        self.parent_session_id: Optional[UUID] = None
        self.is_fork = False

        # Metrics
        self.total_messages = 0
        self.total_tool_calls = 0
        self.total_cost_usd = 0.0
        self.duration_ms: Optional[int] = None

        # API Usage
        self.api_input_tokens = 0
        self.api_output_tokens = 0
        self.api_cache_creation_tokens = 0
        self.api_cache_read_tokens = 0

        # Result
        self.result_data: Optional[dict] = None
        self.error_message: Optional[str] = None

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None

    def can_transition_to(self, new_status: SessionStatus) -> bool:
        """Check if transition to new status is valid."""
        valid_transitions = {
            SessionStatus.CREATED: [SessionStatus.CONNECTING, SessionStatus.TERMINATED],
            SessionStatus.CONNECTING: [SessionStatus.ACTIVE, SessionStatus.FAILED],
            SessionStatus.ACTIVE: [
                SessionStatus.WAITING,
                SessionStatus.PROCESSING,
                SessionStatus.PAUSED,
                SessionStatus.COMPLETED,
                SessionStatus.FAILED,
                SessionStatus.TERMINATED,
            ],
            SessionStatus.WAITING: [SessionStatus.ACTIVE, SessionStatus.PROCESSING, SessionStatus.TERMINATED],
            SessionStatus.PROCESSING: [SessionStatus.ACTIVE, SessionStatus.COMPLETED, SessionStatus.FAILED],
            SessionStatus.PAUSED: [SessionStatus.ACTIVE, SessionStatus.TERMINATED],
            SessionStatus.COMPLETED: [SessionStatus.ARCHIVED],
            SessionStatus.FAILED: [SessionStatus.ARCHIVED],
            SessionStatus.TERMINATED: [SessionStatus.ARCHIVED],
            SessionStatus.ARCHIVED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: SessionStatus) -> None:
        """Transition to new status with validation."""
        from app.domain.exceptions import InvalidStateTransitionError

        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

        if new_status == SessionStatus.ACTIVE and not self.started_at:
            self.started_at = datetime.utcnow()
        elif new_status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.TERMINATED]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def increment_message_count(self) -> None:
        """Increment total message counter."""
        self.total_messages += 1
        self.updated_at = datetime.utcnow()

    def increment_tool_call_count(self) -> None:
        """Increment total tool call counter."""
        self.total_tool_calls += 1
        self.updated_at = datetime.utcnow()

    def add_cost(self, cost_usd: float) -> None:
        """Add to total cost."""
        self.total_cost_usd += cost_usd
        self.updated_at = datetime.utcnow()

    def update_api_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Update API token usage counters."""
        self.api_input_tokens += input_tokens
        self.api_output_tokens += output_tokens
        self.api_cache_creation_tokens += cache_creation_tokens
        self.api_cache_read_tokens += cache_read_tokens
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if session is in active state."""
        return self.status in [
            SessionStatus.ACTIVE,
            SessionStatus.WAITING,
            SessionStatus.PROCESSING,
        ]

    def is_terminal(self) -> bool:
        """Check if session is in terminal state."""
        return self.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.TERMINATED,
            SessionStatus.ARCHIVED,
        ]

    def set_result(self, result_data: dict) -> None:
        """Set session result data."""
        self.result_data = result_data
        self.updated_at = datetime.utcnow()

    def set_error(self, error_message: str) -> None:
        """Set session error message."""
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
