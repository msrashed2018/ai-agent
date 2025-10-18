"""Hook execution context."""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from uuid import UUID


@dataclass
class HookContext:
    """Context object passed to hooks during execution.

    Contains session and execution metadata to help hooks make informed decisions.
    """
    session_id: UUID
    tool_name: Optional[str] = None
    user_id: Optional[UUID] = None
    execution_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "session_id": str(self.session_id),
            "tool_name": self.tool_name,
            "user_id": str(self.user_id) if self.user_id else None,
            "execution_metadata": self.execution_metadata or {}
        }
