"""Tool group management commands."""

import click
import json
from typing import Optional, List
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, print_info, format_output, confirm


@click.group(name="tool-groups")
def tool_groups():
    """Manage tool groups."""
    pass


@tool_groups.command(name="list")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_tool_groups(format: str):
    """List all tool groups."""
    client = get_client()

    try:
        result = client.list_tool_groups()
        format_output(result, format, title="Tool Groups")

    except Exception as e:
        raise click.ClickException(f"Failed to list tool groups: {str(e)}")


@tool_groups.command(name="create")
@click.option("--name", required=True, help="Tool group name")
@click.option("--description", help="Tool group description")
@click.option("--allowed-tools", multiple=True, help="Allowed tool pattern (can be used multiple times)")
@click.option("--disallowed-tools", multiple=True, help="Disallowed tool pattern (can be used multiple times)")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_tool_group(
    name: str,
    description: Optional[str],
    allowed_tools: tuple,
    disallowed_tools: tuple,
    format: str,
):
    """Create a new tool group."""
    client = get_client()

    data = {
        "name": name,
        "allowed_tools": list(allowed_tools) if allowed_tools else None,
        "disallowed_tools": list(disallowed_tools) if disallowed_tools else None,
    }
    if description:
        data["description"] = description

    try:
        tool_group = client.create_tool_group(data)
        print_success(f"Tool group created: {tool_group['id']}")
        format_output(tool_group, format, title="Tool Group Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create tool group: {str(e)}")


@tool_groups.command(name="get")
@click.argument("tool_group_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_tool_group(tool_group_id: str, format: str):
    """Get tool group details by ID."""
    client = get_client()

    try:
        tool_group = client.get_tool_group(tool_group_id)
        format_output(tool_group, format, title=f"Tool Group {tool_group_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get tool group: {str(e)}")


@tool_groups.command(name="update")
@click.argument("tool_group_id")
@click.option("--name", help="Tool group name")
@click.option("--description", help="Tool group description")
@click.option("--allowed-tools", multiple=True, help="Replace allowed tools (can be used multiple times)")
@click.option("--disallowed-tools", multiple=True, help="Replace disallowed tools (can be used multiple times)")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_tool_group(
    tool_group_id: str,
    name: Optional[str],
    description: Optional[str],
    allowed_tools: tuple,
    disallowed_tools: tuple,
    format: str,
):
    """Update a tool group."""
    client = get_client()

    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if disallowed_tools:
        data["disallowed_tools"] = list(disallowed_tools)

    if not data:
        raise click.ClickException("No update fields provided")

    try:
        tool_group = client.update_tool_group(tool_group_id, data)
        print_success(f"Tool group {tool_group_id} updated")
        format_output(tool_group, format, title="Updated Tool Group")

    except Exception as e:
        raise click.ClickException(f"Failed to update tool group: {str(e)}")


@tool_groups.command(name="delete")
@click.argument("tool_group_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_tool_group(tool_group_id: str, yes: bool):
    """Delete a tool group."""
    if not yes and not confirm(f"Are you sure you want to delete tool group {tool_group_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.delete_tool_group(tool_group_id)
        print_success(f"Tool group {tool_group_id} deleted")

    except Exception as e:
        raise click.ClickException(f"Failed to delete tool group: {str(e)}")


@tool_groups.command(name="add-allowed")
@click.argument("tool_group_id")
@click.argument("tool")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def add_allowed_tool(tool_group_id: str, tool: str, format: str):
    """Add a tool to the allowed list."""
    client = get_client()

    try:
        tool_group = client.add_allowed_tool(tool_group_id, tool)
        print_success(f"Tool '{tool}' added to allowed list")
        format_output(tool_group, format, title="Updated Tool Group")

    except Exception as e:
        raise click.ClickException(f"Failed to add allowed tool: {str(e)}")


@tool_groups.command(name="remove-allowed")
@click.argument("tool_group_id")
@click.argument("tool")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def remove_allowed_tool(tool_group_id: str, tool: str, format: str):
    """Remove a tool from the allowed list."""
    client = get_client()

    try:
        tool_group = client.remove_allowed_tool(tool_group_id, tool)
        print_success(f"Tool '{tool}' removed from allowed list")
        format_output(tool_group, format, title="Updated Tool Group")

    except Exception as e:
        raise click.ClickException(f"Failed to remove allowed tool: {str(e)}")


@tool_groups.command(name="add-disallowed")
@click.argument("tool_group_id")
@click.argument("tool")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def add_disallowed_tool(tool_group_id: str, tool: str, format: str):
    """Add a tool to the disallowed list."""
    client = get_client()

    try:
        tool_group = client.add_disallowed_tool(tool_group_id, tool)
        print_success(f"Tool '{tool}' added to disallowed list")
        format_output(tool_group, format, title="Updated Tool Group")

    except Exception as e:
        raise click.ClickException(f"Failed to add disallowed tool: {str(e)}")


@tool_groups.command(name="remove-disallowed")
@click.argument("tool_group_id")
@click.argument("tool")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def remove_disallowed_tool(tool_group_id: str, tool: str, format: str):
    """Remove a tool from the disallowed list."""
    client = get_client()

    try:
        tool_group = client.remove_disallowed_tool(tool_group_id, tool)
        print_success(f"Tool '{tool}' removed from disallowed list")
        format_output(tool_group, format, title="Updated Tool Group")

    except Exception as e:
        raise click.ClickException(f"Failed to remove disallowed tool: {str(e)}")
