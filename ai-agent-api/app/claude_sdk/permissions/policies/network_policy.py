"""Network policy for controlling network access."""
import logging
from typing import List, Union, Optional
from urllib.parse import urlparse

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class NetworkPolicy(BasePolicy):
    """Policy for controlling network access.

    Allows or blocks network requests based on domain whitelist/blacklist.

    Example usage:
        >>> policy = NetworkPolicy(
        ...     allowed_domains=["api.example.com", "*.github.com"],
        ...     blocked_domains=["malicious.com"]
        ... )
    """

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None
    ):
        """Initialize network policy.

        Args:
            allowed_domains: List of allowed domains (None = all allowed)
            blocked_domains: List of blocked domains
        """
        self.allowed_domains = set(allowed_domains) if allowed_domains else None
        self.blocked_domains = set(blocked_domains) if blocked_domains else set()

    @property
    def policy_name(self) -> str:
        """Return policy name."""
        return "network_policy"

    @property
    def priority(self) -> int:
        """Medium priority (30)."""
        return 30

    def applies_to_tool(self, tool_name: str) -> bool:
        """Check if policy applies to network tools.

        Args:
            tool_name: Tool name

        Returns:
            True for network-related tools
        """
        # This would apply to HTTP request tools, API calls, etc.
        network_tools = ["http_request", "api_call", "fetch", "curl"]
        return tool_name in network_tools

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate network access permission.

        Args:
            tool_name: Tool name
            input_data: Tool input
            context: SDK context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Extract URL from input
        url = input_data.get("url") or input_data.get("endpoint", "")

        if not url:
            # No URL specified - allow (shouldn't happen)
            return PermissionResultAllow()

        # Parse domain from URL
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
        except Exception as e:
            logger.error(f"Failed to parse URL {url}: {e}")
            return PermissionResultDeny(
                message=f"Invalid URL format: {url}",
                interrupt=False
            )

        # Check blocked domains
        if domain in self.blocked_domains:
            logger.warning(
                f"Blocked network access to {domain}",
                extra={"tool_name": tool_name, "domain": domain}
            )
            return PermissionResultDeny(
                message=f"Network access denied: {domain} is blocked",
                interrupt=False
            )

        # Check allowed domains if whitelist is defined
        if self.allowed_domains is not None:
            if domain not in self.allowed_domains:
                logger.warning(
                    f"Domain not in whitelist: {domain}",
                    extra={"tool_name": tool_name, "domain": domain}
                )
                return PermissionResultDeny(
                    message=f"Network access denied: {domain} not in allowed list",
                    interrupt=False
                )

        # Passed all checks - allow
        logger.debug(f"Network access allowed: {domain}")
        return PermissionResultAllow()
