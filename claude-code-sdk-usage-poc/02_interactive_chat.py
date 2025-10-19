#!/usr/bin/env python3
"""
Interactive Chat Client - Claude Agent SDK

This script demonstrates:
- ClaudeSDKClient for interactive conversations
- Multi-turn conversations with type-safe message handling
- Real-time message processing
- Dynamic model and permission switching
- Graceful session management
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
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


async def interactive_chat() -> None:
    """Main interactive chat function with type-safe handling."""

    logger.info("=" * 60 + "\nInteractive Chat with Claude\n" + "=" * 60)
    logger.info("Type 'quit', 'exit', or 'bye' to end the conversation")
    logger.info("Type 'help' for available commands")
    logger.info("Commands: /model <name>, /permission <mode>, /interrupt, /info")

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Configure options with type annotation
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        allowed_tools=["python", "bash", "read_file", "write_file"],
        permission_mode="bypassPermissions",  # Allow all operations without prompting
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info(f"Configuration: ClaudeAgentOptions(allowed_tools={options.allowed_tools}, "
               f"permission_mode={options.permission_mode}, model={options.model}, cwd={options.cwd})")

    turn_counter: int = 0

    try:
        # Use ClaudeSDKClient as async context manager
        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"ClaudeSDKClient initialized: type={type(client).__name__}")
            logger.info("Claude is ready! Start chatting...")

            while True:
                # Get user input
                try:
                    user_input: str = input("\nYou: ").strip()
                    turn_counter += 1

                    logger.info(f"Turn #{turn_counter}: User input received ({len(user_input)} chars): '{user_input}'")

                except (EOFError, KeyboardInterrupt):
                    logger.info("User interrupted session via keyboard")
                    break

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    logger.info(f"User requested session end at turn #{turn_counter}")
                    break

                if user_input.lower() == 'help':
                    logger.info("Available commands: /model <name>, /permission <mode>, /interrupt, /info, quit/exit/bye")
                    continue

                # Handle special commands
                if user_input.startswith('/'):
                    await handle_command(client, user_input)
                    continue

                # Send message to Claude
                logger.info(f"Turn #{turn_counter}: Sending query to Claude...")

                await client.query(user_input)

                # Receive and display response
                message_counter: int = 0
                async for message in client.receive_response():
                    message_counter += 1

                    if isinstance(message, AssistantMessage):
                        parent_info = f", parent_tool_use_id={message.parent_tool_use_id}" if message.parent_tool_use_id else ""
                        logger.info(f"  Message #{message_counter}: AssistantMessage("
                                   f"model={message.model}, blocks={len(message.content)}{parent_info})")

                        for i, block in enumerate(message.content):
                            if isinstance(block, TextBlock):
                                text: str = block.text
                                logger.info(f"    Block #{i+1}: TextBlock(length={len(text)}, text='{text}')")

                            elif isinstance(block, ToolUseBlock):
                                tool_name: str = block.name
                                tool_input: dict = block.input
                                tool_id: str = block.id

                                logger.info(f"    Block #{i+1}: ToolUseBlock(id={tool_id}, name={tool_name}, input={tool_input})")

                            elif isinstance(block, ToolResultBlock):
                                result_content: str = block.content
                                is_error: bool = block.is_error
                                tool_use_id: str = block.tool_use_id

                                if is_error:
                                    logger.error(f"    Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, "
                                                f"is_error={is_error}, content={result_content})")
                                else:
                                    logger.info(f"    Block #{i+1}: ToolResultBlock(tool_use_id={tool_use_id}, "
                                               f"is_error={is_error}, content_length={len(result_content)})")

                    elif isinstance(message, ResultMessage):
                        duration_ms: int = message.duration_ms
                        cost_usd: Optional[float] = message.total_cost_usd
                        num_turns: int = message.num_turns
                        session_id: str = message.session_id

                        cost_info = f", cost=${cost_usd:.4f}" if cost_usd is not None else ""
                        logger.info(f"  Message #{message_counter}: ResultMessage(session_id={session_id}, "
                                   f"duration={duration_ms}ms, turns={num_turns}{cost_info})")
                        break

    except Exception as e:
        logger.error(f"Error in interactive chat at turn #{turn_counter}: {type(e).__name__} - {str(e)}",
                    exc_info=True)

    logger.info(f"=" * 60 + f"\nInteractive chat session ended after {turn_counter} turns\n" + "=" * 60)


async def handle_command(client: ClaudeSDKClient, command: str) -> None:
    """Handle special slash commands with type-safe client operations.

    Args:
        client: The ClaudeSDKClient instance
        command: The command string starting with /
    """
    parts: list[str] = command.split()
    cmd: str = parts[0].lower()

    logger.info(f"Processing command: {cmd} (full command: '{command}')")

    try:
        if cmd == '/model' and len(parts) > 1:
            model: str = parts[1]
            await client.set_model(model)
            logger.info(f"Model changed to: {model}")

        elif cmd == '/permission' and len(parts) > 1:
            mode: str = parts[1]
            await client.set_permission_mode(mode)
            logger.info(f"Permission mode changed to: {mode}")

        elif cmd == '/interrupt':
            await client.interrupt()
            logger.info("Client operation interrupted")

        elif cmd == '/info':
            info = await client.get_server_info()
            logger.info(f"Server info retrieved: type={type(info).__name__}, data={info}")
            if not info:
                logger.warning("No server info available")

        else:
            logger.warning(f"Unknown command: {cmd}. Available: /model, /permission, /interrupt, /info")

    except Exception as e:
        logger.error(f"Command execution failed for '{cmd}': {type(e).__name__} - {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(interactive_chat())
