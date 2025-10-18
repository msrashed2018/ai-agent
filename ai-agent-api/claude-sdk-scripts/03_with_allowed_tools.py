#!/usr/bin/env python3
"""
Claude SDK test: Restricting allowed tools
Demonstrates how to control which tools Claude can use
"""

import asyncio
import tempfile
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


async def test_with_all_tools():
    """Test with all tools allowed (wildcard)"""
    print("\n" + "=" * 80)
    print("TEST 1: WITH ALL TOOLS ALLOWED (wildcard)")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        options = ClaudeAgentOptions(
            cwd=tmpdir,
            model="claude-3-5-sonnet-20241022",
            max_turns=3,
            allowed_tools=["*"],  # Allow all tools
        )

        client = ClaudeSDKClient(options=options)
        prompt = "Create a test file and list files in this directory"
        print(f"Allowed Tools: {options.allowed_tools}")
        print(f"Prompt: {prompt}\n")

        await client.connect(prompt)

        tool_calls = []
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'name'):
                        tool_calls.append(block.name)
                        print(f"Tool used: {block.name}")

        await client.disconnect()
        print(f"Total tools used: {len(tool_calls)}")


async def test_with_restricted_tools():
    """Test with restricted tools"""
    print("\n" + "=" * 80)
    print("TEST 2: WITH RESTRICTED TOOLS ONLY")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        options = ClaudeAgentOptions(
            cwd=tmpdir,
            model="claude-3-5-sonnet-20241022",
            max_turns=3,
            allowed_tools=["Write", "Read"],  # Only allow Write and Read
        )

        client = ClaudeSDKClient(options=options)
        prompt = "Create a file called config.json with some test data"
        print(f"Allowed Tools: {options.allowed_tools}")
        print(f"Prompt: {prompt}\n")

        await client.connect(prompt)

        tool_calls = []
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'name'):
                        tool_calls.append(block.name)
                        print(f"Tool used: {block.name}")

        await client.disconnect()
        print(f"Total tools used: {len(tool_calls)}")


async def test_with_glob_patterns():
    """Test with glob patterns for tool names"""
    print("\n" + "=" * 80)
    print("TEST 3: WITH GLOB PATTERNS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        options = ClaudeAgentOptions(
            cwd=tmpdir,
            model="claude-3-5-sonnet-20241022",
            max_turns=3,
            allowed_tools=["Read*", "Write*"],  # Glob patterns
        )

        client = ClaudeSDKClient(options=options)
        prompt = "Create a test.txt file with content"
        print(f"Allowed Tools (patterns): {options.allowed_tools}")
        print(f"Prompt: {prompt}\n")

        await client.connect(prompt)

        tool_calls = []
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'name'):
                        tool_calls.append(block.name)
                        print(f"Tool used: {block.name}")

        await client.disconnect()
        print(f"Total tools used: {len(tool_calls)}")


async def main():
    await test_with_all_tools()
    await test_with_restricted_tools()
    await test_with_glob_patterns()


if __name__ == "__main__":
    asyncio.run(main())
