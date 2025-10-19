#!/usr/bin/env python3
"""
MCP SDK Server Example - Claude Agent SDK

This script demonstrates:
- Creating custom SDK MCP servers with @tool decorator
- In-process tool execution with type-safe interfaces
- Multiple tool categories (calculator, data, utilities)
- Tool error handling and security
- Comprehensive logging of tool definitions and usage
"""

import asyncio
import logging
import json
import uuid
from pathlib import Path
from typing import Dict, Any

from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
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


# ============================================================================
# CALCULATOR TOOLS
# ============================================================================

@tool("calculate", "Perform mathematical calculations safely", {"expression": str})
async def calculate(args: Dict[str, Any]) -> Dict[str, Any]:
    """Safe calculator that evaluates mathematical expressions.

    Args:
        args: Dictionary with 'expression' key containing math expression

    Returns:
        Tool result dictionary with content and optional is_error flag
    """
    expression: str = args["expression"].strip()

    logger.info(f"Tool 'calculate' invoked: expression='{expression}'")

    # Security: only allow safe mathematical operations
    allowed_chars: set = set("0123456789+-*/().% ")
    if not all(c in allowed_chars for c in expression):
        logger.warning(f"Tool 'calculate' rejected: invalid characters in '{expression}'")
        return {
            "content": [{"type": "text", "text": "Error: Expression contains invalid characters"}],
            "is_error": True
        }

    try:
        # Use eval with restricted builtins for safety
        result: float = eval(expression, {"__builtins__": {}}, {})
        logger.info(f"Tool 'calculate' result: {expression} = {result}")
        return {
            "content": [{
                "type": "text",
                "text": f"Expression: {expression}\nResult: {result}"
            }]
        }
    except Exception as e:
        logger.error(f"Tool 'calculate' error: {type(e).__name__} - {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Calculation error: {str(e)}"}],
            "is_error": True
        }


@tool("unit_convert", "Convert between units", {"value": float, "from_unit": str, "to_unit": str})
async def unit_convert(args: Dict[str, Any]) -> Dict[str, Any]:
    """Convert between different units.

    Args:
        args: Dictionary with value, from_unit, and to_unit

    Returns:
        Tool result dictionary
    """
    value: float = args["value"]
    from_unit: str = args["from_unit"].lower()
    to_unit: str = args["to_unit"].lower()

    logger.info(f"Tool 'unit_convert' invoked: {value} {from_unit} to {to_unit}")

    # Length conversions (to meters)
    length_units: Dict[str, float] = {
        "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
        "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.34
    }

    try:
        # Length conversion
        if from_unit in length_units and to_unit in length_units:
            meters: float = value * length_units[from_unit]
            result: float = meters / length_units[to_unit]

            logger.info(f"Tool 'unit_convert' result: {value} {from_unit} = {result:.6g} {to_unit}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"{value} {from_unit} = {result:.6g} {to_unit}"
                }]
            }
        else:
            logger.warning(f"Tool 'unit_convert' unsupported: {from_unit} to {to_unit}")
            return {
                "content": [{"type": "text", "text": f"Unsupported conversion: {from_unit} to {to_unit}"}],
                "is_error": True
            }

    except Exception as e:
        logger.error(f"Tool 'unit_convert' error: {type(e).__name__} - {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Conversion error: {str(e)}"}],
            "is_error": True
        }


# ============================================================================
# DATA TOOLS
# ============================================================================

@tool("format_json", "Format and validate JSON data", {"json_string": str})
async def format_json(args: Dict[str, Any]) -> Dict[str, Any]:
    """Format and validate JSON strings.

    Args:
        args: Dictionary with json_string to format

    Returns:
        Tool result dictionary
    """
    import json

    json_string: str = args["json_string"]

    logger.info(f"Tool 'format_json' invoked: input_length={len(json_string)}")

    try:
        # Parse and reformat JSON
        data = json.loads(json_string)
        formatted: str = json.dumps(data, indent=2, sort_keys=True)

        logger.info(f"Tool 'format_json' success: formatted {len(formatted)} chars")
        return {
            "content": [{
                "type": "text",
                "text": f"Formatted JSON:\n{formatted}"
            }]
        }
    except json.JSONDecodeError as e:
        logger.error(f"Tool 'format_json' JSON decode error: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Invalid JSON: {str(e)}"}],
            "is_error": True
        }
    except Exception as e:
        logger.error(f"Tool 'format_json' error: {type(e).__name__} - {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True
        }


@tool("text_stats", "Analyze text statistics", {"text": str})
async def text_stats(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze text and provide statistics.

    Args:
        args: Dictionary with text to analyze

    Returns:
        Tool result dictionary
    """
    text: str = args["text"]

    logger.info(f"Tool 'text_stats' invoked: text_length={len(text)}")

    try:
        # Calculate statistics
        char_count: int = len(text)
        word_count: int = len(text.split())
        line_count: int = len(text.splitlines())
        unique_words: int = len(set(text.lower().split()))

        stats: str = f"""Text Statistics:
- Characters: {char_count}
- Words: {word_count}
- Lines: {line_count}
- Unique words: {unique_words}
- Average word length: {char_count / word_count if word_count > 0 else 0:.1f}
"""

        logger.info(f"Tool 'text_stats' result: chars={char_count}, words={word_count}, lines={line_count}")
        return {
            "content": [{"type": "text", "text": stats}]
        }
    except Exception as e:
        logger.error(f"Tool 'text_stats' error: {type(e).__name__} - {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error analyzing text: {str(e)}"}],
            "is_error": True
        }


async def main() -> None:
    """Main function demonstrating SDK MCP servers."""

    logger.info("=" * 60 + "\nMCP SDK Server Example\n" + "=" * 60)

    # Create unique working directory
    working_dir: Path = Path(f"/workspace/me/repositories/claude-code-sdk-tests/working_directory/{uuid.uuid4()}")
    working_dir.mkdir(parents=True, exist_ok=True)

    # Create SDK MCP server with custom tools
    my_tools_server = create_sdk_mcp_server(
        name="my_tools",
        version="1.0.0",
        tools=[calculate, unit_convert, format_json, text_stats]
    )

    logger.info(f"SDK MCP server created: name='my_tools', version='1.0.0', tools=['calculate', 'unit_convert', 'format_json', 'text_stats']")

    # Configure options with the SDK server
    # Note: Don't restrict allowed_tools when using MCP servers
    # The tools will be prefixed as: mcp__my_tools__<tool_name>
    # Use bypassPermissions to allow MCP tools without prompting
    options: ClaudeAgentOptions = ClaudeAgentOptions(
        mcp_servers={"my_tools": my_tools_server},
        permission_mode="bypassPermissions",  # Allow all tools without prompting
        model="claude-sonnet-4-5",
        cwd=str(working_dir)
    )

    logger.info("Configuration:")
    logger.info(json.dumps({
        "mcp_servers": ["my_tools"],
        "permission_mode": options.permission_mode,
        "model": options.model,
        "cwd": options.cwd
    }, indent=2))
    logger.info("Note: MCP tools will be available as: mcp__my_tools__<tool_name>\n")

    prompt: str = """
    Please demonstrate the custom tools by:
    1. Calculate: 15 * 23 + 100
    2. Convert: 100 meters to feet
    3. Format this JSON: {"name":"Alice","age":30,"city":"NYC"}
    4. Analyze statistics for this text: "The quick brown fox jumps over the lazy dog"
    """

    logger.info(f"Sending prompt ({len(prompt)} chars): {prompt.strip()}")

    try:
        async with ClaudeSDKClient(options=options) as client:
            logger.info(f"ClaudeSDKClient initialized with SDK MCP server: type={type(client).__name__}")

            await client.query(prompt)

            message_counter: int = 0
            tool_use_counter: int = 0

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
                            tool_use_counter += 1
                            tool_name: str = block.name
                            tool_input: dict = block.input
                            tool_id: str = block.id

                            logger.info(f"  Block #{i+1}: ToolUseBlock(id={tool_id}, name={tool_name})")
                            logger.info(f"    Input:\n{json.dumps(tool_input, indent=6, default=str)}")

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

            logger.info(f"\nSDK MCP Server statistics: total_tool_uses={tool_use_counter}")

    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__} - {str(e)}", exc_info=True)

    logger.info("=" * 60 + "\nExample completed\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
