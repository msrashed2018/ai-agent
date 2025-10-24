# Celery Background Tasks Integration Plan

## Overview

This plan details how to integrate Celery for asynchronous task execution following the existing code patterns, directory structure, and layered architecture.

**Status**: ✅ Infrastructure Ready (Docker, Redis, Makefile)
**Status**: ⏳ Implementation Needed (Celery app, tasks, refactoring)

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Architecture Design](#architecture-design)
3. [Directory Structure](#directory-structure)
4. [Implementation Steps](#implementation-steps)
5. [Logging Strategy](#logging-strategy)
6. [Monitoring Integration](#monitoring-integration)
7. [Testing Plan](#testing-plan)
8. [Rollout Strategy](#rollout-strategy)

---

## Current State Analysis

### ✅ What We Have

**Infrastructure (Docker Compose)**:
```yaml
# docker-compose.yml lines 91-139
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info
  environment:
    CELERY_BROKER_URL: redis://redis:6379/1
    CELERY_RESULT_BACKEND: redis://redis:6379/2

celery-beat:
  command: celery -A app.celery_app beat --loglevel=info
```

**Redis Separation**:
- Database 0: Application cache
- Database 1: Celery broker (message queue)
- Database 2: Celery result backend (task results storage)

**Makefile Commands**:
```bash
make run-worker       # Run Celery worker (foreground)
make run-worker-bg    # Run Celery worker (background)
make run-beat         # Run Celery beat scheduler (foreground)
make run-beat-bg      # Run Celery beat (background)
make stop             # Stop all services
make logs             # Tail all logs
```

**Configuration** (`app/core/config.py`):
```python
celery_broker_url: str        # Redis broker URL
celery_result_backend: str    # Redis result backend URL
```

### ❌ What We Need to Create

1. **`app/celery_app.py`** - Celery application instance
2. **`app/celery_tasks/`** - Task definitions directory
3. **`app/celery_tasks/task_execution.py`** - Background task execution
4. **`app/celery_tasks/scheduled_tasks.py`** - Scheduled task management
5. **Refactor `TaskService.execute_task()`** - Split sync/async
6. **Enhanced logging** - Structured logging for full cycle
7. **Monitoring integration** - Track task status in real-time

---

## Architecture Design

### Layered Architecture Integration

Following existing pattern:

```
API Layer (app/api/v1/tasks.py)
    ↓
Service Layer (app/services/task_service.py)
    ↓ [NEW] Queue background task
Celery Task Layer (app/celery_tasks/task_execution.py)
    ↓
Service Layer (reuse TaskService methods)
    ↓
SDK Integration Layer (app/claude_sdk/)
    ↓
Repository Layer (app/repositories/)
    ↓
Database/Infrastructure
```

### Execution Flow Comparison

**Before (Synchronous)**:
```
POST /tasks/{id}/execute
    ↓ [BLOCKS 60-120s]
TaskService.execute_task()
    ↓
SessionService.send_message()
    ↓
Claude Code CLI execution
    ↓
HTTP 202 response (AFTER completion)
```

**After (Asynchronous)**:
```
POST /tasks/{id}/execute
    ↓
Create execution record (status=QUEUED)
    ↓
Queue Celery task
    ↓
HTTP 202 response (IMMEDIATE)

[Background - Celery Worker]
    ↓
execute_task_async.delay()
    ↓
Update status=RUNNING
    ↓
TaskService.execute_task_sync()
    ↓
SessionService.send_message()
    ↓
Claude Code CLI execution
    ↓
Update status=COMPLETED/FAILED
```

### State Machine Extension

Add new `QUEUED` status:

```
PENDING → QUEUED → RUNNING → COMPLETED/FAILED
           ↑
           └─ New state for tasks in Celery queue
```

---

## Directory Structure

### New Files to Create

```
app/
├── celery_app.py                    # NEW - Celery application
├── celery_tasks/                    # NEW - Celery tasks directory
│   ├── __init__.py
│   ├── task_execution.py           # Background task execution
│   ├── scheduled_tasks.py          # Scheduled task management
│   ├── monitoring.py               # Periodic monitoring tasks
│   └── utils.py                    # Shared task utilities
├── core/
│   ├── config.py                   # EXISTS - add Celery settings
│   └── logging.py                  # EXISTS - enhance for Celery
├── domain/
│   └── entities/
│       └── task_execution.py      # MODIFY - add QUEUED status
├── services/
│   ├── task_service.py             # MODIFY - split sync/async
│   └── celery_service.py           # NEW - Celery management service
└── api/
    └── v1/
        └── tasks.py                # MODIFY - queue tasks instead
```

### Log Files Structure

```
logs/
├── api.log                         # FastAPI application logs
├── celery-worker.log               # Celery worker logs
├── celery-beat.log                 # Celery beat scheduler logs
├── task-execution-{exec_id}.log    # Individual task execution logs
└── errors/                         # Error-specific logs
    └── task-errors-{date}.log
```

---

## Implementation Steps

### Phase 1: Create Celery Application (2 hours)

#### Step 1.1: Create `app/celery_app.py`

```python
"""Celery application configuration.

Following existing patterns:
- Uses app.core.config for settings
- Uses app.core.logging for structured logging
- Integrates with existing infrastructure
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
    # Task routing
    task_routes={
        "app.celery_tasks.task_execution.*": {"queue": "task_execution"},
        "app.celery_tasks.scheduled_tasks.*": {"queue": "scheduled"},
        "app.celery_tasks.monitoring.*": {"queue": "monitoring"},
    },

    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task behavior
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    task_track_started=True,  # Track when task starts

    # Retry behavior
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Result backend
    result_expires=86400,  # 24 hours
    result_extended=True,  # Store task args/kwargs

    # Worker behavior
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Logging
    worker_hijack_root_logger=False,  # Don't override our logging
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.celery_tasks"])


# Celery Signals for Logging and Monitoring

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Log when worker is ready."""
    logger.info(
        "Celery worker ready",
        extra={
            "worker_hostname": sender.hostname,
            "worker_type": "celery_worker",
        }
    )


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log before task execution starts."""
    logger.info(
        "Task started",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "task_args": str(args)[:200],  # Truncate large args
            "task_kwargs": str(kwargs)[:200],
            "event": "task_started",
        }
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    """Log after task execution completes."""
    logger.info(
        "Task completed",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "task_state": state,
            "event": "task_completed",
        }
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """Log task failures."""
    logger.error(
        "Task failed",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "error": str(exception),
            "error_type": type(exception).__name__,
            "task_args": str(args)[:200],
            "event": "task_failed",
        },
        exc_info=einfo,
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Log task success."""
    logger.info(
        "Task succeeded",
        extra={
            "task_name": sender.name,
            "result_preview": str(result)[:200] if result else "None",
            "event": "task_succeeded",
        }
    )


# Health check task
@celery_app.task(name="health_check")
def health_check():
    """Health check task for monitoring."""
    return {"status": "healthy", "worker": "ok"}
```

**Key Design Decisions**:
- ✅ Uses existing `app.core.config.settings`
- ✅ Uses existing `app.core.logging.get_logger()`
- ✅ Follows structured logging pattern
- ✅ Signals for comprehensive lifecycle logging
- ✅ Separate queues for different task types
- ✅ Retry and reliability settings

#### Step 1.2: Update `app/domain/entities/task_execution.py`

Add `QUEUED` status:

```python
class TaskExecutionStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"      # Created, not yet queued
    QUEUED = "queued"        # NEW - In Celery queue
    RUNNING = "running"      # Executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"        # Failed with error
    CANCELLED = "cancelled"  # Manually cancelled
```

Update `TaskExecution` entity:

```python
@dataclass
class TaskExecution:
    # ... existing fields ...

    # NEW fields for Celery integration
    celery_task_id: Optional[str] = None  # Celery task ID
    queued_at: Optional[datetime] = None  # When queued to Celery
    worker_hostname: Optional[str] = None  # Which worker processed it
    retry_count: int = 0  # Number of retries
```

---

### Phase 2: Create Task Execution Celery Task (3 hours)

#### Step 2.1: Create `app/celery_tasks/__init__.py`

```python
"""Celery tasks package.

Tasks are organized by category:
- task_execution: Background execution of user tasks
- scheduled_tasks: Periodic scheduled task management
- monitoring: System monitoring and health checks
"""

from app.celery_tasks.task_execution import execute_task_async
from app.celery_tasks.scheduled_tasks import check_scheduled_tasks
from app.celery_tasks.monitoring import collect_metrics

__all__ = [
    "execute_task_async",
    "check_scheduled_tasks",
    "collect_metrics",
]
```

#### Step 2.2: Create `app/celery_tasks/task_execution.py`

```python
"""Background task execution via Celery.

Handles asynchronous execution of user-defined tasks using Claude Code.
Integrates with existing TaskService and SessionService.
"""

import asyncio
from typing import Optional, Dict
from uuid import UUID
from celery import Task
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.core.logging import get_logger
from app.domain.entities.task_execution import TaskExecutionStatus

# Use Celery's task logger for task-specific logging
task_logger = get_task_logger(__name__)
# Use our structured logger for application logging
app_logger = get_logger(__name__)


class TaskExecutionTask(Task):
    """Custom Task class with error handling and lifecycle management."""

    autoretry_for = (Exception,)  # Retry on any exception
    retry_kwargs = {"max_retries": 3, "countdown": 60}  # Wait 60s between retries
    retry_backoff = True  # Exponential backoff
    retry_jitter = True  # Add randomness to backoff

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries."""
        execution_id = args[0] if args else None

        app_logger.error(
            "Task execution failed after all retries",
            extra={
                "celery_task_id": task_id,
                "execution_id": execution_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "retry_count": self.request.retries,
            },
            exc_info=einfo,
        )

        # Update execution status in database
        if execution_id:
            asyncio.run(self._mark_execution_failed(execution_id, str(exc)))

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        execution_id = args[0] if args else None

        app_logger.warning(
            "Task execution retry",
            extra={
                "celery_task_id": task_id,
                "execution_id": execution_id,
                "error": str(exc),
                "retry_count": self.request.retries,
                "max_retries": self.max_retries,
            }
        )

    async def _mark_execution_failed(self, execution_id: str, error_message: str):
        """Mark execution as failed in database."""
        from app.database.session import get_async_session_context
        from app.repositories.task_execution_repository import TaskExecutionRepository
        from datetime import datetime

        async with get_async_session_context() as db:
            repo = TaskExecutionRepository(db)
            await repo.update(
                execution_id,
                status=TaskExecutionStatus.FAILED.value,
                error_message=error_message,
                completed_at=datetime.utcnow(),
            )
            await db.commit()


@celery_app.task(
    bind=True,
    base=TaskExecutionTask,
    name="app.celery_tasks.task_execution.execute_task_async",
    queue="task_execution",
    track_started=True,
)
def execute_task_async(
    self,
    execution_id: str,
    task_id: str,
    user_id: str,
    variables: Optional[Dict] = None,
):
    """Execute a task asynchronously in background.

    This Celery task wraps the synchronous task execution logic,
    providing retry, error handling, and monitoring capabilities.

    Args:
        execution_id: TaskExecution UUID
        task_id: Task UUID
        user_id: User UUID
        variables: Variables for prompt template substitution

    Returns:
        Dict with execution results

    Raises:
        Exception: Any error during execution (will trigger retry)
    """
    app_logger.info(
        "Starting background task execution",
        extra={
            "celery_task_id": self.request.id,
            "execution_id": execution_id,
            "task_id": task_id,
            "user_id": user_id,
            "worker_hostname": self.request.hostname,
            "retry_count": self.request.retries,
        }
    )

    # Run async execution in event loop
    result = asyncio.run(
        _execute_task_impl(
            execution_id=execution_id,
            task_id=task_id,
            user_id=user_id,
            variables=variables or {},
            celery_task_id=self.request.id,
            worker_hostname=self.request.hostname,
        )
    )

    app_logger.info(
        "Background task execution completed",
        extra={
            "celery_task_id": self.request.id,
            "execution_id": execution_id,
            "task_id": task_id,
            "status": result.get("status"),
            "duration_seconds": result.get("duration_seconds"),
        }
    )

    return result


async def _execute_task_impl(
    execution_id: str,
    task_id: str,
    user_id: str,
    variables: Dict,
    celery_task_id: str,
    worker_hostname: str,
) -> Dict:
    """Internal async implementation of task execution.

    This function contains the actual business logic, separated from
    the Celery task wrapper for testability.
    """
    from datetime import datetime
    from app.database.session import get_async_session_context
    from app.repositories.task_repository import TaskRepository
    from app.repositories.task_execution_repository import TaskExecutionRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.session_repository import SessionRepository
    from app.repositories.message_repository import MessageRepository
    from app.repositories.tool_call_repository import ToolCallRepository
    from app.services.task_service import TaskService
    from app.services.sdk_session_service import SDKIntegratedSessionService
    from app.services.storage_manager import StorageManager
    from app.services.audit_service import AuditService
    from app.claude_sdk import ClaudeSDKClientManager, PermissionService, EventBroadcaster
    from app.infrastructure.redis_client import RedisClient

    start_time = datetime.utcnow()

    async with get_async_session_context() as db:
        # Initialize repositories
        task_repo = TaskRepository(db)
        task_execution_repo = TaskExecutionRepository(db)
        user_repo = UserRepository(db)
        session_repo = SessionRepository(db)
        message_repo = MessageRepository(db)
        tool_call_repo = ToolCallRepository(db)

        # Initialize services
        audit_service = AuditService(db)
        storage_manager = StorageManager()

        # SDK components
        sdk_client_manager = ClaudeSDKClientManager()
        permission_service = PermissionService(db)
        redis_client = RedisClient()
        event_broadcaster = EventBroadcaster(redis_client)

        # Session service
        session_service = SDKIntegratedSessionService(
            db=db,
            session_repo=session_repo,
            message_repo=message_repo,
            tool_call_repo=tool_call_repo,
            user_repo=user_repo,
            mcp_server_repo=None,  # Will be initialized inside
            storage_manager=storage_manager,
            audit_service=audit_service,
            sdk_client_manager=sdk_client_manager,
            permission_service=permission_service,
            event_broadcaster=event_broadcaster,
        )

        # Task service
        task_service = TaskService(
            db=db,
            task_repo=task_repo,
            task_execution_repo=task_execution_repo,
            user_repo=user_repo,
            audit_service=audit_service,
        )

        try:
            # Update execution status to RUNNING
            await task_execution_repo.update(
                execution_id,
                status=TaskExecutionStatus.RUNNING.value,
                celery_task_id=celery_task_id,
                worker_hostname=worker_hostname,
                started_at=start_time,
            )
            await db.commit()

            app_logger.info(
                "Execution status updated to RUNNING",
                extra={"execution_id": execution_id}
            )

            # Execute task synchronously (existing logic)
            execution = await task_service.execute_task_sync(
                execution_id=execution_id,
                session_service=session_service,
            )

            # Calculate duration
            end_time = datetime.utcnow()
            duration_seconds = int((end_time - start_time).total_seconds())

            # Update execution with results
            await task_execution_repo.update(
                execution_id,
                status=TaskExecutionStatus.COMPLETED.value,
                completed_at=end_time,
                duration_seconds=duration_seconds,
            )
            await db.commit()

            app_logger.info(
                "Task execution completed successfully",
                extra={
                    "execution_id": execution_id,
                    "duration_seconds": duration_seconds,
                }
            )

            return {
                "status": "completed",
                "execution_id": execution_id,
                "session_id": str(execution.session_id) if execution.session_id else None,
                "duration_seconds": duration_seconds,
            }

        except Exception as e:
            # Mark as failed
            end_time = datetime.utcnow()
            duration_seconds = int((end_time - start_time).total_seconds())

            await task_execution_repo.update(
                execution_id,
                status=TaskExecutionStatus.FAILED.value,
                error_message=str(e),
                completed_at=end_time,
                duration_seconds=duration_seconds,
            )
            await db.commit()

            app_logger.error(
                "Task execution failed",
                extra={
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_seconds": duration_seconds,
                },
                exc_info=True,
            )

            # Re-raise for Celery retry mechanism
            raise
```

**Key Design Decisions**:
- ✅ Custom `TaskExecutionTask` class for retry logic
- ✅ Separated `_execute_task_impl()` for testability
- ✅ Comprehensive logging at each step
- ✅ Error handling with automatic retries
- ✅ Tracks Celery task ID and worker hostname
- ✅ Updates execution status in database
- ✅ Reuses existing service layer logic

---

### Phase 3: Refactor TaskService (2 hours)

#### Step 3.1: Update `app/services/task_service.py`

Split `execute_task()` into two methods:

```python
class TaskService:
    # ... existing code ...

    async def execute_task(
        self,
        task_id: str,
        trigger_type: str = "manual",
        variables: Optional[dict] = None,
        execution_mode: str = "async",  # NEW parameter
    ):
        """Execute a task (async or sync based on mode).

        Args:
            task_id: Task UUID
            trigger_type: "manual", "scheduled", or "webhook"
            variables: Variables for prompt template
            execution_mode: "async" (queue to Celery) or "sync" (block and wait)

        Returns:
            TaskExecution entity
        """
        from app.domain.entities.task_execution import TaskExecution, TaskExecutionStatus
        from uuid import uuid4

        logger.info(
            "Executing task",
            extra={
                "task_id": task_id,
                "trigger_type": trigger_type,
                "execution_mode": execution_mode,
            }
        )

        # 1. Get and validate task
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        if not task.is_active:
            raise ValidationError("Task is not active")

        # 2. Create execution record
        execution = TaskExecution(
            id=uuid4(),
            task_id=task.id,
            user_id=task.user_id,
            trigger_type=trigger_type,
            variables=variables or {},
            status=TaskExecutionStatus.PENDING,
        )

        # Persist execution
        from app.models.task_execution import TaskExecutionModel
        execution_model = TaskExecutionModel(
            id=execution.id,
            task_id=execution.task_id,
            user_id=execution.user_id,
            trigger_type=execution.trigger_type,
            variables=execution.variables,
            status=execution.status.value,
        )
        self.db.add(execution_model)
        await self.db.flush()
        await self.db.commit()

        if execution_mode == "async":
            # Queue to Celery for background execution
            return await self._execute_task_async(execution, task, variables)
        else:
            # Execute synchronously (blocking)
            return await self._execute_task_sync(execution, task, variables)

    async def _execute_task_async(
        self,
        execution: TaskExecution,
        task: Task,
        variables: Optional[dict],
    ):
        """Queue task for background execution via Celery."""
        from app.celery_tasks.task_execution import execute_task_async
        from datetime import datetime

        logger.info(
            "Queuing task for background execution",
            extra={
                "execution_id": str(execution.id),
                "task_id": str(task.id),
            }
        )

        # Queue Celery task
        celery_task = execute_task_async.delay(
            execution_id=str(execution.id),
            task_id=str(task.id),
            user_id=str(task.user_id),
            variables=variables or {},
        )

        # Update execution with Celery task ID
        execution.status = TaskExecutionStatus.QUEUED
        execution.celery_task_id = celery_task.id
        execution.queued_at = datetime.utcnow()

        await self.task_execution_repo.update(
            str(execution.id),
            status=TaskExecutionStatus.QUEUED.value,
            celery_task_id=celery_task.id,
            queued_at=execution.queued_at,
        )
        await self.db.commit()

        logger.info(
            "Task queued successfully",
            extra={
                "execution_id": str(execution.id),
                "celery_task_id": celery_task.id,
            }
        )

        return execution

    async def _execute_task_sync(
        self,
        execution: TaskExecution,
        task: Task,
        variables: Optional[dict],
    ):
        """Execute task synchronously (existing implementation).

        This is the original blocking implementation,
        kept for backward compatibility and testing.
        """
        # ... existing execute_task() implementation ...
        # (moved from the original execute_task method)
```

---

### Phase 4: Update API Endpoint (1 hour)

#### Step 4.1: Update `app/api/v1/tasks.py`

```python
from typing import Literal

class TaskExecuteRequest(BaseModel):
    """Task execution request."""
    variables: dict = {}
    execution_mode: Literal["async", "sync"] = "async"  # NEW field


@router.post("/{task_id}/execute", response_model=TaskExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_task(
    task_id: UUID,
    request: TaskExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> TaskExecutionResponse:
    """
    Manually execute a task.

    By default, tasks are executed asynchronously in the background via Celery.
    Use execution_mode="sync" to wait for completion (not recommended for long tasks).

    Args:
        task_id: Task UUID
        request.variables: Variables for prompt template substitution
        request.execution_mode: "async" (default) or "sync"

    Returns:
        202 Accepted with execution details
        - async mode: status="queued", returns immediately
        - sync mode: status="completed"/"failed", waits for completion
    """
    # ... existing validation ...

    # Execute task (async or sync based on request)
    execution = await service.execute_task(
        task_id=str(task_id),
        trigger_type="manual",
        variables=request.variables,
        execution_mode=request.execution_mode,  # NEW
    )

    # Build response
    response = TaskExecutionResponse.model_validate(execution)
    response._links = Links(
        self=f"/api/v1/task-executions/{execution.id}",
        task=f"/api/v1/tasks/{task.id}",
    )

    if execution.session_id:
        response._links.session = f"/api/v1/sessions/{execution.session_id}"

    # Add Celery task tracking link if async
    if execution.celery_task_id:
        response._links.celery_task = f"/api/v1/admin/celery-tasks/{execution.celery_task_id}"

    return response
```

---

## Logging Strategy

### Comprehensive Logging Through Full Cycle

**Goal**: Log every step from API request to task completion with correlation IDs.

#### Log Levels

```python
# API Request
logger.info("Task execution requested", extra={
    "request_id": request_id,
    "user_id": user_id,
    "task_id": task_id,
    "execution_mode": "async/sync",
})

# Execution Created
logger.info("Task execution created", extra={
    "execution_id": execution_id,
    "status": "pending",
})

# Queued to Celery
logger.info("Task queued to Celery", extra={
    "execution_id": execution_id,
    "celery_task_id": celery_task_id,
    "status": "queued",
    "queue_name": "task_execution",
})

# Celery Worker Picks Up
logger.info("Celery worker started task", extra={
    "celery_task_id": celery_task_id,
    "execution_id": execution_id,
    "worker_hostname": worker_hostname,
    "status": "running",
})

# Session Created
logger.info("Session created for task", extra={
    "execution_id": execution_id,
    "session_id": session_id,
    "working_directory": working_dir,
})

# SDK Client Setup
logger.info("SDK client setup started", extra={
    "session_id": session_id,
    "execution_id": execution_id,
})

# Message Sent to Claude
logger.info("Message sent to Claude", extra={
    "session_id": session_id,
    "execution_id": execution_id,
    "prompt_length": len(prompt),
})

# Tool Calls (for each tool)
logger.info("Tool executed", extra={
    "session_id": session_id,
    "execution_id": execution_id,
    "tool_name": tool_name,
    "tool_duration_ms": duration_ms,
})

# Report Generation
logger.info("Report generated", extra={
    "execution_id": execution_id,
    "report_id": report_id,
    "report_format": "markdown",
    "report_size_bytes": file_size,
})

# Task Completed
logger.info("Task execution completed", extra={
    "execution_id": execution_id,
    "celery_task_id": celery_task_id,
    "status": "completed",
    "duration_seconds": duration,
    "total_messages": message_count,
    "total_tool_calls": tool_call_count,
})

# Task Failed
logger.error("Task execution failed", extra={
    "execution_id": execution_id,
    "celery_task_id": celery_task_id,
    "status": "failed",
    "error": error_message,
    "error_type": error_type,
    "retry_count": retry_count,
}, exc_info=True)
```

#### Error Storage

Store errors in multiple locations:

1. **task_executions.error_message**: Database field
2. **session.error_message**: Session-level errors
3. **logs/errors/task-errors-{date}.log**: Dedicated error log
4. **audit_logs**: Audit trail entry

```python
# On error, persist to all locations
async def handle_task_error(
    execution_id: str,
    session_id: Optional[str],
    error: Exception,
):
    """Persist error to all relevant locations."""
    error_data = {
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.utcnow().isoformat(),
        "traceback": traceback.format_exc(),
    }

    # 1. Update execution
    await task_execution_repo.update(
        execution_id,
        error_message=error_data["error"],
        error_details=error_data,  # JSON field
    )

    # 2. Update session if exists
    if session_id:
        await session_repo.update(
            session_id,
            error_message=error_data["error"],
        )

    # 3. Log to error log file
    error_logger = get_logger("task_errors")
    error_logger.error(
        "Task execution error",
        extra={
            "execution_id": execution_id,
            "session_id": session_id,
            **error_data,
        },
        exc_info=True,
    )

    # 4. Create audit log
    await audit_service.log_action(
        user_id=user_id,
        action_type="task.failed",
        resource_type="task_execution",
        resource_id=execution_id,
        action_details=error_data,
    )
```

---

## Monitoring Integration

### Enhanced Monitoring Script

Update `scripts/monitor_session.sh` to include:

1. **API logs tail**
2. **Celery worker logs tail**
3. **Task execution logs**
4. **Realtime status updates**

#### New Features

```bash
# Add to monitor_session.sh

# Display API logs related to execution
display_api_logs() {
    local execution_id="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                    API LOGS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    # Search logs for execution_id
    if [[ -f "logs/api.log" ]]; then
        echo -e "${BOLD}Recent API logs for execution:${NC}"
        grep "$execution_id" logs/api.log | tail -50 || echo "No logs found"
    else
        echo -e "${YELLOW}API log file not found${NC}"
    fi
}

# Display Celery worker logs
display_celery_logs() {
    local celery_task_id="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                  CELERY WORKER LOGS${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    if [[ -f "logs/celery-worker.log" ]]; then
        echo -e "${BOLD}Recent Celery logs for task:${NC}"
        grep "$celery_task_id" logs/celery-worker.log | tail -50 || echo "No logs found"
    else
        echo -e "${YELLOW}Celery worker log file not found${NC}"
    fi
}

# Display full execution timeline
display_execution_timeline() {
    local execution_id="$1"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}                  EXECUTION TIMELINE${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo

    # Combine logs from all sources
    {
        grep "$execution_id" logs/api.log 2>/dev/null || true
        grep "$execution_id" logs/celery-worker.log 2>/dev/null || true
    } | sort | tail -100
}
```

### New Monitoring Command

```bash
# Add new option to test_tasks_api.sh

monitor-execution() {
    local execution_id="$1"

    echo "Real-time monitoring of execution: $execution_id"

    while true; do
        clear

        # Get current status
        status_json=$(api_get "/api/v1/task-executions/$execution_id")
        status=$(echo "$status_json" | jq -r '.status')

        # Display status
        echo "Status: $status"
        echo "Last updated: $(date)"
        echo

        # Tail logs
        echo "=== Recent Logs ==="
        tail -20 logs/api.log | grep "$execution_id" || echo "No recent logs"

        # Check if completed
        if [[ "$status" == "completed" ]] || [[ "$status" == "failed" ]]; then
            echo
            echo "Execution finished: $status"
            break
        fi

        sleep 2
    done
}
```

---

## Testing Plan

### Unit Tests

```python
# tests/unit/test_celery_tasks.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.celery_tasks.task_execution import execute_task_async, _execute_task_impl


class TestExecuteTaskAsync:
    """Test Celery task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_impl_success(self):
        """Test successful task execution."""
        # Arrange
        execution_id = "test-exec-id"
        task_id = "test-task-id"
        user_id = "test-user-id"
        variables = {"env": "test"}

        # Act
        result = await _execute_task_impl(
            execution_id=execution_id,
            task_id=task_id,
            user_id=user_id,
            variables=variables,
            celery_task_id="celery-123",
            worker_hostname="worker-1",
        )

        # Assert
        assert result["status"] == "completed"
        assert result["execution_id"] == execution_id

    @pytest.mark.asyncio
    async def test_execute_task_impl_handles_errors(self):
        """Test error handling in task execution."""
        # Test that errors are properly caught and logged
        pass

    def test_celery_task_retry_logic(self):
        """Test that tasks retry on failure."""
        # Test retry mechanism
        pass
```

### Integration Tests

```python
# tests/integration/test_background_task_execution.py

import pytest
from uuid import uuid4
from app.celery_tasks.task_execution import execute_task_async


class TestBackgroundTaskExecution:
    """Integration tests for background task execution."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_task_execution_flow(self, db_session, test_user, test_task):
        """Test complete flow from queue to completion."""
        # Create execution
        execution_id = str(uuid4())

        # Queue task
        celery_task = execute_task_async.delay(
            execution_id=execution_id,
            task_id=str(test_task.id),
            user_id=str(test_user.id),
            variables={"test": "value"},
        )

        # Wait for completion (with timeout)
        result = celery_task.get(timeout=30)

        # Verify
        assert result["status"] == "completed"

        # Check database
        from app.repositories.task_execution_repository import TaskExecutionRepository
        repo = TaskExecutionRepository(db_session)
        execution = await repo.get_by_id(execution_id)

        assert execution.status == "completed"
        assert execution.celery_task_id == celery_task.id

    @pytest.mark.integration
    def test_task_appears_in_celery_queue(self):
        """Test that task is actually queued to Celery."""
        pass

    @pytest.mark.integration
    def test_concurrent_task_execution(self):
        """Test multiple tasks running concurrently."""
        pass
```

---

## Rollout Strategy

### Phase 1: Infrastructure (Week 1)

**Day 1-2**: Create Celery app and basic tasks
- ✅ Create `app/celery_app.py`
- ✅ Create `app/celery_tasks/` structure
- ✅ Add comprehensive logging
- ✅ Test Celery connection

**Day 3-4**: Refactor TaskService
- ✅ Split sync/async execution
- ✅ Add `QUEUED` status
- ✅ Update API endpoint
- ✅ Add execution_mode parameter

**Day 5**: Testing and monitoring
- ✅ Write unit tests
- ✅ Write integration tests
- ✅ Update monitoring scripts
- ✅ Test in development environment

### Phase 2: Gradual Rollout (Week 2)

**Day 1-2**: Feature flag rollout
- ✅ Add feature flag: `ENABLE_ASYNC_TASK_EXECUTION`
- ✅ Default to sync for existing users
- ✅ Test async with new tasks only

**Day 3-4**: Production testing
- ✅ Deploy to staging
- ✅ Run smoke tests
- ✅ Monitor Celery workers
- ✅ Verify error handling

**Day 5**: Full rollout
- ✅ Enable async by default
- ✅ Monitor production metrics
- ✅ Rollback plan ready

### Phase 3: Optimization (Week 3)

**Day 1-3**: Performance tuning
- ✅ Optimize worker count
- ✅ Tune prefetch settings
- ✅ Add auto-scaling if needed

**Day 4-5**: Documentation and training
- ✅ Update API docs
- ✅ Create runbook for ops team
- ✅ Document monitoring procedures

---

## Immediate Next Steps

1. ✅ **Review this plan** - Get stakeholder approval
2. ✅ **Create Celery app** - Implement `app/celery_app.py`
3. ✅ **Create background task** - Implement `app/celery_tasks/task_execution.py`
4. ✅ **Test locally** - Verify Celery worker processes tasks
5. ✅ **Update monitoring** - Enhance scripts with log tailing
6. ✅ **Deploy to staging** - Test in staging environment

---

## Success Criteria

✅ Task execution returns immediately (< 1 second)
✅ Background execution tracked in Celery
✅ Comprehensive logging through full cycle
✅ Errors saved in multiple locations (DB, logs, audit)
✅ Monitoring script shows real-time progress
✅ Retry logic works for transient failures
✅ No regression in existing functionality

---

**Document Created**: 2025-10-24
**Status**: Ready for Implementation
**Estimated Effort**: 2-3 weeks (1 developer)
