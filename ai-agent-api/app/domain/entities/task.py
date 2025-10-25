"""Task domain entity."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class Task:
    """Task definition for repeatable agent operations."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        name: str,
        prompt_template: str,
        allowed_tools: List[str],
        sdk_options: dict,
        tool_group_id: Optional[UUID] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.tool_group_id = tool_group_id
        self.name = name
        self.description: Optional[str] = None
        self.prompt_template = prompt_template
        self.allowed_tools = allowed_tools
        self.disallowed_tools: List[str] = []
        self.sdk_options = sdk_options
        self.working_directory_path: Optional[str] = None

        # Scheduling
        self.is_scheduled = False
        self.schedule_cron: Optional[str] = None
        self.schedule_enabled = False

        # Post-execution
        self.generate_report = False
        self.report_format: Optional[str] = None
        self.notification_config: Optional[dict] = None

        # Metadata
        self.tags: List[str] = []
        self.is_public = False
        self.is_active = True
        self.is_deleted = False

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deleted_at: Optional[datetime] = None

    def render_prompt(self, variables: dict) -> str:
        """Render prompt template with variables."""
        from jinja2 import Template
        template = Template(self.prompt_template)
        return template.render(**variables)

    def validate_schedule(self) -> None:
        """Validate cron expression if scheduled."""
        from app.domain.exceptions import ValidationError

        if self.is_scheduled:
            if not self.schedule_cron:
                raise ValidationError("schedule_cron required when is_scheduled=True")

            # Validate cron expression format
            from croniter import croniter
            if not croniter.is_valid(self.schedule_cron):
                raise ValidationError(f"Invalid cron expression: {self.schedule_cron}")

    def validate_report_format(self) -> None:
        """Validate report format if report generation enabled."""
        from app.domain.exceptions import ValidationError

        if self.generate_report:
            valid_formats = ["json", "markdown", "html", "pdf"]
            if not self.report_format or self.report_format not in valid_formats:
                raise ValidationError(
                    f"Invalid report_format: {self.report_format}. Must be one of {valid_formats}"
                )

    def soft_delete(self) -> None:
        """Soft delete the task."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the task."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the task."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
