"""
Session-related schemas.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Links, PaginatedResponse


class SessionCreateRequest(BaseModel):
    """Create session request."""

    template_id: Optional[UUID] = Field(None, description="Session template ID to use as base configuration")
    name: Optional[str] = Field(None, max_length=255, description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    working_directory: Optional[str] = Field(None, description="Working directory path")
    allowed_tools: Optional[List[str]] = Field(None, description="Allowed tool patterns (glob)")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    sdk_options: Optional[Dict[str, Any]] = Field(None, description="Claude SDK options override")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata")

    # Phase 4: Session mode
    mode: Optional[str] = Field("interactive", description="Session mode: interactive, background, forked")

    # Phase 4: Parent session (for forking)
    parent_session_id: Optional[UUID] = Field(None, description="Parent session ID (for forking)")
    fork_at_message: Optional[int] = Field(None, description="Fork from message index")

    # Phase 4: Streaming configuration
    include_partial_messages: Optional[bool] = Field(False, description="Enable real-time streaming")

    # Phase 4: Retry configuration
    max_retries: Optional[int] = Field(3, description="Max retry attempts")
    retry_delay: Optional[float] = Field(2.0, description="Retry delay in seconds")
    timeout_seconds: Optional[int] = Field(120, description="Timeout in seconds")

    # Phase 4: Hooks configuration
    hooks_enabled: Optional[List[str]] = Field([], description="Enabled hook types")

    # Phase 4: Permission configuration
    permission_mode: Optional[str] = Field("default", description="Permission mode")
    custom_policies: Optional[List[str]] = Field([], description="Custom policy names")


class SessionResponse(BaseModel):
    """Session response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID = Field(..., description="Session UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    name: Optional[str] = Field(None, description="Session name")
    description: Optional[str] = Field(None, description="Session description")
    status: str = Field(..., description="Session status (active/paused/completed/failed)")
    working_directory: str = Field(..., description="Working directory path")
    allowed_tools: List[str] = Field(..., description="Allowed tool patterns")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    sdk_options: Dict[str, Any] = Field(..., description="Claude SDK options")
    parent_session_id: Optional[UUID] = Field(None, description="Parent session if forked")
    is_fork: bool = Field(..., description="Whether this is a forked session")
    message_count: int = Field(..., description="Total messages in session")
    tool_call_count: int = Field(..., description="Total tool calls in session")
    total_cost_usd: float = Field(..., description="Total API cost in USD")
    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    links: Links = Field(default_factory=Links, description="HATEOAS links", alias="_links")


class SessionListResponse(PaginatedResponse[SessionResponse]):
    """Paginated session list response."""
    pass


class SessionQueryRequest(BaseModel):
    """Query message request."""
    
    message: str = Field(..., min_length=1, max_length=50000, description="User message")
    fork: bool = Field(False, description="Fork session before sending message")


class SessionQueryResponse(BaseModel):
    """Query message response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: UUID = Field(..., description="Session UUID (new if forked)")
    status: str = Field(..., description="Session status")
    parent_session_id: Optional[UUID] = Field(None, description="Parent if forked")
    is_fork: bool = Field(..., description="Whether session was forked")
    message_id: UUID = Field(..., description="Created message UUID")
    links: Links = Field(default_factory=Links, description="HATEOAS links", alias="_links")


class SessionResumeRequest(BaseModel):
    """Resume session request."""
    
    fork: bool = Field(False, description="Fork session before resuming")


class MessageResponse(BaseModel):
    """Message response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(..., description="Message UUID")
    session_id: UUID = Field(..., description="Session UUID")
    message_type: str = Field(..., description="Message type (user/assistant/system/result)")
    content: Dict[str, Any] = Field(..., description="Message content blocks")
    token_count: Optional[int] = Field(None, description="Token count")
    cost_usd: Optional[float] = Field(None, description="Message cost in USD")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class ToolCallResponse(BaseModel):
    """Tool call response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Tool call UUID")
    session_id: UUID = Field(..., description="Session UUID")
    tool_use_message_id: Optional[UUID] = Field(None, description="Message with tool_use block")
    tool_result_message_id: Optional[UUID] = Field(None, description="Message with tool_result block")
    tool_name: str = Field(..., description="Tool name")
    tool_input: Dict[str, Any] = Field(..., description="Tool input parameters")
    tool_output: Optional[Dict[str, Any]] = Field(None, description="Tool output data")
    status: str = Field(..., description="Status (pending/success/error)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(None, description="Execution duration in milliseconds")
    created_at: datetime = Field(..., description="Creation timestamp")


# Phase 4: New schemas for advanced features

class SessionForkRequest(BaseModel):
    """Fork session request."""
    name: Optional[str] = Field(None, description="Name for forked session")
    fork_at_message: Optional[int] = Field(None, description="Fork from message index")
    include_working_directory: bool = Field(True, description="Copy working directory files")


class SessionArchiveRequest(BaseModel):
    """Archive session request."""
    upload_to_s3: bool = Field(True, description="Upload archive to S3")
    compression: str = Field("gzip", description="Compression algorithm")


class HookExecutionResponse(BaseModel):
    """Hook execution response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Hook execution UUID")
    session_id: UUID = Field(..., description="Session UUID")
    hook_type: str = Field(..., description="Hook type")
    hook_name: str = Field(..., description="Hook name")
    tool_use_id: Optional[str] = Field(None, description="Associated tool use ID")
    input_data: Dict[str, Any] = Field(..., description="Hook input data")
    output_data: Dict[str, Any] = Field(..., description="Hook output data")
    continue_execution: bool = Field(..., description="Whether execution should continue")
    executed_at: datetime = Field(..., description="Execution timestamp")
    duration_ms: Optional[int] = Field(None, description="Execution duration")


class PermissionDecisionResponse(BaseModel):
    """Permission decision response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Permission decision UUID")
    session_id: UUID = Field(..., description="Session UUID")
    tool_name: str = Field(..., description="Tool name")
    input_data: Dict[str, Any] = Field(..., description="Tool input data")
    context: Dict[str, Any] = Field(..., description="Permission context")
    decision: str = Field(..., description="Decision (allow/deny)")
    reason: Optional[str] = Field(None, description="Decision reason")
    interrupted: bool = Field(..., description="Whether execution was interrupted")
    decided_at: datetime = Field(..., description="Decision timestamp")


class ArchiveMetadataResponse(BaseModel):
    """Archive metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Archive metadata UUID")
    session_id: UUID = Field(..., description="Session UUID")
    archive_path: str = Field(..., description="Archive file path or S3 URL")
    size_bytes: int = Field(..., description="Archive size in bytes")
    compression: str = Field(..., description="Compression algorithm")
    manifest: Dict[str, Any] = Field(..., description="Archive manifest")
    status: str = Field(..., description="Archive status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MetricsSnapshotResponse(BaseModel):
    """Metrics snapshot response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Snapshot UUID")
    session_id: UUID = Field(..., description="Session UUID")
    total_messages: int = Field(..., description="Total messages")
    total_tool_calls: int = Field(..., description="Total tool calls")
    total_errors: int = Field(..., description="Total errors")
    total_retries: int = Field(..., description="Total retries")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_input_tokens: int = Field(..., description="Total input tokens")
    total_output_tokens: int = Field(..., description="Total output tokens")
    total_cache_creation_tokens: int = Field(..., description="Total cache creation tokens")
    total_cache_read_tokens: int = Field(..., description="Total cache read tokens")
    total_duration_ms: int = Field(..., description="Total duration in milliseconds")
    created_at: datetime = Field(..., description="Snapshot timestamp")
