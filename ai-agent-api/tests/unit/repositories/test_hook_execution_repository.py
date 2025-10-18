"""Unit tests for HookExecutionRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.hook_execution_repository import HookExecutionRepository
from app.models.hook_execution import HookExecutionModel


class TestHookExecutionRepository:
    """Test cases for HookExecutionRepository."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def repository(self, mock_db):
        """Hook execution repository instance."""
        return HookExecutionRepository(mock_db)

    @pytest.fixture
    def sample_hook_execution(self):
        """Sample hook execution model."""
        return HookExecutionModel(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=uuid4(),
            hook_name="pre_tool_use",
            tool_use_id="tool_123",
            tool_name="file_reader",
            input_data={"file": "test.txt"},
            output_data={"status": "success"},
            context_data={"user": "test_user"},
            execution_time_ms=250,
            created_at=datetime.utcnow(),
        )

    async def test_repository_inheritance(self, repository):
        """Test that repository inherits from BaseRepository."""
        from app.repositories.base import BaseRepository
        assert isinstance(repository, BaseRepository)

    async def test_get_by_session(self, repository, mock_db, sample_hook_execution):
        """Test getting hook executions by session ID."""
        session_id = sample_hook_execution.session_id
        
        # Mock the database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_hook_execution]
        mock_db.execute.return_value = mock_result

        # Call the method
        result = await repository.get_by_session(session_id)

        # Assertions
        assert len(result) == 1
        assert result[0] == sample_hook_execution
        
        # Verify the query was called correctly
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0][0]
        # We can't easily verify the exact SQL, but we can check it's a select statement
        assert hasattr(call_args, 'whereclause')

    async def test_get_by_session_with_pagination(self, repository, mock_db, sample_hook_execution):
        """Test getting hook executions with skip and limit."""
        session_id = sample_hook_execution.session_id
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_hook_execution]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id, skip=10, limit=5)

        assert len(result) == 1
        mock_db.execute.assert_called_once()

    async def test_get_by_hook_name(self, repository, mock_db, sample_hook_execution):
        """Test getting hook executions by hook name."""
        session_id = sample_hook_execution.session_id
        hook_name = sample_hook_execution.hook_name
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_hook_execution]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_hook_name(session_id, hook_name)

        assert len(result) == 1
        assert result[0] == sample_hook_execution
        mock_db.execute.assert_called_once()

    async def test_get_by_hook_name_with_pagination(self, repository, mock_db, sample_hook_execution):
        """Test getting hook executions by hook name with pagination."""
        session_id = sample_hook_execution.session_id
        hook_name = sample_hook_execution.hook_name
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_hook_name(session_id, hook_name, skip=5, limit=10)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_by_tool_use_id(self, repository, mock_db, sample_hook_execution):
        """Test getting hook executions by tool use ID."""
        tool_use_id = sample_hook_execution.tool_use_id
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_hook_execution]
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_tool_use_id(tool_use_id)

        assert len(result) == 1
        assert result[0] == sample_hook_execution
        mock_db.execute.assert_called_once()

    async def test_get_failed_executions(self, repository, mock_db):
        """Test getting failed hook executions."""
        session_id = uuid4()
        failed_execution = HookExecutionModel(
            id=uuid4(),
            session_id=session_id,
            tool_call_id=None,
            hook_name="post_tool_use",
            tool_use_id="tool_456",
            tool_name="file_writer",
            input_data={"file": "test.txt"},
            output_data={},
            context_data={},
            execution_time_ms=500,
            created_at=datetime.utcnow(),
            error_message="Permission denied",
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [failed_execution]
        mock_db.execute.return_value = mock_result

        result = await repository.get_failed_executions(session_id)

        assert len(result) == 1
        assert result[0] == failed_execution
        assert result[0].error_message == "Permission denied"
        mock_db.execute.assert_called_once()

    async def test_get_failed_executions_with_pagination(self, repository, mock_db):
        """Test getting failed executions with pagination."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_failed_executions(session_id, skip=0, limit=50)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_by_session_empty_result(self, repository, mock_db):
        """Test getting hook executions when no records exist."""
        session_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_get_by_hook_name_empty_result(self, repository, mock_db):
        """Test getting hook executions by hook name when no records exist."""
        session_id = uuid4()
        hook_name = "non_existent_hook"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_hook_name(session_id, hook_name)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    async def test_multiple_hook_executions_same_session(self, repository, mock_db):
        """Test getting multiple hook executions for the same session."""
        session_id = uuid4()
        
        hook_executions = [
            HookExecutionModel(
                id=uuid4(),
                session_id=session_id,
                tool_call_id=uuid4(),
                hook_name="pre_tool_use",
                tool_use_id=f"tool_{i}",
                tool_name=f"test_tool_{i}",
                input_data={"test": f"data_{i}"},
                output_data={"result": f"output_{i}"},
                context_data={},
                execution_time_ms=100 + i * 50,
                created_at=datetime.utcnow(),
            )
            for i in range(3)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = hook_executions
        mock_db.execute.return_value = mock_result

        result = await repository.get_by_session(session_id)

        assert len(result) == 3
        for i, execution in enumerate(result):
            assert execution.tool_use_id == f"tool_{i}"
            assert execution.execution_time_ms == 100 + i * 50

    async def test_repository_model_type(self, repository):
        """Test that repository has correct model type."""
        assert repository.model == HookExecutionModel

    async def test_repository_db_session(self, repository, mock_db):
        """Test that repository stores database session."""
        assert repository.db == mock_db