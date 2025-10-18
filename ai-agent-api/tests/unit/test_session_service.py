"""Unit tests for SessionService."""

import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.session_service import SessionService
from app.domain.entities.session import Session, SessionStatus, SessionMode
from app.domain.value_objects.sdk_options import SDKOptions
from app.domain.exceptions import (
    SessionNotFoundError,
    QuotaExceededError,
    PermissionDeniedError,
)
from app.models.session import SessionModel


class TestSessionService:
    """Test cases for SessionService."""

    @pytest.fixture
    def session_service(self, db_session, mock_storage_manager, mock_audit_service):
        """Create SessionService with mocked dependencies."""
        from app.repositories.session_repository import SessionRepository
        from app.repositories.message_repository import MessageRepository
        from app.repositories.tool_call_repository import ToolCallRepository
        from app.repositories.user_repository import UserRepository
        
        return SessionService(
            db=db_session,
            session_repo=SessionRepository(db_session),
            message_repo=MessageRepository(db_session),
            tool_call_repo=ToolCallRepository(db_session),
            user_repo=UserRepository(db_session),
            storage_manager=mock_storage_manager,
            audit_service=mock_audit_service,
        )

    @pytest.mark.asyncio
    async def test_create_session_success(
        self,
        session_service,
        test_user,
        mock_storage_manager,
        mock_audit_service,
    ):
        """Test successful session creation."""
        # Arrange
        user_id = test_user.id
        mode = SessionMode.INTERACTIVE
        sdk_options = {
            "model": "claude-sonnet-4-5",
            "max_turns": 10,
            "permission_mode": "default",
        }
        
        mock_storage_manager.create_working_directory.return_value = "/tmp/test-workdir"
        
        # Act
        session = await session_service.create_session(
            user_id=user_id,
            mode=mode,
            sdk_options=sdk_options,
            name="Test Session",
        )
        
        # Assert
        assert session is not None
        assert session.user_id == user_id
        assert session.mode == mode
        assert session.status == SessionStatus.CREATED
        assert session.name == "Test Session"
        assert session.working_directory_path == "/tmp/test-workdir"
        
        # Verify storage manager was called
        mock_storage_manager.create_working_directory.assert_called_once()
        
        # Verify audit logging
        mock_audit_service.log_session_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_quota_exceeded(
        self,
        session_service,
        test_user,
        db_session,
    ):
        """Test session creation fails when quota exceeded."""
        # Arrange - Create multiple sessions to exceed quota
        user_id = test_user.id
        
        # Create 5 active sessions (assuming quota is 5)
        for i in range(5):
            session = SessionModel(
                id=uuid4(),
                user_id=user_id,
                name=f"Session {i}",
                mode="interactive",
                status="active",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/session-{i}",
            )
            db_session.add(session)
        await db_session.commit()
        
        # Act & Assert
        with pytest.raises(QuotaExceededError):
            await session_service.create_session(
                user_id=user_id,
                mode=SessionMode.INTERACTIVE,
                sdk_options={"model": "claude-sonnet-4-5"},
            )

    @pytest.mark.asyncio
    async def test_get_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
    ):
        """Test successful session retrieval."""
        # Act
        session = await session_service.get_session(
            session_id=str(test_session_model.id),
            user_id=test_user.id,
        )
        
        # Assert
        assert session is not None
        assert session.id == test_session_model.id
        assert session.user_id == test_user.id
        assert session.name == test_session_model.name

    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self,
        session_service,
        test_user,
    ):
        """Test session retrieval with non-existent session."""
        # Act & Assert
        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session_id=str(uuid4()),
                user_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_session_permission_denied(
        self,
        session_service,
        test_session_model,
    ):
        """Test session retrieval with different user."""
        # Act & Assert
        with pytest.raises(PermissionDeniedError):
            await session_service.get_session(
                session_id=str(test_session_model.id),
                user_id=uuid4(),  # Different user
            )

    @pytest.mark.asyncio
    async def test_list_sessions(
        self,
        session_service,
        test_user,
        db_session,
    ):
        """Test listing user sessions."""
        # Arrange - Create multiple sessions
        session_ids = []
        for i in range(3):
            session = SessionModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Session {i}",
                mode="interactive",
                status="created",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/session-{i}",
            )
            db_session.add(session)
            session_ids.append(session.id)
        await db_session.commit()
        
        # Act
        sessions = await session_service.list_sessions(
            user_id=test_user.id,
            limit=10,
            offset=0,
        )
        
        # Assert
        assert len(sessions) == 3
        assert all(s.user_id == test_user.id for s in sessions)

    @pytest.mark.asyncio
    async def test_pause_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
        db_session,
    ):
        """Test successful session pausing."""
        # Arrange - Set session to active
        test_session_model.status = "active"
        await db_session.commit()
        
        # Act
        session = await session_service.pause_session(
            session_id=str(test_session_model.id),
            user_id=test_user.id,
        )
        
        # Assert
        assert session.status == SessionStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
        db_session,
    ):
        """Test successful session resuming."""
        # Arrange - Set session to paused
        test_session_model.status = "paused"
        await db_session.commit()
        
        # Act
        session = await session_service.resume_session(
            session_id=str(test_session_model.id),
            user_id=test_user.id,
        )
        
        # Assert
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_terminate_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
    ):
        """Test successful session termination."""
        # Act
        session = await session_service.terminate_session(
            session_id=str(test_session_model.id),
            user_id=test_user.id,
        )
        
        # Assert
        assert session.status == SessionStatus.TERMINATED

    @pytest.mark.asyncio
    async def test_delete_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
    ):
        """Test successful session deletion."""
        # Act
        result = await session_service.delete_session(
            session_id=str(test_session_model.id),
            user_id=test_user.id,
        )
        
        # Assert
        assert result is True
        
        # Verify session is soft-deleted
        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session_id=str(test_session_model.id),
                user_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_validate_user_quotas_within_limits(
        self,
        session_service,
        test_user,
        db_session,
    ):
        """Test quota validation when within limits."""
        # Arrange - Create 2 active sessions (under limit)
        for i in range(2):
            session = SessionModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Session {i}",
                mode="interactive",
                status="active",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/session-{i}",
            )
            db_session.add(session)
        await db_session.commit()
        
        # Act - Should not raise exception
        await session_service._validate_user_quotas(test_user.id)

    @pytest.mark.asyncio
    async def test_get_active_sessions(
        self,
        session_service,
        test_user,
        db_session,
    ):
        """Test getting active sessions for user."""
        # Arrange
        active_sessions = []
        for i in range(2):
            session = SessionModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Active Session {i}",
                mode="interactive",
                status="active",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/active-{i}",
            )
            db_session.add(session)
            active_sessions.append(session)
        
        # Add paused session (should not be included)
        paused_session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Paused Session",
            mode="interactive",
            status="paused",
            sdk_options={"model": "claude-sonnet-4-5"},
            working_directory_path="/tmp/paused",
        )
        db_session.add(paused_session)
        await db_session.commit()
        
        # Act
        active = await session_service.get_active_sessions(test_user.id)
        
        # Assert
        assert len(active) == 2
        assert all(s.status == SessionStatus.ACTIVE for s in active)

    @pytest.mark.asyncio
    async def test_fork_session_success(
        self,
        session_service,
        test_session_model,
        test_user,
        mock_storage_manager,
    ):
        """Test successful session forking."""
        # Arrange
        mock_storage_manager.create_working_directory.return_value = "/tmp/fork-workdir"
        
        # Act
        forked_session = await session_service.fork_session(
            str(test_session_model.id)
        )
        
        # Assert
        assert forked_session.parent_session_id == test_session_model.id
        assert forked_session.is_fork is True
        assert forked_session.user_id == test_session_model.user_id
        assert forked_session.mode.value == test_session_model.mode
        assert forked_session.id != test_session_model.id
        
        # Verify new working directory created
        mock_storage_manager.create_working_directory.assert_called()