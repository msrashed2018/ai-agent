"""Unit tests for HookExecution domain entity."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.entities.hook_execution import HookExecution


class TestHookExecutionEntity:
    """Test cases for HookExecution entity."""

    def test_hook_execution_creation(self):
        """Test hook execution initialization."""
        hook_id = uuid4()
        session_id = uuid4()
        tool_call_id = uuid4()
        created_at = datetime.utcnow()
        
        input_data = {"param1": "value1", "param2": 123}
        output_data = {"result": "success", "data": "output"}
        context_data = {"user_id": str(uuid4()), "environment": "test"}

        hook_execution = HookExecution(
            id=hook_id,
            session_id=session_id,
            tool_call_id=tool_call_id,
            hook_name="pre_tool_use",
            tool_use_id="tool_123",
            tool_name="file_reader",
            input_data=input_data,
            output_data=output_data,
            context_data=context_data,
            execution_time_ms=250,
            created_at=created_at,
        )

        assert hook_execution.id == hook_id
        assert hook_execution.session_id == session_id
        assert hook_execution.tool_call_id == tool_call_id
        assert hook_execution.hook_name == "pre_tool_use"
        assert hook_execution.tool_use_id == "tool_123"
        assert hook_execution.tool_name == "file_reader"
        assert hook_execution.input_data == input_data
        assert hook_execution.output_data == output_data
        assert hook_execution.context_data == context_data
        assert hook_execution.execution_time_ms == 250
        assert hook_execution.created_at == created_at
        assert hook_execution.error_message is None

    def test_hook_execution_creation_with_error(self):
        """Test hook execution creation with error message."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=uuid4(),
            hook_name="post_tool_use",
            tool_use_id="tool_456",
            tool_name="file_writer",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=500,
            created_at=datetime.utcnow(),
            error_message="Hook execution failed: Permission denied",
        )

        assert hook_execution.error_message == "Hook execution failed: Permission denied"

    def test_hook_execution_without_tool_call_id(self):
        """Test hook execution creation without tool_call_id."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="custom_hook",
            tool_use_id="tool_789",
            tool_name="custom_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.tool_call_id is None

    def test_hook_execution_validation_negative_execution_time(self):
        """Test validation fails for negative execution time."""
        with pytest.raises(ValueError, match="Execution time cannot be negative"):
            HookExecution(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                hook_name="test_hook",
                tool_use_id="tool_123",
                tool_name="test_tool",
                input_data={},
                output_data={},
                context_data={},
                execution_time_ms=-50,
                created_at=datetime.utcnow(),
            )

    def test_hook_execution_validation_empty_hook_name(self):
        """Test validation fails for empty hook name."""
        with pytest.raises(ValueError, match="Hook name cannot be empty"):
            HookExecution(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                hook_name="   ",
                tool_use_id="tool_123",
                tool_name="test_tool",
                input_data={},
                output_data={},
                context_data={},
                execution_time_ms=100,
                created_at=datetime.utcnow(),
            )

    def test_hook_execution_validation_empty_tool_use_id(self):
        """Test validation fails for empty tool use ID."""
        with pytest.raises(ValueError, match="Tool use ID cannot be empty"):
            HookExecution(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                hook_name="test_hook",
                tool_use_id="",
                tool_name="test_tool",
                input_data={},
                output_data={},
                context_data={},
                execution_time_ms=100,
                created_at=datetime.utcnow(),
            )

    def test_hook_execution_validation_empty_tool_name(self):
        """Test validation fails for empty tool name."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            HookExecution(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                hook_name="test_hook",
                tool_use_id="tool_123",
                tool_name="",
                input_data={},
                output_data={},
                context_data={},
                execution_time_ms=100,
                created_at=datetime.utcnow(),
            )

    def test_is_successful_no_error(self):
        """Test is_successful returns True when no error."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.is_successful() is True
        assert hook_execution.is_failed() is False

    def test_is_failed_with_error(self):
        """Test is_failed returns True when error exists."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
            error_message="Something went wrong",
        )

        assert hook_execution.is_successful() is False
        assert hook_execution.is_failed() is True

    def test_get_hook_type_pre_hook(self):
        """Test get_hook_type for pre hook."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="pre_tool_use",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.get_hook_type() == "pre"

    def test_get_hook_type_post_hook(self):
        """Test get_hook_type for post hook."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="post_tool_use",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.get_hook_type() == "post"

    def test_get_hook_type_custom_hook(self):
        """Test get_hook_type for custom hook."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="custom_validation_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.get_hook_type() == "custom"

    def test_get_hook_type_no_underscore(self):
        """Test get_hook_type for hook name without underscore."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="VALIDATION",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_execution.get_hook_type() == "validation"

    def test_get_execution_time_seconds(self):
        """Test get_execution_time_seconds conversion."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=2500,  # 2.5 seconds
            created_at=datetime.utcnow(),
        )

        assert hook_execution.get_execution_time_seconds() == 2.5

    def test_is_slow_execution_default_threshold(self):
        """Test is_slow_execution with default threshold (1 second)."""
        fast_hook = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="fast_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=500,  # 0.5 seconds
            created_at=datetime.utcnow(),
        )

        slow_hook = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="slow_hook",
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=1500,  # 1.5 seconds
            created_at=datetime.utcnow(),
        )

        assert fast_hook.is_slow_execution() is False
        assert slow_hook.is_slow_execution() is True

    def test_is_slow_execution_custom_threshold(self):
        """Test is_slow_execution with custom threshold."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=750,
            created_at=datetime.utcnow(),
        )

        # With 500ms threshold, 750ms is slow
        assert hook_execution.is_slow_execution(threshold_ms=500) is True
        
        # With 1000ms threshold, 750ms is not slow
        assert hook_execution.is_slow_execution(threshold_ms=1000) is False

    def test_has_input_data(self):
        """Test has_input_data method."""
        hook_with_input = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={"param": "value"},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        hook_without_input = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_with_input.has_input_data() is True
        assert hook_without_input.has_input_data() is False

    def test_has_output_data(self):
        """Test has_output_data method."""
        hook_with_output = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={"result": "success"},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        hook_without_output = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_with_output.has_output_data() is True
        assert hook_without_output.has_output_data() is False

    def test_has_context_data(self):
        """Test has_context_data method."""
        hook_with_context = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={"user": "test_user"},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        hook_without_context = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        assert hook_with_context.has_context_data() is True
        assert hook_without_context.has_context_data() is False

    def test_hook_execution_immutability(self):
        """Test that HookExecution is immutable (frozen dataclass)."""
        hook_execution = HookExecution(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            hook_name="test_hook",
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            output_data={},
            context_data={},
            execution_time_ms=100,
            created_at=datetime.utcnow(),
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            hook_execution.hook_name = "modified_hook"

        with pytest.raises(AttributeError):
            hook_execution.execution_time_ms = 200