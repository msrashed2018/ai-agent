"""
Task-related schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class TaskCreateRequest(BaseModel):
    """Create task request."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    prompt_template: str = Field(..., min_length=1, description="Prompt template with {{variables}}")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="SDK options override")
    is_scheduled: bool = Field(False, description="Whether task is scheduled")
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduling")
    schedule_enabled: bool = Field(False, description="Whether schedule is enabled")
    generate_report: bool = Field(False, description="Generate report after execution")
    report_format: Optional[str] = Field("html", description="Report format (html/pdf/json)")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification configuration")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")


class TaskUpdateRequest(BaseModel):
    """Update task request."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    prompt_template: Optional[str] = Field(None, min_length=1, description="Prompt template")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="SDK options override")
    is_scheduled: Optional[bool] = Field(None, description="Whether task is scheduled")
    schedule_cron: Optional[str] = Field(None, description="Cron expression")
    schedule_enabled: Optional[bool] = Field(None, description="Whether schedule is enabled")
    generate_report: Optional[bool] = Field(None, description="Generate report after execution")
    report_format: Optional[str] = Field(None, description="Report format")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification config")
    tags: Optional[List[str]] = Field(None, description="Task tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")


class TaskResponse(BaseModel):
    """Task response - matches Task entity fields only."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID = Field(..., description="Task UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    prompt_template: str = Field(..., description="Prompt template")
    allowed_tools: List[str] = Field(default_factory=list, description="Allowed tool patterns")
    disallowed_tools: List[str] = Field(default_factory=list, description="Disallowed tool patterns")
    sdk_options: Dict[str, Any] = Field(default_factory=dict, description="SDK options")
    working_directory_path: Optional[str] = Field(None, description="Working directory path")
    is_scheduled: bool = Field(default=False, description="Whether task is scheduled")
    schedule_cron: Optional[str] = Field(None, description="Cron expression")
    schedule_enabled: bool = Field(default=False, description="Whether schedule is enabled")
    generate_report: bool = Field(default=False, description="Generate report after execution")
    report_format: Optional[str] = Field(None, description="Report format")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification config")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    is_public: bool = Field(default=False, description="Is publicly available")
    is_active: bool = Field(default=True, description="Whether task is active")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class TaskExecuteRequest(BaseModel):
    """Execute task request."""
    
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")


class TaskExecutionResponse(BaseModel):
    """Task execution response."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID = Field(..., description="Execution UUID")
    task_id: UUID = Field(..., description="Task UUID")
    session_id: Optional[UUID] = Field(None, description="Session UUID")
    status: str = Field(..., description="Execution status (pending/running/completed/failed)")
    trigger_type: str = Field(..., description="Trigger type (manual/scheduled/api)")
    prompt_variables: Dict[str, Any] = Field(default_factory=dict, description="Used template variables")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    report_id: Optional[UUID] = Field(None, description="Generated report UUID")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Execution duration in milliseconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class TaskListResponse(PaginatedResponse[TaskResponse]):
    """Paginated task list response."""
    pass


class TaskExecutionListResponse(PaginatedResponse[TaskExecutionResponse]):
    """Paginated task execution list response."""
    pass
