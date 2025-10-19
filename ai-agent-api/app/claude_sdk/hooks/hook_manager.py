"""Hook manager for orchestrating hook execution."""
import logging
import time
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import HookMatcher

from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from app.claude_sdk.hooks.hook_registry import HookRegistry
from app.claude_sdk.hooks.hook_context import HookContext
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.models.hook_execution import HookExecutionModel

logger = logging.getLogger(__name__)


class HookManager:
    """Orchestrate hook execution across all hook types.

    The HookManager is responsible for:
    - Registering hooks by type and priority
    - Executing hooks in the correct order
    - Logging hook executions to the database
    - Building SDK-compatible HookMatcher configurations
    - Handling hook errors gracefully

    Example usage:
        >>> manager = HookManager(db, hook_execution_repo)
        >>> manager.register_hook(HookType.PRE_TOOL_USE, AuditHook(), priority=10)
        >>> manager.register_hook(HookType.PRE_TOOL_USE, ValidationHook(), priority=20)
        >>> hook_matchers = manager.build_hook_matchers(session_id, enabled_hooks)
        >>> # Use hook_matchers in ClaudeAgentOptions
    """

    def __init__(
        self,
        db: AsyncSession,
        hook_execution_repo: HookExecutionRepository
    ):
        """Initialize hook manager.

        Args:
            db: Database session for persistence
            hook_execution_repo: Repository for logging hook executions
        """
        self.db = db
        self.hook_execution_repo = hook_execution_repo
        self.registry = HookRegistry()

        logger.info("HookManager initialized")

    async def register_hook(
        self,
        hook_type: HookType,
        hook: BaseHook,
        priority: Optional[int] = None
    ) -> None:
        """Register a hook for execution.

        Args:
            hook_type: Type of hook to register
            hook: Hook instance
            priority: Execution priority (lower = higher priority).
                     If None, uses hook's default priority.
        """
        actual_priority = priority if priority is not None else hook.priority

        self.registry.register(hook_type, hook, actual_priority)

        logger.info(
            f"Registered hook: type={hook_type.value}, "
            f"class={hook.__class__.__name__}, priority={actual_priority}"
        )

    async def execute_hooks(
        self,
        hook_type: HookType,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any,
        session_id: UUID
    ) -> Dict[str, Any]:
        """Execute all hooks for a given type in priority order.

        Based on POC script 04_hook_system.py, hooks receive:
        - input_data: Dict containing tool information and parameters
        - tool_use_id: ID of the tool being used (or None)
        - context: SDK context object

        Hooks must return: {"continue_": True/False, ...}

        Args:
            hook_type: Type of hooks to execute
            input_data: Hook input data from SDK
            tool_use_id: Tool use ID if applicable
            context: Hook context from SDK
            session_id: Session ID for logging

        Returns:
            Merged hook results with at least {"continue_": bool}
        """
        hooks = self.registry.get_hooks(hook_type)

        if not hooks:
            # No hooks registered for this type, continue execution
            return {"continue_": True}

        # Merged result starts with continue=True
        merged_result: Dict[str, Any] = {"continue_": True}

        for hook in hooks:
            hook_name = hook.__class__.__name__
            start_time = time.time()

            try:
                logger.debug(
                    f"Executing hook: {hook_name} for {hook_type.value}",
                    extra={"session_id": str(session_id), "tool_use_id": tool_use_id}
                )

                # Execute the hook
                hook_result = await hook.execute(input_data, tool_use_id, context)

                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)

                # Log successful execution
                await self._log_hook_execution(
                    session_id=session_id,
                    hook_type=hook_type,
                    hook_name=hook_name,
                    tool_use_id=tool_use_id,
                    tool_name=input_data.get("name") or input_data.get("tool_name"),
                    input_data=input_data,
                    output_data=hook_result,
                    context_data=self._serialize_context(context),
                    execution_time_ms=execution_time_ms,
                    error_message=None
                )

                # Merge results (later hooks can override earlier ones)
                merged_result.update(hook_result)

                # Stop if hook says to not continue
                if not hook_result.get("continue_", True):
                    logger.warning(
                        f"Hook {hook_name} blocked execution",
                        extra={"session_id": str(session_id), "tool_use_id": tool_use_id}
                    )
                    break

            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)

                logger.error(
                    f"Hook {hook_name} failed: {type(e).__name__} - {str(e)}",
                    extra={"session_id": str(session_id), "tool_use_id": tool_use_id},
                    exc_info=True
                )

                # Log failed execution
                await self._log_hook_execution(
                    session_id=session_id,
                    hook_type=hook_type,
                    hook_name=hook_name,
                    tool_use_id=tool_use_id,
                    tool_name=input_data.get("name") or input_data.get("tool_name"),
                    input_data=input_data,
                    output_data={},
                    context_data=self._serialize_context(context),
                    execution_time_ms=execution_time_ms,
                    error_message=f"{type(e).__name__}: {str(e)}"
                )

                # Continue with other hooks despite error
                continue

        return merged_result

    def build_hook_matchers(
        self,
        session_id: UUID,
        enabled_hook_types: List[HookType]
    ) -> Dict[str, List[HookMatcher]]:
        """Build SDK-compatible HookMatcher configuration.

        Based on POC script 04_hook_system.py, the SDK expects:
        {
            "PreToolUse": [HookMatcher(hooks=[...])],
            "PostToolUse": [HookMatcher(hooks=[...])],
            ...
        }

        Args:
            session_id: Session ID for hook execution context
            enabled_hook_types: List of hook types to enable

        Returns:
            Dictionary mapping hook type names to HookMatcher lists
        """
        hook_matchers: Dict[str, List[HookMatcher]] = {}

        for hook_type in enabled_hook_types:
            hooks = self.registry.get_hooks(hook_type)

            if hooks:
                # Create wrapper function that calls execute_hooks
                # Use closure to capture hook_type value correctly
                def create_hook_callback(ht: HookType):
                    async def hook_callback(
                        input_data: Dict[str, Any],
                        tool_use_id: str,
                        context: Any
                    ) -> Dict[str, Any]:
                        return await self.execute_hooks(
                            hook_type=ht,
                            input_data=input_data,
                            tool_use_id=tool_use_id,
                            context=context,
                            session_id=session_id
                        )
                    return hook_callback

                # Build the callback for this hook type
                callback = create_hook_callback(hook_type)

                # Create HookMatcher
                matcher = HookMatcher(hooks=[callback])

                hook_matchers[hook_type.value] = [matcher]

                logger.info(
                    f"Built HookMatcher for {hook_type.value} with {len(hooks)} hooks"
                )

        return hook_matchers

    async def _log_hook_execution(
        self,
        session_id: UUID,
        hook_type: HookType,
        hook_name: str,
        tool_use_id: Optional[str],
        tool_name: Optional[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context_data: Dict[str, Any],
        execution_time_ms: int,
        error_message: Optional[str]
    ) -> None:
        """Log hook execution to database.

        Args:
            session_id: Session ID
            hook_type: Type of hook executed
            hook_name: Name of hook class
            tool_use_id: Tool use ID if applicable
            tool_name: Name of tool being used
            input_data: Hook input data
            output_data: Hook output data
            context_data: Serialized context
            execution_time_ms: Execution duration in milliseconds
            error_message: Error message if hook failed
        """
        try:
            hook_execution = HookExecutionModel(
                session_id=session_id,
                tool_call_id=None,  # Will be linked later if needed
                hook_name=f"{hook_type.value}_{hook_name}",
                tool_use_id=tool_use_id or "",
                tool_name=tool_name or "unknown",
                input_data=input_data,
                output_data=output_data,
                context_data=context_data,
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )

            await self.hook_execution_repo.create(hook_execution)

        except Exception as e:
            # Don't fail hook execution if logging fails
            logger.error(
                f"Failed to log hook execution: {type(e).__name__} - {str(e)}",
                extra={"session_id": str(session_id)},
                exc_info=True
            )

    def _serialize_context(self, context: Any) -> Dict[str, Any]:
        """Serialize SDK context object to dictionary.

        Args:
            context: SDK context object

        Returns:
            Serialized context dictionary
        """
        if isinstance(context, dict):
            return context

        try:
            # Try to extract relevant fields from context
            return {
                "type": type(context).__name__,
                "signal": str(getattr(context, "signal", None)),
                "suggestions": len(getattr(context, "suggestions", [])),
            }
        except Exception:
            return {"type": type(context).__name__ if context else "None"}
