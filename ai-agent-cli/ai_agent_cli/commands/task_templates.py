"""Task template management commands."""

import click
import json
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, print_info, format_output, confirm


@click.group(name="task-templates")
def task_templates():
    """Manage task templates."""
    pass


@task_templates.command(name="list")
@click.option("--category", help="Filter by category")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_templates(category: Optional[str], tags: tuple, page: int, page_size: int, format: str):
    """List all task templates."""
    client = get_client()

    params = {"page": page, "page_size": page_size}
    if category:
        params["category"] = category
    if tags:
        params["tags"] = list(tags)

    try:
        result = client.list_task_templates(params)
        format_output(result, format, title="Task Templates")

    except Exception as e:
        raise click.ClickException(f"Failed to list task templates: {str(e)}")


@task_templates.command(name="get")
@click.argument("template_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_template(template_id: str, format: str):
    """Get task template details by ID."""
    client = get_client()

    try:
        template = client.get_task_template(template_id)
        format_output(template, format, title=f"Task Template {template_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get task template: {str(e)}")


@task_templates.command(name="create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
@click.option("--category", help="Template category (kubernetes, docker, git, monitoring, database)")
@click.option("--icon", help="Icon name for UI")
@click.option("--prompt-template", required=True, help="Prompt template with {{variables}}")
@click.option("--allowed-tools", multiple=True, help="Allowed tool patterns")
@click.option("--disallowed-tools", multiple=True, help="Disallowed tool patterns")
@click.option("--sdk-options", help="SDK options as JSON string")
@click.option("--generate-report", is_flag=True, help="Generate report after execution")
@click.option("--report-format", type=click.Choice(["html", "pdf", "json", "markdown"]), default="html", help="Report format")
@click.option("--tags", multiple=True, help="Template tags")
@click.option("--template-variables-schema", help="JSON Schema for template variables")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_template(
    name: str,
    description: Optional[str],
    category: Optional[str],
    icon: Optional[str],
    prompt_template: str,
    allowed_tools: tuple,
    disallowed_tools: tuple,
    sdk_options: Optional[str],
    generate_report: bool,
    report_format: str,
    tags: tuple,
    template_variables_schema: Optional[str],
    format: str,
):
    """Create a new task template (admin only)."""
    client = get_client()

    data = {
        "name": name,
        "prompt_template": prompt_template,
        "generate_report": generate_report,
        "report_format": report_format,
        "is_public": True,
        "is_active": True,
    }

    if description:
        data["description"] = description
    if category:
        data["category"] = category
    if icon:
        data["icon"] = icon
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if disallowed_tools:
        data["disallowed_tools"] = list(disallowed_tools)
    if sdk_options:
        try:
            data["sdk_options"] = json.loads(sdk_options)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for sdk-options")
    if tags:
        data["tags"] = list(tags)
    if template_variables_schema:
        try:
            data["template_variables_schema"] = json.loads(template_variables_schema)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for template-variables-schema")

    try:
        template = client.create_task_template(data)
        print_success(f"Task template created: {template['id']}")
        format_output(template, format, title="Task Template Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create task template: {str(e)}")


@task_templates.command(name="update")
@click.argument("template_id")
@click.option("--name", help="Template name")
@click.option("--description", help="Template description")
@click.option("--category", help="Template category")
@click.option("--icon", help="Icon name")
@click.option("--prompt-template", help="Prompt template")
@click.option("--is-active", type=bool, help="Active status")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_template(
    template_id: str,
    name: Optional[str],
    description: Optional[str],
    category: Optional[str],
    icon: Optional[str],
    prompt_template: Optional[str],
    is_active: Optional[bool],
    format: str,
):
    """Update a task template (admin only)."""
    client = get_client()

    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if category is not None:
        data["category"] = category
    if icon is not None:
        data["icon"] = icon
    if prompt_template is not None:
        data["prompt_template"] = prompt_template
    if is_active is not None:
        data["is_active"] = is_active

    if not data:
        raise click.ClickException("No update fields provided")

    try:
        template = client.update_task_template(template_id, data)
        print_success(f"Task template {template_id} updated")
        format_output(template, format, title="Updated Task Template")

    except Exception as e:
        raise click.ClickException(f"Failed to update task template: {str(e)}")


@task_templates.command(name="delete")
@click.argument("template_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_template(template_id: str, yes: bool):
    """Delete a task template (admin only)."""
    if not yes and not confirm(f"Are you sure you want to delete task template {template_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.delete_task_template(template_id)
        print_success(f"Task template {template_id} deleted")

    except Exception as e:
        raise click.ClickException(f"Failed to delete task template: {str(e)}")


@task_templates.command(name="create-task")
@click.argument("template_id")
@click.option("--name", help="Custom task name (overrides template)")
@click.option("--description", help="Custom task description")
@click.option("--variables", help="Template variables as JSON string")
@click.option("--tags", multiple=True, help="Additional tags")
@click.option("--schedule-cron", help="Cron expression for scheduling")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_task_from_template(
    template_id: str,
    name: Optional[str],
    description: Optional[str],
    variables: Optional[str],
    tags: tuple,
    schedule_cron: Optional[str],
    format: str,
):
    """Create a task from a template."""
    client = get_client()

    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if variables:
        try:
            data["variables"] = json.loads(variables)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for variables")
    if tags:
        data["tags"] = list(tags)
    if schedule_cron:
        data["schedule_cron"] = schedule_cron

    try:
        task = client.create_task_from_template(template_id, data)
        print_success(f"Task created from template: {task['id']}")
        format_output(task, format, title="Created Task")

    except Exception as e:
        raise click.ClickException(f"Failed to create task from template: {str(e)}")


@task_templates.command(name="stats")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_stats(format: str):
    """Get task template usage statistics."""
    client = get_client()

    try:
        stats = client.get_task_template_stats()
        format_output(stats, format, title="Task Template Statistics")

    except Exception as e:
        raise click.ClickException(f"Failed to get statistics: {str(e)}")


@task_templates.command(name="category")
@click.argument("category")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_by_category(category: str, page: int, page_size: int, format: str):
    """Get task templates by category."""
    client = get_client()

    params = {"page": page, "page_size": page_size}

    try:
        result = client.get_templates_by_category(category, params)
        format_output(result, format, title=f"Templates in category: {category}")

    except Exception as e:
        raise click.ClickException(f"Failed to get templates by category: {str(e)}")
