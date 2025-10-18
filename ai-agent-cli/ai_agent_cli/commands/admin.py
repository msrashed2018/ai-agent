"""Admin commands."""

import click
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import format_output


@click.group(name="admin")
def admin():
    """Administrative commands (admin users only)."""
    pass


@admin.command(name="stats")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_stats(format: str):
    """Get system-wide statistics."""
    client = get_client()

    try:
        stats = client.get_system_stats()
        format_output(stats, format, title="System Statistics")

    except Exception as e:
        raise click.ClickException(f"Failed to get system stats: {str(e)}")


@admin.command(name="sessions")
@click.option("--user-id", help="Filter by user ID")
@click.option("--status", type=click.Choice(["active", "paused", "completed", "failed"]), help="Filter by status")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_all_sessions(user_id: Optional[str], status: Optional[str], page: int, page_size: int, format: str):
    """List all sessions across all users."""
    client = get_client()

    params = {"page": page, "page_size": page_size}
    if user_id:
        params["user_id"] = user_id
    if status:
        params["status"] = status

    try:
        result = client.list_all_sessions(params)
        format_output(result, format, title="All Sessions (Admin View)")

    except Exception as e:
        raise click.ClickException(f"Failed to list sessions: {str(e)}")


@admin.command(name="users")
@click.option("--include-deleted", is_flag=True, help="Include deleted users")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_all_users(include_deleted: bool, page: int, page_size: int, format: str):
    """List all users."""
    client = get_client()

    params = {"page": page, "page_size": page_size, "include_deleted": include_deleted}

    try:
        result = client.list_all_users(params)
        format_output(result, format, title="All Users (Admin View)")

    except Exception as e:
        raise click.ClickException(f"Failed to list users: {str(e)}")
