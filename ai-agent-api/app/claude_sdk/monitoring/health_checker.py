"""Health checker for monitoring system health."""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.logging import get_logger


logger = get_logger(__name__)


class HealthChecker:
    """Monitor SDK and service health."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_sdk_availability(self) -> bool:
        """Check if Claude SDK CLI is available."""
        try:
            import subprocess
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            is_available = result.returncode == 0
            logger.info(
                f"Claude SDK availability check: {'available' if is_available else 'unavailable'}",
                extra={"is_available": is_available}
            )
            return is_available
        except Exception as e:
            logger.error(f"Claude SDK availability check failed: {e}")
            return False

    async def check_mcp_servers(self) -> Dict[str, bool]:
        """Check health of all MCP servers."""
        # TODO: Implement MCP server health checks
        # This would query the MCP server manager for active servers
        # and ping each one to verify it's responsive
        return {}

    async def check_database(self) -> bool:
        """Check database connectivity."""
        try:
            result = await self.db.execute(text("SELECT 1"))
            is_healthy = result.scalar() == 1
            logger.info(
                f"Database health check: {'healthy' if is_healthy else 'unhealthy'}",
                extra={"is_healthy": is_healthy}
            )
            return is_healthy
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def check_s3_storage(self) -> bool:
        """Check S3 storage availability."""
        from app.core.config import settings

        if settings.storage_provider != "s3":
            return True  # N/A for filesystem storage

        try:
            import boto3
            from botocore.exceptions import ClientError

            s3_client = boto3.client(
                's3',
                region_name=settings.aws_s3_region,
                aws_access_key_id=settings.aws_access_key_id or None,
                aws_secret_access_key=settings.aws_secret_access_key or None
            )

            # Try to list objects in bucket (with max 1 result)
            s3_client.list_objects_v2(Bucket=settings.aws_s3_bucket, MaxKeys=1)
            is_healthy = True
        except ClientError as e:
            logger.error(f"S3 health check failed: {e}")
            is_healthy = False
        except Exception as e:
            logger.error(f"S3 health check error: {e}")
            is_healthy = False

        logger.info(
            f"S3 storage health check: {'healthy' if is_healthy else 'unhealthy'}",
            extra={"is_healthy": is_healthy}
        )
        return is_healthy

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        sdk_available = await self.check_sdk_availability()
        db_healthy = await self.check_database()
        s3_healthy = await self.check_s3_storage()
        mcp_servers = await self.check_mcp_servers()

        all_healthy = sdk_available and db_healthy and s3_healthy and all(mcp_servers.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": {
                "claude_sdk": sdk_available,
                "database": db_healthy,
                "s3_storage": s3_healthy,
                "mcp_servers": mcp_servers
            },
            "timestamp": "2025-10-19T12:00:00Z"  # Would be actual timestamp
        }
