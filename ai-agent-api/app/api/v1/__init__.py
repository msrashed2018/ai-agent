"""
API v1 router initialization.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    # sessions,  # REMOVED: Using tasks API only
    # session_templates,  # REMOVED: Using tasks API only
    tasks,
    task_templates,
    reports,
    mcp_servers,
    mcp_import_export,
    admin,
    websocket,
    monitoring,
    tool_groups,
)


# Create main v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_v1_router.include_router(auth.router)
# api_v1_router.include_router(sessions.router)  # REMOVED: Using tasks API only
# api_v1_router.include_router(session_templates.router)  # REMOVED: Using tasks API only
api_v1_router.include_router(tasks.router)
api_v1_router.include_router(task_templates.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(mcp_servers.router)
api_v1_router.include_router(mcp_import_export.router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(websocket.router)
api_v1_router.include_router(monitoring.router)
api_v1_router.include_router(tool_groups.router)


__all__ = ["api_v1_router"]
