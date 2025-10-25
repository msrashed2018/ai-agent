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
@click.option("--tool-group-id", help="Tool group UUID for allowed/disallowed tools")
@click.option("--allowed-tools", multiple=True, help="Allowed tool patterns")
@click.option("--disallowed-tools", multiple=True, help="Disallowed tool patterns")
@click.option("--is-scheduled", is_flag=True, help="Enable scheduling")
@click.option("--schedule-cron", help="Cron expression for scheduling")
@click.option("--schedule-enabled", is_flag=True, help="Enable schedule immediately")
@click.option("--generate-report", is_flag=True, help="Generate report after execution")
@click.option("--report-format", type=click.Choice(["html", "pdf", "json", "markdown"]), default="html", help="Report format")
@click.option("--tags", multiple=True, help="Task tags")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_task(
    name: str,
    description: Optional[str],
    prompt_template: str,
    tool_group_id: Optional[str],
    allowed_tools: tuple,
    disallowed_tools: tuple,
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
    if tool_group_id:
        data["tool_group_id"] = tool_group_id
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if disallowed_tools:
        data["disallowed_tools"] = list(disallowed_tools)
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
@click.option("--prompt-template", help="Prompt template with {{variables}}")
@click.option("--tool-group-id", help="Tool group UUID for allowed/disallowed tools")
@click.option("--allowed-tools", multiple=True, help="Allowed tool patterns")
@click.option("--disallowed-tools", multiple=True, help="Disallowed tool patterns")
@click.option("--is-scheduled", is_flag=True, help="Enable scheduling")
@click.option("--schedule-cron", help="Cron expression for scheduling")
@click.option("--schedule-enabled", type=bool, help="Enable/disable schedule")
@click.option("--generate-report", type=bool, help="Enable/disable report generation")
@click.option("--report-format", type=click.Choice(["html", "pdf", "json", "markdown"]), help="Report format")
@click.option("--tags", multiple=True, help="Task tags")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def update_task(
    task_id: str,
    name: Optional[str],
    description: Optional[str],
    prompt_template: Optional[str],
    tool_group_id: Optional[str],
    allowed_tools: tuple,
    disallowed_tools: tuple,
    is_scheduled: bool,
    schedule_cron: Optional[str],
    schedule_enabled: Optional[bool],
    generate_report: Optional[bool],
    report_format: Optional[str],
    tags: tuple,
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
    if tool_group_id is not None:
        data["tool_group_id"] = tool_group_id
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if disallowed_tools:
        data["disallowed_tools"] = list(disallowed_tools)
    if is_scheduled:
        data["is_scheduled"] = is_scheduled
    if schedule_cron is not None:
        data["schedule_cron"] = schedule_cron
    if schedule_enabled is not None:
        data["schedule_enabled"] = schedule_enabled
    if generate_report is not None:
        data["generate_report"] = generate_report
    if report_format is not None:
        data["report_format"] = report_format
    if tags:
        data["tags"] = list(tags)

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


@tasks.command(name="retry-execution")
@click.argument("execution_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def retry_execution(execution_id: str, format: str):
    """Retry a failed task execution.

    Can retry executions with status: pending, queued, or failed.

    Example:
        ai-agent tasks retry-execution abc123
    """
    client = get_client()

    try:
        execution = client.retry_task_execution(execution_id)
        print_success(f"Execution {execution_id} queued for retry")
        format_output(execution, format, title="Retried Execution")

    except Exception as e:
        raise click.ClickException(f"Failed to retry execution: {str(e)}")


# ===== NEW COMMANDS: Tool Calls, Cancellation, Working Directory =====


@tasks.command(name="tool-calls")
@click.argument("execution_id")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_tool_calls(execution_id: str, page: int, page_size: int, format: str):
    """List tool calls for a task execution.

    Shows all commands/tools that were executed during the task run,
    including inputs, outputs, status, and timing information.

    Note: Only available for sync mode executions (with sessions).
    """
    client = get_client()

    params = {"page": page, "page_size": page_size}

    try:
        result = client.get_execution_tool_calls(execution_id, params)
        format_output(result, format, title=f"Tool Calls for Execution {execution_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to list tool calls: {str(e)}")


@tasks.command(name="cancel")
@click.argument("execution_id")
@click.option("--reason", help="Cancellation reason")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def cancel_execution(execution_id: str, reason: Optional[str], yes: bool, format: str):
    """Cancel a running task execution.

    Can cancel:
    - PENDING or QUEUED executions (cancelled immediately)
    - RUNNING async mode executions (marked for cancellation)

    Cannot cancel:
    - RUNNING sync mode executions (subprocess safety)
    - Already finished executions (COMPLETED, FAILED, CANCELLED)
    """
    if not yes and not confirm(f"Are you sure you want to cancel execution {execution_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    data = {}
    if reason:
        data["reason"] = reason

    try:
        execution = client.cancel_task_execution(execution_id, data)
        print_success(f"Execution {execution_id} cancelled")
        format_output(execution, format, title="Cancelled Execution")

    except Exception as e:
        raise click.ClickException(f"Failed to cancel execution: {str(e)}")


@tasks.command(name="files")
@click.argument("execution_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_execution_files(execution_id: str, format: str):
    """List files in task execution's working directory.

    Shows all files created/modified during task execution with metadata
    (path, size, last modified timestamp).

    Note: Working directory must still exist (not archived or cleaned up).
    """
    client = get_client()

    try:
        result = client.get_execution_files(execution_id)
        format_output(result, format, title=f"Files for Execution {execution_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to list files: {str(e)}")


@tasks.command(name="download-file")
@click.argument("execution_id")
@click.argument("file_path")
@click.option("--output", "-o", help="Output file path (default: use original filename)")
def download_execution_file(execution_id: str, file_path: str, output: Optional[str]):
    """Download a specific file from task execution's working directory.

    FILE_PATH should be the relative path as shown in 'tasks files' command.

    Example:
        ai-agent tasks download-file abc123 output.txt -o /tmp/result.txt
    """
    import os
    client = get_client()

    try:
        content = client.download_execution_file(execution_id, file_path)

        # Determine output path
        output_path = output or os.path.basename(file_path)

        # Write file
        with open(output_path, 'wb') as f:
            f.write(content)

        print_success(f"File downloaded to: {output_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to download file: {str(e)}")


@tasks.command(name="archive")
@click.argument("execution_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def archive_execution(execution_id: str, yes: bool, format: str):
    """Archive task execution's working directory to tar.gz.

    Creates a compressed archive and deletes the original directory to save space.

    WARNING: This operation is irreversible! The directory will be deleted after archiving.
    """
    if not yes and not confirm(
        f"Archive execution {execution_id}? This will delete the original directory!"
    ):
        print_info("Aborted")
        return

    client = get_client()

    try:
        result = client.archive_execution_directory(execution_id)
        print_success(f"Execution directory archived successfully")
        format_output(result, format, title="Archive Details")

    except Exception as e:
        raise click.ClickException(f"Failed to archive directory: {str(e)}")


@tasks.command(name="download-archive")
@click.argument("execution_id")
@click.option("--output", "-o", help="Output file path (default: <execution_id>.tar.gz)")
def download_archive(execution_id: str, output: Optional[str]):
    """Download archived working directory as tar.gz.

    The execution_id is the same as the original task execution ID.
    """
    client = get_client()

    try:
        content = client.download_archive(execution_id)

        # Determine output path
        output_path = output or f"{execution_id}.tar.gz"

        # Write archive
        with open(output_path, 'wb') as f:
            f.write(content)

        print_success(f"Archive downloaded to: {output_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to download archive: {str(e)}")
