"""Task template domain entity."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TaskTemplate:
    """Template for creating pre-configured tasks."""

    def __init__(
        self,
        id: UUID,
        name: str,
        prompt_template: str,
        allowed_tools: List[str],
        sdk_options: dict,
    ):
        self.id = id
        self.name = name
        self.description: Optional[str] = None
        self.category: Optional[str] = None  # e.g., "kubernetes", "docker", "git", "database"
        self.prompt_template = prompt_template
        self.allowed_tools = allowed_tools
        self.disallowed_tools: List[str] = []
        self.sdk_options = sdk_options

        # Template variables hints/docs
        self.template_variables_schema: Optional[dict] = None  # JSON Schema for variables

        # Post-execution defaults
        self.generate_report = False
        self.report_format: Optional[str] = None

        # Metadata
        self.tags: List[str] = []
        self.is_public = True  # Templates are public by default
        self.is_active = True
        self.icon: Optional[str] = None  # Icon name for UI

        # Usage stats
        self.usage_count = 0

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def create_task_from_template(
        self,
        user_id: UUID,
        task_name: Optional[str] = None,
        custom_variables: Optional[dict] = None,
    ) -> dict:
        """Create task data from this template."""
        from uuid import uuid4

        task_data = {
            "id": uuid4(),
            "user_id": user_id,
            "name": task_name or self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "allowed_tools": self.allowed_tools.copy(),
            "disallowed_tools": self.disallowed_tools.copy(),
            "sdk_options": self.sdk_options.copy(),
            "generate_report": self.generate_report,
            "report_format": self.report_format,
            "tags": self.tags.copy() + ["from-template"],
        }

        return task_data

    def increment_usage(self) -> None:
        """Increment usage count."""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
