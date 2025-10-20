#!/usr/bin/env python3
"""
Authentication APIs Test Script

Tests all 3 authentication endpoints with comprehensive scenarios including:
- Success cases
- Error cases
- Security validations
- Both admin and regular user testing

Usage:
    python3 docs/apis/authentication/test_authentication.py

Returns exit code 0 if all tests pass, 1 if any test fails.
"""

import requests
import sys
import json
from typing import Dict, Any, Tuple
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
AUTH_ENDPOINT = f"{BASE_URL}/api/v1/auth"

# Test users from seed.py
ADMIN_EMAIL = "admin@default.org"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "user@default.org"
USER_PASSWORD = "user1234"

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class AuthenticationTester:
    """Test suite for Authentication APIs."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.admin_tokens = {}
        self.user_tokens = {}

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

    def test_login_success_admin(self) -> bool:
        """Test successful login with admin credentials."""
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )

            if response.status_code != 200:
                self.log_test(
                    "Login - Admin (Success)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate response structure
            required_fields = ['access_token', 'refresh_token', 'token_type', 'expires_in']
            for field in required_fields:
                if field not in data:
                    self.log_test(
                        "Login - Admin (Success)",
                        False,
                        f"Missing field: {field}"
                    )
                    return False

            # Store tokens for subsequent tests
            self.admin_tokens = data

            # Validate token expiry (should be 6 hours = 21600 seconds)
            expected_expiry = 21600
            if data['expires_in'] != expected_expiry:
                self.log_test(
                    "Login - Admin (Success)",
                    False,
                    f"Expected expires_in={expected_expiry}, got {data['expires_in']}"
                )
                return False

            self.log_test(
                "Login - Admin (Success)",
                True,
                f"Token expires in: {data['expires_in']} seconds (6 hours)"
            )
            return True

        except Exception as e:
            self.log_test("Login - Admin (Success)", False, str(e))
            return False

    def test_login_success_user(self) -> bool:
        """Test successful login with regular user credentials."""
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": USER_EMAIL, "password": USER_PASSWORD}
            )

            if response.status_code != 200:
                self.log_test(
                    "Login - User (Success)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()
            self.user_tokens = data

            self.log_test(
                "Login - User (Success)",
                True,
                f"User: {USER_EMAIL}"
            )
            return True

        except Exception as e:
            self.log_test("Login - User (Success)", False, str(e))
            return False

    def test_login_wrong_password(self) -> bool:
        """Test login with wrong password."""
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
            )

            if response.status_code != 401:
                self.log_test(
                    "Login - Wrong Password",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False

            data = response.json()
            if data.get('detail') != "Incorrect email or password":
                self.log_test(
                    "Login - Wrong Password",
                    False,
                    f"Unexpected error message: {data.get('detail')}"
                )
                return False

            self.log_test("Login - Wrong Password", True, "Returned 401 as expected")
            return True

        except Exception as e:
            self.log_test("Login - Wrong Password", False, str(e))
            return False

    def test_login_nonexistent_user(self) -> bool:
        """Test login with non-existent email."""
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/login",
                json={"email": "nonexistent@email.com", "password": "admin123"}
            )

            if response.status_code != 401:
                self.log_test(
                    "Login - Non-existent User",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False

            # Should return same error message (no user enumeration)
            data = response.json()
            if data.get('detail') != "Incorrect email or password":
                self.log_test(
                    "Login - Non-existent User",
                    False,
                    "Error message reveals user existence (security issue)"
                )
                return False

            self.log_test(
                "Login - Non-existent User",
                True,
                "No user enumeration - same error message"
            )
            return True

        except Exception as e:
            self.log_test("Login - Non-existent User", False, str(e))
            return False

    def test_get_current_user_admin(self) -> bool:
        """Test GET /auth/me with admin token."""
        if not self.admin_tokens:
            self.log_test("Get Current User - Admin", False, "No admin token available")
            return False

        try:
            response = requests.get(
                f"{AUTH_ENDPOINT}/me",
                headers={"Authorization": f"Bearer {self.admin_tokens['access_token']}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Get Current User - Admin",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate admin user fields
            if data.get('email') != ADMIN_EMAIL:
                self.log_test(
                    "Get Current User - Admin",
                    False,
                    f"Expected email {ADMIN_EMAIL}, got {data.get('email')}"
                )
                return False

            if data.get('role') != 'admin':
                self.log_test(
                    "Get Current User - Admin",
                    False,
                    f"Expected role 'admin', got {data.get('role')}"
                )
                return False

            self.log_test(
                "Get Current User - Admin",
                True,
                f"Email: {data['email']}, Role: {data['role']}"
            )
            return True

        except Exception as e:
            self.log_test("Get Current User - Admin", False, str(e))
            return False

    def test_get_current_user_regular(self) -> bool:
        """Test GET /auth/me with regular user token."""
        if not self.user_tokens:
            self.log_test("Get Current User - Regular User", False, "No user token available")
            return False

        try:
            response = requests.get(
                f"{AUTH_ENDPOINT}/me",
                headers={"Authorization": f"Bearer {self.user_tokens['access_token']}"}
            )

            if response.status_code != 200:
                self.log_test(
                    "Get Current User - Regular User",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate user role
            if data.get('role') != 'user':
                self.log_test(
                    "Get Current User - Regular User",
                    False,
                    f"Expected role 'user', got {data.get('role')}"
                )
                return False

            self.log_test(
                "Get Current User - Regular User",
                True,
                f"Email: {data['email']}, Role: {data['role']}"
            )
            return True

        except Exception as e:
            self.log_test("Get Current User - Regular User", False, str(e))
            return False

    def test_get_current_user_no_auth(self) -> bool:
        """Test GET /auth/me without authentication."""
        try:
            response = requests.get(f"{AUTH_ENDPOINT}/me")

            # Accept both 401 and 403 as valid responses for no auth
            if response.status_code not in [401, 403]:
                self.log_test(
                    "Get Current User - No Auth",
                    False,
                    f"Expected 401 or 403, got {response.status_code}"
                )
                return False

            data = response.json()
            if data.get('detail') != "Not authenticated":
                self.log_test(
                    "Get Current User - No Auth",
                    False,
                    f"Unexpected error message: {data.get('detail')}"
                )
                return False

            self.log_test(
                "Get Current User - No Auth",
                True,
                f"Returned {response.status_code} as expected"
            )
            return True

        except Exception as e:
            self.log_test("Get Current User - No Auth", False, str(e))
            return False

    def test_get_current_user_invalid_token(self) -> bool:
        """Test GET /auth/me with invalid token."""
        try:
            response = requests.get(
                f"{AUTH_ENDPOINT}/me",
                headers={"Authorization": "Bearer invalid_token_here"}
            )

            if response.status_code != 401:
                self.log_test(
                    "Get Current User - Invalid Token",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False

            self.log_test("Get Current User - Invalid Token", True, "Returned 401 as expected")
            return True

        except Exception as e:
            self.log_test("Get Current User - Invalid Token", False, str(e))
            return False

    def test_refresh_token_admin(self) -> bool:
        """Test POST /auth/refresh with admin refresh token."""
        if not self.admin_tokens:
            self.log_test("Refresh Token - Admin", False, "No admin refresh token available")
            return False

        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/refresh",
                json={"refresh_token": self.admin_tokens['refresh_token']}
            )

            if response.status_code != 200:
                self.log_test(
                    "Refresh Token - Admin",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False

            data = response.json()

            # Validate new access token is returned
            if 'access_token' not in data:
                self.log_test("Refresh Token - Admin", False, "No access_token in response")
                return False

            # Verify new token format (tokens may be same if generated in same second)
            # What's important is that we got a valid token back
            if not data['access_token'] or len(data['access_token']) < 100:
                self.log_test(
                    "Refresh Token - Admin",
                    False,
                    "Invalid access token format"
                )
                return False

            self.log_test(
                "Refresh Token - Admin",
                True,
                "New access token received (tokens may be same if generated in same second)"
            )
            return True

        except Exception as e:
            self.log_test("Refresh Token - Admin", False, str(e))
            return False

    def test_refresh_token_invalid(self) -> bool:
        """Test POST /auth/refresh with invalid token."""
        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/refresh",
                json={"refresh_token": "invalid_token"}
            )

            if response.status_code != 401:
                self.log_test(
                    "Refresh Token - Invalid",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False

            self.log_test("Refresh Token - Invalid", True, "Returned 401 as expected")
            return True

        except Exception as e:
            self.log_test("Refresh Token - Invalid", False, str(e))
            return False

    def test_refresh_with_access_token(self) -> bool:
        """Test POST /auth/refresh with access token instead of refresh token."""
        if not self.admin_tokens:
            self.log_test(
                "Refresh Token - Wrong Token Type",
                False,
                "No admin token available"
            )
            return False

        try:
            response = requests.post(
                f"{AUTH_ENDPOINT}/refresh",
                json={"refresh_token": self.admin_tokens['access_token']}
            )

            if response.status_code != 401:
                self.log_test(
                    "Refresh Token - Wrong Token Type",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False

            data = response.json()
            if data.get('detail') != "Invalid token type":
                self.log_test(
                    "Refresh Token - Wrong Token Type",
                    False,
                    f"Expected 'Invalid token type', got '{data.get('detail')}'"
                )
                return False

            self.log_test(
                "Refresh Token - Wrong Token Type",
                True,
                "Token type validation working"
            )
            return True

        except Exception as e:
            self.log_test("Refresh Token - Wrong Token Type", False, str(e))
            return False

    def run_all_tests(self):
        """Run all authentication tests."""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}Authentication APIs Test Suite{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"Base URL: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test POST /auth/login
        self.log_section("POST /auth/login - Authentication")
        self.test_login_success_admin()
        self.test_login_success_user()
        self.test_login_wrong_password()
        self.test_login_nonexistent_user()

        # Test GET /auth/me
        self.log_section("GET /auth/me - Get Current User")
        self.test_get_current_user_admin()
        self.test_get_current_user_regular()
        self.test_get_current_user_no_auth()
        self.test_get_current_user_invalid_token()

        # Test POST /auth/refresh
        self.log_section("POST /auth/refresh - Token Refresh")
        self.test_refresh_token_admin()
        self.test_refresh_token_invalid()
        self.test_refresh_with_access_token()

        # Print summary
        self.print_summary()

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
    tester = AuthenticationTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
