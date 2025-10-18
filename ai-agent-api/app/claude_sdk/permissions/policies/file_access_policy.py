"""File access policy for restricting file operations."""
import logging
from pathlib import Path
from typing import List, Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class FileAccessPolicy(BasePolicy):
    """Policy for restricting file system access.

    Based on POC 03_custom_permissions.py patterns, this policy:
    - Blocks access to restricted files/directories (e.g., /etc/passwd, ~/.ssh/)
    - Only allows writes to explicitly allowed paths
    - Expands ~ in paths before checking

    Example usage:
        >>> policy = FileAccessPolicy(
        ...     restricted_read_paths=["/etc/passwd", "~/.ssh/", "~/.aws/credentials"],
        ...     allowed_write_paths=["/tmp/", "/workspace/working/"]
        ... )
    """

    def __init__(
        self,
        restricted_read_paths: List[str],
        allowed_write_paths: List[str]
    ):
        """Initialize file access policy.

        Args:
            restricted_read_paths: Paths that cannot be read
            allowed_write_paths: Paths where writes are allowed
        """
        self.restricted_read_paths = [
            Path(p).expanduser() for p in restricted_read_paths
        ]
        self.allowed_write_paths = [
            Path(p).expanduser() for p in allowed_write_paths
        ]

    @property
    def policy_name(self) -> str:
        """Return policy name."""
        return "file_access_policy"

    @property
    def priority(self) -> int:
        """High priority (10) for security policies."""
        return 10

    def applies_to_tool(self, tool_name: str) -> bool:
        """Check if policy applies to file-related tools.

        Args:
            tool_name: Tool name

        Returns:
            True for file operation tools
        """
        file_tools = ["read_file", "Read", "write_file", "Write", "Edit"]
        return tool_name in file_tools

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate file access permission.

        Args:
            tool_name: Tool name
            input_data: Tool input
            context: SDK context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Extract file path from input
        file_path = input_data.get("file_path") or input_data.get("path", "")

        if not file_path:
            # No file path specified - allow (shouldn't happen)
            return PermissionResultAllow()

        # Expand user home directory
        expanded_path = Path(file_path).expanduser()

        # Check read restrictions
        if tool_name in ["read_file", "Read"]:
            for restricted in self.restricted_read_paths:
                # Check if file is restricted or within restricted directory
                if (str(expanded_path) == str(restricted) or
                    str(expanded_path).startswith(str(restricted))):
                    logger.warning(
                        f"Blocked read of restricted file: {file_path}",
                        extra={"tool_name": tool_name, "file_path": file_path}
                    )
                    return PermissionResultDeny(
                        message=f"Reading restricted file blocked: {file_path}. "
                                f"This file contains sensitive system information.",
                        interrupt=False
                    )

        # Check write restrictions
        elif tool_name in ["write_file", "Write", "Edit"]:
            # Check if path is in allowed write directories
            is_allowed = any(
                str(expanded_path).startswith(str(allowed))
                for allowed in self.allowed_write_paths
            )

            if not is_allowed:
                logger.warning(
                    f"Blocked write to non-allowed path: {file_path}",
                    extra={"tool_name": tool_name, "file_path": file_path}
                )
                return PermissionResultDeny(
                    message=f"File write not allowed in: {file_path}. "
                            f"Allowed paths: {[str(p) for p in self.allowed_write_paths]}",
                    interrupt=False
                )

        # Passed all checks - allow
        logger.debug(f"File access allowed: {tool_name} on {file_path}")
        return PermissionResultAllow()
