"""
API v1 router initialization.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    sessions,
    session_templates,
    tasks,
    reports,
    mcp_servers,
    mcp_import_export,
    admin,
    websocket,
    monitoring,
)


# Create main v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(sessions.router)
api_v1_router.include_router(session_templates.router)
api_v1_router.include_router(tasks.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(mcp_servers.router)
api_v1_router.include_router(mcp_import_export.router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(websocket.router)
api_v1_router.include_router(monitoring.router)


__all__ = ["api_v1_router"]
