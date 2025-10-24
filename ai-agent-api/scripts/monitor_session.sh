#!/bin/bash
#
# Session Monitoring Script
#
# Usage:
#   ./scripts/monitor_session.sh <session_id>
#   ./scripts/monitor_session.sh <session_id> --watch
#   ./scripts/monitor_session.sh <session_id> --claude-logs
#
# Description:
#   Fetches complete session status including:
#   - Session details
#   - Messages
#   - Tool calls
#   - Audit logs
#   - Working directory contents
#   - Claude Code CLI logs (if available)
#

set -euo pipefail

# Configuration
API_URL="${AI_AGENT_API_URL:-http://localhost:8000}"
TOKEN="${AI_AGENT_ADMIN_ACCESS_TOKEN:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Check dependencies
command -v jq >/dev/null 2>&1 || { echo "Error: jq is required but not installed." >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "Error: curl is required but not installed." >&2; exit 1; }

# Usage
usage() {
    cat <<EOF
${BOLD}Session Monitoring Script${NC}

${BOLD}USAGE:${NC}
    $0 <session_id> [OPTIONS]

${BOLD}OPTIONS:${NC}
    --watch             Watch session in real-time (refreshes every 2 seconds)
    --claude-logs       Show Claude Code CLI logs
    --messages          Show only messages
    --tools             Show only tool calls
    --json              Output raw JSON
    --help              Show this help message

${BOLD}EXAMPLES:${NC}
    # Full session status
    $0 770e8400-e29b-41d4-a716-446655440002

    # Watch session execution in real-time
    $0 770e8400-e29b-41d4-a716-446655440002 --watch

    # View Claude Code CLI logs
    $0 770e8400-e29b-41d4-a716-446655440002 --claude-logs

    # Export as JSON
    $0 770e8400-e29b-41d4-a716-446655440002 --json > session.json

${BOLD}ENVIRONMENT VARIABLES:${NC}
    AI_AGENT_API_URL              API base URL (default: http://localhost:8000)
    AI_AGENT_ADMIN_ACCESS_TOKEN   Bearer token for authentication

EOF
    exit 0
}

# Parse arguments
SESSION_ID=""
MODE="full"
WATCH=false
SHOW_CLAUDE_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            usage
            ;;
        --watch|-w)
            WATCH=true
            shift
            ;;
        --claude-logs|-c)
            SHOW_CLAUDE_LOGS=true
            shift
            ;;
        --messages|-m)
            MODE="messages"
            shift
            ;;
        --tools|-t)
            MODE="tools"
            shift
            ;;
        --json|-j)
            MODE="json"
            shift
            ;;
        *)
            if [[ -z "$SESSION_ID" ]]; then
                SESSION_ID="$1"
            else
                echo -e "${RED}Error: Unknown argument '$1'${NC}" >&2
                usage
            fi
            shift
            ;;
    esac
done

if [[ -z "$SESSION_ID" ]]; then
    echo -e "${RED}Error: session_id is required${NC}" >&2
    usage
fi

if [[ -z "$TOKEN" ]]; then
    # Try to load from .env.tokens
    if [[ -f ".env.tokens" ]]; then
        source .env.tokens
        TOKEN="$AI_AGENT_ADMIN_ACCESS_TOKEN"
    fi

    if [[ -z "$TOKEN" ]]; then
        echo -e "${RED}Error: No authentication token found${NC}" >&2
        echo "Set AI_AGENT_ADMIN_ACCESS_TOKEN environment variable or run 'make login-admin'" >&2
        exit 1
    fi
fi

# API call helper
api_get() {
    local endpoint="$1"
    curl -s -X GET "${API_URL}${endpoint}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Accept: application/json"
}

# Get session details
get_session() {
    api_get "/api/v1/sessions/${SESSION_ID}"
}

# Get session messages
get_messages() {
    api_get "/api/v1/sessions/${SESSION_ID}/messages?page=1&page_size=1000"
}

# Get tool calls
get_tool_calls() {
    api_get "/api/v1/sessions/${SESSION_ID}/tool-calls?page=1&page_size=1000"
}

# Get audit logs for session
get_audit_logs() {
    api_get "/api/v1/admin/audit-logs?resource_type=session&resource_id=${SESSION_ID}&page=1&page_size=100"
}

# Find Claude Code CLI log file
find_claude_log() {
    local working_dir="$1"

    # Convert working directory to project hash
    # /workspace/... -> -workspace-...
    local project_hash=$(echo "$working_dir" | sed 's|^/|-|' | tr '/' '-')

    local claude_log_dir="$HOME/.claude/projects/$project_hash"
    local claude_log_file="${claude_log_dir}/${SESSION_ID}.jsonl"

    if [[ -f "$claude_log_file" ]]; then
        echo "$claude_log_file"
    else
        echo ""
    fi
}

# Display session summary
display_session() {
    local session_json="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    SESSION STATUS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    # Basic info
    echo -e "${BOLD}Session ID:${NC}       $(echo "$session_json" | jq -r '.id')"
    echo -e "${BOLD}User ID:${NC}          $(echo "$session_json" | jq -r '.user_id')"
    echo -e "${BOLD}Name:${NC}             $(echo "$session_json" | jq -r '.name')"

    # Status with color
    local status=$(echo "$session_json" | jq -r '.status')
    local status_color="$NC"
    case "$status" in
        active)
            status_color="$GREEN"
            ;;
        processing)
            status_color="$YELLOW"
            ;;
        failed)
            status_color="$RED"
            ;;
        terminated)
            status_color="$MAGENTA"
            ;;
    esac
    echo -e "${BOLD}Status:${NC}           ${status_color}${status}${NC}"

    echo -e "${BOLD}Mode:${NC}             $(echo "$session_json" | jq -r '.mode')"
    echo -e "${BOLD}Created:${NC}          $(echo "$session_json" | jq -r '.created_at')"
    echo -e "${BOLD}Last Active:${NC}      $(echo "$session_json" | jq -r '.last_active_at // "N/A"')"

    # Error message if failed
    local error_msg=$(echo "$session_json" | jq -r '.error_message // empty')
    if [[ -n "$error_msg" ]]; then
        echo -e "${BOLD}${RED}Error:${NC}            $error_msg"
    fi

    echo

    # Metrics
    echo -e "${BOLD}${BLUE}Metrics:${NC}"
    echo -e "  Message Count:    $(echo "$session_json" | jq -r '.message_count')"
    echo -e "  Tool Call Count:  $(echo "$session_json" | jq -r '.tool_call_count')"
    echo -e "  Total Tokens:     $(echo "$session_json" | jq -r '.total_tokens')"
    echo -e "  Input Tokens:     $(echo "$session_json" | jq -r '.input_tokens')"
    echo -e "  Output Tokens:    $(echo "$session_json" | jq -r '.output_tokens')"
    echo -e "  Total Cost:       \$$(echo "$session_json" | jq -r '.total_cost')"
    echo

    # Working directory
    local working_dir=$(echo "$session_json" | jq -r '.working_directory_path')
    echo -e "${BOLD}${BLUE}Working Directory:${NC}"
    echo -e "  Path: $working_dir"
    if [[ -d "$working_dir" ]]; then
        echo -e "  ${GREEN}✓ Exists${NC}"
        echo -e "  Files: $(find "$working_dir" -type f 2>/dev/null | wc -l)"
    else
        echo -e "  ${RED}✗ Does not exist${NC}"
    fi
    echo

    # SDK Options
    echo -e "${BOLD}${BLUE}SDK Configuration:${NC}"
    echo "$session_json" | jq -r '.sdk_options | {
        model,
        max_tokens,
        allowed_tools: .allowed_tools[:3],
        mcp_servers: .mcp_servers | keys
    }' | sed 's/^/  /'
    echo
}

# Display messages
display_messages() {
    local messages_json="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    MESSAGES${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    local total=$(echo "$messages_json" | jq -r '.total')
    echo -e "${BOLD}Total Messages:${NC} $total"
    echo

    echo "$messages_json" | jq -r '.items[] |
        "[\(.sequence_number)] \(.message_type | ascii_upcase) - \(.created_at)\n" +
        "Content: \(.content[:200])\(.content | if length > 200 then "..." else "" end)\n"
    '
}

# Display tool calls
display_tool_calls() {
    local tool_calls_json="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    TOOL CALLS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    local total=$(echo "$tool_calls_json" | jq -r '.total')
    echo -e "${BOLD}Total Tool Calls:${NC} $total"
    echo

    echo "$tool_calls_json" | jq -r '.items[] |
        "Tool: \(.tool_name)\n" +
        "Status: \(.status)\n" +
        "Started: \(.started_at)\n" +
        "Duration: \(.duration_ms)ms\n" +
        "Input: \(.tool_input | tostring | .[0:150])\n" +
        "Output: \(.tool_output // "N/A" | tostring | .[0:150])\n" +
        "---"
    '
}

# Display Claude Code CLI logs
display_claude_logs() {
    local working_dir="$1"

    local log_file=$(find_claude_log "$working_dir")

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                 CLAUDE CODE CLI LOGS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    if [[ -z "$log_file" ]]; then
        echo -e "${YELLOW}Claude Code CLI log file not found${NC}"
        echo "Expected locations searched:"
        local project_hash=$(echo "$working_dir" | sed 's|^/|-|' | tr '/' '-')
        echo "  $HOME/.claude/projects/$project_hash/${SESSION_ID}.jsonl"
        return
    fi

    echo -e "${BOLD}Log File:${NC} $log_file"
    echo -e "${BOLD}Size:${NC} $(du -h "$log_file" | cut -f1)"
    echo

    echo -e "${BOLD}Recent Entries:${NC}"
    tail -n 50 "$log_file" | jq -C '.' 2>/dev/null || cat "$log_file" | tail -n 50
}

# Main monitoring function
monitor_session() {
    # Fetch all data
    local session_json=$(get_session)

    # Check if session exists
    if echo "$session_json" | jq -e '.detail' >/dev/null 2>&1; then
        echo -e "${RED}Error: $(echo "$session_json" | jq -r '.detail')${NC}" >&2
        exit 1
    fi

    # Mode selection
    case "$MODE" in
        json)
            # Full JSON output
            echo "$session_json" | jq '.'
            ;;
        messages)
            local messages_json=$(get_messages)
            display_messages "$messages_json"
            ;;
        tools)
            local tool_calls_json=$(get_tool_calls)
            display_tool_calls "$tool_calls_json"
            ;;
        full)
            # Clear screen if watching
            if [[ "$WATCH" == "true" ]]; then
                clear
            fi

            # Display session summary
            display_session "$session_json"

            # Display messages
            local messages_json=$(get_messages)
            display_messages "$messages_json"
            echo

            # Display tool calls
            local tool_calls_json=$(get_tool_calls)
            display_tool_calls "$tool_calls_json"
            echo

            # Display Claude logs if requested
            if [[ "$SHOW_CLAUDE_LOGS" == "true" ]]; then
                local working_dir=$(echo "$session_json" | jq -r '.working_directory_path')
                display_claude_logs "$working_dir"
            fi
            ;;
    esac
}

# Watch mode
if [[ "$WATCH" == "true" ]]; then
    while true; do
        monitor_session
        sleep 2
    done
else
    monitor_session
fi
