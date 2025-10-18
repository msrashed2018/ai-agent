"""Configuration commands."""

import click
from ai_agent_cli.core.config import config_manager
from ai_agent_cli.utils.output import print_success, print_info, print_key_value


@click.group(name="config")
def config():
    """Manage CLI configuration."""
    pass


@config.command(name="show")
def show_config():
    """Show current configuration."""
    cfg = config_manager.load()

    config_dict = {
        "api_url": cfg.api_url,
        "default_output_format": cfg.default_output_format,
        "timeout": cfg.timeout,
        "authenticated": "Yes" if cfg.access_token else "No",
        "config_file": str(config_manager.config_file),
    }

    print_key_value(config_dict, title="CLI Configuration")


@config.command(name="set-api-url")
@click.argument("url")
def set_api_url(url: str):
    """Set the API base URL."""
    config_manager.set_api_url(url)
    print_success(f"API URL set to: {url}")


@config.command(name="get-api-url")
def get_api_url():
    """Get the current API base URL."""
    url = config_manager.get_api_url()
    print_info(f"API URL: {url}")


@config.command(name="reset")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def reset_config(yes: bool):
    """Reset configuration to defaults."""
    from ai_agent_cli.utils.output import confirm

    if not yes and not confirm("Are you sure you want to reset configuration to defaults?"):
        print_info("Aborted")
        return

    # Clear tokens and reset to default config
    config_manager.clear_tokens()

    from ai_agent_cli.core.config import CLIConfig
    default_config = CLIConfig()
    config_manager.save(default_config)

    print_success("Configuration reset to defaults")
