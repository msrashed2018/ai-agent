#!/usr/bin/env python3
"""
Monitoring APIs Test Script

Tests all 7 monitoring endpoints with comprehensive scenarios including:
- Health check endpoints (no auth required)
- Cost tracking with admin and regular users
- Authorization validation (admin vs user access)
- Session metrics with ownership validation

Usage:
    python3 docs/apis/monitoring/test_monitoring.py

Returns exit code 0 if all tests pass, 1 if any test fails.
"""

import requests
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth"
MONITORING_ENDPOINT = f"{BASE_URL}/api/v1/monitoring"

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


class MonitoringTester:
    """Test suite for Monitoring APIs."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.admin_token = None
        self.user_token = None

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

    def test_health_overall(self) -> bool:
        """Test GET /monitoring/health - Overall system health."""
        try:
            response = requests.get(f"{MONITORING_ENDPOINT}/health")

            if response.status_code != 200:
                self.log_test(
                    "Health - Overall",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['status', 'timestamp', 'checks']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Health - Overall",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            # Check components exist in 'checks'
            if 'checks' not in data:
                self.log_test(
                    "Health - Overall",
                    False,
                    "Missing 'checks' field"
                )
                return False

            self.log_test(
                "Health - Overall",
                True,
                f"Status: {data['status']}, Checks: {len(data['checks'])} components"
            )
            return True

        except Exception as e:
            self.log_test("Health - Overall", False, str(e))
            return False

    def test_health_database(self) -> bool:
        """Test GET /monitoring/health/database - Database connectivity."""
        try:
            response = requests.get(f"{MONITORING_ENDPOINT}/health/database")

            if response.status_code != 200:
                self.log_test(
                    "Health - Database",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response
            if 'healthy' not in data:
                self.log_test("Health - Database", False, "Missing 'healthy' field")
                return False

            self.log_test(
                "Health - Database",
                True,
                f"Healthy: {data['healthy']}"
            )
            return True

        except Exception as e:
            self.log_test("Health - Database", False, str(e))
            return False

    def test_health_sdk(self) -> bool:
        """Test GET /monitoring/health/sdk - Claude SDK availability."""
        try:
            response = requests.get(f"{MONITORING_ENDPOINT}/health/sdk")

            if response.status_code != 200:
                self.log_test(
                    "Health - SDK",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if 'available' not in data:
                self.log_test("Health - SDK", False, "Missing 'available' field")
                return False

            self.log_test(
                "Health - SDK",
                True,
                f"Available: {data['available']}"
            )
            return True

        except Exception as e:
            self.log_test("Health - SDK", False, str(e))
            return False

    def test_health_storage(self) -> bool:
        """Test GET /monitoring/health/storage - Storage availability."""
        try:
            response = requests.get(f"{MONITORING_ENDPOINT}/health/storage")

            if response.status_code != 200:
                self.log_test(
                    "Health - Storage",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if 'healthy' not in data:
                self.log_test("Health - Storage", False, "Missing 'healthy' field")
                return False

            self.log_test(
                "Health - Storage",
                True,
                f"Healthy: {data['healthy']}"
            )
            return True

        except Exception as e:
            self.log_test("Health - Storage", False, str(e))
            return False

    def test_costs_user_admin_own(self) -> bool:
        """Test GET /monitoring/costs/user/{user_id} - Admin accessing own costs."""
        if not self.admin_token:
            self.log_test("Costs - Admin Own", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/user/{ADMIN_USER_ID}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Costs - Admin Own",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['user_id', 'total_cost_usd', 'period', 'start_date', 'end_date']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Costs - Admin Own",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            if data['user_id'] != ADMIN_USER_ID:
                self.log_test(
                    "Costs - Admin Own",
                    False,
                    f"Expected user_id {ADMIN_USER_ID}, got {data['user_id']}"
                )
                return False

            self.log_test(
                "Costs - Admin Own",
                True,
                f"Total cost: ${data['total_cost_usd']:.2f}, Sessions: {data.get('total_sessions', 0)}"
            )
            return True

        except Exception as e:
            self.log_test("Costs - Admin Own", False, str(e))
            return False

    def test_costs_user_admin_other(self) -> bool:
        """Test GET /monitoring/costs/user/{user_id} - Admin accessing other user's costs."""
        if not self.admin_token:
            self.log_test("Costs - Admin Other User", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/user/{USER_USER_ID}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Costs - Admin Other User",
                    False,
                    f"Expected 200 (admin can access other users), got {response.status_code}"
                )
                return False

            data = response.json()

            if data['user_id'] != USER_USER_ID:
                self.log_test(
                    "Costs - Admin Other User",
                    False,
                    f"Expected user_id {USER_USER_ID}, got {data['user_id']}"
                )
                return False

            self.log_test(
                "Costs - Admin Other User",
                True,
                "Admin successfully accessed other user's costs"
            )
            return True

        except Exception as e:
            self.log_test("Costs - Admin Other User", False, str(e))
            return False

    def test_costs_user_regular_own(self) -> bool:
        """Test GET /monitoring/costs/user/{user_id} - Regular user accessing own costs."""
        if not self.user_token:
            self.log_test("Costs - User Own", False, "No user token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/user/{USER_USER_ID}",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Costs - User Own",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            if data['user_id'] != USER_USER_ID:
                self.log_test(
                    "Costs - User Own",
                    False,
                    f"Expected user_id {USER_USER_ID}, got {data['user_id']}"
                )
                return False

            self.log_test(
                "Costs - User Own",
                True,
                f"Total cost: ${data['total_cost_usd']:.2f}, Sessions: {data.get('total_sessions', 0)}"
            )
            return True

        except Exception as e:
            self.log_test("Costs - User Own", False, str(e))
            return False

    def test_costs_user_regular_other(self) -> bool:
        """Test GET /monitoring/costs/user/{user_id} - Regular user accessing other user's costs."""
        if not self.user_token:
            self.log_test("Costs - User Other (Forbidden)", False, "No user token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/user/{ADMIN_USER_ID}",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )

            if response.status_code != 403:
                self.log_test(
                    "Costs - User Other (Forbidden)",
                    False,
                    f"Expected 403, got {response.status_code}"
                )
                return False

            self.log_test(
                "Costs - User Other (Forbidden)",
                True,
                "Regular user correctly forbidden from accessing other user's costs"
            )
            return True

        except Exception as e:
            self.log_test("Costs - User Other (Forbidden)", False, str(e))
            return False

    def test_budget_admin_own(self) -> bool:
        """Test GET /monitoring/costs/budget/{user_id} - Admin accessing own budget."""
        if not self.admin_token:
            self.log_test("Budget - Admin Own", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/budget/{ADMIN_USER_ID}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Budget - Admin Own",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['user_id', 'monthly_budget_usd', 'current_month_cost_usd', 'remaining_budget_usd', 'percent_used']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Budget - Admin Own",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            self.log_test(
                "Budget - Admin Own",
                True,
                f"Usage: {data['percent_used']:.1f}%, Remaining: ${data['remaining_budget_usd']:.2f}"
            )
            return True

        except Exception as e:
            self.log_test("Budget - Admin Own", False, str(e))
            return False

    def test_budget_admin_other(self) -> bool:
        """Test GET /monitoring/costs/budget/{user_id} - Admin accessing other user's budget."""
        if not self.admin_token:
            self.log_test("Budget - Admin Other User", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/budget/{USER_USER_ID}",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Budget - Admin Other User",
                    False,
                    f"Expected 200 (admin can access other users), got {response.status_code}"
                )
                return False

            self.log_test(
                "Budget - Admin Other User",
                True,
                "Admin successfully accessed other user's budget"
            )
            return True

        except Exception as e:
            self.log_test("Budget - Admin Other User", False, str(e))
            return False

    def test_budget_regular_own(self) -> bool:
        """Test GET /monitoring/costs/budget/{user_id} - Regular user accessing own budget."""
        if not self.user_token:
            self.log_test("Budget - User Own", False, "No user token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/budget/{USER_USER_ID}",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Budget - User Own",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            self.log_test(
                "Budget - User Own",
                True,
                f"Usage: {data['percent_used']:.1f}%, Remaining: ${data['remaining_budget_usd']:.2f}"
            )
            return True

        except Exception as e:
            self.log_test("Budget - User Own", False, str(e))
            return False

    def test_budget_regular_other(self) -> bool:
        """Test GET /monitoring/costs/budget/{user_id} - Regular user accessing other user's budget."""
        if not self.user_token:
            self.log_test("Budget - User Other (Forbidden)", False, "No user token available")
            return False

        try:
            response = requests.get(
                f"{MONITORING_ENDPOINT}/costs/budget/{ADMIN_USER_ID}",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )

            if response.status_code != 403:
                self.log_test(
                    "Budget - User Other (Forbidden)",
                    False,
                    f"Expected 403, got {response.status_code}"
                )
                return False

            self.log_test(
                "Budget - User Other (Forbidden)",
                True,
                "Regular user correctly forbidden from accessing other user's budget"
            )
            return True

        except Exception as e:
            self.log_test("Budget - User Other (Forbidden)", False, str(e))
            return False

    def test_session_metrics_no_auth(self) -> bool:
        """Test GET /monitoring/metrics/session/{session_id} - Without authentication."""
        try:
            # Use a dummy session ID since we don't have real sessions yet
            response = requests.get(
                f"{MONITORING_ENDPOINT}/metrics/session/00000000-0000-0000-0000-000000000000"
            )

            # Accept both 401 and 403 as valid responses for no auth
            if response.status_code not in [401, 403]:
                self.log_test(
                    "Session Metrics - No Auth",
                    False,
                    f"Expected 401 or 403, got {response.status_code}"
                )
                return False

            self.log_test(
                "Session Metrics - No Auth",
                True,
                f"Returned {response.status_code} as expected"
            )
            return True

        except Exception as e:
            self.log_test("Session Metrics - No Auth", False, str(e))
            return False

    def test_session_metrics_nonexistent(self) -> bool:
        """Test GET /monitoring/metrics/session/{session_id} - Non-existent session."""
        if not self.admin_token:
            self.log_test("Session Metrics - Not Found", False, "No admin token available")
            return False

        try:
            # Use a UUID that doesn't exist
            response = requests.get(
                f"{MONITORING_ENDPOINT}/metrics/session/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )

            if response.status_code != 404:
                self.log_test(
                    "Session Metrics - Not Found",
                    False,
                    f"Expected 404, got {response.status_code}"
                )
                return False

            self.log_test(
                "Session Metrics - Not Found",
                True,
                "Non-existent session correctly returned 404"
            )
            return True

        except Exception as e:
            self.log_test("Session Metrics - Not Found", False, str(e))
            return False

    def run_all_tests(self):
        """Run all monitoring tests."""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}Monitoring APIs Test Suite{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"Base URL: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Setup authentication
        if not self.setup_authentication():
            print(f"\n{RED}Failed to setup authentication. Aborting tests.{RESET}\n")
            return 1

        # Test Health Endpoints (No auth required)
        self.log_section("Health Check Endpoints (No Auth Required)")
        self.test_health_overall()
        self.test_health_database()
        self.test_health_sdk()
        self.test_health_storage()

        # Test Cost Tracking Endpoints
        self.log_section("GET /monitoring/costs/user/{user_id} - Cost Tracking")
        self.test_costs_user_admin_own()
        self.test_costs_user_admin_other()
        self.test_costs_user_regular_own()
        self.test_costs_user_regular_other()

        # Test Budget Endpoints
        self.log_section("GET /monitoring/costs/budget/{user_id} - Budget Status")
        self.test_budget_admin_own()
        self.test_budget_admin_other()
        self.test_budget_regular_own()
        self.test_budget_regular_other()

        # Test Session Metrics Endpoint
        self.log_section("GET /monitoring/metrics/session/{session_id} - Session Metrics")
        self.test_session_metrics_no_auth()
        self.test_session_metrics_nonexistent()

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
    tester = MonitoringTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
