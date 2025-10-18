"""Metrics hook for tracking tool execution statistics."""
import logging
import time
from typing import Dict, Any, Optional

from app.claude_sdk.hooks.base_hook import BaseHook, HookType

logger = logging.getLogger(__name__)


class MetricsHook(BaseHook):
    """Metrics hook for collecting tool usage statistics.

    Tracks tool execution duration, frequency, and success rates.
    Executes after tool completion (PostToolUse) to capture actual results.
    """

    def __init__(self):
        """Initialize metrics hook."""
        self.tool_execution_count: Dict[str, int] = {}
        self.tool_error_count: Dict[str, int] = {}

    @property
    def hook_type(self) -> HookType:
        """Return PostToolUse to measure completed executions."""
        return HookType.POST_TOOL_USE

    @property
    def priority(self) -> int:
        """Normal priority (100)."""
        return 100

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Collect metrics from tool execution.

        Args:
            input_data: Tool execution data including results
            tool_use_id: Tool use ID
            context: Hook context

        Returns:
            {"continue_": True} with metrics in hookSpecificOutput
        """
        try:
            tool_name = input_data.get("name") or input_data.get("tool_name", "unknown")
            is_error = input_data.get("is_error", False)

            # Track execution count
            self.tool_execution_count[tool_name] = (
                self.tool_execution_count.get(tool_name, 0) + 1
            )

            # Track error count
            if is_error:
                self.tool_error_count[tool_name] = (
                    self.tool_error_count.get(tool_name, 0) + 1
                )

            logger.debug(
                f"Metrics: {tool_name} executions={self.tool_execution_count[tool_name]}, "
                f"errors={self.tool_error_count.get(tool_name, 0)}",
                extra={"tool_name": tool_name, "tool_use_id": tool_use_id}
            )

            return {
                "continue_": True,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "metricsCollected": {
                        "tool_name": tool_name,
                        "execution_count": self.tool_execution_count[tool_name],
                        "error_count": self.tool_error_count.get(tool_name, 0)
                    }
                }
            }

        except Exception as e:
            logger.error(
                f"MetricsHook failed: {type(e).__name__} - {str(e)}",
                exc_info=True
            )
            return {"continue_": True}

    def get_statistics(self) -> Dict[str, Any]:
        """Get collected statistics.

        Returns:
            Dictionary with execution and error counts per tool
        """
        return {
            "tool_executions": self.tool_execution_count.copy(),
            "tool_errors": self.tool_error_count.copy()
        }

    def reset_statistics(self) -> None:
        """Reset all collected statistics."""
        self.tool_execution_count.clear()
        self.tool_error_count.clear()
