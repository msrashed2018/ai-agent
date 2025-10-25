"""Seed tool groups."""

import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.tool_group import ToolGroupModel

logger = logging.getLogger(__name__)


# Default tool groups with common configurations
# Note: Tool names must match valid Claude Code tools:
# Valid tools: Bash, Read, Write, Edit, Glob, Grep, Task, WebFetch, WebSearch,
#              AskUserQuestion, Skill, SlashCommand, NotebookEdit, mcp__*__*, *
DEFAULT_TOOL_GROUPS = [
    {
        "name": "Read-Only Tools",
        "description": "Safe tools for reading and inspecting without making changes",
        "allowed_tools": ["Read", "Glob", "Grep"],
        "disallowed_tools": [],
        "is_public": True,
    },
    {
        "name": "Development Tools",
        "description": "Tools for software development tasks",
        "allowed_tools": ["Read", "Write", "Glob", "Grep", "Bash"],
        "disallowed_tools": ["Edit"],
        "is_public": True,
    },
    {
        "name": "DevOps Tools",
        "description": "Tools for infrastructure and deployment tasks",
        "allowed_tools": ["Bash", "Read", "Glob", "Grep"],
        "disallowed_tools": ["Write", "Edit"],
        "is_public": True,
    },
    {
        "name": "Data Analysis Tools",
        "description": "Tools for data processing and analysis",
        "allowed_tools": ["Read", "Grep", "Bash"],
        "disallowed_tools": ["Write", "Edit"],
        "is_public": True,
    },
]


async def seed_tool_groups(db: AsyncSession) -> None:
    """Seed default tool groups.

    Creates default tool groups assigned to admin user that can be reused
    by all users in the organization.

    Args:
        db: AsyncSession for database operations
    """
    logger.info("Seeding tool groups...")

    # Get admin user to assign tool groups to
    result = await db.execute(
        select(UserModel).where(UserModel.username == "admin")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        logger.warning("  Admin user not found, skipping tool groups seeding")
        return

    # Check which tool groups already exist
    for group_data in DEFAULT_TOOL_GROUPS:
        result = await db.execute(
            select(ToolGroupModel).where(
                ToolGroupModel.name == group_data["name"],
                ToolGroupModel.user_id == admin_user.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"  Tool group '{group_data['name']}' already exists, skipping")
            continue

        # Create new tool group with exact model structure
        tool_group = ToolGroupModel(
            id=uuid4(),
            user_id=admin_user.id,
            name=group_data["name"],
            description=group_data["description"],
            allowed_tools=group_data["allowed_tools"],
            disallowed_tools=group_data.get("disallowed_tools", []),
            is_public=group_data.get("is_public", False),
            is_active=True,
            is_deleted=False,
        )

        db.add(tool_group)
        logger.info(f"  ✅ Created tool group: {group_data['name']}")

    await db.commit()
    logger.info("Tool groups seeded successfully!")
