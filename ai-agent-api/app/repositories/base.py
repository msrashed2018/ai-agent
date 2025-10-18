"""Base repository with common CRUD operations."""
from typing import Generic, TypeVar, Type, Optional, List, Any
from uuid import UUID
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """Initialize repository with model class and database session."""
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get record by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None,
    ) -> List[ModelType]:
        """Get all records with optional filters."""
        query = select(self.model)
        
        if filters:
            for filter_condition in filters:
                query = query.where(filter_condition)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        """Hard delete a record by ID."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        """Count records with optional filters."""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for filter_condition in filters:
                query = query.where(filter_condition)
        
        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists(self, id: UUID) -> bool:
        """Check if record exists by ID."""
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one() > 0
