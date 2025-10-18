"""Tool call value objects."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ToolCallStatus(str, Enum):
    """Tool call status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    DENIED = "denied"


class PermissionDecision(str, Enum):
    """Permission decision enumeration."""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True)
class ToolCall:
    """Immutable tool call value object."""
    id: UUID
    session_id: UUID
    tool_name: str
    tool_use_id: str
    tool_input: Dict[str, Any]
    status: ToolCallStatus
    created_at: datetime
    message_id: Optional[UUID] = None
    tool_output: Optional[Dict[str, Any]] = None
    is_error: bool = False
    error_message: Optional[str] = None
    permission_decision: Optional[PermissionDecision] = None
    permission_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    @classmethod
    def create_pending(
        cls,
        session_id: UUID,
        tool_name: str,
        tool_use_id: str,
        tool_input: Dict[str, Any],
        message_id: Optional[UUID] = None,
    ) -> "ToolCall":
        """Factory method for pending tool call."""
        return cls(
            id=uuid4(),
            session_id=session_id,
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            tool_input=tool_input,
            status=ToolCallStatus.PENDING,
            message_id=message_id,
            created_at=datetime.utcnow(),
        )

    def with_status(self, status: ToolCallStatus) -> "ToolCall":
        """Create new instance with updated status."""
        from dataclasses import replace
        return replace(self, status=status)

    def with_permission(
        self,
        decision: PermissionDecision,
        reason: Optional[str] = None,
    ) -> "ToolCall":
        """Create new instance with permission decision."""
        from dataclasses import replace
        return replace(
            self,
            permission_decision=decision,
            permission_reason=reason,
        )

    def with_output(
        self,
        output: Dict[str, Any],
        is_error: bool = False,
        error_message: Optional[str] = None,
    ) -> "ToolCall":
        """Create new instance with output."""
        from dataclasses import replace
        completed_at = datetime.utcnow()
        duration_ms = None
        if self.started_at:
            duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        return replace(
            self,
            tool_output=output,
            is_error=is_error,
            error_message=error_message,
            status=ToolCallStatus.ERROR if is_error else ToolCallStatus.SUCCESS,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

    def with_started(self) -> "ToolCall":
        """Create new instance marked as started."""
        from dataclasses import replace
        return replace(
            self,
            status=ToolCallStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

    def is_pending(self) -> bool:
        """Check if tool call is pending."""
        return self.status == ToolCallStatus.PENDING

    def is_running(self) -> bool:
        """Check if tool call is running."""
        return self.status == ToolCallStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if tool call is completed (success or error)."""
        return self.status in [ToolCallStatus.SUCCESS, ToolCallStatus.ERROR]

    def is_denied(self) -> bool:
        """Check if tool call was denied."""
        return self.status == ToolCallStatus.DENIED
