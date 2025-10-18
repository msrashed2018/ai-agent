# AI Agent CLI - Usage Examples with Test Data

Complete usage examples for all CLI commands with sample test data and expected outputs.

## Table of Contents

1. [Configuration Commands](#configuration-commands)
2. [Authentication Commands](#authentication-commands)
3. [Session Management Commands](#session-management-commands)
4. [Task Automation Commands](#task-automation-commands)
5. [Report Management Commands](#report-management-commands)
6. [MCP Server Management Commands](#mcp-server-management-commands)
7. [Admin Commands](#admin-commands)
8. [Complete Workflows](#complete-workflows)

---

## Configuration Commands

### Show Current Configuration

```bash
ai-agent config show
```

**Output:**
```
┌─────────────────────────┬──────────────────────────────────────┐
│                     Key │ Value                                │
├─────────────────────────┼──────────────────────────────────────┤
│                 Api Url │ http://localhost:8000                │
│ Default Output Format   │ table                                │
│                 Timeout │ 30                                   │
│           Authenticated │ Yes                                  │
│             Config File │ /home/user/.ai-agent-cli/config.json │
└─────────────────────────┴──────────────────────────────────────┘
```

### Set API URL

```bash
ai-agent config set-api-url http://localhost:8000
```

**Output:**
```
✓ API URL set to: http://localhost:8000
```

### Get API URL

```bash
ai-agent config get-api-url
```

**Output:**
```
ℹ API URL: http://localhost:8000
```

### Reset Configuration

```bash
ai-agent config reset --yes
```

**Output:**
```
✓ Configuration reset to defaults
```

---

## Authentication Commands

### Login

```bash
ai-agent auth login --email admin@example.com --password admin123
```

**Output:**
```
✓ Successfully logged in as admin@example.com
ℹ Access token expires in 3600 seconds
```

**Test Data:**
- Email: `admin@example.com`
- Password: `admin123`

### Check Authentication Status

```bash
ai-agent auth status
```

**Output:**
```
✓ Authenticated
ℹ API URL: http://localhost:8000
ℹ Logged in as: admin@example.com (admin)
```

### Get Current User Info (whoami)

```bash
ai-agent auth whoami
```

**Output (table format):**
```
┌────────────┬─────────────────────────────────────┐
│        Key │ Value                               │
├────────────┼─────────────────────────────────────┤
│         Id │ 550e8400-e29b-41d4-a716-446655440000│
│      Email │ admin@example.com                   │
│       Role │ admin                               │
│ Created At │ 2025-10-18T10:30:00                 │
└────────────┴─────────────────────────────────────┘
```

**Output (JSON format):**
```bash
ai-agent auth whoami --format json
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com",
  "role": "admin",
  "created_at": "2025-10-18T10:30:00"
}
```

### Refresh Access Token

```bash
ai-agent auth refresh
```

**Output:**
```
✓ Access token refreshed successfully
ℹ New token expires in 3600 seconds
```

### Logout

```bash
ai-agent auth logout
```

**Output:**
```
✓ Successfully logged out
```

---

## Session Management Commands

### Create a Session

**Basic Creation:**
```bash
ai-agent sessions create --name "Investigation Session" --description "Investigating production issue"
```

**With Allowed Tools:**
```bash
ai-agent sessions create \
  --name "Code Review Session" \
  --description "Review authentication module" \
  --allowed-tools "Read" \
  --allowed-tools "Bash" \
  --allowed-tools "Grep" \
  --working-directory "/workspace/project"
```

**With System Prompt:**
```bash
ai-agent sessions create \
  --name "Security Audit" \
  --system-prompt "You are a security auditor. Focus on finding vulnerabilities and security issues." \
  --allowed-tools "Read" \
  --allowed-tools "Grep"
```

**Output:**
```
✓ Session created: a1b2c3d4-e5f6-7890-abcd-ef1234567890

┌─────────────────┬────────────────────────────────────────┐
│             Key │ Value                                  │
├─────────────────┼────────────────────────────────────────┤
│              Id │ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│         User Id │ 550e8400-e29b-41d4-a716-446655440000   │
│            Name │ Investigation Session                  │
│     Description │ Investigating production issue         │
│          Status │ active                                 │
│ Working Dir     │ /tmp/sessions/a1b2c3d4                 │
│   Allowed Tools │ ["Read", "Bash", "Grep"]               │
│      Created At │ 2025-10-18T11:00:00                    │
└─────────────────┴────────────────────────────────────────┘
```

### List Sessions

**List All:**
```bash
ai-agent sessions list
```

**Filter by Status:**
```bash
ai-agent sessions list --status active
```

**Filter Fork Sessions:**
```bash
ai-agent sessions list --is-fork true
```

**With Pagination:**
```bash
ai-agent sessions list --page 1 --page-size 10
```

**JSON Output:**
```bash
ai-agent sessions list --format json
```

**Output:**
```
┌────────────────────────────────────────┬─────────────────────┬────────┬──────────┬──────────────┐
│ Id                                     │ Name                │ Status │ Messages │ Cost (USD)   │
├────────────────────────────────────────┼─────────────────────┼────────┼──────────┼──────────────┤
│ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │ Investigation       │ active │ 15       │ 0.045        │
│ b2c3d4e5-f6a7-8901-bcde-f12345678901   │ Code Review         │ paused │ 8        │ 0.023        │
│ c3d4e5f6-a7b8-9012-cdef-123456789012   │ Security Audit      │ active │ 22       │ 0.067        │
└────────────────────────────────────────┴─────────────────────┴────────┴──────────┴──────────────┘

ℹ Showing page 1 of 3 (50 total items)
```

### Get Session Details

```bash
ai-agent sessions get a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Output:**
```
┌──────────────────────┬────────────────────────────────────────┐
│                  Key │ Value                                  │
├──────────────────────┼────────────────────────────────────────┤
│                   Id │ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│              User Id │ 550e8400-e29b-41d4-a716-446655440000   │
│                 Name │ Investigation Session                  │
│          Description │ Investigating production issue         │
│               Status │ active                                 │
│      Working Dir     │ /tmp/sessions/a1b2c3d4                 │
│        Allowed Tools │ ["Read", "Bash", "Grep"]               │
│        Message Count │ 15                                     │
│     Tool Call Count  │ 42                                     │
│    Total Cost (USD)  │ 0.045                                  │
│   Total Input Tokens │ 12450                                  │
│  Total Output Tokens │ 3890                                   │
│           Created At │ 2025-10-18T11:00:00                    │
│           Updated At │ 2025-10-18T11:45:23                    │
│           Started At │ 2025-10-18T11:01:15                    │
└──────────────────────┴────────────────────────────────────────┘
```

### Send Message to Session (Query)

**Simple Query:**
```bash
ai-agent sessions query a1b2c3d4-e5f6-7890-abcd-ef1234567890 "What files are in the current directory?"
```

**Fork Before Query:**
```bash
ai-agent sessions query a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  "Try a different approach to fix the bug" \
  --fork
```

**Complex Query:**
```bash
ai-agent sessions query a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  "Analyze the authentication.py file for security vulnerabilities. Check for SQL injection, XSS, and improper input validation."
```

**Output:**
```
✓ Message sent to session a1b2c3d4-e5f6-7890-abcd-ef1234567890

┌──────────────────────┬────────────────────────────────────────┐
│                  Key │ Value                                  │
├──────────────────────┼────────────────────────────────────────┤
│                   Id │ a1b2c3d4-e5f6-7890-abcd-ef1234567890   │
│               Status │ active                                 │
│   Parent Session Id  │ null                                   │
│              Is Fork │ false                                  │
│           Message Id │ d4e5f6a7-b8c9-0123-defg-456789012345   │
└──────────────────────┴────────────────────────────────────────┘
```

### List Messages in Session

```bash
ai-agent sessions messages a1b2c3d4-e5f6-7890-abcd-ef1234567890 --limit 10
```

**With JSON Output:**
```bash
ai-agent sessions messages a1b2c3d4-e5f6-7890-abcd-ef1234567890 --limit 5 --format json
```

**Output (JSON):**
```json
[
  {
    "id": "d4e5f6a7-b8c9-0123-defg-456789012345",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message_type": "user",
    "content": {
      "text": "What files are in the current directory?"
    },
    "token_count": 12,
    "cost_usd": 0.0001,
    "created_at": "2025-10-18T11:30:00"
  },
  {
    "id": "e5f6a7b8-c9d0-1234-efgh-567890123456",
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message_type": "assistant",
    "content": {
      "text": "I'll check the current directory for you.",
      "tool_uses": [
        {
          "id": "tool_123",
          "name": "Bash",
          "input": {"command": "ls -la"}
        }
      ]
    },
    "token_count": 145,
    "cost_usd": 0.0015,
    "created_at": "2025-10-18T11:30:02"
  }
]
```

### List Tool Calls in Session

```bash
ai-agent sessions tool-calls a1b2c3d4-e5f6-7890-abcd-ef1234567890 --limit 20
```

**Output:**
```
┌──────────────────────────────────────┬───────────┬─────────┬──────────────────────┬─────────────┐
│ Id                                   │ Tool Name │ Status  │ Started At           │ Duration(ms)│
├──────────────────────────────────────┼───────────┼─────────┼──────────────────────┼─────────────┤
│ tool1-e5f6-7890-abcd-ef1234567890    │ Bash      │ success │ 2025-10-18T11:30:05  │ 125         │
│ tool2-f6a7-8901-bcde-f12345678901    │ Read      │ success │ 2025-10-18T11:30:10  │ 45          │
│ tool3-a7b8-9012-cdef-123456789012    │ Grep      │ success │ 2025-10-18T11:30:15  │ 89          │
│ tool4-b8c9-0123-defg-234567890123    │ Write     │ error   │ 2025-10-18T11:30:20  │ 12          │
└──────────────────────────────────────┴───────────┴─────────┴──────────────────────┴─────────────┘
```

### Pause Session

```bash
ai-agent sessions pause a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Output:**
```
✓ Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 paused
```

### Resume Session

**Resume Existing:**
```bash
ai-agent sessions resume a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Fork and Resume:**
```bash
ai-agent sessions resume a1b2c3d4-e5f6-7890-abcd-ef1234567890 --fork
```

**Output:**
```
✓ Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 resumed
```

### Terminate Session

```bash
ai-agent sessions terminate a1b2c3d4-e5f6-7890-abcd-ef1234567890 --yes
```

**Output:**
```
✓ Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 terminated
```

### Download Working Directory

```bash
ai-agent sessions download-workdir a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --output /tmp/session-workdir.tar.gz
```

**Output:**
```
✓ Working directory downloaded to /tmp/session-workdir.tar.gz
```

---

## Task Automation Commands

### Create Task

**Simple Task:**
```bash
ai-agent tasks create \
  --name "Daily Health Check" \
  --description "Check system health daily" \
  --prompt-template "Check the health status of the system"
```

**Task with Variables:**
```bash
ai-agent tasks create \
  --name "Service Health Check" \
  --description "Check specific service health" \
  --prompt-template "Check the health status of {{service_name}} and report any issues found. Check response time and error rates." \
  --allowed-tools "Bash" \
  --allowed-tools "Read"
```

**Scheduled Task:**
```bash
ai-agent tasks create \
  --name "Nightly Backup Check" \
  --description "Verify backups completed successfully" \
  --prompt-template "Check if backup for {{environment}} completed successfully. Verify backup size and integrity." \
  --is-scheduled \
  --schedule-cron "0 2 * * *" \
  --schedule-enabled \
  --generate-report \
  --report-format pdf \
  --tags backup \
  --tags automation \
  --tags nightly
```

**Task with Notification:**
```bash
ai-agent tasks create \
  --name "Critical Alert Monitor" \
  --prompt-template "Monitor {{log_path}} for critical errors in the last {{time_window}}" \
  --generate-report \
  --report-format html \
  --tags monitoring \
  --tags alerts
```

**Output:**
```
✓ Task created: t1a2b3c4-d5e6-7890-abcd-ef1234567890

┌─────────────────────┬──────────────────────────────────────────┐
│                 Key │ Value                                    │
├─────────────────────┼──────────────────────────────────────────┤
│                  Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890     │
│                Name │ Service Health Check                     │
│         Description │ Check specific service health            │
│   Prompt Template   │ Check health of {{service_name}}...      │
│       Is Scheduled  │ false                                    │
│    Generate Report  │ true                                     │
│      Report Format  │ html                                     │
│                Tags │ ["monitoring", "health"]                 │
│          Created At │ 2025-10-18T12:00:00                      │
└─────────────────────┴──────────────────────────────────────────┘
```

### List Tasks

**List All:**
```bash
ai-agent tasks list
```

**Filter by Scheduled:**
```bash
ai-agent tasks list --is-scheduled true
```

**Filter by Tags:**
```bash
ai-agent tasks list --tags monitoring --tags backup
```

**Output:**
```
┌──────────────────────────────────────┬──────────────────────┬───────────┬──────────┬─────────────┐
│ Id                                   │ Name                 │ Scheduled │ Enabled  │ Executions  │
├──────────────────────────────────────┼──────────────────────┼───────────┼──────────┼─────────────┤
│ t1a2b3c4-d5e6-7890-abcd-ef1234567890 │ Service Health Check │ false     │ -        │ 15          │
│ t2b3c4d5-e6f7-8901-bcde-f12345678901 │ Nightly Backup Check │ true      │ true     │ 127         │
│ t3c4d5e6-f7a8-9012-cdef-123456789012 │ Daily Health Check   │ false     │ -        │ 8           │
└──────────────────────────────────────┴──────────────────────┴───────────┴──────────┴─────────────┘
```

### Get Task Details

```bash
ai-agent tasks get t1a2b3c4-d5e6-7890-abcd-ef1234567890
```

**Output:**
```
┌─────────────────────┬──────────────────────────────────────────┐
│                 Key │ Value                                    │
├─────────────────────┼──────────────────────────────────────────┤
│                  Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890     │
│                Name │ Service Health Check                     │
│         Description │ Check specific service health            │
│   Prompt Template   │ Check health of {{service_name}}...      │
│       Allowed Tools │ ["Bash", "Read"]                         │
│       Is Scheduled  │ false                                    │
│      Schedule Cron  │ null                                     │
│    Schedule Enabled │ false                                    │
│   Last Executed At  │ 2025-10-18T11:30:00                      │
│     Execution Count │ 15                                       │
│       Success Count │ 14                                       │
│       Failure Count │ 1                                        │
│    Generate Report  │ true                                     │
│      Report Format  │ html                                     │
│                Tags │ ["monitoring", "health"]                 │
│          Created At │ 2025-10-18T10:00:00                      │
│          Updated At │ 2025-10-18T11:30:05                      │
└─────────────────────┴──────────────────────────────────────────┘
```

### Update Task

```bash
ai-agent tasks update t1a2b3c4-d5e6-7890-abcd-ef1234567890 \
  --description "Updated health check description" \
  --schedule-enabled false
```

**Output:**
```
✓ Task t1a2b3c4-d5e6-7890-abcd-ef1234567890 updated
```

### Execute Task

**Without Variables:**
```bash
ai-agent tasks execute t1a2b3c4-d5e6-7890-abcd-ef1234567890
```

**With Variables:**
```bash
ai-agent tasks execute t1a2b3c4-d5e6-7890-abcd-ef1234567890 \
  --variables '{"service_name": "nginx", "threshold": "95"}'
```

**Complex Variables:**
```bash
ai-agent tasks execute t2b3c4d5-e6f7-8901-bcde-f12345678901 \
  --variables '{
    "environment": "production",
    "backup_path": "/backups/prod",
    "retention_days": 30,
    "notify_on_failure": true
  }'
```

**Output:**
```
✓ Task execution started: exec-1a2b-3c4d-5e6f-7890

┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ exec-1a2b-3c4d-5e6f-7890               │
│          Task Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890   │
│       Session Id │ sess-2b3c-4d5e-6f7a-8901               │
│           Status │ running                                │
│     Trigger Type │ manual                                 │
│        Variables │ {"service_name": "nginx"}              │
│       Created At │ 2025-10-18T12:15:00                    │
└──────────────────┴────────────────────────────────────────┘
```

### List Task Executions

```bash
ai-agent tasks executions t1a2b3c4-d5e6-7890-abcd-ef1234567890
```

**Output:**
```
┌──────────────────────────────────────┬───────────┬──────────┬──────────────────────┬──────────────┐
│ Id                                   │ Status    │ Trigger  │ Started At           │ Duration(ms) │
├──────────────────────────────────────┼───────────┼──────────┼──────────────────────┼──────────────┤
│ exec-1a2b-3c4d-5e6f-7890             │ completed │ manual   │ 2025-10-18T12:15:00  │ 4523         │
│ exec-2b3c-4d5e-6f7a-8901             │ completed │ manual   │ 2025-10-18T11:30:00  │ 3892         │
│ exec-3c4d-5e6f-7a8b-9012             │ failed    │ scheduled│ 2025-10-18T10:00:00  │ 1234         │
└──────────────────────────────────────┴───────────┴──────────┴──────────────────────┴──────────────┘
```

### Get Execution Status

```bash
ai-agent tasks execution-status exec-1a2b-3c4d-5e6f-7890
```

**Output:**
```
┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ exec-1a2b-3c4d-5e6f-7890               │
│          Task Id │ t1a2b3c4-d5e6-7890-abcd-ef1234567890   │
│       Session Id │ sess-2b3c-4d5e-6f7a-8901               │
│           Status │ completed                              │
│     Trigger Type │ manual                                 │
│        Variables │ {"service_name": "nginx"}              │
│      Result Data │ {"status": "healthy", "uptime": 99.9}  │
│        Report Id │ rep-3c4d-5e6f-7a8b-9012                │
│   Error Message  │ null                                   │
│      Duration Ms │ 4523                                   │
│       Created At │ 2025-10-18T12:15:00                    │
│       Started At │ 2025-10-18T12:15:01                    │
│     Completed At │ 2025-10-18T12:15:05                    │
└──────────────────┴────────────────────────────────────────┘
```

### Delete Task

```bash
ai-agent tasks delete t1a2b3c4-d5e6-7890-abcd-ef1234567890 --yes
```

**Output:**
```
✓ Task t1a2b3c4-d5e6-7890-abcd-ef1234567890 deleted
```

---

## Report Management Commands

### List Reports

**List All:**
```bash
ai-agent reports list
```

**Filter by Session:**
```bash
ai-agent reports list --session-id a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Filter by Type:**
```bash
ai-agent reports list --report-type auto_generated
```

**Output:**
```
┌──────────────────────────────────────┬──────────────────────┬──────────────┬────────────┬──────────────────────┐
│ Id                                   │ Title                │ Type         │ Format     │ Created At           │
├──────────────────────────────────────┼──────────────────────┼──────────────┼────────────┼──────────────────────┤
│ rep-3c4d-5e6f-7a8b-9012              │ Health Check Report  │ auto_gen     │ html       │ 2025-10-18T12:15:05  │
│ rep-4d5e-6f7a-8b9c-0123              │ Security Audit       │ manual       │ pdf        │ 2025-10-18T11:00:00  │
│ rep-5e6f-7a8b-9c0d-1234              │ Backup Verification  │ auto_gen     │ json       │ 2025-10-18T02:30:00  │
└──────────────────────────────────────┴──────────────────────┴──────────────┴────────────┴──────────────────────┘
```

### Get Report Details

```bash
ai-agent reports get rep-3c4d-5e6f-7a8b-9012
```

**Output:**
```
┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ rep-3c4d-5e6f-7a8b-9012                │
│       Session Id │ sess-2b3c-4d5e-6f7a-8901               │
│            Title │ Service Health Check Report            │
│      Description │ Automated health check results         │
│      Report Type │ auto_generated                         │
│      File Format │ html                                   │
│  File Size Bytes │ 45678                                  │
│     Storage Path │ /reports/rep-3c4d-5e6f.html            │
│       Created At │ 2025-10-18T12:15:05                    │
└──────────────────┴────────────────────────────────────────┘
```

### Download Report

**HTML Format:**
```bash
ai-agent reports download rep-3c4d-5e6f-7a8b-9012 \
  --format html \
  --output /tmp/health-report.html
```

**PDF Format:**
```bash
ai-agent reports download rep-4d5e-6f7a-8b9c-0123 \
  --format pdf \
  --output /tmp/security-audit.pdf
```

**JSON Format:**
```bash
ai-agent reports download rep-5e6f-7a8b-9c0d-1234 \
  --format json \
  --output /tmp/backup-report.json
```

**Output:**
```
✓ Report downloaded to /tmp/health-report.html
```

---

## MCP Server Management Commands

### List MCP Servers

```bash
ai-agent mcp list
```

**Output:**
```
┌──────────────────────────────────────┬────────────────────┬───────────┬─────────┬────────────────┐
│ Id                                   │ Name               │ Type      │ Enabled │ Health Status  │
├──────────────────────────────────────┼────────────────────┼───────────┼─────────┼────────────────┤
│ mcp-1a2b-3c4d-5e6f-7890              │ kubernetes-mcp     │ stdio     │ true    │ healthy        │
│ mcp-2b3c-4d5e-6f7a-8901              │ filesystem-mcp     │ stdio     │ true    │ healthy        │
│ mcp-3c4d-5e6f-7a8b-9012              │ database-mcp       │ http      │ false   │ unknown        │
└──────────────────────────────────────┴────────────────────┴───────────┴─────────┴────────────────┘
```

### Create MCP Server

**Filesystem MCP Server:**
```bash
ai-agent mcp create \
  --name "filesystem-mcp" \
  --description "Local filesystem access" \
  --server-type stdio \
  --config '{
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    "env": {}
  }' \
  --enabled
```

**Kubernetes MCP Server:**
```bash
ai-agent mcp create \
  --name "kubernetes-mcp" \
  --description "Kubernetes cluster access" \
  --server-type stdio \
  --config '{
    "command": "kubectl",
    "args": ["mcp"],
    "env": {
      "KUBECONFIG": "/home/user/.kube/config"
    }
  }' \
  --enabled
```

**HTTP MCP Server:**
```bash
ai-agent mcp create \
  --name "api-gateway-mcp" \
  --description "API Gateway MCP" \
  --server-type http \
  --config '{
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer token123"
    }
  }' \
  --enabled
```

**Output:**
```
✓ MCP server created: mcp-1a2b-3c4d-5e6f-7890

┌──────────────────┬────────────────────────────────────────┐
│              Key │ Value                                  │
├──────────────────┼────────────────────────────────────────┤
│               Id │ mcp-1a2b-3c4d-5e6f-7890                │
│             Name │ filesystem-mcp                         │
│      Description │ Local filesystem access                │
│      Server Type │ stdio                                  │
│           Config │ {"command": "npx", "args": [...]}      │
│       Is Enabled │ true                                   │
│        Is Global │ false                                  │
│    Health Status │ unknown                                │
│       Created At │ 2025-10-18T13:00:00                    │
└──────────────────┴────────────────────────────────────────┘
```

### Get MCP Server Details

```bash
ai-agent mcp get mcp-1a2b-3c4d-5e6f-7890
```

**Output:**
```
┌─────────────────────────┬────────────────────────────────────────┐
│                     Key │ Value                                  │
├─────────────────────────┼────────────────────────────────────────┤
│                      Id │ mcp-1a2b-3c4d-5e6f-7890                │
│                    Name │ filesystem-mcp                         │
│             Description │ Local filesystem access                │
│             Server Type │ stdio                                  │
│                  Config │ {"command":"npx","args":[...]}         │
│              Is Enabled │ true                                   │
│               Is Global │ false                                  │
│           Health Status │ healthy                                │
│ Last Health Check At    │ 2025-10-18T13:05:00                    │
│              Created At │ 2025-10-18T13:00:00                    │
│              Updated At │ 2025-10-18T13:05:00                    │
└─────────────────────────┴────────────────────────────────────────┘
```

### Update MCP Server

```bash
ai-agent mcp update mcp-1a2b-3c4d-5e6f-7890 \
  --description "Updated filesystem MCP" \
  --enabled false
```

**Output:**
```
✓ MCP server mcp-1a2b-3c4d-5e6f-7890 updated
```

### Health Check MCP Server

```bash
ai-agent mcp health-check mcp-1a2b-3c4d-5e6f-7890
```

**Output:**
```
✓ Health check completed for server mcp-1a2b-3c4d-5e6f-7890

┌─────────────────────────┬────────────────────────────────────────┐
│                     Key │ Value                                  │
├─────────────────────────┼────────────────────────────────────────┤
│                      Id │ mcp-1a2b-3c4d-5e6f-7890                │
│                    Name │ filesystem-mcp                         │
│           Health Status │ healthy                                │
│ Last Health Check At    │ 2025-10-18T13:10:00                    │
└─────────────────────────┴────────────────────────────────────────┘
```

### Import Claude Desktop Configuration

**Test Data - Create sample config file:**
```bash
cat > /tmp/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {}
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/workspace/project"],
      "env": {}
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"],
      "env": {}
    }
  }
}
EOF
```

**Import:**
```bash
ai-agent mcp import /tmp/claude_desktop_config.json
```

**Import with Override:**
```bash
ai-agent mcp import /tmp/claude_desktop_config.json --override
```

**Output:**
```
✓ Imported 3 servers
ℹ Skipped 0 existing servers
```

### Export Configuration

```bash
ai-agent mcp export --output /tmp/mcp-export.json --include-global
```

**Output:**
```
✓ Configuration exported to /tmp/mcp-export.json
```

**Exported File Content:**
```json
{
  "mcpServers": {
    "filesystem-mcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "env": {}
    },
    "kubernetes-mcp": {
      "command": "kubectl",
      "args": ["mcp"],
      "env": {
        "KUBECONFIG": "/home/user/.kube/config"
      }
    }
  }
}
```

### List MCP Templates

```bash
ai-agent mcp templates --format json
```

**Output:**
```json
{
  "templates": [
    {
      "name": "filesystem",
      "description": "Local filesystem access",
      "server_type": "stdio",
      "config_template": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "<path>"],
        "env": {}
      }
    },
    {
      "name": "kubernetes",
      "description": "Kubernetes cluster management",
      "server_type": "stdio",
      "config_template": {
        "command": "kubectl",
        "args": ["mcp"],
        "env": {
          "KUBECONFIG": "<kubeconfig_path>"
        }
      }
    },
    {
      "name": "postgres",
      "description": "PostgreSQL database access",
      "server_type": "stdio",
      "config_template": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "<connection_string>"],
        "env": {}
      }
    }
  ],
  "total": 3
}
```

### Delete MCP Server

```bash
ai-agent mcp delete mcp-1a2b-3c4d-5e6f-7890 --yes
```

**Output:**
```
✓ MCP server mcp-1a2b-3c4d-5e6f-7890 deleted
```

---

## Admin Commands

### Get System Statistics

```bash
ai-agent admin stats --format json
```

**Output:**
```json
{
  "sessions": {
    "total": 1523,
    "active": 45,
    "completed_today": 127
  },
  "tasks": {
    "total": 89,
    "scheduled_enabled": 23,
    "executions_today": 156
  },
  "users": {
    "total": 234,
    "active_today": 67
  },
  "cost": {
    "total_usd": 456.78,
    "today_usd": 12.34
  },
  "storage": {
    "working_dirs_mb": 15678,
    "reports_mb": 4523,
    "archives_mb": 8901
  }
}
```

### List All Sessions (Admin)

```bash
ai-agent admin sessions
```

**Filter by User:**
```bash
ai-agent admin sessions --user-id 550e8400-e29b-41d4-a716-446655440000
```

**Filter by Status:**
```bash
ai-agent admin sessions --status active
```

**Output:**
```
┌──────────────────────────────────────┬──────────────────────────┬────────┬──────────┬─────────────┐
│ Session Id                           │ User Email               │ Status │ Messages │ Cost (USD)  │
├──────────────────────────────────────┼──────────────────────────┼────────┼──────────┼─────────────┤
│ a1b2c3d4-e5f6-7890-abcd-ef1234567890 │ user1@example.com        │ active │ 15       │ 0.045       │
│ b2c3d4e5-f6a7-8901-bcde-f12345678901 │ user2@example.com        │ paused │ 8        │ 0.023       │
│ c3d4e5f6-a7b8-9012-cdef-123456789012 │ admin@example.com        │ active │ 22       │ 0.067       │
└──────────────────────────────────────┴──────────────────────────┴────────┴──────────┴─────────────┘
```

### List All Users (Admin)

```bash
ai-agent admin users
```

**Include Deleted:**
```bash
ai-agent admin users --include-deleted
```

**Output:**
```
┌──────────────────────────────────────┬────────────────────────┬──────────┬────────────┬──────────────────────┐
│ Id                                   │ Email                  │ Role     │ Is Deleted │ Created At           │
├──────────────────────────────────────┼────────────────────────┼──────────┼────────────┼──────────────────────┤
│ 550e8400-e29b-41d4-a716-446655440000 │ admin@example.com      │ admin    │ false      │ 2025-01-01T00:00:00  │
│ 661f9511-f3ac-52e5-b827-557766551111 │ user1@example.com      │ user     │ false      │ 2025-02-15T10:30:00  │
│ 772fa622-04bd-63f6-c938-668877662222 │ user2@example.com      │ user     │ false      │ 2025-03-20T14:15:00  │
└──────────────────────────────────────┴────────────────────────┴──────────┴────────────┴──────────────────────┘
```

---

## Complete Workflows

### Workflow 1: Investigation Session

```bash
# 1. Create session
SESSION_ID=$(ai-agent sessions create \
  --name "Production Bug Investigation" \
  --description "Investigating timeout errors" \
  --allowed-tools "Read" --allowed-tools "Bash" --allowed-tools "Grep" \
  --format json | jq -r '.id')

# 2. Query the issue
ai-agent sessions query $SESSION_ID \
  "Analyze the application logs in /var/log/app for timeout errors in the last hour"

# 3. Follow-up query
ai-agent sessions query $SESSION_ID \
  "Check the database connection pool settings and compare with recommended values"

# 4. List messages
ai-agent sessions messages $SESSION_ID --limit 20 --format json

# 5. List tool calls
ai-agent sessions tool-calls $SESSION_ID --format table

# 6. Download working directory
ai-agent sessions download-workdir $SESSION_ID --output investigation-$(date +%Y%m%d).tar.gz

# 7. Terminate
ai-agent sessions terminate $SESSION_ID --yes
```

### Workflow 2: Automated Monitoring Task

```bash
# 1. Create monitoring task
TASK_ID=$(ai-agent tasks create \
  --name "API Health Monitor" \
  --prompt-template "Check API health at {{api_url}}. Expected response time: <{{threshold_ms}}ms. Report any anomalies." \
  --is-scheduled \
  --schedule-cron "*/5 * * * *" \
  --schedule-enabled \
  --generate-report \
  --report-format html \
  --tags monitoring --tags api \
  --format json | jq -r '.id')

# 2. Execute manually first
EXEC_ID=$(ai-agent tasks execute $TASK_ID \
  --variables '{"api_url": "https://api.example.com/health", "threshold_ms": 200}' \
  --format json | jq -r '.id')

# 3. Wait for completion
sleep 10

# 4. Check status
ai-agent tasks execution-status $EXEC_ID

# 5. If report generated, download it
REPORT_ID=$(ai-agent tasks execution-status $EXEC_ID --format json | jq -r '.report_id')
if [ "$REPORT_ID" != "null" ]; then
  ai-agent reports download $REPORT_ID --format html --output api-health-report.html
fi

# 6. List execution history
ai-agent tasks executions $TASK_ID
```

### Workflow 3: MCP Server Setup

```bash
# 1. List available templates
ai-agent mcp templates

# 2. Create filesystem MCP
FS_MCP_ID=$(ai-agent mcp create \
  --name "project-filesystem" \
  --description "Project workspace access" \
  --server-type stdio \
  --config '{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/workspace/project"],"env":{}}' \
  --enabled \
  --format json | jq -r '.id')

# 3. Create kubernetes MCP
K8S_MCP_ID=$(ai-agent mcp create \
  --name "prod-kubernetes" \
  --description "Production K8s cluster" \
  --server-type stdio \
  --config '{"command":"kubectl","args":["mcp"],"env":{"KUBECONFIG":"/home/user/.kube/prod-config"}}' \
  --enabled \
  --format json | jq -r '.id')

# 4. Health check all servers
ai-agent mcp health-check $FS_MCP_ID
ai-agent mcp health-check $K8S_MCP_ID

# 5. List all servers
ai-agent mcp list

# 6. Export configuration for backup
ai-agent mcp export --output mcp-backup-$(date +%Y%m%d).json --include-global
```

### Workflow 4: Session with Fork

```bash
# 1. Create initial session
SESSION_ID=$(ai-agent sessions create \
  --name "Feature Development" \
  --format json | jq -r '.id')

# 2. Initial exploration
ai-agent sessions query $SESSION_ID "Analyze the authentication module structure"

# 3. Fork for alternative approach
ai-agent sessions query $SESSION_ID \
  "Try implementing OAuth2 instead of JWT" \
  --fork

# This creates a new session (fork) while preserving the original
```

---

## Test Data Summary

### User Credentials
- **Admin User:**
  - Email: `admin@example.com`
  - Password: `admin123`
  - Role: `admin`

- **Regular User:**
  - Email: `user@example.com`
  - Password: `user123`
  - Role: `user`

### Sample UUIDs for Testing
- Session ID: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Task ID: `t1a2b3c4-d5e6-7890-abcd-ef1234567890`
- Execution ID: `exec-1a2b-3c4d-5e6f-7890`
- Report ID: `rep-3c4d-5e6f-7a8b-9012`
- MCP Server ID: `mcp-1a2b-3c4d-5e6f-7890`
- User ID: `550e8400-e29b-41d4-a716-446655440000`

### Sample Task Variables
```json
{
  "service_name": "nginx",
  "environment": "production",
  "threshold": "95",
  "api_url": "https://api.example.com/health",
  "threshold_ms": 200,
  "log_path": "/var/log/application.log",
  "time_window": "1h",
  "backup_path": "/backups/prod",
  "retention_days": 30
}
```

### Sample MCP Configurations
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    "env": {}
  },
  "kubernetes": {
    "command": "kubectl",
    "args": ["mcp"],
    "env": {"KUBECONFIG": "/home/user/.kube/config"}
  },
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/db"],
    "env": {}
  }
}
```

---

## Tips for Testing

1. **Always start with authentication:**
   ```bash
   ai-agent config set-api-url http://localhost:8000
   ai-agent auth login
   ```

2. **Use JSON output for scripting:**
   ```bash
   SESSION_ID=$(ai-agent sessions create --name "Test" --format json | jq -r '.id')
   ```

3. **Check help for any command:**
   ```bash
   ai-agent sessions query --help
   ```

4. **Use --yes to skip confirmations in scripts:**
   ```bash
   ai-agent sessions terminate $SESSION_ID --yes
   ```

5. **Test API connectivity:**
   ```bash
   curl $(ai-agent config get-api-url)/health
   ```
