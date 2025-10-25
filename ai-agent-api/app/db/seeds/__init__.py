"""Database seeding module - orchestrates all seed functions."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds.organizations_users import seed_organizations_and_users
from app.db.seeds.task_templates import seed_task_templates
from app.db.seeds.tool_groups import seed_tool_groups
from app.db.seeds.mcp_servers import seed_mcp_servers
from app.db.seeds.hooks import seed_hooks
from app.db.seeds.tasks import seed_tasks

logger = logging.getLogger(__name__)


async def seed_all(db: AsyncSession) -> None:
    """Run all seed functions in correct order.

    This function orchestrates the complete database seeding process,
    ensuring all default data is created at startup to prepare the system.

    Seeding order:
    1. Organizations and Users (foundational data)
    2. Task Templates (independent)
    3. Tool Groups (depends on users)
    4. MCP Servers (depends on users)
    5. Hooks (depends on users)
    6. Tasks (depends on users and tool groups)

    Args:
        db: AsyncSession for database operations
    """
    try:
        logger.info("Starting database seeding process...")

        # Seed organizations and users first (foundational data)
        await seed_organizations_and_users(db)

        # Seed task templates (independent)
        await seed_task_templates(db)

        # Seed tool groups (depends on users)
        await seed_tool_groups(db)

        # Seed MCP servers (depends on users)
        await seed_mcp_servers(db)

        # Seed hooks (depends on users)
        await seed_hooks(db)

        # Seed tasks (depends on users and tool groups)
        await seed_tasks(db)

        logger.info("✅ All database seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error during database seeding: {e}")
        raise
