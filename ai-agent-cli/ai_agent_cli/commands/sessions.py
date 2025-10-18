"""Session management commands."""

import click
import json
from pathlib import Path
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import (
    print_success,
    print_info,
    format_output,
    confirm,
)


@click.group(name="sessions")
def sessions():
    """Manage Claude Code sessions."""
    pass


@sessions.command(name="create")
@click.option("--name", help="Session name")
@click.option("--description", help="Session description")
@click.option("--working-directory", help="Working directory path")
@click.option("--allowed-tools", multiple=True, help="Allowed tool patterns (can specify multiple)")
@click.option("--system-prompt", help="Custom system prompt")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def create_session(
    name: Optional[str],
    description: Optional[str],
    working_directory: Optional[str],
    allowed_tools: tuple,
    system_prompt: Optional[str],
    format: str,
):
    """Create a new Claude Code session."""
    client = get_client()

    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if working_directory:
        data["working_directory"] = working_directory
    if allowed_tools:
        data["allowed_tools"] = list(allowed_tools)
    if system_prompt:
        data["system_prompt"] = system_prompt

    try:
        session = client.create_session(data)
        print_success(f"Session created: {session['id']}")
        format_output(session, format, title="Session Details")

    except Exception as e:
        raise click.ClickException(f"Failed to create session: {str(e)}")


@sessions.command(name="list")
@click.option("--status", type=click.Choice(["active", "paused", "completed", "failed"]), help="Filter by status")
@click.option("--is-fork", type=bool, help="Filter by fork status")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_sessions(status: Optional[str], is_fork: Optional[bool], page: int, page_size: int, format: str):
    """List all sessions."""
    client = get_client()

    params = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if is_fork is not None:
        params["is_fork"] = is_fork

    try:
        result = client.list_sessions(params)
        format_output(result, format, title="Sessions")

    except Exception as e:
        raise click.ClickException(f"Failed to list sessions: {str(e)}")


@sessions.command(name="get")
@click.argument("session_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_session(session_id: str, format: str):
    """Get session details by ID."""
    client = get_client()

    try:
        session = client.get_session(session_id)
        format_output(session, format, title=f"Session {session_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get session: {str(e)}")


@sessions.command(name="query")
@click.argument("session_id")
@click.argument("message")
@click.option("--fork", is_flag=True, help="Fork session before sending message")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def send_message(session_id: str, message: str, fork: bool, format: str):
    """Send a message to a session."""
    client = get_client()

    try:
        response = client.send_message(session_id, message, fork)
        print_success(f"Message sent to session {response['id']}")
        format_output(response, format, title="Query Response")

    except Exception as e:
        raise click.ClickException(f"Failed to send message: {str(e)}")


@sessions.command(name="messages")
@click.argument("session_id")
@click.option("--limit", default=50, help="Number of messages to return")
@click.option("--format", type=click.Choice(["table", "json"]), default="json", help="Output format")
def list_messages(session_id: str, limit: int, format: str):
    """List messages in a session."""
    client = get_client()

    try:
        messages = client.list_messages(session_id, limit)
        format_output(messages, format, title=f"Messages in Session {session_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to list messages: {str(e)}")


@sessions.command(name="tool-calls")
@click.argument("session_id")
@click.option("--limit", default=50, help="Number of tool calls to return")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_tool_calls(session_id: str, limit: int, format: str):
    """List tool calls in a session."""
    client = get_client()

    try:
        tool_calls = client.list_tool_calls(session_id, limit)
        format_output(tool_calls, format, title=f"Tool Calls in Session {session_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to list tool calls: {str(e)}")


@sessions.command(name="pause")
@click.argument("session_id")
def pause_session(session_id: str):
    """Pause an active session."""
    client = get_client()

    try:
        session = client.pause_session(session_id)
        print_success(f"Session {session_id} paused")

    except Exception as e:
        raise click.ClickException(f"Failed to pause session: {str(e)}")


@sessions.command(name="resume")
@click.argument("session_id")
@click.option("--fork", is_flag=True, help="Fork session before resuming")
def resume_session(session_id: str, fork: bool):
    """Resume a paused session."""
    client = get_client()

    try:
        session = client.resume_session(session_id, fork)
        print_success(f"Session {session['id']} resumed")

    except Exception as e:
        raise click.ClickException(f"Failed to resume session: {str(e)}")


@sessions.command(name="terminate")
@click.argument("session_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def terminate_session(session_id: str, yes: bool):
    """Terminate a session."""
    if not yes and not confirm(f"Are you sure you want to terminate session {session_id}?"):
        print_info("Aborted")
        return

    client = get_client()

    try:
        client.terminate_session(session_id)
        print_success(f"Session {session_id} terminated")

    except Exception as e:
        raise click.ClickException(f"Failed to terminate session: {str(e)}")


@sessions.command(name="download-workdir")
@click.argument("session_id")
@click.option("--output", "-o", required=True, help="Output file path (.tar.gz)")
def download_working_directory(session_id: str, output: str):
    """Download session working directory as tar.gz archive."""
    client = get_client()
    output_path = Path(output)

    try:
        client.download_working_directory(session_id, output_path)
        print_success(f"Working directory downloaded to {output_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to download working directory: {str(e)}")
