"""Base policy interface for permission system."""
from abc import ABC, abstractmethod
from typing import Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext


class BasePolicy(ABC):
    """Abstract base class for permission policies.

    All policies must implement the evaluate method which receives:
    - tool_name: Name of the tool being invoked
    - input_data: Tool input parameters
    - context: SDK ToolPermissionContext

    Policies must return either:
    - PermissionResultAllow() to allow execution
    - PermissionResultDeny(message="...", interrupt=False) to deny

    Example from POC 03_custom_permissions.py:
        async def permission_handler(tool_name, input_data, context):
            if should_allow:
                return PermissionResultAllow()
            else:
                return PermissionResultDeny(
                    message="Access denied: reason",
                    interrupt=False
                )
    """

    @abstractmethod
    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate permission for tool execution.

        Args:
            tool_name: Name of the tool being invoked
            input_data: Tool input parameters
            context: SDK permission context

        Returns:
            PermissionResultAllow or PermissionResultDeny

        Example:
            # Allow execution
            return PermissionResultAllow()

            # Deny execution
            return PermissionResultDeny(
                message="File access denied: path not in allowed list",
                interrupt=False  # Don't interrupt entire session
            )
        """
        pass

    @property
    def priority(self) -> int:
        """Return policy execution priority (lower number = higher priority).

        Default priority is 100. Override to change evaluation order.
        Higher priority policies are evaluated first.
        """
        return 100

    @property
    @abstractmethod
    def policy_name(self) -> str:
        """Return unique name for this policy."""
        pass

    def applies_to_tool(self, tool_name: str) -> bool:
        """Check if this policy applies to the given tool.

        Override this method to limit policy scope to specific tools.

        Args:
            tool_name: Name of the tool

        Returns:
            True if policy should evaluate this tool

        Example:
            def applies_to_tool(self, tool_name):
                return tool_name in ["read_file", "write_file", "Read", "Write"]
        """
        # By default, policies apply to all tools
        return True
