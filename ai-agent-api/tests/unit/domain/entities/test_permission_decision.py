"""Unit tests for PermissionDecision domain entity."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.entities.permission_decision import PermissionDecision, PermissionResult


class TestPermissionDecisionEntity:
    """Test cases for PermissionDecision entity."""

    def test_permission_decision_creation_allowed(self):
        """Test permission decision initialization with ALLOWED result."""
        decision_id = uuid4()
        session_id = uuid4()
        tool_call_id = uuid4()
        created_at = datetime.utcnow()
        
        input_data = {"file_path": "/tmp/test.txt", "operation": "read"}
        context_data = {"user_id": str(uuid4()), "permission_level": "admin"}

        permission_decision = PermissionDecision(
            id=decision_id,
            session_id=session_id,
            tool_call_id=tool_call_id,
            tool_use_id="tool_456",
            tool_name="file_reader",
            input_data=input_data,
            context_data=context_data,
            decision=PermissionResult.ALLOWED,
            reason="User has admin privileges",
            policy_applied="admin_policy",
            created_at=created_at,
        )

        assert permission_decision.id == decision_id
        assert permission_decision.session_id == session_id
        assert permission_decision.tool_call_id == tool_call_id
        assert permission_decision.tool_use_id == "tool_456"
        assert permission_decision.tool_name == "file_reader"
        assert permission_decision.input_data == input_data
        assert permission_decision.context_data == context_data
        assert permission_decision.decision == PermissionResult.ALLOWED
        assert permission_decision.reason == "User has admin privileges"
        assert permission_decision.policy_applied == "admin_policy"
        assert permission_decision.created_at == created_at

    def test_permission_decision_creation_denied(self):
        """Test permission decision initialization with DENIED result."""
        permission_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=uuid4(),
            tool_use_id="tool_789",
            tool_name="file_writer",
            input_data={"file_path": "/etc/passwd"},
            context_data={"user_id": "guest"},
            decision=PermissionResult.DENIED,
            reason="Security violation: attempt to write to system file",
            policy_applied="security_policy",
            created_at=datetime.utcnow(),
        )

        assert permission_decision.decision == PermissionResult.DENIED
        assert "Security violation" in permission_decision.reason

    def test_permission_decision_creation_bypassed(self):
        """Test permission decision initialization with BYPASSED result."""
        permission_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,  # Can be None
            tool_use_id="tool_999",
            tool_name="system_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.BYPASSED,
            reason="System tool bypassed permission check",
            policy_applied=None,  # Can be None
            created_at=datetime.utcnow(),
        )

        assert permission_decision.decision == PermissionResult.BYPASSED
        assert permission_decision.tool_call_id is None
        assert permission_decision.policy_applied is None

    def test_permission_decision_validation_empty_tool_use_id(self):
        """Test validation fails for empty tool use ID."""
        with pytest.raises(ValueError, match="Tool use ID cannot be empty"):
            PermissionDecision(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                tool_use_id="   ",
                tool_name="test_tool",
                input_data={},
                context_data={},
                decision=PermissionResult.ALLOWED,
                reason="Test reason",
                policy_applied=None,
                created_at=datetime.utcnow(),
            )

    def test_permission_decision_validation_empty_tool_name(self):
        """Test validation fails for empty tool name."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            PermissionDecision(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                tool_use_id="tool_123",
                tool_name="",
                input_data={},
                context_data={},
                decision=PermissionResult.ALLOWED,
                reason="Test reason",
                policy_applied=None,
                created_at=datetime.utcnow(),
            )

    def test_permission_decision_validation_empty_reason(self):
        """Test validation fails for empty reason."""
        with pytest.raises(ValueError, match="Reason cannot be empty"):
            PermissionDecision(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                tool_use_id="tool_123",
                tool_name="test_tool",
                input_data={},
                context_data={},
                decision=PermissionResult.ALLOWED,
                reason="   ",
                policy_applied=None,
                created_at=datetime.utcnow(),
            )

    def test_permission_decision_validation_empty_policy_applied(self):
        """Test validation fails for empty string in policy_applied."""
        with pytest.raises(ValueError, match="Policy applied cannot be empty string"):
            PermissionDecision(
                id=uuid4(),
                session_id=uuid4(),
                tool_call_id=None,
                tool_use_id="tool_123",
                tool_name="test_tool",
                input_data={},
                context_data={},
                decision=PermissionResult.ALLOWED,
                reason="Test reason",
                policy_applied="   ",  # Empty string should fail
                created_at=datetime.utcnow(),
            )

    def test_is_allowed_method(self):
        """Test is_allowed method."""
        allowed_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Permission granted",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        denied_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.DENIED,
            reason="Permission denied",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert allowed_decision.is_allowed() is True
        assert allowed_decision.is_denied() is False
        assert allowed_decision.is_bypassed() is False

        assert denied_decision.is_allowed() is False
        assert denied_decision.is_denied() is True
        assert denied_decision.is_bypassed() is False

    def test_is_bypassed_method(self):
        """Test is_bypassed method."""
        bypassed_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_789",
            tool_name="system_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.BYPASSED,
            reason="System bypass",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert bypassed_decision.is_bypassed() is True
        assert bypassed_decision.is_allowed() is False
        assert bypassed_decision.is_denied() is False

    def test_requires_user_approval(self):
        """Test requires_user_approval method."""
        user_approval_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="dangerous_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Allowed after user manual approval",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        automatic_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="safe_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Automatic approval by policy",
            policy_applied="default_policy",
            created_at=datetime.utcnow(),
        )

        assert user_approval_decision.requires_user_approval() is True
        assert automatic_decision.requires_user_approval() is False

    def test_is_automated_decision(self):
        """Test is_automated_decision method."""
        automated_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Automatic approval by default policy rule",
            policy_applied="default_policy",
            created_at=datetime.utcnow(),
        )

        manual_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.DENIED,
            reason="Denied after admin review",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert automated_decision.is_automated_decision() is True
        assert manual_decision.is_automated_decision() is False

    def test_has_policy(self):
        """Test has_policy method."""
        with_policy = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Applied security policy",
            policy_applied="security_policy",
            created_at=datetime.utcnow(),
        )

        without_policy = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.DENIED,
            reason="Manual decision",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert with_policy.has_policy() is True
        assert without_policy.has_policy() is False

    def test_is_security_related(self):
        """Test is_security_related method."""
        security_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="file_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.DENIED,
            reason="Blocked due to security violation - unsafe file access",
            policy_applied="security_policy",
            created_at=datetime.utcnow(),
        )

        regular_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="calc_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Standard calculation allowed",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert security_decision.is_security_related() is True
        assert regular_decision.is_security_related() is False

    def test_has_input_data(self):
        """Test has_input_data method."""
        with_input = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={"param": "value"},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Test reason",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        without_input = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Test reason",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert with_input.has_input_data() is True
        assert without_input.has_input_data() is False

    def test_has_context_data(self):
        """Test has_context_data method."""
        with_context = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            context_data={"user": "admin"},
            decision=PermissionResult.ALLOWED,
            reason="Test reason",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        without_context = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_456",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Test reason",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        assert with_context.has_context_data() is True
        assert without_context.has_context_data() is False

    def test_permission_decision_immutability(self):
        """Test that PermissionDecision is immutable (frozen dataclass)."""
        decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=None,
            tool_use_id="tool_123",
            tool_name="test_tool",
            input_data={},
            context_data={},
            decision=PermissionResult.ALLOWED,
            reason="Test reason",
            policy_applied=None,
            created_at=datetime.utcnow(),
        )

        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            decision.decision = PermissionResult.DENIED

        with pytest.raises(AttributeError):
            decision.reason = "Modified reason"

    def test_permission_result_enum_values(self):
        """Test PermissionResult enum values."""
        assert PermissionResult.ALLOWED == "allowed"
        assert PermissionResult.DENIED == "denied"
        assert PermissionResult.BYPASSED == "bypassed"

    def test_complex_permission_scenario(self):
        """Test complex permission decision scenario."""
        complex_decision = PermissionDecision(
            id=uuid4(),
            session_id=uuid4(),
            tool_call_id=uuid4(),
            tool_use_id="dangerous_tool_001",
            tool_name="system_file_modifier",
            input_data={
                "file_path": "/system/config/app.conf",
                "operation": "write",
                "content": "modified_config"
            },
            context_data={
                "user_id": "admin_user",
                "user_role": "system_admin",
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": "192.168.1.100"
            },
            decision=PermissionResult.DENIED,
            reason="Security policy violation: restricted file access outside business hours",
            policy_applied="time_based_security_policy",
            created_at=datetime.utcnow(),
        )

        # Validate complex scenario
        assert complex_decision.is_denied() is True
        assert complex_decision.is_security_related() is True
        assert complex_decision.has_policy() is True
        assert complex_decision.is_automated_decision() is True
        assert complex_decision.has_input_data() is True
        assert complex_decision.has_context_data() is True
        assert complex_decision.requires_user_approval() is False  # Automated policy decision