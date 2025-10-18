"""Permission decision domain entity."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class PermissionResult(str, Enum):
    """Permission decision result enumeration."""
    ALLOWED = "allowed"
    DENIED = "denied"
    BYPASSED = "bypassed"


@dataclass(frozen=True)
class PermissionDecision:
    """Immutable permission decision entity.

    Represents a single permission check decision with full context
    and decision reasoning.
    """
    id: UUID
    session_id: UUID
    tool_call_id: Optional[UUID]
    tool_use_id: str
    tool_name: str
    input_data: Dict[str, Any]
    context_data: Dict[str, Any]
    decision: PermissionResult
    reason: str
    policy_applied: Optional[str]
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate the permission decision data."""
        if not self.tool_use_id.strip():
            raise ValueError("Tool use ID cannot be empty")
        if not self.tool_name.strip():
            raise ValueError("Tool name cannot be empty")
        if not self.reason.strip():
            raise ValueError("Reason cannot be empty")
        if self.policy_applied is not None and not self.policy_applied.strip():
            raise ValueError("Policy applied cannot be empty string")

    def is_allowed(self) -> bool:
        """Check if permission was granted."""
        return self.decision == PermissionResult.ALLOWED

    def is_denied(self) -> bool:
        """Check if permission was denied."""
        return self.decision == PermissionResult.DENIED

    def is_bypassed(self) -> bool:
        """Check if permission was bypassed."""
        return self.decision == PermissionResult.BYPASSED

    def requires_user_approval(self) -> bool:
        """Check if this decision required user approval."""
        return "user" in self.reason.lower() or "manual" in self.reason.lower()

    def is_automated_decision(self) -> bool:
        """Check if this was an automated policy decision."""
        automated_keywords = ["automatic", "policy", "rule", "default"]
        return any(keyword in self.reason.lower() for keyword in automated_keywords)

    def has_policy(self) -> bool:
        """Check if a specific policy was applied."""
        return self.policy_applied is not None

    def is_security_related(self) -> bool:
        """Check if this is a security-related permission decision."""
        security_keywords = ["security", "unsafe", "dangerous", "restricted", "blocked"]
        return any(keyword in self.reason.lower() for keyword in security_keywords)

    def has_input_data(self) -> bool:
        """Check if permission decision has input data."""
        return bool(self.input_data)

    def has_context_data(self) -> bool:
        """Check if permission decision has context data."""
        return bool(self.context_data)
