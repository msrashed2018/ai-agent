"""Tool blacklist policy for blocking specific tools."""
import logging
from typing import List, Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class ToolBlacklistPolicy(BasePolicy):
    """Policy that blocks specific blacklisted tools.

    Example usage:
        >>> policy = ToolBlacklistPolicy(
        ...     blocked_tools=["dangerous_tool", "system_command"]
        ... )
    """

    def __init__(self, blocked_tools: List[str]):
        """Initialize tool blacklist policy.

        Args:
            blocked_tools: List of blocked tool names
        """
        self.blocked_tools = set(blocked_tools)

    @property
    def policy_name(self) -> str:
        """Return policy name."""
        return "tool_blacklist_policy"

    @property
    def priority(self) -> int:
        """High priority (20) to block early."""
        return 20

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate tool blacklist.

        Args:
            tool_name: Tool name
            input_data: Tool input
            context: SDK context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        if tool_name in self.blocked_tools:
            logger.warning(
                f"Tool blocked by blacklist: {tool_name}",
                extra={"tool_name": tool_name}
            )
            return PermissionResultDeny(
                message=f"Tool '{tool_name}' is not allowed by security policy",
                interrupt=False
            )
        else:
            logger.debug(f"Tool not in blacklist: {tool_name}")
            return PermissionResultAllow()
