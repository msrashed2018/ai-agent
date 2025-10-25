"""Seed hooks (webhooks and event handlers)."""

import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import UserModel
from app.models.hook import HookModel

logger = logging.getLogger(__name__)


# Default hook configurations for development
DEFAULT_HOOKS = [
    {
        "name": "Task Execution Notification",
        "description": "Send webhook notification when task execution completes",
        "hook_event": "PreToolUse",
        "matcher": None,
        "is_enabled": True,
        "implementation_type": "webhook",
        "implementation_config": {
            "webhook_url": "http://localhost:3000/api/webhooks/task-completion",
            "retry_on_failure": True,
            "retry_count": 3,
            "timeout_seconds": 30,
            "headers": {
                "X-Event-Type": "task.completed",
                "Content-Type": "application/json",
            }
        }
    },
    {
        "name": "Tool Call Audit Log",
        "description": "Log all tool calls for audit and compliance tracking",
        "hook_event": "PostToolUse",
        "matcher": None,
        "is_enabled": True,
        "implementation_type": "builtin",
        "implementation_config": {
            "log_format": "json",
            "include_input": True,
            "include_output": True,
            "include_context": True,
            "log_level": "info"
        }
    },
    {
        "name": "Permission Decision Webhook",
        "description": "Notify external system of permission decisions",
        "hook_event": "UserPromptSubmit",
        "matcher": None,
        "is_enabled": True,
        "implementation_type": "webhook",
        "implementation_config": {
            "webhook_url": "http://localhost:3000/api/webhooks/permissions",
            "method": "POST",
            "retry_on_failure": True,
            "retry_count": 2,
            "timeout_seconds": 20,
            "headers": {
                "Authorization": "Bearer ${WEBHOOK_TOKEN}",
                "Content-Type": "application/json",
            },
            "include_decision_reason": True
        }
    },
    {
        "name": "Error Alert Hook",
        "description": "Send alert when task execution encounters errors",
        "hook_event": "Stop",
        "matcher": None,
        "is_enabled": True,
        "implementation_type": "webhook",
        "implementation_config": {
            "webhook_url": "http://localhost:3000/api/webhooks/errors",
            "method": "POST",
            "alert_channels": ["slack", "email"],
            "include_stack_trace": True,
            "include_context": True,
        }
    },
    {
        "name": "Execution Metrics Collector",
        "description": "Collect and report execution metrics and performance data",
        "hook_event": "PreCompact",
        "matcher": None,
        "is_enabled": True,
        "implementation_type": "builtin",
        "implementation_config": {
            "metrics_to_collect": [
                "execution_duration_ms",
                "tokens_used",
                "tool_calls_count",
                "memory_usage_mb",
                "success_rate"
            ],
            "collection_interval_minutes": 5,
            "export_format": "prometheus",
            "export_endpoint": "http://localhost:9090/metrics"
        }
    },
]


async def seed_hooks(db: AsyncSession) -> None:
    """Seed default webhook and event handler configurations.

    Creates pre-configured hooks that can be used for notifications,
    auditing, and external system integration.

    Args:
        db: AsyncSession for database operations
    """
    logger.info("Seeding hooks...")

    # Get admin user to assign hooks to
    result = await db.execute(
        select(UserModel).where(UserModel.username == "admin")
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        logger.warning("  Admin user not found, skipping hooks seeding")
        return

    # Check which hooks already exist
    for hook_data in DEFAULT_HOOKS:
        result = await db.execute(
            select(HookModel).where(
                HookModel.name == hook_data["name"],
                HookModel.user_id == admin_user.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"  Hook '{hook_data['name']}' already exists, skipping")
            continue

        # Create new hook configuration
        hook = HookModel(
            id=uuid4(),
            user_id=admin_user.id,
            name=hook_data["name"],
            description=hook_data["description"],
            hook_event=hook_data["hook_event"],
            matcher=hook_data.get("matcher"),
            implementation_type=hook_data.get("implementation_type", "webhook"),
            implementation_config=hook_data.get("implementation_config", {}),
            is_enabled=hook_data.get("is_enabled", True),
        )

        db.add(hook)
        logger.info(f"  ✅ Created hook: {hook_data['name']}")

    await db.commit()
    logger.info("Hooks seeded successfully!")
