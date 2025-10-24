#!/bin/bash
#
# Task Execution Monitoring Script (with Celery integration)
#
# Usage:
#   ./scripts/monitor_task_execution.sh <execution_id>
#   ./scripts/monitor_task_execution.sh <execution_id> --watch
#   ./scripts/monitor_task_execution.sh <execution_id> --api-logs
#   ./scripts/monitor_task_execution.sh <execution_id> --full
#
# Description:
#   Monitors task execution progress including:
#   - Execution status and metrics
#   - Celery task status
#   - Session details
#   - API logs (errors and task-related entries)
#   - Claude Code CLI logs
#
# Author: AI Agent System
# Date: 2025-10-24
#

set -euo pipefail

# Configuration
API_URL="${AI_AGENT_API_URL:-http://localhost:8000}"
TOKEN="${AI_AGENT_ADMIN_ACCESS_TOKEN:-}"
LOG_FILE="${AI_AGENT_LOG_FILE:-logs/api.log}"
LOG_LINES="${AI_AGENT_LOG_LINES:-100}"
MONITOR_LOG_DIR="${AI_AGENT_MONITOR_LOG_DIR:-logs/monitoring}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create monitoring log directory if it doesn't exist
mkdir -p "$MONITOR_LOG_DIR" 2>/dev/null || true

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
${BOLD}Task Execution Monitoring Script${NC}

${BOLD}USAGE:${NC}
    $0 <execution_id> [OPTIONS]

${BOLD}OPTIONS:${NC}
    --watch             Watch execution in real-time (refreshes every 3 seconds)
    --api-logs          Show API logs (tail ${LOG_LINES} lines)
    --full              Show complete monitoring (execution + session + logs)
    --json              Output raw JSON
    --help              Show this help message

${BOLD}EXAMPLES:${NC}
    # Basic execution status
    $0 123e4567-e89b-12d3-a456-426614174000

    # Watch execution in real-time
    $0 123e4567-e89b-12d3-a456-426614174000 --watch

    # Full monitoring with API logs
    $0 123e4567-e89b-12d3-a456-426614174000 --full

    # API logs only
    $0 123e4567-e89b-12d3-a456-426614174000 --api-logs

${BOLD}ENVIRONMENT VARIABLES:${NC}
    AI_AGENT_API_URL              API base URL (default: http://localhost:8000)
    AI_AGENT_ADMIN_ACCESS_TOKEN   Bearer token for authentication
    AI_AGENT_LOG_FILE             API log file path (default: logs/api.log)
    AI_AGENT_LOG_LINES            Number of log lines to show (default: 100)
    AI_AGENT_MONITOR_LOG_DIR      Directory for monitoring logs (default: logs/monitoring)

${BOLD}MONITORING LOGS:${NC}
    - Monitoring data is automatically saved to: logs/monitoring/execution_<ID>_<TIMESTAMP>.log
    - Includes execution status, API logs, and JSON data for investigation
    - Watch mode does not create log files (real-time display only)

EOF
    exit 0
}

# Parse arguments
EXECUTION_ID=""
MODE="execution"
WATCH=false
SHOW_API_LOGS=false
SHOW_FULL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            usage
            ;;
        --watch|-w)
            WATCH=true
            shift
            ;;
        --api-logs|-l)
            SHOW_API_LOGS=true
            shift
            ;;
        --full|-f)
            SHOW_FULL=true
            shift
            ;;
        --json|-j)
            MODE="json"
            shift
            ;;
        *)
            if [[ -z "$EXECUTION_ID" ]]; then
                EXECUTION_ID="$1"
            else
                echo -e "${RED}Error: Unknown argument '$1'${NC}" >&2
                usage
            fi
            shift
            ;;
    esac
done

if [[ -z "$EXECUTION_ID" ]]; then
    echo -e "${RED}Error: execution_id is required${NC}" >&2
    usage
fi

# Load token if not set
if [[ -z "$TOKEN" ]]; then
    if [[ -f ".env.tokens" ]]; then
        source .env.tokens
        TOKEN="$AI_AGENT_ADMIN_ACCESS_TOKEN"
    fi

    if [[ -z "$TOKEN" ]]; then
        echo -e "${RED}Error: No authentication token found${NC}" >&2
        echo "Set AI_AGENT_ADMIN_ACCESS_TOKEN or run 'make login-admin'" >&2
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

# Get task execution status
get_execution() {
    api_get "/api/v1/task-executions/${EXECUTION_ID}"
}

# Get session details
get_session() {
    local session_id="$1"
    api_get "/api/v1/sessions/${session_id}"
}

# Display execution status
display_execution() {
    local exec_json="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                TASK EXECUTION STATUS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    # Basic info
    echo -e "${BOLD}Execution ID:${NC}     $(echo "$exec_json" | jq -r '.id')"
    echo -e "${BOLD}Task ID:${NC}          $(echo "$exec_json" | jq -r '.task_id')"
    echo -e "${BOLD}Session ID:${NC}       $(echo "$exec_json" | jq -r '.session_id // "N/A"')"

    # Status with color
    local status=$(echo "$exec_json" | jq -r '.status')
    local status_color="$NC"
    case "$status" in
        pending)
            status_color="$CYAN"
            ;;
        queued)
            status_color="$BLUE"
            ;;
        running)
            status_color="$YELLOW"
            ;;
        completed)
            status_color="$GREEN"
            ;;
        failed)
            status_color="$RED"
            ;;
        cancelled)
            status_color="$MAGENTA"
            ;;
    esac
    echo -e "${BOLD}Status:${NC}           ${status_color}${BOLD}${status^^}${NC}"

    echo -e "${BOLD}Trigger Type:${NC}     $(echo "$exec_json" | jq -r '.trigger_type')"
    echo

    # Celery integration info
    local celery_task_id=$(echo "$exec_json" | jq -r '.celery_task_id // "N/A"')
    local worker_hostname=$(echo "$exec_json" | jq -r '.worker_hostname // "N/A"')
    local retry_count=$(echo "$exec_json" | jq -r '.retry_count // "0"')

    echo -e "${BOLD}${BLUE}Celery Integration:${NC}"
    echo -e "  Celery Task ID:   $celery_task_id"
    echo -e "  Worker Hostname:  $worker_hostname"
    echo -e "  Retry Count:      $retry_count"
    echo

    # Timestamps
    echo -e "${BOLD}${BLUE}Timeline:${NC}"
    echo -e "  Created:          $(echo "$exec_json" | jq -r '.created_at')"
    echo -e "  Queued:           $(echo "$exec_json" | jq -r '.queued_at // "N/A"')"
    echo -e "  Started:          $(echo "$exec_json" | jq -r '.started_at // "N/A"')"
    echo -e "  Completed:        $(echo "$exec_json" | jq -r '.completed_at // "N/A"')"

    local duration=$(echo "$exec_json" | jq -r '.duration_seconds // null')
    if [[ "$duration" != "null" ]]; then
        echo -e "  Duration:         ${duration}s"
    fi
    echo

    # Variables used
    echo -e "${BOLD}${BLUE}Prompt Variables:${NC}"
    echo "$exec_json" | jq -r '.prompt_variables' | sed 's/^/  /'
    echo

    # Result data
    local result_data=$(echo "$exec_json" | jq -r '.result_data // null')
    if [[ "$result_data" != "null" ]]; then
        echo -e "${BOLD}${BLUE}Result Data:${NC}"
        echo "$exec_json" | jq -r '.result_data' | sed 's/^/  /'
        echo
    fi

    # Error message if failed
    local error_msg=$(echo "$exec_json" | jq -r '.error_message // empty')
    if [[ -n "$error_msg" ]]; then
        echo -e "${BOLD}${RED}Error Message:${NC}"
        echo -e "  $error_msg"
        echo
    fi

    # Report link
    local report_id=$(echo "$exec_json" | jq -r '.report_id // null')
    if [[ "$report_id" != "null" ]]; then
        echo -e "${BOLD}${GREEN}Report Generated:${NC} $report_id"
        echo
    fi
}

# Display session summary
display_session_summary() {
    local session_id="$1"

    if [[ "$session_id" == "null" || -z "$session_id" ]]; then
        echo -e "${YELLOW}No session created yet (task still queued)${NC}"
        return
    fi

    local session_json=$(get_session "$session_id")

    # Check if session exists
    if echo "$session_json" | jq -e '.detail' >/dev/null 2>&1; then
        echo -e "${YELLOW}Session not accessible: $(echo "$session_json" | jq -r '.detail')${NC}"
        return
    fi

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    SESSION DETAILS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    echo -e "${BOLD}Session ID:${NC}       $(echo "$session_json" | jq -r '.id')"
    echo -e "${BOLD}Name:${NC}             $(echo "$session_json" | jq -r '.name')"
    echo -e "${BOLD}Status:${NC}           $(echo "$session_json" | jq -r '.status')"
    echo -e "${BOLD}Messages:${NC}         $(echo "$session_json" | jq -r '.message_count')"
    echo -e "${BOLD}Tool Calls:${NC}       $(echo "$session_json" | jq -r '.tool_call_count')"
    echo -e "${BOLD}Total Tokens:${NC}     $(echo "$session_json" | jq -r '.total_tokens')"
    echo -e "${BOLD}Cost:${NC}             \$$(echo "$session_json" | jq -r '.total_cost')"
    echo

    # Working directory
    local working_dir=$(echo "$session_json" | jq -r '.working_directory_path')
    echo -e "${BOLD}Working Dir:${NC}      $working_dir"

    # Claude Code logs path
    local project_hash=$(echo "$working_dir" | sed 's|^/|-|' | tr '/' '-')
    local claude_log_path="$HOME/.claude/projects/$project_hash/${session_id}.jsonl"
    if [[ -f "$claude_log_path" ]]; then
        echo -e "${BOLD}Claude Logs:${NC}      ${GREEN}✓${NC} $claude_log_path"
    else
        echo -e "${BOLD}Claude Logs:${NC}      ${YELLOW}✗ Not found${NC}"
    fi
    echo
}

# Display API logs
display_api_logs() {
    local execution_id="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    API LOGS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    if [[ ! -f "$LOG_FILE" ]]; then
        echo -e "${YELLOW}Log file not found: $LOG_FILE${NC}"
        return
    fi

    echo -e "${BOLD}Log File:${NC} $LOG_FILE"
    echo -e "${BOLD}Lines:${NC}    Last $LOG_LINES"
    echo

    # Show last N lines, with optional filtering for execution ID
    echo -e "${BOLD}Recent API Activity:${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"

    # Try to filter for execution-related logs first
    local filtered_logs=$(tail -n 1000 "$LOG_FILE" | grep -E "$execution_id|task_execution|celery" || true)

    if [[ -n "$filtered_logs" ]]; then
        echo -e "${BOLD}${GREEN}Execution-related logs:${NC}"
        echo "$filtered_logs" | tail -n 50
        echo
    fi

    # Show general recent logs
    echo -e "${BOLD}${BLUE}Recent general logs:${NC}"
    tail -n "$LOG_LINES" "$LOG_FILE" | while IFS= read -r line; do
        # Color-code log levels
        if echo "$line" | grep -q "ERROR"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -q "WARNING"; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -q "INFO"; then
            echo -e "$line"
        else
            echo "$line"
        fi
    done
    echo
}

# Log monitoring data to file
log_monitoring_data() {
    local exec_json="$1"
    local log_file="${MONITOR_LOG_DIR}/execution_${EXECUTION_ID}_${TIMESTAMP}.log"

    {
        echo "==================================================================="
        echo "Task Execution Monitoring Log"
        echo "Generated: $(date)"
        echo "Execution ID: $EXECUTION_ID"
        echo "==================================================================="
        echo
        echo "--- EXECUTION DATA (JSON) ---"
        echo "$exec_json" | jq '.'
        echo
        echo "--- EXECUTION STATUS ---"
        echo "$exec_json" | jq -r '
            "Execution ID: \(.id)",
            "Task ID: \(.task_id)",
            "Session ID: \(.session_id // "N/A")",
            "Status: \(.status)",
            "Trigger Type: \(.trigger_type)",
            "Celery Task ID: \(.celery_task_id // "N/A")",
            "Worker Hostname: \(.worker_hostname // "N/A")",
            "Retry Count: \(.retry_count // 0)",
            "Created: \(.created_at)",
            "Queued: \(.queued_at // "N/A")",
            "Started: \(.started_at // "N/A")",
            "Completed: \(.completed_at // "N/A")",
            "Duration: \(.duration_seconds // "N/A")s",
            "Error: \(.error_message // "None")"
        '
        echo
        echo "--- API LOGS (Last $LOG_LINES lines) ---"
        if [[ -f "$LOG_FILE" ]]; then
            tail -n "$LOG_LINES" "$LOG_FILE"
        else
            echo "Log file not found: $LOG_FILE"
        fi
        echo
        echo "==================================================================="
        echo "End of monitoring log"
        echo "==================================================================="
    } > "$log_file" 2>&1

    echo -e "${GREEN}✓ Monitoring data saved to: $log_file${NC}"
}

# Main monitoring function
monitor_execution() {
    # Fetch execution data
    local exec_json=$(get_execution)

    # Check if execution exists
    if echo "$exec_json" | jq -e '.detail' >/dev/null 2>&1; then
        echo -e "${RED}Error: $(echo "$exec_json" | jq -r '.detail')${NC}" >&2
        exit 1
    fi

    # Log monitoring data to file (unless in watch mode)
    if [[ "$WATCH" != "true" ]] && [[ "$MODE" != "json" ]]; then
        log_monitoring_data "$exec_json"
    fi

    # Mode selection
    case "$MODE" in
        json)
            # Full JSON output
            echo "$exec_json" | jq '.'
            ;;
        execution)
            # Clear screen if watching
            if [[ "$WATCH" == "true" ]]; then
                clear
                echo -e "${BOLD}${MAGENTA}Watching execution ${EXECUTION_ID}... (Ctrl+C to exit)${NC}"
                echo
            fi

            # Display execution status
            display_execution "$exec_json"

            # Display session if requested or if full mode
            if [[ "$SHOW_FULL" == "true" ]]; then
                local session_id=$(echo "$exec_json" | jq -r '.session_id // null')
                display_session_summary "$session_id"
            fi

            # Display API logs if requested or if full mode
            if [[ "$SHOW_API_LOGS" == "true" ]] || [[ "$SHOW_FULL" == "true" ]]; then
                display_api_logs "$EXECUTION_ID"
            fi

            # Show quick help for active executions
            local status=$(echo "$exec_json" | jq -r '.status')
            if [[ "$status" == "queued" ]] || [[ "$status" == "running" ]]; then
                echo -e "${BOLD}${CYAN}Monitoring Commands:${NC}"
                echo -e "  Watch mode:           $0 $EXECUTION_ID --watch"
                echo -e "  With API logs:        $0 $EXECUTION_ID --api-logs"
                echo -e "  Full monitoring:      $0 $EXECUTION_ID --full"

                local session_id=$(echo "$exec_json" | jq -r '.session_id // null')
                if [[ "$session_id" != "null" ]]; then
                    echo -e "  Session details:      ./scripts/monitor_session.sh $session_id"
                fi
                echo
            elif [[ "$status" == "completed" ]]; then
                echo -e "${GREEN}${BOLD}✓ Execution completed successfully!${NC}"
                local session_id=$(echo "$exec_json" | jq -r '.session_id // null')
                if [[ "$session_id" != "null" ]]; then
                    echo -e "View session: ./scripts/monitor_session.sh $session_id"
                fi
                echo
            elif [[ "$status" == "failed" ]]; then
                echo -e "${RED}${BOLD}✗ Execution failed${NC}"
                echo -e "Check logs above for error details"
                echo
            fi
            ;;
    esac
}

# Watch mode
if [[ "$WATCH" == "true" ]]; then
    while true; do
        monitor_execution

        # Check if execution is complete
        local exec_json=$(get_execution)
        local status=$(echo "$exec_json" | jq -r '.status')
        if [[ "$status" == "completed" ]] || [[ "$status" == "failed" ]] || [[ "$status" == "cancelled" ]]; then
            echo -e "${BOLD}${YELLOW}Execution finished. Press Ctrl+C to exit or wait for refresh...${NC}"
        fi

        sleep 3
    done
else
    monitor_execution
fi
