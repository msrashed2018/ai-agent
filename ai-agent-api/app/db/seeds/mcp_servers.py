"""Seed MCP servers."""

import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.mcp_server import MCPServerModel

logger = logging.getLogger(__name__)


# Default MCP server configurations for development
DEFAULT_MCP_SERVERS = [
    {
        "name": "Filesystem Tools",
        "description": "MCP server for filesystem operations (read, write, list directories)",
        "server_type": "stdio",
        "is_enabled": True,
        "is_global": False,
        "config": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-filesystem", "${HOME}"],
            "env": {},
            "category": "filesystem",
            "capabilities": ["read_files", "write_files", "list_directories"],
            "supported_os": ["linux", "macos", "windows"],
        }
    },
    {
        "name": "Git Repository Tools",
        "description": "MCP server for Git operations (clone, commit, push, pull)",
        "server_type": "stdio",
        "is_enabled": True,
        "is_global": False,
        "config": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-git"],
            "env": {},
            "category": "version_control",
            "capabilities": ["clone_repo", "commit", "push", "pull", "branch"],
            "supported_os": ["linux", "macos", "windows"],
        }
    },
    {
        "name": "Web Fetch Tools",
        "description": "MCP server for fetching and processing web content",
        "server_type": "stdio",
        "is_enabled": True,
        "is_global": False,
        "config": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-web-fetch"],
            "env": {},
            "category": "web",
            "capabilities": ["fetch_url", "parse_html", "extract_text"],
            "supported_os": ["linux", "macos", "windows"],
        }
    },
    {
        "name": "Database Query Tools",
        "description": "MCP server for database operations (PostgreSQL)",
        "server_type": "stdio",
        "is_enabled": True,
        "is_global": False,
        "config": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-postgres"],
            "env": {
                "DATABASE_URL": "postgresql://aiagent:password@localhost:5432/aiagent_db"
            },
            "category": "database",
            "capabilities": ["query_database", "execute_sql", "list_tables"],
            "supported_os": ["linux", "macos", "windows"],
        }
    },
    {
        "name": "Docker Operations",
        "description": "MCP server for Docker container management",
        "server_type": "stdio",
        "is_enabled": True,
        "is_global": False,
        "config": {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-docker"],
            "env": {},
            "category": "containers",
            "capabilities": ["list_containers", "inspect_container", "build_image"],
            "supported_os": ["linux", "macos"],
        }
    },
]


async def seed_mcp_servers(db: AsyncSession) -> None:
    """Seed default MCP server configurations.

    Creates pre-configured MCP servers that can be used by tasks and sessions.
    These are development-friendly servers that demonstrate common integrations.

    Args:
        db: AsyncSession for database operations
    """
    logger.info("Seeding MCP servers...")

    # Get admin user to assign servers to
    result = await db.execute(
        select(UserModel).where(UserModel.username == "admin")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        logger.warning("  Admin user not found, skipping MCP servers seeding")
        return

    # Check which MCP servers already exist
    for server_data in DEFAULT_MCP_SERVERS:
        result = await db.execute(
            select(MCPServerModel).where(
                MCPServerModel.name == server_data["name"],
                MCPServerModel.user_id == admin_user.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"  MCP server '{server_data['name']}' already exists, skipping")
            continue

        # Create new MCP server configuration
        mcp_server = MCPServerModel(
            id=uuid4(),
            user_id=admin_user.id,
            name=server_data["name"],
            description=server_data["description"],
            server_type=server_data["server_type"],
            config=server_data.get("config", {}),
            is_enabled=server_data.get("is_enabled", True),
            is_global=server_data.get("is_global", False),
        )

        db.add(mcp_server)
        logger.info(f"  ✅ Created MCP server: {server_data['name']}")

    await db.commit()
    logger.info("MCP servers seeded successfully!")
