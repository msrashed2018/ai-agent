"""Command policy for filtering dangerous bash commands."""
import logging
from typing import List, Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class CommandPolicy(BasePolicy):
    """Policy for filtering dangerous bash commands.

    Based on POC 03_custom_permissions.py patterns, blocks commands
    that contain dangerous patterns or attempt to access sensitive files.

    Example usage:
        >>> policy = CommandPolicy(
        ...     blocked_patterns=["rm -rf", "sudo rm", "format", "cat /etc/passwd"]
        ... )
    """

    def __init__(self, blocked_patterns: List[str]):
        """Initialize command policy.

        Args:
            blocked_patterns: Command patterns to block
        """
        self.blocked_patterns = blocked_patterns

    @property
    def policy_name(self) -> str:
        """Return policy name."""
        return "command_policy"

    @property
    def priority(self) -> int:
        """High priority (10) for security policies."""
        return 10

    def applies_to_tool(self, tool_name: str) -> bool:
        """Check if policy applies to command execution tools.

        Args:
            tool_name: Tool name

        Returns:
            True for bash/command tools
        """
        return tool_name in ["bash", "Bash"]

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate command execution permission.

        Args:
            tool_name: Tool name
            input_data: Tool input
            context: SDK context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Extract command from input
        command = input_data.get("command", "")

        if not command:
            # No command specified - allow (shouldn't happen)
            return PermissionResultAllow()

        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in command:
                logger.warning(
                    f"Blocked dangerous command: contains '{pattern}'",
                    extra={"tool_name": tool_name, "command": command[:100]}
                )
                return PermissionResultDeny(
                    message=f"Command blocked: contains dangerous pattern '{pattern}'",
                    interrupt=False
                )

        # Passed all checks - allow
        logger.debug(f"Command allowed: {command[:50]}...")
        return PermissionResultAllow()
