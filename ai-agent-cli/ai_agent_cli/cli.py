"""Main CLI entry point."""

import click
from ai_agent_cli.core.config import config_manager
from ai_agent_cli.core.exceptions import CLIError
from ai_agent_cli.utils.output import console, print_error

# Import command groups
from ai_agent_cli.commands import auth, tasks, reports, mcp, admin, config, monitoring
# from ai_agent_cli.commands import sessions, session_templates  # REMOVED: Using tasks API only


@click.group()
@click.version_option(version="1.0.0", prog_name="ai-agent")
@click.pass_context
def cli(ctx):
    """AI Agent CLI - Command-line interface for AI-Agent-API-Service.

    Interact with the AI-Agent-API-Service through a powerful command-line interface.
    Manage sessions, tasks, reports, and MCP servers via REST API.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_manager"] = config_manager


# Register command groups
cli.add_command(auth.auth)
# cli.add_command(sessions.sessions)  # REMOVED: Using tasks API only
# cli.add_command(session_templates.session_templates)  # REMOVED: Using tasks API only
cli.add_command(tasks.tasks)
cli.add_command(reports.reports)
cli.add_command(mcp.mcp)
cli.add_command(admin.admin)
cli.add_command(config.config)
cli.add_command(monitoring.monitoring)


def main():
    """Main entry point."""
    try:
        cli()
    except CLIError as e:
        print_error(str(e))
        exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
