"""Integration tests for HookExecutionRepository with real database."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.repositories.hook_execution_repository import HookExecutionRepository
from app.models.session import SessionModel
from app.models.user import UserModel, OrganizationModel


@pytest.mark.asyncio
class TestHookExecutionRepositoryIntegration:
    """Integration tests for HookExecutionRepository with real database."""

    async def test_create_hook_execution(self, db_session, test_session_model):
        """Test creating a hook execution record."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        hook_data = {
            "session_id": test_session_model.id,
            "hook_name": "audit_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 150,
            "allowed": True,
            "blocked": False,
            "modified_input": None,
            "hook_output": {"audit_id": "12345"},
            "error_message": None,
        }

        # Act
        hook_execution = await repo.create(hook_data)

        # Assert
        assert hook_execution.id is not None
        assert hook_execution.session_id == test_session_model.id
        assert hook_execution.hook_name == "audit_hook"
        assert hook_execution.hook_type == "PreToolUse"
        assert hook_execution.tool_name == "Bash"
        assert hook_execution.priority == 100
        assert hook_execution.allowed is True
        assert hook_execution.blocked is False

    async def test_find_by_session_id(self, db_session, test_session_model):
        """Test finding hook executions by session ID."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create multiple hook executions
        for i in range(3):
            await repo.create({
                "session_id": test_session_model.id,
                "hook_name": f"hook_{i}",
                "hook_type": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {},
                "priority": 100 + i,
                "executed_at": datetime.now(timezone.utc),
                "execution_duration_ms": 100 + i * 50,
                "allowed": True,
                "blocked": False,
            })

        # Act
        hook_executions = await repo.find_by_session_id(test_session_model.id)

        # Assert
        assert len(hook_executions) == 3
        assert all(he.session_id == test_session_model.id for he in hook_executions)
        # Verify they're ordered by executed_at descending (most recent first)
        for i in range(len(hook_executions) - 1):
            assert hook_executions[i].executed_at >= hook_executions[i + 1].executed_at

    async def test_find_by_hook_name(self, db_session, test_session_model):
        """Test finding hook executions by hook name."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create hook executions with different names
        await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "audit_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 100,
            "allowed": True,
            "blocked": False,
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "metrics_hook",
            "hook_type": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {},
            "priority": 50,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 80,
            "allowed": True,
            "blocked": False,
        })

        # Act
        audit_hooks = await repo.find_by_hook_name(test_session_model.id, "audit_hook")
        metrics_hooks = await repo.find_by_hook_name(test_session_model.id, "metrics_hook")

        # Assert
        assert len(audit_hooks) == 1
        assert audit_hooks[0].hook_name == "audit_hook"
        assert len(metrics_hooks) == 1
        assert metrics_hooks[0].hook_name == "metrics_hook"

    async def test_find_blocked_executions(self, db_session, test_session_model):
        """Test finding blocked hook executions."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create allowed and blocked executions
        await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "permission_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 50,
            "allowed": False,
            "blocked": True,
            "error_message": "Dangerous command blocked",
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "permission_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 30,
            "allowed": True,
            "blocked": False,
        })

        # Act
        blocked = await repo.find_blocked_executions(test_session_model.id)

        # Assert
        assert len(blocked) == 1
        assert blocked[0].blocked is True
        assert blocked[0].allowed is False
        assert "Dangerous" in blocked[0].error_message

    async def test_get_execution_statistics(self, db_session, test_session_model):
        """Test getting execution statistics for a session."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create various hook executions
        for i in range(5):
            await repo.create({
                "session_id": test_session_model.id,
                "hook_name": "audit_hook",
                "hook_type": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {},
                "priority": 100,
                "executed_at": datetime.now(timezone.utc),
                "execution_duration_ms": 100 + i * 20,
                "allowed": True,
                "blocked": False,
            })
        
        # Create one blocked execution
        await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "permission_hook",
            "hook_type": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {},
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 50,
            "allowed": False,
            "blocked": True,
        })

        # Act
        stats = await repo.get_execution_statistics(test_session_model.id)

        # Assert
        assert stats["total_executions"] == 6
        assert stats["blocked_count"] == 1
        assert stats["allowed_count"] == 5
        assert stats["avg_execution_time_ms"] > 0
        assert stats["max_execution_time_ms"] >= stats["min_execution_time_ms"]

    async def test_delete_old_executions(self, db_session, test_session_model):
        """Test deleting old hook executions."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Create executions
        for i in range(3):
            await repo.create({
                "session_id": test_session_model.id,
                "hook_name": "audit_hook",
                "hook_type": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {},
                "priority": 100,
                "executed_at": datetime.now(timezone.utc),
                "execution_duration_ms": 100,
                "allowed": True,
                "blocked": False,
            })

        # Act
        initial_count = len(await repo.find_by_session_id(test_session_model.id))
        deleted_count = await repo.delete_old_executions(days=0)  # Delete all
        final_count = len(await repo.find_by_session_id(test_session_model.id))

        # Assert
        assert initial_count == 3
        assert deleted_count >= 3
        assert final_count == 0

    async def test_hook_execution_with_complex_data(self, db_session, test_session_model):
        """Test hook execution with complex nested data structures."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        complex_input = {
            "command": "kubectl apply",
            "args": ["-f", "deployment.yaml"],
            "env": {"KUBECONFIG": "/path/to/config"},
            "nested": {
                "level1": {
                    "level2": ["item1", "item2", "item3"]
                }
            }
        }
        complex_output = {
            "status": "success",
            "resources": ["deployment/app", "service/app"],
            "warnings": [],
            "metrics": {
                "execution_time": 1.5,
                "resources_created": 2
            }
        }

        # Act
        hook_execution = await repo.create({
            "session_id": test_session_model.id,
            "hook_name": "audit_hook",
            "hook_type": "PostToolUse",
            "tool_name": "Kubectl",
            "tool_input": complex_input,
            "priority": 100,
            "executed_at": datetime.now(timezone.utc),
            "execution_duration_ms": 1500,
            "allowed": True,
            "blocked": False,
            "hook_output": complex_output,
        })

        # Assert
        assert hook_execution.tool_input == complex_input
        assert hook_execution.hook_output == complex_output
        
        # Retrieve and verify
        retrieved = await repo.find_by_id(hook_execution.id)
        assert retrieved.tool_input["nested"]["level1"]["level2"] == ["item1", "item2", "item3"]
        assert retrieved.hook_output["metrics"]["execution_time"] == 1.5

    async def test_concurrent_hook_executions(self, db_session, test_session_model):
        """Test creating multiple hook executions concurrently."""
        # Arrange
        repo = HookExecutionRepository(db_session)
        
        # Act - Create multiple executions
        executions = []
        for i in range(10):
            execution = await repo.create({
                "session_id": test_session_model.id,
                "hook_name": f"hook_{i % 3}",  # 3 different hooks
                "hook_type": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": f"echo {i}"},
                "priority": 100 - i,  # Different priorities
                "executed_at": datetime.now(timezone.utc),
                "execution_duration_ms": 100 + i * 10,
                "allowed": True,
                "blocked": False,
            })
            executions.append(execution)

        # Assert
        assert len(executions) == 10
        all_executions = await repo.find_by_session_id(test_session_model.id)
        assert len(all_executions) == 10
        
        # Verify all executions have unique IDs
        execution_ids = [e.id for e in all_executions]
        assert len(execution_ids) == len(set(execution_ids))
