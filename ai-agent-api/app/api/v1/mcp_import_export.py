"""
Additional MCP endpoints for Claude Desktop compatibility.

Import/export and template endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import Dict, Any, List

from app.api.dependencies import get_current_active_user, get_db_session
from app.domain.entities import User
from app.repositories.mcp_server_repository import MCPServerRepository
from app.mcp import MCPConfigManager, MCPConfigBuilder


router = APIRouter(prefix="/mcp-servers", tags=["mcp-servers"])


@router.post("/import")
async def import_claude_desktop_config(
    file: UploadFile = File(...),
    override_existing: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
    """
    Export user's MCP servers to Claude Desktop config format.
    
    Returns config compatible with Claude Desktop, Cursor, etc.
    """
    repo = MCPServerRepository(db)
    manager = MCPConfigManager(repo)
    
    config = await manager.export_claude_desktop_config(
        user_id=current_user.id,
        include_global=include_global
    )
    
    return config


@router.get("/templates")
async def get_mcp_server_templates(
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Get pre-configured templates for popular MCP servers.
    
    Returns list of templates with configuration examples.
    """
    repo = MCPServerRepository(db)
    manager = MCPConfigManager(repo)
    
    templates = await manager.get_server_templates()
    
    return {
        "templates": templates,
        "total": len(templates)
    }
