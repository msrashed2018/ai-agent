#!/bin/bash
# Example: MCP server management workflow

set -e

echo "=== AI Agent CLI MCP Server Management Example ==="

# 1. List existing servers
echo -e "\n1. Listing existing MCP servers..."
ai-agent mcp list --format table

# 2. Create a new MCP server
echo -e "\n2. Creating new MCP server..."
SERVER_OUTPUT=$(ai-agent mcp create \
  --name "example-mcp-server" \
  --description "Example MCP server for testing" \
  --server-type stdio \
  --config '{"command":"npx","args":["-y","@modelcontextprotocol/server-filesystem","/tmp"],"env":{}}' \
  --enabled \
  --format json)

SERVER_ID=$(echo $SERVER_OUTPUT | jq -r '.id')
echo "MCP server created: $SERVER_ID"

# 3. Get server details
echo -e "\n3. Getting server details..."
ai-agent mcp get $SERVER_ID --format table

# 4. Perform health check
echo -e "\n4. Performing health check..."
ai-agent mcp health-check $SERVER_ID --format table

# 5. Update server (disable it)
echo -e "\n5. Disabling server..."
ai-agent mcp update $SERVER_ID --enabled false --format table

# 6. List templates
echo -e "\n6. Listing available MCP server templates..."
ai-agent mcp templates --format json | jq -r '.templates[] | "\(.name): \(.description)"'

# 7. Export configuration
echo -e "\n7. Exporting configuration..."
ai-agent mcp export --output /tmp/mcp-export.json --include-global
echo "Configuration exported to: /tmp/mcp-export.json"
cat /tmp/mcp-export.json | jq '.'

# 8. Import configuration (example - commented out to avoid errors)
echo -e "\n8. Import example (commented out):"
echo "# ai-agent mcp import ~/Library/Application\ Support/Claude/claude_desktop_config.json"

echo -e "\n=== MCP server management workflow complete! ==="
echo "Note: To delete the server, run: ai-agent mcp delete $SERVER_ID --yes"
