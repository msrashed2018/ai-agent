"""Domain-wide enumerations."""
from enum import Enum


class ArchiveStatus(str, Enum):
    """Archive status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
