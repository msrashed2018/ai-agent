"""Unit tests for Session domain entity."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.entities.session import Session, SessionMode, SessionStatus
from app.domain.exceptions import InvalidStateTransitionError


class TestSessionEntity:
    """Test cases for Session entity."""

    def test_session_creation(self):
        """Test session initialization."""
        session_id = uuid4()
        user_id = uuid4()
        sdk_options = {"model": "claude-sonnet-4-5", "max_turns": 10}

        session = Session(
            id=session_id,
            user_id=user_id,
            mode=SessionMode.INTERACTIVE,
            sdk_options=sdk_options,
        )

        assert session.id == session_id
        assert session.user_id == user_id
        assert session.mode == SessionMode.INTERACTIVE
        assert session.status == SessionStatus.CREATED
        assert session.sdk_options == sdk_options
        assert session.name is None
        assert session.working_directory_path is None
        assert session.parent_session_id is None
        assert session.is_fork is False

    def test_session_creation_with_name(self):
        """Test session creation with name."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
            name="Test Session",
        )

        assert session.name == "Test Session"

    def test_session_metrics_initialized(self):
        """Test session metrics initialization."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.total_messages == 0
        assert session.total_tool_calls == 0
        assert session.total_cost_usd == 0.0
        assert session.duration_ms is None
        assert session.api_input_tokens == 0
        assert session.api_output_tokens == 0
        assert session.api_cache_creation_tokens == 0
        assert session.api_cache_read_tokens == 0

    def test_valid_status_transition(self):
        """Test valid status transition."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.status == SessionStatus.CREATED
        assert session.can_transition_to(SessionStatus.CONNECTING) is True

        session.transition_to(SessionStatus.CONNECTING)
        assert session.status == SessionStatus.CONNECTING

    def test_invalid_status_transition_raises_error(self):
        """Test invalid status transition raises error."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # Try to transition from CREATED to COMPLETED (invalid)
        with pytest.raises(InvalidStateTransitionError):
            session.transition_to(SessionStatus.COMPLETED)

    def test_can_transition_to_method(self):
        """Test can_transition_to method for valid transitions."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # From CREATED
        assert session.can_transition_to(SessionStatus.CONNECTING) is True
        assert session.can_transition_to(SessionStatus.TERMINATED) is True
        assert session.can_transition_to(SessionStatus.ACTIVE) is False

        # Transition to CONNECTING
        session.status = SessionStatus.CONNECTING
        assert session.can_transition_to(SessionStatus.ACTIVE) is True
        assert session.can_transition_to(SessionStatus.FAILED) is True
        assert session.can_transition_to(SessionStatus.CREATED) is False

    def test_status_transition_updates_timestamps(self):
        """Test status transition updates timestamps."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        original_updated_at = session.updated_at
        session.transition_to(SessionStatus.CONNECTING)
        assert session.updated_at >= original_updated_at

    def test_active_status_sets_started_at(self):
        """Test transitioning to ACTIVE sets started_at."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.started_at is None

        session.transition_to(SessionStatus.CONNECTING)
        session.transition_to(SessionStatus.ACTIVE)

        assert session.started_at is not None

    def test_terminal_status_sets_completed_at_and_duration(self):
        """Test transitioning to terminal status sets completed_at and duration."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # Move to ACTIVE state
        session.transition_to(SessionStatus.CONNECTING)
        session.transition_to(SessionStatus.ACTIVE)

        started_at = session.started_at

        # Transition to terminal state
        session.transition_to(SessionStatus.COMPLETED)

        assert session.completed_at is not None
        assert session.duration_ms is not None
        assert session.duration_ms >= 0

    def test_increment_message_count(self):
        """Test incrementing message count."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.total_messages == 0

        session.increment_message_count()
        assert session.total_messages == 1

        session.increment_message_count()
        assert session.total_messages == 2

    def test_increment_tool_call_count(self):
        """Test incrementing tool call count."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.total_tool_calls == 0

        session.increment_tool_call_count()
        assert session.total_tool_calls == 1

        session.increment_tool_call_count()
        assert session.total_tool_calls == 2

    def test_add_cost(self):
        """Test adding cost."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.total_cost_usd == 0.0

        session.add_cost(0.50)
        assert session.total_cost_usd == 0.50

        session.add_cost(0.30)
        assert session.total_cost_usd == 0.80

    def test_update_api_tokens(self):
        """Test updating API token usage."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        session.update_api_tokens(
            input_tokens=100,
            output_tokens=50,
            cache_creation_tokens=10,
            cache_read_tokens=5,
        )

        assert session.api_input_tokens == 100
        assert session.api_output_tokens == 50
        assert session.api_cache_creation_tokens == 10
        assert session.api_cache_read_tokens == 5

    def test_update_api_tokens_accumulates(self):
        """Test API token updates accumulate."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        session.update_api_tokens(input_tokens=100, output_tokens=50)
        session.update_api_tokens(input_tokens=200, output_tokens=100)

        assert session.api_input_tokens == 300
        assert session.api_output_tokens == 150

    def test_is_active(self):
        """Test is_active method."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.is_active() is False

        session.status = SessionStatus.ACTIVE
        assert session.is_active() is True

        session.status = SessionStatus.WAITING
        assert session.is_active() is True

        session.status = SessionStatus.PROCESSING
        assert session.is_active() is True

        session.status = SessionStatus.COMPLETED
        assert session.is_active() is False

    def test_is_terminal(self):
        """Test is_terminal method."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.is_terminal() is False

        session.status = SessionStatus.COMPLETED
        assert session.is_terminal() is True

        session.status = SessionStatus.FAILED
        assert session.is_terminal() is True

        session.status = SessionStatus.TERMINATED
        assert session.is_terminal() is True

        session.status = SessionStatus.ARCHIVED
        assert session.is_terminal() is True

        session.status = SessionStatus.ACTIVE
        assert session.is_terminal() is False

    def test_set_result(self):
        """Test setting result data."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        result_data = {"output": "test result"}
        session.set_result(result_data)

        assert session.result_data == result_data

    def test_set_error(self):
        """Test setting error message."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        error_message = "Something went wrong"
        session.set_error(error_message)

        assert session.error_message == error_message

    def test_result_and_error_initially_none(self):
        """Test result and error are initially None."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        assert session.result_data is None
        assert session.error_message is None

    def test_archived_status_has_no_valid_transitions(self):
        """Test ARCHIVED status has no valid transitions."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        session.status = SessionStatus.ARCHIVED

        assert session.can_transition_to(SessionStatus.ACTIVE) is False
        assert session.can_transition_to(SessionStatus.CREATED) is False
        assert session.can_transition_to(SessionStatus.ARCHIVED) is False

    def test_fork_session_properties(self):
        """Test fork session properties."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        parent_id = uuid4()
        session.parent_session_id = parent_id
        session.is_fork = True

        assert session.parent_session_id == parent_id
        assert session.is_fork is True

    def test_session_non_interactive_mode(self):
        """Test session with non-interactive mode."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.NON_INTERACTIVE,
            sdk_options={},
        )

        assert session.mode == SessionMode.NON_INTERACTIVE

    def test_complete_status_workflow(self):
        """Test complete workflow from created to archived."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # CREATED -> CONNECTING -> ACTIVE
        session.transition_to(SessionStatus.CONNECTING)
        session.transition_to(SessionStatus.ACTIVE)
        assert session.started_at is not None

        # Process some work
        session.increment_message_count()
        session.increment_tool_call_count()
        session.add_cost(0.50)

        # ACTIVE -> COMPLETED
        session.transition_to(SessionStatus.COMPLETED)
        assert session.completed_at is not None
        assert session.duration_ms is not None

        # COMPLETED -> ARCHIVED
        session.transition_to(SessionStatus.ARCHIVED)
        assert session.status == SessionStatus.ARCHIVED

    def test_working_directory_path_assignment(self):
        """Test assigning working directory path."""
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        workdir_path = "/tmp/session-workdir"
        session.working_directory_path = workdir_path

        assert session.working_directory_path == workdir_path
