"""MCP server management commands."""

import click
import json
from pathlib import Path
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, print_info, format_output, confirm


@click.group(name="mcp")
def mcp():
    """Manage MCP servers."""
    pass


@mcp.command(name="list")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_servers(format: str):
    """List all MCP servers."""
    client = get_client()

    try:
        result = client.list_mcp_servers()
        format_output(result, format, title="MCP Servers")

    except Exception as e:
        raise click.ClickException(f"Failed to list MCP servers: {str(e)}")


@mcp.command(name="create")
@click.option("--name", required=True, help="Server name")
@click.option("--description", help="Server description")
@click.option("--server-type", required=True, type=click.Choice(["stdio", "sse", "http"]), help="Server type")
@click.option("--config", required=True, help="Server configuration as JSON string")
@click.option("--enabled/--disabled", default=True, help="Enable server immediately")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_server(name: str, description: Optional[str], server_type: str, config: str, enabled: bool, format: str):
    """Create a new MCP server."""
    client = get_client()

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON for config")

    data = {
        "name": name,
        "server_type": server_type,
        "config": config_dict,
        "is_enabled": enabled,
    }
    if description:
        data["description"] = description

    try:
        server = client.create_mcp_server(data)
        print_success(f"MCP server created: {server['id']}")
        format_output(server, format, title="MCP Server Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create MCP server: {str(e)}")


@mcp.command(name="get")
@click.argument("server_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_server(server_id: str, format: str):
    """Get MCP server details by ID."""
    client = get_client()

    try:
        server = client.get_mcp_server(server_id)
        format_output(server, format, title=f"MCP Server {server_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get MCP server: {str(e)}")


@mcp.command(name="update")
@click.argument("server_id")
@click.option("--description", help="Server description")
@click.option("--config", help="Server configuration as JSON string")
@click.option("--enabled", type=bool, help="Enable/disable server")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_server(server_id: str, description: Optional[str], config: Optional[str], enabled: Optional[bool], format: str):
    """Update MCP server configuration."""
    client = get_client()

    data = {}
    if description is not None:
        data["description"] = description
    if config is not None:
        try:
            data["config"] = json.loads(config)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for config")
    if enabled is not None:
        data["is_enabled"] = enabled

    if not data:
        raise click.ClickException("No update fields provided")

    try:
        server = client.update_mcp_server(server_id, data)
        print_success(f"MCP server {server_id} updated")
        format_output(server, format, title="Updated MCP Server")

    except Exception as e:
        raise click.ClickException(f"Failed to update MCP server: {str(e)}")


@mcp.command(name="delete")
@click.argument("server_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_server(server_id: str, yes: bool):
    """Delete an MCP server."""
    if not yes and not confirm(f"Are you sure you want to delete MCP server {server_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.delete_mcp_server(server_id)
        print_success(f"MCP server {server_id} deleted")

    except Exception as e:
        raise click.ClickException(f"Failed to delete MCP server: {str(e)}")


@mcp.command(name="health-check")
@click.argument("server_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def health_check(server_id: str, format: str):
    """Perform health check on MCP server."""
    client = get_client()

    try:
        server = client.health_check_mcp_server(server_id)
        print_success(f"Health check completed for server {server_id}")
        format_output(server, format, title="Health Check Result")

    except Exception as e:
        raise click.ClickException(f"Health check failed: {str(e)}")


@mcp.command(name="import")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--override/--no-override", default=False, help="Override existing servers")
def import_config(config_file: str, override: bool):
    """Import MCP servers from Claude Desktop config file."""
    client = get_client()
    config_path = Path(config_file)

    try:
        result = client.import_claude_desktop_config(config_path, override)
        print_success(f"Imported {result.get('imported', 0)} servers")
        if result.get('skipped', 0) > 0:
            print_info(f"Skipped {result['skipped']} existing servers")
        if result.get('errors', 0) > 0:
            print_info(f"Failed to import {result['errors']} servers")

    except Exception as e:
        raise click.ClickException(f"Failed to import config: {str(e)}")


@mcp.command(name="export")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--include-global/--no-global", default=True, help="Include global servers")
def export_config(output: str, include_global: bool):
    """Export MCP servers to Claude Desktop config format."""
    client = get_client()
    output_path = Path(output)

    try:
        config = client.export_claude_desktop_config(include_global)

        with open(output_path, "w") as f:
            json.dump(config, f, indent=2)

        print_success(f"Configuration exported to {output_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to export config: {str(e)}")


@mcp.command(name="templates")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def list_templates(format: str):
    """List available MCP server templates."""
    client = get_client()

    try:
        result = client.get_mcp_templates()
        format_output(result, format, title="MCP Server Templates")

    except Exception as e:
        raise click.ClickException(f"Failed to get templates: {str(e)}")
