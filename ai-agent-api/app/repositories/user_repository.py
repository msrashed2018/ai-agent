"""User repository for database operations."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserModel
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """Repository for user database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(UserModel, db)

    async def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """Get user by ID (excluding soft-deleted)."""
        result = await self.db.execute(
            select(UserModel).where(
                and_(
                    UserModel.id == user_id,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        result = await self.db.execute(
            select(UserModel).where(
                and_(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username."""
        result = await self.db.execute(
            select(UserModel).where(
                and_(
                    UserModel.username == username,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get all users in an organization."""
        result = await self.db.execute(
            select(UserModel)
            .where(
                and_(
                    UserModel.organization_id == organization_id,
                    UserModel.deleted_at.is_(None)
                )
            )
            .order_by(UserModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get all active users."""
        result = await self.db.execute(
            select(UserModel)
            .where(
                and_(
                    UserModel.is_active == True,
                    UserModel.deleted_at.is_(None)
                )
            )
            .order_by(UserModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_role(
        self,
        role: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserModel]:
        """Get users by role."""
        result = await self.db.execute(
            select(UserModel)
            .where(
                and_(
                    UserModel.role == role,
                    UserModel.deleted_at.is_(None)
                )
            )
            .order_by(UserModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: UUID) -> bool:
        """Update user's last login timestamp."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                last_login_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def update_password(self, user_id: UUID, password_hash: str) -> bool:
        """Update user's password hash."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                password_hash=password_hash,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def activate(self, user_id: UUID) -> bool:
        """Activate a user account."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=True, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def deactivate(self, user_id: UUID) -> bool:
        """Deactivate a user account."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=False
            )
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def update_quotas(
        self,
        user_id: UUID,
        max_concurrent_sessions: Optional[int] = None,
        max_api_calls_per_hour: Optional[int] = None,
        max_storage_mb: Optional[int] = None,
    ) -> bool:
        """Update user quotas."""
        values = {"updated_at": datetime.utcnow()}
        
        if max_concurrent_sessions is not None:
            values["max_concurrent_sessions"] = max_concurrent_sessions
        if max_api_calls_per_hour is not None:
            values["max_api_calls_per_hour"] = max_api_calls_per_hour
        if max_storage_mb is not None:
            values["max_storage_mb"] = max_storage_mb
        
        stmt = update(UserModel).where(UserModel.id == user_id).values(**values)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count_by_organization(self, organization_id: UUID) -> int:
        """Count users in an organization."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(UserModel)
            .where(
                and_(
                    UserModel.organization_id == organization_id,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(UserModel)
            .where(
                and_(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one() > 0

    async def username_exists(self, username: str) -> bool:
        """Check if username is already taken."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(UserModel)
            .where(
                and_(
                    UserModel.username == username,
                    UserModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one() > 0
