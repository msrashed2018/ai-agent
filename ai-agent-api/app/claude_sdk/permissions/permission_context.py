"""Permission context for policy evaluation."""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from uuid import UUID


@dataclass
class PermissionContext:
    """Context object for permission policy evaluation.

    Contains session and execution metadata to help policies make
    informed access control decisions.
    """
    session_id: UUID
    user_id: Optional[UUID] = None
    working_directory: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "session_id": str(self.session_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "working_directory": self.working_directory,
            "session_metadata": self.session_metadata or {}
        }
