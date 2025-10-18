# Integration Changes Required for New Claude SDK Module

**Version**: 1.0
**Date**: 2025-10-19
**Status**: Migration Guide

---

## Executive Summary

This document outlines all required changes **outside** the `app/claude_sdk` module to integrate with the new Claude SDK module architecture. The new architecture introduces significant enhancements including session modes, forking, comprehensive persistence, storage archival, and advanced monitoring.

**Scope of Changes**:
- Database schema updates (new tables, columns)
- Domain entity enhancements
- API endpoint modifications
- Service layer updates
- Schema (Pydantic) changes
- Repository extensions
- Configuration updates

---

## Table of Contents

1. [Database Schema Changes](#1-database-schema-changes)
2. [Domain Entity Updates](#2-domain-entity-updates)
3. [Database Models (ORM) Changes](#3-database-models-orm-changes)
4. [Repository Layer Extensions](#4-repository-layer-extensions)
5. [Service Layer Updates](#5-service-layer-updates)
6. [API Schemas (Pydantic) Changes](#6-api-schemas-pydantic-changes)
7. [API Endpoints Updates](#7-api-endpoints-updates)
8. [Configuration Changes](#8-configuration-changes)
9. [Dependencies & Initialization](#9-dependencies--initialization)
10. [Migration Strategy](#10-migration-strategy)

---

## 1. Database Schema Changes

### 1.1 New Tables to Create

#### **hook_executions**
Audit trail for all hook invocations.

```sql
CREATE TABLE hook_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    hook_type VARCHAR(50) NOT NULL,  -- 'PreToolUse', 'PostToolUse', etc.
    tool_use_id VARCHAR(255),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    continue_execution BOOLEAN NOT NULL DEFAULT TRUE,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_hook_executions_session (session_id),
    INDEX idx_hook_executions_type (hook_type),
    INDEX idx_hook_executions_executed_at (executed_at)
);
```

#### **permission_decisions**
Audit trail for permission checks.

```sql
CREATE TABLE permission_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL,
    context JSONB NOT NULL,  -- ToolPermissionContext serialized
    decision VARCHAR(20) NOT NULL,  -- 'allow' or 'deny'
    reason TEXT,
    interrupted BOOLEAN NOT NULL DEFAULT FALSE,
    decided_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_permission_decisions_session (session_id),
    INDEX idx_permission_decisions_tool (tool_name),
    INDEX idx_permission_decisions_decision (decision)
);
```

#### **working_directory_archives**
Track S3/storage archives of working directories.

```sql
CREATE TABLE working_directory_archives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    archive_path TEXT NOT NULL,  -- S3 URI or local path (e.g., s3://bucket/archives/session_id.tar.gz)
    size_bytes BIGINT NOT NULL,
    compression VARCHAR(20) NOT NULL DEFAULT 'gzip',  -- 'gzip', 'zip', 'tar'
    manifest JSONB NOT NULL,  -- File listing with metadata
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    archived_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_archives_status (status),
    INDEX idx_archives_created_at (created_at)
);
```

#### **session_metrics_snapshots**
Historical tracking of session metrics for analytics.

```sql
CREATE TABLE session_metrics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    snapshot_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Message counts
    total_messages INT NOT NULL,
    total_tool_calls INT NOT NULL,
    total_hook_executions INT NOT NULL,
    total_permission_checks INT NOT NULL,
    total_errors INT NOT NULL,
    total_retries INT NOT NULL,

    -- Cost & tokens
    total_cost_usd NUMERIC(10, 6) NOT NULL,
    total_input_tokens INT NOT NULL,
    total_output_tokens INT NOT NULL,
    total_cache_creation_tokens INT NOT NULL,
    total_cache_read_tokens INT NOT NULL,

    -- Timing
    duration_ms BIGINT NOT NULL,
    avg_tool_duration_ms INT,

    INDEX idx_metrics_session (session_id),
    INDEX idx_metrics_snapshot_at (snapshot_at)
);
```

### 1.2 Existing Table Updates

#### **sessions** table modifications

```sql
-- Add new columns for enhanced functionality
ALTER TABLE sessions

-- Session mode (interactive vs background vs forked)
ADD COLUMN mode VARCHAR(50) NOT NULL DEFAULT 'interactive' CHECK (mode IN ('interactive', 'background', 'forked')),

-- Streaming configuration
ADD COLUMN include_partial_messages BOOLEAN DEFAULT FALSE,

-- Retry configuration
ADD COLUMN max_retries INT DEFAULT 3,
ADD COLUMN retry_delay FLOAT DEFAULT 2.0,
ADD COLUMN timeout_seconds INT DEFAULT 120,

-- Hook configuration
ADD COLUMN hooks_enabled JSONB DEFAULT '[]',  -- ["PreToolUse", "PostToolUse", ...]

-- Permission configuration
ADD COLUMN permission_mode VARCHAR(50) DEFAULT 'default' CHECK (permission_mode IN ('default', 'acceptEdits', 'bypassPermissions')),
ADD COLUMN custom_policies JSONB DEFAULT '[]',  -- ["FileAccessPolicy", "CommandPolicy", ...]

-- Metrics tracking
ADD COLUMN total_hook_executions INT DEFAULT 0,
ADD COLUMN total_permission_checks INT DEFAULT 0,
ADD COLUMN total_errors INT DEFAULT 0,
ADD COLUMN total_retries INT DEFAULT 0,

-- Archive reference
ADD COLUMN archive_id UUID REFERENCES working_directory_archives(id),

-- Template reference (if session created from template)
ADD COLUMN template_id UUID REFERENCES session_templates(id);

-- Add indexes for new columns
CREATE INDEX idx_sessions_mode ON sessions(mode);
CREATE INDEX idx_sessions_permission_mode ON sessions(permission_mode);
CREATE INDEX idx_sessions_template_id ON sessions(template_id);
CREATE INDEX idx_sessions_archive_id ON sessions(archive_id);
```

#### **messages** table modifications

```sql
-- Add streaming support
ALTER TABLE messages
ADD COLUMN is_partial BOOLEAN DEFAULT FALSE,  -- TRUE for partial StreamEvents
ADD COLUMN parent_message_id UUID REFERENCES messages(id),  -- Link partial to complete message
ADD COLUMN model VARCHAR(100),  -- Model used for this message
ADD COLUMN thinking_content TEXT;  -- ThinkingBlock content if present

CREATE INDEX idx_messages_parent (parent_message_id);
CREATE INDEX idx_messages_is_partial (is_partial);
```

#### **tool_calls** table modifications

```sql
-- Add execution metrics
ALTER TABLE tool_calls
ADD COLUMN duration_ms INT,
ADD COLUMN retries INT DEFAULT 0,
ADD COLUMN hook_pre_data JSONB,  -- PreToolUse hook data
ADD COLUMN hook_post_data JSONB,  -- PostToolUse hook data
ADD COLUMN permission_decision VARCHAR(20),  -- 'allow', 'deny', 'not_checked'
ADD COLUMN permission_reason TEXT;

CREATE INDEX idx_tool_calls_duration (duration_ms);
CREATE INDEX idx_tool_calls_permission (permission_decision);
```

### 1.3 Migration Scripts

Create Alembic migration:

```bash
poetry run alembic revision --autogenerate -m "Add new Claude SDK module tables and columns"
```

Manually review and adjust the generated migration, then apply:

```bash
poetry run alembic upgrade head
```

---

## 2. Domain Entity Updates

### 2.1 Session Entity (`app/domain/entities/session.py`)

**Add new SessionMode enum**:

```python
class SessionMode(str, Enum):
    """Session execution modes."""
    INTERACTIVE = "interactive"          # Real-time chat (UI)
    BACKGROUND = "background"            # Automated task (no user interaction)
    FORKED = "forked"                   # Continuation of existing session
```

**Update Session class**:

```python
class Session:
    """Session aggregate root."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        mode: SessionMode,
        sdk_options: dict,
        name: Optional[str] = None,
        status: SessionStatus = SessionStatus.CREATED,
    ):
        # ... existing fields ...

        # NEW: Streaming configuration
        self.include_partial_messages: bool = False

        # NEW: Retry configuration
        self.max_retries: int = 3
        self.retry_delay: float = 2.0
        self.timeout_seconds: int = 120

        # NEW: Hook configuration
        self.hooks_enabled: List[str] = []  # ["PreToolUse", "PostToolUse", ...]

        # NEW: Permission configuration
        self.permission_mode: str = "default"  # 'default', 'acceptEdits', 'bypassPermissions'
        self.custom_policies: List[str] = []

        # NEW: Metrics
        self.total_hook_executions: int = 0
        self.total_permission_checks: int = 0
        self.total_errors: int = 0
        self.total_retries: int = 0

        # NEW: Archive reference
        self.archive_id: Optional[UUID] = None

        # NEW: Template reference
        self.template_id: Optional[UUID] = None

    # NEW: Metrics update methods
    def increment_hook_execution_count(self) -> None:
        """Increment hook execution counter."""
        self.total_hook_executions += 1
        self.updated_at = datetime.utcnow()

    def increment_permission_check_count(self) -> None:
        """Increment permission check counter."""
        self.total_permission_checks += 1
        self.updated_at = datetime.utcnow()

    def increment_error_count(self) -> None:
        """Increment error counter."""
        self.total_errors += 1
        self.updated_at = datetime.utcnow()

    def increment_retry_count(self) -> None:
        """Increment retry counter."""
        self.total_retries += 1
        self.updated_at = datetime.utcnow()
```

### 2.2 New Domain Entities

Create new files in `app/domain/entities/`:

#### **hook_execution.py**

```python
"""Hook execution domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Optional


@dataclass
class HookExecution:
    """Domain entity for hook execution audit trail."""

    id: UUID
    session_id: UUID
    hook_type: str  # 'PreToolUse', 'PostToolUse', etc.
    tool_use_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    continue_execution: bool
    executed_at: datetime
```

#### **permission_decision.py**

```python
"""Permission decision domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Optional


@dataclass
class PermissionDecision:
    """Domain entity for permission check audit trail."""

    id: UUID
    session_id: UUID
    tool_name: str
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    decision: str  # 'allow' or 'deny'
    reason: Optional[str]
    interrupted: bool
    decided_at: datetime
```

#### **archive_metadata.py**

```python
"""Working directory archive metadata."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Optional
from enum import Enum


class ArchiveStatus(str, Enum):
    """Archive status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ArchiveMetadata:
    """Domain entity for working directory archive."""

    id: UUID
    session_id: UUID
    archive_path: str  # S3 URI or local path
    size_bytes: int
    compression: str  # 'gzip', 'zip', 'tar'
    manifest: Dict[str, Any]  # File listing
    status: ArchiveStatus
    error_message: Optional[str]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

---

## 3. Database Models (ORM) Changes

### 3.1 Update SessionModel (`app/models/session.py`)

Add new columns to match schema changes:

```python
from sqlalchemy import Column, String, Integer, Float, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID

class SessionModel(Base):
    """Session table model."""

    __tablename__ = "sessions"

    # ... existing columns ...

    # NEW: Session mode
    mode = Column(String(50), nullable=False, default="interactive")

    # NEW: Streaming
    include_partial_messages = Column(Boolean, default=False)

    # NEW: Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Float, default=2.0)
    timeout_seconds = Column(Integer, default=120)

    # NEW: Hooks
    hooks_enabled = Column(JSONB, default=[])

    # NEW: Permissions
    permission_mode = Column(String(50), default="default")
    custom_policies = Column(JSONB, default=[])

    # NEW: Metrics
    total_hook_executions = Column(Integer, default=0)
    total_permission_checks = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    total_retries = Column(Integer, default=0)

    # NEW: Archive
    archive_id = Column(UUID(as_uuid=True), ForeignKey("working_directory_archives.id"))

    # NEW: Template
    template_id = Column(UUID(as_uuid=True), ForeignKey("session_templates.id"))

    # NEW: Relationships
    archive = relationship("WorkingDirectoryArchiveModel", back_populates="session", uselist=False)
    hook_executions = relationship("HookExecutionModel", back_populates="session", cascade="all, delete-orphan")
    permission_decisions = relationship("PermissionDecisionModel", back_populates="session", cascade="all, delete-orphan")
    metrics_snapshots = relationship("SessionMetricsSnapshotModel", back_populates="session", cascade="all, delete-orphan")

    # UPDATE: Constraints
    __table_args__ = (
        CheckConstraint("mode IN ('interactive', 'background', 'forked')", name="chk_mode"),
        CheckConstraint("permission_mode IN ('default', 'acceptEdits', 'bypassPermissions')", name="chk_permission_mode"),
        # ... existing constraints ...
    )
```

### 3.2 Create New Models

#### **hook_execution.py** (`app/models/`)

```python
"""Hook execution database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, JSONB


class HookExecutionModel(Base):
    """Hook execution table model."""

    __tablename__ = "hook_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    hook_type = Column(String(50), nullable=False, index=True)
    tool_use_id = Column(String(255))
    input_data = Column(JSONB, nullable=False, default={})
    output_data = Column(JSONB, nullable=False, default={})
    continue_execution = Column(Boolean, nullable=False, default=True)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("SessionModel", back_populates="hook_executions")
```

#### **permission_decision.py** (`app/models/`)

```python
"""Permission decision database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, JSONB


class PermissionDecisionModel(Base):
    """Permission decision table model."""

    __tablename__ = "permission_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False, index=True)
    input_data = Column(JSONB, nullable=False, default={})
    context = Column(JSONB, nullable=False, default={})
    decision = Column(String(20), nullable=False, index=True)  # 'allow', 'deny'
    reason = Column(Text)
    interrupted = Column(Boolean, nullable=False, default=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="permission_decisions")
```

#### **working_directory_archive.py** (`app/models/`)

```python
"""Working directory archive database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, BigInteger, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, JSONB


class WorkingDirectoryArchiveModel(Base):
    """Working directory archive table model."""

    __tablename__ = "working_directory_archives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    archive_path = Column(Text, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    compression = Column(String(20), nullable=False, default="gzip")
    manifest = Column(JSONB, nullable=False, default={})
    status = Column(String(50), nullable=False, default="pending", index=True)
    error_message = Column(Text)
    archived_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="archive")
```

#### **session_metrics_snapshot.py** (`app/models/`)

```python
"""Session metrics snapshot database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Integer, BigInteger, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


class SessionMetricsSnapshotModel(Base):
    """Session metrics snapshot table model."""

    __tablename__ = "session_metrics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Counts
    total_messages = Column(Integer, nullable=False, default=0)
    total_tool_calls = Column(Integer, nullable=False, default=0)
    total_hook_executions = Column(Integer, nullable=False, default=0)
    total_permission_checks = Column(Integer, nullable=False, default=0)
    total_errors = Column(Integer, nullable=False, default=0)
    total_retries = Column(Integer, nullable=False, default=0)

    # Cost & tokens
    total_cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    total_cache_creation_tokens = Column(Integer, nullable=False, default=0)
    total_cache_read_tokens = Column(Integer, nullable=False, default=0)

    # Timing
    duration_ms = Column(BigInteger, nullable=False, default=0)
    avg_tool_duration_ms = Column(Integer)

    # Relationships
    session = relationship("SessionModel", back_populates="metrics_snapshots")
```

### 3.3 Update MessageModel (`app/models/message.py`)

```python
class MessageModel(Base):
    """Message table model."""

    __tablename__ = "messages"

    # ... existing columns ...

    # NEW: Streaming support
    is_partial = Column(Boolean, default=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"))
    model = Column(String(100))
    thinking_content = Column(Text)

    # NEW: Relationships
    partial_messages = relationship("MessageModel", back_populates="parent_message")
    parent_message = relationship("MessageModel", remote_side=[id], back_populates="partial_messages")
```

### 3.4 Update ToolCallModel (`app/models/tool_call.py`)

```python
class ToolCallModel(Base):
    """Tool call table model."""

    __tablename__ = "tool_calls"

    # ... existing columns ...

    # NEW: Execution metrics
    duration_ms = Column(Integer)
    retries = Column(Integer, default=0)

    # NEW: Hook data
    hook_pre_data = Column(JSONB)
    hook_post_data = Column(JSONB)

    # NEW: Permission data
    permission_decision = Column(String(20))  # 'allow', 'deny', 'not_checked'
    permission_reason = Column(Text)
```

---

## 4. Repository Layer Extensions

### 4.1 Create New Repositories

#### **hook_execution_repository.py** (`app/repositories/`)

```python
"""Hook execution repository."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hook_execution import HookExecutionModel
from app.repositories.base import BaseRepository


class HookExecutionRepository(BaseRepository[HookExecutionModel]):
    """Repository for hook execution data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(HookExecutionModel, db)

    async def get_by_session(self, session_id: UUID, limit: int = 100) -> List[HookExecutionModel]:
        """Get all hook executions for a session."""
        stmt = (
            select(HookExecutionModel)
            .where(HookExecutionModel.session_id == session_id)
            .order_by(HookExecutionModel.executed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_hook_type(
        self,
        session_id: UUID,
        hook_type: str,
        limit: int = 100
    ) -> List[HookExecutionModel]:
        """Get hook executions by type for a session."""
        stmt = (
            select(HookExecutionModel)
            .where(
                HookExecutionModel.session_id == session_id,
                HookExecutionModel.hook_type == hook_type
            )
            .order_by(HookExecutionModel.executed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

#### **permission_decision_repository.py** (`app/repositories/`)

```python
"""Permission decision repository."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission_decision import PermissionDecisionModel
from app.repositories.base import BaseRepository


class PermissionDecisionRepository(BaseRepository[PermissionDecisionModel]):
    """Repository for permission decision data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(PermissionDecisionModel, db)

    async def get_by_session(self, session_id: UUID, limit: int = 100) -> List[PermissionDecisionModel]:
        """Get all permission decisions for a session."""
        stmt = (
            select(PermissionDecisionModel)
            .where(PermissionDecisionModel.session_id == session_id)
            .order_by(PermissionDecisionModel.decided_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_denied_permissions(self, session_id: UUID) -> List[PermissionDecisionModel]:
        """Get all denied permission requests for a session."""
        stmt = (
            select(PermissionDecisionModel)
            .where(
                PermissionDecisionModel.session_id == session_id,
                PermissionDecisionModel.decision == "deny"
            )
            .order_by(PermissionDecisionModel.decided_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

#### **working_directory_archive_repository.py** (`app/repositories/`)

```python
"""Working directory archive repository."""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.working_directory_archive import WorkingDirectoryArchiveModel
from app.repositories.base import BaseRepository


class WorkingDirectoryArchiveRepository(BaseRepository[WorkingDirectoryArchiveModel]):
    """Repository for working directory archive data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(WorkingDirectoryArchiveModel, db)

    async def get_by_session(self, session_id: UUID) -> Optional[WorkingDirectoryArchiveModel]:
        """Get archive by session ID."""
        stmt = select(WorkingDirectoryArchiveModel).where(
            WorkingDirectoryArchiveModel.session_id == session_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_archives(self, limit: int = 10) -> list[WorkingDirectoryArchiveModel]:
        """Get pending archives for background processing."""
        stmt = (
            select(WorkingDirectoryArchiveModel)
            .where(WorkingDirectoryArchiveModel.status == "pending")
            .order_by(WorkingDirectoryArchiveModel.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

#### **session_metrics_snapshot_repository.py** (`app/repositories/`)

```python
"""Session metrics snapshot repository."""
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session_metrics_snapshot import SessionMetricsSnapshotModel
from app.repositories.base import BaseRepository


class SessionMetricsSnapshotRepository(BaseRepository[SessionMetricsSnapshotModel]):
    """Repository for session metrics snapshot data access."""

    def __init__(self, db: AsyncSession):
        super().__init__(SessionMetricsSnapshotModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        limit: int = 100
    ) -> List[SessionMetricsSnapshotModel]:
        """Get metrics snapshots for a session."""
        stmt = (
            select(SessionMetricsSnapshotModel)
            .where(SessionMetricsSnapshotModel.session_id == session_id)
            .order_by(SessionMetricsSnapshotModel.snapshot_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_snapshot(self, session_id: UUID) -> Optional[SessionMetricsSnapshotModel]:
        """Get latest metrics snapshot for a session."""
        stmt = (
            select(SessionMetricsSnapshotModel)
            .where(SessionMetricsSnapshotModel.session_id == session_id)
            .order_by(SessionMetricsSnapshotModel.snapshot_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

### 4.2 Update Existing Repositories

#### **session_repository.py**

Add new query methods:

```python
class SessionRepository(BaseRepository[SessionModel]):
    """Repository for session data access."""

    # ... existing methods ...

    async def get_by_mode(self, mode: str, limit: int = 100) -> List[SessionModel]:
        """Get sessions by mode (interactive, background, forked)."""
        stmt = (
            select(SessionModel)
            .where(SessionModel.mode == mode)
            .order_by(SessionModel.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_forked_sessions(self, parent_session_id: UUID) -> List[SessionModel]:
        """Get all forked sessions from a parent."""
        stmt = (
            select(SessionModel)
            .where(
                SessionModel.parent_session_id == parent_session_id,
                SessionModel.is_fork == True
            )
            .order_by(SessionModel.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_sessions_with_archives(self, limit: int = 100) -> List[SessionModel]:
        """Get sessions that have archives."""
        stmt = (
            select(SessionModel)
            .where(SessionModel.archive_id.isnot(None))
            .order_by(SessionModel.completed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

---

## 5. Service Layer Updates

### 5.1 Update SessionService (`app/services/session_service.py`)

Add new methods for session forking and archival:

```python
class SessionService:
    """Business logic for session management."""

    # ... existing methods ...

    async def fork_session(
        self,
        parent_session_id: UUID,
        user_id: UUID,
        fork_at_message: Optional[int] = None,
        name: Optional[str] = None
    ) -> Session:
        """Fork an existing session.

        Creates a new session that:
        1. Copies configuration from parent
        2. Optionally restores context up to specific message
        3. Creates new working directory
        4. Links to parent session

        Args:
            parent_session_id: Parent session UUID
            user_id: User UUID (must own parent session)
            fork_at_message: Optional message index to fork from
            name: Optional name for forked session

        Returns:
            New forked Session entity
        """
        # 1. Get parent session (with authorization)
        parent_session = await self.get_session(parent_session_id, user_id)

        # 2. Create forked session with parent's configuration
        forked_session = await self.create_session(
            user_id=user_id,
            mode=SessionMode.FORKED,
            sdk_options=parent_session.sdk_options.copy(),
            name=name or f"Fork of {parent_session.name}",
            parent_session_id=parent_session_id
        )

        # 3. Optionally copy messages up to fork point
        if fork_at_message is not None:
            # Retrieve parent messages
            parent_messages = await self.message_repo.get_session_messages(
                parent_session_id,
                limit=fork_at_message
            )

            # Copy to forked session
            # (This will be handled by new SDK module's ForkedExecutor)

        # 4. Audit log
        await self.audit_service.log_session_forked(
            session_id=forked_session.id,
            parent_session_id=parent_session_id,
            user_id=user_id,
            fork_at_message=fork_at_message
        )

        return forked_session

    async def archive_session(
        self,
        session_id: UUID,
        user_id: UUID,
        upload_to_s3: bool = True
    ) -> ArchiveMetadata:
        """Archive a session's working directory.

        Args:
            session_id: Session UUID
            user_id: User UUID (must own session)
            upload_to_s3: Whether to upload to S3 or keep local

        Returns:
            ArchiveMetadata with archive details
        """
        # 1. Get session
        session = await self.get_session(session_id, user_id)

        # 2. Verify session is in terminal state
        if not session.is_terminal():
            from app.domain.exceptions import InvalidStateError
            raise InvalidStateError("Can only archive completed/failed/terminated sessions")

        # 3. Delegate to new SDK module's StorageArchiver
        # (Will be implemented in new SDK module)
        from app.claude_sdk.persistence import StorageArchiver

        archiver = StorageArchiver(storage_provider="s3" if upload_to_s3 else "local")
        archive_metadata = await archiver.archive_working_directory(
            session_id=session_id,
            working_dir=Path(session.working_directory_path)
        )

        # 4. Update session with archive reference
        await self.session_repo.update(
            session_id,
            archive_id=archive_metadata.id,
            status=SessionStatus.ARCHIVED.value
        )

        # 5. Audit log
        await self.audit_service.log_session_archived(
            session_id=session_id,
            user_id=user_id,
            archive_path=archive_metadata.archive_path,
            size_bytes=archive_metadata.size_bytes
        )

        return archive_metadata

    async def retrieve_archive(
        self,
        session_id: UUID,
        user_id: UUID,
        extract_to: Optional[Path] = None
    ) -> Path:
        """Retrieve and extract archived working directory.

        Used for session resumption or inspection.
        """
        # Get session and verify ownership
        session = await self.get_session(session_id, user_id)

        if not session.archive_id:
            from app.domain.exceptions import ArchiveNotFoundError
            raise ArchiveNotFoundError(f"Session {session_id} has no archive")

        # Delegate to StorageArchiver
        from app.claude_sdk.persistence import StorageArchiver

        archiver = StorageArchiver()
        extracted_path = await archiver.retrieve_archive(
            session_id=session_id,
            extract_to=extract_to or Path(session.working_directory_path)
        )

        return extracted_path
```

### 5.2 Update TaskService (`app/services/task_service.py`)

Add method to link tasks with background sessions:

```python
class TaskService:
    """Business logic for task management and execution."""

    # ... existing methods ...

    async def execute_task_as_background_session(
        self,
        task_id: UUID,
        user_id: UUID,
        variables: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Execute a task as a background Claude SDK session.

        This is the new way to execute tasks using the SDK module's
        BackgroundExecutor instead of ad-hoc execution.

        Args:
            task_id: Task UUID
            user_id: User UUID
            variables: Optional template variables

        Returns:
            Background Session entity
        """
        # 1. Get task
        task = await self.get_task(task_id, user_id)

        # 2. Render prompt template with variables
        prompt = task.render_prompt(variables or {})

        # 3. Create background session
        from app.services.session_service import SessionService
        from app.domain.entities.session import SessionMode

        session_service = SessionService(
            db=self.db,
            session_repo=self.session_repo,
            # ... inject dependencies ...
        )

        session = await session_service.create_session(
            user_id=user_id,
            mode=SessionMode.BACKGROUND,
            sdk_options=task.sdk_options,
            name=f"Task: {task.name}"
        )

        # 4. Execute via new SDK module's BackgroundExecutor
        from app.claude_sdk.execution import ExecutorFactory
        from app.claude_sdk.core import EnhancedClaudeClient, ClientConfig

        client_config = ClientConfig(
            session_id=session.id,
            model=task.sdk_options.get("model", "claude-sonnet-4-5"),
            permission_mode="bypassPermissions",  # Background tasks don't need approval
            max_retries=3,
            # ... other config ...
        )

        client = EnhancedClaudeClient(client_config)
        executor = ExecutorFactory.create_executor(
            session=session,
            client=client,
            execution_mode="background"
        )

        # Execute (returns ExecutionResult, not streaming)
        result = await executor.execute(prompt)

        # 5. Create task execution record
        await self.task_execution_repo.create(
            task_id=task_id,
            session_id=session.id,
            status="completed" if result.success else "failed",
            result_data=result.data,
            error_message=result.error_message
        )

        # 6. Archive session if configured
        if task.sdk_options.get("auto_archive", True):
            await session_service.archive_session(session.id, user_id, upload_to_s3=True)

        return session
```

---

## 6. API Schemas (Pydantic) Changes

### 6.1 Update SessionCreateRequest (`app/schemas/session.py`)

```python
class SessionCreateRequest(BaseModel):
    """Create session request."""

    template_id: Optional[UUID] = Field(None, description="Session template ID")
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    # NEW: Session mode
    mode: Optional[str] = Field("interactive", description="Session mode: interactive, background, forked")

    # NEW: Parent session (for forking)
    parent_session_id: Optional[UUID] = Field(None, description="Parent session ID (for forking)")
    fork_at_message: Optional[int] = Field(None, description="Fork from message index")

    # Configuration
    working_directory: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    sdk_options: Optional[Dict[str, Any]] = None

    # NEW: Streaming configuration
    include_partial_messages: Optional[bool] = Field(False, description="Enable real-time streaming")

    # NEW: Retry configuration
    max_retries: Optional[int] = Field(3, description="Max retry attempts")
    retry_delay: Optional[float] = Field(2.0, description="Retry delay in seconds")
    timeout_seconds: Optional[int] = Field(120, description="Timeout in seconds")

    # NEW: Hooks configuration
    hooks_enabled: Optional[List[str]] = Field([], description="Enabled hook types")

    # NEW: Permission configuration
    permission_mode: Optional[str] = Field("default", description="Permission mode")
    custom_policies: Optional[List[str]] = Field([], description="Custom policy names")

    metadata: Optional[Dict[str, Any]] = None
```

### 6.2 Update SessionResponse (`app/schemas/session.py`)

```python
class SessionResponse(BaseModel):
    """Session response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Identity
    id: UUID
    user_id: UUID
    name: Optional[str]
    description: Optional[str]

    # NEW: Mode
    mode: str = Field(..., description="Session mode: interactive, background, forked")

    # State
    status: str

    # Configuration
    working_directory: str
    allowed_tools: List[str]
    system_prompt: Optional[str]
    sdk_options: Dict[str, Any]

    # NEW: Streaming
    include_partial_messages: bool

    # NEW: Retry
    max_retries: int
    retry_delay: float
    timeout_seconds: int

    # NEW: Hooks
    hooks_enabled: List[str]

    # NEW: Permissions
    permission_mode: str
    custom_policies: List[str]

    # Relationships
    parent_session_id: Optional[UUID]
    is_fork: bool

    # NEW: Archive
    archive_id: Optional[UUID] = Field(None, description="Archive UUID if archived")

    # NEW: Template
    template_id: Optional[UUID] = Field(None, description="Template UUID if created from template")

    # Metrics
    message_count: int
    tool_call_count: int

    # NEW: Enhanced metrics
    hook_execution_count: int = Field(..., alias="total_hook_executions")
    permission_check_count: int = Field(..., alias="total_permission_checks")
    error_count: int = Field(..., alias="total_errors")
    retry_count: int = Field(..., alias="total_retries")

    # Cost & tokens
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int

    # Timestamps
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    error_message: Optional[str]
    metadata: Dict[str, Any]
    links: Links = Field(default_factory=Links, alias="_links")
```

### 6.3 Create New Schemas

#### **HookExecutionResponse** (`app/schemas/session.py`)

```python
class HookExecutionResponse(BaseModel):
    """Hook execution response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    hook_type: str
    tool_use_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    continue_execution: bool
    executed_at: datetime
```

#### **PermissionDecisionResponse** (`app/schemas/session.py`)

```python
class PermissionDecisionResponse(BaseModel):
    """Permission decision response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    tool_name: str
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    decision: str  # 'allow' or 'deny'
    reason: Optional[str]
    interrupted: bool
    decided_at: datetime
```

#### **ArchiveMetadataResponse** (`app/schemas/session.py`)

```python
class ArchiveMetadataResponse(BaseModel):
    """Archive metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    archive_path: str
    size_bytes: int
    compression: str
    manifest: Dict[str, Any]
    status: str
    error_message: Optional[str]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

#### **SessionForkRequest** (`app/schemas/session.py`)

```python
class SessionForkRequest(BaseModel):
    """Fork session request."""

    name: Optional[str] = Field(None, description="Name for forked session")
    fork_at_message: Optional[int] = Field(None, description="Fork from message index (None = fork entire session)")
    include_working_directory: bool = Field(True, description="Copy working directory files")
```

#### **SessionArchiveRequest** (`app/schemas/session.py`)

```python
class SessionArchiveRequest(BaseModel):
    """Archive session request."""

    upload_to_s3: bool = Field(True, description="Upload to S3 storage")
    compression: str = Field("gzip", description="Compression format: gzip, zip, tar")
```

---

## 7. API Endpoints Updates

### 7.1 Update Sessions Router (`app/api/v1/sessions.py`)

Add new endpoints for forking, archiving, and enhanced queries:

```python
# NEW: Fork session endpoint
@router.post("/{session_id}/fork", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def fork_session(
    session_id: UUID,
    request: SessionForkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Fork an existing session.

    Creates a new session that:
    - Copies configuration from parent session
    - Optionally restores conversation context up to specific message
    - Creates new working directory (optionally copying files)
    - Links to parent session via parent_session_id

    Use cases:
    - Interactive investigation of background task results
    - Branching conversation to explore different paths
    - Creating session from specific point in history
    """
    # Initialize service
    session_service = SessionService(...)  # inject dependencies

    # Fork session
    forked_session = await session_service.fork_session(
        parent_session_id=session_id,
        user_id=current_user.id,
        fork_at_message=request.fork_at_message,
        name=request.name
    )

    # Build response
    response = SessionResponse.model_validate(forked_session)
    response._links = Links(
        self=f"/api/v1/sessions/{forked_session.id}",
        parent=f"/api/v1/sessions/{session_id}",
        messages=f"/api/v1/sessions/{forked_session.id}/messages",
    )

    return response


# NEW: Archive session endpoint
@router.post("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def archive_session(
    session_id: UUID,
    request: SessionArchiveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """
    Archive a session's working directory.

    Compresses and uploads the working directory to S3/storage.
    Only available for completed/failed/terminated sessions.

    After archiving, the local working directory can be cleaned up
    to save disk space. The archive can be retrieved later if needed.
    """
    session_service = SessionService(...)

    archive_metadata = await session_service.archive_session(
        session_id=session_id,
        user_id=current_user.id,
        upload_to_s3=request.upload_to_s3
    )

    return ArchiveMetadataResponse.model_validate(archive_metadata)


# NEW: Get archive info
@router.get("/{session_id}/archive", response_model=ArchiveMetadataResponse)
async def get_session_archive(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ArchiveMetadataResponse:
    """Get archive metadata for a session."""
    repo = WorkingDirectoryArchiveRepository(db)
    archive = await repo.get_by_session(session_id)

    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No archive found for session {session_id}"
        )

    return ArchiveMetadataResponse.model_validate(archive)


# NEW: Download archive
@router.get("/{session_id}/archive/download")
async def download_session_archive(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Download archived working directory as tar.gz file."""
    # Retrieve archive
    session_service = SessionService(...)
    extracted_path = await session_service.retrieve_archive(
        session_id=session_id,
        user_id=current_user.id
    )

    # Stream file
    return StreamingResponse(
        open(extracted_path, "rb"),
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={session_id}.tar.gz"}
    )


# NEW: Get hook executions
@router.get("/{session_id}/hooks", response_model=List[HookExecutionResponse])
async def get_session_hooks(
    session_id: UUID,
    hook_type: Optional[str] = Query(None, description="Filter by hook type"),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[HookExecutionResponse]:
    """
    Get hook execution history for a session.

    Returns all hook invocations with input/output data for audit trail.
    """
    repo = HookExecutionRepository(db)

    if hook_type:
        hooks = await repo.get_by_hook_type(session_id, hook_type, limit)
    else:
        hooks = await repo.get_by_session(session_id, limit)

    return [HookExecutionResponse.model_validate(h) for h in hooks]


# NEW: Get permission decisions
@router.get("/{session_id}/permissions", response_model=List[PermissionDecisionResponse])
async def get_session_permissions(
    session_id: UUID,
    decision: Optional[str] = Query(None, description="Filter by decision: allow, deny"),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[PermissionDecisionResponse]:
    """
    Get permission decision history for a session.

    Returns all permission checks with decisions for audit trail.
    Useful for understanding what tools were blocked and why.
    """
    repo = PermissionDecisionRepository(db)

    if decision == "deny":
        permissions = await repo.get_denied_permissions(session_id)
    else:
        permissions = await repo.get_by_session(session_id, limit)
        if decision == "allow":
            permissions = [p for p in permissions if p.decision == "allow"]

    return [PermissionDecisionResponse.model_validate(p) for p in permissions]


# NEW: Get metrics snapshots
@router.get("/{session_id}/metrics/history", response_model=List[Dict[str, Any]])
async def get_session_metrics_history(
    session_id: UUID,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """
    Get historical metrics snapshots for a session.

    Returns time-series metrics data for analytics and monitoring.
    Useful for tracking cost, token usage, and performance over time.
    """
    repo = SessionMetricsSnapshotRepository(db)
    snapshots = await repo.get_by_session(session_id, limit)

    return [
        {
            "snapshot_at": s.snapshot_at.isoformat(),
            "total_messages": s.total_messages,
            "total_tool_calls": s.total_tool_calls,
            "total_cost_usd": float(s.total_cost_usd),
            "total_input_tokens": s.total_input_tokens,
            "total_output_tokens": s.total_output_tokens,
            "duration_ms": s.duration_ms,
        }
        for s in snapshots
    ]


# UPDATE: Create session endpoint
# Modify to support new session modes and configuration
@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,  # Updated schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """
    Create a new session.

    Supports:
    - Interactive sessions (real-time chat)
    - Background sessions (automated tasks)
    - Forked sessions (continuation of existing session)
    - Session templates
    """
    # ... implementation using new SessionCreateRequest fields ...
```

---

## 8. Configuration Changes

### 8.1 Environment Variables

Add to `.env` file:

```bash
# Claude SDK Configuration
CLAUDE_SDK_DEFAULT_MODEL=claude-sonnet-4-5
CLAUDE_SDK_MAX_RETRIES=3
CLAUDE_SDK_RETRY_DELAY=2.0
CLAUDE_SDK_TIMEOUT_SECONDS=120
CLAUDE_SDK_DEFAULT_PERMISSION_MODE=default  # default, acceptEdits, bypassPermissions

# Storage Configuration
STORAGE_PROVIDER=s3  # 's3', 'minio', 'local'
AWS_S3_BUCKET=ai-agent-archives
AWS_S3_REGION=us-east-1
AWS_S3_ARCHIVE_PREFIX=archives/
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Archival Configuration
ARCHIVE_COMPRESSION=gzip  # gzip, zip, tar
ARCHIVE_AUTO_CLEANUP=true  # Delete local working dir after archive
ARCHIVE_RETENTION_DAYS=90  # Auto-delete archives after N days

# Session Limits
MAX_CONCURRENT_INTERACTIVE_SESSIONS=10
MAX_CONCURRENT_BACKGROUND_SESSIONS=50
SESSION_IDLE_TIMEOUT_MINUTES=30
SESSION_AUTO_ARCHIVE_DAYS=180

# Metrics & Monitoring
ENABLE_METRICS_COLLECTION=true
METRICS_SNAPSHOT_INTERVAL_SECONDS=60
ENABLE_COST_TRACKING=true
USER_MONTHLY_BUDGET_USD=100.0

# Hooks Configuration
ENABLE_AUDIT_HOOK=true
ENABLE_METRICS_HOOK=true
ENABLE_PERSISTENCE_HOOK=true
ENABLE_NOTIFICATION_HOOK=true
ENABLE_CUSTOM_HOOKS=true

# Permissions Configuration
ENABLE_CUSTOM_POLICIES=true
DEFAULT_BLOCKED_COMMANDS=rm -rf,sudo rm,format,dd
DEFAULT_RESTRICTED_PATHS=/etc/passwd,/etc/shadow,~/.ssh,~/.aws/credentials
```

### 8.2 Update Config Class (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application configuration."""

    # ... existing settings ...

    # NEW: Claude SDK settings
    claude_sdk_default_model: str = "claude-sonnet-4-5"
    claude_sdk_max_retries: int = 3
    claude_sdk_retry_delay: float = 2.0
    claude_sdk_timeout_seconds: int = 120
    claude_sdk_default_permission_mode: str = "default"

    # NEW: Storage settings
    storage_provider: str = "s3"  # 's3', 'minio', 'local'
    aws_s3_bucket: str = "ai-agent-archives"
    aws_s3_region: str = "us-east-1"
    aws_s3_archive_prefix: str = "archives/"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # NEW: Archival settings
    archive_compression: str = "gzip"
    archive_auto_cleanup: bool = True
    archive_retention_days: int = 90

    # NEW: Session limits
    max_concurrent_interactive_sessions: int = 10
    max_concurrent_background_sessions: int = 50
    session_idle_timeout_minutes: int = 30
    session_auto_archive_days: int = 180

    # NEW: Metrics settings
    enable_metrics_collection: bool = True
    metrics_snapshot_interval_seconds: int = 60
    enable_cost_tracking: bool = True
    user_monthly_budget_usd: float = 100.0

    # NEW: Hooks settings
    enable_audit_hook: bool = True
    enable_metrics_hook: bool = True
    enable_persistence_hook: bool = True
    enable_notification_hook: bool = True
    enable_custom_hooks: bool = True

    # NEW: Permissions settings
    enable_custom_policies: bool = True
    default_blocked_commands: List[str] = ["rm -rf", "sudo rm", "format", "dd"]
    default_restricted_paths: List[str] = ["/etc/passwd", "/etc/shadow", "~/.ssh", "~/.aws/credentials"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## 9. Dependencies & Initialization

### 9.1 Update Dependencies (`app/api/dependencies.py`)

Add dependency injection for new SDK components:

```python
from app.claude_sdk.core import SessionManager, EnhancedClaudeClient
from app.claude_sdk.hooks import HookManager
from app.claude_sdk.permissions import PermissionManager
from app.claude_sdk.persistence import StorageArchiver
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.repositories.working_directory_archive_repository import WorkingDirectoryArchiveRepository


async def get_session_manager(
    db: AsyncSession = Depends(get_db_session)
) -> SessionManager:
    """Get Session Manager instance."""
    return SessionManager(db)


async def get_hook_manager(
    db: AsyncSession = Depends(get_db_session)
) -> HookManager:
    """Get Hook Manager instance."""
    return HookManager(db)


async def get_permission_manager(
    db: AsyncSession = Depends(get_db_session)
) -> PermissionManager:
    """Get Permission Manager instance."""
    return PermissionManager(db)


async def get_storage_archiver() -> StorageArchiver:
    """Get Storage Archiver instance."""
    from app.core.config import settings
    return StorageArchiver(
        provider=settings.storage_provider,
        bucket=settings.aws_s3_bucket,
        region=settings.aws_s3_region
    )


async def get_hook_execution_repo(
    db: AsyncSession = Depends(get_db_session)
) -> HookExecutionRepository:
    """Get Hook Execution Repository."""
    return HookExecutionRepository(db)


async def get_permission_decision_repo(
    db: AsyncSession = Depends(get_db_session)
) -> PermissionDecisionRepository:
    """Get Permission Decision Repository."""
    return PermissionDecisionRepository(db)


async def get_archive_repo(
    db: AsyncSession = Depends(get_db_session)
) -> WorkingDirectoryArchiveRepository:
    """Get Working Directory Archive Repository."""
    return WorkingDirectoryArchiveRepository(db)
```

---

## 10. Migration Strategy

### 10.1 Phased Migration Approach

#### **Phase 1: Database Migration (Week 1)**
- [ ] Create Alembic migration for new tables and columns
- [ ] Test migration on staging database
- [ ] Run migration on production with zero downtime
- [ ] Verify schema changes

#### **Phase 2: Models & Repositories (Week 1-2)**
- [ ] Create new ORM models
- [ ] Create new repositories
- [ ] Update existing models with new columns
- [ ] Update existing repositories with new methods
- [ ] Write unit tests for repositories

#### **Phase 3: Domain Layer (Week 2)**
- [ ] Update Session entity with new fields and methods
- [ ] Create new domain entities (HookExecution, PermissionDecision, ArchiveMetadata)
- [ ] Update domain exceptions if needed
- [ ] Write unit tests for domain logic

#### **Phase 4: API Schemas (Week 2-3)**
- [ ] Update request/response schemas
- [ ] Create new schemas for hooks, permissions, archives
- [ ] Update API documentation
- [ ] Test schema validation

#### **Phase 5: Service Layer (Week 3-4)**
- [ ] Update SessionService with forking and archiving methods
- [ ] Update TaskService to use background sessions
- [ ] Integrate with new claude_sdk module
- [ ] Write integration tests

#### **Phase 6: API Endpoints (Week 4-5)**
- [ ] Add new endpoints (fork, archive, hooks, permissions)
- [ ] Update existing endpoints to support new fields
- [ ] Update OpenAPI documentation
- [ ] Write API integration tests

#### **Phase 7: Configuration & Deployment (Week 5)**
- [ ] Update .env configuration
- [ ] Update Settings class
- [ ] Configure S3 storage
- [ ] Test end-to-end workflows

#### **Phase 8: Testing & Validation (Week 6)**
- [ ] Run full test suite
- [ ] Perform load testing
- [ ] Test session forking workflow
- [ ] Test archival and retrieval
- [ ] Test hooks and permissions audit trail

### 10.2 Backward Compatibility

**Maintain compatibility during migration**:

1. **Database**: New columns have defaults, old sessions work unchanged
2. **API**: Existing endpoints unchanged, new fields optional in requests
3. **Services**: Old service methods still work, new methods added
4. **Mode field**: Defaults to "interactive" for existing sessions

**Breaking changes** (if any):
- None expected - all changes are additive

### 10.3 Rollback Plan

If issues arise:

1. **Database rollback**:
   ```bash
   poetry run alembic downgrade -1
   ```

2. **Code rollback**: Revert git commits
3. **Data consistency**: New tables can be truncated without affecting existing data
4. **Archive cleanup**: S3 archives are separate, can be deleted if needed

---

## 11. Testing Checklist

### 11.1 Unit Tests

- [ ] Session entity methods (fork, archive, metrics)
- [ ] Domain entities (HookExecution, PermissionDecision, ArchiveMetadata)
- [ ] Repositories (CRUD operations, queries)
- [ ] Service methods (fork_session, archive_session)

### 11.2 Integration Tests

- [ ] Database schema changes
- [ ] Repository queries with new columns
- [ ] Service layer integration with new SDK module
- [ ] API endpoints (fork, archive, hooks, permissions)

### 11.3 E2E Tests

- [ ] Interactive session workflow (create, query, fork)
- [ ] Background session workflow (create, execute, archive)
- [ ] Session forking from completed session
- [ ] Archive and retrieval workflow
- [ ] Hooks audit trail
- [ ] Permission decisions audit trail

### 11.4 Performance Tests

- [ ] Concurrent session creation
- [ ] Archive upload/download speed
- [ ] Metrics snapshot insertion rate
- [ ] Hook execution overhead
- [ ] Permission check overhead

---

## 12. Documentation Updates

### 12.1 API Documentation

- [ ] Update OpenAPI/Swagger docs
- [ ] Document new endpoints
- [ ] Add example requests/responses
- [ ] Update Postman collection

### 12.2 Developer Documentation

- [ ] Update CLAUDE.md with new features
- [ ] Update README.md
- [ ] Create migration guide
- [ ] Document new environment variables

### 12.3 User Documentation

- [ ] Explain session modes (interactive, background, forked)
- [ ] Document session forking use cases
- [ ] Explain archival and retrieval
- [ ] Document hooks and permissions audit trail

---

## Summary

This migration guide provides a **complete roadmap** for integrating the new Claude SDK module architecture with the existing ai-agent-api codebase. The changes are **additive and backward-compatible**, allowing for a phased migration with zero downtime.

**Key Benefits**:
- ✅ Enhanced session management (forking, archival)
- ✅ Comprehensive audit trails (hooks, permissions)
- ✅ Production-ready resilience (retry, monitoring)
- ✅ Storage archival to S3
- ✅ Advanced metrics tracking
- ✅ Support for multiple session modes

**Estimated Timeline**: 6 weeks for complete migration and testing.

**Next Steps**: Review this document, prioritize phases, and begin Phase 1 (Database Migration).
