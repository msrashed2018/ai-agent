"""
Sessions API endpoints.
"""

import asyncio
import tarfile
import tempfile
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Response,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_active_user,
    get_db_session,
    get_metrics_collector,
)
from app.domain.entities import User
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.services.sdk_session_service import SDKIntegratedSessionService
from app.schemas.session import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse,
    SessionQueryRequest,
    SessionQueryResponse,
    SessionResumeRequest,
    MessageResponse,
    ToolCallResponse,
    SessionForkRequest,
    SessionArchiveRequest,
    HookExecutionResponse,
    PermissionDecisionResponse,
    ArchiveMetadataResponse,
    MetricsSnapshotResponse,
)
from app.schemas.common import PaginationParams, PaginatedResponse, Links
from app.schemas.mappers import session_to_response


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Create a new interactive session.

    Creates a Claude Code session with specified configuration.
    The session will be initialized but not started until the first message is sent.

    If template_id is provided, the session will be created using the template's
    configuration as defaults, which can be overridden by request parameters.
    """
    # Initialize all required dependencies
    from app.repositories.session_repository import SessionRepository
    from app.repositories.message_repository import MessageRepository
    from app.repositories.tool_call_repository import ToolCallRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.mcp_server_repository import MCPServerRepository
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService
    from app.claude_sdk import ClaudeSDKClientManager, PermissionService
    from app.domain.entities import SessionMode
    
    session_repo = SessionRepository(db)
    message_repo = MessageRepository(db)
    tool_call_repo = ToolCallRepository(db)
    user_repo = UserRepository(db)
    mcp_server_repo = MCPServerRepository(db)
    storage_manager = StorageManager()
    audit_service = AuditService(db)
    sdk_client_manager = ClaudeSDKClientManager()
    permission_service = PermissionService(
        db=db,
        user_repo=user_repo,
        session_repo=session_repo,
        mcp_server_repo=mcp_server_repo,
        audit_service=audit_service,
    )
    
    service = SDKIntegratedSessionService(
        db=db,
        session_repo=session_repo,
        message_repo=message_repo,
        tool_call_repo=tool_call_repo,
        user_repo=user_repo,
        mcp_server_repo=mcp_server_repo,
        storage_manager=storage_manager,
        audit_service=audit_service,
        sdk_client_manager=sdk_client_manager,
        permission_service=permission_service,
    )

    # If template_id is provided, load template configuration first
    session_config = {}
    if request.template_id:
        from app.repositories.session_template_repository import SessionTemplateRepository
        from app.services.session_template_service import SessionTemplateService

        template_service = SessionTemplateService(
            db=db,
            template_repo=SessionTemplateRepository(db),
            user_repo=user_repo,
            mcp_server_repo=mcp_server_repo,
            audit_service=audit_service,
        )

        try:
            # Get template and increment usage
            template = await template_service.get_template(request.template_id, current_user.id)
            await template_service.increment_usage(request.template_id, current_user.id)

            # Use template configuration as base
            template_config = template.clone_configuration()
            session_config = {
                "name": request.name or f"Session from {template.name}",
                "description": request.description or template.description,
                "working_directory": request.working_directory or template_config.get("working_directory"),
                "allowed_tools": request.allowed_tools or template_config.get("allowed_tools"),
                "system_prompt": request.system_prompt or template_config.get("system_prompt"),
                "sdk_options": {**template_config.get("sdk_options", {}), **(request.sdk_options or {})},
                "metadata": {
                    **(request.metadata or {}),
                    "created_from_template_id": str(template.id),
                    "template_name": template.name,
                },
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create session from template: {str(e)}",
            )
    else:
        # Use request parameters directly
        session_config = {
            "name": request.name,
            "description": request.description,
            "working_directory": request.working_directory,
            "allowed_tools": request.allowed_tools,
            "system_prompt": request.system_prompt,
            "sdk_options": request.sdk_options or {},
            "metadata": request.metadata or {},
        }

    # Build SDK options from request
    # Extract relevant SDK options from config
    sdk_opts = session_config.get("sdk_options", {})
    
    # Create SDKOptions with proper fields (matching the dataclass definition)
    from app.domain.value_objects.sdk_options import SDKOptions
    sdk_options_obj = SDKOptions(
        model=sdk_opts.get("model", "claude-3-5-sonnet-20241022"),
        max_turns=sdk_opts.get("max_turns", 20),
        permission_mode=sdk_opts.get("permission_mode", "default"),
        allowed_tools=session_config.get("allowed_tools") or ["*"],
        disallowed_tools=sdk_opts.get("disallowed_tools"),
        cwd=session_config.get("working_directory"),
        mcp_servers=sdk_opts.get("mcp_servers"),
        custom_config={
            k: v for k, v in sdk_opts.items() 
            if k not in ["model", "max_turns", "permission_mode", "allowed_tools", 
                        "disallowed_tools", "cwd", "mcp_servers"]
        } if sdk_opts else None,
    )
    
    # Add system_prompt to the dict separately if provided
    sdk_options_dict = sdk_options_obj.to_dict()
    if session_config.get("system_prompt"):
        sdk_options_dict["system_prompt"] = session_config.get("system_prompt")
    
    # Create session (always interactive mode for now)
    session = await service.create_session(
        user_id=current_user.id,
        mode=SessionMode.INTERACTIVE,
        sdk_options=sdk_options_dict,
        name=session_config.get("name") or "Untitled Session",
    )

    # Convert Session entity to SessionResponse
    # Extract fields from sdk_options for response
    response = SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        description=None,  # Session entity doesn't have description field
        status=session.status.value,
        working_directory=session.working_directory_path or "",
        allowed_tools=sdk_options_dict.get("allowed_tools", []),
        system_prompt=sdk_options_dict.get("system_prompt"),
        sdk_options=sdk_options_dict,
        parent_session_id=session.parent_session_id,
        is_fork=session.is_fork,
        message_count=session.total_messages,
        tool_call_count=session.total_tool_calls,
        total_cost_usd=session.total_cost_usd,
        total_input_tokens=session.api_input_tokens,
        total_output_tokens=session.api_output_tokens,
        created_at=session.created_at,
        updated_at=session.updated_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
        error_message=session.error_message,
        metadata=session_config.get("metadata", {}),
    )
    
    # Add HATEOAS links
    response._links = Links(
        self=f"/api/v1/sessions/{session.id}",
        query=f"/api/v1/sessions/{session.id}/query",
        messages=f"/api/v1/sessions/{session.id}/messages",
        tool_calls=f"/api/v1/sessions/{session.id}/tool-calls",
        stream=f"/api/v1/sessions/{session.id}/stream",
    )

    return response


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Get session details by ID.
    
    Returns full session information including statistics and metadata.
    """
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Build HATEOAS links
    response = session_to_response(session)
    response._links = Links(
        self=f"/api/v1/sessions/{session.id}",
        query=f"/api/v1/sessions/{session.id}/query",
        messages=f"/api/v1/sessions/{session.id}/messages",
        tool_calls=f"/api/v1/sessions/{session.id}/tool-calls",
        stream=f"/api/v1/sessions/{session.id}/stream",
    )
    
    return response


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    is_fork: Optional[bool] = Query(None, description="Filter by fork status"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionListResponse:
    """
    List user's sessions with pagination and filtering.
    
    Returns paginated list of sessions owned by the authenticated user.
    """
    repo = SessionRepository(db)
    
    # Get sessions
    sessions = await repo.get_by_user(
        user_id=current_user.id,
        skip=pagination.offset,
        limit=pagination.limit,
    )
    
    # Apply filters
    if status_filter:
        sessions = [s for s in sessions if s.status == status_filter]
    if is_fork is not None:
        sessions = [s for s in sessions if s.is_fork == is_fork]
    
    # Get total count (this should be a separate query in production)
    total = len(sessions)
    
    # Convert to response models
    items = []
    for session in sessions:
        response = session_to_response(session)
        response._links = Links(
            self=f"/api/v1/sessions/{session.id}",
            query=f"/api/v1/sessions/{session.id}/query",
        )
        items.append(response)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/{session_id}/query", response_model=SessionQueryResponse)
async def send_message(
    session_id: UUID,
    request: SessionQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionQueryResponse:
    """
    Send a message to the session.
    
    Sends a user message to Claude Code and processes the response.
    Optionally forks the session before sending the message.
    """
    # Initialize all required dependencies
    from app.repositories.message_repository import MessageRepository
    from app.repositories.tool_call_repository import ToolCallRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.mcp_server_repository import MCPServerRepository
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService
    from app.claude_sdk import ClaudeSDKClientManager, PermissionService
    
    session_repo = SessionRepository(db)
    message_repo = MessageRepository(db)
    tool_call_repo = ToolCallRepository(db)
    user_repo = UserRepository(db)
    mcp_server_repo = MCPServerRepository(db)
    storage_manager = StorageManager()
    audit_service = AuditService(db)
    sdk_client_manager = ClaudeSDKClientManager()
    permission_service = PermissionService(
        db=db,
        user_repo=user_repo,
        session_repo=session_repo,
        mcp_server_repo=mcp_server_repo,
        audit_service=audit_service,
    )
    
    service = SDKIntegratedSessionService(
        db=db,
        session_repo=session_repo,
        message_repo=message_repo,
        tool_call_repo=tool_call_repo,
        user_repo=user_repo,
        mcp_server_repo=mcp_server_repo,
        storage_manager=storage_manager,
        audit_service=audit_service,
        sdk_client_manager=sdk_client_manager,
        permission_service=permission_service,
    )
    
    # Get session
    repo = session_repo
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Fork if requested
    if request.fork:
        session = await service.fork_session(str(session_id), current_user.id)
    
    # Send message and collect responses
    last_message = None
    async for message in service.send_message(
        session_id=UUID(str(session.id)),
        user_id=current_user.id,
        message_text=request.message,
    ):
        last_message = message
        # Message is already persisted by the service
    
    # Refresh session to get updated status
    session = await repo.get_by_id(str(session.id))
    
    # Build response
    response = SessionQueryResponse(
        id=session.id,
        status=session.status if isinstance(session.status, str) else session.status.value,
        parent_session_id=session.parent_session_id,
        is_fork=session.is_fork,
        message_id=last_message.id if last_message else None,
    )
    response._links = Links(
        self=f"/api/v1/sessions/{session.id}",
        message=f"/api/v1/sessions/{session.id}/messages/{message.id}",
        stream=f"/api/v1/sessions/{session.id}/stream",
    )
    
    return response


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    before_id: Optional[UUID] = Query(None, description="Return messages before this ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[MessageResponse]:
    """
    List messages in a session.
    
    Returns messages in reverse chronological order (newest first).
    """
    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Get messages
    message_repo = MessageRepository(db)
    messages = await message_repo.list_by_session(
        session_id=str(session_id),
        limit=limit,
    )
    
    # Convert to response models
    return [MessageResponse.model_validate(msg) for msg in messages]


@router.get("/{session_id}/tool-calls", response_model=List[ToolCallResponse])
async def list_tool_calls(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of tool calls to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[ToolCallResponse]:
    """
    List tool calls in a session.
    
    Returns tool calls in reverse chronological order (newest first).
    """
    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Get tool calls
    tool_call_repo = ToolCallRepository(db)
    tool_calls = await tool_call_repo.list_by_session(
        session_id=str(session_id),
        limit=limit,
    )
    
    # Convert to response models
    return [ToolCallResponse.model_validate(tc) for tc in tool_calls]


@router.post("/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: UUID,
    request: SessionResumeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Resume a paused or completed session.
    
    Reactivates the session for continued interaction.
    Optionally forks the session before resuming.
    """
    service = SDKIntegratedSessionService(db)
    
    # Get session
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Fork if requested
    if request.fork:
        session = await service.fork_session(str(session_id))
    else:
        # Resume existing session
        if session.status == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session is already active",
            )
        
        session = await service.resume_session(str(session_id))
    
    # Build HATEOAS links
    response = session_to_response(session)
    response._links = Links(
        self=f"/api/v1/sessions/{session.id}",
        query=f"/api/v1/sessions/{session.id}/query",
        messages=f"/api/v1/sessions/{session.id}/messages",
    )
    
    return response


@router.post("/{session_id}/pause", response_model=SessionResponse)
async def pause_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Pause an active session.
    
    Temporarily halts session activity without terminating it.
    """
    service = SDKIntegratedSessionService(db)
    
    # Get session
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Pause session
    session = await service.pause_session(str(session_id))
    
    # Build HATEOAS links
    response = session_to_response(session)
    response._links = Links(
        self=f"/api/v1/sessions/{session.id}",
        resume=f"/api/v1/sessions/{session.id}/resume",
    )
    
    return response


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Terminate a session and clean up resources.
    
    Permanently ends the session and disconnects the SDK client.
    """
    service = SDKIntegratedSessionService(db)
    
    # Get session
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Terminate session
    await service.terminate_session(str(session_id))


@router.get("/{session_id}/workdir/download")
async def download_working_directory(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """
    Download session working directory as tar.gz archive.
    
    Creates a compressed archive of the session's working directory.
    """
    # Get session
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # Check ownership
    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )
    
    # Check if working directory exists
    workdir_path = Path(session.working_directory)
    if not workdir_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Working directory not found",
        )
    
    # Create tar.gz archive in temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
    
    try:
        with tarfile.open(temp_file.name, "w:gz") as tar:
            tar.add(workdir_path, arcname=workdir_path.name)
        
        # Create streaming response
        def iterfile():
            with open(temp_file.name, "rb") as f:
                yield from f
        
        filename = f"{session_id}-workdir.tar.gz"
        
        return StreamingResponse(
            iterfile(),
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
    finally:
        # Schedule cleanup (file will be deleted after streaming completes)
        asyncio.create_task(_cleanup_temp_file(temp_file.name))


async def _cleanup_temp_file(filepath: str) -> None:
    """Clean up temporary file after a delay."""
    await asyncio.sleep(10)  # Wait for download to complete
    try:
        Path(filepath).unlink()
    except Exception:
        pass  # Ignore cleanup errors


# Phase 4: Advanced Session Endpoints

@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session_endpoint(
    session_id: UUID,
    request: SessionForkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Fork an existing session.

    Creates a new session based on an existing session's configuration and optionally
    its working directory contents. The forked session can continue from a specific
    message in the conversation history.
    """
    from app.schemas.session import SessionForkRequest
    from app.services.session_service import SessionService
    from app.repositories.user_repository import UserRepository
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService

    session_repo = SessionRepository(db)
    message_repo = MessageRepository(db)
    tool_call_repo = ToolCallRepository(db)
    user_repo = UserRepository(db)
    storage_manager = StorageManager()
    audit_service = AuditService(db)

    service = SessionService(
        db=db,
        session_repo=session_repo,
        message_repo=message_repo,
        tool_call_repo=tool_call_repo,
        user_repo=user_repo,
        storage_manager=storage_manager,
        audit_service=audit_service,
    )

    # Fork session
    forked_session = await service.fork_session_advanced(
        parent_session_id=session_id,
        user_id=current_user.id,
        fork_at_message=request.fork_at_message,
        name=request.name,
    )

    # Convert to response
    from app.schemas.mappers import session_to_response
    response = session_to_response(forked_session)
    response._links = Links(
        self=f"/api/v1/sessions/{forked_session.id}",
        parent=f"/api/v1/sessions/{session_id}",
        query=f"/api/v1/sessions/{forked_session.id}/query",
    )

    return response


@router.post("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def archive_session_endpoint(
    session_id: UUID,
    request: SessionArchiveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """
    Archive session's working directory.

    Creates a compressed archive of the session's working directory and uploads it
    to configured storage (S3 or filesystem). The archive includes all files created
    during the session.
    """
    from app.schemas.session import SessionArchiveRequest, ArchiveMetadataResponse
    from app.services.session_service import SessionService
    from app.repositories.user_repository import UserRepository
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService

    session_repo = SessionRepository(db)
    message_repo = MessageRepository(db)
    tool_call_repo = ToolCallRepository(db)
    user_repo = UserRepository(db)
    storage_manager = StorageManager()
    audit_service = AuditService(db)

    service = SessionService(
        db=db,
        session_repo=session_repo,
        message_repo=message_repo,
        tool_call_repo=tool_call_repo,
        user_repo=user_repo,
        storage_manager=storage_manager,
        audit_service=audit_service,
    )

    # Archive session
    archive_metadata = await service.archive_session_to_storage(
        session_id=session_id,
        user_id=current_user.id,
        upload_to_s3=request.upload_to_s3,
    )

    # Convert to response
    return ArchiveMetadataResponse(
        id=archive_metadata.id,
        session_id=archive_metadata.session_id,
        archive_path=archive_metadata.archive_path,
        size_bytes=archive_metadata.size_bytes,
        compression=archive_metadata.compression,
        manifest=archive_metadata.manifest,
        status=archive_metadata.status.value,
        error_message=archive_metadata.error_message,
        archived_at=archive_metadata.archived_at,
        created_at=archive_metadata.created_at,
        updated_at=archive_metadata.updated_at,
    )


@router.get("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def get_session_archive(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """
    Get archive metadata for a session.

    Returns information about the session's archived working directory,
    including size, location, and manifest of archived files.
    """
    from app.schemas.session import ArchiveMetadataResponse
    from app.repositories.working_directory_archive_repository import (
        WorkingDirectoryArchiveRepository
    )

    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Get archive metadata
    archive_repo = WorkingDirectoryArchiveRepository(db)
    archives = await archive_repo.get_by_session(str(session_id))

    if not archives:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive found for session {session_id}",
        )

    archive = archives[0]  # Get most recent
    return ArchiveMetadataResponse.model_validate(archive)


@router.get("/{session_id}/hooks", response_model=List[HookExecutionResponse])
async def get_session_hooks(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of hook executions to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[HookExecutionResponse]:
    """
    Get hook execution history for a session.

    Returns a list of all hook executions that occurred during the session,
    including hook type, input/output data, and execution results.
    """
    from app.schemas.session import HookExecutionResponse
    from app.repositories.hook_execution_repository import HookExecutionRepository

    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Get hook executions
    hook_repo = HookExecutionRepository(db)
    hooks = await hook_repo.get_by_session(str(session_id), limit=limit)

    return [HookExecutionResponse.model_validate(hook) for hook in hooks]


@router.get("/{session_id}/permissions", response_model=List[PermissionDecisionResponse])
async def get_session_permissions(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of permission decisions to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[PermissionDecisionResponse]:
    """
    Get permission decision history for a session.

    Returns a list of all permission decisions made during the session,
    including tool names, decisions (allow/deny), and reasons.
    """
    from app.schemas.session import PermissionDecisionResponse
    from app.repositories.permission_decision_repository import PermissionDecisionRepository

    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Get permission decisions
    perm_repo = PermissionDecisionRepository(db)
    decisions = await perm_repo.get_by_session(str(session_id), limit=limit)

    return [PermissionDecisionResponse.model_validate(decision) for decision in decisions]


@router.get("/{session_id}/metrics/snapshots", response_model=List[MetricsSnapshotResponse])
async def get_session_metrics_snapshots(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of snapshots to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[MetricsSnapshotResponse]:
    """
    Get historical metrics snapshots for a session.

    Returns time-series data of session metrics including costs, token usage,
    and performance statistics captured at different points during execution.
    """
    from app.schemas.session import MetricsSnapshotResponse
    from app.repositories.session_metrics_snapshot_repository import (
        SessionMetricsSnapshotRepository
    )

    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Get metrics snapshots
    metrics_repo = SessionMetricsSnapshotRepository(db)
    snapshots = await metrics_repo.get_by_session(str(session_id), limit=limit)

    return [MetricsSnapshotResponse.model_validate(snapshot) for snapshot in snapshots]


@router.get("/{session_id}/metrics/current")
async def get_current_metrics(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    metrics_collector = Depends(get_metrics_collector),
):
    """
    Get current session metrics.

    Returns real-time metrics for the session including costs, token usage,
    message counts, and tool call statistics.
    """
    from app.api.dependencies import get_metrics_collector

    # Check session ownership
    repo = SessionRepository(db)
    session = await repo.get_by_id(str(session_id))

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session",
        )

    # Get current metrics
    metrics = await metrics_collector.get_session_metrics(session_id)

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics not found for session",
        )

    return metrics
