"""Integration tests for PermissionManager with real database logging."""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.claude_sdk.permissions.permission_manager import PermissionManager
from app.claude_sdk.permissions.policy_engine import PolicyEngine
from app.claude_sdk.permissions.policies.file_access_policy import FileAccessPolicy
from app.claude_sdk.permissions.policies.command_policy import CommandPolicy
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.models.session import SessionModel


@pytest.mark.asyncio
class TestPermissionManagerDatabaseIntegration:
    """Integration tests for PermissionManager with database logging."""

    async def test_permission_decision_logged_to_database(self, db_session, test_session_model, test_user):
        """Test that permission decisions are logged to database."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        
        context = {
            "tool_name": "Write",
            "tool_input": {"path": "/tmp/test.txt", "content": "Hello"},
        }

        # Act
        result = await manager.can_use_tool(context)

        # Assert
        assert result.allowed is True
        
        # Verify logged to database
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 1
        assert decisions[0].tool_name == "Write"
        assert decisions[0].decision == "allow"
        assert decisions[0].user_id == test_user.id

    async def test_denied_permission_logged(self, db_session, test_session_model, test_user):
        """Test that denied permissions are logged correctly."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        command_policy = CommandPolicy()
        policy_engine.register_policy(command_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        
        context = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
        }

        # Act
        result = await manager.can_use_tool(context)

        # Assert
        assert result.allowed is False
        
        # Verify logged to database
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 1
        assert decisions[0].decision == "deny"
        assert "dangerous" in decisions[0].reason.lower() or "blocked" in decisions[0].reason.lower()

    async def test_multiple_decisions_all_logged(self, db_session, test_session_model, test_user):
        """Test that multiple permission decisions are all logged."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Act - Make multiple permission checks
        contexts = [
            {"tool_name": "Read", "tool_input": {"path": "/tmp/file1.txt"}},
            {"tool_name": "Write", "tool_input": {"path": "/tmp/file2.txt"}},
            {"tool_name": "Read", "tool_input": {"path": "/etc/passwd"}},  # Should be denied
        ]
        
        results = []
        for ctx in contexts:
            result = await manager.can_use_tool(ctx)
            results.append(result)

        # Assert
        assert results[0].allowed is True  # /tmp read allowed
        assert results[1].allowed is True  # /tmp write allowed
        assert results[2].allowed is False  # /etc read denied
        
        # Verify all logged
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 3
        
        # Check specific decisions
        allowed_decisions = [d for d in decisions if d.decision == "allow"]
        denied_decisions = [d for d in decisions if d.decision == "deny"]
        assert len(allowed_decisions) == 2
        assert len(denied_decisions) == 1

    async def test_policy_name_recorded(self, db_session, test_session_model, test_user):
        """Test that the evaluating policy name is recorded."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        
        context = {
            "tool_name": "Write",
            "tool_input": {"path": "/etc/passwd"},
        }

        # Act
        await manager.can_use_tool(context)

        # Assert
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 1
        assert decisions[0].policy_name == "FileAccessPolicy"

    async def test_evaluation_duration_tracked(self, db_session, test_session_model, test_user):
        """Test that permission evaluation duration is tracked."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        # Create a slow policy
        import asyncio
        from app.claude_sdk.permissions.base_policy import BasePolicy
        
        class SlowPolicy(BasePolicy):
            def __init__(self):
                super().__init__("SlowPolicy", priority=100)
            
            async def evaluate(self, context: dict):
                await asyncio.sleep(0.1)  # 100ms delay
                from app.domain.value_objects.permission_result import PermissionResultAllow
                return PermissionResultAllow(reason="Slow evaluation")
        
        slow_policy = SlowPolicy()
        policy_engine.register_policy(slow_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        
        context = {"tool_name": "Test", "tool_input": {}}

        # Act
        await manager.can_use_tool(context)

        # Assert
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 1
        # Should be at least 100ms
        assert decisions[0].evaluation_duration_ms >= 100

    async def test_context_persisted(self, db_session, test_session_model, test_user):
        """Test that permission context is persisted to database."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        
        context = {
            "tool_name": "Write",
            "tool_input": {
                "path": "/tmp/test.txt",
                "content": "Test content",
                "mode": "0644",
            },
            "metadata": {
                "request_id": str(uuid4()),
                "source": "api",
            }
        }

        # Act
        await manager.can_use_tool(context)

        # Assert
        decisions = await decision_repo.find_by_session_id(test_session_model.id)
        assert len(decisions) == 1
        assert decisions[0].context is not None
        assert "metadata" in decisions[0].context

    async def test_find_denied_decisions(self, db_session, test_session_model, test_user):
        """Test querying denied decisions from database."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        command_policy = CommandPolicy()
        policy_engine.register_policy(command_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Act - Make multiple checks with some denials
        dangerous_commands = ["rm -rf /", "dd if=/dev/zero of=/dev/sda", "format c:"]
        safe_commands = ["ls -la", "cat file.txt"]
        
        for cmd in dangerous_commands + safe_commands:
            context = {"tool_name": "Bash", "tool_input": {"command": cmd}}
            await manager.can_use_tool(context)

        # Assert
        denied = await decision_repo.find_denied_decisions(test_session_model.id)
        assert len(denied) == 3  # All dangerous commands denied
        assert all(d.decision == "deny" for d in denied)

    async def test_permission_statistics(self, db_session, test_session_model, test_user):
        """Test permission decision statistics."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Act - Make 10 permission checks (7 allowed, 3 denied)
        for i in range(7):
            context = {"tool_name": "Read", "tool_input": {"path": f"/tmp/file{i}.txt"}}
            await manager.can_use_tool(context)
        
        for i in range(3):
            context = {"tool_name": "Read", "tool_input": {"path": f"/etc/file{i}.txt"}}
            await manager.can_use_tool(context)

        # Assert
        stats = await decision_repo.get_decision_statistics(test_session_model.id)
        assert stats["total_decisions"] == 10
        assert stats["allowed_count"] == 7
        assert stats["denied_count"] == 3

    async def test_multiple_sessions_isolated_decisions(self, db_session, test_user):
        """Test that permission decisions are isolated per session."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        
        # Create two sessions
        from app.models.session import SessionModel
        session1 = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Session 1",
            mode="interactive",
            status="created",
            sdk_options={"model": "claude-sonnet-4-5"},
        )
        session2 = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Session 2",
            mode="interactive",
            status="created",
            sdk_options={"model": "claude-sonnet-4-5"},
        )
        db_session.add(session1)
        db_session.add(session2)
        await db_session.commit()
        
        # Create managers for both sessions
        policy_engine = PolicyEngine()
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager1 = PermissionManager(
            session_id=session1.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )
        manager2 = PermissionManager(
            session_id=session2.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Act
        context1 = {"tool_name": "Read", "tool_input": {"path": "/tmp/file1.txt"}}
        context2 = {"tool_name": "Write", "tool_input": {"path": "/tmp/file2.txt"}}
        
        await manager1.can_use_tool(context1)
        await manager2.can_use_tool(context2)

        # Assert
        session1_decisions = await decision_repo.find_by_session_id(session1.id)
        session2_decisions = await decision_repo.find_by_session_id(session2.id)
        
        assert len(session1_decisions) == 1
        assert len(session2_decisions) == 1
        assert session1_decisions[0].tool_name == "Read"
        assert session2_decisions[0].tool_name == "Write"

    async def test_find_by_tool_name(self, db_session, test_session_model, test_user):
        """Test querying decisions by tool name."""
        # Arrange
        decision_repo = PermissionDecisionRepository(db_session)
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        policy_engine.register_policy(file_policy)
        
        manager = PermissionManager(
            session_id=test_session_model.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Act - Use different tools
        tools = ["Read", "Write", "Bash", "Read", "Write"]
        for tool in tools:
            context = {"tool_name": tool, "tool_input": {}}
            await manager.can_use_tool(context)

        # Assert
        read_decisions = await decision_repo.find_by_tool_name(test_session_model.id, "Read")
        write_decisions = await decision_repo.find_by_tool_name(test_session_model.id, "Write")
        bash_decisions = await decision_repo.find_by_tool_name(test_session_model.id, "Bash")
        
        assert len(read_decisions) == 2
        assert len(write_decisions) == 2
        assert len(bash_decisions) == 1
