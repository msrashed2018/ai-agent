#!/usr/bin/env python3
"""
AI Agent CLI - Unified command-line interface for AI Agent API

Usage:
    aiagent.py task list
    aiagent.py task create <prompt> [--name NAME] [--tags TAG1,TAG2]
    aiagent.py task execute <task_id> [--variables '{}']
    aiagent.py task status <task_id>

    aiagent.py execution status <execution_id>
    aiagent.py execution monitor <execution_id> [--watch]
    aiagent.py execution logs <execution_id>

    aiagent.py session monitor <session_id> [--watch]
    aiagent.py session messages <session_id>

    aiagent.py health
"""

import sys
import os
import json
import argparse
import requests
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_URL = os.getenv("AI_AGENT_API_URL", "http://localhost:8000")
TOKEN_FILE = Path(".env.tokens")

# ANSI Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def get_token():
    """Load admin token from .env.tokens file."""
    if not TOKEN_FILE.exists():
        print(f"{Colors.RED}Error: No token file found. Run 'make login-admin' first{Colors.NC}")
        sys.exit(1)

    with open(TOKEN_FILE) as f:
        for line in f:
            if line.startswith("AI_AGENT_ADMIN_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip()

    print(f"{Colors.RED}Error: No admin token found in {TOKEN_FILE}{Colors.NC}")
    sys.exit(1)

def api_request(method, endpoint, data=None, params=None):
    """Make API request with authentication."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{API_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}API Error: {e}{Colors.NC}")
        if hasattr(e.response, 'text'):
            print(e.response.text)
        sys.exit(1)

# ============================================================================
# TASK COMMANDS
# ============================================================================

def task_list(args):
    """List all tasks."""
    result = api_request("GET", "/api/v1/tasks")

    print(f"{Colors.BOLD}{Colors.CYAN}Tasks (Total: {result.get('total', 0)}){Colors.NC}")
    print()

    for task in result.get('items', []):
        status_icon = "✓" if task['is_active'] else "✗"
        print(f"{status_icon} {Colors.BOLD}{task['name']}{Colors.NC}")
        print(f"  ID: {task['id']}")
        print(f"  Description: {task.get('description', 'N/A')[:80]}")
        print(f"  Tags: {', '.join(task.get('tags', []))}")
        print(f"  Created: {task['created_at']}")
        print()

def task_create(args):
    """Create a new task."""
    data = {
        "name": args.name,
        "description": args.description or "",
        "prompt_template": args.prompt,
        "allowed_tools": args.tools.split(",") if args.tools else [],
        "sdk_options": {},
        "is_scheduled": False,
        "generate_report": args.report,
        "report_format": args.report_format,
        "tags": args.tags.split(",") if args.tags else []
    }

    result = api_request("POST", "/api/v1/tasks", data=data)

    print(f"{Colors.GREEN}✓ Task created successfully!{Colors.NC}")
    print(f"  ID: {result['id']}")
    print(f"  Name: {result['name']}")
    print()
    print(f"Execute with: aiagent.py task execute {result['id']}")

def task_execute(args):
    """Execute a task."""
    variables = json.loads(args.variables) if args.variables else {}
    data = {"variables": variables}

    result = api_request("POST", f"/api/v1/tasks/{args.task_id}/execute", data=data)

    print(f"{Colors.GREEN}✓ Task execution started!{Colors.NC}")
    print(f"  Execution ID: {result['id']}")
    print(f"  Status: {result['status']}")
    print(f"  Created: {result['created_at']}")
    print()
    print(f"Monitor with: aiagent.py execution monitor {result['id']} --watch")

def task_status(args):
    """Get task details."""
    result = api_request("GET", f"/api/v1/tasks/{args.task_id}")

    print(f"{Colors.BOLD}{Colors.CYAN}Task Details{Colors.NC}")
    print(f"  ID: {result['id']}")
    print(f"  Name: {result['name']}")
    print(f"  Description: {result.get('description', 'N/A')}")
    print(f"  Active: {result['is_active']}")
    print(f"  Scheduled: {result['is_scheduled']}")
    print(f"  Report Generation: {result['generate_report']}")
    print(f"  Tags: {', '.join(result.get('tags', []))}")
    print()

# ============================================================================
# EXECUTION COMMANDS
# ============================================================================

def execution_status(args):
    """Get execution status."""
    result = api_request("GET", f"/api/v1/tasks/executions/{args.execution_id}")

    # Status color
    status_colors = {
        "pending": Colors.CYAN,
        "queued": Colors.BLUE,
        "running": Colors.YELLOW,
        "completed": Colors.GREEN,
        "failed": Colors.RED,
        "cancelled": Colors.MAGENTA
    }
    status_color = status_colors.get(result['status'], Colors.NC)

    print(f"{Colors.BOLD}{Colors.CYAN}Execution Status{Colors.NC}")
    print(f"  Execution ID: {result['id']}")
    print(f"  Task ID: {result['task_id']}")
    print(f"  Status: {status_color}{result['status'].upper()}{Colors.NC}")
    print(f"  Trigger: {result['trigger_type']}")
    print()

    if result.get('session_id'):
        print(f"  Session ID: {result['session_id']}")

    if result.get('celery_task_id'):
        print(f"  Celery Task ID: {result['celery_task_id']}")

    print()
    print(f"  Created: {result.get('created_at', 'N/A')}")
    print(f"  Queued: {result.get('queued_at', 'N/A')}")
    print(f"  Started: {result.get('started_at', 'N/A')}")
    print(f"  Completed: {result.get('completed_at', 'N/A')}")

    if result.get('error_message'):
        print(f"\n  {Colors.RED}Error: {result['error_message']}{Colors.NC}")

    print()

def execution_monitor(args):
    """Monitor execution (with optional watch mode)."""
    if args.watch:
        try:
            while True:
                os.system('clear')
                print(f"{Colors.BOLD}{Colors.MAGENTA}Monitoring Execution (Ctrl+C to exit){Colors.NC}\n")
                execution_status(args)

                # Check if finished
                result = api_request("GET", f"/api/v1/tasks/executions/{args.execution_id}")
                if result['status'] in ['completed', 'failed', 'cancelled']:
                    print(f"{Colors.YELLOW}Execution finished.{Colors.NC}")
                    break

                time.sleep(3)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Monitoring stopped.{Colors.NC}")
    else:
        execution_status(args)

def execution_logs(args):
    """Show execution logs from monitoring directory."""
    log_dir = Path("logs/monitoring")

    if not log_dir.exists():
        print(f"{Colors.YELLOW}No monitoring logs found{Colors.NC}")
        return

    # Find logs for this execution
    log_files = list(log_dir.glob(f"execution_{args.execution_id}_*.log"))

    if not log_files:
        print(f"{Colors.YELLOW}No logs found for execution {args.execution_id}{Colors.NC}")
        return

    # Show most recent log
    latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    print(f"{Colors.BOLD}Log file: {latest_log}{Colors.NC}\n")

    with open(latest_log) as f:
        print(f.read())

# ============================================================================
# SESSION COMMANDS
# ============================================================================

def session_monitor(args):
    """Monitor session details."""
    result = api_request("GET", f"/api/v1/sessions/{args.session_id}")

    print(f"{Colors.BOLD}{Colors.CYAN}Session Details{Colors.NC}")
    print(f"  ID: {result['id']}")
    print(f"  Name: {result['name']}")
    print(f"  Status: {result['status']}")
    print(f"  Mode: {result['mode']}")
    print()
    print(f"  Messages: {result.get('message_count', 0)}")
    print(f"  Tool Calls: {result.get('tool_call_count', 0)}")
    print(f"  Total Tokens: {result.get('total_tokens', 0)}")
    print(f"  Cost: ${result.get('total_cost', 0)}")
    print()
    print(f"  Working Dir: {result.get('working_directory_path', 'N/A')}")
    print()

def session_messages(args):
    """List session messages."""
    result = api_request("GET", f"/api/v1/sessions/{args.session_id}/messages",
                        params={"page": 1, "page_size": 100})

    print(f"{Colors.BOLD}{Colors.CYAN}Messages (Total: {result.get('total', 0)}){Colors.NC}\n")

    for msg in result.get('items', []):
        msg_type = msg['message_type'].upper()
        content = msg.get('content', '')[:200]
        print(f"[{msg['sequence_number']}] {msg_type}")
        print(f"  {content}")
        print(f"  ({msg['created_at']})")
        print()

# ============================================================================
# SYSTEM COMMANDS
# ============================================================================

def health_check(args):
    """Check API health."""
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        result = response.json()

        print(f"{Colors.GREEN}✓ API is healthy{Colors.NC}")
        print(f"  Service: {result['service']}")
        print(f"  Version: {result['version']}")
        print(f"  Environment: {result['environment']}")
    except Exception as e:
        print(f"{Colors.RED}✗ API is not responding: {e}{Colors.NC}")
        sys.exit(1)

# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="AI Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # TASK commands
    task_parser = subparsers.add_parser("task", help="Task operations")
    task_sub = task_parser.add_subparsers(dest="action")

    task_sub.add_parser("list", help="List all tasks")

    create_parser = task_sub.add_parser("create", help="Create a task")
    create_parser.add_argument("prompt", help="Task prompt template")
    create_parser.add_argument("--name", required=True, help="Task name")
    create_parser.add_argument("--description", help="Task description")
    create_parser.add_argument("--tools", help="Comma-separated allowed tools")
    create_parser.add_argument("--tags", help="Comma-separated tags")
    create_parser.add_argument("--report", action="store_true", help="Generate report")
    create_parser.add_argument("--report-format", default="html", help="Report format")

    execute_parser = task_sub.add_parser("execute", help="Execute a task")
    execute_parser.add_argument("task_id", help="Task ID")
    execute_parser.add_argument("--variables", help="JSON variables")

    status_parser = task_sub.add_parser("status", help="Get task status")
    status_parser.add_argument("task_id", help="Task ID")

    # EXECUTION commands
    exec_parser = subparsers.add_parser("execution", help="Execution operations")
    exec_sub = exec_parser.add_subparsers(dest="action")

    exec_status_parser = exec_sub.add_parser("status", help="Get execution status")
    exec_status_parser.add_argument("execution_id", help="Execution ID")

    exec_monitor_parser = exec_sub.add_parser("monitor", help="Monitor execution")
    exec_monitor_parser.add_argument("execution_id", help="Execution ID")
    exec_monitor_parser.add_argument("--watch", action="store_true", help="Watch mode")

    exec_logs_parser = exec_sub.add_parser("logs", help="Show execution logs")
    exec_logs_parser.add_argument("execution_id", help="Execution ID")

    # SESSION commands
    session_parser = subparsers.add_parser("session", help="Session operations")
    session_sub = session_parser.add_subparsers(dest="action")

    session_monitor_parser = session_sub.add_parser("monitor", help="Monitor session")
    session_monitor_parser.add_argument("session_id", help="Session ID")

    session_messages_parser = session_sub.add_parser("messages", help="List messages")
    session_messages_parser.add_argument("session_id", help="Session ID")

    # SYSTEM commands
    subparsers.add_parser("health", help="Check API health")

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command == "task":
        if args.action == "list":
            task_list(args)
        elif args.action == "create":
            task_create(args)
        elif args.action == "execute":
            task_execute(args)
        elif args.action == "status":
            task_status(args)
    elif args.command == "execution":
        if args.action == "status":
            execution_status(args)
        elif args.action == "monitor":
            execution_monitor(args)
        elif args.action == "logs":
            execution_logs(args)
    elif args.command == "session":
        if args.action == "monitor":
            session_monitor(args)
        elif args.action == "messages":
            session_messages(args)
    elif args.command == "health":
        health_check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
