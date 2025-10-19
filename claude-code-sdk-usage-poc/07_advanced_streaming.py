#!/usr/bin/env python3
"""
Advanced Streaming Example - Claude Agent SDK

This script demonstrates:
- Streaming mode with partial messages (include_partial_messages=True)
- Real-time message processing with timing
- StreamEvent handling
- Session statistics and metrics
- Clean JSON logging
"""

import asyncio
import logging
import json
import time
import uuid
from pathlib import Path
from typing import Optional

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage
from claude_agent_sdk.types import StreamEvent


# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class StreamingDemo:
    """Demonstrates advanced streaming capabilities with type-safe message handling."""

    def __init__(self):
        self.message_count: int = 0
        self.start_time: float = time.time()
        self.session_log: list[dict] = []

    async def handle_message(self, message) -> None:
        """Process incoming messages with detailed logging.

        Args:
            message: Message object from Claude (AssistantMessage, ResultMessage, or StreamEvent)
        """
        self.message_count += 1
        elapsed: float = time.time() - self.start_time

        log_entry: dict = {
            "timestamp": elapsed,
            "message_number": self.message_count,
            "type": type(message).__name__
        }

        if isinstance(message, AssistantMessage):
            log_entry["model"] = message.model
            log_entry["content_blocks"] = len(message.content)

            logger.info(f"\n[{elapsed:.1f}s] Message #{self.message_count}: AssistantMessage")
            logger.info(json.dumps({
                "model": message.model,
                "blocks": len(message.content)
            }, indent=2))

            for i, block in enumerate(message.content):
                if isinstance(block, TextBlock):
                    text: str = block.text
                    log_entry.setdefault("blocks", []).append({"type": "TextBlock", "length": len(text)})
                    logger.info(f"\n  Block #{i+1}: TextBlock")
                    logger.info(json.dumps({
                        "length": len(text),
                        "preview": text[:100] + "..." if len(text) > 100 else text
                    }, indent=4))

                elif isinstance(block, ToolUseBlock):
                    tool_name: str = block.name
                    tool_input: dict = block.input
                    tool_id: str = block.id
                    log_entry.setdefault("blocks", []).append({"type": "ToolUseBlock", "name": tool_name, "id": tool_id})
                    logger.info(f"\n  Block #{i+1}: ToolUseBlock")
                    logger.info(json.dumps({
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_input
                    }, indent=4, default=str))

                elif isinstance(block, ToolResultBlock):
                    result_content: str = block.content
                    is_error: bool = block.is_error
                    tool_use_id: str = block.tool_use_id
                    log_entry.setdefault("blocks", []).append({"type": "ToolResultBlock", "tool_use_id": tool_use_id, "is_error": is_error})

                    logger.info(f"\n  Block #{i+1}: ToolResultBlock")
                    logger.info(json.dumps({
                        "tool_use_id": tool_use_id,
                        "is_error": is_error,
                        "content_length": len(result_content) if isinstance(result_content, str) else 0
                    }, indent=4))

        elif isinstance(message, StreamEvent):
            event_type: str = message.event.get("type", "unknown")
            log_entry["event_type"] = event_type
            log_entry["event_data"] = message.event
            logger.info(f"\n[{elapsed:.1f}s] StreamEvent")
            logger.info(json.dumps({
                "type": event_type,
                "data": message.event
            }, indent=2, default=str))

        elif isinstance(message, ResultMessage):
            duration_ms: int = message.duration_ms
            cost_usd: Optional[float] = message.total_cost_usd
            num_turns: int = message.num_turns
            session_id: str = message.session_id

            log_entry["duration_ms"] = duration_ms
            log_entry["cost_usd"] = cost_usd
            log_entry["num_turns"] = num_turns
            log_entry["session_id"] = session_id

            logger.info(f"\n[{elapsed:.1f}s] ResultMessage")
            logger.info(json.dumps({
                "session_id": session_id,
                "duration_ms": duration_ms,
                "turns": num_turns,
                "cost_usd": cost_usd
            }, indent=2, default=str))

        self.session_log.append(log_entry)


async def main() -> None:
    """Main function demonstrating advanced streaming features."""

    logger.info("\n" + "=" * 60)
    logger.info("Advanced Streaming Example")
    logger.info("=" * 60 + "\n")

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Create streaming demo instance
    demo: StreamingDemo = StreamingDemo()

    logger.info("StreamingDemo Instance:")
    logger.info(json.dumps({
        "type": type(demo).__name__,
        "start_time": demo.start_time
    }, indent=2))

    # Configure options with streaming enabled
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        allowed_tools=["python", "bash", "read_file", "write_file"],
        permission_mode="acceptEdits",
        include_partial_messages=True,  # Enable partial message streaming
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info("\nConfiguration:")
    logger.info(json.dumps({
        "allowed_tools": options.allowed_tools,
        "permission_mode": options.permission_mode,
        "include_partial_messages": options.include_partial_messages,
        "model": options.model,
        "cwd": options.cwd
    }, indent=2))

    prompt: str = """
    Create a simple Python script that:
    1. Defines a function to calculate fibonacci numbers
    2. Has a main function that prints the first 10 fibonacci numbers
    3. Save it to a file called fibonacci.py
    4. Run the script to verify it works
    """

    logger.info(f"Sending prompt ({len(prompt)} chars): {prompt.strip()}")

    try:
        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"\nClaudeSDKClient initialized with streaming enabled: type={type(client).__name__}")

            await client.query(prompt)

            # Process streaming messages
            async for message in client.receive_response():
                await demo.handle_message(message)

                # Break on ResultMessage
                if isinstance(message, ResultMessage):
                    break

            # Calculate message type distribution
            message_types: dict = {}
            for entry in demo.session_log:
                msg_type: str = entry["type"]
                message_types[msg_type] = message_types.get(msg_type, 0) + 1

            # Log session statistics
            logger.info("\n" + "=" * 60)
            logger.info("Session Statistics")
            logger.info("=" * 60)
            logger.info(json.dumps({
                "total_messages": demo.message_count,
                "session_duration_seconds": round(time.time() - demo.start_time, 2),
                "log_entries": len(demo.session_log),
                "message_type_distribution": message_types
            }, indent=2))

            # Save session log to JSON file
            log_file_path = working_dir / "streaming_session_log.json"
            with open(log_file_path, 'w') as f:
                json.dump(demo.session_log, f, indent=2, default=str)

            logger.info(f"\nSession log saved to: {log_file_path}")

    except Exception as e:
        logger.error(f"\nError: {type(e).__name__} - {str(e)}")

        # Still save session log even on error
        if demo.session_log:
            log_file_path = working_dir / "streaming_session_log_error.json"
            with open(log_file_path, 'w') as f:
                json.dump(demo.session_log, f, indent=2, default=str)
            logger.info(f"Partial session log saved to: {log_file_path}")

    logger.info("\n" + "=" * 60)
    logger.info("Completed")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
