"""Unit tests for PermissionDecisionRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.models.permission_decision import PermissionDecisionModel


class TestPermissionDecisionRepository:
    """Test cases for PermissionDecisionRepository."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repository(self, mock_db):
        """Permission decision repository instance."""
        return PermissionDecisionRepository(mock_db)

    @pytest.fixture
    def sample_permission_decision(self):
        """Sample permission decision model."""
        return PermissionDecisionModel(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=uuid4(),
            tool_use_id="tool_123",
            tool_name="file_reader",
            input_data={"file": "test.txt"},
            context_data={"user": "test_user"},
            decision="allowed",
            reason="User has read permission",
            policy_applied="read_policy",
            created_at=datetime.utcnow(),
        )

    async def test_repository_inheritance(self, repository):
        """Test that repository inherits from BaseRepository."""
        from app.repositories.base import BaseRepository
        assert isinstance(repository, BaseRepository)

    async def test_get_by_session(self, repository, mock_db, sample_permission_decision):
        """Test getting permission decisions by session ID."""
        session_id = sample_permission_decision.session_id
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert len(result) == 1
        assert result[0] == sample_permission_decision
        mock_db.execute.assert_called_once()

    async def test_get_by_session_with_pagination(self, repository, mock_db, sample_permission_decision):
        """Test getting permission decisions with pagination."""
        session_id = sample_permission_decision.session_id
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id, skip=5, limit=10)

        assert len(result) == 1
        mock_db.execute.assert_called_once()

    async def test_get_by_decision_allowed(self, repository, mock_db, sample_permission_decision):
        """Test getting permission decisions by decision type (allowed)."""
        session_id = sample_permission_decision.session_id
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_decision(session_id, "allowed")

        assert len(result) == 1
        assert result[0] == sample_permission_decision
        assert result[0].decision == "allowed"
        mock_db.execute.assert_called_once()

    async def test_get_by_decision_denied(self, repository, mock_db):
        """Test getting permission decisions by decision type (denied)."""
        session_id = uuid4()
        denied_decision = PermissionDecisionModel(
            id=uuid4(),
            session_id=session_id,
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="file_writer",
            input_data={"file": "system.conf"},
            context_data={"user": "guest"},
            decision="denied",
            reason="Insufficient permissions",
            policy_applied="security_policy",
            created_at=datetime.utcnow(),
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [denied_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_decision(session_id, "denied")

        assert len(result) == 1
        assert result[0] == denied_decision
        assert result[0].decision == "denied"
        mock_db.execute.assert_called_once()

    async def test_get_by_decision_with_pagination(self, repository, mock_db):
        """Test getting permission decisions by decision type with pagination."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_decision(session_id, "bypassed", skip=10, limit=20)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_by_tool_name(self, repository, mock_db, sample_permission_decision):
        """Test getting permission decisions by tool name."""
        session_id = sample_permission_decision.session_id
        tool_name = sample_permission_decision.tool_name
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_permission_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_tool_name(session_id, tool_name)

        assert len(result) == 1
        assert result[0] == sample_permission_decision
        assert result[0].tool_name == tool_name
        mock_db.execute.assert_called_once()

    async def test_get_by_tool_name_with_pagination(self, repository, mock_db):
        """Test getting permission decisions by tool name with pagination."""
        session_id = uuid4()
        tool_name = "test_tool"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_tool_name(session_id, tool_name, skip=0, limit=50)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_count_by_decision(self, repository, mock_db):
        """Test counting permission decisions by decision type."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_db.execute.return_value = mock_result

        count = await repository.count_by_decision(session_id, "allowed")

        assert count == 5
        mock_db.execute.assert_called_once()

    async def test_count_by_decision_zero(self, repository, mock_db):
        """Test counting permission decisions when count is zero."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        count = await repository.count_by_decision(session_id, "denied")

        assert count == 0
        mock_db.execute.assert_called_once()

    async def test_get_denied_decisions(self, repository, mock_db):
        """Test getting denied decisions (convenience method)."""
        session_id = uuid4()
        denied_decision = PermissionDecisionModel(
            id=uuid4(),
            session_id=session_id,
            tool_call_id=uuid4(),
            tool_use_id="tool_789",
            tool_name="system_tool",
            input_data={"action": "delete"},
            context_data={"user": "user123"},
            decision="denied",
            reason="Dangerous operation blocked",
            policy_applied="safety_policy",
            created_at=datetime.utcnow(),
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [denied_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_denied_decisions(session_id)

        assert len(result) == 1
        assert result[0] == denied_decision
        assert result[0].decision == "denied"
        mock_db.execute.assert_called_once()

    async def test_get_denied_decisions_with_pagination(self, repository, mock_db):
        """Test getting denied decisions with pagination."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_denied_decisions(session_id, skip=5, limit=15)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_multiple_decision_types_same_session(self, repository, mock_db):
        """Test getting multiple permission decisions with different types."""
        session_id = uuid4()
        
        decisions = [
            PermissionDecisionModel(
                id=uuid4(),
                session_id=session_id,
                tool_call_id=None,
                tool_use_id=f"tool_{i}",
                tool_name=f"test_tool_{i}",
                input_data={"param": f"value_{i}"},
                context_data={"user": "test_user"},
                decision=decision_type,
                reason=f"Test reason {i}",
                policy_applied=f"policy_{i}",
                created_at=datetime.utcnow(),
            )
            for i, decision_type in enumerate(["allowed", "denied", "bypassed"])
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = decisions
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert len(result) == 3
        decision_types = [d.decision for d in result]
        assert "allowed" in decision_types
        assert "denied" in decision_types
        assert "bypassed" in decision_types

    async def test_empty_results(self, repository, mock_db):
        """Test all methods with empty results."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result

        # Test all query methods return empty lists
        session_result = await repository.get_by_session(session_id)
        assert len(session_result) == 0

        decision_result = await repository.get_by_decision(session_id, "allowed")
        assert len(decision_result) == 0

        tool_result = await repository.get_by_tool_name(session_id, "nonexistent_tool")
        assert len(tool_result) == 0

        denied_result = await repository.get_denied_decisions(session_id)
        assert len(denied_result) == 0

        # Test count returns 0
        mock_db.execute.return_value = mock_result  # Reset for count call
        count_result = await repository.count_by_decision(session_id, "allowed")
        assert count_result == 0

    async def test_repository_model_type(self, repository):
        """Test that repository has correct model type."""
        assert repository.model == PermissionDecisionModel

    async def test_repository_db_session(self, repository, mock_db):
        """Test that repository stores database session."""
        assert repository.db == mock_db

    async def test_permission_decision_with_no_tool_call_id(self, repository, mock_db):
        """Test permission decision without tool_call_id (system-level permission)."""
        session_id = uuid4()
        system_decision = PermissionDecisionModel(
            id=uuid4(),
            session_id=session_id,
            tool_call_id=None,  # System-level decision
            tool_use_id="system_tool_001",
            tool_name="system_config",
            input_data={"config": "update"},
            context_data={"admin": "true"},
            decision="allowed",
            reason="Admin user has system access",
            policy_applied="admin_policy",
            created_at=datetime.utcnow(),
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [system_decision]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert len(result) == 1
        assert result[0].tool_call_id is None
        assert result[0].tool_name == "system_config"