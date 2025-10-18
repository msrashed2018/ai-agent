"""Session service for business logic."""
from typing import Optional, AsyncIterator
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

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
        workdir = await self.storage_manager.create_working_directory(session.id)
        session.working_directory_path = str(workdir)

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
        return session

    async def get_session(self, session_id: UUID, user_id: UUID) -> Session:
        """Get session by ID with authorization check."""
        session_model = await self.session_repo.get_by_id(session_id)
        if not session_model:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Check authorization - simple ownership check
        # Admin users can access all sessions, regular users only their own
        user_model = await self.user_repo.get_by_id(user_id)
        if session_model.user_id != user_id and user_model.role != "admin":
            raise PermissionDeniedError("Not authorized to access this session")

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
