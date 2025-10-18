"""Unit tests for ToolCallRepository."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.repositories.tool_call_repository import ToolCallRepository
from app.models.tool_call import ToolCallModel


class TestToolCallRepository:
    """Test cases for ToolCallRepository."""

    @pytest_asyncio.fixture
    async def tool_call_repository(self, db_session):
        """Create ToolCallRepository instance."""
        return ToolCallRepository(db_session)

    @pytest_asyncio.fixture
    async def test_tool_call(self, db_session, test_session_model):
        """Create a test tool call."""
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="bash",
            tool_use_id="toolu_test_123",
            tool_input={"command": "ls -la"},
            status="pending",
            is_error=False,
        )
        db_session.add(tool_call)
        await db_session.commit()
        await db_session.refresh(tool_call)
        return tool_call

    @pytest_asyncio.fixture
    async def completed_tool_call(self, db_session, test_session_model):
        """Create a completed tool call."""
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="grep",
            tool_use_id="toolu_test_456",
            tool_input={"pattern": "error", "path": "/var/log"},
            tool_output={"matches": ["line 1", "line 2"]},
            status="success",
            is_error=False,
            started_at=datetime.utcnow() - timedelta(seconds=10),
            completed_at=datetime.utcnow(),
            duration_ms=500,
        )
        db_session.add(tool_call)
        await db_session.commit()
        await db_session.refresh(tool_call)
        return tool_call

    @pytest_asyncio.fixture
    async def pending_permission_tool_call(self, db_session, test_session_model):
        """Create a tool call pending permission decision."""
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="edit",
            tool_use_id="toolu_test_789",
            tool_input={"file": "config.yaml", "content": "new content"},
            status="pending",
            is_error=False,
            permission_decision=None,
        )
        db_session.add(tool_call)
        await db_session.commit()
        await db_session.refresh(tool_call)
        return tool_call

    # Test: create (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_create_tool_call(self, db_session, tool_call_repository, test_session_model):
        """Test creating a new tool call."""
        # Arrange
        tool_call_id = uuid4()
        tool_call_data = {
            "id": tool_call_id,
            "session_id": test_session_model.id,
            "tool_name": "read",
            "tool_use_id": "toolu_new_001",
            "tool_input": {"file_path": "/etc/hosts"},
            "status": "pending",
            "is_error": False,
        }

        # Act
        created = await tool_call_repository.create(**tool_call_data)

        # Assert
        assert created is not None
        assert created.id == tool_call_id
        assert created.tool_name == "read"
        assert created.tool_use_id == "toolu_new_001"
        assert created.status == "pending"
        assert created.session_id == test_session_model.id
        assert created.created_at is not None

    # Test: get_by_id (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, db_session, tool_call_repository, test_tool_call):
        """Test getting tool call by ID when it exists."""
        # Act
        result = await tool_call_repository.get_by_id(test_tool_call.id)

        # Assert
        assert result is not None
        assert result.id == test_tool_call.id
        assert result.tool_name == test_tool_call.tool_name
        assert result.tool_use_id == test_tool_call.tool_use_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session, tool_call_repository):
        """Test getting tool call by non-existent ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await tool_call_repository.get_by_id(non_existent_id)

        # Assert
        assert result is None

    # Test: get_by_session
    @pytest.mark.asyncio
    async def test_get_by_session(self, db_session, tool_call_repository, test_session_model, test_tool_call, completed_tool_call):
        """Test getting all tool calls for a session."""
        # Act
        result = await tool_call_repository.get_by_session(test_session_model.id)

        # Assert
        assert len(result) >= 2
        tool_use_ids = [tc.tool_use_id for tc in result]
        assert test_tool_call.tool_use_id in tool_use_ids
        assert completed_tool_call.tool_use_id in tool_use_ids

    @pytest.mark.asyncio
    async def test_get_by_session_ordered_by_created_at(self, db_session, tool_call_repository, test_session_model):
        """Test tool calls are ordered by creation time."""
        # Arrange: Create tool calls with different timestamps
        old_tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="tool_old",
            tool_use_id="toolu_old",
            tool_input={},
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="tool_new",
            tool_use_id="toolu_new",
            tool_input={},
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_tool_call, new_tool_call])
        await db_session.commit()

        # Act
        result = await tool_call_repository.get_by_session(test_session_model.id)

        # Assert
        assert len(result) >= 2
        # Find our test tool calls in the result
        old_idx = next(i for i, tc in enumerate(result) if tc.tool_use_id == "toolu_old")
        new_idx = next(i for i, tc in enumerate(result) if tc.tool_use_id == "toolu_new")
        assert old_idx < new_idx  # Old should come before new

    @pytest.mark.asyncio
    async def test_get_by_session_with_pagination(self, db_session, tool_call_repository, test_session_model):
        """Test pagination with skip and limit."""
        # Arrange: Create multiple tool calls
        for i in range(5):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                tool_name=f"tool_{i}",
                tool_use_id=f"toolu_page_{i}",
                tool_input={},
            )
            db_session.add(tool_call)
        await db_session.commit()

        # Act
        page1 = await tool_call_repository.get_by_session(test_session_model.id, skip=0, limit=2)
        page2 = await tool_call_repository.get_by_session(test_session_model.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_by_session_empty(self, db_session, tool_call_repository):
        """Test getting tool calls for session with no tool calls."""
        # Arrange
        non_existent_session_id = uuid4()

        # Act
        result = await tool_call_repository.get_by_session(non_existent_session_id)

        # Assert
        assert result == []

    # Test: get_by_tool_use_id
    @pytest.mark.asyncio
    async def test_get_by_tool_use_id_exists(self, db_session, tool_call_repository, test_tool_call):
        """Test getting tool call by tool_use_id when it exists."""
        # Act
        result = await tool_call_repository.get_by_tool_use_id(test_tool_call.tool_use_id)

        # Assert
        assert result is not None
        assert result.id == test_tool_call.id
        assert result.tool_use_id == test_tool_call.tool_use_id

    @pytest.mark.asyncio
    async def test_get_by_tool_use_id_not_found(self, db_session, tool_call_repository):
        """Test getting tool call by non-existent tool_use_id."""
        # Act
        result = await tool_call_repository.get_by_tool_use_id("toolu_nonexistent")

        # Assert
        assert result is None

    # Test: get_by_status
    @pytest.mark.asyncio
    async def test_get_by_status(self, db_session, tool_call_repository, test_tool_call, completed_tool_call):
        """Test getting tool calls by status."""
        # Act
        pending = await tool_call_repository.get_by_status("pending")
        success = await tool_call_repository.get_by_status("success")

        # Assert
        assert len(pending) >= 1
        assert any(tc.tool_use_id == test_tool_call.tool_use_id for tc in pending)
        assert len(success) >= 1
        assert any(tc.tool_use_id == completed_tool_call.tool_use_id for tc in success)

    @pytest.mark.asyncio
    async def test_get_by_status_with_session_filter(self, db_session, tool_call_repository, test_session_model, test_tool_call):
        """Test getting tool calls by status filtered by session."""
        # Act
        result = await tool_call_repository.get_by_status("pending", session_id=test_session_model.id)

        # Assert
        assert len(result) >= 1
        assert all(tc.session_id == test_session_model.id for tc in result)
        assert all(tc.status == "pending" for tc in result)

    @pytest.mark.asyncio
    async def test_get_by_status_not_found(self, db_session, tool_call_repository):
        """Test getting tool calls with status that doesn't exist."""
        # Act
        result = await tool_call_repository.get_by_status("nonexistent_status")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_status_with_pagination(self, db_session, tool_call_repository, test_session_model):
        """Test status filtering with pagination."""
        # Arrange: Create multiple pending tool calls
        for i in range(5):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                tool_name=f"tool_{i}",
                tool_use_id=f"toolu_status_{i}",
                tool_input={},
                status="pending",
            )
            db_session.add(tool_call)
        await db_session.commit()

        # Act
        page1 = await tool_call_repository.get_by_status("pending", skip=0, limit=2)
        page2 = await tool_call_repository.get_by_status("pending", skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert all(tc.status == "pending" for tc in page1)
        assert all(tc.status == "pending" for tc in page2)

    # Test: get_by_tool_name
    @pytest.mark.asyncio
    async def test_get_by_tool_name(self, db_session, tool_call_repository, test_tool_call):
        """Test getting tool calls by tool name."""
        # Act
        result = await tool_call_repository.get_by_tool_name("bash")

        # Assert
        assert len(result) >= 1
        assert any(tc.tool_use_id == test_tool_call.tool_use_id for tc in result)
        assert all(tc.tool_name == "bash" for tc in result)

    @pytest.mark.asyncio
    async def test_get_by_tool_name_with_session_filter(self, db_session, tool_call_repository, test_session_model, test_tool_call):
        """Test getting tool calls by tool name filtered by session."""
        # Act
        result = await tool_call_repository.get_by_tool_name("bash", session_id=test_session_model.id)

        # Assert
        assert len(result) >= 1
        assert all(tc.session_id == test_session_model.id for tc in result)
        assert all(tc.tool_name == "bash" for tc in result)

    @pytest.mark.asyncio
    async def test_get_by_tool_name_ordered_desc(self, db_session, tool_call_repository, test_session_model):
        """Test tool calls by name are ordered by created_at descending."""
        # Arrange: Create tool calls with same name but different timestamps
        old_tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="test_tool",
            tool_use_id="toolu_tool_old",
            tool_input={},
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        new_tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="test_tool",
            tool_use_id="toolu_tool_new",
            tool_input={},
            created_at=datetime.utcnow(),
        )
        db_session.add_all([old_tool_call, new_tool_call])
        await db_session.commit()

        # Act
        result = await tool_call_repository.get_by_tool_name("test_tool")

        # Assert
        assert len(result) >= 2
        # Find our test tool calls in the result
        new_idx = next(i for i, tc in enumerate(result) if tc.tool_use_id == "toolu_tool_new")
        old_idx = next(i for i, tc in enumerate(result) if tc.tool_use_id == "toolu_tool_old")
        assert new_idx < old_idx  # New should come before old (DESC order)

    @pytest.mark.asyncio
    async def test_get_by_tool_name_not_found(self, db_session, tool_call_repository):
        """Test getting tool calls with tool name that doesn't exist."""
        # Act
        result = await tool_call_repository.get_by_tool_name("nonexistent_tool")

        # Assert
        assert result == []

    # Test: get_pending_for_permission
    @pytest.mark.asyncio
    async def test_get_pending_for_permission(self, db_session, tool_call_repository, pending_permission_tool_call):
        """Test getting pending tool calls awaiting permission."""
        # Act
        result = await tool_call_repository.get_pending_for_permission()

        # Assert
        assert len(result) >= 1
        assert any(tc.tool_use_id == pending_permission_tool_call.tool_use_id for tc in result)
        assert all(tc.status == "pending" for tc in result)
        assert all(tc.permission_decision is None for tc in result)

    @pytest.mark.asyncio
    async def test_get_pending_for_permission_with_session(self, db_session, tool_call_repository, test_session_model, pending_permission_tool_call):
        """Test getting pending permission tool calls filtered by session."""
        # Act
        result = await tool_call_repository.get_pending_for_permission(session_id=test_session_model.id)

        # Assert
        assert len(result) >= 1
        assert all(tc.session_id == test_session_model.id for tc in result)
        assert all(tc.status == "pending" for tc in result)
        assert all(tc.permission_decision is None for tc in result)

    @pytest.mark.asyncio
    async def test_get_pending_for_permission_excludes_decided(self, db_session, tool_call_repository, test_session_model):
        """Test that tool calls with permission decisions are excluded."""
        # Arrange: Create tool call with permission decision
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="delete",
            tool_use_id="toolu_decided",
            tool_input={},
            status="pending",
            permission_decision="allow",
        )
        db_session.add(tool_call)
        await db_session.commit()

        # Act
        result = await tool_call_repository.get_pending_for_permission(session_id=test_session_model.id)

        # Assert
        assert not any(tc.tool_use_id == "toolu_decided" for tc in result)

    @pytest.mark.asyncio
    async def test_get_pending_for_permission_excludes_non_pending(self, db_session, tool_call_repository, test_session_model):
        """Test that non-pending tool calls are excluded."""
        # Arrange: Create running tool call without permission decision
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=test_session_model.id,
            tool_name="running_tool",
            tool_use_id="toolu_running",
            tool_input={},
            status="running",
            permission_decision=None,
        )
        db_session.add(tool_call)
        await db_session.commit()

        # Act
        result = await tool_call_repository.get_pending_for_permission(session_id=test_session_model.id)

        # Assert
        assert not any(tc.tool_use_id == "toolu_running" for tc in result)

    # Test: update_status
    @pytest.mark.asyncio
    async def test_update_status_to_running(self, db_session, tool_call_repository, test_tool_call):
        """Test updating tool call status to running."""
        # Act
        success = await tool_call_repository.update_status(test_tool_call.id, "running")
        await db_session.refresh(test_tool_call)

        # Assert
        assert success is True
        assert test_tool_call.status == "running"
        assert test_tool_call.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_success(self, db_session, tool_call_repository, test_tool_call):
        """Test updating tool call status to success."""
        # Act
        success = await tool_call_repository.update_status(test_tool_call.id, "success")
        await db_session.refresh(test_tool_call)

        # Assert
        assert success is True
        assert test_tool_call.status == "success"
        assert test_tool_call.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_to_error_with_message(self, db_session, tool_call_repository, test_tool_call):
        """Test updating tool call status to error with error message."""
        # Act
        success = await tool_call_repository.update_status(
            test_tool_call.id,
            "error",
            error_message="Command failed with exit code 1"
        )
        await db_session.refresh(test_tool_call)

        # Assert
        assert success is True
        assert test_tool_call.status == "error"
        assert test_tool_call.is_error is True
        assert test_tool_call.error_message == "Command failed with exit code 1"
        assert test_tool_call.completed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, db_session, tool_call_repository):
        """Test updating status of non-existent tool call."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await tool_call_repository.update_status(non_existent_id, "success")

        # Assert
        assert success is False

    @pytest.mark.asyncio
    async def test_update_status_updates_updated_at(self, db_session, tool_call_repository, test_tool_call):
        """Test that update_status updates the updated_at timestamp."""
        # Arrange
        original_updated_at = test_tool_call.updated_at

        # Act
        await tool_call_repository.update_status(test_tool_call.id, "running")
        await db_session.refresh(test_tool_call)

        # Assert
        assert test_tool_call.updated_at > original_updated_at

    # Test: set_permission_decision
    @pytest.mark.asyncio
    async def test_set_permission_decision_allow(self, db_session, tool_call_repository, pending_permission_tool_call):
        """Test setting permission decision to allow."""
        # Act
        success = await tool_call_repository.set_permission_decision(
            pending_permission_tool_call.id,
            "allow",
            reason="User approved"
        )
        await db_session.refresh(pending_permission_tool_call)

        # Assert
        assert success is True
        assert pending_permission_tool_call.permission_decision == "allow"
        assert pending_permission_tool_call.permission_reason == "User approved"
        assert pending_permission_tool_call.status == "pending"  # Status should remain pending

    @pytest.mark.asyncio
    async def test_set_permission_decision_deny(self, db_session, tool_call_repository, pending_permission_tool_call):
        """Test setting permission decision to deny."""
        # Act
        success = await tool_call_repository.set_permission_decision(
            pending_permission_tool_call.id,
            "deny",
            reason="Too risky"
        )
        await db_session.refresh(pending_permission_tool_call)

        # Assert
        assert success is True
        assert pending_permission_tool_call.permission_decision == "deny"
        assert pending_permission_tool_call.permission_reason == "Too risky"
        assert pending_permission_tool_call.status == "denied"  # Status should change to denied

    @pytest.mark.asyncio
    async def test_set_permission_decision_without_reason(self, db_session, tool_call_repository, pending_permission_tool_call):
        """Test setting permission decision without reason."""
        # Act
        success = await tool_call_repository.set_permission_decision(
            pending_permission_tool_call.id,
            "allow"
        )
        await db_session.refresh(pending_permission_tool_call)

        # Assert
        assert success is True
        assert pending_permission_tool_call.permission_decision == "allow"
        assert pending_permission_tool_call.permission_reason is None

    @pytest.mark.asyncio
    async def test_set_permission_decision_not_found(self, db_session, tool_call_repository):
        """Test setting permission decision on non-existent tool call."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await tool_call_repository.set_permission_decision(non_existent_id, "allow")

        # Assert
        assert success is False

    # Test: set_output
    @pytest.mark.asyncio
    async def test_set_output_success(self, db_session, tool_call_repository, test_tool_call):
        """Test setting successful tool output."""
        # Arrange
        output = {"stdout": "total 48\ndrwxr-xr-x 12 user user 4096"}

        # Act
        success = await tool_call_repository.set_output(test_tool_call.id, output, is_error=False)
        await db_session.refresh(test_tool_call)

        # Assert
        assert success is True
        assert test_tool_call.tool_output == output
        assert test_tool_call.is_error is False
        assert test_tool_call.status == "success"
        assert test_tool_call.completed_at is not None

    @pytest.mark.asyncio
    async def test_set_output_error(self, db_session, tool_call_repository, test_tool_call):
        """Test setting error tool output."""
        # Arrange
        output = {"error": "Command not found"}

        # Act
        success = await tool_call_repository.set_output(test_tool_call.id, output, is_error=True)
        await db_session.refresh(test_tool_call)

        # Assert
        assert success is True
        assert test_tool_call.tool_output == output
        assert test_tool_call.is_error is True
        assert test_tool_call.status == "error"
        assert test_tool_call.completed_at is not None

    @pytest.mark.asyncio
    async def test_set_output_not_found(self, db_session, tool_call_repository):
        """Test setting output on non-existent tool call."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        success = await tool_call_repository.set_output(non_existent_id, {"output": "test"})

        # Assert
        assert success is False

    # Test: count_by_session
    @pytest.mark.asyncio
    async def test_count_by_session(self, db_session, tool_call_repository, test_session_model, test_tool_call, completed_tool_call):
        """Test counting tool calls in a session."""
        # Act
        count = await tool_call_repository.count_by_session(test_session_model.id)

        # Assert
        assert count >= 2  # At least our two test tool calls

    @pytest.mark.asyncio
    async def test_count_by_session_empty(self, db_session, tool_call_repository):
        """Test counting tool calls for session with no tool calls."""
        # Arrange
        non_existent_session_id = uuid4()

        # Act
        count = await tool_call_repository.count_by_session(non_existent_session_id)

        # Assert
        assert count == 0

    # Test: get_statistics_by_tool
    @pytest.mark.asyncio
    async def test_get_statistics_by_tool(self, db_session, tool_call_repository, test_session_model):
        """Test getting tool call statistics grouped by tool name."""
        # Arrange: Create multiple tool calls for statistics
        for i in range(3):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                tool_name="bash",
                tool_use_id=f"toolu_stat_bash_{i}",
                tool_input={},
                status="success" if i < 2 else "error",
                duration_ms=100 + i * 50,
            )
            db_session.add(tool_call)

        for i in range(2):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                tool_name="grep",
                tool_use_id=f"toolu_stat_grep_{i}",
                tool_input={},
                status="success",
                duration_ms=50 + i * 25,
            )
            db_session.add(tool_call)

        await db_session.commit()

        # Act
        stats = await tool_call_repository.get_statistics_by_tool()

        # Assert
        assert len(stats) >= 2
        bash_stats = next((s for s in stats if s["tool_name"] == "bash"), None)
        grep_stats = next((s for s in stats if s["tool_name"] == "grep"), None)

        assert bash_stats is not None
        assert bash_stats["total_calls"] >= 3
        assert bash_stats["success_count"] >= 2
        assert bash_stats["error_count"] >= 1

        assert grep_stats is not None
        assert grep_stats["total_calls"] >= 2
        assert grep_stats["success_count"] >= 2

    @pytest.mark.asyncio
    async def test_get_statistics_by_tool_with_session_filter(self, db_session, tool_call_repository, test_session_model, test_user):
        """Test getting tool statistics filtered by session."""
        # Arrange: Create another session with tool calls
        from app.models.session import SessionModel
        other_session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Other Session",
            mode="interactive",
            status="active",
            sdk_options={},
        )
        db_session.add(other_session)
        await db_session.commit()

        # Add tool call to other session
        tool_call = ToolCallModel(
            id=uuid4(),
            session_id=other_session.id,
            tool_name="other_tool",
            tool_use_id="toolu_other",
            tool_input={},
            status="success",
        )
        db_session.add(tool_call)
        await db_session.commit()

        # Act
        stats = await tool_call_repository.get_statistics_by_tool(session_id=test_session_model.id)

        # Assert
        tool_names = [s["tool_name"] for s in stats]
        assert "other_tool" not in tool_names  # Should not include tool from other session

    @pytest.mark.asyncio
    async def test_get_statistics_by_tool_avg_duration(self, db_session, tool_call_repository, test_session_model):
        """Test that average duration is calculated correctly."""
        # Arrange: Create tool calls with known durations
        durations = [100, 200, 300]
        for i, duration in enumerate(durations):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                tool_name="timed_tool",
                tool_use_id=f"toolu_timed_{i}",
                tool_input={},
                status="success",
                duration_ms=duration,
            )
            db_session.add(tool_call)
        await db_session.commit()

        # Act
        stats = await tool_call_repository.get_statistics_by_tool(session_id=test_session_model.id)

        # Assert
        timed_stats = next((s for s in stats if s["tool_name"] == "timed_tool"), None)
        assert timed_stats is not None
        assert timed_stats["avg_duration_ms"] == 200.0  # (100 + 200 + 300) / 3

    @pytest.mark.asyncio
    async def test_get_statistics_by_tool_empty(self, db_session, tool_call_repository):
        """Test getting statistics when no tool calls exist."""
        # Arrange
        non_existent_session_id = uuid4()

        # Act
        stats = await tool_call_repository.get_statistics_by_tool(session_id=non_existent_session_id)

        # Assert
        assert stats == []

    # Test: update (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_update_tool_call(self, db_session, tool_call_repository, test_tool_call):
        """Test updating a tool call."""
        # Act
        updated = await tool_call_repository.update(
            test_tool_call.id,
            tool_output={"result": "updated"},
            status="success"
        )

        # Assert
        assert updated is not None
        assert updated.tool_output == {"result": "updated"}
        assert updated.status == "success"

    # Test: delete (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_delete_tool_call(self, db_session, tool_call_repository, test_tool_call):
        """Test deleting a tool call."""
        # Arrange
        tool_call_id = test_tool_call.id

        # Act
        success = await tool_call_repository.delete(tool_call_id)

        # Assert
        assert success is True
        deleted = await tool_call_repository.get_by_id(tool_call_id)
        assert deleted is None
