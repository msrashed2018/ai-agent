# Complete Session Message Flow Documentation

## Overview
This document explains the complete flow of sending a message to Claude Code through the AI Agent API, including what prompt is sent to the SDK, how tools are tracked, and how to retrieve all interaction data.

---

## 🔄 Complete Message Flow

### **Step 1: Send Message to Session**

**Endpoint:** `POST /api/v1/sessions/{session_id}/query`

**Request:**
```json
{
  "message": "Create a Python file that calculates fibonacci numbers",
  "fork": false
}
```

**What Happens:**

1. **Session Validation** ✅
   - Verifies session exists
   - Checks user ownership
   - Validates session status (must be `created` or `active`)

2. **Status Transition** ✅
   - Session: `created` → `active` → `processing`

3. **SDK Client Initialization** (First message only) ✅
   ```python
   # Build MCP configuration
   mcp_config = {
       "kubernetes_readonly": {...},  # SDK built-in MCP server
       "database": {...},              # SDK built-in MCP server  
       "monitoring": {...},            # SDK built-in MCP server
       "user-mcp-server-1": {...},    # User's personal MCP servers
       # ... any other user/global MCP servers
   }
   
   # Create ClaudeAgentOptions
   options = ClaudeAgentOptions(
       model="claude-3-5-sonnet-20241022",
       max_turns=20,
       allowed_tools=["*"],
       permission_mode="default",
       cwd="/tmp/ai-agent-service/sessions/{session_id}",
       mcp_servers=mcp_config,
       system_prompt=None,  # Or custom if provided
       hooks={
           "PreToolUse": [audit_hook, tool_tracking_hook],
           "PostToolUse": [cost_tracking_hook],
           ...
       },
       can_use_tool=permission_callback,  # For security checks
   )
   
   # Connect to Claude Code CLI
   client = ClaudeSDKClient(options=options)
   await client.connect(prompt=None)  # Streaming mode
   ```

4. **Send Message to SDK** ✅
   ```python
   # This sends your message to Claude Code CLI
   await client.query("Create a Python file that calculates fibonacci numbers")
   ```

   **Actual CLI Command Executed Under the Hood:**
   ```bash
   claude --mode agent \
     --model claude-3-5-sonnet-20241022 \
     --max-turns 20 \
     --cwd /tmp/ai-agent-service/sessions/{session_id} \
     --mcp-server kubernetes_readonly \
     --mcp-server database \
     --mcp-server monitoring \
     --mcp-server user-mcp-server-1
   # ... (SDK manages this via subprocess)
   ```

5. **Process Response Stream** ✅
   - SDK returns async stream of messages
   - MessageProcessor parses each message
   - Stores to database in real-time
   - Broadcasts to WebSocket subscribers

---

## 📊 Message Types & Content Structure

### **1. User Message**
```json
{
  "id": "uuid-1",
  "session_id": "session-uuid",
  "message_type": "user",
  "sequence": 1,
  "content": {
    "text": "Create a Python file that calculates fibonacci numbers"
  },
  "created_at": "2025-10-18T01:00:00Z"
}
```

### **2. Assistant Message (with Thinking & Tool Use)**
```json
{
  "id": "uuid-2",
  "session_id": "session-uuid",
  "message_type": "assistant",
  "sequence": 2,
  "content": {
    "content": [
      {
        "type": "thinking",
        "thinking": "I need to create a Python file for fibonacci calculation. First, I'll use write_file tool to create the file.",
        "signature": "sig-abc123"
      },
      {
        "type": "tool_use",
        "id": "tool_use_1",
        "name": "write_file",
        "input": {
          "path": "fibonacci.py",
          "content": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nif __name__ == '__main__':\n    print(fibonacci(10))"
        }
      }
    ]
  },
  "token_count": 150,
  "cost_usd": 0.00045,
  "created_at": "2025-10-18T01:00:01Z"
}
```

### **3. Tool Result Message**
```json
{
  "id": "uuid-3",
  "session_id": "session-uuid",
  "message_type": "result",
  "sequence": 3,
  "content": {
    "content": [
      {
        "type": "tool_result",
        "tool_use_id": "tool_use_1",
        "content": "File written successfully: fibonacci.py",
        "is_error": false
      }
    ]
  },
  "created_at": "2025-10-18T01:00:02Z"
}
```

### **4. Final Assistant Message**
```json
{
  "id": "uuid-4",
  "session_id": "session-uuid",
  "message_type": "assistant",
  "sequence": 4,
  "content": {
    "content": [
      {
        "type": "text",
        "text": "I've created a Python file called fibonacci.py that calculates Fibonacci numbers recursively. The file is ready in your working directory."
      }
    ]
  },
  "token_count": 50,
  "cost_usd": 0.00015,
  "created_at": "2025-10-18T01:00:03Z"
}
```

---

## 🔧 Tool Call Tracking

Every tool use is tracked separately in the `tool_calls` table:

```json
{
  "id": "tool-call-uuid",
  "session_id": "session-uuid",
  "tool_use_message_id": "uuid-2",
  "tool_result_message_id": "uuid-3",
  "tool_name": "write_file",
  "tool_input": {
    "path": "fibonacci.py",
    "content": "def fibonacci(n):\n..."
  },
  "tool_output": {
    "content": "File written successfully: fibonacci.py",
    "is_error": false
  },
  "status": "success",
  "error_message": null,
  "started_at": "2025-10-18T01:00:01Z",
  "completed_at": "2025-10-18T01:00:02Z",
  "duration_ms": 1000
}
```

---

## 📡 API Endpoints to Retrieve Data

### **1. Get All Messages in Session**
```bash
GET /api/v1/sessions/{session_id}/messages?limit=50
```

**Response:**
```json
[
  {
    "id": "uuid-4",
    "message_type": "assistant",
    "content": {...},
    "sequence": 4,
    "created_at": "2025-10-18T01:00:03Z"
  },
  {
    "id": "uuid-3",
    "message_type": "result",
    "content": {...},
    "sequence": 3,
    "created_at": "2025-10-18T01:00:02Z"
  },
  // ... ordered newest first
]
```

### **2. Get Specific Message with Thinking & Tool Use**
```bash
GET /api/v1/sessions/{session_id}/messages/{message_id}
```

**Response includes:**
- `content.content[].type = "thinking"` - Claude's reasoning
- `content.content[].type = "tool_use"` - Tool invocations
- `content.content[].type = "text"` - Text responses

### **3. Get All Tool Calls in Session**
```bash
GET /api/v1/sessions/{session_id}/tool-calls
```

**Response:**
```json
[
  {
    "id": "tool-call-uuid",
    "tool_name": "write_file",
    "tool_input": {...},
    "tool_output": {...},
    "status": "success",
    "duration_ms": 1000,
    "started_at": "2025-10-18T01:00:01Z",
    "completed_at": "2025-10-18T01:00:02Z"
  },
  // ... all tool calls in chronological order
]
```

### **4. Stream Messages in Real-Time**
```bash
GET /api/v1/sessions/{session_id}/stream
```

**WebSocket connection that streams:**
- Messages as they arrive
- Tool executions in real-time
- Thinking blocks as Claude reasons
- Status updates

---

## 🎯 Complete Example Flow

### **Request:**
```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all pods in the default namespace and save to a file"
  }'
```

### **What Gets Sent to Claude Code SDK:**

```python
# 1. ClaudeAgentOptions configuration
options = {
    "model": "claude-3-5-sonnet-20241022",
    "max_turns": 20,
    "allowed_tools": ["*"],
    "permission_mode": "default",
    "cwd": "/tmp/ai-agent-service/sessions/abc-123",
    "mcp_servers": {
        "kubernetes_readonly": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-kubernetes-readonly"],
            "env": {}
        },
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/ai-agent-service/sessions/abc-123"],
            "env": {}
        }
    },
    "system_prompt": None,  # Or custom if provided
    "hooks": {
        "PreToolUse": [...],   # For audit logging
        "PostToolUse": [...],  # For cost tracking
    },
    "can_use_tool": <permission_callback>  # For security
}

# 2. Actual message sent
await client.query("List all pods in the default namespace and save to a file")
```

### **Claude's Thinking & Tool Use:**

**Message 1: User**
```
"List all pods in the default namespace and save to a file"
```

**Message 2: Assistant (with thinking + tool_use)**
```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "I need to list Kubernetes pods in the default namespace and save them to a file. I'll use the kubernetes_list_pods tool first, then use write_file to save the results."
    },
    {
      "type": "tool_use",
      "id": "tool_001",
      "name": "kubernetes_list_pods",
      "input": {
        "namespace": "default"
      }
    }
  ]
}
```

**Message 3: Result**
```json
{
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "tool_001",
      "content": "pod-1: Running\npod-2: Running\npod-3: Pending",
      "is_error": false
    }
  ]
}
```

**Message 4: Assistant (with tool_use)**
```json
{
  "content": [
    {
      "type": "tool_use",
      "id": "tool_002",
      "name": "write_file",
      "input": {
        "path": "pods.txt",
        "content": "pod-1: Running\npod-2: Running\npod-3: Pending"
      }
    }
  ]
}
```

**Message 5: Result**
```json
{
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "tool_002",
      "content": "File written successfully",
      "is_error": false
    }
  ]
}
```

**Message 6: Assistant (final text)**
```json
{
  "content": [
    {
      "type": "text",
      "text": "I've listed all pods in the default namespace and saved them to pods.txt. There are 3 pods: 2 running and 1 pending."
    }
  ]
}
```

---

## 🔍 How to View Complete Session Data

### **Get Session Summary:**
```bash
GET /api/v1/sessions/{session_id}
```
Shows: total messages, total tool calls, total cost, token usage

### **Get All Messages (with thinking):**
```bash
GET /api/v1/sessions/{session_id}/messages?limit=100
```
Shows: All messages including thinking blocks and tool use blocks

### **Get All Tool Calls:**
```bash
GET /api/v1/sessions/{session_id}/tool-calls
```
Shows: Tool name, input, output, duration, success/failure

### **Get Audit Trail:**
```bash
GET /api/v1/admin/audit-logs?session_id={session_id}
```
Shows: Tool permission requests, security checks, all actions

---

## 💡 Key Points

1. **Thinking Blocks** 
   - Captured in `content.content[].type = "thinking"`
   - Shows Claude's reasoning process
   - Available in assistant messages

2. **Tool Tracking**
   - Every tool use creates a ToolCall record
   - Includes input parameters, output, duration
   - Links to both tool_use and tool_result messages

3. **Prompt Structure**
   - User message is sent as-is to SDK
   - SDK adds system prompt (if configured)
   - SDK manages conversation history automatically
   - MCP servers provide tool definitions

4. **Real SDK Request**
   - SDK internally calls `claude --mode agent` CLI
   - Manages subprocess and stdio communication
   - Handles streaming responses
   - Provides structured message objects

5. **Cost Tracking**
   - Each message tracks token count and cost
   - Session totals automatically updated
   - Available in session summary

---

## 📝 Database Tables

### **messages**
- Stores all messages (user, assistant, system, result)
- Contains thinking blocks and tool use blocks
- Tracks tokens and cost per message

### **tool_calls**
- Separate record for each tool execution
- Links to tool_use message and tool_result message
- Tracks status, duration, and results

### **audit_logs**
- Records tool permission checks
- Logs security validations
- Tracks all significant actions

---

## 🚀 Next Steps

To test the complete flow:

1. Create a session: `POST /api/v1/sessions`
2. Send a message: `POST /api/v1/sessions/{id}/query`
3. Retrieve messages: `GET /api/v1/sessions/{id}/messages`
4. Check tool calls: `GET /api/v1/sessions/{id}/tool-calls`
5. View session stats: `GET /api/v1/sessions/{id}`

All thinking, tool use, and results are automatically captured and available through the API!
