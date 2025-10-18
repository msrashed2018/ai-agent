"""Notification hook for sending alerts on specific events."""
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from app.claude_sdk.hooks.base_hook import BaseHook, HookType

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""
    LOG = "log"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationHook(BaseHook):
    """Notification hook for sending alerts on tool execution events.

    Can notify via different channels (log, email, webhook, etc.) when
    specific tools are used or when errors occur.
    """

    def __init__(
        self,
        hook_type_value: HookType,
        notification_channel: NotificationChannel = NotificationChannel.LOG,
        tool_filter: Optional[List[str]] = None,
        notify_on_error: bool = True
    ):
        """Initialize notification hook.

        Args:
            hook_type_value: Which hook type to use (PreToolUse or PostToolUse)
            notification_channel: Channel to send notifications to
            tool_filter: Only notify for these tools (None = all tools)
            notify_on_error: Whether to notify on errors
        """
        self._hook_type = hook_type_value
        self.notification_channel = notification_channel
        self.tool_filter = tool_filter
        self.notify_on_error = notify_on_error

    @property
    def hook_type(self) -> HookType:
        """Return configured hook type."""
        return self._hook_type

    @property
    def priority(self) -> int:
        """Low priority (200) to notify after other processing."""
        return 200

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Send notification if conditions are met.

        Args:
            input_data: Tool execution data
            tool_use_id: Tool use ID
            context: Hook context

        Returns:
            {"continue_": True} (notifications don't block execution)
        """
        try:
            tool_name = input_data.get("name") or input_data.get("tool_name")
            is_error = input_data.get("is_error", False)

            # Check if we should notify for this tool
            should_notify = False

            if self.tool_filter:
                # Only notify for specific tools
                should_notify = tool_name in self.tool_filter
            elif self.notify_on_error and is_error:
                # Notify on any error
                should_notify = True
            elif not self.notify_on_error:
                # Notify on all tools (if no filter)
                should_notify = True

            if should_notify:
                await self._send_notification(
                    tool_name=tool_name,
                    tool_use_id=tool_use_id,
                    input_data=input_data,
                    is_error=is_error
                )

            return {"continue_": True}

        except Exception as e:
            logger.error(
                f"NotificationHook error: {type(e).__name__} - {str(e)}",
                exc_info=True
            )
            return {"continue_": True}

    async def _send_notification(
        self,
        tool_name: str,
        tool_use_id: Optional[str],
        input_data: Dict[str, Any],
        is_error: bool
    ) -> None:
        """Send notification through configured channel.

        Args:
            tool_name: Name of tool
            tool_use_id: Tool use ID
            input_data: Tool execution data
            is_error: Whether this is an error notification
        """
        message = self._format_notification_message(
            tool_name, tool_use_id, input_data, is_error
        )

        if self.notification_channel == NotificationChannel.LOG:
            if is_error:
                logger.error(message)
            else:
                logger.info(message)

        elif self.notification_channel == NotificationChannel.EMAIL:
            # TODO: Implement email notifications
            logger.info(f"Email notification: {message}")

        elif self.notification_channel == NotificationChannel.WEBHOOK:
            # TODO: Implement webhook notifications
            logger.info(f"Webhook notification: {message}")

        elif self.notification_channel == NotificationChannel.SMS:
            # TODO: Implement SMS notifications
            logger.info(f"SMS notification: {message}")

    def _format_notification_message(
        self,
        tool_name: str,
        tool_use_id: Optional[str],
        input_data: Dict[str, Any],
        is_error: bool
    ) -> str:
        """Format notification message.

        Args:
            tool_name: Name of tool
            tool_use_id: Tool use ID
            input_data: Tool execution data
            is_error: Whether this is an error

        Returns:
            Formatted message string
        """
        status = "ERROR" if is_error else "SUCCESS"
        return (
            f"[{status}] Tool {tool_name} (ID: {tool_use_id}) - "
            f"{self._hook_type.value}"
        )
