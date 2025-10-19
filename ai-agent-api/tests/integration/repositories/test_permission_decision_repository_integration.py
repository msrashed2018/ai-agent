"""Integration tests for PermissionDecisionRepository with real database.""""""Integration tests for PermissionDecisionRepository with real database."""



import pytestimport pytest

from datetime import datetime, timezone, timedeltafrom datetime import datetime, timezone, timedelta

from uuid import uuid4from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.permission_decision_repository import PermissionDecisionRepository

from app.repositories.permission_decision_repository import PermissionDecisionRepositoryfrom app.models.session import SessionModel

from app.models.user import UserModel, OrganizationModel



@pytest.mark.asyncio

async def test_create_permission_decision(db_session: AsyncSession, test_session_model):@pytest.mark.asyncio

    """Test creating a permission decision record"""class TestPermissionDecisionRepositoryIntegration:

    repo = PermissionDecisionRepository(db_session)    """Integration tests for PermissionDecisionRepository with real database."""

    

    decision_data = {    async def test_create_permission_decision(self, db_session, test_session_model, test_user):

        "session_id": test_session_model.id,        """Test creating a permission decision record."""

        "tool_use_id": "toolu_bash_001",        # Arrange

        "tool_name": "bash_tool",        repo = PermissionDecisionRepository(db_session)

        "input_data": {"command": "ls -la"},        decision_data = {

        "context_data": {"working_directory": "/home/user"},            "session_id": test_session_model.id,

        "decision": "allowed",            "user_id": test_user.id,

        "reason": "User has bash access",            "tool_name": "Bash",

        "policy_applied": "file_access_policy"            "tool_input": {"command": "ls -la"},

    }            "decision": "allow",

                "reason": "User has bash access",

    decision = await repo.create(**decision_data)            "policy_name": "file_access_policy",

    await db_session.commit()            "evaluated_at": datetime.now(timezone.utc),

                "evaluation_duration_ms": 25,

    assert decision.id is not None            "context": {

    assert decision.session_id == test_session_model.id                "working_directory": "/home/user",

    assert decision.tool_use_id == "toolu_bash_001"                "environment": "production"

    assert decision.tool_name == "bash_tool"            },

    assert decision.decision == "allowed"        }

    assert decision.reason == "User has bash access"

    assert decision.policy_applied == "file_access_policy"        # Act

        decision = await repo.create(decision_data)



@pytest.mark.asyncio        # Assert

async def test_find_by_session_id(db_session: AsyncSession, test_session_model):        assert decision.id is not None

    """Test finding permission decisions by session ID"""        assert decision.session_id == test_session_model.id

    repo = PermissionDecisionRepository(db_session)        assert decision.user_id == test_user.id

            assert decision.tool_name == "Bash"

    await repo.create(**{        assert decision.decision == "allow"

        "session_id": test_session_model.id,        assert decision.policy_name == "file_access_policy"

        "tool_use_id": "toolu_001",        assert decision.evaluation_duration_ms == 25

        "tool_name": "bash_tool",

        "input_data": {"command": "ls"},    async def test_find_by_session_id(self, db_session, test_session_model, test_user):

        "decision": "allowed",        """Test finding permission decisions by session ID."""

        "reason": "Permitted action"        # Arrange

    })        repo = PermissionDecisionRepository(db_session)

            

    await repo.create(**{        # Create multiple decisions

        "session_id": test_session_model.id,        for i in range(5):

        "tool_use_id": "toolu_002",            await repo.create({

        "tool_name": "python_tool",                "session_id": test_session_model.id,

        "input_data": {"code": "print('test')"},                "user_id": test_user.id,

        "decision": "denied",                "tool_name": f"Tool_{i}",

        "reason": "Restricted action"                "tool_input": {"param": f"value_{i}"},

    })                "decision": "allow" if i % 2 == 0 else "deny",

                    "reason": f"Reason {i}",

    await db_session.commit()                "policy_name": "test_policy",

                    "evaluated_at": datetime.now(timezone.utc),

    decisions = await repo.get_by_session(test_session_model.id)                "evaluation_duration_ms": 10 + i * 5,

    assert len(decisions) >= 2            })

    decisions_list = [d.decision for d in decisions]

    assert "allowed" in decisions_list        # Act

    assert "denied" in decisions_list        decisions = await repo.find_by_session_id(test_session_model.id)



        # Assert

@pytest.mark.asyncio        assert len(decisions) == 5

async def test_find_denied_decisions(db_session: AsyncSession, test_session_model):        assert all(d.session_id == test_session_model.id for d in decisions)

    """Test finding denied permission decisions"""        # Should be ordered by evaluated_at descending

    repo = PermissionDecisionRepository(db_session)        for i in range(len(decisions) - 1):

                assert decisions[i].evaluated_at >= decisions[i + 1].evaluated_at

    await repo.create(**{

        "session_id": test_session_model.id,    async def test_find_denied_decisions(self, db_session, test_session_model, test_user):

        "tool_use_id": "toolu_allowed",        """Test finding denied permission decisions."""

        "tool_name": "bash_tool",        # Arrange

        "input_data": {"command": "ls"},        repo = PermissionDecisionRepository(db_session)

        "decision": "allowed",        

        "reason": "Permitted"        # Create allowed and denied decisions

    })        await repo.create({

                "session_id": test_session_model.id,

    await repo.create(**{            "user_id": test_user.id,

        "session_id": test_session_model.id,            "tool_name": "Bash",

        "tool_use_id": "toolu_denied_1",            "tool_input": {"command": "rm -rf /"},

        "tool_name": "bash_tool",            "decision": "deny",

        "input_data": {"command": "rm -rf /"},            "reason": "Dangerous command",

        "decision": "denied",            "policy_name": "command_policy",

        "reason": "Dangerous command"            "evaluated_at": datetime.now(timezone.utc),

    })            "evaluation_duration_ms": 15,

            })

    await repo.create(**{        

        "session_id": test_session_model.id,        await repo.create({

        "tool_use_id": "toolu_denied_2",            "session_id": test_session_model.id,

        "tool_name": "file_tool",            "user_id": test_user.id,

        "input_data": {"path": "/etc/passwd"},            "tool_name": "Bash",

        "decision": "denied",            "tool_input": {"command": "ls"},

        "reason": "Restricted file"            "decision": "allow",

    })            "reason": "Safe command",

                "policy_name": "command_policy",

    await db_session.commit()            "evaluated_at": datetime.now(timezone.utc),

                "evaluation_duration_ms": 10,

    denied = await repo.get_denied_decisions(test_session_model.id)        })

    assert len(denied) == 2        

    assert all(d.decision == "denied" for d in denied)        await repo.create({

            "session_id": test_session_model.id,

            "user_id": test_user.id,

@pytest.mark.asyncio            "tool_name": "Write",

async def test_find_by_tool_name(db_session: AsyncSession, test_session_model):            "tool_input": {"path": "/etc/passwd"},

    """Test finding permission decisions by tool name"""            "decision": "deny",

    repo = PermissionDecisionRepository(db_session)            "reason": "System file write blocked",

                "policy_name": "file_access_policy",

    await repo.create(**{            "evaluated_at": datetime.now(timezone.utc),

        "session_id": test_session_model.id,            "evaluation_duration_ms": 20,

        "tool_use_id": "toolu_bash_1",        })

        "tool_name": "bash_tool",

        "input_data": {"command": "ls"},        # Act

        "decision": "allowed",        denied = await repo.find_denied_decisions(test_session_model.id)

        "reason": "Permitted"

    })        # Assert

            assert len(denied) == 2

    await repo.create(**{        assert all(d.decision == "deny" for d in denied)

        "session_id": test_session_model.id,        reasons = [d.reason for d in denied]

        "tool_use_id": "toolu_python_1",        assert "Dangerous command" in reasons

        "tool_name": "python_tool",        assert "System file write blocked" in reasons

        "input_data": {"code": "print('test')"},

        "decision": "allowed",    async def test_find_by_tool_name(self, db_session, test_session_model, test_user):

        "reason": "Permitted"        """Test finding permission decisions by tool name."""

    })        # Arrange

            repo = PermissionDecisionRepository(db_session)

    await repo.create(**{        

        "session_id": test_session_model.id,        # Create decisions for different tools

        "tool_use_id": "toolu_bash_2",        for tool in ["Bash", "Write", "Read", "Bash", "Write"]:

        "tool_name": "bash_tool",            await repo.create({

        "input_data": {"command": "pwd"},                "session_id": test_session_model.id,

        "decision": "allowed",                "user_id": test_user.id,

        "reason": "Permitted"                "tool_name": tool,

    })                "tool_input": {},

                    "decision": "allow",

    await db_session.commit()                "reason": "Test",

                    "policy_name": "test_policy",

    bash_decisions = await repo.get_by_tool_name(test_session_model.id, "bash_tool")                "evaluated_at": datetime.now(timezone.utc),

    assert len(bash_decisions) == 2                "evaluation_duration_ms": 10,

    assert all(d.tool_name == "bash_tool" for d in bash_decisions)            })



        # Act

@pytest.mark.asyncio        bash_decisions = await repo.find_by_tool_name(test_session_model.id, "Bash")

async def test_decision_with_complex_context(db_session: AsyncSession, test_session_model):        write_decisions = await repo.find_by_tool_name(test_session_model.id, "Write")

    """Test permission decision with complex context data"""        read_decisions = await repo.find_by_tool_name(test_session_model.id, "Read")

    repo = PermissionDecisionRepository(db_session)

            # Assert

    complex_context = {        assert len(bash_decisions) == 2

        "working_directory": "/home/user/project",        assert len(write_decisions) == 2

        "environment": "production",        assert len(read_decisions) == 1

        "user_permissions": ["read", "write"],        assert all(d.tool_name == "Bash" for d in bash_decisions)

        "metadata": {

            "source": "cli",    async def test_find_by_policy_name(self, db_session, test_session_model, test_user):

            "version": "1.0.0"        """Test finding permission decisions by policy name."""

        }        # Arrange

    }        repo = PermissionDecisionRepository(db_session)

            

    decision = await repo.create(**{        # Create decisions with different policies

        "session_id": test_session_model.id,        await repo.create({

        "tool_use_id": "toolu_complex",            "session_id": test_session_model.id,

        "tool_name": "bash_tool",            "user_id": test_user.id,

        "input_data": {"command": "ls -la /home/user/project"},            "tool_name": "Bash",

        "context_data": complex_context,            "tool_input": {},

        "decision": "allowed",            "decision": "allow",

        "reason": "User has permissions in working directory"            "reason": "Test",

    })            "policy_name": "file_access_policy",

                "evaluated_at": datetime.now(timezone.utc),

    await db_session.commit()            "evaluation_duration_ms": 10,

            })

    retrieved = await repo.get_by_id(decision.id)        

    assert retrieved.context_data == complex_context        await repo.create({

    assert retrieved.context_data["environment"] == "production"            "session_id": test_session_model.id,

            "user_id": test_user.id,

            "tool_name": "Write",

@pytest.mark.asyncio            "tool_input": {},

async def test_get_nonexistent_decision(db_session: AsyncSession):            "decision": "deny",

    """Test retrieving a non-existent permission decision"""            "reason": "Test",

    repo = PermissionDecisionRepository(db_session)            "policy_name": "command_policy",

                "evaluated_at": datetime.now(timezone.utc),

    non_existent_id = uuid4()            "evaluation_duration_ms": 15,

    result = await repo.get_by_id(non_existent_id)        })

    assert result is None

        # Act

        file_policy_decisions = await repo.find_by_policy_name(test_session_model.id, "file_access_policy")

@pytest.mark.asyncio        command_policy_decisions = await repo.find_by_policy_name(test_session_model.id, "command_policy")

async def test_bypassed_decision(db_session: AsyncSession, test_session_model):

    """Test creating a bypassed permission decision"""        # Assert

    repo = PermissionDecisionRepository(db_session)        assert len(file_policy_decisions) == 1

            assert file_policy_decisions[0].policy_name == "file_access_policy"

    decision = await repo.create(**{        assert len(command_policy_decisions) == 1

        "session_id": test_session_model.id,        assert command_policy_decisions[0].policy_name == "command_policy"

        "tool_use_id": "toolu_bypass",

        "tool_name": "admin_tool",    async def test_get_decision_statistics(self, db_session, test_session_model, test_user):

        "input_data": {"action": "system_config"},        """Test getting decision statistics for a session."""

        "decision": "bypassed",        # Arrange

        "reason": "Admin override enabled"        repo = PermissionDecisionRepository(db_session)

    })        

            # Create various decisions

    await db_session.commit()        for i in range(7):

                await repo.create({

    retrieved = await repo.get_by_id(decision.id)                "session_id": test_session_model.id,

    assert retrieved.decision == "bypassed"                "user_id": test_user.id,

    assert "Admin override" in retrieved.reason                "tool_name": "Bash",

                "tool_input": {},

                "decision": "allow" if i < 5 else "deny",

@pytest.mark.asyncio                "reason": "Test",

async def test_count_by_decision(db_session: AsyncSession, test_session_model):                "policy_name": "test_policy",

    """Test counting decisions by type"""                "evaluated_at": datetime.now(timezone.utc),

    repo = PermissionDecisionRepository(db_session)                "evaluation_duration_ms": 10 + i * 3,

                })

    # Create various decisions

    for i in range(5):        # Act

        await repo.create(**{        stats = await repo.get_decision_statistics(test_session_model.id)

            "session_id": test_session_model.id,

            "tool_use_id": f"toolu_allowed_{i}",        # Assert

            "tool_name": "bash_tool",        assert stats["total_decisions"] == 7

            "input_data": {"command": "ls"},        assert stats["allowed_count"] == 5

            "decision": "allowed",        assert stats["denied_count"] == 2

            "reason": "Permitted"        assert stats["avg_evaluation_time_ms"] > 0

        })        assert stats["max_evaluation_time_ms"] >= stats["min_evaluation_time_ms"]

    

    for i in range(3):    async def test_find_by_user_id(self, db_session, test_session_model, test_user, admin_user):

        await repo.create(**{        """Test finding permission decisions by user ID."""

            "session_id": test_session_model.id,        # Arrange

            "tool_use_id": f"toolu_denied_{i}",        repo = PermissionDecisionRepository(db_session)

            "tool_name": "bash_tool",        

            "input_data": {"command": "rm"},        # Create decisions for different users

            "decision": "denied",        await repo.create({

            "reason": "Restricted"            "session_id": test_session_model.id,

        })            "user_id": test_user.id,

                "tool_name": "Bash",

    await db_session.commit()            "tool_input": {},

                "decision": "allow",

    allowed_count = await repo.count_by_decision(test_session_model.id, "allowed")            "reason": "Test user decision",

    denied_count = await repo.count_by_decision(test_session_model.id, "denied")            "policy_name": "test_policy",

                "evaluated_at": datetime.now(timezone.utc),

    assert allowed_count == 5            "evaluation_duration_ms": 10,

    assert denied_count == 3        })

        
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
