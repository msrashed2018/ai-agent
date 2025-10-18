"""Base hook interface for Claude SDK integration."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class HookType(str, Enum):
    """Available hook types in Claude SDK.

    Based on POC script 04_hook_system.py, the Python SDK supports 6 hook types:
    - PreToolUse: Before tool execution
    - PostToolUse: After tool execution
    - UserPromptSubmit: When user submits a prompt
    - Stop: Right before Claude concludes its response
    - SubagentStop: Right before a subagent concludes its response
    - PreCompact: Before conversation compaction
    """
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"


class BaseHook(ABC):
    """Abstract base class for all hooks.

    All hooks must implement the execute method which receives:
    - input_data: Dict containing tool information and parameters
    - tool_use_id: ID of the tool being used (may be None)
    - context: SDK context object

    Hooks must return a dictionary with:
    - continue_: bool (required) - Whether to continue execution
    - hookSpecificOutput: dict (optional) - Hook-specific data

    Example from POC 04_hook_system.py:
        async def pre_tool_use_hook(input_data, tool_use_id, context):
            return {"continue_": True}
    """

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Execute the hook logic.

        Args:
            input_data: Dictionary containing hook-specific input data
            tool_use_id: Tool use ID if applicable
            context: Hook execution context from SDK

        Returns:
            Dictionary with at minimum:
            - continue_: bool - Whether to continue execution
            - hookSpecificOutput: dict (optional) - Additional hook data

        Example return values:
            # Allow and continue
            {"continue_": True}

            # Block execution
            {"continue_": False, "reason": "Security policy violation"}

            # Allow with metadata
            {
                "continue_": True,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow"
                }
            }
        """
        pass

    @property
    @abstractmethod
    def hook_type(self) -> HookType:
        """Return the type of hook this implements."""
        pass

    @property
    def priority(self) -> int:
        """Return hook execution priority (lower number = higher priority).

        Default priority is 100. Override to change execution order.
        Hooks with lower priority numbers execute first.
        """
        return 100
