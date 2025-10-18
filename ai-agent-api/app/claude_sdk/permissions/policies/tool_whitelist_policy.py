"""Tool whitelist policy for allowing only specific tools."""
import logging
from typing import List, Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class ToolWhitelistPolicy(BasePolicy):
    """Policy that only allows specific whitelisted tools.

    Example usage:
        >>> policy = ToolWhitelistPolicy(
        ...     allowed_tools=["python", "read_file", "write_file", "bash"]
        ... )
    """

    def __init__(self, allowed_tools: List[str]):
        """Initialize tool whitelist policy.

        Args:
            allowed_tools: List of allowed tool names
        """
        self.allowed_tools = set(allowed_tools)

    @property
    def policy_name(self) -> str:
        """Return policy name."""
        return "tool_whitelist_policy"

    @property
    def priority(self) -> int:
        """Medium priority (50)."""
        return 50

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate tool whitelist.

        Args:
            tool_name: Tool name
            input_data: Tool input
            context: SDK context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        if tool_name in self.allowed_tools:
            logger.debug(f"Tool allowed by whitelist: {tool_name}")
            return PermissionResultAllow()
        else:
            logger.warning(
                f"Tool not in whitelist: {tool_name}",
                extra={"tool_name": tool_name}
            )
            return PermissionResultDeny(
                message=f"Tool '{tool_name}' not in allowed list. "
                        f"Allowed tools: {sorted(self.allowed_tools)}",
                interrupt=False
            )
