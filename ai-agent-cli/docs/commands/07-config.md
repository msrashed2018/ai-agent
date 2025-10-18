# Config Commands

Local CLI configuration management. These commands manage the CLI's local settings and authentication tokens stored in `~/.ai-agent-cli/config.json`.

**Note**: These commands do NOT interact with the API service. They only manage local CLI configuration.

---

## Commands Overview

| CLI Command | Description | API Call? |
|------------|-------------|-----------|
| `ai-agent config show` | Show current configuration | No |
| `ai-agent config set-api-url <url>` | Set API base URL | No |
| `ai-agent config get-api-url` | Get current API URL | No |
| `ai-agent config reset` | Reset to default settings | No |

---

## Configuration File

**Location**: `~/.ai-agent-cli/config.json`

**Structure**:
```json
{
  "api_url": "http://localhost:8000",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-uuid",
    "email": "admin@example.com",
    "role": "admin"
  },
  "last_updated": "2025-01-15T10:30:00Z"
}
```

**Permissions**: `0600` (read/write for owner only)

---

## 1. Show Configuration

### CLI Command
```bash
# Show current config
ai-agent config show

# JSON output
ai-agent config show --output json

# Show with tokens (sensitive)
ai-agent config show --show-tokens
```

### What Happens Locally

**Step 1: Read Config File**
```python
import json
from pathlib import Path

config_path = Path.home() / ".ai-agent-cli" / "config.json"

if not config_path.exists():
    print("No configuration found. Run 'ai-agent auth login' first.")
    return

with open(config_path, 'r') as f:
    config = json.load(f)
```

**Step 2: Mask Sensitive Data**
```python
# Mask tokens by default
if not show_tokens:
    if config.get("access_token"):
        config["access_token"] = config["access_token"][:20] + "..."
    if config.get("refresh_token"):
        config["refresh_token"] = config["refresh_token"][:20] + "..."
```

**Step 3: Display Configuration**

Terminal output:
```
CLI Configuration
═══════════════════

API URL: http://localhost:8000
Status: Authenticated

User:
  ID: user-uuid
  Email: admin@example.com
  Role: admin

Tokens:
  Access Token: eyJhbGciOiJIUzI1NiI...
  Refresh Token: eyJhbGciOiJIUzI1NiI...

Last Updated: 2025-01-15T10:30:00Z
```

JSON output:
```json
{
  "api_url": "http://localhost:8000",
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "eyJhbGciOiJIUzI1NiI...",
  "user": {
    "id": "user-uuid",
    "email": "admin@example.com",
    "role": "admin"
  },
  "last_updated": "2025-01-15T10:30:00Z"
}
```

### Key Files
- Config manager: [ai_agent_cli/core/config.py](../../ai-agent-cli/ai_agent_cli/core/config.py)

---

## 2. Set API URL

### CLI Command
```bash
# Set API URL
ai-agent config set-api-url http://localhost:8000

# Set production URL
ai-agent config set-api-url https://api.example.com

# Set with validation
ai-agent config set-api-url https://api.example.com --validate
```

### What Happens Locally

**Step 1: Validate URL Format**
```python
from urllib.parse import urlparse

parsed = urlparse(url)
if not parsed.scheme in ['http', 'https']:
    raise ValueError("URL must start with http:// or https://")
if not parsed.netloc:
    raise ValueError("Invalid URL format")
```

**Step 2: Optional Health Check**
```python
if validate:
    # Try calling health endpoint
    import httpx
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        if response.status_code != 200:
            print(f"Warning: API health check failed (status {response.status_code})")
    except Exception as e:
        print(f"Warning: Could not reach API: {e}")
        # Ask user if they want to continue
```

**Step 3: Update Config File**
```python
config_path = Path.home() / ".ai-agent-cli" / "config.json"

# Load existing config
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    config = {}

# Update API URL
config["api_url"] = url
config["last_updated"] = datetime.utcnow().isoformat()

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

# Set file permissions to 0600
config_path.chmod(0o600)
```

**Step 4: Clear Tokens (if URL changed)**
```python
# If API URL changed, clear existing tokens
# User must re-authenticate
if old_url != url:
    config["access_token"] = None
    config["refresh_token"] = None
    config["user"] = None
    print("API URL changed. Please run 'ai-agent auth login' to re-authenticate.")
```

### Output
```
✓ API URL updated: https://api.example.com
⚠ Tokens cleared. Run 'ai-agent auth login' to re-authenticate.
```

### Key Files
- Config manager: [ai_agent_cli/core/config.py](../../ai-agent-cli/ai_agent_cli/core/config.py)
- Command handler: [ai_agent_cli/commands/config.py](../../ai-agent-cli/ai_agent_cli/commands/config.py)

---

## 3. Get API URL

### CLI Command
```bash
# Get current API URL
ai-agent config get-api-url

# Output as URL only (for scripting)
ai-agent config get-api-url --plain
```

### What Happens Locally

**Step 1: Read Config**
```python
config_path = Path.home() / ".ai-agent-cli" / "config.json"

if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
        api_url = config.get("api_url", "http://localhost:8000")
else:
    api_url = "http://localhost:8000"  # Default
```

**Step 2: Display**

Normal output:
```
Current API URL: http://localhost:8000
```

Plain output (for scripting):
```
http://localhost:8000
```

### Usage in Scripts
```bash
# Get API URL for use in scripts
API_URL=$(ai-agent config get-api-url --plain)
echo "Connecting to: $API_URL"

# Test connectivity
curl -f "$API_URL/health" || echo "API not reachable"
```

---

## 4. Reset Configuration

### CLI Command
```bash
# Reset to defaults (with confirmation)
ai-agent config reset

# Skip confirmation
ai-agent config reset --force

# Reset only tokens (keep API URL)
ai-agent config reset --tokens-only
```

### What Happens Locally

**Step 1: Confirm Action**
```python
if not force:
    response = input("This will clear all configuration including tokens. Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
```

**Step 2: Reset Config File**

Full reset:
```python
config_path = Path.home() / ".ai-agent-cli" / "config.json"

# Create default config
default_config = {
    "api_url": "http://localhost:8000",
    "access_token": None,
    "refresh_token": None,
    "user": None,
    "last_updated": datetime.utcnow().isoformat()
}

# Write default config
with open(config_path, 'w') as f:
    json.dump(default_config, f, indent=2)

config_path.chmod(0o600)
```

Tokens only:
```python
# Keep existing config, only clear tokens
with open(config_path, 'r') as f:
    config = json.load(f)

config["access_token"] = None
config["refresh_token"] = None
config["user"] = None
config["last_updated"] = datetime.utcnow().isoformat()

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
```

**Step 3: Confirmation**
```
✓ Configuration reset to defaults
  API URL: http://localhost:8000
  Run 'ai-agent auth login' to authenticate.
```

---

## Environment Variable Overrides

The CLI supports environment variables that override config file settings:

### `AI_AGENT_API_URL`
```bash
# Temporarily use different API
export AI_AGENT_API_URL=https://staging-api.example.com
ai-agent sessions list  # Uses staging API

# Or inline
AI_AGENT_API_URL=https://staging-api.example.com ai-agent sessions list
```

### `AI_AGENT_ACCESS_TOKEN`
```bash
# Use token from environment (for CI/CD)
export AI_AGENT_ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
ai-agent sessions list  # Uses token from env

# Or inline
AI_AGENT_ACCESS_TOKEN="..." ai-agent admin stats
```

### Priority Order

Configuration values are resolved in this order (highest to lowest):

1. Environment variables (`AI_AGENT_API_URL`, `AI_AGENT_ACCESS_TOKEN`)
2. Config file (`~/.ai-agent-cli/config.json`)
3. Default values (`http://localhost:8000`)

### Implementation

From [ai_agent_cli/core/config.py](../../ai-agent-cli/ai_agent_cli/core/config.py):

```python
class ConfigManager:
    def get_api_url(self) -> str:
        """Get API URL with env var override."""
        # Check environment variable first
        if "AI_AGENT_API_URL" in os.environ:
            return os.environ["AI_AGENT_API_URL"]

        # Check config file
        config = self._load_config()
        if config and "api_url" in config:
            return config["api_url"]

        # Return default
        return "http://localhost:8000"

    def get_access_token(self) -> Optional[str]:
        """Get access token with env var override."""
        # Check environment variable first
        if "AI_AGENT_ACCESS_TOKEN" in os.environ:
            return os.environ["AI_AGENT_ACCESS_TOKEN"]

        # Check config file
        config = self._load_config()
        if config and "access_token" in config:
            return config["access_token"]

        return None
```

---

## Examples

### Example 1: Setup for Different Environments

```bash
# Development (default)
ai-agent config set-api-url http://localhost:8000
ai-agent auth login

# Staging
ai-agent config set-api-url https://staging-api.example.com
ai-agent auth login

# Production
ai-agent config set-api-url https://api.example.com
ai-agent auth login

# Check current config
ai-agent config show
```

### Example 2: CI/CD Pipeline

```bash
#!/bin/bash
# CI/CD script using environment variables

export AI_AGENT_API_URL="https://api.example.com"
export AI_AGENT_ACCESS_TOKEN="$CI_API_TOKEN"  # From CI secrets

# Run automated task
ai-agent tasks execute task-health-check --wait

# Get results
ai-agent tasks execution-status execution-id
```

### Example 3: Multiple Profiles

```bash
# Create profile switcher script
cat > switch-profile.sh <<'EOF'
#!/bin/bash
PROFILE=$1

case $PROFILE in
  dev)
    ai-agent config set-api-url http://localhost:8000
    ;;
  staging)
    ai-agent config set-api-url https://staging-api.example.com
    ;;
  prod)
    ai-agent config set-api-url https://api.example.com
    ;;
  *)
    echo "Usage: $0 {dev|staging|prod}"
    exit 1
    ;;
esac

ai-agent config show
EOF

chmod +x switch-profile.sh

# Use it
./switch-profile.sh dev
./switch-profile.sh prod
```

### Example 4: Backup and Restore Config

```bash
# Backup config
cp ~/.ai-agent-cli/config.json ~/config-backup.json

# Restore config
cp ~/config-backup.json ~/.ai-agent-cli/config.json
chmod 600 ~/.ai-agent-cli/config.json

# Or reset and restore selectively
ai-agent config reset
ai-agent config set-api-url $(jq -r '.api_url' ~/config-backup.json)
# Then re-authenticate
ai-agent auth login
```

---

## Troubleshooting

### Config File Not Found
```bash
# Error: No configuration found
# Solution: Login to create config
ai-agent auth login
```

### Permission Denied
```bash
# Error: Permission denied accessing config file
# Solution: Fix permissions
chmod 600 ~/.ai-agent-cli/config.json
```

### Invalid API URL
```bash
# Error: Could not connect to API
# Solution: Verify URL and test manually
ai-agent config get-api-url
curl $(ai-agent config get-api-url --plain)/health

# Update if incorrect
ai-agent config set-api-url http://correct-url:8000
```

### Token Expired
```bash
# Error: 401 Unauthorized
# Solution: Refresh or re-login
ai-agent auth refresh
# Or
ai-agent auth login
```

### Multiple Environments Confusion
```bash
# Check where you're pointing
ai-agent config show

# Verify with health check
curl $(ai-agent config get-api-url --plain)/health

# Or use explicit env var
AI_AGENT_API_URL=http://localhost:8000 ai-agent sessions list
```

---

## Security Best Practices

### 1. File Permissions
```bash
# Config file should be 0600 (owner read/write only)
ls -la ~/.ai-agent-cli/config.json
# -rw------- 1 user user 456 Jan 15 10:30 config.json

# Fix if needed
chmod 600 ~/.ai-agent-cli/config.json
```

### 2. Don't Commit Tokens
```bash
# Never commit config.json to git
echo "config.json" >> .gitignore

# Use environment variables for CI/CD
# Never hardcode tokens in scripts
```

### 3. Rotate Tokens Regularly
```bash
# Logout and re-login to get fresh tokens
ai-agent auth logout
ai-agent auth login
```

### 4. Separate Profiles for Environments
```bash
# Use different user accounts for prod vs dev
# Don't use prod tokens on dev machines
```

---

## Notes

- **Local Only**: Config commands don't make API calls
- **Token Storage**: Tokens stored in plaintext in config file (secure file permissions required)
- **Environment Variables**: Override config file for CI/CD and multi-environment usage
- **Auto-Creation**: Config file created automatically on first `auth login`
- **No Remote Sync**: Config is local only, not synced between machines
