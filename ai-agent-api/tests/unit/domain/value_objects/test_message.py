"""Unit tests for Message value object."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.value_objects.message import Message, MessageType


class TestMessageValueObject:
    """Test cases for Message value object."""

    def test_message_factory_from_user_text(self):
        """Test creating user message from text."""
        session_id = uuid4()
        text = "What is 2+2?"

        message = Message.from_user_text(session_id, text, 1)

        assert message.session_id == session_id
        assert message.message_type == MessageType.USER
        assert message.content == {"content": text}
        assert message.sequence_number == 1
        assert message.created_at is not None
        assert message.model is None

    def test_message_factory_from_assistant(self):
        """Test creating assistant message."""
        session_id = uuid4()
        content = {"content": [{"type": "text", "text": "2+2=4"}]}

        message = Message.from_assistant(session_id, content, 2, model="claude-sonnet-4-5")

        assert message.session_id == session_id
        assert message.message_type == MessageType.ASSISTANT
        assert message.content == content
        assert message.sequence_number == 2
        assert message.model == "claude-sonnet-4-5"
        assert message.created_at is not None

    def test_message_factory_from_system(self):
        """Test creating system message."""
        session_id = uuid4()
        content = {"message": "System initialized"}

        message = Message.from_system(session_id, content, 1)

        assert message.session_id == session_id
        assert message.message_type == MessageType.SYSTEM
        assert message.content == content
        assert message.sequence_number == 1
        assert message.created_at is not None

    def test_message_factory_from_result(self):
        """Test creating result message."""
        session_id = uuid4()
        content = {"result": "success", "data": {"key": "value"}}

        message = Message.from_result(session_id, content, 5)

        assert message.session_id == session_id
        assert message.message_type == MessageType.RESULT
        assert message.content == content
        assert message.sequence_number == 5
        assert message.created_at is not None

    def test_message_is_user_message(self):
        """Test is_user_message method."""
        session_id = uuid4()

        user_message = Message.from_user_text(session_id, "test", 1)
        assistant_message = Message.from_assistant(session_id, {}, 2)

        assert user_message.is_user_message() is True
        assert assistant_message.is_user_message() is False

    def test_message_is_assistant_message(self):
        """Test is_assistant_message method."""
        session_id = uuid4()

        user_message = Message.from_user_text(session_id, "test", 1)
        assistant_message = Message.from_assistant(session_id, {}, 2)

        assert assistant_message.is_assistant_message() is True
        assert user_message.is_assistant_message() is False

    def test_message_is_system_message(self):
        """Test is_system_message method."""
        session_id = uuid4()

        user_message = Message.from_user_text(session_id, "test", 1)
        system_message = Message.from_system(session_id, {}, 1)

        assert system_message.is_system_message() is True
        assert user_message.is_system_message() is False

    def test_message_is_result_message(self):
        """Test is_result_message method."""
        session_id = uuid4()

        user_message = Message.from_user_text(session_id, "test", 1)
        result_message = Message.from_result(session_id, {}, 5)

        assert result_message.is_result_message() is True
        assert user_message.is_result_message() is False

    def test_message_get_text_content(self):
        """Test extracting text content."""
        session_id = uuid4()

        message = Message.from_user_text(session_id, "Hello world", 1)
        assert message.get_text_content() == "Hello world"

        # Message without text content
        complex_content = Message.from_assistant(
            session_id,
            {"content": [{"type": "tool_use", "id": "123"}]},
            2
        )
        assert complex_content.get_text_content() is None

    def test_message_immutability(self):
        """Test that Message is immutable (frozen dataclass)."""
        message = Message.from_user_text(uuid4(), "test", 1)

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            message.sequence_number = 2

    def test_message_equality(self):
        """Test message equality based on values."""
        session_id = uuid4()
        message_id = uuid4()

        message1 = Message(
            id=message_id,
            session_id=session_id,
            message_type=MessageType.USER,
            content={"content": "test"},
            sequence_number=1,
            created_at=datetime.utcnow(),
        )

        message2 = Message(
            id=message_id,
            session_id=session_id,
            message_type=MessageType.USER,
            content={"content": "test"},
            sequence_number=1,
            created_at=message1.created_at,
        )

        assert message1 == message2

    def test_message_with_parent_tool_use_id(self):
        """Test message with parent tool use ID."""
        session_id = uuid4()
        tool_use_id = "tool_use_123"

        message = Message.from_assistant(
            session_id,
            {"result": "executed"},
            2,
            model="claude-sonnet-4-5",
        )

        # Create message with parent tool use by reconstructing
        result_message = Message(
            id=uuid4(),
            session_id=session_id,
            message_type=MessageType.RESULT,
            content={"result": "tool executed"},
            sequence_number=3,
            created_at=datetime.utcnow(),
            parent_tool_use_id=tool_use_id,
        )

        assert result_message.parent_tool_use_id == tool_use_id

    def test_message_types_enum(self):
        """Test MessageType enum values."""
        assert MessageType.USER == "user"
        assert MessageType.ASSISTANT == "assistant"
        assert MessageType.SYSTEM == "system"
        assert MessageType.RESULT == "result"

    def test_message_with_empty_content(self):
        """Test message with empty content."""
        message = Message.from_assistant(uuid4(), {}, 1)
        assert message.content == {}
        assert message.get_text_content() is None
