"""
Task template schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class TaskTemplateCreateRequest(BaseModel):
    """Create task template request."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category (kubernetes, docker, git, etc.)")
    prompt_template: str = Field(..., min_length=1, description="Prompt template with {{variables}}")
    template_variables_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for template variables")
    tool_group_id: Optional[str] = Field(None, description="Tool group UUID (if set, uses tool group's allowed/disallowed tools)")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns (used if tool_group_id is not set)")
    disallowed_tools: Optional[List[str]] = Field(None, description="Disallowed tool patterns (used if tool_group_id is not set)")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="SDK options")
    generate_report: bool = Field(False, description="Generate report after execution")
    report_format: Optional[str] = Field("html", description="Report format (html/pdf/json/markdown)")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    icon: Optional[str] = Field(None, description="Icon name for UI")
    is_public: Optional[bool] = Field(None, description="Is publicly available")
    is_active: Optional[bool] = Field(None, description="Whether template is active")


class TaskTemplateUpdateRequest(BaseModel):
    """Update task template request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    prompt_template: Optional[str] = Field(None, min_length=1, description="Prompt template")
    template_variables_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for variables")
    tool_group_id: Optional[str] = Field(None, description="Tool group UUID (if set, uses tool group's allowed/disallowed tools)")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns (used if tool_group_id is not set)")
    disallowed_tools: Optional[List[str]] = Field(None, description="Disallowed tool patterns (used if tool_group_id is not set)")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="SDK options")
    generate_report: Optional[bool] = Field(None, description="Generate report after execution")
    report_format: Optional[str] = Field(None, description="Report format")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    icon: Optional[str] = Field(None, description="Icon name for UI")
    is_active: Optional[bool] = Field(None, description="Whether template is active")
    is_public: Optional[bool] = Field(None, description="Is publicly available")


class TaskTemplateResponse(BaseModel):
    """Task template response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(..., description="Template UUID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    prompt_template: str = Field(..., description="Prompt template")
    template_variables_schema: Optional[Dict[str, Any]] = Field(None, description="Variables schema")
    tool_group_id: Optional[UUID] = Field(None, description="Associated tool group UUID")
    allowed_tools: List[str] = Field(default_factory=list, description="Allowed tool patterns (used if tool_group_id not set)")
    disallowed_tools: List[str] = Field(default_factory=list, description="Disallowed tool patterns (used if tool_group_id not set)")
    sdk_options: Dict[str, Any] = Field(default_factory=dict, description="SDK options")
    generate_report: bool = Field(default=False, description="Generate report after execution")
    report_format: Optional[str] = Field(None, description="Report format")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    is_public: bool = Field(default=True, description="Is publicly available")
    is_active: bool = Field(default=True, description="Whether template is active")
    icon: Optional[str] = Field(None, description="Icon name for UI")
    usage_count: int = Field(default=0, description="Number of times used")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    links: Links = Field(default_factory=Links, alias="_links", description="HATEOAS links")


class TaskTemplateListResponse(PaginatedResponse):
    """List of task templates."""

    items: List[TaskTemplateResponse] = Field(..., description="List of templates")


class CreateTaskFromTemplateRequest(BaseModel):
    """Request to create task from template."""

    name: Optional[str] = Field(None, description="Custom task name (defaults to template name)")
    description: Optional[str] = Field(None, description="Custom task description")
    tags: Optional[List[str]] = Field(None, description="Additional tags (template tags + these)")
    is_scheduled: bool = Field(False, description="Whether task should be scheduled")
    schedule_cron: Optional[str] = Field(None, description="Cron expression for scheduling")
    schedule_enabled: bool = Field(False, description="Whether schedule is enabled")


class TaskTemplateStatsResponse(BaseModel):
    """Task template usage statistics."""

    total_templates: int = Field(..., description="Total number of templates")
    active_templates: int = Field(..., description="Number of active templates")
    categories: Dict[str, int] = Field(..., description="Templates per category")
    most_used: List[TaskTemplateResponse] = Field(..., description="Most used templates")
