#!/usr/bin/env python3
"""
Authentication Helper Script for AI Agent API

This script handles login and exports access/refresh tokens as environment variables
for easy use in subsequent API calls.

Usage:
    # Login as admin (default)
    source <(python3 scripts/auth_helper.py)

    # Login as regular user
    source <(python3 scripts/auth_helper.py --user user)

    # Login with custom credentials
    source <(python3 scripts/auth_helper.py --email user@example.com --password mypass

    # Export to file (for use in other shells)
    python3 scripts/auth_helper.py --export-file .env.tokens

After running, the following environment variables will be available:
    For admin user:
        - AI_AGENT_ADMIN_ACCESS_TOKEN
        - AI_AGENT_ADMIN_REFRESH_TOKEN
        - AI_AGENT_ADMIN_USER_ID

    For regular user:
        - AI_AGENT_USER_ACCESS_TOKEN
        - AI_AGENT_USER_REFRESH_TOKEN
        - AI_AGENT_USER_USER_ID
"""

import argparse
import json
import sys
import requests
from typing import Optional, Dict, Any


# Default configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_ADMIN_EMAIL = "admin@default.org"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_USER_EMAIL = "user@default.org"
DEFAULT_USER_PASSWORD = "user1234"


class AuthHelper:
    """Helper class for authentication operations."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.auth_endpoint = f"{self.base_url}/api/v1/auth"

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and get tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Dictionary with access_token, refresh_token, and user info

        Raises:
            Exception: If login fails
        """
        try:
            response = requests.post(
                f"{self.auth_endpoint}/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                raise Exception(f"Login failed: {error_detail}")

            token_data = response.json()

            # Get user info
            user_info = self.get_current_user(token_data['access_token'])

            return {
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'token_type': token_data['token_type'],
                'expires_in': token_data['expires_in'],
                'user': user_info
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during login: {e}")

    def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get current user information.

        Args:
            access_token: JWT access token

        Returns:
            Dictionary with user information
        """
        try:
            response = requests.get(
                f"{self.auth_endpoint}/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise Exception("Failed to get user info")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error getting user info: {e}")

    def export_bash_env(self, auth_data: Dict[str, Any]) -> str:
        """
        Generate bash export commands for environment variables.

        Args:
            auth_data: Authentication data from login

        Returns:
            String with bash export commands
        """
        user = auth_data['user']
        role = user['role']

        # Use role-specific variable names
        prefix = "ADMIN" if role == "admin" else "USER"

        exports = [
            f"export AI_AGENT_{prefix}_ACCESS_TOKEN='{auth_data['access_token']}'",
            f"export AI_AGENT_{prefix}_REFRESH_TOKEN='{auth_data['refresh_token']}'",
            f"export AI_AGENT_{prefix}_USER_ID='{user['id']}'",
            "",
            "# Access token exported successfully!",
            f"# User: {user['email']} ({user['role']})",
            f"# Token expires in: {auth_data['expires_in']} seconds ({auth_data['expires_in']//3600} hours)",
            "",
            "# Use in curl commands like:",
            f'# curl -H "Authorization: Bearer $AI_AGENT_{prefix}_ACCESS_TOKEN" http://localhost:8000/api/v1/sessions',
        ]

        return '\n'.join(exports)

    def export_to_file(self, auth_data: Dict[str, Any], filename: str) -> None:
        """
        Export tokens to a file.

        Args:
            auth_data: Authentication data from login
            filename: Output filename
        """
        user = auth_data['user']
        role = user['role']
        prefix = "ADMIN" if role == "admin" else "USER"

        content = [
            "# AI Agent API Tokens",
            f"# Generated for: {user['email']} ({user['role']})",
            f"# Expires in: {auth_data['expires_in']} seconds ({auth_data['expires_in']//3600} hours)",
            "",
            f"AI_AGENT_{prefix}_ACCESS_TOKEN={auth_data['access_token']}",
            f"AI_AGENT_{prefix}_REFRESH_TOKEN={auth_data['refresh_token']}",
            f"AI_AGENT_{prefix}_USER_ID={user['id']}",
        ]

        with open(filename, 'w') as f:
            f.write('\n'.join(content))

        print(f"✅ Tokens exported to {filename}", file=sys.stderr)
        print(f"   User: {user['email']} ({user['role']})", file=sys.stderr)
        print(f"   Load with: source {filename}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='AI Agent API Authentication Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--base-url',
        default=DEFAULT_BASE_URL,
        help=f'API base URL (default: {DEFAULT_BASE_URL})'
    )

    parser.add_argument(
        '--user',
        choices=['admin', 'user'],
        help='Use predefined user credentials (admin or user)'
    )

    parser.add_argument(
        '--email',
        help='User email for login'
    )

    parser.add_argument(
        '--password',
        help='User password for login'
    )

    parser.add_argument(
        '--export-file',
        help='Export tokens to file instead of stdout'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of bash exports'
    )

    args = parser.parse_args()

    # Determine credentials
    if args.email and args.password:
        email = args.email
        password = args.password
    elif args.user == 'user':
        email = DEFAULT_USER_EMAIL
        password = DEFAULT_USER_PASSWORD
    else:  # Default to admin
        email = DEFAULT_ADMIN_EMAIL
        password = DEFAULT_ADMIN_PASSWORD

    # Authenticate
    try:
        auth = AuthHelper(args.base_url)
        auth_data = auth.login(email, password)

        if args.export_file:
            # Export to file
            auth.export_to_file(auth_data, args.export_file)
        elif args.json:
            # Output as JSON
            print(json.dumps(auth_data, indent=2))
        else:
            # Output bash exports
            print(auth.export_bash_env(auth_data))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
