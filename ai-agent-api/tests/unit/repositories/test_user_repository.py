"""Unit tests for UserRepository."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from app.repositories.user_repository import UserRepository
from app.models.user import UserModel, OrganizationModel


class TestUserRepository:
    """Test cases for UserRepository."""

    @pytest_asyncio.fixture
    async def user_repository(self, db_session):
        """Create UserRepository instance."""
        return UserRepository(db_session)

    @pytest_asyncio.fixture
    async def second_organization(self, db_session):
        """Create a second test organization."""
        org = OrganizationModel(
            id=uuid4(),
            name="Second Organization",
            slug="second-org",
            plan="enterprise",
            max_users=50,
            max_sessions_per_month=5000,
            max_storage_gb=500,
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        return org

    # Test: create (inherited from BaseRepository)
    @pytest.mark.asyncio
    async def test_create_user(self, user_repository, test_organization):
        """Test creating a new user."""
        # Arrange
        user_data = {
            "organization_id": test_organization.id,
            "email": "new@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password_hash": "$2b$12$hashed",
            "role": "user",
        }

        # Act
        user = await user_repository.create(**user_data)

        # Assert
        assert user is not None
        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.username == "newuser"
        assert user.full_name == "New User"
        assert user.role == "user"
        assert user.is_active is True
        assert user.deleted_at is None

    # Test: get_by_id
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, test_user):
        """Test getting user by ID successfully."""
        # Act
        user = await user_repository.get_by_id(test_user.id)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.username == test_user.username

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository):
        """Test getting user by non-existent ID."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        user = await user_repository.get_by_id(non_existent_id)

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self, user_repository, test_user, db_session):
        """Test that get_by_id excludes soft-deleted users."""
        # Arrange - Soft delete the user
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        user = await user_repository.get_by_id(test_user.id)

        # Assert
        assert user is None

    # Test: get_by_email
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repository, test_user):
        """Test getting user by email successfully."""
        # Act
        user = await user_repository.get_by_email(test_user.email)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """Test getting user by non-existent email."""
        # Act
        user = await user_repository.get_by_email("nonexistent@example.com")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email_case_sensitive(self, user_repository, test_user):
        """Test that email lookup is case-sensitive."""
        # Act
        user = await user_repository.get_by_email(test_user.email.upper())

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_email_excludes_soft_deleted(self, user_repository, test_user, db_session):
        """Test that get_by_email excludes soft-deleted users."""
        # Arrange
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        user = await user_repository.get_by_email(test_user.email)

        # Assert
        assert user is None

    # Test: get_by_username
    @pytest.mark.asyncio
    async def test_get_by_username_success(self, user_repository, test_user):
        """Test getting user by username successfully."""
        # Act
        user = await user_repository.get_by_username(test_user.username)

        # Assert
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, user_repository):
        """Test getting user by non-existent username."""
        # Act
        user = await user_repository.get_by_username("nonexistent")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_by_username_excludes_soft_deleted(self, user_repository, test_user, db_session):
        """Test that get_by_username excludes soft-deleted users."""
        # Arrange
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        user = await user_repository.get_by_username(test_user.username)

        # Assert
        assert user is None

    # Test: get_by_organization
    @pytest.mark.asyncio
    async def test_get_by_organization_success(
        self, user_repository, test_user, test_organization, db_session
    ):
        """Test getting users by organization."""
        # Arrange - Create additional users
        for i in range(3):
            user = UserModel(
                organization_id=test_organization.id,
                email=f"user{i}@example.com",
                username=f"user{i}",
                password_hash="$2b$12$hashed",
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # Act
        users = await user_repository.get_by_organization(test_organization.id)

        # Assert
        assert len(users) == 4  # test_user + 3 new users
        assert all(u.organization_id == test_organization.id for u in users)
        assert all(u.deleted_at is None for u in users)

    @pytest.mark.asyncio
    async def test_get_by_organization_pagination(
        self, user_repository, test_organization, db_session
    ):
        """Test pagination in get_by_organization."""
        # Arrange - Create 10 users
        for i in range(10):
            user = UserModel(
                organization_id=test_organization.id,
                email=f"page{i}@example.com",
                username=f"pageuser{i}",
                password_hash="$2b$12$hashed",
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # Act
        first_page = await user_repository.get_by_organization(
            test_organization.id, skip=0, limit=5
        )
        second_page = await user_repository.get_by_organization(
            test_organization.id, skip=5, limit=5
        )

        # Assert
        assert len(first_page) == 5
        assert len(second_page) == 5
        # Verify no overlap
        first_ids = {u.id for u in first_page}
        second_ids = {u.id for u in second_page}
        assert len(first_ids.intersection(second_ids)) == 0

    @pytest.mark.asyncio
    async def test_get_by_organization_empty(self, user_repository):
        """Test getting users from organization with no users."""
        # Arrange
        empty_org_id = uuid4()

        # Act
        users = await user_repository.get_by_organization(empty_org_id)

        # Assert
        assert len(users) == 0

    @pytest.mark.asyncio
    async def test_get_by_organization_excludes_soft_deleted(
        self, user_repository, test_user, test_organization, db_session
    ):
        """Test that get_by_organization excludes soft-deleted users."""
        # Arrange - Create active user and soft-delete test_user
        active_user = UserModel(
            organization_id=test_organization.id,
            email="active@example.com",
            username="active",
            password_hash="$2b$12$hashed",
            role="user",
        )
        db_session.add(active_user)
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        users = await user_repository.get_by_organization(test_organization.id)

        # Assert
        assert len(users) == 1
        assert users[0].id == active_user.id

    # Test: get_active_users
    @pytest.mark.asyncio
    async def test_get_active_users(self, user_repository, test_user, db_session):
        """Test getting active users."""
        # Arrange - Create mix of active and inactive users
        inactive_user = UserModel(
            organization_id=test_user.organization_id,
            email="inactive@example.com",
            username="inactive",
            password_hash="$2b$12$hashed",
            role="user",
            is_active=False,
        )
        db_session.add(inactive_user)
        await db_session.commit()

        # Act
        users = await user_repository.get_active_users()

        # Assert
        assert len(users) >= 1
        assert all(u.is_active is True for u in users)
        assert test_user.id in [u.id for u in users]
        assert inactive_user.id not in [u.id for u in users]

    @pytest.mark.asyncio
    async def test_get_active_users_pagination(self, user_repository, test_organization, db_session):
        """Test pagination in get_active_users."""
        # Arrange - Create 10 active users
        for i in range(10):
            user = UserModel(
                organization_id=test_organization.id,
                email=f"active{i}@example.com",
                username=f"activeuser{i}",
                password_hash="$2b$12$hashed",
                role="user",
                is_active=True,
            )
            db_session.add(user)
        await db_session.commit()

        # Act
        first_page = await user_repository.get_active_users(skip=0, limit=5)
        second_page = await user_repository.get_active_users(skip=5, limit=5)

        # Assert
        assert len(first_page) == 5
        assert len(second_page) >= 5

    @pytest.mark.asyncio
    async def test_get_active_users_ordering(self, user_repository, test_organization, db_session):
        """Test that get_active_users returns users ordered by created_at desc."""
        # Arrange - Create users with different timestamps
        older_user = UserModel(
            organization_id=test_organization.id,
            email="older@example.com",
            username="older",
            password_hash="$2b$12$hashed",
            role="user",
            is_active=True,
        )
        db_session.add(older_user)
        await db_session.commit()

        # Add newer user
        newer_user = UserModel(
            organization_id=test_organization.id,
            email="newer@example.com",
            username="newer",
            password_hash="$2b$12$hashed",
            role="user",
            is_active=True,
        )
        db_session.add(newer_user)
        await db_session.commit()

        # Act
        users = await user_repository.get_active_users()

        # Assert
        assert len(users) >= 2
        # First user should be newer (desc order)
        user_ids = [u.id for u in users]
        newer_idx = user_ids.index(newer_user.id)
        older_idx = user_ids.index(older_user.id)
        assert newer_idx < older_idx

    # Test: get_by_role
    @pytest.mark.asyncio
    async def test_get_by_role_user(self, user_repository, test_user, admin_user):
        """Test getting users by role."""
        # Act
        users = await user_repository.get_by_role("user")

        # Assert
        assert len(users) >= 1
        assert all(u.role == "user" for u in users)
        assert test_user.id in [u.id for u in users]
        assert admin_user.id not in [u.id for u in users]

    @pytest.mark.asyncio
    async def test_get_by_role_admin(self, user_repository, test_user, admin_user):
        """Test getting admin users."""
        # Act
        users = await user_repository.get_by_role("admin")

        # Assert
        assert len(users) >= 1
        assert all(u.role == "admin" for u in users)
        assert admin_user.id in [u.id for u in users]
        assert test_user.id not in [u.id for u in users]

    @pytest.mark.asyncio
    async def test_get_by_role_empty(self, user_repository):
        """Test getting users by role with no matches."""
        # Act
        users = await user_repository.get_by_role("viewer")

        # Assert
        # Might be 0 or might have viewers if created elsewhere
        assert isinstance(users, list)
        assert all(u.role == "viewer" for u in users)

    @pytest.mark.asyncio
    async def test_get_by_role_pagination(self, user_repository, test_organization, db_session):
        """Test pagination in get_by_role."""
        # Arrange - Create 10 users with same role
        for i in range(10):
            user = UserModel(
                organization_id=test_organization.id,
                email=f"viewer{i}@example.com",
                username=f"viewer{i}",
                password_hash="$2b$12$hashed",
                role="viewer",
            )
            db_session.add(user)
        await db_session.commit()

        # Act
        first_page = await user_repository.get_by_role("viewer", skip=0, limit=5)
        second_page = await user_repository.get_by_role("viewer", skip=5, limit=5)

        # Assert
        assert len(first_page) == 5
        assert len(second_page) == 5

    # Test: update_last_login
    @pytest.mark.asyncio
    async def test_update_last_login_success(self, user_repository, test_user, db_session):
        """Test updating last login timestamp."""
        # Arrange
        assert test_user.last_login_at is None

        # Act
        result = await user_repository.update_last_login(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.last_login_at is not None
        assert isinstance(test_user.last_login_at, datetime)

    @pytest.mark.asyncio
    async def test_update_last_login_nonexistent(self, user_repository):
        """Test updating last login for non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.update_last_login(non_existent_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_last_login_updates_timestamp(
        self, user_repository, test_user, db_session
    ):
        """Test that multiple last login updates change the timestamp."""
        # Arrange
        first_result = await user_repository.update_last_login(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)
        first_login = test_user.last_login_at

        # Act - Update again
        import asyncio
        await asyncio.sleep(0.01)  # Ensure time difference
        second_result = await user_repository.update_last_login(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)
        second_login = test_user.last_login_at

        # Assert
        assert first_result is True
        assert second_result is True
        assert first_login is not None
        assert second_login is not None
        assert second_login >= first_login

    # Test: update_password
    @pytest.mark.asyncio
    async def test_update_password_success(self, user_repository, test_user, db_session):
        """Test updating user password."""
        # Arrange
        old_hash = test_user.password_hash
        new_hash = "$2b$12$new_hashed_password"

        # Act
        result = await user_repository.update_password(test_user.id, new_hash)
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.password_hash == new_hash
        assert test_user.password_hash != old_hash

    @pytest.mark.asyncio
    async def test_update_password_nonexistent(self, user_repository):
        """Test updating password for non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.update_password(non_existent_id, "$2b$12$new_hash")

        # Assert
        assert result is False

    # Test: activate
    @pytest.mark.asyncio
    async def test_activate_user(self, user_repository, test_user, db_session):
        """Test activating a user account."""
        # Arrange
        test_user.is_active = False
        await db_session.commit()

        # Act
        result = await user_repository.activate(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.is_active is True

    @pytest.mark.asyncio
    async def test_activate_already_active(self, user_repository, test_user, db_session):
        """Test activating an already active user."""
        # Arrange
        assert test_user.is_active is True

        # Act
        result = await user_repository.activate(test_user.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_activate_nonexistent(self, user_repository):
        """Test activating non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.activate(non_existent_id)

        # Assert
        assert result is False

    # Test: deactivate
    @pytest.mark.asyncio
    async def test_deactivate_user(self, user_repository, test_user, db_session):
        """Test deactivating a user account."""
        # Arrange
        assert test_user.is_active is True

        # Act
        result = await user_repository.deactivate(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_already_inactive(self, user_repository, test_user, db_session):
        """Test deactivating an already inactive user."""
        # Arrange
        test_user.is_active = False
        await db_session.commit()

        # Act
        result = await user_repository.deactivate(test_user.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent(self, user_repository):
        """Test deactivating non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.deactivate(non_existent_id)

        # Assert
        assert result is False

    # Test: soft_delete
    @pytest.mark.asyncio
    async def test_soft_delete_user(self, user_repository, test_user, db_session):
        """Test soft deleting a user."""
        # Arrange
        assert test_user.deleted_at is None
        assert test_user.is_active is True

        # Act
        result = await user_repository.soft_delete(test_user.id)
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.deleted_at is not None
        assert test_user.is_active is False

    @pytest.mark.asyncio
    async def test_soft_delete_already_deleted(self, user_repository, test_user, db_session):
        """Test soft deleting an already deleted user."""
        # Arrange
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        result = await user_repository.soft_delete(test_user.id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_soft_delete_nonexistent(self, user_repository):
        """Test soft deleting non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.soft_delete(non_existent_id)

        # Assert
        assert result is False

    # Test: update_quotas
    @pytest.mark.asyncio
    async def test_update_quotas_all(self, user_repository, test_user, db_session):
        """Test updating all quotas."""
        # Arrange
        old_sessions = test_user.max_concurrent_sessions
        old_api_calls = test_user.max_api_calls_per_hour
        old_storage = test_user.max_storage_mb

        # Act
        result = await user_repository.update_quotas(
            test_user.id,
            max_concurrent_sessions=10,
            max_api_calls_per_hour=2000,
            max_storage_mb=20480,
        )
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.max_concurrent_sessions == 10
        assert test_user.max_api_calls_per_hour == 2000
        assert test_user.max_storage_mb == 20480

    @pytest.mark.asyncio
    async def test_update_quotas_partial(self, user_repository, test_user, db_session):
        """Test updating only some quotas."""
        # Arrange
        old_sessions = test_user.max_concurrent_sessions
        old_api_calls = test_user.max_api_calls_per_hour
        old_storage = test_user.max_storage_mb

        # Act
        result = await user_repository.update_quotas(
            test_user.id,
            max_concurrent_sessions=15,
        )
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.max_concurrent_sessions == 15
        assert test_user.max_api_calls_per_hour == old_api_calls
        assert test_user.max_storage_mb == old_storage

    @pytest.mark.asyncio
    async def test_update_quotas_none_values(self, user_repository, test_user, db_session):
        """Test that None values don't update quotas."""
        # Arrange
        old_sessions = test_user.max_concurrent_sessions

        # Act
        result = await user_repository.update_quotas(
            test_user.id,
            max_concurrent_sessions=None,
            max_api_calls_per_hour=None,
            max_storage_mb=None,
        )
        await db_session.commit()
        await db_session.refresh(test_user)

        # Assert
        assert result is True
        assert test_user.max_concurrent_sessions == old_sessions

    @pytest.mark.asyncio
    async def test_update_quotas_nonexistent(self, user_repository):
        """Test updating quotas for non-existent user."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        result = await user_repository.update_quotas(
            non_existent_id,
            max_concurrent_sessions=10,
        )

        # Assert
        assert result is False

    # Test: count_by_organization
    @pytest.mark.asyncio
    async def test_count_by_organization(
        self, user_repository, test_user, test_organization, db_session
    ):
        """Test counting users in an organization."""
        # Arrange - Create additional users
        for i in range(3):
            user = UserModel(
                organization_id=test_organization.id,
                email=f"count{i}@example.com",
                username=f"countuser{i}",
                password_hash="$2b$12$hashed",
                role="user",
            )
            db_session.add(user)
        await db_session.commit()

        # Act
        count = await user_repository.count_by_organization(test_organization.id)

        # Assert
        assert count == 4  # test_user + 3 new users

    @pytest.mark.asyncio
    async def test_count_by_organization_empty(self, user_repository):
        """Test counting users in empty organization."""
        # Arrange
        empty_org_id = uuid4()

        # Act
        count = await user_repository.count_by_organization(empty_org_id)

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_by_organization_excludes_soft_deleted(
        self, user_repository, test_user, test_organization, db_session
    ):
        """Test that count excludes soft-deleted users."""
        # Arrange - Create active user and soft-delete test_user
        active_user = UserModel(
            organization_id=test_organization.id,
            email="countactive@example.com",
            username="countactive",
            password_hash="$2b$12$hashed",
            role="user",
        )
        db_session.add(active_user)
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        count = await user_repository.count_by_organization(test_organization.id)

        # Assert
        assert count == 1

    # Test: email_exists
    @pytest.mark.asyncio
    async def test_email_exists_true(self, user_repository, test_user):
        """Test email_exists returns True for existing email."""
        # Act
        exists = await user_repository.email_exists(test_user.email)

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    async def test_email_exists_false(self, user_repository):
        """Test email_exists returns False for non-existent email."""
        # Act
        exists = await user_repository.email_exists("nonexistent@example.com")

        # Assert
        assert exists is False

    @pytest.mark.asyncio
    async def test_email_exists_soft_deleted(self, user_repository, test_user, db_session):
        """Test email_exists excludes soft-deleted users."""
        # Arrange
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        exists = await user_repository.email_exists(test_user.email)

        # Assert
        assert exists is False

    # Test: username_exists
    @pytest.mark.asyncio
    async def test_username_exists_true(self, user_repository, test_user):
        """Test username_exists returns True for existing username."""
        # Act
        exists = await user_repository.username_exists(test_user.username)

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    async def test_username_exists_false(self, user_repository):
        """Test username_exists returns False for non-existent username."""
        # Act
        exists = await user_repository.username_exists("nonexistent")

        # Assert
        assert exists is False

    @pytest.mark.asyncio
    async def test_username_exists_soft_deleted(self, user_repository, test_user, db_session):
        """Test username_exists excludes soft-deleted users."""
        # Arrange
        test_user.deleted_at = datetime.utcnow()
        await db_session.commit()

        # Act
        exists = await user_repository.username_exists(test_user.username)

        # Assert
        assert exists is False
