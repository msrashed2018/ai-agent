"""Task template service for business logic."""
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.task_template import TaskTemplate
from app.domain.entities.task import Task
from app.domain.exceptions import TaskNotFoundError, ValidationError
from app.repositories.task_template_repository import TaskTemplateRepository
from app.repositories.task_repository import TaskRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskTemplateService:
    """Business logic for task template management."""

    def __init__(
        self,
        db: AsyncSession,
        template_repo: TaskTemplateRepository,
        task_repo: TaskRepository,
    ):
        self.db = db
        self.template_repo = template_repo
        self.task_repo = task_repo

    async def create_template(
        self,
        name: str,
        prompt_template: str,
        allowed_tools: list[str],
        sdk_options: dict,
        description: Optional[str] = None,
        category: Optional[str] = None,
        template_variables_schema: Optional[dict] = None,
        disallowed_tools: Optional[list[str]] = None,
        generate_report: bool = False,
        report_format: Optional[str] = None,
        tags: Optional[list[str]] = None,
        icon: Optional[str] = None,
    ) -> TaskTemplate:
        """Create a new task template."""
        logger.info(
            "Creating new task template",
            extra={
                "template_name": name,
                "category": category,
                "generate_report": generate_report,
            }
        )

        # Check if template with same name already exists
        existing = await self.template_repo.get_by_name(name)
        if existing:
            raise ValidationError(f"Template with name '{name}' already exists")

        # Create template entity
        template = TaskTemplate(
            id=uuid4(),
            name=name,
            prompt_template=prompt_template,
            allowed_tools=allowed_tools or [],
            sdk_options=sdk_options or {},
        )
        template.description = description
        template.category = category
        template.template_variables_schema = template_variables_schema
        template.disallowed_tools = disallowed_tools or []
        template.generate_report = generate_report
        template.report_format = report_format
        template.tags = tags or []
        template.icon = icon

        # Save to database
        template = await self.template_repo.create(template)
        await self.db.commit()

        logger.info(
            "Task template created successfully",
            extra={"template_id": str(template.id), "template_name": template.name}
        )

        return template

    async def get_template(self, template_id: UUID) -> TaskTemplate:
        """Get template by ID."""
        template = await self.template_repo.get_by_id(template_id)
        if not template:
            raise TaskNotFoundError(f"Template {template_id} not found")
        return template

    async def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[List[TaskTemplate], int]:
        """List templates with filters and pagination."""
        skip = (page - 1) * page_size
        templates, total = await self.template_repo.list_all(
            category=category,
            tags=tags,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )
        return templates, total

    async def update_template(
        self,
        template_id: UUID,
        **kwargs,
    ) -> TaskTemplate:
        """Update template fields."""
        # Get existing template
        template = await self.get_template(template_id)

        # Update fields
        updated = await self.template_repo.update(template_id, **kwargs)
        if not updated:
            raise TaskNotFoundError(f"Template {template_id} not found")

        await self.db.commit()

        logger.info(
            "Task template updated",
            extra={"template_id": str(template_id), "updated_fields": list(kwargs.keys())}
        )

        return updated

    async def delete_template(self, template_id: UUID) -> None:
        """Delete a template."""
        template = await self.get_template(template_id)

        success = await self.template_repo.delete(template_id)
        if not success:
            raise TaskNotFoundError(f"Template {template_id} not found")

        await self.db.commit()

        logger.info(
            "Task template deleted",
            extra={"template_id": str(template_id)}
        )

    async def create_task_from_template(
        self,
        template_id: UUID,
        user_id: UUID,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None,
        additional_tags: Optional[List[str]] = None,
        is_scheduled: bool = False,
        schedule_cron: Optional[str] = None,
        schedule_enabled: bool = False,
    ) -> Task:
        """Create a task from a template."""
        # Get template
        template = await self.get_template(template_id)

        logger.info(
            "Creating task from template",
            extra={
                "template_id": str(template_id),
                "template_name": template.name,
                "user_id": str(user_id),
            }
        )

        # Create task entity from template
        task = Task(
            id=uuid4(),
            user_id=user_id,
            name=custom_name or template.name,
            prompt_template=template.prompt_template,
            allowed_tools=template.allowed_tools.copy(),
            sdk_options=template.sdk_options.copy(),
        )
        task.description = custom_description or template.description
        task.disallowed_tools = template.disallowed_tools.copy()
        task.generate_report = template.generate_report
        task.report_format = template.report_format

        # Combine tags: template tags + additional tags + "from-template"
        task.tags = template.tags.copy()
        if additional_tags:
            task.tags.extend(additional_tags)
        if "from-template" not in task.tags:
            task.tags.append("from-template")

        # Set scheduling if provided
        task.is_scheduled = is_scheduled
        task.schedule_cron = schedule_cron
        task.schedule_enabled = schedule_enabled

        # Validate if scheduled
        if is_scheduled:
            task.validate_schedule()

        # Save task
        task = await self.task_repo.create(task)

        # Increment template usage count
        await self.template_repo.increment_usage(template_id)

        await self.db.commit()

        logger.info(
            "Task created from template successfully",
            extra={
                "task_id": str(task.id),
                "template_id": str(template_id),
                "task_name": task.name,
            }
        )

        return task

    async def get_most_used_templates(self, limit: int = 10) -> List[TaskTemplate]:
        """Get most used templates."""
        return await self.template_repo.get_most_used(limit)

    async def get_templates_by_category(self, category: str) -> List[TaskTemplate]:
        """Get templates by category."""
        return await self.template_repo.get_by_category(category)

    async def get_template_stats(self) -> dict:
        """Get template statistics."""
        # Get category stats
        categories = await self.template_repo.get_categories_stats()

        # Get total and active counts
        all_templates, total = await self.template_repo.list_all(is_active=None, limit=1000)
        active_count = sum(1 for t in all_templates if t.is_active)

        # Get most used
        most_used = await self.get_most_used_templates(limit=5)

        return {
            "total_templates": total,
            "active_templates": active_count,
            "categories": categories,
            "most_used": most_used,
        }
