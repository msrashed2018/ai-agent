"""Integration tests for HookExecutionRepository with real database."""

import pytest
from datetime import datetime, timezone

from app.repositories.hook_execution_repository import HookExecutionRepository


@pytest.mark.asyncio
class TestHookExecutionRepositoryIntegration:
    """Integration tests for HookExecutionRepository with real database."""

    import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.hook_execution_repository import HookExecutionRepository

@pytest.mark.asyncio
async def test_create_and_get_hook_execution(db_session: AsyncSession, test_session_model):
    """Test creating and retrieving a hook execution"""
    repo = HookExecutionRepository(db_session)
    
    execution_data = {
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "tool_456",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "ls -la"},
        "output_data": {"stdout": "file1.txt\nfile2.txt"},
        "execution_time_ms": 150
    }
    
    execution = await repo.create(**execution_data)
    await db_session.commit()
    
    retrieved = await repo.get_by_id(execution.id)
    assert retrieved is not None
    assert retrieved.hook_name == "pre_execute"
    assert retrieved.tool_name == "bash_tool"
    assert retrieved.execution_time_ms == 150
    assert retrieved.tool_call_id is None
    assert retrieved.input_data == {"command": "ls -la"}
    assert retrieved.output_data == {"stdout": "file1.txt\nfile2.txt"}

@pytest.mark.asyncio
async def test_get_by_session(db_session: AsyncSession, test_session_model):
    """Test retrieving all hook executions for a session"""
    repo = HookExecutionRepository(db_session)
    
    execution1 = await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "echo test"},
        "execution_time_ms": 100
    })
    
    execution2 = await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "post_execute",
        "tool_use_id": "toolu_python_001",
        "tool_name": "python_tool",
        "input_data": {"code": "print('hello')"},
        "execution_time_ms": 200
    })
    
    await db_session.commit()
    
    executions = await repo.get_by_session(test_session_model.id)
    assert len(executions) >= 2
    hook_names = [e.hook_name for e in executions]
    assert "pre_execute" in hook_names
    assert "post_execute" in hook_names

@pytest.mark.asyncio
async def test_get_by_hook_name(db_session: AsyncSession, test_session_model):
    """Test retrieving hook executions by hook name"""
    repo = HookExecutionRepository(db_session)
    
    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "ls"},
        "execution_time_ms": 50
    })
    
    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_python_001",
        "tool_name": "python_tool",
        "input_data": {"code": "print('test')"},
        "execution_time_ms": 75
    })
    
    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "post_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "pwd"},
        "execution_time_ms": 25
    })
    
    await db_session.commit()
    
    pre_execute_hooks = await repo.get_by_hook_name(test_session_model.id, "pre_execute")
    assert len(pre_execute_hooks) == 2
    assert all(h.hook_name == "pre_execute" for h in pre_execute_hooks)
    
    post_execute_hooks = await repo.get_by_hook_name(test_session_model.id, "post_execute")
    assert len(post_execute_hooks) == 1
    assert post_execute_hooks[0].hook_name == "post_execute"

@pytest.mark.asyncio
async def test_hook_execution_with_error(db_session: AsyncSession, test_session_model):
    """Test creating a hook execution with error information"""
    repo = HookExecutionRepository(db_session)
    
    execution = await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "invalid_command"},
        "error_message": "Command not found: invalid_command",
        "execution_time_ms": 10
    })
    
    await db_session.commit()
    
    retrieved = await repo.get_by_id(execution.id)
    assert retrieved.error_message == "Command not found: invalid_command"
    assert retrieved.output_data is None

@pytest.mark.asyncio
async def test_hook_execution_with_context(db_session: AsyncSession, test_session_model):
    """Test creating a hook execution with context data"""
    repo = HookExecutionRepository(db_session)
    
    context_data = {
        "user_id": "user_123",
        "permissions": ["read", "write"],
        "metadata": {"source": "cli"}
    }
    
    execution = await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_file_001",
        "tool_name": "file_tool",
        "input_data": {"path": "/tmp/test.txt"},
        "output_data": {"success": True},
        "context_data": context_data,
        "execution_time_ms": 120
    })
    
    await db_session.commit()
    
    retrieved = await repo.get_by_id(execution.id)
    assert retrieved.context_data == context_data
    assert retrieved.context_data["permissions"] == ["read", "write"]

@pytest.mark.asyncio
async def test_hook_execution_complex_json_data(db_session: AsyncSession, test_session_model):
    """Test hook execution with complex nested JSON data"""
    repo = HookExecutionRepository(db_session)
    
    complex_input = {
        "nested": {
            "level1": {
                "level2": {
                "data": [1, 2, 3],
                    "flags": {"enabled": True, "mode": "strict"}
                }
            }
        },
        "array_of_objects": [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"}
        ]
    }
    
    complex_output = {
        "results": [
            {"status": "success", "value": 42},
            {"status": "pending", "value": None}
        ],
        "summary": {"total": 2, "succeeded": 1, "failed": 0}
    }
    
    execution = await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "post_execute",
        "tool_use_id": "toolu_complex_001",
        "tool_name": "complex_tool",
        "input_data": complex_input,
        "output_data": complex_output,
        "execution_time_ms": 250
    })
    
    await db_session.commit()
    
    retrieved = await repo.get_by_id(execution.id)
    assert retrieved.input_data == complex_input
    assert retrieved.output_data == complex_output
    assert retrieved.input_data["nested"]["level1"]["level2"]["data"] == [1, 2, 3]
    assert retrieved.output_data["summary"]["total"] == 2

@pytest.mark.asyncio
async def test_get_nonexistent_hook_execution(db_session: AsyncSession):
    """Test retrieving a non-existent hook execution"""
    repo = HookExecutionRepository(db_session)
    
    from uuid import uuid4
    non_existent_id = uuid4()
    
    result = await repo.get_by_id(non_existent_id)
    assert result is None

@pytest.mark.asyncio
async def test_get_by_session_empty(db_session: AsyncSession, test_session_model):
    """Test getting hook executions for a session with no executions"""
    repo = HookExecutionRepository(db_session)
    
    executions = await repo.get_by_session(test_session_model.id)
    assert executions == []

@pytest.mark.asyncio
async def test_get_by_hook_name_not_found(db_session: AsyncSession, test_session_model):
    """Test getting hook executions by name that doesn't exist"""
    repo = HookExecutionRepository(db_session)
    
    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "ls"},
        "execution_time_ms": 50
    })
    
    await db_session.commit()
    
    results = await repo.get_by_hook_name(test_session_model.id, "nonexistent_hook")
    assert results == []
        
    async def test_get_by_session(self, db_session, test_session_model):
        """Test getting hook executions by session ID."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create executions
        for i in range(3):
            await repo.create(
                session_id=test_session_model.id,
                hook_name=f"hook_{i}",
                tool_use_id=f"tool_{i}",
                tool_name="Bash",
                input_data={},
                output_data={},
                context_data={},
                execution_time_ms=100
            )
        await db_session.commit()

        # Act
        executions = await repo.get_by_session(test_session_model.id)

        # Assert
        assert len(executions) == 3
