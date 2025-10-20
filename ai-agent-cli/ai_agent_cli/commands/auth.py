"""Authentication commands."""

import click
from ai_agent_cli.core.client import get_client
from ai_agent_cli.core.config import config_manager
from ai_agent_cli.utils.output import print_success, print_info, print_key_value, format_output


@click.group(name="auth")
def auth():
    """Authentication and user management commands."""
    pass


@auth.command(name="login")
@click.option("--email", prompt=True, help="User email address")
@click.option("--password", prompt=True, hide_input=True, help="User password")
def login(email: str, password: str):
    """Login to AI Agent API and store credentials."""
    client = get_client()

    try:
        response = client.login(email, password)

        # Store tokens
        config_manager.set_tokens(
            access_token=response["access_token"],
            refresh_token=response.get("refresh_token"),
        )

        print_success(f"Successfully logged in as {email}")
        print_info(f"Access token expires in {response['expires_in']} seconds")

    except Exception as e:
        raise click.ClickException(f"Login failed: {str(e)}")


@auth.command(name="refresh")
def refresh():
    """Refresh access token using refresh token."""
    refresh_token = config_manager.get_refresh_token()

    if not refresh_token:
        raise click.ClickException("No refresh token found. Please login again.")

    client = get_client()

    try:
        response = client.refresh_access_token(refresh_token)

        # Update access token
        config_manager.set_tokens(access_token=response["access_token"])

        print_success("Access token refreshed successfully")
        print_info(f"New token expires in {response['expires_in']} seconds")

    except Exception as e:
        raise click.ClickException(f"Token refresh failed: {str(e)}")


@auth.command(name="logout")
@click.option("--all", "logout_all", is_flag=True, help="Logout from all devices")
def logout(logout_all: bool):
    """Logout and clear stored credentials."""
    if config_manager.is_authenticated():
        client = get_client()
        try:
            if logout_all:
                client.logout_all()
                print_success("Successfully logged out from all devices")
            else:
                client.logout()
                print_success("Successfully logged out")
        except Exception as e:
            print_info(f"Warning: API logout failed: {str(e)}")
            print_info("Clearing local credentials anyway...")

    config_manager.clear_tokens()
    print_success("Local credentials cleared")


@auth.command(name="whoami")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def whoami(format: str):
    """Show current user information."""
    if not config_manager.is_authenticated():
        raise click.ClickException("Not authenticated. Please login first.")

    client = get_client()

    try:
        user_info = client.get_current_user()
        format_output(user_info, format, title="Current User")

    except Exception as e:
        raise click.ClickException(f"Failed to get user info: {str(e)}")


@auth.command(name="status")
def status():
    """Show authentication status."""
    if config_manager.is_authenticated():
        print_success("Authenticated")
        print_info(f"API URL: {config_manager.get_api_url()}")

        try:
            client = get_client()
            user_info = client.get_current_user()
            print_info(f"Logged in as: {user_info['email']} ({user_info['role']})")
        except Exception:
            print_info("Token may be expired. Try refreshing or logging in again.")
    else:
        print_info("Not authenticated")
        print_info("Run 'ai-agent auth login' to authenticate")
