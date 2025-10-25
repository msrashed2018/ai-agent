"""Database seeding utilities for AI Agent API.

This module provides the main entry point for database seeding.
The actual seed logic is organized into modular files in app/db/seeds/.

Usage:
    from app.db.seed import seed_default_data
    await seed_default_data(db)
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds import seed_all

logger = logging.getLogger(__name__)


async def seed_default_data(db: AsyncSession) -> None:
    """Seed the database with all default data.

    This is the main entry point for database seeding. It delegates to
    the modular seed functions in app/db/seeds/ which are organized by entity:
    - Organizations and Users
    - Task Templates
    - Tool Groups

    Args:
        db: AsyncSession for database operations
    """
    await seed_all(db)