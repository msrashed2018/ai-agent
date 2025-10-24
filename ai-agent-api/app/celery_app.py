"""Celery application configuration.

Integrates with existing infrastructure:
- Uses app.core.config for settings
- Uses app.core.logging for structured logging
- Connects to Redis broker/backend from docker-compose
"""

from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_success,
    worker_ready,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "ai-agent-tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    # Task routing - separate queues for different task types
    task_routes={
        "app.celery_tasks.task_execution.*": {"queue": "task_execution"},
        "app.celery_tasks.scheduled_tasks.*": {"queue": "scheduled"},
        "app.celery_tasks.monitoring.*": {"queue": "monitoring"},
    },

    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task behavior
    task_acks_late=True,  # Acknowledge after task completes (prevents loss)
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    task_track_started=True,  # Track when task starts executing

    # Retry behavior
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,

    # Result backend
    result_expires=86400,  # Keep results for 24 hours
    result_extended=True,  # Store task args/kwargs in result

    # Worker behavior
    worker_prefetch_multiplier=1,  # One task at a time per worker (for long tasks)
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)

    # Logging
    worker_hijack_root_logger=False,  # Don't override our logging config
)

# Auto-discover tasks in celery_tasks module
celery_app.autodiscover_tasks(["app.celery_tasks"])


# ============================================================================
# Celery Signals for Logging and Monitoring
# ============================================================================

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Log when Celery worker is ready."""
    logger.info(
        "Celery worker ready",
        extra={
            "worker_hostname": sender.hostname,
            "worker_type": "celery_worker",
            "event": "worker_ready",
        }
    )


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log before task execution starts."""
    logger.info(
        "Celery task started",
        extra={
            "celery_task_id": task_id,
            "task_name": task.name,
            "task_args": str(args)[:200] if args else "[]",
            "task_kwargs": str(kwargs)[:200] if kwargs else "{}",
            "event": "task_started",
        }
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    """Log after task execution completes."""
    logger.info(
        "Celery task completed",
        extra={
            "celery_task_id": task_id,
            "task_name": task.name,
            "task_state": state,
            "event": "task_completed",
        }
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """Log task failures with full context."""
    logger.error(
        "Celery task failed",
        extra={
            "celery_task_id": task_id,
            "task_name": sender.name if sender else "unknown",
            "error": str(exception),
            "error_type": type(exception).__name__,
            "task_args": str(args)[:200] if args else "[]",
            "event": "task_failed",
        },
        exc_info=einfo,
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log task success."""
    logger.info(
        "Celery task succeeded",
        extra={
            "task_name": sender.name if sender else "unknown",
            "result_preview": str(result)[:200] if result else "None",
            "event": "task_succeeded",
        }
    )


# ============================================================================
# Health Check Task
# ============================================================================

@celery_app.task(name="health_check")
def health_check():
    """Health check task for monitoring Celery workers."""
    return {"status": "healthy", "worker": "ok"}
