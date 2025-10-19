# Claude Agent SDK - User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Usage Patterns](#usage-patterns)
6. [Configuration Options](#configuration-options)
7. [Tool Management](#tool-management)
8. [Permission System](#permission-system)
9. [Hook System](#hook-system)
10. [MCP Server Integration](#mcp-server-integration)
11. [Error Handling](#error-handling)
12. [Advanced Features](#advanced-features)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

## Introduction

The Claude Agent SDK is a Python library that enables you to build AI-powered applications using Claude Code. It provides two main interfaces:

- **`query()`**: Simple, one-shot interactions perfect for automation and batch processing
- **`ClaudeSDKClient`**: Full-featured streaming client for interactive applications

The SDK communicates with Claude Code (the CLI version of Claude) to provide capabilities like:

- Code execution (Python, Bash, etc.)
- File system operations
- Tool integration via Model Context Protocol (MCP)
- Custom permission handling
- Event hooks for workflow control

## Installation

### Prerequisites

1. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Install the Python SDK**:
   ```bash
   pip install claude-agent-sdk
   ```

3. **Verify installation**:
   ```bash
   claude --version  # Should show version 2.0.0 or higher
   ```

## Quick Start

### Simple Query Example

```python
import asyncio
from claude_agent_sdk import query

async def main():
    # Simple one-shot question
    async for message in query(prompt="What is 2 + 2?"):
        print(f"Type: {type(message).__name__}")
        if hasattr(message, 'content'):
            print(f"Content: {message.content}")

asyncio.run(main())
```

### Interactive Client Example

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock

async def main():
    async with ClaudeSDKClient() as client:
        # Send a message
        await client.query("Hello, can you help me with Python?")
        
        # Receive the response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

asyncio.run(main())
```

## Core Concepts

### Message Types

The SDK uses strongly-typed message objects:

- **`UserMessage`**: Your inputs to Claude
- **`AssistantMessage`**: Claude's responses
- **`SystemMessage`**: System notifications and metadata
- **`ResultMessage`**: Final results with cost and usage information
- **`StreamEvent`**: Partial updates during streaming (optional)

### Content Blocks

Messages contain content blocks of different types:

- **`TextBlock`**: Regular text content
- **`ThinkingBlock`**: Claude's reasoning process
- **`ToolUseBlock`**: Tool invocation requests  
- **`ToolResultBlock`**: Tool execution results

### Options Configuration

Use `ClaudeAgentOptions` to configure behavior:

```python
from claude_agent_sdk import ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    permission_mode="acceptEdits",
    cwd="/path/to/project",
    allowed_tools=["python", "bash", "read_file"]
)

async for message in query(prompt="Analyze this codebase", options=options):
    print(message)
```

## Usage Patterns

### 1. One-Shot Queries (query function)

Best for: Automation, batch processing, simple questions

```python
from claude_agent_sdk import query, ClaudeAgentOptions

# Basic usage
async def simple_query():
    async for message in query(prompt="Explain Python decorators"):
        print(message)

# With configuration
async def configured_query():
    options = ClaudeAgentOptions(
        system_prompt="You are a Python expert. Be concise.",
        allowed_tools=["python"],
        permission_mode="acceptEdits"
    )
    
    async for message in query(
        prompt="Create a simple web server",
        options=options
    ):
        print(message)

# Batch processing
async def batch_process():
    prompts = [
        "What is machine learning?",
        "Explain neural networks",
        "What is deep learning?"
    ]
    
    for prompt in prompts:
        print(f"\n--- Processing: {prompt} ---")
        async for message in query(prompt=prompt):
            if hasattr(message, 'content'):
                print(message.content)
```

### 2. Interactive Conversations (ClaudeSDKClient)

Best for: Chat interfaces, debugging sessions, multi-turn conversations

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage

async def interactive_session():
    options = ClaudeAgentOptions(
        permission_mode="default",  # Prompt for dangerous operations
        cwd="/home/user/project"
    )
    
    async with ClaudeSDKClient(options=options) as client:
        # First interaction
        await client.query("Help me debug this Python script")
        
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                print(f"Cost: ${message.total_cost_usd:.4f}")
                break  # Response complete
        
        # Follow-up interaction
        await client.query("Now run the fixed script")
        
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
            elif isinstance(message, ResultMessage):
                break

# Chat loop example
async def chat_loop():
    async with ClaudeSDKClient() as client:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            await client.query(user_input)
            
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                elif isinstance(message, ResultMessage):
                    break
```

### 3. Streaming Mode

For real-time applications with continuous input:

```python
async def streaming_example():
    async def message_stream():
        # Send multiple messages over time
        yield {
            "type": "user",
            "message": {"role": "user", "content": "Start a coding session"},
            "session_id": "coding_session"
        }
        
        await asyncio.sleep(1)  # Simulate delay
        
        yield {
            "type": "user", 
            "message": {"role": "user", "content": "Create a simple calculator"},
            "session_id": "coding_session"
        }
    
    async with ClaudeSDKClient() as client:
        await client.connect(prompt=message_stream())
        
        async for message in client.receive_messages():
            print(f"Received: {type(message).__name__}")
            # Handle messages as they arrive
```

## Configuration Options

### ClaudeAgentOptions Reference

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    # Model Configuration
    model="claude-sonnet-4-5",  # or "claude-opus-4-1-20250805", etc.
    system_prompt="You are a helpful assistant",
    
    # Tool Management
    allowed_tools=["python", "bash", "read_file", "write_file"],
    disallowed_tools=["dangerous_tool"],
    
    # Permission System
    permission_mode="default",  # "default", "acceptEdits", "bypassPermissions"
    
    # Session Management
    continue_conversation=False,
    resume="session_id_to_resume",
    max_turns=10,
    
    # Environment
    cwd="/path/to/working/directory",
    cli_path="/custom/path/to/claude",
    env={"CUSTOM_VAR": "value"},
    
    # Advanced
    include_partial_messages=True,  # Stream partial responses
    fork_session=True,  # Create new session when resuming
    max_buffer_size=2048000,  # 2MB buffer limit
)
```

### System Prompt Options

```python
# String system prompt
options = ClaudeAgentOptions(
    system_prompt="You are an expert Python developer"
)

# Preset with append
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset", 
        "preset": "claude_code",
        "append": "Focus on clean, well-documented code"
    }
)
```

### Working Directory and Environment

```python
options = ClaudeAgentOptions(
    cwd="/home/user/my_project",
    env={
        "PYTHONPATH": "/custom/python/path",
        "DEBUG": "true"
    },
    add_dirs=["/additional/context/dir"]
)
```

## Tool Management

### Allowed and Disallowed Tools

```python
# Restrict to specific tools
options = ClaudeAgentOptions(
    allowed_tools=["python", "read_file", "write_file"]
)

# Allow all except specific tools
options = ClaudeAgentOptions(
    disallowed_tools=["bash", "dangerous_command"]
)

# Common tool combinations
web_dev_tools = ["python", "bash", "read_file", "write_file", "browser"]
data_science_tools = ["python", "read_file", "write_file", "jupyter"]
safe_tools = ["python", "read_file"]  # No file writes or shell access
```

### Tool Usage Examples

```python
async def tool_usage_examples():
    # Python-only environment
    python_options = ClaudeAgentOptions(allowed_tools=["python"])
    async for msg in query("Calculate fibonacci numbers", options=python_options):
        print(msg)
    
    # Web development environment
    web_options = ClaudeAgentOptions(
        allowed_tools=["python", "bash", "read_file", "write_file", "browser"],
        cwd="/path/to/web/project"
    )
    async for msg in query("Create a Flask web app", options=web_options):
        print(msg)
    
    # Read-only analysis
    readonly_options = ClaudeAgentOptions(
        allowed_tools=["python", "read_file"],
        permission_mode="default"
    )
    async for msg in query("Analyze this codebase", options=readonly_options):
        print(msg)
```

## Permission System

### Permission Modes

```python
# Default: Prompt user for dangerous operations
options = ClaudeAgentOptions(permission_mode="default")

# Auto-accept file edits (but prompt for other dangerous operations)
options = ClaudeAgentOptions(permission_mode="acceptEdits") 

# Allow all operations without prompting (use with caution!)
options = ClaudeAgentOptions(permission_mode="bypassPermissions")
```

### Custom Permission Callbacks

```python
from claude_agent_sdk import (
    ClaudeAgentOptions, PermissionResultAllow, PermissionResultDeny,
    ToolPermissionContext
)

async def custom_permission_handler(
    tool_name: str, 
    input_data: dict, 
    context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Custom permission logic."""
    
    # Always allow safe tools
    if tool_name in ["python", "read_file"]:
        return PermissionResultAllow()
    
    # Block dangerous bash commands
    if tool_name == "bash":
        command = input_data.get("command", "")
        dangerous_commands = ["rm ", "sudo", "chmod 777", "> /dev/"]
        
        if any(cmd in command for cmd in dangerous_commands):
            return PermissionResultDeny(
                message=f"Dangerous command blocked: {command}",
                interrupt=True
            )
    
    # Allow file writes in specific directories only
    if tool_name == "write_file":
        file_path = input_data.get("path", "")
        allowed_dirs = ["/tmp/", "/home/user/safe_area/"]
        
        if not any(file_path.startswith(dir) for dir in allowed_dirs):
            return PermissionResultDeny(
                message=f"File write not allowed in: {file_path}"
            )
    
    # Default: allow
    return PermissionResultAllow()

# Use custom permission handler
options = ClaudeAgentOptions(can_use_tool=custom_permission_handler)

# Note: custom permission callbacks require streaming mode
async with ClaudeSDKClient(options=options) as client:
    await client.query("Write a Python script to /tmp/test.py")
    async for message in client.receive_response():
        print(message)
```

### Dynamic Permission Updates

```python
async def dynamic_permissions():
    async with ClaudeSDKClient() as client:
        # Start restrictive
        await client.set_permission_mode("default")
        await client.query("Analyze this code for security issues")
        
        # Switch to auto-accept after analysis
        await client.set_permission_mode("acceptEdits") 
        await client.query("Now fix the security issues you found")
```

## Hook System

Hooks allow you to intercept and modify SDK behavior at specific events.

### Available Hook Events

- **`PreToolUse`**: Before tool execution
- **`PostToolUse`**: After tool execution  
- **`UserPromptSubmit`**: When user submits input
- **`Stop`**: When execution stops
- **`SubagentStop`**: When subagent stops
- **`PreCompact`**: Before conversation compacting

### Hook Examples

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

async def pre_tool_hook(input_data, tool_use_id, context):
    """Log all tool usage."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})
    
    print(f"About to use tool: {tool_name}")
    print(f"Input: {tool_input}")
    
    # Allow execution to continue
    return {
        "continue_": True,
        "suppressOutput": False
    }

async def post_tool_hook(input_data, tool_use_id, context):
    """Log tool results."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_response = input_data.get("tool_response", {})
    
    print(f"Tool {tool_name} completed")
    print(f"Response: {tool_response}")
    
    return {"continue_": True}

# Configure hooks
hook_matcher = HookMatcher(
    matcher="python|bash",  # Match Python or Bash tools
    hooks=[pre_tool_hook, post_tool_hook]
)

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [hook_matcher],
        "PostToolUse": [hook_matcher]
    }
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Write and run a Python script")
    async for message in client.receive_response():
        print(message)
```

### Advanced Hook Examples

```python
async def validation_hook(input_data, tool_use_id, context):
    """Validate and modify tool inputs."""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name == "python":
        code = tool_input.get("code", "")
        
        # Block dangerous operations
        if "os.system" in code or "subprocess" in code:
            return {
                "continue_": False,
                "decision": "block",
                "systemMessage": "Dangerous code execution blocked",
                "reason": "Code contains potentially dangerous operations"
            }
        
        # Modify code to add safety checks
        safe_code = f"""
import sys
# Safety: limit execution time
sys.settrace(lambda *args: None)  # Disable debugging

{code}
"""
        
        return {
            "continue_": True,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**tool_input, "code": safe_code}
            }
        }
    
    return {"continue_": True}

async def audit_hook(input_data, tool_use_id, context):
    """Audit all user inputs."""
    prompt = input_data.get("prompt", "")
    
    # Log to audit file
    with open("/var/log/claude_audit.log", "a") as f:
        f.write(f"User prompt: {prompt}\n")
    
    return {"continue_": True}

# Set up comprehensive hooks
validation_matcher = HookMatcher(matcher="python", hooks=[validation_hook])
audit_matcher = HookMatcher(hooks=[audit_hook])

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [validation_matcher],
        "UserPromptSubmit": [audit_matcher]
    }
)
```

## MCP Server Integration

The SDK supports both in-process SDK servers and external MCP servers.

### Creating SDK MCP Servers

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

# Define tools with the @tool decorator
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args):
    """Safe calculator tool."""
    try:
        # Simple expression evaluation (be careful with eval in production!)
        result = eval(args["expression"])
        return {
            "content": [{"type": "text", "text": f"Result: {result}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True
        }

@tool("get_weather", "Get weather information", {"city": str})
async def get_weather(args):
    """Mock weather tool."""
    city = args["city"]
    return {
        "content": [{"type": "text", "text": f"Weather in {city}: Sunny, 72°F"}]
    }

@tool("file_stats", "Get file statistics", {"path": str})
async def file_stats(args):
    """Get file information."""
    import os
    path = args["path"]
    
    try:
        stat = os.stat(path)
        return {
            "content": [{
                "type": "text", 
                "text": f"File: {path}\nSize: {stat.st_size} bytes\nModified: {stat.st_mtime}"
            }]
        }
    except FileNotFoundError:
        return {
            "content": [{"type": "text", "text": f"File not found: {path}"}],
            "is_error": True
        }

# Create server
my_tools_server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0", 
    tools=[calculate, get_weather, file_stats]
)

# Use in configuration
options = ClaudeAgentOptions(
    mcp_servers={"my_tools": my_tools_server},
    allowed_tools=["calculate", "get_weather", "file_stats"]
)

async for message in query("Calculate 15 * 23 and get weather for NYC", options=options):
    print(message)
```

### Complex Tool Examples

```python
# Database tool
@tool("query_db", "Query database", {"sql": str, "database": str})
async def query_database(args):
    """Execute SQL queries safely."""
    sql = args["sql"].lower().strip()
    database = args["database"]
    
    # Security: only allow SELECT queries
    if not sql.startswith("select"):
        return {
            "content": [{"type": "text", "text": "Only SELECT queries allowed"}],
            "is_error": True
        }
    
    # Mock database query
    if "users" in sql:
        result = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    else:
        result = [{"message": "No data found"}]
    
    return {
        "content": [{"type": "text", "text": f"Query result: {result}"}]
    }

# HTTP request tool  
@tool("http_request", "Make HTTP requests", {"url": str, "method": str})
async def http_request(args):
    """Make safe HTTP requests."""
    import aiohttp
    
    url = args["url"]
    method = args.get("method", "GET").upper()
    
    # Security: only allow requests to safe domains
    allowed_domains = ["api.example.com", "httpbin.org"]
    if not any(domain in url for domain in allowed_domains):
        return {
            "content": [{"type": "text", "text": "Domain not allowed"}],
            "is_error": True
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url) as response:
                text = await response.text()
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"Status: {response.status}\nResponse: {text[:500]}"
                    }]
                }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Request failed: {str(e)}"}],
            "is_error": True
        }

# Create comprehensive server
advanced_server = create_sdk_mcp_server(
    name="advanced_tools",
    tools=[query_database, http_request]
)
```

### External MCP Servers

```python
# Configure external MCP servers alongside SDK servers
options = ClaudeAgentOptions(
    mcp_servers={
        # SDK server (in-process)
        "my_tools": my_tools_server,
        
        # External stdio server
        "filesystem": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem", "/path/to/files"]
        },
        
        # External server with environment
        "git": {
            "command": "mcp-server-git",
            "args": ["--repository", "/path/to/repo"],
            "env": {"GIT_CONFIG": "/custom/git/config"}
        },
        
        # SSE server
        "remote_tools": {
            "type": "sse",
            "url": "https://api.example.com/mcp",
            "headers": {"Authorization": "Bearer token123"}
        }
    }
)
```

## Error Handling

### Exception Types

```python
from claude_agent_sdk import (
    ClaudeSDKError, CLIConnectionError, CLINotFoundError, 
    ProcessError, CLIJSONDecodeError
)

async def error_handling_example():
    try:
        async for message in query("Hello"):
            print(message)
            
    except CLINotFoundError:
        print("Claude Code not installed. Run: npm install -g @anthropic-ai/claude-code")
        
    except CLIConnectionError as e:
        print(f"Connection failed: {e}")
        
    except ProcessError as e:
        print(f"Claude Code process error: {e}")
        print(f"Exit code: {e.exit_code}")
        print(f"Stderr: {e.stderr}")
        
    except CLIJSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Problematic line: {e.line}")
        
    except ClaudeSDKError as e:
        print(f"General SDK error: {e}")
```

### Robust Error Handling

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, CLIConnectionError

async def robust_client():
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with ClaudeSDKClient() as client:
                await client.query("Hello, Claude!")
                
                async for message in client.receive_response():
                    print(message)
                    
                break  # Success, exit retry loop
                
        except CLIConnectionError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("All attempts failed")
                raise
```

## Advanced Features

### Session Management

```python
# Continue previous conversation
options = ClaudeAgentOptions(
    continue_conversation=True,
    resume="previous_session_id"
)

# Fork session (create new session based on previous one)
options = ClaudeAgentOptions(
    resume="previous_session_id",
    fork_session=True
)

# Limit conversation length
options = ClaudeAgentOptions(max_turns=5)

async def session_management():
    # Start new session
    async with ClaudeSDKClient() as client:
        await client.query("Start analyzing this project")
        
        # Get session info
        server_info = await client.get_server_info()
        print(f"Session capabilities: {server_info}")
        
        async for message in client.receive_response():
            print(message)
```

### Model Switching

```python
async def model_switching():
    async with ClaudeSDKClient() as client:
        # Start with Sonnet
        await client.set_model("claude-sonnet-4-5")
        await client.query("Explain this complex algorithm")
        
        async for message in client.receive_response():
            print(message)
        
        # Switch to Opus for implementation
        await client.set_model("claude-opus-4-1-20250805")
        await client.query("Now implement the algorithm")
        
        async for message in client.receive_response():
            print(message)
```

### Interruption and Control

```python
async def interruption_example():
    async with ClaudeSDKClient() as client:
        # Start long-running task
        await client.query("Process this large dataset and generate report")
        
        # Set up timeout
        timeout_task = asyncio.create_task(asyncio.sleep(30))
        response_task = asyncio.create_task(
            [msg async for msg in client.receive_response()][-1]
        )
        
        done, pending = await asyncio.wait(
            [timeout_task, response_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if timeout_task in done:
            print("Operation timed out, interrupting...")
            await client.interrupt()
            
            # Cancel pending task
            for task in pending:
                task.cancel()
        else:
            print("Operation completed successfully")
```

### Partial Message Streaming

```python
async def partial_streaming():
    options = ClaudeAgentOptions(include_partial_messages=True)
    
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Write a long story")
        
        async for message in client.receive_messages():
            if isinstance(message, StreamEvent):
                # Handle partial updates
                print(f"Partial: {message.event}")
            else:
                # Handle complete messages
                print(f"Complete: {message}")
```

### Agent Definitions

```python
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

# Define custom agents
agents = {
    "code_reviewer": AgentDefinition(
        description="Expert code reviewer",
        prompt="You are an expert code reviewer. Focus on security, performance, and best practices.",
        tools=["python", "read_file"],
        model="sonnet"
    ),
    
    "documentation_writer": AgentDefinition(
        description="Technical documentation specialist", 
        prompt="You are a technical writer. Create clear, comprehensive documentation.",
        tools=["read_file", "write_file"],
        model="sonnet"
    )
}

options = ClaudeAgentOptions(agents=agents)

# Use specific agent (would be activated via Claude Code commands)
async for message in query("Review this code", options=options):
    print(message)
```

## Best Practices

### 1. Choose the Right Interface

```python
# Use query() for:
# - Simple automation tasks
# - Batch processing
# - One-shot questions
# - When you don't need interactivity

async def automation_example():
    files = ["file1.py", "file2.py", "file3.py"]
    
    for file in files:
        async for msg in query(f"Analyze {file} for bugs"):
            if hasattr(msg, 'content'):
                print(f"{file}: {msg.content}")

# Use ClaudeSDKClient for:
# - Interactive applications
# - Multi-turn conversations
# - When you need interrupts
# - Dynamic conversation control

async def interactive_example():
    async with ClaudeSDKClient() as client:
        while True:
            user_input = input("Query: ")
            await client.query(user_input)
            # Handle response...
```

### 2. Configure Permissions Appropriately

```python
# For automation: use restrictive permissions
automation_options = ClaudeAgentOptions(
    permission_mode="default",  # Prompt for dangerous operations
    allowed_tools=["python", "read_file"]  # No writes or shell access
)

# For interactive development: use moderate permissions
dev_options = ClaudeAgentOptions(
    permission_mode="acceptEdits",  # Auto-accept file edits
    allowed_tools=["python", "bash", "read_file", "write_file"]
)

# For trusted environments: use permissive settings
trusted_options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",  # Allow all operations
    # Don't restrict tools
)
```

### 3. Handle Errors Gracefully

```python
async def robust_implementation():
    options = ClaudeAgentOptions(
        max_buffer_size=2048000,  # Increase buffer for large responses
        stderr=lambda msg: print(f"Claude stderr: {msg}")  # Monitor stderr
    )
    
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query("Complex task")
            
            async for message in client.receive_response():
                print(message)
                
    except Exception as e:
        print(f"Error: {e}")
        # Implement fallback or retry logic
```

### 4. Use Appropriate Working Directories

```python
# Set working directory for file operations
options = ClaudeAgentOptions(
    cwd="/path/to/project",
    add_dirs=["/additional/context"]  # Add context directories
)

# Ensure directory exists
import os
project_dir = "/path/to/project"
if not os.path.exists(project_dir):
    os.makedirs(project_dir)
    
options = ClaudeAgentOptions(cwd=project_dir)
```

### 5. Optimize for Performance

```python
# For long conversations: enable partial messages
streaming_options = ClaudeAgentOptions(
    include_partial_messages=True,
    max_buffer_size=4096000  # Larger buffer for streaming
)

# For batch processing: disable unnecessary features
batch_options = ClaudeAgentOptions(
    include_partial_messages=False,  # Reduce overhead
    max_turns=1  # Limit conversation length
)
```

## Troubleshooting

### Common Issues

#### 1. Claude Code Not Found

```bash
# Error: CLINotFoundError
# Solution: Install Claude Code
npm install -g @anthropic-ai/claude-code

# Or specify custom path
options = ClaudeAgentOptions(cli_path="/custom/path/to/claude")
```

#### 2. Permission Denied Errors

```python
# Error: Permission denied for tool execution
# Solution: Adjust permission mode
options = ClaudeAgentOptions(
    permission_mode="acceptEdits",  # or "bypassPermissions"
    allowed_tools=["python", "bash", "read_file", "write_file"]
)
```

#### 3. JSON Decode Errors

```python
# Error: CLIJSONDecodeError
# Solution: Increase buffer size
options = ClaudeAgentOptions(
    max_buffer_size=4096000,  # Increase from default 1MB
    stderr=lambda msg: print(f"Debug: {msg}")  # Monitor for clues
)
```

#### 4. Process Timeout

```python
# Error: Process hangs or times out
# Solution: Use interrupts and timeouts
async def with_timeout():
    async with ClaudeSDKClient() as client:
        try:
            await asyncio.wait_for(
                client.query("Long running task"),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            await client.interrupt()
            print("Task interrupted due to timeout")
```

#### 5. Working Directory Issues

```python
# Error: File not found or permission errors
# Solution: Verify directory exists and permissions
import os

cwd = "/path/to/project"
if not os.path.exists(cwd):
    print(f"Directory does not exist: {cwd}")
    os.makedirs(cwd, exist_ok=True)

if not os.access(cwd, os.R_OK | os.W_OK):
    print(f"Insufficient permissions for: {cwd}")

options = ClaudeAgentOptions(cwd=cwd)
```

### Debug Mode

```python
# Enable debug output
options = ClaudeAgentOptions(
    extra_args={"debug-to-stderr": None},  # Enable debug mode
    stderr=lambda msg: print(f"DEBUG: {msg}")  # Capture debug output
)

# Or use file logging
import sys
debug_file = open("/tmp/claude_debug.log", "w")
options = ClaudeAgentOptions(
    extra_args={"debug-to-stderr": None},
    debug_stderr=debug_file  # Legacy: write to file
)
```

### Version Compatibility

```python
# Check Claude Code version
import subprocess

try:
    result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
    print(f"Claude Code version: {result.stdout.strip()}")
except FileNotFoundError:
    print("Claude Code not installed")

# Skip version check if needed (not recommended)
import os
os.environ["CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"] = "1"
```

This user guide provides comprehensive coverage of the Claude Agent SDK's capabilities. Start with the Quick Start section for immediate usage, then explore the specific features and patterns that match your use case. The SDK is designed to be flexible and powerful while maintaining safety through its permission system and error handling.