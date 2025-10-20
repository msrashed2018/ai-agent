"""Monitoring and health check commands."""

import click
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import format_output


@click.group(name="monitoring")
def monitoring():
    """System monitoring and health checks."""
    pass


@monitoring.command(name="health")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_health(format: str):
    """Get overall system health status."""
    client = get_client()

    try:
        health = client.get_health()
        format_output(health, format, title="System Health")

    except Exception as e:
        raise click.ClickException(f"Failed to get health status: {str(e)}")


@monitoring.command(name="health-db")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_database_health(format: str):
    """Get database health status."""
    client = get_client()

    try:
        health = client.get_database_health()
        format_output(health, format, title="Database Health")

    except Exception as e:
        raise click.ClickException(f"Failed to get database health: {str(e)}")


@monitoring.command(name="health-sdk")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_sdk_health(format: str):
    """Get SDK health status."""
    client = get_client()

    try:
        health = client.get_sdk_health()
        format_output(health, format, title="SDK Health")

    except Exception as e:
        raise click.ClickException(f"Failed to get SDK health: {str(e)}")


@monitoring.command(name="health-storage")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_storage_health(format: str):
    """Get storage health status."""
    client = get_client()

    try:
        health = client.get_storage_health()
        format_output(health, format, title="Storage Health")

    except Exception as e:
        raise click.ClickException(f"Failed to get storage health: {str(e)}")


@monitoring.command(name="costs")
@click.argument("user_id")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_user_costs(user_id: str, start_date: Optional[str], end_date: Optional[str], format: str):
    """Get user cost information."""
    client = get_client()

    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    try:
        costs = client.get_user_costs(user_id, params if params else None)
        format_output(costs, format, title=f"Costs for User {user_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get user costs: {str(e)}")


@monitoring.command(name="budget")
@click.argument("user_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_user_budget(user_id: str, format: str):
    """Get user budget information."""
    client = get_client()

    try:
        budget = client.get_user_budget(user_id)
        format_output(budget, format, title=f"Budget for User {user_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get user budget: {str(e)}")


@monitoring.command(name="session-metrics")
@click.argument("session_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_session_metrics(session_id: str, format: str):
    """Get session-specific metrics."""
    client = get_client()

    try:
        metrics = client.get_session_metrics(session_id)
        format_output(metrics, format, title=f"Metrics for Session {session_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get session metrics: {str(e)}")
