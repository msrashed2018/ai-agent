"""Hook Handlers for Claude SDK integration.

Provides hook callback functions for the official Claude SDK.
Hooks intercept SDK events for audit logging, tool tracking, and validation.

Based on Document 7: Hook & Permission System
"""

import logging
import time
from typing import Any, Dict, Optional
from uuid import UUID

from claude_agent_sdk.types import (
    HookInput,
    HookContext,
    HookJSONOutput,
)

from app.repositories.tool_call_repository import ToolCallRepository
from app.repositories.session_repository import SessionRepository
from app.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def create_audit_hook(
    session_id: UUID,
    audit_service: AuditService,
):
    """Create audit logging hook for SDK events.
    
    Logs all tool usage to audit log for compliance and debugging.
    
    Args:
        session_id: Session UUID
        audit_service: AuditService instance
        
    Returns:
        Async hook callback function
        
    Example:
        >>> audit_hook = create_audit_hook(session_id, audit_service)
        >>> hooks = {"PreToolUse": [HookMatcher(hooks=[audit_hook])]}
    """

    async def audit_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Log SDK events to audit log."""
        hook_event = input_data.get("hook_event_name")

        try:
            if hook_event == "PreToolUse":
                # Log tool execution start
                await audit_service.log_tool_executed(
                    session_id=session_id,
                    tool_name=input_data["tool_name"],
                    tool_input=input_data["tool_input"],
                    result="started",
                )

            elif hook_event == "PostToolUse":
                # Log tool execution completion
                tool_response = input_data.get("tool_response", {})
                is_error = tool_response.get("is_error", False)
                
                await audit_service.log_tool_executed(
                    session_id=session_id,
                    tool_name=input_data["tool_name"],
                    tool_input=input_data["tool_input"],
                    result="error" if is_error else "success",
                )

            elif hook_event == "UserPromptSubmit":
                # Log user prompt submission
                await audit_service.log_action(
                    action="user_prompt_submitted",
                    session_id=session_id,
                    details={"prompt_length": len(input_data.get("prompt", ""))},
                )

        except Exception as e:
            logger.error(f"Audit hook error: {e}")

        # Always continue execution
        return {"continue_": True}

    return audit_hook


def create_tool_tracking_hook(
    session_id: UUID,
    db: AsyncSession,
    tool_call_repo: ToolCallRepository,
):
    """Create hook for tracking tool execution times and metrics.
    
    Tracks start/end times and updates tool_call records in database.
    
    Args:
        session_id: Session UUID
        db: Database session
        tool_call_repo: ToolCallRepository instance
        
    Returns:
        Async hook callback function
    """
    # Store start times per tool_use_id
    tool_start_times: Dict[str, float] = {}

    async def tracking_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Track tool execution metrics."""
        hook_event = input_data.get("hook_event_name")

        try:
            if hook_event == "PreToolUse" and tool_use_id:
                # Record start time
                tool_start_times[tool_use_id] = time.time()

            elif hook_event == "PostToolUse" and tool_use_id:
                # Calculate duration and update database
                if tool_use_id in tool_start_times:
                    start_time = tool_start_times[tool_use_id]
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Update tool call record
                    tool_call = await tool_call_repo.get_by_tool_use_id(tool_use_id)
                    if tool_call:
                        tool_call.duration_ms = duration_ms
                        tool_call.completed_at = tool_call.completed_at or time.time()
                        await db.commit()

                    # Clean up
                    del tool_start_times[tool_use_id]

        except Exception as e:
            logger.error(f"Tool tracking hook error: {e}")

        return {"continue_": True}

    return tracking_hook


def create_cost_tracking_hook(
    session_id: UUID,
    db: AsyncSession,
    session_repo: SessionRepository,
):
    """Create hook for tracking API costs per session.
    
    Updates session total_cost_usd from tool responses.
    
    Args:
        session_id: Session UUID
        db: Database session
        session_repo: SessionRepository instance
        
    Returns:
        Async hook callback function
    """

    async def cost_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Track and accumulate API costs."""
        hook_event = input_data.get("hook_event_name")

        try:
            if hook_event == "PostToolUse":
                # Extract cost from tool response if available
                tool_response = input_data.get("tool_response", {})
                cost = tool_response.get("cost_usd", 0) or tool_response.get("total_cost_usd", 0)

                if cost and cost > 0:
                    # Update session cost
                    session = await session_repo.get_by_id(session_id)
                    if session:
                        session.total_cost_usd = (session.total_cost_usd or 0) + cost
                        await db.commit()

        except Exception as e:
            logger.error(f"Cost tracking hook error: {e}")

        return {"continue_": True}

    return cost_hook


def create_validation_hook():
    """Create prompt validation hook for security.
    
    Validates user prompts for:
    - Prompt injection attempts
    - Excessive length
    - Malicious patterns
    
    Returns:
        Async hook callback function
    """

    # Patterns that might indicate prompt injection
    dangerous_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "you are now",
        "pretend you are",
        "disregard",
        "forget everything",
        "new instructions:",
        "system:",
        "assistant:",
    ]

    async def validation_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Validate user prompts for security issues."""
        hook_event = input_data.get("hook_event_name")

        if hook_event == "UserPromptSubmit":
            prompt = input_data.get("prompt", "")
            prompt_lower = prompt.lower()

            # Check for prompt injection attempts
            for pattern in dangerous_patterns:
                if pattern in prompt_lower:
                    logger.warning(f"Blocked prompt injection attempt: {pattern}")
                    return {
                        "decision": "block",
                        "systemMessage": "Prompt blocked: potential security issue detected",
                        "reason": f"Detected suspicious pattern: {pattern}",
                    }

            # Check prompt length
            max_length = 50000  # 50k characters
            if len(prompt) > max_length:
                logger.warning(f"Blocked excessively long prompt: {len(prompt)} chars")
                return {
                    "decision": "block",
                    "systemMessage": f"Prompt too long (max {max_length} characters)",
                    "reason": f"Prompt length: {len(prompt)} exceeds limit",
                }

        return {"continue_": True}

    return validation_hook


def create_rate_limit_hook(
    user_id: UUID,
    rate_limiter,  # RateLimiter service
):
    """Create rate limiting hook for tool execution.
    
    Enforces per-user rate limits on tool usage.
    
    Args:
        user_id: User UUID
        rate_limiter: RateLimiter service instance
        
    Returns:
        Async hook callback function
    """

    async def rate_limit_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Enforce rate limits on tool usage."""
        hook_event = input_data.get("hook_event_name")

        try:
            if hook_event == "PreToolUse":
                tool_name = input_data["tool_name"]

                # Check rate limit for this tool
                allowed = await rate_limiter.check_tool_rate_limit(
                    user_id=user_id,
                    tool_name=tool_name,
                )

                if not allowed:
                    logger.warning(f"Rate limit exceeded for user {user_id}, tool {tool_name}")
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": "Rate limit exceeded for this tool",
                        }
                    }

        except Exception as e:
            logger.error(f"Rate limit hook error: {e}")

        return {"continue_": True}

    return rate_limit_hook


def create_notification_hook(
    user_id: UUID,
    notification_service,  # NotificationService
):
    """Create notification hook for important events.
    
    Sends notifications to users on:
    - Tool execution errors
    - Session completion
    - Long-running tasks
    
    Args:
        user_id: User UUID
        notification_service: NotificationService instance
        
    Returns:
        Async hook callback function
    """

    async def notification_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Send notifications on specific events."""
        hook_event = input_data.get("hook_event_name")

        try:
            if hook_event == "PostToolUse":
                tool_name = input_data["tool_name"]
                tool_response = input_data.get("tool_response", {})

                # Notify on errors
                if tool_response.get("is_error"):
                    error_msg = tool_response.get("error", "Unknown error")
                    await notification_service.send_alert(
                        user_id=user_id,
                        title=f"Tool Error: {tool_name}",
                        message=f"Tool {tool_name} failed: {error_msg[:100]}",
                        severity="warning",
                    )

            elif hook_event == "Stop":
                # Notify on session stop
                await notification_service.send_notification(
                    user_id=user_id,
                    title="Session Stopped",
                    message="Your Claude session has stopped",
                    severity="info",
                )

        except Exception as e:
            logger.error(f"Notification hook error: {e}")

        return {"continue_": True}

    return notification_hook


def create_webhook_hook(
    webhook_config: dict,
):
    """Create webhook hook for external integrations.
    
    Calls external HTTP endpoint with hook event data.
    
    Args:
        webhook_config: Webhook configuration with url, headers, etc.
        
    Returns:
        Async hook callback function
    """
    import httpx

    url = webhook_config.get("url")
    method = webhook_config.get("method", "POST")
    headers = webhook_config.get("headers", {})
    timeout_ms = webhook_config.get("timeout_ms", 5000)

    async def webhook_hook(
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> HookJSONOutput:
        """Call external webhook with hook event."""
        try:
            # Prepare payload
            payload = {
                "hook_event": input_data.get("hook_event_name"),
                "data": input_data,
                "tool_use_id": tool_use_id,
            }

            # Call webhook
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=timeout_ms / 1000.0,
                )
                response.raise_for_status()

                # Try to parse response as hook output
                try:
                    hook_output = response.json()
                    if isinstance(hook_output, dict):
                        return hook_output
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Webhook hook error: {e}")

        # Continue on webhook failure
        return {"continue_": True}

    return webhook_hook
