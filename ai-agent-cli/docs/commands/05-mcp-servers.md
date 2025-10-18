# MCP Servers Commands

Model Context Protocol (MCP) servers provide additional tools and capabilities to Claude sessions. Servers can be stdio (local processes), SSE (server-sent events), or HTTP (remote servers).

---

## Commands Overview

| CLI Command | API Endpoint | Description |
|------------|-------------|-------------|
| `ai-agent mcp list` | `GET /api/v1/mcp-servers` | List MCP servers |
| `ai-agent mcp create` | `POST /api/v1/mcp-servers` | Register new MCP server |
| `ai-agent mcp get <server-id>` | `GET /api/v1/mcp-servers/{server_id}` | Get server details |
| `ai-agent mcp update <server-id>` | `PATCH /api/v1/mcp-servers/{server_id}` | Update server config |
| `ai-agent mcp delete <server-id>` | `DELETE /api/v1/mcp-servers/{server_id}` | Delete server |
| `ai-agent mcp health-check <server-id>` | `POST /api/v1/mcp-servers/{server_id}/health-check` | Check server health |
| `ai-agent mcp import` | `POST /api/v1/mcp-servers/import` | Import Claude Desktop config |
| `ai-agent mcp export` | `GET /api/v1/mcp-servers/export` | Export to Claude Desktop format |
| `ai-agent mcp templates` | `GET /api/v1/mcp-servers/templates` | Get server templates |

---

## MCP Server Types

### 1. stdio (Local Process)
Spawns a local process that communicates via stdin/stdout:
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
  "env": {
    "KUBECONFIG": "/path/to/kubeconfig"
  }
}
```

### 2. SSE (Server-Sent Events)
Connects to remote server via SSE:
```json
{
  "type": "sse",
  "url": "https://mcp-server.example.com/sse",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

### 3. HTTP (Remote HTTP)
Connects to remote server via HTTP:
```json
{
  "type": "http",
  "url": "https://mcp-server.example.com",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

---

## 1. List MCP Servers

### CLI Command
```bash
# List all available servers (user's + global)
ai-agent mcp list

# JSON output
ai-agent mcp list --output json
```

### What Happens in Backend API

**Step 1: Authentication**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;
```

**Step 2: Query User's Servers**
```sql
-- Get user's personal MCP servers
SELECT * FROM mcp_servers
WHERE user_id = 'user-uuid'
  AND deleted_at IS NULL
ORDER BY created_at DESC;
```

**Step 3: Query Global Servers**
```sql
-- Get globally available MCP servers
SELECT * FROM mcp_servers
WHERE is_global = true
  AND is_enabled = true
  AND deleted_at IS NULL
ORDER BY created_at DESC;
```

**Step 4: Combine and Deduplicate**
```python
# Combine lists, user servers take precedence
all_servers = user_servers + [s for s in global_servers if s.is_global]
# Deduplicate by name (user servers override globals)
```

**Step 5: Return Response**
```json
{
  "items": [
    {
      "id": "server-uuid-1",
      "name": "kubernetes",
      "description": "Query Kubernetes clusters",
      "server_type": "stdio",
      "config": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
        "env": {"KUBECONFIG": "/home/user/.kube/config"}
      },
      "is_global": false,
      "is_enabled": true,
      "health_status": "healthy",
      "user_id": "user-uuid",
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "server-uuid-2",
      "name": "filesystem",
      "server_type": "stdio",
      "is_global": true,
      "is_enabled": true
    }
  ],
  "total": 2
}
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_servers.py:31-56](../../ai-agent-api/app/api/v1/mcp_servers.py#L31-L56)
- Repository: [app/repositories/mcp_server_repository.py](../../ai-agent-api/app/repositories/mcp_server_repository.py)

---

## 2. Create MCP Server

### CLI Command
```bash
# Create stdio server
ai-agent mcp create \
  --name my-kubernetes \
  --description "My K8s cluster" \
  --type stdio \
  --command npx \
  --args '"-y" "@modelcontextprotocol/server-kubernetes"' \
  --env KUBECONFIG=/path/to/kubeconfig

# Create SSE server
ai-agent mcp create \
  --name remote-mcp \
  --type sse \
  --url https://mcp.example.com/sse \
  --headers '{"Authorization": "Bearer token"}'

# Interactive mode
ai-agent mcp create --interactive
```

### What Happens in Backend API

**Step 1: Authentication**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;
```

**Step 2: Check for Duplicate Name**
```sql
-- Check if server with same name exists for user
SELECT * FROM mcp_servers
WHERE name = 'my-kubernetes'
  AND user_id = 'user-uuid'
  AND deleted_at IS NULL;
```

If exists:
```json
{
  "status": 409,
  "detail": "MCP server with name 'my-kubernetes' already exists"
}
```

**Step 3: Validate Configuration**

For stdio servers:
```python
# Validate required fields
if "command" not in config:
    raise ValueError("stdio server requires 'command'")

normalized_config = {
    "command": config["command"],
    "args": config.get("args", []),
    "env": config.get("env", {})
}
```

For SSE/HTTP servers:
```python
# Validate URL
if "url" not in config:
    raise ValueError("sse/http server requires 'url'")

if not config["url"].startswith(("http://", "https://")):
    raise ValueError(f"Invalid URL: {config['url']}")

normalized_config = {
    "url": config["url"],
    "headers": config.get("headers", {})
}
```

**Step 4: Create Database Record**
```sql
INSERT INTO mcp_servers (
  id, name, description, server_type, config,
  user_id, is_global, is_enabled, health_status,
  created_at, updated_at
) VALUES (
  'server-uuid',
  'my-kubernetes',
  'My K8s cluster',
  'stdio',
  '{"command": "npx", "args": ["-y", "@modelcontextprotocol/server-kubernetes"], "env": {"KUBECONFIG": "/path/to/kubeconfig"}}',
  'user-uuid',
  false,
  true,
  'unknown',
  '2025-01-15T10:00:00Z',
  '2025-01-15T10:00:00Z'
);
```

**Step 5: Audit Log**
```sql
INSERT INTO audit_logs (
  id, user_id, action, resource_type, resource_id,
  details, created_at
) VALUES (
  'audit-uuid',
  'user-uuid',
  'mcp_server_create',
  'mcp_server',
  'server-uuid',
  '{"name": "my-kubernetes", "server_type": "stdio"}',
  '2025-01-15T10:00:00Z'
);
```

**Step 6: Return Created Server**
```json
{
  "id": "server-uuid",
  "name": "my-kubernetes",
  "description": "My K8s cluster",
  "server_type": "stdio",
  "config": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
    "env": {"KUBECONFIG": "/path/to/kubeconfig"}
  },
  "is_global": false,
  "is_enabled": true,
  "health_status": "unknown",
  "user_id": "user-uuid",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### How MCP Servers Are Used in Sessions

When a session is created with MCP servers enabled:

**Step 1: Merge MCP Configurations**

From [app/mcp/config_builder.py:119-151](../../ai-agent-api/app/mcp/config_builder.py#L119-L151):

```python
# 1. Start with SDK tools (in-process Python tools)
from app.mcp.sdk_tools import SDK_MCP_SERVERS
config = dict(SDK_MCP_SERVERS)  # 7 tools across 3 servers

# 2. Add user's external servers
user_servers = await mcp_server_repo.list_by_user(user_id)
for server in user_servers:
    if server.is_enabled:
        config[server.name] = convert_to_sdk_format(server)

# 3. Add global servers
global_servers = await mcp_server_repo.list_enabled()
for server in global_servers:
    if server.is_global and server.is_enabled:
        if server.name not in config:  # User servers take precedence
            config[server.name] = convert_to_sdk_format(server)
```

**Step 2: Convert to SDK Format**

```python
# For stdio servers (omit type field for stdio)
sdk_config = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
    "env": {"KUBECONFIG": "/path/to/kubeconfig"}
}

# For SSE servers (include type field)
sdk_config = {
    "type": "sse",
    "url": "https://mcp.example.com/sse",
    "headers": {"Authorization": "Bearer token"}
}
```

**Step 3: Pass to Claude SDK**

Final ClaudeAgentOptions with merged MCP config:
```python
options = ClaudeAgentOptions(
    cwd="/data/sessions/session-uuid",
    model="claude-sonnet-4-5",
    allowed_tools=["Bash", "Read"],
    mcp_servers={
        # SDK tools (in-process)
        "kubernetes_readonly": { ... },  # SDK tool
        "database": { ... },             # SDK tool
        "monitoring": { ... },           # SDK tool

        # User's external servers
        "my-kubernetes": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
            "env": {"KUBECONFIG": "/path/to/kubeconfig"}
        },

        # Global servers
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "***"}
        }
    }
)
```

**Step 4: Claude Code CLI Command**

The SDK spawns subprocess with:
```bash
claude \
  --cwd /data/sessions/session-uuid \
  --model claude-sonnet-4-5 \
  --allowed-tools "Bash,Read" \
  --mcp-server kubernetes_readonly:sdk \
  --mcp-server database:sdk \
  --mcp-server monitoring:sdk \
  --mcp-server my-kubernetes:npx:"-y":"@modelcontextprotocol/server-kubernetes" \
  --mcp-server github:npx:"-y":"@modelcontextprotocol/server-github"
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_servers.py:59-92](../../ai-agent-api/app/api/v1/mcp_servers.py#L59-L92)
- Service: [app/services/mcp_server_service.py:32-78](../../ai-agent-api/app/services/mcp_server_service.py#L32-L78)
- Config validation: [app/mcp/config_manager.py:179-216](../../ai-agent-api/app/mcp/config_manager.py#L179-L216)
- Usage in sessions: [app/mcp/config_builder.py](../../ai-agent-api/app/mcp/config_builder.py)

---

## 3. Update MCP Server

### CLI Command
```bash
# Update description
ai-agent mcp update server-uuid --description "Updated description"

# Update configuration
ai-agent mcp update server-uuid \
  --config '{"command": "npx", "args": ["-y", "@modelcontextprotocol/server-kubernetes"], "env": {"KUBECONFIG": "/new/path"}}'

# Disable server
ai-agent mcp update server-uuid --enabled false
```

### What Happens in Backend API

**Step 1-2: Auth & Get Server**
```sql
SELECT * FROM users WHERE id = 'user-uuid' AND is_active = true;

SELECT * FROM mcp_servers
WHERE id = 'server-uuid'
  AND deleted_at IS NULL;
```

**Step 3: Authorization Check**
```python
# Only owner can update (not admins for MCP servers)
if server.user_id != current_user.id:
    raise HTTPException(403, "Not authorized to update this server")
```

**Step 4: Update Database**
```sql
UPDATE mcp_servers
SET description = 'Updated description',
    updated_at = '2025-01-15T11:00:00Z'
WHERE id = 'server-uuid';
```

**Step 5: Audit Log**
```sql
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
VALUES ('user-uuid', 'mcp_server_update', 'mcp_server', 'server-uuid', '{"description": "Updated description"}');
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_servers.py:123-158](../../ai-agent-api/app/api/v1/mcp_servers.py#L123-L158)
- Service: [app/services/mcp_server_service.py:121-170](../../ai-agent-api/app/services/mcp_server_service.py#L121-L170)

---

## 4. Delete MCP Server

### CLI Command
```bash
ai-agent mcp delete server-uuid
```

### What Happens in Backend API

**Step 1-3: Auth, Get Server, Check Ownership** (same as update)

**Step 4: Delete from Database**
```sql
-- Soft delete
UPDATE mcp_servers
SET deleted_at = '2025-01-15T11:00:00Z',
    updated_at = '2025-01-15T11:00:00Z'
WHERE id = 'server-uuid';
```

**Step 5: Audit Log**
```sql
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
VALUES ('user-uuid', 'mcp_server_delete', 'mcp_server', 'server-uuid', '{"name": "my-kubernetes"}');
```

**Step 6: Return 204 No Content**

### Key Backend Files
- Route handler: [app/api/v1/mcp_servers.py:161-190](../../ai-agent-api/app/api/v1/mcp_servers.py#L161-L190)
- Service: [app/services/mcp_server_service.py:172-200](../../ai-agent-api/app/services/mcp_server_service.py#L172-L200)

---

## 5. Health Check

### CLI Command
```bash
ai-agent mcp health-check server-uuid
```

### What Happens in Backend API

**Step 1-2: Auth & Get Server** (standard flow)

**Step 3: Authorization Check**
```python
# Users can check health of global servers too
if not server.is_global and server.user_id != current_user.id and current_user.role != "admin":
    raise HTTPException(403, "Not authorized to access this server")
```

**Step 4: Perform Health Check**

Current implementation is simplified (returns basic validation):
```python
# TODO: Implement actual connection test
# For stdio: Try spawning process
# For SSE/HTTP: Try connecting to URL

health_result = {
    "status": "success",
    "message": "MCP server configuration appears valid",
    "details": {
        "name": server.name,
        "command": server.config.get("command"),
        "args": server.config.get("args"),
        "env_vars": len(server.config.get("env", {}))
    }
}
```

**Step 5: Update Health Status**
```sql
UPDATE mcp_servers
SET health_status = 'healthy',
    last_health_check_at = '2025-01-15T11:00:00Z',
    updated_at = '2025-01-15T11:00:00Z'
WHERE id = 'server-uuid';
```

**Step 6: Return Updated Server**
```json
{
  "id": "server-uuid",
  "name": "my-kubernetes",
  "health_status": "healthy",
  "last_health_check_at": "2025-01-15T11:00:00Z"
}
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_servers.py:193-226](../../ai-agent-api/app/api/v1/mcp_servers.py#L193-L226)
- Service: [app/services/mcp_server_service.py:202-235](../../ai-agent-api/app/services/mcp_server_service.py#L202-L235)

---

## 6. Import Claude Desktop Config

### CLI Command
```bash
# Import from file
ai-agent mcp import claude_desktop_config.json

# Override existing servers
ai-agent mcp import claude_desktop_config.json --override

# From stdin
cat claude_desktop_config.json | ai-agent mcp import -
```

### Claude Desktop Config Format
```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
      "env": {
        "KUBECONFIG": "/path/to/kubeconfig"
      }
    },
    "remote-server": {
      "type": "sse",
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

### What Happens in Backend API

**Step 1: Parse Upload**
```python
# Read multipart form data
file_content = await file.read()
config_data = json.loads(file_content)

# Validate structure
if "mcpServers" not in config_data:
    raise HTTPException(400, "Invalid config: missing 'mcpServers' key")
```

**Step 2: Process Each Server**

For each server in config:

```python
imported = []
skipped = []
errors = []

for server_name, server_config in config_data["mcpServers"].items():
    # Check if exists
    existing_servers = await mcp_server_repo.list_by_user(user_id)
    exists = any(s.name == server_name for s in existing_servers)

    if exists and not override_existing:
        skipped.append(server_name)
        continue

    # Determine type (default: stdio)
    server_type = server_config.get("type", "stdio")

    # Validate and normalize
    normalized_config = normalize_config(server_type, server_config)

    # Create or update
    if exists and override_existing:
        # Update existing
        await mcp_server_repo.update(existing_server_id, config=normalized_config)
    else:
        # Create new
        new_server = MCPServer(
            id=uuid4(),
            user_id=user_id,
            name=server_name,
            description="Imported from Claude Desktop config",
            server_type=server_type,
            config=normalized_config,
            is_enabled=true
        )
        await mcp_server_repo.create(new_server)

    imported.append(server_name)
```

**Step 3: Database Operations**

For each imported server:
```sql
INSERT INTO mcp_servers (
  id, user_id, name, description, server_type, config,
  is_global, is_enabled, health_status, created_at, updated_at
) VALUES (
  'server-uuid',
  'user-uuid',
  'kubernetes',
  'Imported from Claude Desktop config',
  'stdio',
  '{"command": "npx", "args": ["-y", "@modelcontextprotocol/server-kubernetes"], "env": {...}}',
  false,
  true,
  'unknown',
  '2025-01-15T11:00:00Z',
  '2025-01-15T11:00:00Z'
);
```

**Step 4: Return Import Summary**
```json
{
  "imported": ["kubernetes", "remote-server"],
  "skipped": [],
  "errors": [],
  "summary": "Imported 2, skipped 0, errors 0"
}
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_import_export.py:21-74](../../ai-agent-api/app/api/v1/mcp_import_export.py#L21-L74)
- Config manager: [app/mcp/config_manager.py:34-130](../../ai-agent-api/app/mcp/config_manager.py#L34-L130)
- Normalization: [app/mcp/config_manager.py:179-216](../../ai-agent-api/app/mcp/config_manager.py#L179-L216)

---

## 7. Export to Claude Desktop Format

### CLI Command
```bash
# Export to file
ai-agent mcp export > claude_desktop_config.json

# Exclude global servers
ai-agent mcp export --no-global > my_servers_only.json
```

### What Happens in Backend API

**Step 1: Get User's Servers**
```sql
SELECT * FROM mcp_servers
WHERE user_id = 'user-uuid'
  AND deleted_at IS NULL;
```

**Step 2: Get Global Servers (if requested)**
```sql
SELECT * FROM mcp_servers
WHERE is_global = true
  AND is_enabled = true
  AND deleted_at IS NULL;
```

**Step 3: Deduplicate**
```python
# Add globals not already in user's list
servers = user_servers
if include_global:
    servers += [
        s for s in global_servers
        if s.name not in [us.name for us in user_servers]
    ]
```

**Step 4: Build Claude Desktop Format**
```python
mcp_servers_config = {}

for server in servers:
    if not server.is_enabled:
        continue

    config = server.config.copy()

    # Add type field for non-stdio servers
    if server.server_type != "stdio":
        config["type"] = server.server_type

    mcp_servers_config[server.name] = config
```

**Step 5: Return Claude Desktop Config**
```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
      "env": {
        "KUBECONFIG": "/path/to/kubeconfig"
      }
    },
    "remote-server": {
      "type": "sse",
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

### Key Backend Files
- Route handler: [app/api/v1/mcp_import_export.py:77-96](../../ai-agent-api/app/api/v1/mcp_import_export.py#L77-L96)
- Config manager: [app/mcp/config_manager.py:132-177](../../ai-agent-api/app/mcp/config_manager.py#L132-L177)

---

## 8. Get Server Templates

### CLI Command
```bash
# List all templates
ai-agent mcp templates

# Get specific template
ai-agent mcp templates --name kubernetes

# Create from template
ai-agent mcp templates --name kubernetes --create
```

### What Happens in Backend API

**Step 1: Return Pre-defined Templates**

From [app/mcp/config_manager.py:314-389](../../ai-agent-api/app/mcp/config_manager.py#L314-L389):

```python
templates = [
    {
        "name": "kubernetes",
        "display_name": "Kubernetes",
        "description": "Query Kubernetes clusters",
        "server_type": "stdio",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-kubernetes"],
            "env": {"KUBECONFIG": "/path/to/kubeconfig"}
        },
        "required_env": ["KUBECONFIG"]
    },
    {
        "name": "filesystem",
        "display_name": "Filesystem",
        "description": "Access local filesystem",
        "server_type": "stdio",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
        },
        "required_args": ["path"]
    },
    # ... postgres, brave-search, github templates
]
```

**Step 2: Return Templates**
```json
{
  "templates": [
    {
      "name": "kubernetes",
      "display_name": "Kubernetes",
      "description": "Query Kubernetes clusters",
      "server_type": "stdio",
      "config": {...},
      "required_env": ["KUBECONFIG"]
    }
  ],
  "total": 5
}
```

### Available Templates

| Template | Description | Required Config |
|----------|-------------|----------------|
| `kubernetes` | Query K8s clusters | `KUBECONFIG` env var |
| `filesystem` | Access local files | `path` argument |
| `postgres` | Query PostgreSQL | `POSTGRES_URL` env var |
| `brave-search` | Web search | `BRAVE_API_KEY` env var |
| `github` | GitHub repos | `GITHUB_TOKEN` env var |

### Key Backend Files
- Route handler: [app/api/v1/mcp_import_export.py:99-116](../../ai-agent-api/app/api/v1/mcp_import_export.py#L99-L116)
- Templates: [app/mcp/config_manager.py:314-389](../../ai-agent-api/app/mcp/config_manager.py#L314-L389)

---

## Complete Flow Diagram: MCP Server in Session

```
1. User creates MCP server via CLI
   ↓
2. API validates config and stores in database
   ↓
3. User creates session (or executes task)
   ↓
4. Session creation merges MCP configs:
   - SDK tools (in-process Python)
   - User's external servers
   - Global servers
   ↓
5. MCPConfigBuilder converts to SDK format
   ↓
6. ClaudeSDKClient receives merged config
   ↓
7. SDK spawns Claude Code CLI subprocess:

   claude \
     --cwd /data/sessions/abc123 \
     --mcp-server kubernetes_readonly:sdk \
     --mcp-server my-kubernetes:npx:"-y":"@modelcontextprotocol/server-kubernetes" \
     --mcp-server github:npx:"-y":"@modelcontextprotocol/server-github"

   ↓
8. Claude Code CLI spawns MCP server processes:
   - SDK servers: Imported as Python modules
   - External stdio: Spawned as subprocesses
   - SSE/HTTP: Connected via network
   ↓
9. Claude can use tools from all MCP servers
```

---

## Examples

### Example 1: Create and Use Kubernetes MCP Server

```bash
# Create server
ai-agent mcp create \
  --name my-k8s \
  --type stdio \
  --command npx \
  --args '"-y" "@modelcontextprotocol/server-kubernetes"' \
  --env KUBECONFIG=/home/user/.kube/config

# Create session using this server
ai-agent sessions create \
  --name "K8s debugging" \
  --model claude-sonnet-4-5 \
  --mcp-servers my-k8s

# Query the session (can now use K8s tools)
ai-agent sessions query session-abc "List all pods in default namespace"

# Claude will use the kubernetes MCP server to execute kubectl commands
```

### Example 2: Import from Claude Desktop

```bash
# Export your Claude Desktop config first
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json .

# Import to ai-agent-api
ai-agent mcp import claude_desktop_config.json

# List imported servers
ai-agent mcp list

# Now all your Claude Desktop servers are available for sessions
```

### Example 3: Use Template

```bash
# View templates
ai-agent mcp templates

# Get specific template
ai-agent mcp templates --name postgres

# Create from template (interactive)
ai-agent mcp create --from-template postgres
# Prompts for: POSTGRES_URL

# Or provide directly
ai-agent mcp create \
  --from-template postgres \
  --env POSTGRES_URL=postgresql://localhost/mydb
```

---

## Notes

- **SDK Tools**: The system includes 7 built-in SDK tools (kubernetes_readonly, database, monitoring) that are always available
- **User Servers**: Each user can register their own MCP servers
- **Global Servers**: Admins can mark servers as global (available to all users)
- **Priority**: User servers take precedence over global servers with same name
- **Security**: Credentials in env vars are stored encrypted in database
- **Health Checks**: Currently basic validation; future versions will test actual connectivity
- **Claude Desktop Compatibility**: Full import/export support for claude_desktop_config.json format
