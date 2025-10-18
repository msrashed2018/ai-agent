"""Validation hook for tool input validation."""
import logging
from typing import Dict, Any, Optional, List

from app.claude_sdk.hooks.base_hook import BaseHook, HookType

logger = logging.getLogger(__name__)


class ValidationHook(BaseHook):
    """Validation hook for checking tool inputs before execution.

    Validates tool inputs against predefined rules and blocks execution
    if validation fails.
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize validation hook.

        Args:
            validation_rules: Optional custom validation rules per tool
        """
        self.validation_rules = validation_rules or {}

    @property
    def hook_type(self) -> HookType:
        """Return PreToolUse to validate before execution."""
        return HookType.PRE_TOOL_USE

    @property
    def priority(self) -> int:
        """High priority (20) to validate early."""
        return 20

    async def execute(
        self,
        input_data: Dict[str, Any],
        tool_use_id: Optional[str],
        context: Any
    ) -> Dict[str, Any]:
        """Validate tool input data.

        Args:
            input_data: Tool execution parameters
            tool_use_id: Tool use ID
            context: Hook context

        Returns:
            {"continue_": True} if valid, {"continue_": False} if invalid
        """
        try:
            tool_name = input_data.get("name") or input_data.get("tool_name")
            tool_input = input_data.get("input", {})

            # Check if we have validation rules for this tool
            if tool_name in self.validation_rules:
                rules = self.validation_rules[tool_name]
                validation_result = self._validate_input(tool_input, rules)

                if not validation_result["valid"]:
                    logger.warning(
                        f"Validation failed for {tool_name}: {validation_result['errors']}",
                        extra={"tool_name": tool_name, "tool_use_id": tool_use_id}
                    )

                    return {
                        "continue_": False,
                        "decision": "block",
                        "reason": f"Validation failed: {', '.join(validation_result['errors'])}",
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "validation": validation_result
                        }
                    }

            logger.debug(
                f"Validation passed for {tool_name}",
                extra={"tool_name": tool_name, "tool_use_id": tool_use_id}
            )

            return {"continue_": True}

        except Exception as e:
            logger.error(
                f"ValidationHook error: {type(e).__name__} - {str(e)}",
                exc_info=True
            )
            # Don't block on validation errors - allow execution
            return {"continue_": True}

    def _validate_input(
        self,
        tool_input: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate tool input against rules.

        Args:
            tool_input: Input parameters to validate
            rules: Validation rules

        Returns:
            Dictionary with "valid" bool and "errors" list
        """
        errors: List[str] = []

        # Check required fields
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in tool_input:
                errors.append(f"Missing required field: {field}")

        # Check field types
        field_types = rules.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in tool_input:
                actual_value = tool_input[field]
                if expected_type == "string" and not isinstance(actual_value, str):
                    errors.append(f"Field {field} must be string")
                elif expected_type == "int" and not isinstance(actual_value, int):
                    errors.append(f"Field {field} must be integer")
                elif expected_type == "bool" and not isinstance(actual_value, bool):
                    errors.append(f"Field {field} must be boolean")

        # Check field patterns (regex)
        field_patterns = rules.get("field_patterns", {})
        for field, pattern in field_patterns.items():
            if field in tool_input:
                import re
                value = str(tool_input[field])
                if not re.match(pattern, value):
                    errors.append(f"Field {field} does not match pattern {pattern}")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
