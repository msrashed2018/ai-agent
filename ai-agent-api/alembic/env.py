"""
Alembic environment configuration for async SQLAlchemy.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models for autogenerate support
from app.core.config import settings
from app.database.base import Base
from app.models.user import UserModel, OrganizationModel
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.tool_call import ToolCallModel
from app.models.task import TaskModel
from app.models.task_execution import TaskExecutionModel
from app.models.report import ReportModel
from app.models.audit_log import AuditLogModel
from app.models.mcp_server import MCPServerModel
from app.models.working_directory import WorkingDirectoryModel
from app.models.hook import HookModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def render_item(type_, obj, autogen_context):
    """Render custom types without module prefix."""
    from app.database.base import JSONB, ARRAY, INET
    from sqlalchemy import String

    if type_ == "type":
        if isinstance(obj, JSONB):
            return "JSONB()"
        elif isinstance(obj, INET):
            return "INET()"
        elif isinstance(obj, ARRAY):
            # Get the item_type from the ARRAY instance
            item_type = getattr(obj, 'item_type', String)
            item_type_name = item_type.__name__ if hasattr(item_type, '__name__') else "String"
            return f"ARRAY(sa.{item_type_name})"
    return False


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
