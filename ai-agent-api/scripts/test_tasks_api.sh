#!/bin/bash
#
# Task API Testing Script
#
# Usage:
#   ./scripts/test_tasks_api.sh              # Interactive menu
#   ./scripts/test_tasks_api.sh list         # List all tasks
#   ./scripts/test_tasks_api.sh execute <task_id> <variables_json>
#   ./scripts/test_tasks_api.sh status <execution_id>
#
# Description:
#   Comprehensive testing script for Tasks API endpoints
#

set -euo pipefail

# Configuration
API_URL="${AI_AGENT_API_URL:-http://localhost:8000}"
TOKEN="${AI_AGENT_ADMIN_ACCESS_TOKEN:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Load token
if [[ -z "$TOKEN" ]]; then
    if [[ -f ".env.tokens" ]]; then
        source .env.tokens
        TOKEN="$AI_AGENT_ADMIN_ACCESS_TOKEN"
    fi

    if [[ -z "$TOKEN" ]]; then
        echo -e "${RED}Error: No authentication token found${NC}" >&2
        echo "Run 'make login-admin' first" >&2
        exit 1
    fi
fi

# API helpers
api_get() {
    curl -s -X GET "${API_URL}$1" -H "Authorization: Bearer ${TOKEN}"
}

api_post() {
    local endpoint="$1"
    local data="$2"
    curl -s -X POST "${API_URL}${endpoint}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$data"
}

# List all tasks
list_tasks() {
    echo -e "${BOLD}${CYAN}Fetching tasks...${NC}"
    local response=$(api_get "/api/v1/tasks")

    echo "$response" | jq -r '
        "Total Tasks: \(.total)\n",
        (.items[] |
            "─────────────────────────────────────────",
            "ID: \(.id)",
            "Name: \(.name)",
            "Description: \(.description[:80])",
            "Tags: \(.tags | join(", "))",
            "Scheduled: \(.is_scheduled)",
            "Active: \(.is_active)",
            "Created: \(.created_at)",
            ""
        )
    '
}

# Get task details
get_task() {
    local task_id="$1"
    echo -e "${BOLD}${CYAN}Fetching task ${task_id}...${NC}"
    api_get "/api/v1/tasks/${task_id}" | jq '.'
}

# Execute task
execute_task() {
    local task_id="$1"
    local variables="${2:-{}}"

    echo -e "${BOLD}${CYAN}Executing task ${task_id}...${NC}"
    echo -e "${BOLD}Variables:${NC} $variables"
    echo

    local response=$(api_post "/api/v1/tasks/${task_id}/execute" "{\"variables\": $variables}")

    # Check for errors
    if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
        echo -e "${RED}Error: $(echo "$response" | jq -r '.detail')${NC}"
        return 1
    fi

    echo -e "${GREEN}Task execution started!${NC}"
    echo

    # Extract key info
    local execution_id=$(echo "$response" | jq -r '.id')
    local session_id=$(echo "$response" | jq -r '.session_id')
    local status=$(echo "$response" | jq -r '.status')

    echo -e "${BOLD}Execution ID:${NC} $execution_id"
    echo -e "${BOLD}Session ID:${NC}   $session_id"
    echo -e "${BOLD}Status:${NC}       $status"
    echo

    # Save for later reference
    echo "$execution_id" > /tmp/last_execution_id
    echo "$session_id" > /tmp/last_session_id

    echo -e "${BOLD}${YELLOW}Monitor execution:${NC}"
    echo "  ./scripts/test_tasks_api.sh status $execution_id"
    echo "  ./scripts/monitor_session.sh $session_id"
    echo "  ./scripts/monitor_session.sh $session_id --watch"
    echo
}

# Get execution status
get_execution_status() {
    local execution_id="$1"

    echo -e "${BOLD}${CYAN}Fetching execution status...${NC}"
    local response=$(api_get "/api/v1/task-executions/${execution_id}")

    # Check for errors
    if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
        echo -e "${RED}Error: $(echo "$response" | jq -r '.detail')${NC}"
        return 1
    fi

    echo "$response" | jq -r '
        "Execution ID: \(.id)",
        "Task ID: \(.task_id)",
        "Session ID: \(.session_id)",
        "Status: \(.status)",
        "Trigger Type: \(.trigger_type)",
        "Variables: \(.variables | tostring)",
        "Started: \(.started_at)",
        "Completed: \(.completed_at // "N/A")",
        "Duration: \(.duration_seconds // "N/A") seconds",
        "Error: \(.error_message // "None")",
        "",
        "Links:",
        "  Session: \(._links.session)",
        "  Report: \(._links.report // "N/A")"
    '

    # Extract session ID for monitoring
    local session_id=$(echo "$response" | jq -r '.session_id')
    local status=$(echo "$response" | jq -r '.status')

    if [[ "$status" == "completed" ]]; then
        echo
        echo -e "${GREEN}✓ Execution completed successfully!${NC}"
    elif [[ "$status" == "failed" ]]; then
        echo
        echo -e "${RED}✗ Execution failed${NC}"
    elif [[ "$status" == "running" ]]; then
        echo
        echo -e "${YELLOW}⟳ Execution still running...${NC}"
        echo "Monitor with: ./scripts/monitor_session.sh $session_id --watch"
    fi
}

# List task executions
list_executions() {
    local task_id="$1"

    echo -e "${BOLD}${CYAN}Fetching executions for task ${task_id}...${NC}"
    local response=$(api_get "/api/v1/tasks/${task_id}/executions")

    echo "$response" | jq -r '
        "Total Executions: \(.total)\n",
        (.items[] |
            "─────────────────────────────────────────",
            "Execution ID: \(.id)",
            "Status: \(.status)",
            "Trigger: \(.trigger_type)",
            "Started: \(.started_at)",
            "Duration: \(.duration_seconds // "N/A")s",
            ""
        )
    '
}

# Interactive menu
interactive_menu() {
    while true; do
        echo
        echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"
        echo -e "${BOLD}${CYAN}       Tasks API Testing Menu${NC}"
        echo -e "${BOLD}${CYAN}═══════════════════════════════════════${NC}"
        echo
        echo "1. List all tasks"
        echo "2. Get task details"
        echo "3. Execute task"
        echo "4. Get execution status"
        echo "5. List task executions"
        echo "6. Monitor session (last execution)"
        echo "0. Exit"
        echo

        read -p "Select option: " choice

        case "$choice" in
            1)
                list_tasks
                ;;
            2)
                read -p "Enter task ID: " task_id
                get_task "$task_id"
                ;;
            3)
                read -p "Enter task ID: " task_id
                read -p "Enter variables (JSON, or press Enter for {}): " variables
                variables="${variables:-{}}"
                execute_task "$task_id" "$variables"
                ;;
            4)
                if [[ -f /tmp/last_execution_id ]]; then
                    default_id=$(cat /tmp/last_execution_id)
                    read -p "Enter execution ID [$default_id]: " execution_id
                    execution_id="${execution_id:-$default_id}"
                else
                    read -p "Enter execution ID: " execution_id
                fi
                get_execution_status "$execution_id"
                ;;
            5)
                read -p "Enter task ID: " task_id
                list_executions "$task_id"
                ;;
            6)
                if [[ -f /tmp/last_session_id ]]; then
                    session_id=$(cat /tmp/last_session_id)
                    echo "Monitoring session: $session_id"
                    "${SCRIPT_DIR}/monitor_session.sh" "$session_id" --watch
                else
                    echo -e "${RED}No recent session found${NC}"
                fi
                ;;
            0)
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac
    done
}

# Command line mode
if [[ $# -eq 0 ]]; then
    interactive_menu
else
    case "$1" in
        list)
            list_tasks
            ;;
        get)
            get_task "$2"
            ;;
        execute)
            execute_task "$2" "${3:-{}}"
            ;;
        status)
            get_execution_status "$2"
            ;;
        executions)
            list_executions "$2"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Usage: $0 [list|get|execute|status|executions]"
            exit 1
            ;;
    esac
fi
