"""Seed organizations and users."""

import logging
import bcrypt
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import OrganizationModel, UserModel

logger = logging.getLogger(__name__)


async def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


async def seed_organizations_and_users(db: AsyncSession) -> None:
    """Seed default organization and users.

    Creates:
    - Default organization with enterprise plan
    - Admin user with superuser privileges
    - Regular test user

    Args:
        db: AsyncSession for database operations
    """
    try:
        # Check if we already have organizations
        result = await db.execute(select(OrganizationModel))
        existing_orgs = result.scalars().first()

        if existing_orgs is not None:
            logger.info("  Organizations already exist, skipping")
            return

        logger.info("Seeding organizations and users...")

        # Create default organization
        org = OrganizationModel(
            id=uuid4(),
            name="Default Organization",
            slug="default",
            primary_email="admin@default.org",
            primary_contact_name="System Administrator",
            plan="enterprise",
            max_users=100,
            max_sessions_per_month=10000,
            max_storage_gb=1000,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(org)
        await db.flush()  # Get the ID for foreign key references
        logger.info(f"  ✅ Created organization: {org.name}")

        # Create admin user
        admin_password = "admin123"
        admin_user = UserModel(
            id=uuid4(),
            organization_id=org.id,
            email="admin@default.org",
            username="admin",
            password_hash=await hash_password(admin_password),
            full_name="System Administrator",
            role="admin",
            is_active=True,
            is_superuser=True,
            max_concurrent_sessions=10,
            max_api_calls_per_hour=5000,
            max_storage_mb=10240,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(admin_user)
        logger.info(f"  ✅ Created admin user: {admin_user.username}")

        # Create regular test user
        user_password = "user1234"
        test_user = UserModel(
            id=uuid4(),
            organization_id=org.id,
            email="user@default.org",
            username="user",
            password_hash=await hash_password(user_password),
            full_name="Test User",
            role="user",
            is_active=True,
            is_superuser=False,
            max_concurrent_sessions=5,
            max_api_calls_per_hour=1000,
            max_storage_mb=1024,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(test_user)
        logger.info(f"  ✅ Created test user: {test_user.username}")

        await db.commit()

        logger.info("Organizations and users seeded successfully!")
        logger.info("Default admin credentials - Username: admin, Password: admin123")
        logger.info("Default user credentials - Username: user, Password: user1234")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error seeding organizations/users: {e}")
        raise
