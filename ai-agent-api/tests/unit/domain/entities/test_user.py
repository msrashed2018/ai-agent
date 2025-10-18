"""Unit tests for User domain entity."""

import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.entities.user import User, UserRole
from app.domain.exceptions import ValidationError


class TestUserEntity:
    """Test cases for User entity."""

    def test_user_creation(self):
        """Test user initialization."""
        user_id = uuid4()
        org_id = uuid4()

        user = User(
            id=user_id,
            organization_id=org_id,
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
        )

        assert user.id == user_id
        assert user.organization_id == org_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_default_quotas(self):
        """Test default user quotas."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.max_concurrent_sessions == 5
        assert user.max_api_calls_per_hour == 1000
        assert user.max_storage_mb == 10240

    def test_update_last_login(self):
        """Test updating last login timestamp."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        initial_updated_at = user.updated_at

        # Wait a tiny bit to ensure timestamp difference
        user.update_last_login()

        assert user.last_login_at is not None
        assert user.updated_at >= initial_updated_at

    def test_deactivate_user(self):
        """Test deactivating a user account."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.is_active is True
        user.deactivate()
        assert user.is_active is False

    def test_activate_user(self):
        """Test activating a user account."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        user.is_active = False
        user.activate()
        assert user.is_active is True

    def test_set_valid_role(self):
        """Test setting a valid user role."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        user.set_role(UserRole.ADMIN)
        assert user.role == UserRole.ADMIN

        user.set_role(UserRole.VIEWER)
        assert user.role == UserRole.VIEWER

    def test_set_invalid_role_raises_error(self):
        """Test setting an invalid role raises ValidationError."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        with pytest.raises(ValidationError) as exc_info:
            user.set_role("invalid_role")

        assert "Invalid role" in str(exc_info.value)

    def test_is_admin_when_role_is_admin(self):
        """Test is_admin method when role is admin."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        user.set_role(UserRole.ADMIN)
        assert user.is_admin() is True

    def test_is_admin_when_is_superuser(self):
        """Test is_admin method when user is superuser."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        user.is_superuser = True
        assert user.is_admin() is True

    def test_is_admin_when_regular_user(self):
        """Test is_admin method when user is regular user."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.role == UserRole.USER
        assert user.is_admin() is False

    def test_can_access_own_session(self):
        """Test user can access their own session."""
        user_id = uuid4()
        user = User(
            id=user_id,
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.can_access_session(user_id) is True

    def test_cannot_access_other_session_as_regular_user(self):
        """Test regular user cannot access other user's session."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        other_user_id = uuid4()
        assert user.can_access_session(other_user_id) is False

    def test_admin_can_access_any_session(self):
        """Test admin user can access any session."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="admin@example.com",
            username="admin",
            password_hash="hashed",
        )

        user.set_role(UserRole.ADMIN)
        other_user_id = uuid4()
        assert user.can_access_session(other_user_id) is True

    def test_update_quotas(self):
        """Test updating user quotas."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        user.update_quotas(
            max_concurrent_sessions=10,
            max_api_calls_per_hour=5000,
            max_storage_mb=20480,
        )

        assert user.max_concurrent_sessions == 10
        assert user.max_api_calls_per_hour == 5000
        assert user.max_storage_mb == 20480

    def test_update_quotas_partial(self):
        """Test updating only some quotas."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        original_storage = user.max_storage_mb
        user.update_quotas(max_concurrent_sessions=15)

        assert user.max_concurrent_sessions == 15
        assert user.max_api_calls_per_hour == 1000  # unchanged
        assert user.max_storage_mb == original_storage  # unchanged

    def test_user_profile_fields_optional(self):
        """Test that profile fields are optional."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.full_name is None
        assert user.avatar_url is None

        user.full_name = "Test User"
        user.avatar_url = "https://example.com/avatar.jpg"

        assert user.full_name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.jpg"

    def test_last_login_initially_none(self):
        """Test that last login is initially None."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.last_login_at is None

    def test_deleted_at_initially_none(self):
        """Test that deleted_at is initially None."""
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        assert user.deleted_at is None

    def test_timestamps_set_on_creation(self):
        """Test that timestamps are set on creation."""
        before_creation = datetime.utcnow()
        user = User(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        after_creation = datetime.utcnow()

        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation
        # Check timestamps are within a reasonable time delta (within 10ms)
        time_delta = (user.updated_at - user.created_at).total_seconds()
        assert 0 <= time_delta <= 0.01  # Allow up to 10ms difference
