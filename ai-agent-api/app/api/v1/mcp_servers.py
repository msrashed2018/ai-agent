"""
MCP Servers API endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.domain.entities import User
from app.repositories.mcp_server_repository import MCPServerRepository
from app.services.mcp_server_service import MCPServerService
from app.schemas.mcp import (
    MCPServerCreateRequest,
    MCPServerUpdateRequest,
    MCPServerResponse,
    MCPServerListResponse,
)


router = APIRouter(prefix="/mcp-servers", tags=["mcp-servers"])


@router.get("", response_model=MCPServerListResponse)
async def list_mcp_servers(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPServerListResponse:
    """
    List all available MCP servers for user.
    
    Returns both user's own servers and global servers.
    """
    repo = MCPServerRepository(db)
    
    # Get user's servers and global servers
    user_servers = await repo.list_by_user(str(current_user.id))
    global_servers = await repo.list_enabled()
    
    # Combine and deduplicate
    all_servers = user_servers + [s for s in global_servers if s.is_global]
    
    # Convert to response models
    items = [MCPServerResponse.model_validate(server) for server in all_servers]
    
    return MCPServerListResponse(
        items=items,
        total=len(items),
    )


@router.post("", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def register_mcp_server(
    request: MCPServerCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPServerResponse:
    """
    Register a new MCP server.
    
    Creates a user-specific MCP server configuration.
    """
    # Initialize required dependencies
    repo = MCPServerRepository(db)
    from app.services.audit_service import AuditService
    audit_service = AuditService(db)
    service = MCPServerService(db, repo, audit_service)
    
    # Check if server with same name already exists for user
    existing = await repo.get_by_name_and_user(request.name, str(current_user.id))
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MCP server with name '{request.name}' already exists",
        )
    
    # Create server
    server = await service.create_server(
        user=current_user,
        server_data=request,
    )
    
    return MCPServerResponse.model_validate(server)


@router.get("/templates")
async def get_mcp_server_templates(
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get pre-configured templates for popular MCP servers.
    
    Returns list of templates with configuration examples.
    """
    # Import here to avoid circular imports
    from app.mcp import MCPConfigManager
    
    repo = MCPServerRepository(db)
    manager = MCPConfigManager(repo)
    
    templates = await manager.get_server_templates()
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/import")
async def import_claude_desktop_config(
    file: UploadFile = File(...),
    override_existing: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Import MCP servers from Claude Desktop config file.
    
    Accepts claude_desktop_config.json format:
    ```json
    {
        "mcpServers": {
            "server_name": {
                "command": "npx",
                "args": [...],
                "env": {...}
            }
        }
    }
    ```
    """
    # Import here to avoid circular imports
    from app.mcp import MCPConfigManager
    import json
    
    # Read and parse file
    try:
        content = await file.read()
        config_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Import servers
    repo = MCPServerRepository(db)
    manager = MCPConfigManager(repo)
    
    try:
        result = await manager.import_claude_desktop_config(
            config_data=config_data,
            user_id=current_user.id,
            override_existing=override_existing
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/export")
async def export_claude_desktop_config(
    include_global: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export user's MCP servers to Claude Desktop config format.
    
    Returns config compatible with Claude Desktop, Cursor, etc.
    """
    # Import here to avoid circular imports
    from app.mcp import MCPConfigManager
    
    repo = MCPServerRepository(db)
    manager = MCPConfigManager(repo)
    
    config = await manager.export_claude_desktop_config(
        user_id=current_user.id,
        include_global=include_global
    )
    
    return config


@router.get("/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(
    server_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPServerResponse:
    """
    Get MCP server details by ID.
    """
    repo = MCPServerRepository(db)
    server = await repo.get_by_id(str(server_id))
    
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )
    
    # Check ownership (unless global server)
    if not server.is_global and server.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this server",
        )
    
    return MCPServerResponse.model_validate(server)


@router.patch("/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(
    server_id: UUID,
    request: MCPServerUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPServerResponse:
    """
    Update MCP server configuration.
    """
    # Initialize required dependencies
    repo = MCPServerRepository(db)
    from app.services.audit_service import AuditService
    audit_service = AuditService(db)
    service = MCPServerService(db, repo, audit_service)
    
    # Get server
    server = await repo.get_by_id(str(server_id))
    
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )
    
    # Check ownership
    if server.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this server",
        )
    
    # Update server
    updated_server = await service.update_server(
        user=current_user,
        server_id=server_id,
        update_data=request,
    )
    
    return updated_server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete an MCP server.
    """
    # Initialize required dependencies
    repo = MCPServerRepository(db)
    from app.services.audit_service import AuditService
    audit_service = AuditService(db)
    service = MCPServerService(db, repo, audit_service)
    
    # Get server
    server = await repo.get_by_id(str(server_id))
    
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )
    
    # Check ownership
    if server.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this server",
        )
    
    # Delete server
    await service.delete_server(
        user=current_user,
        server_id=server_id,
    )


@router.post("/{server_id}/health-check", response_model=MCPServerResponse)
async def check_mcp_server_health(
    server_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPServerResponse:
    """
    Perform health check on MCP server.
    
    Tests connectivity and updates health status.
    """
    # Initialize required dependencies
    repo = MCPServerRepository(db)
    from app.services.audit_service import AuditService
    audit_service = AuditService(db)
    service = MCPServerService(db, repo, audit_service)
    
    # Get server
    server = await repo.get_by_id(str(server_id))
    
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server {server_id} not found",
        )
    
    # Check access (can check health of global servers too)
    if not server.is_global and server.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this server",
        )
    
    # Perform health check
    server = await service.check_health(str(server_id))
    
    return MCPServerResponse.model_validate(server)
