"""Session service for business logic."""
from typing import Optional, AsyncIterator
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.entities.session import Session, SessionStatus, SessionMode
from app.domain.value_objects.message import Message, MessageType
from app.domain.value_objects.tool_call import ToolCall, ToolCallStatus
from app.domain.exceptions import (
    SessionNotFoundError,
    SessionNotActiveError,
    SessionCannotResumeError,
    PermissionDeniedError,
    QuotaExceededError,
)
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.tool_call_repository import ToolCallRepository
from app.repositories.user_repository import UserRepository
from app.services.storage_manager import StorageManager
from app.services.audit_service import AuditService


logger = get_logger(__name__)


class SessionService:
    """Business logic for session management."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        tool_call_repo: ToolCallRepository,
        user_repo: UserRepository,
        storage_manager: StorageManager,
        audit_service: AuditService,
    ):
        self.db = db
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.tool_call_repo = tool_call_repo
        self.user_repo = user_repo
        self.storage_manager = storage_manager
        self.audit_service = audit_service

    async def create_session(
        self,
        user_id: UUID,
        mode: SessionMode,
        sdk_options: dict,
        name: Optional[str] = None,
        parent_session_id: Optional[UUID] = None,
    ) -> Session:
        """Create and initialize a new session."""
        logger.info(
            f"Starting session creation",
            extra={
                "user_id": str(user_id),
                "mode": mode.value,
                "name": name,
                "parent_session_id": str(parent_session_id) if parent_session_id else None,
                "sdk_options_keys": list(sdk_options.keys()) if sdk_options else []
            }
        )
        
        # 1. Validate user quotas
        await self._validate_user_quotas(user_id)

        # 2. Create session entity
        session = Session(
            id=uuid4(),
            user_id=user_id,
            mode=mode,
            sdk_options=sdk_options,
            name=name,
        )

        if parent_session_id:
            session.parent_session_id = parent_session_id
            session.is_fork = True

        # 3. Create working directory
        logger.debug(f"Creating working directory for session {session.id}")
        workdir = await self.storage_manager.create_working_directory(session.id)
        session.working_directory_path = str(workdir)
        logger.info(
            f"Working directory created",
            extra={
                "session_id": str(session.id),
                "working_directory": str(workdir)
            }
        )

        # 4. Persist session (convert domain entity to model)
        from app.models.session import SessionModel
        session_model = SessionModel(
            id=session.id,
            user_id=session.user_id,
            name=session.name,
            mode=session.mode.value,
            status=session.status.value,
            sdk_options=session.sdk_options,
            working_directory_path=session.working_directory_path,
            parent_session_id=session.parent_session_id,
            is_fork=session.is_fork,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        self.db.add(session_model)
        await self.db.flush()

        # 5. Audit log
        await self.audit_service.log_session_created(
            session_id=session.id,
            user_id=user_id,
            mode=mode.value,
            sdk_options=sdk_options,
        )

        await self.db.commit()
        
        logger.info(
            f"Session created successfully",
            extra={
                "session_id": str(session.id),
                "user_id": str(user_id),
                "mode": mode.value,
                "name": name,
                "working_directory": session.working_directory_path
            }
        )
        
        return session

    async def get_session(self, session_id: UUID, user_id: UUID) -> Session:
        """Get session by ID with authorization check."""
        logger.debug(
            f"Getting session",
            extra={
                "session_id": str(session_id),
                "user_id": str(user_id)
            }
        )
        
        session_model = await self.session_repo.get_by_id(session_id)
        if not session_model:
            logger.warning(
                f"Session not found",
                extra={
                    "session_id": str(session_id),
                    "user_id": str(user_id)
                }
            )
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Check authorization - simple ownership check
        # Admin users can access all sessions, regular users only their own
        user_model = await self.user_repo.get_by_id(user_id)
        if session_model.user_id != user_id and user_model.role != "admin":
            logger.warning(
                f"Unauthorized session access attempt",
                extra={
                    "session_id": str(session_id),
                    "requesting_user_id": str(user_id),
                    "session_owner_id": str(session_model.user_id),
                    "user_role": user_model.role if user_model else "unknown"
                }
            )
            raise PermissionDeniedError("Not authorized to access this session")

        logger.debug(
            f"Session retrieved successfully",
            extra={
                "session_id": str(session_id),
                "session_status": session_model.status,
                "session_mode": session_model.mode
            }
        )

        # Convert model to domain entity
        return self._model_to_entity(session_model)

    async def list_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Session]:
        """List all sessions for a user."""
        session_models = await self.session_repo.get_by_user(user_id, skip, limit)
        return [self._model_to_entity(model) for model in session_models]

    async def get_active_sessions(self, user_id: UUID) -> list[Session]:
        """Get all active sessions for a user."""
        session_models = await self.session_repo.get_active_sessions(user_id)
        return [self._model_to_entity(model) for model in session_models]

    async def transition_status(
        self,
        session_id: UUID,
        user_id: UUID,
        new_status: SessionStatus,
    ) -> Session:
        """Transition session to new status."""
        session = await self.get_session(session_id, user_id)
        
        # Validate and perform transition
        session.transition_to(new_status)
        
        # Update in database
        await self.session_repo.update(
            session_id,
            status=new_status.value,
            updated_at=datetime.utcnow(),
            started_at=session.started_at,
            completed_at=session.completed_at,
            duration_ms=session.duration_ms,
        )
        
        await self.db.commit()
        return session

    async def pause_session(self, session_id: UUID, user_id: UUID) -> Session:
        """Pause an active session."""
        return await self.transition_status(session_id, user_id, SessionStatus.PAUSED)

    async def resume_session(
        self,
        session_id: UUID,
        user_id: UUID,
        fork: bool = False,
    ) -> Session:
        """Resume a paused/completed session or fork it."""
        original_model = await self.session_repo.get_by_id(session_id)
        if not original_model:
            raise SessionNotFoundError(f"Session {session_id} not found")

        original = self._model_to_entity(original_model)

        # Check authorization
        if original.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError()

        if fork:
            # Create new forked session
            return await self.create_session(
                user_id=user_id,
                mode=original.mode,
                sdk_options=original.sdk_options,
                name=f"{original.name} (fork)" if original.name else "Forked session",
                parent_session_id=original.id,
            )
        else:
            # Resume existing session
            if original.is_terminal():
                raise SessionCannotResumeError("Cannot resume terminal session")
            return await self.transition_status(session_id, user_id, SessionStatus.ACTIVE)

    async def terminate_session(
        self,
        session_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> Session:
        """Terminate a session."""
        session = await self.transition_status(session_id, user_id, SessionStatus.TERMINATED)
        
        # Audit log
        await self.audit_service.log_session_terminated(
            session_id=session_id,
            user_id=user_id,
            reason=reason,
        )
        
        await self.db.commit()
        return session

    async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """Soft delete a session."""
        session = await self.get_session(session_id, user_id)
        
        # Archive working directory if exists
        if session.working_directory_path:
            await self.storage_manager.archive_working_directory(session_id)
        
        # Soft delete
        success = await self.session_repo.soft_delete(session_id)
        await self.db.commit()
        
        return success

    async def get_session_messages(
        self,
        session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        """Get all messages for a session."""
        # Verify access
        await self.get_session(session_id, user_id)
        
        message_models = await self.message_repo.get_by_session(session_id, skip, limit)
        return [self._message_model_to_value_object(model) for model in message_models]

    async def get_session_tool_calls(
        self,
        session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ToolCall]:
        """Get all tool calls for a session."""
        # Verify access
        await self.get_session(session_id, user_id)
        
        tool_call_models = await self.tool_call_repo.get_by_session(session_id, skip, limit)
        return [self._tool_call_model_to_value_object(model) for model in tool_call_models]

    async def _validate_user_quotas(self, user_id: UUID) -> None:
        """Validate user hasn't exceeded quotas."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise PermissionDeniedError("User not found")

        active_count = await self.session_repo.count_active_sessions(user_id)
        
        if active_count >= user.max_concurrent_sessions:
            await self.audit_service.log_quota_exceeded(
                user_id=user_id,
                quota_type="concurrent_sessions",
                current_value=active_count,
                limit=user.max_concurrent_sessions,
            )
            raise QuotaExceededError(
                f"User has {active_count} active sessions (limit: {user.max_concurrent_sessions})"
            )

    def _model_to_entity(self, model) -> Session:
        """Convert database model to domain entity."""
        session = Session(
            id=model.id,
            user_id=model.user_id,
            mode=SessionMode(model.mode),
            sdk_options=model.sdk_options,
            name=model.name,
            status=SessionStatus(model.status),
        )
        
        # Set additional attributes
        session.working_directory_path = model.working_directory_path
        session.parent_session_id = model.parent_session_id
        session.is_fork = model.is_fork
        session.total_messages = model.total_messages
        session.total_tool_calls = model.total_tool_calls
        session.total_cost_usd = float(model.total_cost_usd) if model.total_cost_usd else 0.0
        session.duration_ms = model.duration_ms
        session.api_input_tokens = model.api_input_tokens
        session.api_output_tokens = model.api_output_tokens
        session.api_cache_creation_tokens = model.api_cache_creation_tokens
        session.api_cache_read_tokens = model.api_cache_read_tokens
        session.result_data = model.result_data
        session.error_message = model.error_message
        session.created_at = model.created_at
        session.updated_at = model.updated_at
        session.started_at = model.started_at
        session.completed_at = model.completed_at
        session.deleted_at = model.deleted_at
        
        return session

    def _message_model_to_value_object(self, model) -> Message:
        """Convert message model to value object."""
        return Message(
            id=model.id,
            session_id=model.session_id,
            message_type=MessageType(model.message_type),
            content=model.content,
            sequence_number=model.sequence_number,
            created_at=model.created_at,
            model=model.model,
            parent_tool_use_id=model.parent_tool_use_id,
        )

    def _tool_call_model_to_value_object(self, model) -> ToolCall:
        """Convert tool call model to value object."""
        from app.domain.value_objects.tool_call import PermissionDecision

        return ToolCall(
            id=model.id,
            session_id=model.session_id,
            tool_name=model.tool_name,
            tool_use_id=model.tool_use_id,
            tool_input=model.tool_input,
            status=ToolCallStatus(model.status),
            created_at=model.created_at,
            message_id=model.message_id,
            tool_output=model.tool_output,
            is_error=model.is_error,
            error_message=model.error_message,
            permission_decision=PermissionDecision(model.permission_decision) if model.permission_decision else None,
            permission_reason=model.permission_reason,
            started_at=model.started_at,
            completed_at=model.completed_at,
            duration_ms=model.duration_ms,
        )

    async def fork_session_advanced(
        self,
        parent_session_id: UUID,
        user_id: UUID,
        fork_at_message: Optional[int] = None,
        name: Optional[str] = None
    ) -> Session:
        """Fork an existing session with advanced options."""
        from pathlib import Path
        import shutil

        # Get parent session
        parent = await self.get_session(parent_session_id, user_id)

        # Create forked session
        forked_session = await self.create_session(
            user_id=user_id,
            mode=SessionMode.FORKED,
            sdk_options=parent.sdk_options,
            name=name or f"{parent.name} (fork)" if parent.name else "Forked session",
            parent_session_id=parent.id,
        )

        # Copy working directory if exists
        if parent.working_directory_path and Path(parent.working_directory_path).exists():
            try:
                parent_workdir = Path(parent.working_directory_path)
                forked_workdir = Path(forked_session.working_directory_path)

                # Copy all files from parent to forked session
                for item in parent_workdir.rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(parent_workdir)
                        dest_path = forked_workdir / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest_path)

                logger.info(
                    f"Copied working directory from parent {parent_session_id} to forked session {forked_session.id}"
                )
            except Exception as e:
                logger.error(f"Failed to copy working directory: {e}")

        # Log fork action
        await self.audit_service.log_session_forked(
            session_id=forked_session.id,
            parent_session_id=parent.id,
            user_id=user_id,
            fork_at_message=fork_at_message,
        )

        await self.db.commit()
        return forked_session

    async def archive_session_to_storage(
        self,
        session_id: UUID,
        user_id: UUID,
        upload_to_s3: bool = True
    ):
        """Archive a session's working directory to storage."""
        from pathlib import Path
        from app.claude_sdk.persistence.storage_archiver import StorageArchiver
        from app.core.config import settings

        # Get session
        session = await self.get_session(session_id, user_id)

        if not session.working_directory_path:
            raise ValueError(f"Session {session_id} has no working directory")

        workdir = Path(session.working_directory_path)
        if not workdir.exists():
            raise ValueError(f"Working directory {workdir} does not exist")

        # Create archiver
        provider = "s3" if upload_to_s3 and settings.storage_provider == "s3" else "filesystem"
        archiver = StorageArchiver(
            provider=provider,
            bucket=settings.aws_s3_bucket if provider == "s3" else None,
            region=settings.aws_s3_region if provider == "s3" else None
        )

        # Archive working directory
        archive_metadata = await archiver.archive_working_directory(
            session_id=session.id,
            working_dir=workdir
        )

        # Persist archive metadata to database
        from app.repositories.working_directory_archive_repository import (
            WorkingDirectoryArchiveRepository
        )
        archive_repo = WorkingDirectoryArchiveRepository(self.db)
        await archive_repo.create(
            session_id=session.id,
            archive_path=archive_metadata.archive_path,
            size_bytes=archive_metadata.size_bytes,
            compression=archive_metadata.compression,
            manifest=archive_metadata.manifest,
            status=archive_metadata.status.value,
            archived_at=archive_metadata.archived_at,
        )

        # Log archival
        await self.audit_service.log_session_archived(
            session_id=session.id,
            user_id=user_id,
            archive_path=archive_metadata.archive_path,
            size_bytes=archive_metadata.size_bytes,
        )

        await self.db.commit()
        return archive_metadata

    async def retrieve_archive(
        self,
        session_id: UUID,
        user_id: UUID,
        extract_to: Optional[Path] = None
    ) -> Path:
        """Retrieve and extract archived working directory."""
        from pathlib import Path
        from app.claude_sdk.persistence.storage_archiver import StorageArchiver
        from app.repositories.working_directory_archive_repository import (
            WorkingDirectoryArchiveRepository
        )

        # Verify access
        session = await self.get_session(session_id, user_id)

        # Get archive metadata
        archive_repo = WorkingDirectoryArchiveRepository(self.db)
        archives = await archive_repo.get_by_session(str(session_id))

        if not archives:
            raise ValueError(f"No archive found for session {session_id}")

        archive = archives[0]  # Get most recent archive

        # Create archiver
        from app.core.config import settings
        archiver = StorageArchiver(
            provider=settings.storage_provider,
            bucket=settings.aws_s3_bucket if settings.storage_provider == "s3" else None,
            region=settings.aws_s3_region if settings.storage_provider == "s3" else None
        )

        # Determine extraction path
        if not extract_to:
            extract_to = Path(session.working_directory_path or f"/tmp/session-{session_id}")

        # Retrieve and extract archive
        extracted_path = await archiver.retrieve_archive(
            session_id=session.id,
            extract_to=extract_to
        )

        return extracted_path
