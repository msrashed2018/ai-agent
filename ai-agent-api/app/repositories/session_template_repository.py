"""Session template repository for database operations."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_, func, any_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session_template import SessionTemplateModel
from app.repositories.base import BaseRepository


class SessionTemplateRepository(BaseRepository[SessionTemplateModel]):
    """Repository for session template database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionTemplateModel, db)

    async def get_by_id(self, template_id: str) -> Optional[SessionTemplateModel]:
        """Get template by ID (excluding soft-deleted)."""
        result = await self.db.execute(
            select(SessionTemplateModel).where(
                and_(
                    SessionTemplateModel.id == UUID(template_id),
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Get all templates owned by a user (excluding soft-deleted)."""
        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(
                and_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_public_templates(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Get all public templates (excluding soft-deleted)."""
        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(
                and_(
                    SessionTemplateModel.is_public == True,
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionTemplateModel.usage_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_organization_shared_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Get organization-shared templates for a user's organization."""
        # This will need to join with users table to filter by organization
        # For now, returning templates where is_organization_shared = True
        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(
                and_(
                    SessionTemplateModel.is_organization_shared == True,
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_accessible_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Get all templates accessible to a user (owned + public + org-shared)."""
        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(
                and_(
                    or_(
                        SessionTemplateModel.user_id == user_id,
                        SessionTemplateModel.is_public == True,
                        SessionTemplateModel.is_organization_shared == True,
                    ),
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(SessionTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Get templates by category (optionally filtered by user access)."""
        conditions = [
            SessionTemplateModel.category == category,
            SessionTemplateModel.deleted_at.is_(None)
        ]

        if user_id:
            conditions.append(
                or_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.is_public == True,
                    SessionTemplateModel.is_organization_shared == True,
                )
            )

        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(and_(*conditions))
            .order_by(SessionTemplateModel.usage_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_name(
        self,
        search_term: str,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Search templates by name (case-insensitive)."""
        conditions = [
            SessionTemplateModel.name.ilike(f"%{search_term}%"),
            SessionTemplateModel.deleted_at.is_(None)
        ]

        if user_id:
            conditions.append(
                or_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.is_public == True,
                    SessionTemplateModel.is_organization_shared == True,
                )
            )

        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(and_(*conditions))
            .order_by(SessionTemplateModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_tags(
        self,
        tags: List[str],
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SessionTemplateModel]:
        """Search templates by tags (matches any of the provided tags)."""
        # Use && (overlap) operator to check if any tag from input exists in template's tags
        # The overlap operator returns true if the arrays have at least one common element
        conditions = [
            SessionTemplateModel.tags.bool_op("&&")(tags),
            SessionTemplateModel.deleted_at.is_(None)
        ]

        if user_id:
            conditions.append(
                or_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.is_public == True,
                    SessionTemplateModel.is_organization_shared == True,
                )
            )

        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(and_(*conditions))
            .order_by(SessionTemplateModel.usage_count.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: UUID) -> int:
        """Count templates owned by a user."""
        result = await self.db.execute(
            select(func.count()).select_from(SessionTemplateModel).where(
                and_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_most_used(
        self,
        limit: int = 10,
        user_id: Optional[UUID] = None,
    ) -> List[SessionTemplateModel]:
        """Get most used templates (globally or for a specific user)."""
        conditions = [SessionTemplateModel.deleted_at.is_(None)]

        if user_id:
            conditions.append(
                or_(
                    SessionTemplateModel.user_id == user_id,
                    SessionTemplateModel.is_public == True,
                    SessionTemplateModel.is_organization_shared == True,
                )
            )

        result = await self.db.execute(
            select(SessionTemplateModel)
            .where(and_(*conditions))
            .order_by(SessionTemplateModel.usage_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_usage_stats(self, template_id: UUID) -> None:
        """Increment usage count and update last_used_at."""
        from datetime import datetime
        template = await self.db.get(SessionTemplateModel, template_id)
        if template:
            template.usage_count += 1
            template.last_used_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(template)

    async def soft_delete(self, template_id: UUID) -> bool:
        """Soft delete a template."""
        from datetime import datetime
        template = await self.db.get(SessionTemplateModel, template_id)
        if template and template.deleted_at is None:
            template.deleted_at = datetime.utcnow()
            await self.db.commit()
            return True
        return False
