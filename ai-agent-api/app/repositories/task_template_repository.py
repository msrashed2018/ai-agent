"""Task template repository."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_template import TaskTemplateModel
from app.domain.entities.task_template import TaskTemplate


class TaskTemplateRepository:
    """Repository for task template operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _model_to_entity(self, model: TaskTemplateModel) -> TaskTemplate:
        """Convert model to entity."""
        entity = TaskTemplate(
            id=model.id,
            name=model.name,
            prompt_template=model.prompt_template,
            allowed_tools=model.allowed_tools or [],
            sdk_options=model.sdk_options or {},
        )
        entity.description = model.description
        entity.category = model.category
        entity.template_variables_schema = model.template_variables_schema
        entity.disallowed_tools = model.disallowed_tools or []
        entity.generate_report = model.generate_report
        entity.report_format = model.report_format
        entity.tags = model.tags or []
        entity.is_public = model.is_public
        entity.is_active = model.is_active
        entity.icon = model.icon
        entity.usage_count = model.usage_count
        entity.created_at = model.created_at
        entity.updated_at = model.updated_at
        return entity

    async def create(self, template: TaskTemplate) -> TaskTemplate:
        """Create a new template."""
        model = TaskTemplateModel(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            prompt_template=template.prompt_template,
            template_variables_schema=template.template_variables_schema,
            allowed_tools=template.allowed_tools,
            disallowed_tools=template.disallowed_tools,
            sdk_options=template.sdk_options,
            generate_report=template.generate_report,
            report_format=template.report_format,
            tags=template.tags,
            is_public=template.is_public,
            is_active=template.is_active,
            icon=template.icon,
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        self.db.add(model)
        await self.db.flush()
        return self._model_to_entity(model)

    async def get_by_id(self, template_id: UUID) -> Optional[TaskTemplate]:
        """Get template by ID."""
        result = await self.db.execute(
            select(TaskTemplateModel).where(TaskTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Optional[TaskTemplate]:
        """Get template by name."""
        result = await self.db.execute(
            select(TaskTemplateModel).where(TaskTemplateModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def list_all(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[TaskTemplate], int]:
        """List templates with filters."""
        query = select(TaskTemplateModel).where(TaskTemplateModel.is_active == is_active)

        if category:
            query = query.where(TaskTemplateModel.category == category)

        if tags:
            # Filter by tags (contains any of the provided tags)
            query = query.where(TaskTemplateModel.tags.overlap(tags))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(TaskTemplateModel.usage_count.desc(), TaskTemplateModel.name)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models], total

    async def get_most_used(self, limit: int = 10) -> List[TaskTemplate]:
        """Get most used templates."""
        query = (
            select(TaskTemplateModel)
            .where(TaskTemplateModel.is_active == True)
            .order_by(desc(TaskTemplateModel.usage_count))
            .limit(limit)
        )

        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def get_by_category(self, category: str) -> List[TaskTemplate]:
        """Get templates by category."""
        query = (
            select(TaskTemplateModel)
            .where(
                TaskTemplateModel.category == category,
                TaskTemplateModel.is_active == True
            )
            .order_by(TaskTemplateModel.name)
        )

        result = await self.db.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, template_id: UUID, **kwargs) -> Optional[TaskTemplate]:
        """Update template fields."""
        result = await self.db.execute(
            select(TaskTemplateModel).where(TaskTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        for key, value in kwargs.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        await self.db.flush()
        return self._model_to_entity(model)

    async def increment_usage(self, template_id: UUID) -> None:
        """Increment template usage count."""
        result = await self.db.execute(
            select(TaskTemplateModel).where(TaskTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()

        if model:
            model.usage_count += 1
            await self.db.flush()

    async def delete(self, template_id: UUID) -> bool:
        """Delete template (hard delete)."""
        result = await self.db.execute(
            select(TaskTemplateModel).where(TaskTemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.db.delete(model)
        await self.db.flush()
        return True

    async def get_categories_stats(self) -> dict:
        """Get templates count per category."""
        from sqlalchemy import func

        query = (
            select(
                TaskTemplateModel.category,
                func.count(TaskTemplateModel.id).label('count')
            )
            .where(TaskTemplateModel.is_active == True)
            .group_by(TaskTemplateModel.category)
        )

        result = await self.db.execute(query)
        stats = {}
        for row in result:
            if row.category:
                stats[row.category] = row.count

        return stats
