"""Policy engine for evaluating permission policies."""
import logging
from typing import List, Union

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.base_policy import BasePolicy

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Engine for evaluating permission policies in priority order.

    The PolicyEngine maintains a list of registered policies and evaluates
    them in priority order (lowest number first). The first policy that
    denies access stops evaluation and returns the denial.

    If no policies deny, access is allowed.
    """

    def __init__(self):
        """Initialize policy engine with empty policy list."""
        self._policies: List[BasePolicy] = []

    def register_policy(self, policy: BasePolicy) -> None:
        """Register a permission policy.

        Args:
            policy: Policy to register
        """
        self._policies.append(policy)
        # Sort policies by priority (lower number = higher priority)
        self._policies.sort(key=lambda p: p.priority)

        logger.info(
            f"Registered policy: {policy.policy_name} "
            f"(priority={policy.priority})"
        )

    def get_policies(self, tool_name: str) -> List[BasePolicy]:
        """Get policies that apply to a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of applicable policies in priority order
        """
        return [
            policy for policy in self._policies
            if policy.applies_to_tool(tool_name)
        ]

    async def evaluate(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Evaluate all applicable policies for a tool.

        Policies are evaluated in priority order. The first policy that
        denies access immediately returns the denial. If no policies deny,
        access is allowed.

        Args:
            tool_name: Name of the tool
            input_data: Tool input parameters
            context: SDK permission context

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        applicable_policies = self.get_policies(tool_name)

        if not applicable_policies:
            # No policies apply - allow by default
            logger.debug(f"No policies for {tool_name} - allowing by default")
            return PermissionResultAllow()

        # Evaluate each policy
        for policy in applicable_policies:
            try:
                result = await policy.evaluate(tool_name, input_data, context)

                # If denied, stop evaluation and return denial
                if isinstance(result, PermissionResultDeny):
                    logger.warning(
                        f"Policy {policy.policy_name} denied {tool_name}: {result.message}"
                    )
                    return result

            except Exception as e:
                logger.error(
                    f"Policy {policy.policy_name} evaluation failed: "
                    f"{type(e).__name__} - {str(e)}",
                    exc_info=True
                )
                # Continue with other policies on error
                continue

        # All policies allowed (or no denials) - allow access
        logger.debug(
            f"All {len(applicable_policies)} policies allowed {tool_name}"
        )
        return PermissionResultAllow()

    def clear_policies(self) -> None:
        """Clear all registered policies."""
        self._policies.clear()
        logger.info("All policies cleared")

    def get_policy_count(self) -> int:
        """Get number of registered policies."""
        return len(self._policies)
