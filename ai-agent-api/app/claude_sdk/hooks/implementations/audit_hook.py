"""Audit hook for logging all tool executions."""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditHook(BaseHook):
    """Audit hook for comprehensive tool execution logging.

    Logs all tool executions to the audit trail for compliance and debugging.
    This hook executes before tool execution (PreToolUse) to capture all
    invocation attempts, including those that may be blocked by permissions.
    """

    def __init__(self, audit_service: AuditService):
        """Initialize audit hook.

        Args:
            audit_service: Service for logging audit events
        """
        self.audit_service = audit_service

    @property
    def hook_type(self) -> HookType:
        """Return PreToolUse as this hook audits before execution."""
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        """High priority (10) to log before other hooks."""
        return 10

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Log tool execution attempt to audit trail.

        Args:
            input_data: Tool execution parameters
            tool_use_id: Tool use ID
            context: Hook context

        Returns:
            {"continue_": True} to allow execution
        """
        try:
            tool_name = input_data.get("name") or input_data.get("tool_name", "unknown")
            tool_input = input_data.get("input", {})

            # Extract session_id from context if available
            session_id = getattr(context, "session_id", None)

            # Log to audit trail
            await self.audit_service.log_event(
                event_type="tool_execution_attempt",
                event_category="tool",
                resource_type="tool",
                resource_id=tool_name,
                session_id=session_id,
                details={
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "tool_input": tool_input,
                    "hook": "AuditHook"
                }
            )

            logger.info(
                f"Audit: Tool execution attempt logged - {tool_name}",
                extra={"tool_name": tool_name, "tool_use_id": tool_use_id}
            )

        except Exception as e:
            logger.error(
                f"AuditHook failed to log: {type(e).__name__} - {str(e)}",
                exc_info=True
            )
            # Don't block execution if audit logging fails

        return {"continue_": True}
