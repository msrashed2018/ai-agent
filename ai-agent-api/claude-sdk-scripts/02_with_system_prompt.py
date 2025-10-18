#!/usr/bin/env python3
"""
Claude SDK test: Using system prompt with query method
Demonstrates one-shot query with custom system prompt
"""

import asyncio
import tempfile
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Working directory: {tmpdir}")

        # Create SDK options with system prompt
        options = ClaudeAgentOptions(
            cwd=tmpdir,
            model="claude-3-5-sonnet-20241022",
            max_turns=3,
            system_prompt="You are a Python expert. Write clean, well-documented code.",
        )

        prompt = "Create a Python script that calculates factorial of 5"
        print(f"\nPrompt: {prompt}")
        print(f"System Prompt: {options.system_prompt}\n")

        print("=" * 80)
        print("USING query() - ONE SHOT QUERY:")
        print("=" * 80)

        # Use query() for simple one-shot interaction
        result = await query(prompt=prompt, options=options)

        print(f"\nResult Type: {type(result)}")
        if hasattr(result, 'content'):
            for block in result.content:
                if hasattr(block, 'text'):
                    print(f"Response: {block.text[:500]}...")

        # Check created files
        print("\n" + "=" * 80)
        print("FILES CREATED:")
        print("=" * 80)
        for file_path in Path(tmpdir).rglob("*"):
            if file_path.is_file():
                print(f"✓ {file_path.name}")
                if file_path.suffix == ".py":
                    print(f"  Content (first 300 chars):\n{file_path.read_text()[:300]}\n")


if __name__ == "__main__":
    asyncio.run(main())
