"""Output formatting utilities."""

import json
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box
from tabulate import tabulate


console = Console()


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {message}", style="bold red")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]![/yellow] {message}", style="yellow")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_json(data: Any, title: Optional[str] = None) -> None:
    """Print data as formatted JSON."""
    json_str = json.dumps(data, indent=2, default=str)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)

    if title:
        console.print(Panel(syntax, title=title, border_style="blue"))
    else:
        console.print(syntax)


def print_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> None:
    """Print data as formatted table."""
    if not data:
        print_warning("No data to display")
        return

    if columns is None:
        columns = list(data[0].keys())

    table = Table(title=title, box=box.ROUNDED, show_header=True, header_style="bold cyan")

    for column in columns:
        table.add_column(column.replace("_", " ").title())

    for row in data:
        table.add_row(*[str(row.get(col, "")) for col in columns])

    console.print(table)


def print_key_value(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """Print data as key-value pairs."""
    table = Table(title=title, box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Key", style="cyan", justify="right")
    table.add_column("Value", style="white")

    for key, value in data.items():
        key_display = key.replace("_", " ").title()
        if isinstance(value, (dict, list)):
            value_display = json.dumps(value, default=str)
        else:
            value_display = str(value)
        table.add_row(key_display, value_display)

    console.print(table)


def format_output(data: Any, format: str = "table", title: Optional[str] = None) -> None:
    """Format and print output based on format type."""
    if format == "json":
        print_json(data, title)
    elif format == "table":
        if isinstance(data, list):
            print_table(data, title=title)
        elif isinstance(data, dict):
            # Check if it's a paginated response
            if "items" in data and isinstance(data["items"], list):
                print_table(data["items"], title=title)
                if "total" in data:
                    print_info(
                        f"Showing page {data.get('page', 1)} of {data.get('total_pages', 1)} "
                        f"({data['total']} total items)"
                    )
            else:
                print_key_value(data, title)
        else:
            console.print(data)
    else:
        console.print(data)


def confirm(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation."""
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default
    return response in ["y", "yes"]
