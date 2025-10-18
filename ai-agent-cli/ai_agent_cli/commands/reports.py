"""Report management commands."""

import click
from pathlib import Path
from typing import Optional
from ai_agent_cli.core.client import get_client
from ai_agent_cli.utils.output import print_success, format_output


@click.group(name="reports")
def reports():
    """Manage session reports."""
    pass


@reports.command(name="list")
@click.option("--session-id", help="Filter by session ID")
@click.option("--report-type", help="Filter by report type")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=20, help="Items per page")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def list_reports(
    session_id: Optional[str],
    report_type: Optional[str],
    page: int,
    page_size: int,
    format: str,
):
    """List all reports."""
    client = get_client()

    params = {"page": page, "page_size": page_size}
    if session_id:
        params["session_id"] = session_id
    if report_type:
        params["report_type"] = report_type

    try:
        result = client.list_reports(params)
        format_output(result, format, title="Reports")

    except Exception as e:
        raise click.ClickException(f"Failed to list reports: {str(e)}")


@reports.command(name="get")
@click.argument("report_id")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def get_report(report_id: str, format: str):
    """Get report details by ID."""
    client = get_client()

    try:
        report = client.get_report(report_id)
        format_output(report, format, title=f"Report {report_id}")

    except Exception as e:
        raise click.ClickException(f"Failed to get report: {str(e)}")


@reports.command(name="download")
@click.argument("report_id")
@click.option("--format", type=click.Choice(["html", "pdf", "json"]), default="html", help="Report format")
@click.option("--output", "-o", required=True, help="Output file path")
def download_report(report_id: str, format: str, output: str):
    """Download a report file."""
    client = get_client()
    output_path = Path(output)

    try:
        client.download_report(report_id, format, output_path)
        print_success(f"Report downloaded to {output_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to download report: {str(e)}")
