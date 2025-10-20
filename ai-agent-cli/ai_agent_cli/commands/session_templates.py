"""Session template management commands."""

import click
import json
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, print_info, format_output, confirm


@click.group(name="templates")
def session_templates():
    """Manage session templates."""
    pass


@session_templates.command(name="list")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_templates(page: int, page_size: int, format: str):
    """List all session templates."""
    client = get_client()

    params = {"page": page, "page_size": page_size}

    try:
        result = client.list_session_templates(params)
        format_output(result, format, title="Session Templates")

    except Exception as e:
        raise click.ClickException(f"Failed to list templates: {str(e)}")


@session_templates.command(name="create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
@click.option("--config", required=True, help="Template configuration as JSON string")
@click.option("--tags", multiple=True, help="Template tags")
@click.option("--is-public", is_flag=True, help="Make template public")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_template(
    name: str,
    description: Optional[str],
    config: str,
    tags: tuple,
    is_public: bool,
    format: str,
):
    """Create a new session template."""
    client = get_client()

    try:
        config_dict = json.loads(config)
    except json.JSONDecodeError:
        raise click.ClickException("Invalid JSON for config")

    data = {
        "name": name,
        "template_config": config_dict,
        "is_public": is_public,
    }
    if description:
        data["description"] = description
    if tags:
        data["tags"] = list(tags)

    try:
        template = client.create_session_template(data)
        print_success(f"Template created: {template['id']}")
        format_output(template, format, title="Template Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create template: {str(e)}")


@session_templates.command(name="get")
@click.argument("template_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def get_template(template_id: str, format: str):
    """Get template details by ID."""
    client = get_client()

    try:
        template = client.get_session_template(template_id)
        format_output(template, format, title=f"Template {template_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get template: {str(e)}")


@session_templates.command(name="update")
@click.argument("template_id")
@click.option("--name", help="Template name")
@click.option("--description", help="Template description")
@click.option("--config", help="Template configuration as JSON string")
@click.option("--tags", multiple=True, help="Template tags")
@click.option("--is-public", type=bool, help="Make template public/private")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_template(
    template_id: str,
    name: Optional[str],
    description: Optional[str],
    config: Optional[str],
    tags: tuple,
    is_public: Optional[bool],
    format: str,
):
    """Update a session template."""
    client = get_client()

    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if config is not None:
        try:
            data["template_config"] = json.loads(config)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for config")
    if tags:
        data["tags"] = list(tags)
    if is_public is not None:
        data["is_public"] = is_public

    if not data:
        raise click.ClickException("No update fields provided")

    try:
        template = client.update_session_template(template_id, data)
        print_success(f"Template {template_id} updated")
        format_output(template, format, title="Updated Template")

    except Exception as e:
        raise click.ClickException(f"Failed to update template: {str(e)}")


@session_templates.command(name="delete")
@click.argument("template_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_template(template_id: str, yes: bool):
    """Delete a session template."""
    if not yes and not confirm(f"Are you sure you want to delete template {template_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.delete_session_template(template_id)
        print_success(f"Template {template_id} deleted")

    except Exception as e:
        raise click.ClickException(f"Failed to delete template: {str(e)}")


@session_templates.command(name="search")
@click.option("--query", help="Search query string")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def search_templates(query: Optional[str], tags: tuple, format: str):
    """Search session templates."""
    client = get_client()

    if not query and not tags:
        raise click.ClickException("Please provide either --query or --tags")

    try:
        result = client.search_session_templates(
            query=query,
            tags=list(tags) if tags else None
        )
        format_output(result, format, title="Search Results")

    except Exception as e:
        raise click.ClickException(f"Failed to search templates: {str(e)}")


@session_templates.command(name="popular")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_popular(format: str):
    """Get popular session templates."""
    client = get_client()

    try:
        result = client.get_popular_templates()
        format_output(result, format, title="Popular Templates")

    except Exception as e:
        raise click.ClickException(f"Failed to get popular templates: {str(e)}")


@session_templates.command(name="share")
@click.argument("template_id")
@click.option("--is-public", type=bool, required=True, help="Set public (true) or private (false)")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_sharing(template_id: str, is_public: bool, format: str):
    """Update template sharing settings."""
    client = get_client()

    try:
        result = client.update_template_sharing(template_id, {"is_public": is_public})
        status = "public" if is_public else "private"
        print_success(f"Template {template_id} is now {status}")
        format_output(result, format, title="Updated Template")

    except Exception as e:
        raise click.ClickException(f"Failed to update sharing settings: {str(e)}")
