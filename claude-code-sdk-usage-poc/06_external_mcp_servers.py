#!/usr/bin/env python3
"""
External MCP Server Example - Claude Agent SDK

This script demonstrates:
- Connecting to external MCP servers (subprocess-based)
- Configuring stdio MCP servers with external packages
- Using filesystem MCP server (@modelcontextprotocol/server-filesystem)
- Clean JSON logging

To run this example, you need:
    npm install -g @modelcontextprotocol/server-filesystem
"""

import asyncio
import logging
import json
import uuid
from pathlib import Path
from typing import Dict

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage


# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function demonstrating external MCP servers."""

    logger.info("\n" + "=" * 60)
    logger.info("External MCP Server Example - Filesystem Server")
    logger.info("=" * 60 + "\n")

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Configure external Filesystem MCP Server (stdio/subprocess-based)
    # This spawns npx as a subprocess that runs the filesystem MCP server
    filesystem_server_config = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(working_dir)],
        "env": {}
    }

    logger.info("External MCP Server Configuration:")
    logger.info(json.dumps({
        "server_name": "filesystem",
        "type": "stdio (subprocess)",
        "package": "@modelcontextprotocol/server-filesystem",
        "command": filesystem_server_config["command"],
        "args": filesystem_server_config["args"]
    }, indent=2))

    # Collect MCP servers
    mcp_servers: Dict[str, Dict] = {
        "filesystem": filesystem_server_config
    }

    # Configure options with bypassPermissions to allow all external tools
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        mcp_servers=mcp_servers,
        permission_mode="bypassPermissions",  # Allow external MCP tools without prompting
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info("\nClaudeAgentOptions:")
    logger.info(json.dumps({
        "mcp_servers": list(mcp_servers.keys()),
        "permission_mode": options.permission_mode,
        "model": options.model,
        "working_dir": str(working_dir)
    }, indent=2))

    # Simple prompt to use filesystem tools
    prompt: str = "Create a file called 'test.txt' with the content 'Hello from external MCP filesystem server!', then read it back to verify."

    logger.info(f"\nPrompt: {prompt}\n")

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            tool_use_counter: int = 0

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for i, block in enumerate(message.content):
                        if isinstance(block, TextBlock):
                            logger.info(f"\n[Claude Response]")
                            logger.info(block.text)

                        elif isinstance(block, ToolUseBlock):
                            tool_use_counter += 1
                            logger.info(f"\n[External MCP Tool Call #{tool_use_counter}]")
                            logger.info(json.dumps({
                                "tool_id": block.id,
                                "tool_name": block.name,
                                "input": block.input
                            }, indent=2, default=str))

                        elif isinstance(block, ToolResultBlock):
                            status = "ERROR" if block.is_error else "SUCCESS"
                            logger.info(f"\n[Tool Result - {status}]")
                            if isinstance(block.content, str):
                                logger.info(block.content[:500])  # First 500 chars
                            else:
                                logger.info(json.dumps(block.content, indent=2, default=str))

                elif isinstance(message, ResultMessage):
                    logger.info("\n" + "=" * 60)
                    logger.info("Summary")
                    logger.info("=" * 60)
                    logger.info(json.dumps({
                        "session_id": message.session_id,
                        "duration_ms": message.duration_ms,
                        "turns": message.num_turns,
                        "cost_usd": message.total_cost_usd,
                        "total_tool_calls": tool_use_counter
                    }, indent=2, default=str))
                    break

    except Exception as e:
        logger.error(f"\nError: {type(e).__name__} - {str(e)}")
        logger.info("\nNote: This example requires the filesystem MCP server to be installed:")
        logger.info("  npm install -g @modelcontextprotocol/server-filesystem")
        logger.info("\nIf you see connection errors, the MCP server package may not be installed.")

    logger.info("\n" + "=" * 60)
    logger.info("Completed")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
