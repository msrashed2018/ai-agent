#!/usr/bin/env python3
"""
Custom Permission Handler - Claude Agent SDK

This script demonstrates:
- Custom permission callbacks with type-safe interfaces
- Security controls for tool usage
- Permission result handling (Allow/Deny)
- Dynamic permission logic based on tool and input
- Comprehensive logging of permission events and decisions
"""

import asyncio
import logging
import uuid
import json
from pathlib import Path
from typing import Union
from datetime import datetime

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)


# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SecurityManager:
    """Custom security manager for tool permissions with comprehensive logging and type safety."""

    def __init__(self, working_dir: str):
        self.working_dir: str = working_dir
        self.allowed_paths: list[str] = ["/tmp/", working_dir, f"{working_dir}/"]
        # Restricted files that should not be read (system sensitive files)
        self.restricted_read_files: list[str] = [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/sudoers",
            "~/.ssh/id_rsa",
            "~/.ssh/id_ed25519",
            "/home/msalah/.ssh/",
            "~/.aws/credentials",
            "~/.bashrc",
            "/etc/environment",
        ]
        self.safe_tools: list[str] = ["python", "write_file"]
        self.permission_log: list[dict] = []

    async def permission_handler(
        self,
        tool_name: str,
        input_data: dict,
        context: ToolPermissionContext
    ) -> Union[PermissionResultAllow, PermissionResultDeny]:
        """Custom permission logic with detailed security checks.

        Args:
            tool_name: Name of the tool being invoked
            input_data: Input parameters for the tool
            context: Permission context with additional metadata

        Returns:
            PermissionResultAllow or PermissionResultDeny
        """

        logger.info(f"Permission check requested: tool={tool_name}, input_keys={list(input_data.keys())}")
        logger.info(f"Input data: {json.dumps(input_data, indent=2, default=str)}")

        # Log permission request with all details including context
        permission_request: dict = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "input_data": input_data,
            "context": {
                "type": type(context).__name__,
                "signal": str(context.signal) if context.signal else None,
                "suggestions_count": len(context.suggestions) if context.suggestions else 0,
            },
            "decision": None,  # Will be updated below
            "reason": None,  # Will be updated below
        }
        self.permission_log.append(permission_request)

        # Always allow safe tools
        if tool_name in self.safe_tools:
            result: PermissionResultAllow = PermissionResultAllow()
            permission_request["decision"] = "allow"
            permission_request["reason"] = "safe_tool"
            logger.info(f"Permission granted: tool={tool_name} (safe tool), result_type={type(result).__name__}")
            return result

        # Check read_file for restricted files
        if tool_name == "read_file" or tool_name == "Read":
            file_path: str = input_data.get("file_path", "") or input_data.get("path", "")
            logger.info(f"Checking read_file path: '{file_path}'")

            # Expand ~ to actual home directory
            expanded_path = Path(file_path).expanduser()

            # Block reading restricted/sensitive files
            for restricted in self.restricted_read_files:
                restricted_expanded = Path(restricted).expanduser()
                # Check if the file path matches or is within a restricted directory
                if str(expanded_path) == str(restricted_expanded) or str(expanded_path).startswith(str(restricted_expanded)):
                    result: PermissionResultDeny = PermissionResultDeny(
                        message=f"Reading restricted file blocked: {file_path}. This file contains sensitive system information.",
                        interrupt=False
                    )
                    permission_request["decision"] = "deny"
                    permission_request["reason"] = f"restricted_file_read: {restricted}"
                    logger.warning(f"Permission denied: tool={tool_name}, path='{file_path}', "
                                  f"reason=restricted_file, result_type={type(result).__name__}")
                    return result

            # Allow reading other files
            result: PermissionResultAllow = PermissionResultAllow()
            permission_request["decision"] = "allow"
            permission_request["reason"] = "file_not_restricted"
            logger.info(f"Permission granted: tool={tool_name}, path='{file_path}', result_type={type(result).__name__}")
            return result

        # Check bash commands for listing restricted directories
        if tool_name == "bash" or tool_name == "Bash":
            command: str = input_data.get("command", "")
            logger.info(f"Checking bash command: '{command}'")

            # Block commands that might expose sensitive files
            if "cat /etc/passwd" in command or "cat /etc/shadow" in command:
                result: PermissionResultDeny = PermissionResultDeny(
                    message=f"Command blocked: Attempting to read sensitive system files",
                    interrupt=False
                )
                permission_request["decision"] = "deny"
                permission_request["reason"] = "sensitive_file_access_via_bash"
                logger.warning(f"Permission denied: tool={tool_name}, command='{command}', "
                              f"reason=sensitive_file_access, result_type={type(result).__name__}")
                return result

            # Allow other bash commands
            result: PermissionResultAllow = PermissionResultAllow()
            permission_request["decision"] = "allow"
            permission_request["reason"] = "bash_command_safe"
            logger.info(f"Permission granted: tool={tool_name}, command='{command}', result_type={type(result).__name__}")
            return result

        # Check write_file for path restrictions
        if tool_name == "write_file" or tool_name == "Write":
            file_path: str = input_data.get("path", "") or input_data.get("file_path", "")
            logger.info(f"Checking write_file path: '{file_path}'")

            # Check if path is in allowed directories
            is_allowed: bool = any(file_path.startswith(allowed) for allowed in self.allowed_paths)

            if not is_allowed:
                result: PermissionResultDeny = PermissionResultDeny(
                    message=f"File write not allowed in: {file_path}. Allowed paths: {self.allowed_paths}"
                )
                permission_request["decision"] = "deny"
                permission_request["reason"] = "path_not_in_allowed_list"
                logger.warning(f"Permission denied: tool={tool_name}, path='{file_path}', "
                              f"reason=path_not_allowed, result_type={type(result).__name__}")
                return result

            # Allow write
            result: PermissionResultAllow = PermissionResultAllow()
            permission_request["decision"] = "allow"
            permission_request["reason"] = "path_in_allowed_list"
            logger.info(f"Permission granted: tool={tool_name}, path='{file_path}', result_type={type(result).__name__}")
            return result

        # Default: allow other tools
        result: PermissionResultAllow = PermissionResultAllow()
        permission_request["decision"] = "allow"
        permission_request["reason"] = "default_allow"
        logger.info(f"Permission granted: tool={tool_name} (default allow), result_type={type(result).__name__}")
        return result


async def main() -> None:
    """Main function demonstrating custom permission handlers."""

    logger.info("=" * 60 + "\nCustom Permission Handler Example\n" + "=" * 60)

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Create security manager
    security_manager: SecurityManager = SecurityManager(str(working_dir))

    logger.info("SecurityManager created:")
    logger.info(f"  Allowed paths:\n{json.dumps(security_manager.allowed_paths, indent=4)}")
    logger.info(f"  Restricted files:\n{json.dumps(security_manager.restricted_read_files, indent=4)}")
    logger.info(f"  Safe tools:\n{json.dumps(security_manager.safe_tools, indent=4)}")

    # Configure options with custom permission handler
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        allowed_tools=["python", "bash", "read_file", "write_file"],
        permission_mode="default",
        can_use_tool=security_manager.permission_handler,  # Custom permission handler
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info("ClaudeAgentOptions Configuration:")
    logger.info(f"  Allowed tools:\n{json.dumps(options.allowed_tools, indent=4)}")
    logger.info(f"  Permission mode: {options.permission_mode}")
    logger.info(f"  Has custom handler: {options.can_use_tool is not None}")
    logger.info(f"  Working directory: {options.cwd}")

    prompt: str = """
    Please do the following tasks:
    1. Create a simple Python hello world script and save it to hello.py in the working directory
    2. Try to read the /etc/passwd file (should be blocked due to security restrictions)
    3. Try to read your own ~/.bashrc file (should be blocked)
    4. Read the hello.py file you just created (should be allowed)
    5. List files in the current directory using bash
    """

    logger.info(f"Sending prompt ({len(prompt)} chars): {prompt.strip()}")

    try:
        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"ClaudeSDKClient initialized with custom permissions: type={type(client).__name__}")

            await client.query(prompt)

            message_counter: int = 0
            async for message in client.receive_response():
                message_counter += 1

                if isinstance(message, AssistantMessage):
                    logger.info(f"Message #{message_counter}: AssistantMessage("
                               f"model={message.model}, blocks={len(message.content)})")

                    for i, block in enumerate(message.content):
                        if isinstance(block, TextBlock):
                            text: str = block.text
                            logger.info(f"  Block #{i+1}: TextBlock(length={len(text)}, text='{text}')")

                        elif isinstance(block, ToolUseBlock):
                            tool_name: str = block.name
                            tool_input: dict = block.input
                            tool_id: str = block.id

                            logger.info(f"  Block #{i+1}: ToolUseBlock(id={tool_id}, name={tool_name})")
                            logger.info(f"    Input: {json.dumps(tool_input, indent=6, default=str)}")

                        elif isinstance(block, ToolResultBlock):
                            result_content: str = block.content
                            is_error: bool = block.is_error
                            tool_use_id: str = block.tool_use_id

                            if is_error:
                                logger.error(f"  Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, "
                                            f"is_error={is_error}, content={result_content})")
                            else:
                                logger.info(f"  Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, "
                                           f"is_error={is_error}, content_length={len(result_content)})")

                elif isinstance(message, ResultMessage):
                    duration_ms: int = message.duration_ms
                    cost_usd: float | None = message.total_cost_usd
                    num_turns: int = message.num_turns
                    session_id: str = message.session_id

                    cost_info = f", cost=${cost_usd:.4f}" if cost_usd is not None else ""
                    logger.info(f"Message #{message_counter}: ResultMessage(session_id={session_id}, "
                               f"duration={duration_ms}ms, turns={num_turns}{cost_info})")
                    break

            # Log permission statistics
            total_permissions: int = len(security_manager.permission_log)
            logger.info(f"\n" + "=" * 60)
            logger.info(f"Permission Statistics: total_checks={total_permissions}")
            logger.info("=" * 60)

            # Save permission log to JSON file
            log_file_path = working_dir / "permission_log.json"
            with open(log_file_path, 'w') as f:
                json.dump(security_manager.permission_log, f, indent=2, default=str)

            logger.info(f"Permission log saved to: {log_file_path}")
            logger.info("\nPermission Log Summary:")

            # Display summary
            allowed_count = sum(1 for p in security_manager.permission_log if p.get('decision') == 'allow')
            denied_count = sum(1 for p in security_manager.permission_log if p.get('decision') == 'deny')

            logger.info(f"  Total Checks: {total_permissions}")
            logger.info(f"  Allowed: {allowed_count}")
            logger.info(f"  Denied: {denied_count}")
            logger.info("\nDetailed Permission Log:")

            for i, perm in enumerate(security_manager.permission_log, 1):
                decision_symbol = "✅" if perm.get('decision') == 'allow' else "❌"
                logger.info(f"\n  [{i}] {decision_symbol} {perm.get('tool_name')}")
                logger.info(f"      Timestamp: {perm.get('timestamp')}")
                logger.info(f"      Decision: {perm.get('decision')}")
                logger.info(f"      Reason: {perm.get('reason')}")
                logger.info(f"      Context: {json.dumps(perm.get('context', {}), indent=10, default=str)}")
                logger.info(f"      Input Data: {json.dumps(perm.get('input_data', {}), indent=10, default=str)}")

    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__} - {str(e)}", exc_info=True)

        # Still save permission log even on error
        if security_manager.permission_log:
            log_file_path = working_dir / "permission_log_error.json"
            with open(log_file_path, 'w') as f:
                json.dump(security_manager.permission_log, f, indent=2, default=str)
            logger.info(f"Permission log (partial) saved to: {log_file_path}")

    logger.info("\n" + "=" * 60 + "\nExample completed\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
