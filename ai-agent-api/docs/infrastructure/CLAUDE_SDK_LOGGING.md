# Claude SDK Execution Logging Guide

## Overview

The AI Agent API now includes comprehensive logging throughout the entire Claude SDK interaction flow. This allows debugging and monitoring of every step from prompt creation through tool execution and result processing.

## Log Flow

### 1. **Initial Task Execution Request**
```
[BG_TASK] Starting background task execution
  - execution_id: unique task execution identifier
  - task_id: the task being executed
  - task_name: human-readable task name
  - user_id: user who triggered execution
  - trigger_type: how task was triggered (manual, scheduled, api)
  - variables_count: number of template variables provided
  - event: "bg_task_started"
```

### 2. **Prompt Template Rendering**

#### Before Rendering
```
[BG_TASK] Rendering prompt template
  - execution_id: unique execution identifier
  - task_id: task being processed
  - task_name: task name
  - template_length: total characters in template
  - template_preview: first 200 characters of template (for debugging)
  - variables_count: number of variables to inject
  - variables_keys: list of variable names (e.g., ["cluster_context", "namespace"])
  - event: "rendering_prompt"
```

#### After Rendering
```
[BG_TASK] Prompt rendered successfully
  - execution_id: execution identifier
  - task_id: task being processed
  - task_name: task name
  - template_length: original template size
  - rendered_length: final prompt size after variable substitution
  - rendered_preview: first 300 characters of final prompt
  - event: "prompt_rendered"
```

### 3. **Claude SDK Execution Initialization**

#### Execution Start
```
[BG_TASK] Executing with Claude SDK directly
  - execution_id: execution identifier
  - task_id: task being executed
  - task_name: task name
  - prompt_length: length of prompt being sent
  - event: "claude_sdk_execution_start"
```

#### Full Prompt Logged
```
[BG_TASK] Full prompt being sent to Claude
  - execution_id: execution identifier
  - task_id: task identifier
  - prompt_preview: first 500 characters of the full prompt
  - prompt_full_length: total prompt length
  - event: "prompt_logged"
```

#### SDK Configuration
```
[BG_TASK] Claude SDK options configured
  - execution_id: execution identifier
  - model: AI model being used (e.g., "claude-opus-4")
  - permission_mode: how tool execution is handled (e.g., "acceptEdits")
  - max_turns: maximum conversation turns allowed
  - working_dir: task working directory
  - event: "sdk_options_configured"
```

### 4. **Claude Messages and Responses**

#### Claude's Text Response
```
[BG_TASK] Claude response message
  - execution_id: execution identifier
  - message_number: which message in the conversation (1, 2, 3...)
  - message_type: "AssistantMessage"
  - text_content: first 300 characters of Claude's response
  - text_length: total response length
  - event: "claude_message_received"
```

#### Tool Execution Requests
```
[BG_TASK] Claude requested tool execution
  - execution_id: execution identifier
  - message_number: conversation turn
  - tools_requested: list of tool names (e.g., ["bash", "read"])
  - tool_count: number of tools requested
  - tool_details: array of tool execution details:
    - id: tool use block ID
    - name: tool name
    - input_keys: parameter names the tool was called with
  - event: "tool_use_requested"
```

Example tool_details:
```json
[
  {
    "id": "tool_use_1",
    "name": "bash",
    "input_keys": ["command", "timeout"]
  },
  {
    "id": "tool_use_2",
    "name": "read",
    "input_keys": ["file_path"]
  }
]
```

### 5. **Execution Completion**

#### Successful Completion
```
[BG_TASK] Claude SDK execution completed successfully
  - execution_id: execution identifier
  - task_id: task identifier
  - task_name: task name
  - total_messages: total messages in conversation
  - total_tool_uses: total tools executed by Claude
  - tools_used_summary: dict of tool usage counts (e.g., {"bash": 3, "read": 2})
  - response_length: length of final response
  - response_preview: first 300 characters of final response
  - duration_ms: total execution time
  - num_turns: number of conversation turns
  - total_cost_usd: API cost of this execution
  - event: "claude_sdk_execution_complete"
```

#### Execution Results Stored
```
[BG_TASK] Execution completed successfully
  - execution_id: execution identifier
  - total_messages: total messages exchanged
  - total_tool_uses: tools executed
  - duration_ms: execution duration
  - cost_usd: API cost
  - num_turns: conversation turns
  - event: "execution_complete"
```

### 6. **Error Handling**

#### Execution Failure
```
[BG_TASK] Claude SDK execution failed
  - execution_id: execution identifier
  - task_id: task identifier
  - task_name: task name
  - error: error message
  - error_type: exception type (e.g., "APIError", "TimeoutError")
  - messages_received: how many messages were received before failure
  - tool_uses_executed: how many tools were executed before failure
  - tools_used_before_failure: dict of tools executed before error
  - event: "claude_sdk_execution_failed"
  - (includes full stack trace with exc_info=True)
```

## Log Levels

- **INFO**: Major events (task start, prompt rendering, tool requests, completion, errors)
- **DEBUG**: Detailed message information (message types, text/tool blocks)

## Example Log Sequence

Here's what a complete execution log sequence looks like:

```
2025-10-25 04:57:28,830 - app.services.task_service - INFO - [BG_TASK] Starting background task execution
  execution_id=abc123, task_id=task-001, task_name="Daily Health Check"

2025-10-25 04:57:28,831 - app.services.task_service - INFO - [BG_TASK] Rendering prompt template
  template_length=450, variables_count=2, variables_keys=["cluster", "namespace"]

2025-10-25 04:57:28,832 - app.services.task_service - INFO - [BG_TASK] Prompt rendered successfully
  rendered_length=650, rendered_preview="Perform infrastructure health check..."

2025-10-25 04:57:28,833 - app.services.task_service - INFO - [BG_TASK] Executing with Claude SDK directly
  prompt_length=650

2025-10-25 04:57:28,834 - app.services.task_service - INFO - [BG_TASK] Full prompt being sent to Claude
  prompt_preview="Perform infrastructure health check on production..."

2025-10-25 04:57:28,835 - app.services.task_service - INFO - [BG_TASK] Claude SDK options configured
  model=claude-opus-4, max_turns=15, permission_mode=acceptEdits

2025-10-25 04:57:31,120 - app.services.task_service - INFO - [BG_TASK] Claude response message
  message_number=1, text_content="I'll check the Kubernetes cluster status..."

2025-10-25 04:57:31,121 - app.services.task_service - INFO - [BG_TASK] Claude requested tool execution
  message_number=1, tools_requested=["bash"], tool_count=1
  tool_details=[{"id": "tool_1", "name": "bash", "input_keys": ["command"]}]

2025-10-25 04:57:35,500 - app.services.task_service - INFO - [BG_TASK] Claude response message
  message_number=2, text_content="Now checking pod status..."

2025-10-25 04:57:36,000 - app.services.task_service - INFO - [BG_TASK] Received final result from Claude
  duration_ms=7200, num_turns=3, total_cost_usd=0.012

2025-10-25 04:57:36,100 - app.services.task_service - INFO - [BG_TASK] Claude SDK execution completed successfully
  total_messages=4, total_tool_uses=2, tools_used_summary={"bash": 2}
  response_length=1200, num_turns=3
```

## Using These Logs for Debugging

### Find What Prompt Was Sent
Search logs for event="prompt_logged":
```
grep "prompt_logged" app.log
grep "Full prompt being sent to Claude" app.log
```

### Track Tool Execution
Search for event="tool_use_requested":
```
grep "tool_use_requested" app.log
```

### Check Execution Performance
Look for duration_ms and total_cost_usd in completion logs:
```
grep "claude_sdk_execution_complete" app.log
```

### Debug Failures
Search for event="claude_sdk_execution_failed" and note:
- How many messages were received before failure
- Which tools were executed before error
- The exact error message and type

### Monitor Token Usage
Check the tools_used_summary to see:
- Which tools Claude preferred
- How many times each tool was called
- Patterns in tool usage across executions

## Performance Insights from Logs

Extract these metrics from the completion log:
- **num_turns**: Lower is better (fewer back-and-forths with Claude)
- **total_tool_uses**: Indicates task complexity
- **duration_ms**: Total execution time
- **total_cost_usd**: API cost per task
- **tools_used_summary**: Which tools are most commonly used

Example analysis:
```
Task: Daily Health Check
  num_turns: 3 (efficient - direct execution)
  total_tool_uses: 2 (reasonable for health check)
  tools_used_summary: {"bash": 2}
  duration_ms: 7200 (7.2 seconds)
  total_cost_usd: 0.012 (under $0.02)
```

## Configuration

Logging level can be controlled in `.env`:
```bash
# Set to DEBUG for very detailed logs
LOG_LEVEL=DEBUG

# Set to INFO for production
LOG_LEVEL=INFO
```

## Related Documentation

- [Task Execution Flow](./TASK_EXECUTION_FLOW.md)
- [Claude SDK Integration](./CLAUDE_SDK_INTEGRATION.md)
- [Debugging Guide](./DEBUGGING.md)
