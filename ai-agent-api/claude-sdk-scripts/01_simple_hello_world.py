#!/usr/bin/env python3
"""
Simple Claude SDK test: Write a hello world file
This is the most basic example of using the Claude SDK client
"""

import asyncio
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, PermissionResultAllow


async def permission_callback(tool_name, tool_input, context):
    """Permission callback - allow all tools for testing"""
    print(f"\n[PERMISSION] Tool '{tool_name}' requesting: {str(tool_input)[:100]}")
    return PermissionResultAllow()


async def main():
    # Create a persistent directory for working files (not temp)
    workdir = Path("/tmp/claude-sdk-test-01")
    workdir.mkdir(exist_ok=True, parents=True)
    print(f"Working directory: {workdir}")

    # Create SDK options with permission callback
    options = ClaudeAgentOptions(
        cwd=str(workdir),
        model="claude-sonnet-4-5",  # Sonnet 4.5 model
        max_turns=5,
        can_use_tool=permission_callback,  # Permission callback goes in options
    )

    # Create client with options
    client = ClaudeSDKClient(options=options)

    prompt = "Create a file called hello_world.py that prints 'Hello, World!' and then run it"
    print(f"\nPrompt: {prompt}\n")

    print("=" * 80)
    print("RESPONSES:")
    print("=" * 80)

    try:
        # Connect and stream responses
        await client.connect(prompt)

        message_count = 0
        async for message in client.receive_response():
            message_count += 1
            print(f"\n[Message #{message_count}]")
            print(f"  Type: {message.type if hasattr(message, 'type') else 'UNKNOWN'}")
            print(f"  Dir: {[attr for attr in dir(message) if not attr.startswith('_')]}")

            if hasattr(message, 'content'):
                print(f"  Content exists: True (length: {len(message.content) if message.content else 0})")
                for i, block in enumerate(message.content):
                    print(f"\n  [Block #{i}]")
                    if hasattr(block, 'type'):
                        print(f"    Type: {block.type}")
                    else:
                        print(f"    Type: NOT FOUND")

                    # Log all block attributes
                    block_attrs = [attr for attr in dir(block) if not attr.startswith('_')]
                    print(f"    Attributes: {block_attrs}")

                    if hasattr(block, 'text'):
                        text = block.text
                        if len(text) > 300:
                            print(f"    Text: {text[:300]}...")
                        else:
                            print(f"    Text: {text}")

                    if hasattr(block, 'name'):
                        print(f"    Tool Name: {block.name}")

                    if hasattr(block, 'input'):
                        print(f"    Tool Input: {str(block.input)[:200]}")

                    if hasattr(block, 'tool_use_id'):
                        print(f"    Tool Use ID: {block.tool_use_id}")

                    if hasattr(block, 'result'):
                        print(f"    Tool Result: {str(block.result)[:200]}")
            else:
                print(f"  Content exists: False")

        print(f"\n[Summary] Total messages received: {message_count}")

        # Disconnect client
        await client.disconnect()

    except Exception as e:
        print(f"\nError during query: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Check if file was created
    print("\n" + "=" * 80)
    print("RESULTS:")
    print("=" * 80)
    hello_file = workdir / "hello_world.py"
    if hello_file.exists():
        print(f"✓ File created: {hello_file}")
        print(f"  Content:\n{hello_file.read_text()}")
    else:
        print("✗ File not created")

    # List all files in workdir
    print(f"\nAll files in {workdir}:")
    for file_path in workdir.rglob("*"):
        if file_path.is_file():
            print(f"  - {file_path.relative_to(workdir)}")


if __name__ == "__main__":
    asyncio.run(main())
