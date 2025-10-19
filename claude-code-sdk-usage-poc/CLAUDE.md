# Claude Agent SDK - Development Guide

**Version**: 1.0
**Purpose**: Essential guidance for working with the Claude Agent SDK test repository

---

## Quick Reference

**CRITICAL: Always consult the documentation first**

1. **Read** `docs/claude-agent-sdk-user-guide.md` - Comprehensive usage patterns and API reference
2. **Read** `docs/claude-agent-sdk-technical-overview.md` - Architecture and internal implementation details
3. **Review** example files (`01_*.py` through `08_*.py`) for specific use cases

---

## Core SDK Concepts

### Two Main Interfaces

**1. `query()` Function** - Simple, one-shot interactions
- Use for: Automation, batch processing, single questions
- Pattern: Fire-and-forget
- Example: `01_basic_hello_world.py`

**2. `ClaudeSDKClient` Class** - Interactive streaming client
- Use for: Chat interfaces, multi-turn conversations, interactive sessions
- Pattern: Bidirectional streaming
- Example: `02_interactive_chat.py`

### Message Types

The SDK uses strongly-typed message objects:
- **`AssistantMessage`**: Claude's responses with content blocks
- **`ResultMessage`**: Final results with cost/usage metadata
- **`StreamEvent`**: Partial updates during streaming (when enabled)

### Content Block Types

Messages contain typed content blocks:
- **`TextBlock`**: Regular text content (`block.text`)
- **`ThinkingBlock`**: Claude's reasoning process
- **`ToolUseBlock`**: Tool invocation requests (`block.name`, `block.input`, `block.id`)
- **`ToolResultBlock`**: Tool execution results (`block.content`, `block.is_error`, `block.tool_use_id`)

---

## Configuration Patterns

### ClaudeAgentOptions - The Central Configuration Object

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    # Model Selection
    model="claude-sonnet-4-5",  # or "claude-opus-4-1-20250805"

    # Tool Management
    allowed_tools=["python", "bash", "read_file", "write_file"],
    disallowed_tools=["dangerous_tool"],

    # Permission System
    permission_mode="default",  # "default", "acceptEdits", "bypassPermissions"
    can_use_tool=custom_permission_handler,  # Custom callback (requires streaming)

    # Working Environment
    cwd="/path/to/working/directory",
    env={"CUSTOM_VAR": "value"},

    # MCP Servers
    mcp_servers={"my_tools": my_tools_server},

    # Hook System
    hooks={
        "PreToolUse": [hook_matcher],
        "PostToolUse": [hook_matcher],
        "UserPromptSubmit": [hook_matcher]
    },

    # Advanced Options
    include_partial_messages=True,  # Enable streaming events
    max_turns=10,  # Limit conversation length
    continue_conversation=True,  # Resume previous session
)
```

### Permission Modes

1. **`"default"`**: Prompts user for dangerous operations (safest)
2. **`"acceptEdits"`**: Auto-approve file edits, prompt for other dangerous operations
3. **`"bypassPermissions"`**: Allow all operations without prompting (use with caution!)
4. **Custom Callbacks**: Implement `can_use_tool` function for fine-grained control

**IMPORTANT**: Custom permission callbacks (`can_use_tool`) require streaming mode (`ClaudeSDKClient`), not `query()`.

---

## Common Use Cases & Examples

### 1. Basic File Operations (`01_basic_hello_world.py`)
- Simple `query()` usage
- File creation with `write_file` tool
- Message type handling with proper type hints
- See: docs/claude-agent-sdk-user-guide.md:53-70

### 2. Interactive Chat (`02_interactive_chat.py`)
- Multi-turn conversations
- Dynamic commands (`/model`, `/permission`, `/interrupt`, `/info`)
- Real-time message processing
- Session management

### 3. Custom Security Controls (`03_custom_permissions.py`)
- Custom permission handler implementation
- Path restrictions (allowed directories)
- Command filtering (dangerous bash commands)
- Permission logging and auditing
- Returns: `PermissionResultAllow()` or `PermissionResultDeny(message, interrupt)`

### 4. Event Hooks (`04_hook_system.py`)
- **PreToolUse**: Intercept before tool execution (validate/modify inputs)
- **PostToolUse**: Process after tool execution (logging/metrics)
- **UserPromptSubmit**: Monitor user inputs (auditing)
- Hook matchers with regex patterns (`matcher="python|bash"`)
- See: docs/claude-agent-sdk-user-guide.md:459-579

### 5. SDK MCP Servers (`05_mcp_sdk_servers.py`)
- Custom tools with `@tool` decorator
- In-process tool execution
- Tool categories: calculator, data, utilities
- Error handling in tool implementations

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("tool_name", "Description", {"param": str})
async def my_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": "Result"}],
        "is_error": False  # Optional
    }

my_server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0",
    tools=[my_tool]
)
```

### 6. External MCP Servers (`06_external_mcp_servers.py`)
- Stdio MCP servers (subprocess-based)
- SSE and HTTP servers
- Mixed SDK + external server configurations

### 7. Advanced Streaming (`07_advanced_streaming.py`)
- Partial message streaming (`include_partial_messages=True`)
- Real-time message processing
- Session metrics tracking
- StreamEvent handling

### 8. Production-Ready Patterns (`08_production_ready.py`)
- Retry logic with exponential backoff
- Comprehensive error handling
- Metrics collection (`SessionMetrics` class)
- Configuration validation
- Production logging

---

## Critical Implementation Patterns

### 1. Always Use Async/Await

```python
import asyncio

async def main():
    async for message in query(prompt="Hello"):
        print(message)

asyncio.run(main())
```

### 2. Type-Safe Message Handling

```python
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ResultMessage

async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                text: str = block.text
            elif isinstance(block, ToolUseBlock):
                tool_name: str = block.name
                tool_input: dict = block.input
    elif isinstance(message, ResultMessage):
        # Response complete
        break
```

### 3. Proper Context Manager Usage

```python
# GOOD: Use async context manager
async with ClaudeSDKClient(options=options) as client:
    await client.query("Hello")
    async for message in client.receive_response():
        process(message)

# AVOID: Manual lifecycle management
```

### 4. Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError, CLIConnectionError, CLINotFoundError,
    ProcessError, CLIJSONDecodeError
)

try:
    async for message in query("Hello"):
        print(message)
except CLINotFoundError:
    print("Install: npm install -g @anthropic-ai/claude-code")
except CLIConnectionError as e:
    print(f"Connection failed: {e}")
except ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

---

## Hook System Deep Dive

### Available Hook Events

1. **`PreToolUse`**: Before tool execution
   - Validate inputs
   - Modify tool parameters
   - Block dangerous operations
   - Return: `{"continue_": True/False, "hookSpecificOutput": {...}}`

2. **`PostToolUse`**: After tool execution
   - Log results
   - Add context to responses
   - Track metrics

3. **`UserPromptSubmit`**: When user submits input
   - Audit logging
   - Input validation
   - Add security context

4. **`Stop`**: When execution stops
5. **`SubagentStop`**: When subagent stops
6. **`PreCompact`**: Before conversation compacting

### Hook Return Structure

```python
async def my_hook(input_data: Dict, tool_use_id: str, context: Any) -> Dict:
    # Allow and continue
    return {"continue_": True}

    # Block operation
    return {
        "continue_": False,
        "decision": "block",
        "systemMessage": "Operation blocked",
        "reason": "Security policy violation"
    }

    # Modify input
    return {
        "continue_": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": modified_input
        }
    }
```

---

## Common Pitfalls & Solutions

### 1. Custom Permissions with query()

**WRONG**:
```python
options = ClaudeAgentOptions(can_use_tool=my_handler)
async for msg in query("Hello", options=options):  # ERROR!
    print(msg)
```

**CORRECT**:
```python
options = ClaudeAgentOptions(can_use_tool=my_handler)
async with ClaudeSDKClient(options=options) as client:  # Streaming required
    await client.query("Hello")
    async for msg in client.receive_response():
        print(msg)
```

### 2. Message Loop Completion

**IMPORTANT**: Always break on `ResultMessage` to end the response loop:

```python
async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        # Process assistant message
        pass
    elif isinstance(message, ResultMessage):
        # Response complete - MUST break here
        break
```

### 3. Working Directory Setup

```python
from pathlib import Path

# Always ensure directory exists
working_dir = Path("/path/to/dir")
working_dir.mkdir(parents=True, exist_ok=True)

options = ClaudeAgentOptions(cwd=str(working_dir))
```

### 4. Tool Result Handling

```python
# Check is_error flag in ToolResultBlock
if isinstance(block, ToolResultBlock):
    if block.is_error:
        logger.error(f"Tool failed: {block.content}")
    else:
        logger.info(f"Tool succeeded: {block.content}")
```

---

## Testing & Development

### Run Examples

```bash
# Quick test
python run_all_examples.py --quick

# Full test suite (includes interactive examples)
python run_all_examples.py --full

# Individual examples
python 01_basic_hello_world.py
python 02_interactive_chat.py
```

### Debug Mode

```python
options = ClaudeAgentOptions(
    extra_args={"debug-to-stderr": None},
    stderr=lambda msg: print(f"DEBUG: {msg}")
)
```

---

## Architecture Reference

**Communication Flow**:
```
Python SDK ←→ Claude Code CLI ←→ Claude API
           JSON over stdin/stdout
```

**SDK Layers**:
1. **Public API**: `query()`, `ClaudeSDKClient`, `@tool` decorator
2. **Internal Implementation**: `InternalClient`, `Query`, Message Parser
3. **Transport Layer**: `SubprocessCLITransport`
4. **Claude Code CLI**: Subprocess with JSON I/O

**Key Files in This Repository**:
- `01-08_*.py`: Progressive examples from basic to production
- `run_all_examples.py`: Test suite runner
- `docs/claude-agent-sdk-user-guide.md`: Complete API reference
- `docs/claude-agent-sdk-technical-overview.md`: Architecture details

---

## Best Practices Summary

1. **Choose the Right Interface**:
   - `query()` for automation and batch processing
   - `ClaudeSDKClient` for interactive applications

2. **Configure Permissions Appropriately**:
   - `"default"` for development and testing
   - `"acceptEdits"` for trusted environments
   - Custom handlers for production security

3. **Handle Errors Gracefully**:
   - Use specific exception types
   - Implement retry logic for connection errors
   - Log errors with full context

4. **Use Type Hints**:
   - All examples use comprehensive type annotations
   - Helps catch errors during development
   - Improves IDE autocomplete

5. **Monitor and Log**:
   - Track tool usage (see `04_hook_system.py`)
   - Collect metrics (see `08_production_ready.py`)
   - Audit permissions (see `03_custom_permissions.py`)

---

## Additional Resources

- **User Guide**: `docs/claude-agent-sdk-user-guide.md` - Complete API reference and patterns
- **Technical Overview**: `docs/claude-agent-sdk-technical-overview.md` - Architecture deep dive
- **Example Progression**:
  - Start: `01_basic_hello_world.py`
  - Interactive: `02_interactive_chat.py`
  - Security: `03_custom_permissions.py`
  - Monitoring: `04_hook_system.py`
  - Custom Tools: `05_mcp_sdk_servers.py`
  - Integration: `06_external_mcp_servers.py`
  - Advanced: `07_advanced_streaming.py`
  - Production: `08_production_ready.py`

---

**Last Updated**: 2025-10-18
