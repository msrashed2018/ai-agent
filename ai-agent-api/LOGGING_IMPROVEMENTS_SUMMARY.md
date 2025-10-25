# Claude SDK Logging Improvements Summary

## Overview

Comprehensive logging has been added throughout the entire task execution flow to track:
- Prompt templates and rendered prompts sent to Claude
- All messages and responses from Claude
- Tool execution requests with parameters
- Execution timing and cost information
- Errors and failures with full context

## Files Modified

### 1. **app/services/task_service.py**
Enhanced logging in the Claude SDK execution flow with detailed information at each step.

#### Changes Made:

**Initial Execution Logging**
- Added task_id and task_name to execution start logs
- Logs now include full prompt preview (first 500 chars)
- Structured logging with consistent event names

**Prompt Template Rendering**
- Logs template preview before and after rendering
- Captures template length and variable keys
- Shows actual template variable substitution

**Claude SDK Initialization**
- Logs full prompt being sent to Claude
- Includes SDK options (model, permission_mode, max_turns, working_dir)
- Working directory creation details logged

**Message Processing**
- **Claude Responses**: Text content (first 300 chars) and total length logged
- **Tool Requests**: Lists all tools requested by Claude with input parameters
- **Result Messages**: Duration, turns, cost, token counts captured
- Tracks which tools were used and how many times

**Execution Completion**
- Summary includes total messages, tool uses, and tools_used_summary dictionary
- Response preview (first 300 chars) and full response length
- Total cost, duration, and number of conversation turns
- Error tracking with partial execution information

**Error Handling**
- Full exception details with execution state
- How many messages received before failure
- Which tools executed before error occurred
- Tools summary showing partial execution progress

### 2. **app/services/audit_service.py** - Bug Fix
Fixed the audit log status constraint violation issue:
- Changed task execution audit log status from "completed" to "success"
- Respects the audit log check constraint: status IN ('success', 'failure', 'denied')

**Lines Fixed:**
- Line 716: Changed `status="completed"` to `status="success"`
- Line 958: Changed `status="completed"` to `status="success"`

### 3. **docs/infrastructure/CLAUDE_SDK_LOGGING.md** (NEW)
Comprehensive documentation for the new logging system including:
- Complete log flow description
- Log levels and severity
- Examples of actual log sequences
- How to use logs for debugging
- Performance metrics from logs
- Configuration options

## Logging Additions by Phase

### Phase 1: Initial Setup
```
[BG_TASK] Starting background task execution
  - execution_id, task_id, task_name, user_id
  - trigger_type, variables_count

[BG_TASK] Rendering prompt template
  - template_preview, variables_keys
  - template_length, variables_count
```

### Phase 2: Prompt Preparation
```
[BG_TASK] Prompt rendered successfully
  - template_length → rendered_length
  - rendered_preview of final prompt

[BG_TASK] Full prompt being sent to Claude
  - Complete prompt preview (500 chars)
  - Full prompt length
```

### Phase 3: SDK Execution
```
[BG_TASK] Executing with Claude SDK directly
  - prompt_length

[BG_TASK] Claude SDK options configured
  - model, permission_mode, max_turns
  - working_dir
```

### Phase 4: Message Processing
```
[BG_TASK] Claude response message
  - message_number, text_content (300 chars)
  - text_length

[BG_TASK] Claude requested tool execution
  - tools_requested list
  - tool_details array with names and input_keys
  - tool_count
```

### Phase 5: Execution Completion
```
[BG_TASK] Received final result from Claude
  - duration_ms, num_turns, is_error
  - total_cost_usd, input_tokens, output_tokens

[BG_TASK] Claude SDK execution completed successfully
  - total_messages, total_tool_uses
  - tools_used_summary (dict with usage counts)
  - response_preview and length
  - duration_ms, num_turns, total_cost_usd
```

## Log Output Examples

### Successful Execution Log Sequence
```
2025-10-25 04:57:28,830 - INFO - [BG_TASK] Starting background task execution
  execution_id=abc123, task_id=task-001, task_name=Daily Health Check
  user_id=user123, trigger_type=manual, variables_count=2

2025-10-25 04:57:28,831 - INFO - [BG_TASK] Rendering prompt template
  template_length=450, variables_keys=["cluster", "namespace"]
  template_preview="Perform infrastructure health check..."

2025-10-25 04:57:28,832 - INFO - [BG_TASK] Prompt rendered successfully
  template_length=450, rendered_length=650
  rendered_preview="Perform health check on cluster: production..."

2025-10-25 04:57:28,833 - INFO - [BG_TASK] Executing with Claude SDK directly
  prompt_length=650

2025-10-25 04:57:28,834 - INFO - [BG_TASK] Full prompt being sent to Claude
  prompt_preview="Perform health check on cluster: production..."
  prompt_full_length=650

2025-10-25 04:57:28,835 - INFO - [BG_TASK] Claude SDK options configured
  model=claude-opus-4, permission_mode=acceptEdits
  max_turns=15, working_dir=/tmp/agent-workdirs/active/task-001

2025-10-25 04:57:31,120 - INFO - [BG_TASK] Claude response message
  message_number=1, message_type=AssistantMessage
  text_content="I'll check the Kubernetes cluster status..."
  text_length=245

2025-10-25 04:57:31,121 - INFO - [BG_TASK] Claude requested tool execution
  message_number=1, tools_requested=["bash"]
  tool_count=1
  tool_details=[{"id":"tool_1","name":"bash","input_keys":["command"]}]

2025-10-25 04:57:35,500 - INFO - [BG_TASK] Claude response message
  message_number=2, message_type=AssistantMessage
  text_content="Now checking pod status..."
  text_length=156

2025-10-25 04:57:36,000 - INFO - [BG_TASK] Received final result from Claude
  duration_ms=7200, num_turns=3, is_error=false
  total_cost_usd=0.012, input_tokens=450, output_tokens=320

2025-10-25 04:57:36,100 - INFO - [BG_TASK] Claude SDK execution completed successfully
  task_id=task-001, task_name=Daily Health Check
  total_messages=4, total_tool_uses=2
  tools_used_summary={"bash": 2}
  response_length=1200, response_preview="The cluster appears healthy..."
  duration_ms=7200, num_turns=3, total_cost_usd=0.012
```

## Debugging Tips

### Find Exact Prompts Sent
```bash
grep "Full prompt being sent to Claude" app.log | head -5
grep "prompt_preview" app.log
```

### Track Tool Execution
```bash
grep "Claude requested tool execution" app.log
grep "tools_used_summary" app.log
```

### Performance Analysis
```bash
grep "claude_sdk_execution_complete" app.log | jq '.duration_ms, .total_cost_usd'
```

### Identify Failures
```bash
grep "claude_sdk_execution_failed" app.log
grep -A5 "Background task execution failed" app.log
```

## Bug Fixed

### Audit Log Status Constraint Violation
**Issue**: Task execution logs were failing with:
```
violates check constraint "ck_audit_logs_chk_audit_status"
DETAIL: status='completed' is not valid
```

**Root Cause**: Audit log table has check constraint:
```sql
status IN ('success', 'failure', 'denied') OR status IS NULL
```

But code was inserting `status='completed'`.

**Solution**: Changed audit log status to `'success'` to match constraint.

**Files Modified**:
- app/services/task_service.py:716 - First occurrence
- app/services/task_service.py:958 - Second occurrence

## Configuration

Set log level in `.env`:
```bash
LOG_LEVEL=INFO      # Production (fewer logs)
LOG_LEVEL=DEBUG     # Development (very detailed)
```

## Related Documentation

- [Claude SDK Logging Guide](./docs/infrastructure/CLAUDE_SDK_LOGGING.md)
- [Task Execution Architecture](./docs/architecture/)
- [Debugging Guide](./docs/infrastructure/)

## Event Types for Structured Logging

All logs use consistent event types for easy filtering:
- `claude_sdk_execution_start` - SDK execution beginning
- `prompt_logged` - Full prompt sent to Claude
- `sdk_options_configured` - SDK options set
- `claude_message_received` - Text response from Claude
- `tool_use_requested` - Claude requested tool execution
- `final_result_received` - Final result with metadata
- `claude_sdk_execution_complete` - Successful completion
- `claude_sdk_execution_failed` - Execution failure

Search by event: `grep "event.*claude_sdk" app.log`
