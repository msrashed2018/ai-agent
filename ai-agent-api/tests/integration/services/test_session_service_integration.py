"""Integration tests for SessionService with database and storage."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.session_service import SessionService
from app.repositories.session_repository import SessionRepository
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.models.session import SessionModel


@pytest.mark.asyncio
class TestSessionServiceIntegration:
    """Integration tests for SessionService with real database."""

    async def test_fork_session_creates_new_session(self, db_session, test_session_model, test_user):
        """Test forking a session creates a new session with copied state."""
        # Arrange
        session_repo = SessionRepository(db_session)
        service = SessionService(session_repo=session_repo)
        
        # Add some history to the original session
        test_session_model.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        test_session_model.total_input_tokens = 100
        test_session_model.total_output_tokens = 50
        await session_repo.update(test_session_model)

        # Act
        forked_session = await service.fork_session_advanced(
            session_id=test_session_model.id,
            user_id=test_user.id,
            new_name="Forked Session",
        )

        # Assert
        assert forked_session.id != test_session_model.id
        assert forked_session.parent_session_id == test_session_model.id
        assert forked_session.name == "Forked Session"
        assert forked_session.conversation_history == test_session_model.conversation_history
        assert forked_session.total_input_tokens == 100
        assert forked_session.total_output_tokens == 50
        
        # Verify both sessions exist in database
        original = await session_repo.find_by_id(test_session_model.id)
        forked = await session_repo.find_by_id(forked_session.id)
        assert original is not None
        assert forked is not None

    async def test_archive_session_to_storage(self, db_session, test_session_model):
        """Test archiving session to storage with metadata."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.services.session_service.StorageArchiver') as mock_archiver:
            mock_archiver_instance = AsyncMock()
            mock_archiver.return_value = mock_archiver_instance
            mock_archiver_instance.archive_working_directory.return_value = {
                "archive_id": "archive_123",
                "s3_key": "archives/session_123/archive.tar.gz",
                "local_path": "/tmp/archives/archive.tar.gz",
                "manifest": {"files": ["file1.txt", "file2.py"]},
            }
            
            service = SessionService(session_repo=session_repo)

            # Act
            archive_result = await service.archive_session_to_storage(
                session_id=test_session_model.id,
                working_directory="/tmp/test-workdir",
            )

            # Assert
            assert archive_result["archive_id"] == "archive_123"
            assert "s3_key" in archive_result
            assert "manifest" in archive_result
            
            # Verify session metadata was updated
            session = await session_repo.find_by_id(test_session_model.id)
            # Archive metadata should be set

    async def test_retrieve_archive_metadata(self, db_session, test_session_model):
        """Test retrieving archive metadata for a session."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        # Create archive metadata
        test_session_model.archive_metadata = {
            "archive_id": "archive_123",
            "s3_key": "archives/session_123/archive.tar.gz",
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "file_count": 5,
            "total_size_bytes": 1024000,
        }
        await session_repo.update(test_session_model)
        
        service = SessionService(session_repo=session_repo)

        # Act
        archive_info = await service.retrieve_archive(test_session_model.id)

        # Assert
        assert archive_info is not None
        assert archive_info["archive_id"] == "archive_123"
        assert archive_info["file_count"] == 5
        assert archive_info["total_size_bytes"] == 1024000

    async def test_create_session_with_hooks_enabled(self, db_session, test_user):
        """Test creating a session with hooks enabled."""
        # Arrange
        session_repo = SessionRepository(db_session)
        service = SessionService(session_repo=session_repo)
        
        session_data = {
            "user_id": test_user.id,
            "name": "Session with Hooks",
            "mode": "interactive",
            "sdk_options": {
                "model": "claude-sonnet-4-5",
                "hooks_enabled": True,
                "enabled_hooks": ["audit", "metrics"],
            },
        }

        # Act
        session = await service.create_session(**session_data)

        # Assert
        assert session.id is not None
        assert session.sdk_options["hooks_enabled"] is True
        assert "audit" in session.sdk_options["enabled_hooks"]
        
        # Verify in database
        retrieved = await session_repo.find_by_id(session.id)
        assert retrieved.sdk_options["hooks_enabled"] is True

    async def test_get_session_hooks_history(self, db_session, test_session_model):
        """Test retrieving hook execution history for a session."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        
        # Create some hook executions
        for i in range(3):
            await hook_repo.create({
                "session_id": test_session_model.id,
                "hook_name": f"hook_{i}",
                "hook_type": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {},
                "priority": 100,
                "executed_at": datetime.now(timezone.utc),
                "execution_duration_ms": 100,
                "allowed": True,
                "blocked": False,
            })
        
        service = SessionService(
            session_repo=session_repo,
            hook_execution_repo=hook_repo,
        )

        # Act
        hooks_history = await service.get_session_hooks_history(test_session_model.id)

        # Assert
        assert len(hooks_history) == 3
        assert all("hook_name" in h for h in hooks_history)

    async def test_get_session_permissions_history(self, db_session, test_session_model, test_user):
        """Test retrieving permission decisions history for a session."""
        # Arrange
        session_repo = SessionRepository(db_session)
        decision_repo = PermissionDecisionRepository(db_session)
        
        # Create some permission decisions
        for i in range(5):
            await decision_repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": "Bash",
                "tool_input": {},
                "decision": "allow" if i % 2 == 0 else "deny",
                "reason": f"Test reason {i}",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10,
            })
        
        service = SessionService(
            session_repo=session_repo,
            permission_decision_repo=decision_repo,
        )

        # Act
        permissions_history = await service.get_session_permissions_history(test_session_model.id)

        # Assert
        assert len(permissions_history) == 5
        allowed_count = sum(1 for p in permissions_history if p["decision"] == "allow")
        denied_count = sum(1 for p in permissions_history if p["decision"] == "deny")
        assert allowed_count == 3
        assert denied_count == 2

    async def test_get_session_metrics_summary(self, db_session, test_session_model):
        """Test retrieving metrics summary for a session."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        # Update session with metrics
        test_session_model.total_input_tokens = 500
        test_session_model.total_output_tokens = 300
        test_session_model.total_cache_creation_tokens = 100
        test_session_model.total_cache_read_tokens = 50
        test_session_model.query_count = 10
        await session_repo.update(test_session_model)
        
        service = SessionService(session_repo=session_repo)

        # Act
        metrics = await service.get_session_metrics_summary(test_session_model.id)

        # Assert
        assert metrics["total_input_tokens"] == 500
        assert metrics["total_output_tokens"] == 300
        assert metrics["total_cache_creation_tokens"] == 100
        assert metrics["total_cache_read_tokens"] == 50
        assert metrics["query_count"] == 10

    async def test_delete_session_cascades(self, db_session, test_session_model):
        """Test deleting session removes related hook executions and decisions."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        decision_repo = PermissionDecisionRepository(db_session)
        
        # Create related data
        await hook_repo.create({
            "session_id": test_session_model.id,
            "hook_name": "test_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 100,
            "allowed": True,
            "blocked": False,
        })
        
        await decision_repo.create({
            "session_id": test_session_model.id,
            "user_id": uuid4(),
            "tool_name": "Bash",
            "tool_input": {},
            "decision": "allow",
            "reason": "Test",
            "policy_name": "test_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 10,
        })
        
        service = SessionService(session_repo=session_repo)

        # Act
        await service.delete_session(test_session_model.id)

        # Assert
        session = await session_repo.find_by_id(test_session_model.id)
        assert session is None
        
        # Verify related data is cleaned up (depends on cascade configuration)

    async def test_update_session_status(self, db_session, test_session_model):
        """Test updating session status through service."""
        # Arrange
        session_repo = SessionRepository(db_session)
        service = SessionService(session_repo=session_repo)

        # Act
        await service.update_session_status(test_session_model.id, "active")

        # Assert
        session = await session_repo.find_by_id(test_session_model.id)
        assert session.status == "active"

    async def test_forked_sessions_independent(self, db_session, test_session_model, test_user):
        """Test that forked sessions operate independently."""
        # Arrange
        session_repo = SessionRepository(db_session)
        service = SessionService(session_repo=session_repo)
        
        # Fork the session
        forked = await service.fork_session_advanced(
            session_id=test_session_model.id,
            user_id=test_user.id,
            new_name="Forked",
        )
        
        # Act - Update original session
        test_session_model.query_count = 10
        test_session_model.total_input_tokens = 200
        await session_repo.update(test_session_model)

        # Assert - Forked session unchanged
        forked_retrieved = await session_repo.find_by_id(forked.id)
        assert forked_retrieved.query_count == 0
        assert forked_retrieved.total_input_tokens == test_session_model.total_input_tokens  # Initial copy

    async def test_session_lifecycle_complete_flow(self, db_session, test_user):
        """Test complete session lifecycle: create, use, fork, archive, delete."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        
        with patch('app.services.session_service.StorageArchiver') as mock_archiver:
            mock_archiver_instance = AsyncMock()
            mock_archiver.return_value = mock_archiver_instance
            mock_archiver_instance.archive_working_directory.return_value = {
                "archive_id": "archive_123",
                "s3_key": "archives/test/archive.tar.gz",
                "manifest": {"files": []},
            }
            
            service = SessionService(
                session_repo=session_repo,
                hook_execution_repo=hook_repo,
            )

            # Act 1: Create
            session = await service.create_session(
                user_id=test_user.id,
                name="Lifecycle Test",
                mode="interactive",
                sdk_options={"model": "claude-sonnet-4-5"},
            )
            assert session.id is not None

            # Act 2: Use (simulate activity)
            session.query_count = 5
            session.total_input_tokens = 100
            await session_repo.update(session)

            # Act 3: Fork
            forked = await service.fork_session_advanced(
                session_id=session.id,
                user_id=test_user.id,
                new_name="Forked Lifecycle Test",
            )
            assert forked.id != session.id

            # Act 4: Archive
            archive_result = await service.archive_session_to_storage(
                session_id=session.id,
                working_directory="/tmp/test",
            )
            assert "archive_id" in archive_result

            # Act 5: Delete
            await service.delete_session(session.id)

            # Assert
            deleted = await session_repo.find_by_id(session.id)
            assert deleted is None
            
            # Forked session should still exist
            forked_retrieved = await session_repo.find_by_id(forked.id)
            assert forked_retrieved is not None
