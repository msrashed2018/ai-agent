#!/bin/bash
# Example: Complete session workflow

set -e

echo "=== AI Agent CLI Session Workflow Example ==="

# 1. Create a session
echo -e "\n1. Creating session..."
SESSION_OUTPUT=$(ai-agent sessions create \
  --name "Example Session" \
  --description "Testing CLI functionality" \
  --format json)

SESSION_ID=$(echo $SESSION_OUTPUT | jq -r '.id')
echo "Session created: $SESSION_ID"

# 2. Send a query
echo -e "\n2. Sending query..."
ai-agent sessions query $SESSION_ID "What is the current date and time?"

# 3. List messages
echo -e "\n3. Listing messages..."
ai-agent sessions messages $SESSION_ID --limit 10 --format table

# 4. List tool calls
echo -e "\n4. Listing tool calls..."
ai-agent sessions tool-calls $SESSION_ID --format table

# 5. Get session details
echo -e "\n5. Getting session details..."
ai-agent sessions get $SESSION_ID --format table

# 6. Pause session
echo -e "\n6. Pausing session..."
ai-agent sessions pause $SESSION_ID

# 7. Resume session
echo -e "\n7. Resuming session..."
ai-agent sessions resume $SESSION_ID

# 8. Download working directory
echo -e "\n8. Downloading working directory..."
ai-agent sessions download-workdir $SESSION_ID --output /tmp/session-workdir.tar.gz
echo "Downloaded to: /tmp/session-workdir.tar.gz"

# 9. Terminate session
echo -e "\n9. Terminating session..."
ai-agent sessions terminate $SESSION_ID --yes

echo -e "\n=== Workflow complete! ==="
