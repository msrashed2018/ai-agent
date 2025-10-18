"""
Mappers to convert domain/DB models to API schemas.
"""

from typing import Any, Dict

from app.schemas.session import SessionResponse


def _sdk_options_to_dict(sdk_options: Any) -> Dict:
    """Convert SDK options (dict or value object) to plain dict."""
    if sdk_options is None:
        return {}
    if isinstance(sdk_options, dict):
        return sdk_options
    # Fallback for value object with to_dict
    to_dict = getattr(sdk_options, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict()
        except Exception:
            return {}
    return {}


def session_to_response(session: Any) -> SessionResponse:
    """Build SessionResponse from a domain entity or SQLAlchemy model."""
    sdk_opts = _sdk_options_to_dict(getattr(session, "sdk_options", None))
    allowed_tools = sdk_opts.get("allowed_tools") or []
    system_prompt = sdk_opts.get("system_prompt")

    # Status can be an Enum or plain str
    status = getattr(session, "status", None)
    status_value = getattr(status, "value", status)

    # Working directory field name differs between layers
    working_directory = (
        getattr(session, "working_directory_path", None)
        or getattr(session, "working_directory", None)
        or ""
    )

    # Numeric fields may be Decimal in the ORM layer
    total_cost_usd = getattr(session, "total_cost_usd", 0) or 0
    try:
        total_cost_usd = float(total_cost_usd)
    except Exception:
        total_cost_usd = 0.0

    return SessionResponse(
        id=getattr(session, "id"),
        user_id=getattr(session, "user_id"),
        name=getattr(session, "name", None),
        description=getattr(session, "description", None),
        status=status_value,
        working_directory=working_directory,
        allowed_tools=allowed_tools,
        system_prompt=system_prompt,
        sdk_options=sdk_opts,
        parent_session_id=getattr(session, "parent_session_id", None),
        is_fork=bool(getattr(session, "is_fork", False)),
        message_count=int(getattr(session, "total_messages", 0) or 0),
        tool_call_count=int(getattr(session, "total_tool_calls", 0) or 0),
        total_cost_usd=total_cost_usd,
        total_input_tokens=int(getattr(session, "api_input_tokens", 0) or 0),
        total_output_tokens=int(getattr(session, "api_output_tokens", 0) or 0),
        created_at=getattr(session, "created_at"),
        updated_at=getattr(session, "updated_at"),
        started_at=getattr(session, "started_at", None),
        completed_at=getattr(session, "completed_at", None),
        error_message=getattr(session, "error_message", None),
        metadata={},
    )


__all__ = ["session_to_response"]

