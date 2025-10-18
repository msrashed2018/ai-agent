"""Permission manager for orchestrating permission checks."""
import logging
from typing import Union, Callable, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.models.permission_decision import PermissionDecisionModel
from app.domain.entities.permission_decision import PermissionResult

logger = logging.getLogger(__name__)


class PermissionManager:
    """Orchestrate permission checking with policy engine and logging.

    The PermissionManager creates a permission callback function that can
    be passed to ClaudeAgentOptions. It:
    - Evaluates policies via the PolicyEngine
    - Logs all permission decisions to the database
    - Provides optional caching for performance
    - Serializes SDK context for storage

    Example usage from POC 03_custom_permissions.py:
        >>> manager = PermissionManager(db, policy_engine, permission_repo)
        >>> # Register policies
        >>> policy_engine.register_policy(FileAccessPolicy(...))
        >>> # Create callback
        >>> callback = manager.create_callback(session_id, user_id)
        >>> # Use in SDK options
        >>> options = ClaudeAgentOptions(can_use_tool=callback, ...)
    """

    def __init__(
        self,
        db: AsyncSession,
        policy_engine: PolicyEngine,
        permission_decision_repo: PermissionDecisionRepository,
        enable_cache: bool = True
    ):
        """Initialize permission manager.

        Args:
            db: Database session
            policy_engine: Engine for evaluating policies
            permission_decision_repo: Repository for logging decisions
            enable_cache: Whether to cache permission decisions
        """
        self.db = db
        self.policy_engine = policy_engine
        self.permission_decision_repo = permission_decision_repo
        self.enable_cache = enable_cache
        self._decision_cache: Dict[str, Union[PermissionResultAllow, PermissionResultDeny]] = {}

        logger.info("PermissionManager initialized")

    def create_callback(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        working_directory: Optional[str] = None
    ) -> Callable:
        """Create permission callback function for SDK.

        Based on POC 03_custom_permissions.py, the callback receives:
        - tool_name: str
        - input_data: dict
        - context: ToolPermissionContext

        And must return: PermissionResultAllow or PermissionResultDeny

        Args:
            session_id: Session ID for logging
            user_id: User ID for logging
            working_directory: Working directory path

        Returns:
            Async permission callback function
        """
        async def permission_callback(
            tool_name: str,
            input_data: dict,
            context: ToolPermissionContext
        ) -> Union[PermissionResultAllow, PermissionResultDeny]:
            """Permission callback for SDK integration.

            Args:
                tool_name: Name of tool being invoked
                input_data: Tool input parameters
                context: SDK permission context

            Returns:
                PermissionResultAllow or PermissionResultDeny
            """
            return await self.can_use_tool(
                tool_name=tool_name,
                input_data=input_data,
                context=context,
                session_id=session_id,
                user_id=user_id
            )

        return permission_callback

    async def can_use_tool(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext,
        session_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Main permission check method.

        Args:
            tool_name: Name of tool
            input_data: Tool input parameters
            context: SDK permission context
            session_id: Session ID
            user_id: User ID

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """
        # Check cache if enabled
        if self.enable_cache:
            cache_key = self._make_cache_key(tool_name, input_data)
            if cache_key in self._decision_cache:
                cached_result = self._decision_cache[cache_key]
                logger.debug(f"Permission cache hit for {tool_name}")
                return cached_result

        # Evaluate policies
        result = await self.policy_engine.evaluate(tool_name, input_data, context)

        # Determine decision type
        if isinstance(result, PermissionResultAllow):
            decision = PermissionResult.ALLOWED
            reason = "policy_allowed"
        else:
            decision = PermissionResult.DENIED
            reason = result.message or "policy_denied"

        # Log decision to database
        await self._log_decision(
            session_id=session_id,
            tool_name=tool_name,
            input_data=input_data,
            context=context,
            decision=decision,
            reason=reason,
            user_id=user_id
        )

        # Cache decision if enabled
        if self.enable_cache:
            cache_key = self._make_cache_key(tool_name, input_data)
            self._decision_cache[cache_key] = result

        return result

    async def _log_decision(
        self,
        session_id: UUID,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext,
        decision: PermissionResult,
        reason: str,
        user_id: Optional[UUID] = None
    ) -> None:
        """Log permission decision to database.

        Args:
            session_id: Session ID
            tool_name: Tool name
            input_data: Tool input
            context: SDK context
            decision: Allow/Deny decision
            reason: Decision reason
            user_id: User ID
        """
        try:
            # Serialize context
            context_data = self._serialize_context(context)

            # Create permission decision record
            permission_decision = PermissionDecisionModel(
                session_id=session_id,
                tool_call_id=None,  # Will be linked later if needed
                tool_use_id="",  # SDK doesn't provide this in permission callback
                tool_name=tool_name,
                input_data=input_data,
                context_data=context_data,
                decision=decision.value,
                reason=reason,
                policy_applied=None  # Could be enhanced to track which policy matched
            )

            await self.permission_decision_repo.create(permission_decision)

            logger.info(
                f"Permission decision logged: {tool_name} = {decision.value}",
                extra={
                    "session_id": str(session_id),
                    "tool_name": tool_name,
                    "decision": decision.value
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to log permission decision: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )
            # Don't fail permission check if logging fails

    def _make_cache_key(self, tool_name: str, input_data: dict) -> str:
        """Create cache key from tool name and input.

        Args:
            tool_name: Tool name
            input_data: Tool input

        Returns:
            Cache key string
        """
        import hashlib
        import json

        # Create stable representation of input data
        input_str = json.dumps(input_data, sort_keys=True, default=str)
        input_hash = hashlib.md5(input_str.encode()).hexdigest()

        return f"{tool_name}:{input_hash}"

    def _serialize_context(self, context: ToolPermissionContext) -> Dict[str, Any]:
        """Serialize SDK context to dictionary.

        Args:
            context: SDK permission context

        Returns:
            Serialized context dictionary
        """
        try:
            return {
                "type": type(context).__name__,
                "signal": str(getattr(context, "signal", None)),
                "suggestions_count": len(getattr(context, "suggestions", [])),
            }
        except Exception:
            return {"type": type(context).__name__ if context else "None"}

    def clear_cache(self) -> None:
        """Clear permission decision cache."""
        self._decision_cache.clear()
        logger.info("Permission cache cleared")
