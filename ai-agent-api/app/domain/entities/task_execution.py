"""Task execution domain entity."""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class TaskExecutionStatus(Enum):
    """Task execution status enumeration."""
    PENDING = "pending"      # Created, not yet queued
    QUEUED = "queued"        # Queued to Celery, waiting for worker
    RUNNING = "running"      # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"        # Failed with error
    CANCELLED = "cancelled"  # Manually cancelled


class TriggerType(Enum):
    """Task execution trigger type enumeration."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    API = "api"


class TaskExecution:
    """Task execution domain entity."""

    def __init__(
        self,
        id: UUID,
        task_id: UUID,
        trigger_type: TriggerType,
        status: TaskExecutionStatus = TaskExecutionStatus.PENDING,
    ):
        self.id = id
        self.task_id = task_id
        self.session_id: Optional[UUID] = None
        self.report_id: Optional[UUID] = None

        # Execution Context
        self.trigger_type = trigger_type
        self.trigger_metadata: Dict[str, Any] = {}

        # Execution Parameters
        self.prompt_variables: Dict[str, Any] = {}

        # Status
        self.status = status
        self.error_message: Optional[str] = None

        # Results
        self.result_data: Dict[str, Any] = {}

        # Metrics
        self.total_messages = 0
        self.total_tool_calls = 0
        self.duration_seconds: Optional[int] = None

        # Celery Integration Fields
        self.celery_task_id: Optional[str] = None  # Celery task ID for async execution
        self.worker_hostname: Optional[str] = None  # Worker that processed the task
        self.retry_count: int = 0  # Number of retry attempts

        # Timestamps
        self.created_at = datetime.utcnow()
        self.queued_at: Optional[datetime] = None  # When queued to Celery
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def queue_execution(self, celery_task_id: str) -> None:
        """Mark execution as queued to Celery.

        Args:
            celery_task_id: Celery task ID for tracking

        Raises:
            ValueError: If execution is not in PENDING status
        """
        if self.status != TaskExecutionStatus.PENDING:
            raise ValueError(f"Cannot queue execution in {self.status.value} status")

        self.status = TaskExecutionStatus.QUEUED
        self.celery_task_id = celery_task_id
        self.queued_at = datetime.utcnow()

    def start_execution(self) -> None:
        """Mark execution as started.

        Can transition from PENDING or QUEUED status.

        Raises:
            ValueError: If execution is not in PENDING or QUEUED status
        """
        if self.status not in [TaskExecutionStatus.PENDING, TaskExecutionStatus.QUEUED]:
            raise ValueError(f"Cannot start execution in {self.status.value} status")

        self.status = TaskExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_execution(self, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as completed."""
        if self.status != TaskExecutionStatus.RUNNING:
            raise ValueError(f"Cannot complete execution in {self.status.value} status")
        
        self.status = TaskExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        if result_data:
            self.result_data = result_data
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed.

        Can fail from any active status (PENDING, QUEUED, RUNNING).

        Args:
            error_message: Error description
        """
        if self.status not in [
            TaskExecutionStatus.PENDING,
            TaskExecutionStatus.QUEUED,
            TaskExecutionStatus.RUNNING
        ]:
            raise ValueError(f"Cannot fail execution in {self.status.value} status")

        self.status = TaskExecutionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

    def cancel_execution(self) -> None:
        """Mark execution as cancelled."""
        if self.status == TaskExecutionStatus.COMPLETED:
            raise ValueError("Cannot cancel completed execution")
        
        self.status = TaskExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

    def update_metrics(self, total_messages: int, total_tool_calls: int) -> None:
        """Update execution metrics."""
        self.total_messages = total_messages
        self.total_tool_calls = total_tool_calls

    def set_session(self, session_id: UUID) -> None:
        """Associate execution with a session."""
        self.session_id = session_id

    def set_report(self, report_id: UUID) -> None:
        """Associate execution with a generated report."""
        self.report_id = report_id

    def set_worker_info(self, worker_hostname: str) -> None:
        """Set worker information for Celery execution.

        Args:
            worker_hostname: Hostname of worker processing the task
        """
        self.worker_hostname = worker_hostname

    def increment_retry_count(self) -> None:
        """Increment retry count for failed execution retry."""
        self.retry_count += 1

    @property
    def is_active(self) -> bool:
        """Check if execution is currently active (not finished)."""
        return self.status in [
            TaskExecutionStatus.PENDING,
            TaskExecutionStatus.QUEUED,
            TaskExecutionStatus.RUNNING
        ]

    @property
    def is_completed(self) -> bool:
        """Check if execution has completed (successfully or not)."""
        return self.status in [
            TaskExecutionStatus.COMPLETED,
            TaskExecutionStatus.FAILED,
            TaskExecutionStatus.CANCELLED
        ]

    @property
    def was_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == TaskExecutionStatus.COMPLETED