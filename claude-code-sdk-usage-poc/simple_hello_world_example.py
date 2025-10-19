#!/usr/bin/env python3
"""
Simple Hello World Example - Claude Agent SDK

This script demonstrates:
1. Using the query() function for simple one-shot interactions
2. Allowing Claude to use the write_file tool
3. Handling different message types from Claude's response
4. Comprehensive logging with proper type hints
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import AsyncIterator, Union

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk import (
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


async def main() -> None:
    """Main function demonstrating Claude creating a hello world file with type-safe handling."""

    logger.info("=" * 60 + "\nClaude Agent SDK - Hello World Example\n" + "=" * 60)

    try:
        # Create unique working directory
        working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
        working_dir.mkdir(parents=True, exist_ok=True)

        # Configure options to allow file writing with type annotation
        options: ClaudeAgentOptions = ClaudeAgentOptions(
            allowed_tools=["write_file", "read_file"],
            permission_mode="acceptEdits",
            cwd=str(working_dir),
            model="claude-sonnet-4-5"
        )

        logger.info(f"Configuration: ClaudeAgentOptions(allowed_tools={options.allowed_tools}, "
                   f"permission_mode={options.permission_mode}, cwd={options.cwd}, model={options.model})")

        # The prompt asking Claude to create a hello world file
        prompt: str = """
        Please create a simple "hello_world.txt" file that contains:
        - A greeting message
        - The current date
        - A simple ASCII art

        Make it friendly and fun!
        """

        logger.info(f"Sending prompt ({len(prompt)} chars): {prompt.strip()}")

        # Type hint for the async iterator of messages
        message_stream: AsyncIterator[Union[AssistantMessage, ResultMessage]] = query(
            prompt=prompt,
            options=options
        )

        message_count: int = 0

        # Use the query function to send the prompt
        async for message in message_stream:
            message_count += 1
            message_type: str = type(message).__name__

            logger.info(f"Received message #{message_count}: {message_type}")

            # Handle different types of messages
            if isinstance(message, AssistantMessage):
                logger.info(f"  AssistantMessage: id={message.id}, model={message.model}, "
                           f"role={message.role}, blocks={len(message.content)}")

                # Process each content block in the assistant's message
                for i, block in enumerate(message.content):
                    if isinstance(block, TextBlock):
                        text: str = block.text
                        logger.info(f"  Block #{i+1}: TextBlock(length={len(text)}, text='{text}')")

                    elif isinstance(block, ToolUseBlock):
                        # ToolUseBlock: tool invocation request
                        tool_name: str = block.name
                        tool_input: dict = block.input
                        tool_id: str = block.id

                        logger.info(f"  Block #{i+1}: ToolUseBlock(id={tool_id}, name={tool_name}, input={tool_input})")

                    elif isinstance(block, ToolResultBlock):
                        # ToolResultBlock: tool execution result
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
                # ResultMessage: final result with metadata
                duration_ms: int = message.duration_ms
                api_duration_ms: int = message.duration_api_ms
                cost_usd: float | None = message.total_cost_usd
                num_turns: int = message.num_turns
                session_id: str = message.session_id
                is_error: bool = message.is_error

                cost_info = f", cost=${cost_usd:.4f}" if cost_usd is not None else ""
                logger.info(f"  ResultMessage: session_id={session_id}, duration={duration_ms}ms, "
                           f"api_duration={api_duration_ms}ms, turns={num_turns}, is_error={is_error}{cost_info}")

                if is_error:
                    logger.error(f"Session ended with error: session_id={session_id}")
                else:
                    logger.info(f"Session completed successfully: session_id={session_id}")

    except Exception as e:
        logger.error(f"Error occurred during Claude interaction: {type(e).__name__} - {str(e)}", exc_info=True)

    logger.info("=" * 60 + f"\nExample completed - processed {message_count} messages\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
