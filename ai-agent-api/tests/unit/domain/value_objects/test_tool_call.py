"""Unit tests for ToolCall value object."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.value_objects.tool_call import ToolCall, ToolCallStatus, PermissionDecision


class TestToolCallValueObject:
    """Test cases for ToolCall value object."""

    def test_tool_call_create_pending(self):
        """Test creating pending tool call."""
        session_id = uuid4()
        tool_name = "mcp__kubernetes__list_pods"
        tool_use_id = "tool_use_123"
        tool_input = {"namespace": "default"}

        tool_call = ToolCall.create_pending(
            session_id=session_id,
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            tool_input=tool_input,
        )

        assert tool_call.session_id == session_id
        assert tool_call.tool_name == tool_name
        assert tool_call.tool_use_id == tool_use_id
        assert tool_call.tool_input == tool_input
        assert tool_call.status == ToolCallStatus.PENDING
        assert tool_call.created_at is not None

    def test_tool_call_with_status(self):
        """Test updating tool call status."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        updated = tool_call.with_status(ToolCallStatus.RUNNING)

        assert tool_call.status == ToolCallStatus.PENDING  # Original unchanged
        assert updated.status == ToolCallStatus.RUNNING

    def test_tool_call_with_permission(self):
        """Test adding permission decision."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        updated = tool_call.with_permission(
            decision=PermissionDecision.ALLOW,
            reason="Tool in allowed list"
        )

        assert updated.permission_decision == PermissionDecision.ALLOW
        assert updated.permission_reason == "Tool in allowed list"

    def test_tool_call_with_output_success(self):
        """Test marking tool call as successful with output."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        ).with_started()

        output = {"pods": ["pod1", "pod2"]}
        updated = tool_call.with_output(output, is_error=False)

        assert updated.tool_output == output
        assert updated.is_error is False
        assert updated.status == ToolCallStatus.SUCCESS
        assert updated.completed_at is not None

    def test_tool_call_with_output_error(self):
        """Test marking tool call as error."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        ).with_started()

        error_msg = "Connection timeout"
        updated = tool_call.with_output(
            {"error": error_msg},
            is_error=True,
            error_message=error_msg
        )

        assert updated.is_error is True
        assert updated.error_message == error_msg
        assert updated.status == ToolCallStatus.ERROR

    def test_tool_call_with_started(self):
        """Test marking tool call as started."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        assert tool_call.started_at is None
        assert tool_call.status == ToolCallStatus.PENDING

        updated = tool_call.with_started()

        assert updated.started_at is not None
        assert updated.status == ToolCallStatus.RUNNING

    def test_tool_call_duration_calculation(self):
        """Test duration calculation from started_at to completed_at."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        ).with_started()

        # Create updated version with output after some time
        updated = tool_call.with_output({"result": "done"})

        assert updated.duration_ms is not None
        assert updated.duration_ms >= 0

    def test_tool_call_is_pending(self):
        """Test is_pending method."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        assert tool_call.is_pending() is True

        updated = tool_call.with_started()
        assert updated.is_pending() is False

    def test_tool_call_is_running(self):
        """Test is_running method."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        assert tool_call.is_running() is False

        updated = tool_call.with_started()
        assert updated.is_running() is True

    def test_tool_call_is_completed(self):
        """Test is_completed method."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        ).with_started()

        assert tool_call.is_completed() is False

        success = tool_call.with_output({"result": "ok"}, is_error=False)
        assert success.is_completed() is True

        error = tool_call.with_output({"error": "fail"}, is_error=True)
        assert error.is_completed() is True

    def test_tool_call_is_denied(self):
        """Test is_denied method."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        # Manually set status to DENIED
        from dataclasses import replace
        denied = replace(tool_call, status=ToolCallStatus.DENIED)

        assert denied.is_denied() is True
        assert tool_call.is_denied() is False

    def test_tool_call_immutability(self):
        """Test ToolCall immutability."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
        )

        with pytest.raises(AttributeError):
            tool_call.status = ToolCallStatus.RUNNING

    def test_tool_call_status_enum(self):
        """Test ToolCallStatus enum."""
        assert ToolCallStatus.PENDING == "pending"
        assert ToolCallStatus.RUNNING == "running"
        assert ToolCallStatus.SUCCESS == "success"
        assert ToolCallStatus.ERROR == "error"
        assert ToolCallStatus.DENIED == "denied"

    def test_permission_decision_enum(self):
        """Test PermissionDecision enum."""
        assert PermissionDecision.ALLOW == "allow"
        assert PermissionDecision.DENY == "deny"
        assert PermissionDecision.ASK == "ask"

    def test_tool_call_with_message_id(self):
        """Test tool call with message ID."""
        message_id = uuid4()
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="test",
            tool_use_id="123",
            tool_input={},
            message_id=message_id,
        )

        assert tool_call.message_id == message_id

    def test_tool_call_complex_workflow(self):
        """Test complete tool call workflow."""
        tool_call = ToolCall.create_pending(
            session_id=uuid4(),
            tool_name="mcp__kubernetes__list_pods",
            tool_use_id="tool_123",
            tool_input={"namespace": "default"},
        )

        # Add permission
        tool_call = tool_call.with_permission(
            PermissionDecision.ALLOW,
            "Tool in allowed list"
        )

        # Start execution
        tool_call = tool_call.with_started()

        # Complete successfully
        tool_call = tool_call.with_output(
            {"pods": ["pod1", "pod2"]},
            is_error=False
        )

        assert tool_call.status == ToolCallStatus.SUCCESS
        assert tool_call.permission_decision == PermissionDecision.ALLOW
        assert tool_call.is_completed() is True
        assert tool_call.duration_ms is not None
