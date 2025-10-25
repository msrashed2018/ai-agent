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
    tool_group_id: Optional[UUID] = Field(None, description="Tool group UUID to use for allowed/disallowed tools")
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
    tool_group_id: Optional[UUID] = Field(None, description="Tool group UUID to use for allowed/disallowed tools")
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
    tool_group_id: Optional[UUID] = Field(None, description="Tool group UUID")
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
    status: str = Field(..., description="Execution status (pending/queued/running/completed/failed/cancelled)")
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


# ===== Tool Call Schemas =====

class ToolCallResponse(BaseModel):
    """Tool call response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(..., description="Tool call UUID")
    session_id: Optional[UUID] = Field(None, description="Session UUID")
    message_id: Optional[UUID] = Field(None, description="Message UUID")
    tool_name: str = Field(..., description="Tool name (e.g., Bash, Read, Write)")
    tool_use_id: str = Field(..., description="Claude SDK tool use ID")
    tool_input: Dict[str, Any] = Field(..., description="Tool input parameters")
    tool_output: Optional[Dict[str, Any]] = Field(None, description="Tool output data")
    status: str = Field(..., description="Tool call status (pending/running/success/error/denied)")
    is_error: bool = Field(False, description="Whether execution resulted in error")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    permission_decision: Optional[str] = Field(None, description="Permission decision (allow/deny/ask)")
    permission_reason: Optional[str] = Field(None, description="Permission decision reason")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class ToolCallListResponse(PaginatedResponse[ToolCallResponse]):
    """Paginated tool call list response."""
    pass


class ExecutionCancelRequest(BaseModel):
    """Cancel execution request."""

    reason: Optional[str] = Field(None, description="Cancellation reason")


class WorkingDirectoryFileInfo(BaseModel):
    """File information in working directory."""

    path: str = Field(..., description="Relative file path")
    size: int = Field(..., description="File size in bytes")
    modified_at: str = Field(..., description="Last modified timestamp (ISO format)")


class WorkingDirectoryManifest(BaseModel):
    """Working directory file manifest."""

    execution_id: UUID = Field(..., description="Execution UUID")
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size in bytes")
    files: List[WorkingDirectoryFileInfo] = Field(..., description="List of files")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class ArchiveResponse(BaseModel):
    """Archive creation response."""

    execution_id: UUID = Field(..., description="Execution UUID")
    archive_path: str = Field(..., description="Archive file path")
    archive_size: int = Field(..., description="Archive size in bytes")
    created_at: datetime = Field(..., description="Archive creation timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


# ===== Enhanced Task Details Schemas =====

class ExecutionSummaryData(BaseModel):
    """Execution statistics summary."""

    total_executions: int = Field(..., description="Total number of executions")
    successful: int = Field(..., description="Number of successful executions")
    failed: int = Field(..., description="Number of failed executions")
    cancelled: int = Field(..., description="Number of cancelled executions")
    avg_duration_seconds: Optional[float] = Field(None, description="Average execution duration")
    success_rate: float = Field(..., description="Success rate (0.0 to 1.0)")
    last_execution: Optional[TaskExecutionResponse] = Field(None, description="Most recent execution")


class MCPToolInfo(BaseModel):
    """MCP server and tools information."""

    server_name: str = Field(..., description="MCP server name")
    tools: List[str] = Field(default_factory=list, description="Available tools from this server")
    enabled: bool = Field(True, description="Whether server is enabled")
    config: Optional[Dict[str, Any]] = Field(None, description="Server configuration")


class WorkingDirectoryInfo(BaseModel):
    """Working directory information."""

    execution_id: UUID = Field(..., description="Execution ID")
    session_id: Optional[UUID] = Field(None, description="Session ID (if applicable)")
    path: str = Field(..., description="Directory path")
    size_bytes: Optional[int] = Field(None, description="Directory size in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_archived: bool = Field(False, description="Whether directory is archived")
    archive_id: Optional[UUID] = Field(None, description="Archive ID if archived")
    links: Optional[Links] = Field(None, alias="_links", description="Related links")


class PermissionPolicyInfo(BaseModel):
    """Permission policy information.

    Note: permission_mode is always set to 'acceptEdits' (auto-approve) for task executions.
    This is system-controlled and not user-configurable to ensure automated tasks run without manual intervention.
    """

    allowed_tools: List[str] = Field(default_factory=list, description="Allowed tool patterns")
    disallowed_tools: List[str] = Field(default_factory=list, description="Disallowed tool patterns")


class AuditSummaryData(BaseModel):
    """Audit trail summary."""

    total_audit_logs: int = Field(..., description="Total audit log entries")
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Recent actions (last 5)")
    links: Optional[Links] = Field(None, alias="_links", description="Audit logs link")


class ReportSummaryData(BaseModel):
    """Reports summary."""

    total: int = Field(..., description="Total number of reports")
    recent: List[Dict[str, Any]] = Field(default_factory=list, description="Recent reports (last 5)")
    links: Optional[Links] = Field(None, alias="_links", description="Reports link")


class TaskDetailedResponse(BaseModel):
    """Detailed task response with all child objects and references."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Core task data
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

    # Enhanced aggregated data
    execution_summary: Optional[ExecutionSummaryData] = Field(None, description="Execution statistics")
    recent_executions: List[TaskExecutionResponse] = Field(default_factory=list, description="Recent executions (last 5)")
    working_directories: Optional[Dict[str, List[WorkingDirectoryInfo]]] = Field(None, description="Working directories (active/archived)")
    mcp_tools: List[MCPToolInfo] = Field(default_factory=list, description="MCP tools available")
    permission_policies: Optional[PermissionPolicyInfo] = Field(None, description="Permission policies")
    audit_summary: Optional[AuditSummaryData] = Field(None, description="Audit trail summary")
    reports_summary: Optional[ReportSummaryData] = Field(None, description="Reports summary")

    # HATEOAS links
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")
