"""Session domain entity."""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


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
    FORKED = "forked"


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
        logger.debug(
            f"Creating new session",
            extra={
                "session_id": str(id),
                "user_id": str(user_id),
                "mode": mode.value,
                "status": status.value,
                "name": name,
                "sdk_options_keys": list(sdk_options.keys()) if sdk_options else []
            }
        )
        
        self.id = id
        self.user_id = user_id
        self.name = name
        self.mode = mode
        self.status = status
        self.sdk_options = sdk_options
        self.working_directory_path: Optional[str] = None
        self.parent_session_id: Optional[UUID] = None
        self.is_fork = False

        # SDK Configuration (Phase 1 - New)
        self.include_partial_messages = False
        self.max_retries = 3
        self.retry_delay = 2.0
        self.timeout_seconds = 120
        self.hooks_enabled: List[str] = []
        self.permission_mode = "default"
        self.custom_policies: List[str] = []

        # Metrics
        self.total_messages = 0
        self.total_tool_calls = 0
        self.total_cost_usd = 0.0
        self.duration_ms: Optional[int] = None

        # Advanced Metrics (Phase 1 - New)
        self.total_hook_executions = 0
        self.total_permission_checks = 0
        self.total_errors = 0
        self.total_retries = 0

        # API Usage
        self.api_input_tokens = 0
        self.api_output_tokens = 0
        self.api_cache_creation_tokens = 0
        self.api_cache_read_tokens = 0

        # Result
        self.result_data: Optional[dict] = None
        self.error_message: Optional[str] = None

        # Archival and Templates (Phase 1 - New)
        self.archive_id: Optional[UUID] = None
        self.template_id: Optional[UUID] = None

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None
        
        logger.info(
            f"Session created successfully",
            extra={
                "session_id": str(self.id),
                "user_id": str(self.user_id),
                "mode": self.mode.value,
                "status": self.status.value,
                "created_at": self.created_at.isoformat()
            }
        )

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
        
        is_valid = new_status in valid_transitions.get(self.status, [])
        
        logger.debug(
            f"Session state transition validation",
            extra={
                "session_id": str(self.id),
                "current_status": self.status.value,
                "requested_status": new_status.value,
                "is_valid": is_valid,
                "valid_transitions": [status.value for status in valid_transitions.get(self.status, [])]
            }
        )
        
        return is_valid

    def transition_to(self, new_status: SessionStatus) -> None:
        """Transition to new status with validation."""
        from app.domain.exceptions import InvalidStateTransitionError

        old_status = self.status
        
        logger.debug(
            f"Attempting session status transition",
            extra={
                "session_id": str(self.id),
                "from_status": old_status.value,
                "to_status": new_status.value
            }
        )

        if not self.can_transition_to(new_status):
            logger.error(
                f"Invalid session status transition attempted",
                extra={
                    "session_id": str(self.id),
                    "from_status": old_status.value,
                    "to_status": new_status.value,
                    "error": f"Cannot transition from {self.status} to {new_status}"
                }
            )
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Handle special transition logic
        if new_status == SessionStatus.ACTIVE and not self.started_at:
            self.started_at = datetime.utcnow()
            logger.info(
                f"Session started",
                extra={
                    "session_id": str(self.id),
                    "started_at": self.started_at.isoformat()
                }
            )
        elif new_status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.TERMINATED]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
            
            logger.info(
                f"Session completed",
                extra={
                    "session_id": str(self.id),
                    "final_status": new_status.value,
                    "completed_at": self.completed_at.isoformat(),
                    "duration_ms": self.duration_ms,
                    "total_messages": self.total_messages,
                    "total_tool_calls": self.total_tool_calls,
                    "total_cost_usd": self.total_cost_usd
                }
            )
        
        logger.info(
            f"Session status transition completed",
            extra={
                "session_id": str(self.id),
                "from_status": old_status.value,
                "to_status": new_status.value,
                "updated_at": self.updated_at.isoformat()
            }
        )

    def increment_message_count(self) -> None:
        """Increment total message counter."""
        self.total_messages += 1
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Session message count incremented",
            extra={
                "session_id": str(self.id),
                "total_messages": self.total_messages
            }
        )

    def increment_tool_call_count(self) -> None:
        """Increment total tool call counter."""
        self.total_tool_calls += 1
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Session tool call count incremented",
            extra={
                "session_id": str(self.id),
                "total_tool_calls": self.total_tool_calls
            }
        )

    def add_cost(self, cost_usd: float) -> None:
        """Add to total cost."""
        previous_cost = self.total_cost_usd
        self.total_cost_usd += cost_usd
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Session cost updated",
            extra={
                "session_id": str(self.id),
                "cost_added_usd": cost_usd,
                "previous_total_usd": previous_cost,
                "new_total_usd": self.total_cost_usd
            }
        )
        
        # Log warning for high costs
        if self.total_cost_usd > 10.0:
            logger.warning(
                f"Session cost exceeds threshold",
                extra={
                    "session_id": str(self.id),
                    "total_cost_usd": self.total_cost_usd,
                    "threshold": 10.0
                }
            )

    def update_api_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Update API token usage counters."""
        previous_total = (self.api_input_tokens + self.api_output_tokens + 
                         self.api_cache_creation_tokens + self.api_cache_read_tokens)
        
        self.api_input_tokens += input_tokens
        self.api_output_tokens += output_tokens
        self.api_cache_creation_tokens += cache_creation_tokens
        self.api_cache_read_tokens += cache_read_tokens
        self.updated_at = datetime.utcnow()
        
        new_total = (self.api_input_tokens + self.api_output_tokens + 
                    self.api_cache_creation_tokens + self.api_cache_read_tokens)
        
        logger.debug(
            f"Session API tokens updated",
            extra={
                "session_id": str(self.id),
                "added_input_tokens": input_tokens,
                "added_output_tokens": output_tokens,
                "added_cache_creation_tokens": cache_creation_tokens,
                "added_cache_read_tokens": cache_read_tokens,
                "total_input_tokens": self.api_input_tokens,
                "total_output_tokens": self.api_output_tokens,
                "total_cache_creation_tokens": self.api_cache_creation_tokens,
                "total_cache_read_tokens": self.api_cache_read_tokens,
                "previous_total_tokens": previous_total,
                "new_total_tokens": new_total
            }
        )

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
        
        logger.info(
            f"Session result set",
            extra={
                "session_id": str(self.id),
                "result_keys": list(result_data.keys()) if result_data else [],
                "result_size": len(str(result_data)) if result_data else 0
            }
        )

    def set_error(self, error_message: str) -> None:
        """Set session error message."""
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
        
        logger.error(
            f"Session error set",
            extra={
                "session_id": str(self.id),
                "error_message": error_message,
                "status": self.status.value
            }
        )

    def increment_hook_execution_count(self) -> None:
        """Increment total hook execution counter."""
        self.total_hook_executions += 1
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Session hook execution count incremented",
            extra={
                "session_id": str(self.id),
                "total_hook_executions": self.total_hook_executions
            }
        )

    def increment_permission_check_count(self) -> None:
        """Increment total permission check counter."""
        self.total_permission_checks += 1
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Session permission check count incremented",
            extra={
                "session_id": str(self.id),
                "total_permission_checks": self.total_permission_checks
            }
        )

    def increment_error_count(self) -> None:
        """Increment total error counter."""
        self.total_errors += 1
        self.updated_at = datetime.utcnow()
        
        logger.warning(
            f"Session error count incremented",
            extra={
                "session_id": str(self.id),
                "total_errors": self.total_errors
            }
        )

    def increment_retry_count(self) -> None:
        """Increment total retry counter."""
        self.total_retries += 1
        self.updated_at = datetime.utcnow()
        
        logger.info(
            f"Session retry count incremented",
            extra={
                "session_id": str(self.id),
                "total_retries": self.total_retries
            }
        )
