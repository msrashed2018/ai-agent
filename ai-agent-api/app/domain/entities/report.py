"""Report domain entity."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ReportType:
    """Report type constants."""
    AUTO_GENERATED = "auto_generated"
    CUSTOM = "custom"
    TEMPLATE = "template"


class ReportFormat:
    """Report format constants."""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class Report:
    """Report aggregate root."""

    def __init__(
        self,
        id: UUID,
        session_id: UUID,
        user_id: UUID,
        title: str,
        content: dict,
    ):
        self.id = id
        self.session_id = session_id
        self.user_id = user_id
        self.title = title
        self.description: Optional[str] = None
        self.content = content

        # Report Type
        self.report_type = ReportType.AUTO_GENERATED
        self.template_name: Optional[str] = None

        # File Outputs
        self.file_path: Optional[str] = None
        self.file_format: Optional[str] = None
        self.file_size_bytes: Optional[int] = None

        # Metadata
        self.tags: List[str] = []
        self.is_public = False
        self.is_deleted = False

        # References
        self.task_execution_id: Optional[UUID] = None

        # Timestamps
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deleted_at: Optional[datetime] = None

    def set_file_output(self, file_path: str, file_format: str, file_size_bytes: int) -> None:
        """Set file output information."""
        self.file_path = file_path
        self.file_format = file_format
        self.file_size_bytes = file_size_bytes
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the report."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the report."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete the report."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def make_public(self) -> None:
        """Make report publicly accessible."""
        self.is_public = True
        self.updated_at = datetime.utcnow()

    def make_private(self) -> None:
        """Make report private."""
        self.is_public = False
        self.updated_at = datetime.utcnow()
