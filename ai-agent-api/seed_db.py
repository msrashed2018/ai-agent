#!/usr/bin/env python3
"""Database seeding script.

This script seeds the database with default data including:
- Default organization
- Admin and test users
- Task templates
- Tool groups
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import AsyncSessionLocal
from app.db.seed import seed_default_data


async def main():
    """Run database seeding."""
    print("🌱 Starting database seeding process...")

    async with AsyncSessionLocal() as db:
        try:
            await seed_default_data(db)
            print("✅ Database seeding completed successfully!")
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
