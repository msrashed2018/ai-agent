# Claude Agent SDK Tests

This repository contains comprehensive examples and tests for the Claude Agent SDK, demonstrating all features from basic usage to advanced production patterns.

## Prerequisites

1. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Verify Claude Code installation**:
   ```bash
   claude --version  # Should show version 2.0.0 or higher
   ```

3. **Ensure you have an Anthropic API key configured**

## Installation

1. **Install Python dependencies**:
   ```bash
   poetry install
   ```

   Or if you prefer pip:
   ```bash
   pip install claude-agent-sdk aiohttp
   ```

## Examples

### Basic Examples

1. **01_basic_hello_world.py** - Simple file creation with write_file tool
   ```bash
   poetry run python 01_basic_hello_world.py
   ```

2. **02_interactive_chat.py** - Interactive chat client with commands
   ```bash
   poetry run python 02_interactive_chat.py
   ```

### Advanced Examples

3. **03_custom_permissions.py** - Custom permission handlers and security
4. **04_hook_system.py** - Event hooks for monitoring operations
5. **05_mcp_sdk_servers.py** - SDK MCP servers with custom tools
6. **06_external_mcp_servers.py** - External MCP server configurations
7. **07_advanced_streaming.py** - Streaming, interrupts, session management
8. **08_production_ready.py** - Production patterns with error handling

### Quick Test

Run a quick functionality test:
```bash
poetry run python run_all_examples.py --quick
```

Run all examples (interactive):
```bash
poetry run python run_all_examples.py --full
```

## Project Structure

```
claude-code-sdk-tests/
├── 01_basic_hello_world.py          # Basic usage example
├── 02_interactive_chat.py           # Interactive client
├── 03_custom_permissions.py         # Security and permissions
├── 04_hook_system.py               # Hook system
├── 05_mcp_sdk_servers.py           # SDK MCP servers
├── 06_external_mcp_servers.py      # External MCP servers
├── 07_advanced_streaming.py        # Advanced streaming
├── 08_production_ready.py          # Production patterns
├── run_all_examples.py             # Test suite runner
├── workspace/                      # Working directory for examples
├── output/                         # Output files
├── logs/                          # Log files
└── temp/                          # Temporary files
```

## Key Features Demonstrated

- **Basic Query Function**: Simple one-shot interactions
- **Interactive Streaming**: Real-time bidirectional communication
- **Permission System**: Custom security controls and tool restrictions
- **Hook System**: Event interception and workflow control
- **MCP Integration**: Both SDK and external server configurations
- **Error Handling**: Comprehensive retry logic and graceful degradation
- **Session Management**: Continuation, forking, and persistence
- **Production Patterns**: Logging, metrics, configuration management

## Configuration

Examples create their own configuration as needed. For production use, see `08_production_ready.py` which demonstrates comprehensive configuration management.

## Troubleshooting

### Common Issues

1. **Claude Code not found**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Permission errors**:
   - Check file permissions in workspace directories
   - Verify Claude Code has necessary permissions

3. **API errors**:
   - Ensure Anthropic API key is configured
   - Check network connectivity

4. **Import errors**:
   - Install dependencies: `poetry install`
   - Verify Python version (3.9+)

### Debug Mode

Enable debug output in examples by modifying the ClaudeAgentOptions:
```python
options = ClaudeAgentOptions(
    extra_args={"debug-to-stderr": None},
    stderr=lambda msg: print(f"DEBUG: {msg}")
)
```

## Documentation

See the documentation files for detailed information:
- `claude-agent-sdk-technical-overview.md` - Technical architecture
- `claude-agent-sdk-user-guide.md` - Comprehensive usage guide

## License

This project is for demonstration and testing purposes.