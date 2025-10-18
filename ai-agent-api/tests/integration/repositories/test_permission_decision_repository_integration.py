"""Integration tests for PermissionDecisionRepository with real database."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.models.session import SessionModel
from app.models.user import UserModel, OrganizationModel


@pytest.mark.asyncio
class TestPermissionDecisionRepositoryIntegration:
    """Integration tests for PermissionDecisionRepository with real database."""

    async def test_create_permission_decision(self, db_session, test_session_model, test_user):
        """Test creating a permission decision record."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        decision_data = {
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "decision": "allow",
            "reason": "User has bash access",
            "policy_name": "file_access_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 25,
            "context": {
                "working_directory": "/home/user",
                "environment": "production"
            },
        }

        # Act
        decision = await repo.create(decision_data)

        # Assert
        assert decision.id is not None
        assert decision.session_id == test_session_model.id
        assert decision.user_id == test_user.id
        assert decision.tool_name == "Bash"
        assert decision.decision == "allow"
        assert decision.policy_name == "file_access_policy"
        assert decision.evaluation_duration_ms == 25

    async def test_find_by_session_id(self, db_session, test_session_model, test_user):
        """Test finding permission decisions by session ID."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create multiple decisions
        for i in range(5):
            await repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": f"Tool_{i}",
                "tool_input": {"param": f"value_{i}"},
                "decision": "allow" if i % 2 == 0 else "deny",
                "reason": f"Reason {i}",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10 + i * 5,
            })

        # Act
        decisions = await repo.find_by_session_id(test_session_model.id)

        # Assert
        assert len(decisions) == 5
        assert all(d.session_id == test_session_model.id for d in decisions)
        # Should be ordered by evaluated_at descending
        for i in range(len(decisions) - 1):
            assert decisions[i].evaluated_at >= decisions[i + 1].evaluated_at

    async def test_find_denied_decisions(self, db_session, test_session_model, test_user):
        """Test finding denied permission decisions."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create allowed and denied decisions
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},
            "decision": "deny",
            "reason": "Dangerous command",
            "policy_name": "command_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 15,
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "decision": "allow",
            "reason": "Safe command",
            "policy_name": "command_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 10,
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Write",
            "tool_input": {"path": "/etc/passwd"},
            "decision": "deny",
            "reason": "System file write blocked",
            "policy_name": "file_access_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 20,
        })

        # Act
        denied = await repo.find_denied_decisions(test_session_model.id)

        # Assert
        assert len(denied) == 2
        assert all(d.decision == "deny" for d in denied)
        reasons = [d.reason for d in denied]
        assert "Dangerous command" in reasons
        assert "System file write blocked" in reasons

    async def test_find_by_tool_name(self, db_session, test_session_model, test_user):
        """Test finding permission decisions by tool name."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create decisions for different tools
        for tool in ["Bash", "Write", "Read", "Bash", "Write"]:
            await repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": tool,
                "tool_input": {},
                "decision": "allow",
                "reason": "Test",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10,
            })

        # Act
        bash_decisions = await repo.find_by_tool_name(test_session_model.id, "Bash")
        write_decisions = await repo.find_by_tool_name(test_session_model.id, "Write")
        read_decisions = await repo.find_by_tool_name(test_session_model.id, "Read")

        # Assert
        assert len(bash_decisions) == 2
        assert len(write_decisions) == 2
        assert len(read_decisions) == 1
        assert all(d.tool_name == "Bash" for d in bash_decisions)

    async def test_find_by_policy_name(self, db_session, test_session_model, test_user):
        """Test finding permission decisions by policy name."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create decisions with different policies
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {},
            "decision": "allow",
            "reason": "Test",
            "policy_name": "file_access_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 10,
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Write",
            "tool_input": {},
            "decision": "deny",
            "reason": "Test",
            "policy_name": "command_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 15,
        })

        # Act
        file_policy_decisions = await repo.find_by_policy_name(test_session_model.id, "file_access_policy")
        command_policy_decisions = await repo.find_by_policy_name(test_session_model.id, "command_policy")

        # Assert
        assert len(file_policy_decisions) == 1
        assert file_policy_decisions[0].policy_name == "file_access_policy"
        assert len(command_policy_decisions) == 1
        assert command_policy_decisions[0].policy_name == "command_policy"

    async def test_get_decision_statistics(self, db_session, test_session_model, test_user):
        """Test getting decision statistics for a session."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create various decisions
        for i in range(7):
            await repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": "Bash",
                "tool_input": {},
                "decision": "allow" if i < 5 else "deny",
                "reason": "Test",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10 + i * 3,
            })

        # Act
        stats = await repo.get_decision_statistics(test_session_model.id)

        # Assert
        assert stats["total_decisions"] == 7
        assert stats["allowed_count"] == 5
        assert stats["denied_count"] == 2
        assert stats["avg_evaluation_time_ms"] > 0
        assert stats["max_evaluation_time_ms"] >= stats["min_evaluation_time_ms"]

    async def test_find_by_user_id(self, db_session, test_session_model, test_user, admin_user):
        """Test finding permission decisions by user ID."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create decisions for different users
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {},
            "decision": "allow",
            "reason": "Test user decision",
            "policy_name": "test_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 10,
        })
        
        await repo.create({
            "session_id": test_session_model.id,
            "user_id": admin_user.id,
            "tool_name": "Bash",
            "tool_input": {},
            "decision": "allow",
            "reason": "Admin user decision",
            "policy_name": "test_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 10,
        })

        # Act
        user_decisions = await repo.find_by_user_id(test_user.id)
        admin_decisions = await repo.find_by_user_id(admin_user.id)

        # Assert
        assert len(user_decisions) >= 1
        assert all(d.user_id == test_user.id for d in user_decisions)
        assert len(admin_decisions) >= 1
        assert all(d.user_id == admin_user.id for d in admin_decisions)

    async def test_delete_old_decisions(self, db_session, test_session_model, test_user):
        """Test deleting old permission decisions."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create decisions
        for i in range(5):
            await repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": "Bash",
                "tool_input": {},
                "decision": "allow",
                "reason": "Test",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10,
            })

        # Act
        initial_count = len(await repo.find_by_session_id(test_session_model.id))
        deleted_count = await repo.delete_old_decisions(days=0)  # Delete all
        final_count = len(await repo.find_by_session_id(test_session_model.id))

        # Assert
        assert initial_count == 5
        assert deleted_count >= 5
        assert final_count == 0

    async def test_decision_with_complex_context(self, db_session, test_session_model, test_user):
        """Test permission decision with complex context data."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        complex_context = {
            "user_role": "developer",
            "environment": "staging",
            "resource_permissions": {
                "read": True,
                "write": False,
                "execute": True
            },
            "restrictions": ["no_delete", "no_sudo"],
            "metadata": {
                "request_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "api"
            }
        }

        # Act
        decision = await repo.create({
            "session_id": test_session_model.id,
            "user_id": test_user.id,
            "tool_name": "Bash",
            "tool_input": {"command": "cat file.txt"},
            "decision": "allow",
            "reason": "Read-only access permitted",
            "policy_name": "role_based_policy",
            "evaluated_at": datetime.now(timezone.utc),
            "evaluation_duration_ms": 30,
            "context": complex_context,
        })

        # Assert
        assert decision.context == complex_context
        
        # Retrieve and verify
        retrieved = await repo.find_by_id(decision.id)
        assert retrieved.context["resource_permissions"]["read"] is True
        assert retrieved.context["resource_permissions"]["write"] is False
        assert retrieved.context["restrictions"] == ["no_delete", "no_sudo"]

    async def test_find_recent_decisions_with_limit(self, db_session, test_session_model, test_user):
        """Test finding recent decisions with pagination."""
        # Arrange
        repo = PermissionDecisionRepository(db_session)
        
        # Create 20 decisions
        for i in range(20):
            await repo.create({
                "session_id": test_session_model.id,
                "user_id": test_user.id,
                "tool_name": "Bash",
                "tool_input": {"index": i},
                "decision": "allow",
                "reason": f"Test {i}",
                "policy_name": "test_policy",
                "evaluated_at": datetime.now(timezone.utc),
                "evaluation_duration_ms": 10,
            })

        # Act
        recent_10 = await repo.find_by_session_id(test_session_model.id, limit=10)
        recent_5 = await repo.find_by_session_id(test_session_model.id, limit=5)

        # Assert
        assert len(recent_10) == 10
        assert len(recent_5) == 5
        # Most recent should be first
        assert recent_5[0].evaluated_at >= recent_5[-1].evaluated_at
