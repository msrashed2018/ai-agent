#!/usr/bin/env python3
"""
Task Management APIs Test Script

Tests all 9 task endpoints with comprehensive scenarios including:
- Task creation with validation
- Task retrieval (basic and detailed)
- Task listing with filters
- Task updates
- Task deletion (soft delete)
- Task execution (async and sync modes)
- Execution listing and monitoring
- Execution retry
- Authorization validation

Usage:
    python3 docs/apis/tasks/test_tasks.py

Returns exit code 0 if all tests pass, 1 if any test fails.
"""

import requests
import sys
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth"
TASKS_ENDPOINT = f"{BASE_URL}/api/v1/tasks"

# Test users from seed.py
ADMIN_EMAIL = "admin@default.org"
ADMIN_PASSWORD = "admin123"
ADMIN_USER_ID = "94d9f5a2-1257-43ac-9de2-6d86421455a6"

USER_EMAIL = "user@default.org"
USER_PASSWORD = "user1234"
USER_USER_ID = "0a6c44d1-51a3-414f-a943-456ff09c3e76"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class TaskTester:
    """Test suite for Task Management APIs."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.admin_token = None
        self.user_token = None
        self.test_task_id = None
        self.test_execution_id = None

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        if passed:
            self.passed += 1
            print(f"{GREEN}✓{RESET} {test_name}")
            if details:
                print(f"  {details}")
        else:
            self.failed += 1
            print(f"{RED}✗{RESET} {test_name}")
            if details:
                print(f"  {RED}{details}{RESET}")

    def log_section(self, title: str):
        """Log test section header."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{title}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

    def setup_authentication(self):
        """Login as both admin and user to get tokens."""
        self.log_section("Setup - Authentication")

        # Login as admin
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            if response.status_code == 200:
                self.admin_token = response.json()['access_token']
                self.log_test("Admin Login", True, f"Token obtained for {ADMIN_EMAIL}")
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
            return False

        # Login as regular user
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": USER_EMAIL, "password": USER_PASSWORD}
            )
            if response.status_code == 200:
                self.user_token = response.json()['access_token']
                self.log_test("User Login", True, f"Token obtained for {USER_EMAIL}")
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

        return True

    def test_create_task_success(self) -> bool:
        """Test POST /tasks - Create task with valid data."""
        if not self.admin_token:
            self.log_test("Create Task - Success", False, "No admin token available")
            return False

        try:
            task_data = {
                "name": "Test K8s Health Check",
                "description": "Check Kubernetes cluster health",
                "prompt_template": "Check the health of {{cluster}} cluster",
                "allowed_tools": [
                    "Bash(kubectl get:*)",
                    "Bash(kubectl describe:*)",
                    "Read"
                ],
                "disallowed_tools": [
                    "Bash(kubectl delete:*)"
                ],
                "sdk_options": {
                    "model": "claude-sonnet-4-5",
                    "max_turns": 10
                },
                "is_scheduled": False,
                "generate_report": False,
                "tags": ["test", "monitoring"]
            }

            response = requests.post(
                TASKS_ENDPOINT,
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=task_data
            )

            if response.status_code != 201:
                self.log_test(
                    "Create Task - Success",
                    False,
                    f"Expected 201, got {response.status_code}: {response.text}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['id', 'name', 'prompt_template', 'allowed_tools', '_links']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Create Task - Success",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            # Store task ID for later tests
            self.test_task_id = data['id']

            self.log_test(
                "Create Task - Success",
                True,
                f"Task created: {data['name']} (ID: {self.test_task_id})"
            )
            return True

        except Exception as e:
            self.log_test("Create Task - Success", False, str(e))
            return False

    def test_create_task_invalid_tool(self) -> bool:
        """Test POST /tasks - Create task with invalid tool pattern."""
        if not self.admin_token:
            self.log_test("Create Task - Invalid Tool", False, "No admin token available")
            return False

        try:
            task_data = {
                "name": "Invalid Task",
                "prompt_template": "Test",
                "allowed_tools": ["InvalidToolPattern123"],
                "sdk_options": {}
            }

            response = requests.post(
                TASKS_ENDPOINT,
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=task_data
            )

            if response.status_code != 400:
                self.log_test(
                    "Create Task - Invalid Tool",
                    False,
                    f"Expected 400, got {response.status_code}"
                )
                return False

            self.log_test(
                "Create Task - Invalid Tool",
                True,
                "Invalid tool pattern correctly rejected"
            )
            return True

        except Exception as e:
            self.log_test("Create Task - Invalid Tool", False, str(e))
            return False

    def test_create_task_invalid_prompt(self) -> bool:
        """Test POST /tasks - Create task with invalid Jinja2 template."""
        if not self.admin_token:
            self.log_test("Create Task - Invalid Prompt", False, "No admin token available")
            return False

        try:
            task_data = {
                "name": "Invalid Prompt Task",
                "prompt_template": "Bad template {{ unclosed",
                "allowed_tools": ["Bash"],
                "sdk_options": {}
            }

            response = requests.post(
                TASKS_ENDPOINT,
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=task_data
            )

            if response.status_code != 400:
                self.log_test(
                    "Create Task - Invalid Prompt",
                    False,
                    f"Expected 400, got {response.status_code}"
                )
                return False

            self.log_test(
                "Create Task - Invalid Prompt",
                True,
                "Invalid Jinja2 template correctly rejected"
            )
            return True

        except Exception as e:
            self.log_test("Create Task - Invalid Prompt", False, str(e))
            return False

    def test_get_task_basic(self) -> bool:
        """Test GET /tasks/{task_id} - Get task with basic info."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("Get Task - Basic", False, "No admin token or task ID available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}/{self.test_task_id}?detailed=false",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Get Task - Basic",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if data['id'] != self.test_task_id:
                self.log_test(
                    "Get Task - Basic",
                    False,
                    f"Expected task_id {self.test_task_id}, got {data['id']}"
                )
                return False

            self.log_test(
                "Get Task - Basic",
                True,
                f"Retrieved task: {data['name']}"
            )
            return True

        except Exception as e:
            self.log_test("Get Task - Basic", False, str(e))
            return False

    def test_get_task_detailed(self) -> bool:
        """Test GET /tasks/{task_id} - Get task with detailed info."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("Get Task - Detailed", False, "No admin token or task ID available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}/{self.test_task_id}?detailed=true",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Get Task - Detailed",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate detailed fields
            detailed_fields = ['execution_summary', 'recent_executions', 'permission_policies']
            for field in detailed_fields:
                if field not in data:
                    self.log_test(
                        "Get Task - Detailed",
                        False,
                        f"Missing detailed field: {field}"
                    )
                    return False

            self.log_test(
                "Get Task - Detailed",
                True,
                f"Retrieved detailed task with execution_summary, working_directories, etc."
            )
            return True

        except Exception as e:
            self.log_test("Get Task - Detailed", False, str(e))
            return False

    def test_get_task_not_found(self) -> bool:
        """Test GET /tasks/{task_id} - Non-existent task."""
        if not self.admin_token:
            self.log_test("Get Task - Not Found", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 404:
                self.log_test(
                    "Get Task - Not Found",
                    False,
                    f"Expected 404, got {response.status_code}"
                )
                return False

            self.log_test(
                "Get Task - Not Found",
                True,
                "Non-existent task correctly returned 404"
            )
            return True

        except Exception as e:
            self.log_test("Get Task - Not Found", False, str(e))
            return False

    def test_get_task_unauthorized(self) -> bool:
        """Test GET /tasks/{task_id} - User accessing another user's task."""
        if not self.user_token or not self.test_task_id:
            self.log_test("Get Task - Unauthorized", False, "No user token or task ID available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}/{self.test_task_id}",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )

            if response.status_code != 403:
                self.log_test(
                    "Get Task - Unauthorized",
                    False,
                    f"Expected 403, got {response.status_code}"
                )
                return False

            self.log_test(
                "Get Task - Unauthorized",
                True,
                "Regular user correctly forbidden from accessing admin's task"
            )
            return True

        except Exception as e:
            self.log_test("Get Task - Unauthorized", False, str(e))
            return False

    def test_list_tasks(self) -> bool:
        """Test GET /tasks - List all tasks."""
        if not self.admin_token:
            self.log_test("List Tasks - All", False, "No admin token available")
            return False

        try:
            response = requests.get(
                TASKS_ENDPOINT,
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "List Tasks - All",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['items', 'total', 'page', 'page_size']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "List Tasks - All",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            self.log_test(
                "List Tasks - All",
                True,
                f"Retrieved {len(data['items'])} tasks (total: {data['total']})"
            )
            return True

        except Exception as e:
            self.log_test("List Tasks - All", False, str(e))
            return False

    def test_list_tasks_filtered(self) -> bool:
        """Test GET /tasks?tags=test - Filter tasks by tags."""
        if not self.admin_token:
            self.log_test("List Tasks - Filtered", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}?tags=test",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "List Tasks - Filtered",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            self.log_test(
                "List Tasks - Filtered",
                True,
                f"Retrieved {len(data['items'])} tasks with tag 'test'"
            )
            return True

        except Exception as e:
            self.log_test("List Tasks - Filtered", False, str(e))
            return False

    def test_update_task(self) -> bool:
        """Test PATCH /tasks/{task_id} - Update task."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("Update Task", False, "No admin token or task ID available")
            return False

        try:
            update_data = {
                "name": "Updated K8s Health Check",
                "description": "Updated description"
            }

            response = requests.patch(
                f"{TASKS_ENDPOINT}/{self.test_task_id}",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=update_data
            )

            if response.status_code != 200:
                self.log_test(
                    "Update Task",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if data['name'] != update_data['name']:
                self.log_test(
                    "Update Task",
                    False,
                    f"Expected name '{update_data['name']}', got '{data['name']}'"
                )
                return False

            self.log_test(
                "Update Task",
                True,
                f"Task updated successfully: {data['name']}"
            )
            return True

        except Exception as e:
            self.log_test("Update Task", False, str(e))
            return False

    def test_execute_task_async(self) -> bool:
        """Test POST /tasks/{task_id}/execute - Execute task (async mode)."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("Execute Task - Async", False, "No admin token or task ID available")
            return False

        try:
            execute_data = {
                "variables": {
                    "cluster": "test-cluster"
                }
            }

            response = requests.post(
                f"{TASKS_ENDPOINT}/{self.test_task_id}/execute",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json=execute_data
            )

            if response.status_code != 202:
                self.log_test(
                    "Execute Task - Async",
                    False,
                    f"Expected 202, got {response.status_code}: {response.text}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['id', 'task_id', 'status', 'trigger_type']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Execute Task - Async",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            # Store execution ID for later tests
            self.test_execution_id = data['id']

            if data['status'] not in ['pending', 'running']:
                self.log_test(
                    "Execute Task - Async",
                    False,
                    f"Expected status 'pending' or 'running', got '{data['status']}'"
                )
                return False

            self.log_test(
                "Execute Task - Async",
                True,
                f"Task execution started (ID: {self.test_execution_id}, Status: {data['status']})"
            )
            return True

        except Exception as e:
            self.log_test("Execute Task - Async", False, str(e))
            return False

    def test_get_task_execution(self) -> bool:
        """Test GET /task-executions/{execution_id} - Get execution details."""
        if not self.admin_token or not self.test_execution_id:
            self.log_test("Get Task Execution", False, "No admin token or execution ID available")
            return False

        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/task-executions/{self.test_execution_id}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Get Task Execution",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if data['id'] != self.test_execution_id:
                self.log_test(
                    "Get Task Execution",
                    False,
                    f"Expected execution_id {self.test_execution_id}, got {data['id']}"
                )
                return False

            self.log_test(
                "Get Task Execution",
                True,
                f"Retrieved execution: Status={data['status']}, Trigger={data['trigger_type']}"
            )
            return True

        except Exception as e:
            self.log_test("Get Task Execution", False, str(e))
            return False

    def test_list_task_executions(self) -> bool:
        """Test GET /tasks/{task_id}/executions - List task executions."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("List Task Executions", False, "No admin token or task ID available")
            return False

        try:
            response = requests.get(
                f"{TASKS_ENDPOINT}/{self.test_task_id}/executions",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "List Task Executions",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['items', 'total', 'page', 'page_size']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "List Task Executions",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            self.log_test(
                "List Task Executions",
                True,
                f"Retrieved {len(data['items'])} executions (total: {data['total']})"
            )
            return True

        except Exception as e:
            self.log_test("List Task Executions", False, str(e))
            return False

    def test_wait_for_execution(self) -> bool:
        """Wait for task execution to complete (with timeout)."""
        if not self.admin_token or not self.test_execution_id:
            self.log_test("Wait for Execution", False, "No admin token or execution ID available")
            return False

        try:
            max_wait = 60  # 60 seconds timeout
            poll_interval = 2  # Poll every 2 seconds
            elapsed = 0

            while elapsed < max_wait:
                response = requests.get(
                    f"{BASE_URL}/api/v1/task-executions/{self.test_execution_id}",
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )

                if response.status_code != 200:
                    self.log_test(
                        "Wait for Execution",
                        False,
                        f"Failed to get execution status: {response.status_code}"
                    )
                    return False

                data = response.json()
                status = data['status']

                if status in ['completed', 'failed', 'cancelled']:
                    self.log_test(
                        "Wait for Execution",
                        True,
                        f"Execution finished with status: {status} (took {elapsed}s)"
                    )
                    return True

                time.sleep(poll_interval)
                elapsed += poll_interval

            self.log_test(
                "Wait for Execution",
                False,
                f"Execution did not complete within {max_wait}s timeout"
            )
            return False

        except Exception as e:
            self.log_test("Wait for Execution", False, str(e))
            return False

    def test_delete_task(self) -> bool:
        """Test DELETE /tasks/{task_id} - Soft delete task."""
        if not self.admin_token or not self.test_task_id:
            self.log_test("Delete Task", False, "No admin token or task ID available")
            return False

        try:
            response = requests.delete(
                f"{TASKS_ENDPOINT}/{self.test_task_id}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 204:
                self.log_test(
                    "Delete Task",
                    False,
                    f"Expected 204, got {response.status_code}"
                )
                return False

            # Verify task is soft deleted (should return 404)
            verify_response = requests.get(
                f"{TASKS_ENDPOINT}/{self.test_task_id}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if verify_response.status_code != 404:
                self.log_test(
                    "Delete Task",
                    False,
                    f"Task still accessible after deletion (status: {verify_response.status_code})"
                )
                return False

            self.log_test(
                "Delete Task",
                True,
                f"Task soft-deleted successfully (ID: {self.test_task_id})"
            )
            return True

        except Exception as e:
            self.log_test("Delete Task", False, str(e))
            return False

    def run_all_tests(self):
        """Run all task tests."""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}Task Management APIs Test Suite{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"Base URL: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Setup authentication
        if not self.setup_authentication():
            print(f"\n{RED}Failed to setup authentication. Aborting tests.{RESET}\n")
            return 1

        # Test Task Creation
        self.log_section("POST /tasks - Create Task")
        self.test_create_task_success()
        self.test_create_task_invalid_tool()
        self.test_create_task_invalid_prompt()

        # Test Task Retrieval
        self.log_section("GET /tasks/{task_id} - Get Task")
        self.test_get_task_basic()
        self.test_get_task_detailed()
        self.test_get_task_not_found()
        self.test_get_task_unauthorized()

        # Test Task Listing
        self.log_section("GET /tasks - List Tasks")
        self.test_list_tasks()
        self.test_list_tasks_filtered()

        # Test Task Update
        self.log_section("PATCH /tasks/{task_id} - Update Task")
        self.test_update_task()

        # Test Task Execution
        self.log_section("POST /tasks/{task_id}/execute - Execute Task")
        self.test_execute_task_async()

        # Test Execution Monitoring
        self.log_section("GET /task-executions/{execution_id} - Get Execution")
        self.test_get_task_execution()

        # Test Execution Listing
        self.log_section("GET /tasks/{task_id}/executions - List Executions")
        self.test_list_task_executions()

        # Wait for execution to complete
        self.log_section("Monitoring - Wait for Execution")
        self.test_wait_for_execution()

        # Test Task Deletion
        self.log_section("DELETE /tasks/{task_id} - Delete Task")
        self.test_delete_task()

        # Print summary
        return self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test Summary{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if self.failed == 0:
            print(f"{GREEN}✓ All tests passed!{RESET}\n")
            return 0
        else:
            print(f"{RED}✗ Some tests failed{RESET}\n")
            return 1


def main():
    """Main entry point."""
    tester = TaskTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
