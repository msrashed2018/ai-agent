"""User domain entity."""
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRole:
    """User role constants."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User:
    """User aggregate root."""

    def __init__(
        self,
        id: UUID,
        organization_id: UUID,
        email: str,
        username: str,
        password_hash: str,
    ):
        self.id = id
        self.organization_id = organization_id
        self.email = email
        self.username = username
        self.password_hash = password_hash

        # Profile
        self.full_name: Optional[str] = None
        self.avatar_url: Optional[str] = None

        # Authorization
        self.role = UserRole.USER
        self.is_active = True
        self.is_superuser = False

        # Quotas & Limits
        self.max_concurrent_sessions = 5
        self.max_api_calls_per_hour = 1000
        self.max_storage_mb = 10240  # 10GB

        # Audit
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.last_login_at: Optional[datetime] = None
        self.deleted_at: Optional[datetime] = None

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def set_role(self, role: str) -> None:
        """Set user role."""
        from app.domain.exceptions import ValidationError

        valid_roles = [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER]
        if role not in valid_roles:
            raise ValidationError(f"Invalid role: {role}. Must be one of {valid_roles}")

        self.role = role
        self.updated_at = datetime.utcnow()

    def update_quotas(
        self,
        max_concurrent_sessions: Optional[int] = None,
        max_api_calls_per_hour: Optional[int] = None,
        max_storage_mb: Optional[int] = None,
    ) -> None:
        """Update user quotas."""
        if max_concurrent_sessions is not None:
            self.max_concurrent_sessions = max_concurrent_sessions
        if max_api_calls_per_hour is not None:
            self.max_api_calls_per_hour = max_api_calls_per_hour
        if max_storage_mb is not None:
            self.max_storage_mb = max_storage_mb

        self.updated_at = datetime.utcnow()

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN or self.is_superuser

    def can_access_session(self, session_user_id: UUID) -> bool:
        """Check if user can access a session."""
        return self.is_admin() or self.id == session_user_id
