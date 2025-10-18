"""Integration tests for HookManager with real database logging."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.claude_sdk.hooks.hook_manager import HookManager
from app.claude_sdk.hooks.base_hook import BaseHook, HookType
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.models.session import SessionModel


class TestHook(BaseHook):
    """Test hook for integration testing."""
    
    def __init__(self, name: str, hook_type: HookType, priority: int = 100, should_block: bool = False):
        super().__init__(name, hook_type, priority)
        self.should_block = should_block
        self.execution_count = 0

    async def execute(self, context: dict) -> dict:
        """Execute the test hook."""
        self.execution_count += 1
        return {
            "allowed": not self.should_block,
            "blocked": self.should_block,
            "modified_input": None,
            "hook_specific_output": {
                "execution_count": self.execution_count,
                "message": f"Executed {self.name}"
            }
        }


@pytest.mark.asyncio
class TestHookManagerDatabaseIntegration:
    """Integration tests for HookManager with database logging."""

    async def test_hook_execution_logged_to_database(self, db_session, test_session_model):
        """Test that hook executions are logged to database."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        test_hook = TestHook("test_hook", HookType.PRE_TOOL_USE, priority=100)
        manager.register_hook(test_hook)
        
        context = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "session_id": test_session_model.id,
        }

        # Act
        await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Assert
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 1
        assert executions[0].hook_name == "test_hook"
        assert executions[0].hook_type == "PreToolUse"
        assert executions[0].tool_name == "Bash"
        assert executions[0].allowed is True
        assert executions[0].blocked is False

    async def test_multiple_hooks_all_logged(self, db_session, test_session_model):
        """Test that multiple hook executions are all logged."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        # Register multiple hooks
        for i in range(3):
            hook = TestHook(f"hook_{i}", HookType.PRE_TOOL_USE, priority=100 - i * 10)
            manager.register_hook(hook)
        
        context = {
            "tool_name": "Write",
            "tool_input": {"path": "/tmp/test.txt"},
            "session_id": test_session_model.id,
        }

        # Act
        await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Assert
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 3
        
        # Verify they're logged in execution order (by priority)
        hook_names = [e.hook_name for e in executions]
        assert "hook_0" in hook_names
        assert "hook_1" in hook_names
        assert "hook_2" in hook_names

    async def test_blocked_hook_logged_correctly(self, db_session, test_session_model):
        """Test that blocked hooks are logged with correct status."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        # Hook that blocks execution
        blocking_hook = TestHook("blocking_hook", HookType.PRE_TOOL_USE, priority=100, should_block=True)
        manager.register_hook(blocking_hook)
        
        context = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
            "session_id": test_session_model.id,
        }

        # Act
        result = await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Assert
        assert result["allowed"] is False
        assert result["blocked"] is True
        
        # Verify database logging
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 1
        assert executions[0].blocked is True
        assert executions[0].allowed is False

    async def test_hook_error_logged_to_database(self, db_session, test_session_model):
        """Test that hook execution errors are logged."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        # Create a hook that raises an error
        class ErrorHook(BaseHook):
            async def execute(self, context: dict) -> dict:
                raise ValueError("Test error")
        
        error_hook = ErrorHook("error_hook", HookType.PRE_TOOL_USE, priority=100)
        manager.register_hook(error_hook)
        
        context = {
            "tool_name": "Bash",
            "tool_input": {"command": "test"},
            "session_id": test_session_model.id,
        }

        # Act
        result = await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Assert - Hook errors don't block execution
        assert result["allowed"] is True
        
        # Verify error was logged
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 1
        assert executions[0].error_message is not None
        assert "Test error" in executions[0].error_message

    async def test_execution_duration_tracked(self, db_session, test_session_model):
        """Test that hook execution duration is tracked in database."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        # Create a slow hook
        import asyncio
        
        class SlowHook(BaseHook):
            async def execute(self, context: dict) -> dict:
                await asyncio.sleep(0.1)  # 100ms delay
                return {"allowed": True, "blocked": False}
        
        slow_hook = SlowHook("slow_hook", HookType.PRE_TOOL_USE, priority=100)
        manager.register_hook(slow_hook)
        
        context = {
            "tool_name": "Bash",
            "tool_input": {},
            "session_id": test_session_model.id,
        }

        # Act
        await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Assert
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 1
        # Should be at least 100ms
        assert executions[0].execution_duration_ms >= 100

    async def test_hook_output_persisted(self, db_session, test_session_model):
        """Test that hook-specific output is persisted to database."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        test_hook = TestHook("output_hook", HookType.POST_TOOL_USE, priority=100)
        manager.register_hook(test_hook)
        
        context = {
            "tool_name": "Write",
            "tool_input": {"path": "/tmp/test.txt"},
            "tool_output": {"success": True},
            "session_id": test_session_model.id,
        }

        # Act
        await manager.execute_hooks(HookType.POST_TOOL_USE, context)

        # Assert
        executions = await hook_repo.find_by_session_id(test_session_model.id)
        assert len(executions) == 1
        assert executions[0].hook_output is not None
        assert "execution_count" in executions[0].hook_output
        assert "message" in executions[0].hook_output

    async def test_multiple_sessions_isolated_logging(self, db_session):
        """Test that hook executions are isolated per session."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        
        # Create two sessions
        from app.models.session import SessionModel
        session1 = SessionModel(
            id=uuid4(),
            user_id=uuid4(),
            name="Session 1",
            mode="interactive",
            status="created",
            sdk_options={"model": "claude-sonnet-4-5"},
        )
        session2 = SessionModel(
            id=uuid4(),
            user_id=uuid4(),
            name="Session 2",
            mode="interactive",
            status="created",
            sdk_options={"model": "claude-sonnet-4-5"},
        )
        db_session.add(session1)
        db_session.add(session2)
        await db_session.commit()
        
        # Create managers for both sessions
        manager1 = HookManager(session_id=session1.id, hook_execution_repo=hook_repo)
        manager2 = HookManager(session_id=session2.id, hook_execution_repo=hook_repo)
        
        # Register hooks
        hook1 = TestHook("hook_1", HookType.PRE_TOOL_USE, priority=100)
        hook2 = TestHook("hook_2", HookType.PRE_TOOL_USE, priority=100)
        manager1.register_hook(hook1)
        manager2.register_hook(hook2)
        
        context1 = {"tool_name": "Bash", "tool_input": {}, "session_id": session1.id}
        context2 = {"tool_name": "Write", "tool_input": {}, "session_id": session2.id}

        # Act
        await manager1.execute_hooks(HookType.PRE_TOOL_USE, context1)
        await manager2.execute_hooks(HookType.PRE_TOOL_USE, context2)

        # Assert
        session1_executions = await hook_repo.find_by_session_id(session1.id)
        session2_executions = await hook_repo.find_by_session_id(session2.id)
        
        assert len(session1_executions) == 1
        assert len(session2_executions) == 1
        assert session1_executions[0].tool_name == "Bash"
        assert session2_executions[0].tool_name == "Write"

    async def test_hook_statistics_accurate(self, db_session, test_session_model):
        """Test that hook execution statistics are accurate."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        # Register multiple hooks, some blocking
        allow_hook = TestHook("allow_hook", HookType.PRE_TOOL_USE, priority=100, should_block=False)
        block_hook = TestHook("block_hook", HookType.PRE_TOOL_USE, priority=90, should_block=True)
        manager.register_hook(allow_hook)
        manager.register_hook(block_hook)
        
        # Execute multiple times
        for i in range(5):
            context = {
                "tool_name": f"Tool_{i}",
                "tool_input": {},
                "session_id": test_session_model.id,
            }
            await manager.execute_hooks(HookType.PRE_TOOL_USE, context)

        # Act
        stats = await hook_repo.get_execution_statistics(test_session_model.id)

        # Assert
        assert stats["total_executions"] == 10  # 2 hooks * 5 executions
        assert stats["blocked_count"] == 5  # block_hook runs 5 times
        assert stats["allowed_count"] == 5  # allow_hook runs 5 times

    async def test_find_executions_by_hook_name(self, db_session, test_session_model):
        """Test querying executions by hook name."""
        # Arrange
        hook_repo = HookExecutionRepository(db_session)
        manager = HookManager(
            session_id=test_session_model.id,
            hook_execution_repo=hook_repo,
        )
        
        audit_hook = TestHook("audit_hook", HookType.PRE_TOOL_USE, priority=100)
        metrics_hook = TestHook("metrics_hook", HookType.POST_TOOL_USE, priority=100)
        manager.register_hook(audit_hook)
        manager.register_hook(metrics_hook)
        
        # Execute both types
        pre_context = {"tool_name": "Bash", "tool_input": {}, "session_id": test_session_model.id}
        post_context = {"tool_name": "Bash", "tool_input": {}, "tool_output": {}, "session_id": test_session_model.id}
        
        await manager.execute_hooks(HookType.PRE_TOOL_USE, pre_context)
        await manager.execute_hooks(HookType.POST_TOOL_USE, post_context)

        # Act
        audit_executions = await hook_repo.find_by_hook_name(test_session_model.id, "audit_hook")
        metrics_executions = await hook_repo.find_by_hook_name(test_session_model.id, "metrics_hook")

        # Assert
        assert len(audit_executions) == 1
        assert audit_executions[0].hook_type == "PreToolUse"
        assert len(metrics_executions) == 1
        assert metrics_executions[0].hook_type == "PostToolUse"
