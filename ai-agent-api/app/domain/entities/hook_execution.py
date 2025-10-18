"""Hook execution domain entity."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class HookExecution:
    """Immutable hook execution entity.

    Represents a single hook execution instance with input/output data
    and execution metadata.
    """
    id: UUID
    session_id: UUID
    tool_call_id: Optional[UUID]
    hook_name: str
    tool_use_id: str
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    context_data: Dict[str, Any]
    execution_time_ms: int
    created_at: datetime
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the hook execution data."""
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative")
        if not self.hook_name.strip():
            raise ValueError("Hook name cannot be empty")
        if not self.tool_use_id.strip():
            raise ValueError("Tool use ID cannot be empty")
        if not self.tool_name.strip():
            raise ValueError("Tool name cannot be empty")

    def is_successful(self) -> bool:
        """Check if hook execution was successful."""
        return self.error_message is None

    def is_failed(self) -> bool:
        """Check if hook execution failed."""
        return self.error_message is not None

    def get_hook_type(self) -> str:
        """Extract hook type from hook name.

        Returns the hook type (pre, post, etc.) from the hook name.
        
        Examples:
            - 'pre_tool_use' -> 'pre'
            - 'post_tool_use' -> 'post'
            - 'custom_hook' -> 'custom'
        """
        return self.hook_name.lower().split('_')[0] if '_' in self.hook_name else self.hook_name.lower()

    def get_execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
        return self.execution_time_ms / 1000.0

    def is_slow_execution(self, threshold_ms: int = 1000) -> bool:
        """Check if execution time exceeds threshold (default 1 second)."""
        return self.execution_time_ms > threshold_ms

    def has_input_data(self) -> bool:
        """Check if hook execution has input data."""
        return bool(self.input_data)

    def has_output_data(self) -> bool:
        """Check if hook execution has output data."""
        return bool(self.output_data)

    def has_context_data(self) -> bool:
        """Check if hook execution has context data."""
        return bool(self.context_data)
