#!/usr/bin/env python3
"""
Basic Hello World Example - Claude Agent SDK

This script demonstrates:
- Basic query() function usage
- Simple file creation with write_file tool
- Message type handling with proper type hints
- Comprehensive logging of inputs, outputs, and SDK objects
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
    """Main function demonstrating basic query() usage with type-safe message handling."""

    logger.info("=" * 60 + "\n" + "Basic Hello World Example - Claude Agent SDK" + "\n" + "=" * 60)

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Configure options with type-safe ClaudeAgentOptions
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        allowed_tools=["write_file", "read_file"],
        permission_mode="acceptEdits",
        cwd=str(working_dir)
    )

    # Log configuration details
    logger.info(f"Configuration: Type={type(options).__name__}, "
                f"Allowed tools={options.allowed_tools}, "
                f"Permission mode={options.permission_mode}, "
                f"Working directory={options.cwd}, "
                f"Model={options.model or 'default'}")

    prompt: str = """
    Create a simple hello_world.txt file with:
    - A greeting message
    - Today's date
    - Some ASCII art
    """

    logger.info(f"Prompt ({len(prompt)} chars): {prompt.strip()}")
    logger.info("Processing query...")

    try:
        # Type hint for the async iterator of messages
        message_stream: AsyncIterator[Union[AssistantMessage, ResultMessage]] = query(
            prompt=prompt,
            options=options
        )

        message_count: int = 0

        async for message in message_stream:
            message_count += 1

            # Log message type
            logger.info(f"Message #{message_count}: {type(message).__name__}")

            if isinstance(message, AssistantMessage):
                # Log AssistantMessage details
                logger.info(f"  AssistantMessage: Model={message.model}, Role={message.role}, Blocks={len(message.content)}")

                # Process each content block with type checking
                for i, block in enumerate(message.content):
                    block_type: str = type(block).__name__

                    if isinstance(block, TextBlock):
                        # TextBlock: text content from Claude
                        text: str = block.text
                        logger.info(f"  Block #{i+1}: TextBlock(text_length={len(text)}, text='{text}')")

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
                            logger.error(f"  Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, is_error={is_error}, content={result_content})")
                        else:
                            logger.info(f"  Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, is_error={is_error}, content={result_content})")

            elif isinstance(message, ResultMessage):
                # ResultMessage: final result with metadata
                duration_ms: int = message.duration_ms
                api_duration_ms: int = message.duration_api_ms
                cost_usd: float | None = message.total_cost_usd
                num_turns: int = message.num_turns
                session_id: str = message.session_id
                is_error: bool = message.is_error

                cost_str = f", cost=${cost_usd:.4f}" if cost_usd is not None else ""
                logger.info(f"  ResultMessage: session_id={session_id}, duration={duration_ms}ms, "
                           f"api_duration={api_duration_ms}ms, turns={num_turns}, is_error={is_error}{cost_str}")

    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__} - {str(e)}", exc_info=True)

    logger.info("=" * 60 + f"\nExample completed - processed {message_count} messages\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
