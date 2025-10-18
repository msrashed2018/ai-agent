"""Options builder for converting domain configuration to SDK options."""
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions
from app.domain.entities.session import Session


class OptionsBuilder:
    """Build ClaudeAgentOptions from business configuration.

    Converts domain Session entity and additional runtime configuration
    into the ClaudeAgentOptions format required by the official SDK.

    Reference: POC scripts in claude-code-sdk-usage-poc/ for SDK patterns.
    """

    @staticmethod
    def build(
        session: Session,
        permission_callback: Optional[Callable] = None,
        hooks: Optional[Dict[str, List[Any]]] = None,
        mcp_servers: Optional[Dict[str, Any]] = None,
    ) -> ClaudeAgentOptions:
        """Build SDK options from domain Session entity.

        Args:
            session: Domain Session entity with configuration
            permission_callback: Optional permission check callback
            hooks: Optional hook matchers for SDK hooks
            mcp_servers: Optional MCP server configurations

        Returns:
            ClaudeAgentOptions configured for SDK client

        Example:
            >>> session = Session(...)
            >>> options = OptionsBuilder.build(session)
            >>> client = ClaudeSDKClient(options)
        """
        # Extract model from sdk_options or use default
        model = session.sdk_options.get("model", "claude-sonnet-4-5")

        # Extract max_turns from sdk_options or use default
        max_turns = session.sdk_options.get("max_turns", 10)

        # Extract allowed_tools list if present
        allowed_tools = session.sdk_options.get("allowed_tools")

        # Determine working directory
        cwd = None
        if session.working_directory_path:
            cwd = Path(session.working_directory_path)

        # Build SDK options
        options = ClaudeAgentOptions(
            model=model,
            permission_mode=session.permission_mode,
            max_turns=max_turns,
            include_partial_messages=session.include_partial_messages,
            cwd=cwd,
            mcp_servers=mcp_servers or {},
            allowed_tools=allowed_tools,
            can_use_tool=permission_callback,
            hooks=hooks or {},
        )

        return options

    @staticmethod
    def build_from_dict(
        session_id: str,
        config_dict: Dict[str, Any],
        permission_callback: Optional[Callable] = None,
        hooks: Optional[Dict[str, List[Any]]] = None,
    ) -> ClaudeAgentOptions:
        """Build SDK options from dictionary configuration.

        Utility method for building options when you have a raw config dict
        instead of a Session entity.

        Args:
            session_id: Session identifier
            config_dict: Configuration dictionary
            permission_callback: Optional permission check callback
            hooks: Optional hook matchers

        Returns:
            ClaudeAgentOptions configured for SDK client
        """
        options = ClaudeAgentOptions(
            model=config_dict.get("model", "claude-sonnet-4-5"),
            permission_mode=config_dict.get("permission_mode", "default"),
            max_turns=config_dict.get("max_turns", 10),
            include_partial_messages=config_dict.get("include_partial_messages", False),
            cwd=Path(config_dict["working_directory"]) if "working_directory" in config_dict else None,
            mcp_servers=config_dict.get("mcp_servers", {}),
            allowed_tools=config_dict.get("allowed_tools"),
            can_use_tool=permission_callback,
            hooks=hooks or {},
        )

        return options
