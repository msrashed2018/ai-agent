"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.common import (
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionQueryRequest,
    SessionQueryResponse,
    SessionResumeRequest,
    MessageResponse,
    ToolCallResponse,
)
from app.schemas.session_template import (
    SessionTemplateCreateRequest,
    SessionTemplateUpdateRequest,
    SessionTemplateSharingUpdateRequest,
    SessionTemplateResponse,
    SessionTemplateListResponse,
    SessionTemplateSearchRequest,
    CreateSessionFromTemplateRequest,
)
from app.schemas.task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskExecuteRequest,
    TaskExecutionResponse,
)
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
)
from app.schemas.mcp import (
    MCPServerCreateRequest,
    MCPServerUpdateRequest,
    MCPServerResponse,
    MCPServerListResponse,
)
from app.schemas.admin import (
    SystemStatsResponse,
    AdminSessionListResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    # Common
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    # Session
    "SessionCreateRequest",
    "SessionResponse",
    "SessionListResponse",
    "SessionQueryRequest",
    "SessionQueryResponse",
    "SessionResumeRequest",
    "MessageResponse",
    "ToolCallResponse",
    # Session Template
    "SessionTemplateCreateRequest",
    "SessionTemplateUpdateRequest",
    "SessionTemplateSharingUpdateRequest",
    "SessionTemplateResponse",
    "SessionTemplateListResponse",
    "SessionTemplateSearchRequest",
    "CreateSessionFromTemplateRequest",
    # Task
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskResponse",
    "TaskExecuteRequest",
    "TaskExecutionResponse",
    # Report
    "ReportResponse",
    "ReportListResponse",
    # MCP
    "MCPServerCreateRequest",
    "MCPServerUpdateRequest",
    "MCPServerResponse",
    "MCPServerListResponse",
    # Admin
    "SystemStatsResponse",
    "AdminSessionListResponse",
]
