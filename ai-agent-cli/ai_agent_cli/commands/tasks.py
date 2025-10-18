"""Task management commands."""

import click
import json
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, print_info, format_output, confirm


@click.group(name="tasks")
def tasks():
    """Manage automated tasks."""
    pass


@tasks.command(name="create")
@click.option("--name", required=True, help="Task name")
@click.option("--description", help="Task description")
@click.option("--prompt-template", required=True, help="Prompt template with {{variables}}")
@click.option("--allowed-tools", multiple=True, help="Allowed tool patterns")
@click.option("--is-scheduled", is_flag=True, help="Enable scheduling")
@click.option("--schedule-cron", help="Cron expression for scheduling")
@click.option("--schedule-enabled", is_flag=True, help="Enable schedule immediately")
@click.option("--generate-report", is_flag=True, help="Generate report after execution")
@click.option("--report-format", type=click.Choice(["html", "pdf", "json"]), default="html", help="Report format")
@click.option("--tags", multiple=True, help="Task tags")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_task(
    name: str,
    description: Optional[str],
    prompt_template: str,
    allowed_tools: tuple,
    is_scheduled: bool,
    schedule_cron: Optional[str],
    schedule_enabled: bool,
    generate_report: bool,
    report_format: str,
    tags: tuple,
    format: str,
):
    """Create a new task."""
    client = get_client()

    data = {
        "name": name,
        "prompt_template": prompt_template,
        "is_scheduled": is_scheduled,
        "schedule_enabled": schedule_enabled,
        "generate_report": generate_report,
        "report_format": report_format,
    }

    if description:
        data["description"] = description
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if schedule_cron:
        data["schedule_cron"] = schedule_cron
    if tags:
        data["tags"] = list(tags)

    try:
        task = client.create_task(data)
        print_success(f"Task created: {task['id']}")
        format_output(task, format, title="Task Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create task: {str(e)}")


@tasks.command(name="list")
@click.option("--tags", multiple=True, help="Filter by tags")
@click.option("--is-scheduled", type=bool, help="Filter by scheduled status")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_tasks(tags: tuple, is_scheduled: Optional[bool], page: int, page_size: int, format: str):
    """List all tasks."""
    client = get_client()

    params = {"page": page, "page_size": page_size}
    if tags:
        params["tags"] = list(tags)
    if is_scheduled is not None:
        params["is_scheduled"] = is_scheduled

    try:
        result = client.list_tasks(params)
        format_output(result, format, title="Tasks")

    except Exception as e:
        raise click.ClickException(f"Failed to list tasks: {str(e)}")


@tasks.command(name="get")
@click.argument("task_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_task(task_id: str, format: str):
    """Get task details by ID."""
    client = get_client()

    try:
        task = client.get_task(task_id)
        format_output(task, format, title=f"Task {task_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get task: {str(e)}")


@tasks.command(name="update")
@click.argument("task_id")
@click.option("--name", help="Task name")
@click.option("--description", help="Task description")
@click.option("--prompt-template", help="Prompt template")
@click.option("--schedule-enabled", type=bool, help="Enable/disable schedule")
@click.option("--generate-report", type=bool, help="Enable/disable report generation")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_task(
    task_id: str,
    name: Optional[str],
    description: Optional[str],
    prompt_template: Optional[str],
    schedule_enabled: Optional[bool],
    generate_report: Optional[bool],
    format: str,
):
    """Update a task."""
    client = get_client()

    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if prompt_template is not None:
        data["prompt_template"] = prompt_template
    if schedule_enabled is not None:
        data["schedule_enabled"] = schedule_enabled
    if generate_report is not None:
        data["generate_report"] = generate_report

    if not data:
        raise click.ClickException("No update fields provided")

    try:
        task = client.update_task(task_id, data)
        print_success(f"Task {task_id} updated")
        format_output(task, format, title="Updated Task")

    except Exception as e:
        raise click.ClickException(f"Failed to update task: {str(e)}")


@tasks.command(name="delete")
@click.argument("task_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_task(task_id: str, yes: bool):
    """Delete a task."""
    if not yes and not confirm(f"Are you sure you want to delete task {task_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.delete_task(task_id)
        print_success(f"Task {task_id} deleted")

    except Exception as e:
        raise click.ClickException(f"Failed to delete task: {str(e)}")


@tasks.command(name="execute")
@click.argument("task_id")
@click.option("--variables", help="Template variables as JSON string")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def execute_task(task_id: str, variables: Optional[str], format: str):
    """Execute a task."""
    client = get_client()

    vars_dict = {}
    if variables:
        try:
            vars_dict = json.loads(variables)
        except json.JSONDecodeError:
            raise click.ClickException("Invalid JSON for variables")

    try:
        execution = client.execute_task(task_id, vars_dict)
        print_success(f"Task execution started: {execution['id']}")
        format_output(execution, format, title="Task Execution")

    except Exception as e:
        raise click.ClickException(f"Failed to execute task: {str(e)}")


@tasks.command(name="executions")
@click.argument("task_id")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_executions(task_id: str, page: int, page_size: int, format: str):
    """List executions for a task."""
    client = get_client()

    params = {"page": page, "page_size": page_size}

    try:
        result = client.list_task_executions(task_id, params)
        format_output(result, format, title=f"Executions for Task {task_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to list executions: {str(e)}")


@tasks.command(name="execution-status")
@click.argument("execution_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_execution_status(execution_id: str, format: str):
    """Get task execution status."""
    client = get_client()

    try:
        execution = client.get_task_execution(execution_id)
        format_output(execution, format, title=f"Execution {execution_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get execution status: {str(e)}")
