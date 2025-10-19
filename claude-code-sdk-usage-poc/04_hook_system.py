#!/usr/bin/env python3
"""
Hook System Example - Claude Agent SDK

This script demonstrates ALL supported hook events in Python SDK:

SUPPORTED HOOKS (6 total):
1. PreToolUse         - Before tool execution
2. PostToolUse        - After tool execution
3. UserPromptSubmit   - When user submits a prompt
4. Stop               - Right before Claude concludes its response
5. SubagentStop       - Right before a subagent (Task tool) concludes its response
6. PreCompact         - Before conversation compaction

NOT SUPPORTED in Python SDK (available in TypeScript only):
❌ SessionStart       - When a new session is started
❌ SessionEnd         - When a session is ending
❌ Notification       - When notifications are sent

Note: Due to setup limitations, the Python SDK does not support SessionStart,
SessionEnd, and Notification hooks.

This script shows:
- Input data structure that SDK passes to each hook
- Output format that hooks should return to SDK
- Simple logging-only implementation to explore the hook system
"""

import asyncio
import logging
import json
import uuid
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage


# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class HookManager:
    """Simple hook manager that logs all hook inputs and outputs."""

    def __init__(self):
        self.hook_logs: list[dict] = []

    def _log_hook(self, hook_name: str, input_data: Dict[str, Any], tool_use_id: str, context: Any, output: Dict[str, Any]):
        """Log hook invocation with all details."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "hook_name": hook_name,
            "tool_use_id": tool_use_id,
            "context_type": type(context).__name__ if context else None,
            "input_data": input_data,
            "output": output
        }
        self.hook_logs.append(log_entry)

        # Compact logging - just show hook name and key info
        logger.info(f"\n[HOOK] {hook_name} | tool_use_id={tool_use_id or 'None'}")
        logger.info(json.dumps({
            "input_data": input_data,
            "output": output
        }, indent=2, default=str))

    async def pre_tool_use_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called BEFORE any tool is executed."""
        output = {"continue_": True}
        self._log_hook("PreToolUse", input_data, tool_use_id, context, output)
        return output

    async def post_tool_use_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called AFTER tool execution completes."""
        output = {"continue_": True}
        self._log_hook("PostToolUse", input_data, tool_use_id, context, output)
        return output

    async def user_prompt_submit_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called when user submits a prompt."""
        output = {"continue_": True}
        self._log_hook("UserPromptSubmit", input_data, tool_use_id, context, output)
        return output

    async def stop_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called when execution stops."""
        output = {"continue_": True}
        self._log_hook("Stop", input_data, tool_use_id, context, output)
        return output

    async def subagent_stop_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called when subagent stops."""
        output = {"continue_": True}
        self._log_hook("SubagentStop", input_data, tool_use_id, context, output)
        return output

    async def pre_compact_hook(self, input_data: Dict[str, Any], tool_use_id: str, context: Any) -> Dict[str, Any]:
        """Hook called before conversation compacting."""
        output = {"continue_": True}
        self._log_hook("PreCompact", input_data, tool_use_id, context, output)
        return output


async def main() -> None:
    """Main function demonstrating all hooks with simple logging."""

    logger.info("\n" + "=" * 60)
    logger.info("Hook System Example - All Hooks")
    logger.info("=" * 60)

    logger.info("\nSupported Hooks in Python SDK (6 total):")
    logger.info("  1. PreToolUse         - Before tool execution")
    logger.info("  2. PostToolUse        - After tool execution")
    logger.info("  3. UserPromptSubmit   - When user submits a prompt")
    logger.info("  4. Stop               - Right before Claude concludes its response")
    logger.info("  5. SubagentStop       - Right before a subagent concludes")
    logger.info("  6. PreCompact         - Before conversation compaction")

    logger.info("\nNOT Supported in Python SDK:")
    logger.info("  ❌ SessionStart, SessionEnd, Notification")
    logger.info("")

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Create hook manager
    hook_manager: HookManager = HookManager()

    # Create hook matchers for all hook types
    all_hooks_matcher: HookMatcher = HookMatcher(
        matcher=None,  # Apply to all
        hooks=[
            hook_manager.pre_tool_use_hook,
            hook_manager.post_tool_use_hook,
        ]
    )

    user_prompt_matcher: HookMatcher = HookMatcher(
        hooks=[hook_manager.user_prompt_submit_hook]
    )

    stop_matcher: HookMatcher = HookMatcher(
        hooks=[hook_manager.stop_hook]
    )

    subagent_stop_matcher: HookMatcher = HookMatcher(
        hooks=[hook_manager.subagent_stop_hook]
    )

    pre_compact_matcher: HookMatcher = HookMatcher(
        hooks=[hook_manager.pre_compact_hook]
    )

    # Configure options with ALL hooks
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        allowed_tools=["python", "bash", "read_file", "write_file"],
        permission_mode="acceptEdits",
        hooks={
            "PreToolUse": [all_hooks_matcher],
            "PostToolUse": [all_hooks_matcher],
            "UserPromptSubmit": [user_prompt_matcher],
            "Stop": [stop_matcher],
            "SubagentStop": [subagent_stop_matcher],
            "PreCompact": [pre_compact_matcher]
        },
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info("Configuration:")
    logger.info(json.dumps({
        "hooks": list(options.hooks.keys()),
        "allowed_tools": options.allowed_tools,
        "permission_mode": options.permission_mode,
        "model": options.model,
        "working_dir": str(working_dir)
    }, indent=2))

    # Simple prompt
    prompt: str = "Please create a simple text file called 'test.txt' with the content 'Hello from hooks test', next step create agent that do create another simple text file called 'test2.txt' with the content 'Hello from hooks test2'"
    logger.info(f"\nPrompt: {prompt}\n")

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            # Process messages silently
            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    result_info = {
                        "session_id": message.session_id,
                        "duration_ms": message.duration_ms,
                        "turns": message.num_turns,
                        "cost_usd": message.total_cost_usd
                    }
                    logger.info("\nResult:")
                    logger.info(json.dumps(result_info, indent=2, default=str))
                    break

            # Save all hook logs to JSON file
            log_file_path = working_dir / "hook_logs.json"
            with open(log_file_path, 'w') as f:
                json.dump(hook_manager.hook_logs, f, indent=2, default=str)

            # Summary
            hook_counts = {}
            for log in hook_manager.hook_logs:
                hook_name = log['hook_name']
                hook_counts[hook_name] = hook_counts.get(hook_name, 0) + 1

            logger.info("\n" + "="*60)
            logger.info("Summary")
            logger.info("="*60)
            logger.info(json.dumps({
                "total_hooks_executed": len(hook_manager.hook_logs),
                "hooks_by_type": hook_counts,
                "log_file": str(log_file_path)
            }, indent=2))

    except Exception as e:
        logger.error(f"\nError: {type(e).__name__} - {str(e)}")

        # Still save hook logs even on error
        if hook_manager.hook_logs:
            log_file_path = working_dir / "hook_logs_error.json"
            with open(log_file_path, 'w') as f:
                json.dump(hook_manager.hook_logs, f, indent=2, default=str)
            logger.info(json.dumps({
                "status": "error",
                "partial_log_file": str(log_file_path)
            }, indent=2))

    logger.info("\n" + "="*60)
    logger.info("Completed")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
