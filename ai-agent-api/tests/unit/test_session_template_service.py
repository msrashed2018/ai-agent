"""Unit tests for SessionTemplateService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.session_template_service import SessionTemplateService
from app.domain.entities.session_template import SessionTemplate, TemplateCategory
from app.domain.exceptions import (
    TemplateNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.session_template import SessionTemplateModel
from app.models.user import UserModel


class TestSessionTemplateService:
    """Test cases for SessionTemplateService."""

    @pytest.fixture
    def template_service(self, db_session, mock_audit_service):
        """Create SessionTemplateService with mocked dependencies."""
        from app.repositories.session_template_repository import SessionTemplateRepository
        from app.repositories.user_repository import UserRepository
        from app.repositories.mcp_server_repository import MCPServerRepository

        return SessionTemplateService(
            db=db_session,
            template_repo=SessionTemplateRepository(db_session),
            user_repo=UserRepository(db_session),
            mcp_server_repo=MCPServerRepository(db_session),
            audit_service=mock_audit_service,
        )

    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for testing."""
        return {
            "name": "Security Audit Template",
            "description": "Template for security code audits",
            "category": TemplateCategory.SECURITY,
            "system_prompt": "You are a security expert analyzing code for vulnerabilities",
            "working_directory": "/workspace/project",
            "allowed_tools": ["Read", "Grep", "Bash"],
            "sdk_options": {"model": "claude-sonnet-4-5", "max_turns": 10},
            "mcp_server_ids": None,
            "is_public": False,
            "is_organization_shared": False,
            "tags": ["security", "audit", "compliance"],
            "template_metadata": {"severity_level": "high"},
        }

    @pytest.mark.asyncio
    async def test_create_template_success(
        self,
        template_service,
        test_user,
        sample_template_data,
        mock_audit_service,
    ):
        """Test successful template creation."""
        # Act
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Assert
        assert template is not None
        assert template.user_id == test_user.id
        assert template.name == sample_template_data["name"]
        assert template.description == sample_template_data["description"]
        assert template.category == sample_template_data["category"]
        assert template.system_prompt == sample_template_data["system_prompt"]
        assert template.allowed_tools == sample_template_data["allowed_tools"]
        assert template.sdk_options == sample_template_data["sdk_options"]
        assert template.tags == sample_template_data["tags"]
        assert template.usage_count == 0
        assert template.deleted_at is None

        # Verify audit logging
        mock_audit_service.log_template_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template_user_not_found(
        self,
        template_service,
        sample_template_data,
    ):
        """Test template creation with non-existent user."""
        # Arrange
        nonexistent_user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValidationError, match="User not found"):
            await template_service.create_template(
                user_id=nonexistent_user_id,
                **sample_template_data
            )

    @pytest.mark.asyncio
    async def test_create_public_template(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test creating a public template."""
        # Arrange
        sample_template_data["is_public"] = True

        # Act
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Assert
        assert template.is_public is True
        assert template.is_organization_shared is False

    @pytest.mark.asyncio
    async def test_get_template_success(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test successfully retrieving a template."""
        # Arrange - Create template first
        created_template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Act
        retrieved_template = await template_service.get_template(
            created_template.id,
            test_user.id,
        )

        # Assert
        assert retrieved_template.id == created_template.id
        assert retrieved_template.name == created_template.name
        assert retrieved_template.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self,
        template_service,
        test_user,
    ):
        """Test retrieving non-existent template."""
        # Arrange
        nonexistent_id = uuid4()

        # Act & Assert
        with pytest.raises(TemplateNotFoundError):
            await template_service.get_template(nonexistent_id, test_user.id)

    @pytest.mark.asyncio
    async def test_update_template_success(
        self,
        template_service,
        test_user,
        sample_template_data,
        mock_audit_service,
    ):
        """Test successfully updating a template."""
        # Arrange - Create template first
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Act
        updated_name = "Updated Security Audit"
        updated_description = "Updated description"
        updated_template = await template_service.update_template(
            template_id=template.id,
            user_id=test_user.id,
            name=updated_name,
            description=updated_description,
        )

        # Assert
        assert updated_template.name == updated_name
        assert updated_template.description == updated_description
        assert updated_template.id == template.id

        # Verify audit logging
        mock_audit_service.log_template_updated.assert_called()

    @pytest.mark.asyncio
    async def test_update_template_not_owner(
        self,
        template_service,
        test_user,
        sample_template_data,
        db_session,
    ):
        """Test updating template by non-owner user."""
        # Arrange - Create template
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Create another user
        other_user = UserModel(
            id=uuid4(),
            email="other@example.com",
            username="otheruser",
            password_hash="hashed",
            role="user",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(PermissionDeniedError):
            await template_service.update_template(
                template_id=template.id,
                user_id=other_user.id,
                name="Attempted Update",
            )

    @pytest.mark.asyncio
    async def test_update_sharing_settings(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test updating template sharing settings."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )
        assert template.is_public is False

        # Act
        updated_template = await template_service.update_sharing_settings(
            template_id=template.id,
            user_id=test_user.id,
            is_public=True,
            is_organization_shared=True,
        )

        # Assert
        assert updated_template.is_public is True
        assert updated_template.is_organization_shared is True

    @pytest.mark.asyncio
    async def test_delete_template_success(
        self,
        template_service,
        test_user,
        sample_template_data,
        mock_audit_service,
    ):
        """Test soft deleting a template."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Act
        await template_service.delete_template(
            template_id=template.id,
            user_id=test_user.id,
        )

        # Assert
        with pytest.raises(TemplateNotFoundError):
            await template_service.get_template(template.id, test_user.id)

        # Verify audit logging
        mock_audit_service.log_template_deleted.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_template_not_owner(
        self,
        template_service,
        test_user,
        sample_template_data,
        db_session,
    ):
        """Test deleting template by non-owner."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )

        # Create another user
        other_user = UserModel(
            id=uuid4(),
            email="other2@example.com",
            username="otheruser2",
            password_hash="hashed",
            role="user",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(PermissionDeniedError):
            await template_service.delete_template(
                template_id=template.id,
                user_id=other_user.id,
            )

    @pytest.mark.asyncio
    async def test_increment_usage(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test incrementing template usage count."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            **sample_template_data
        )
        initial_count = template.usage_count

        # Act
        updated_template = await template_service.increment_usage(
            template_id=template.id,
            user_id=test_user.id,
        )

        # Assert
        assert updated_template.usage_count == initial_count + 1
        assert updated_template.last_used_at is not None

    @pytest.mark.asyncio
    async def test_list_user_templates(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test listing templates owned by user."""
        # Arrange - Create multiple templates
        template1 = await template_service.create_template(
            user_id=test_user.id,
            name="Template 1",
            **{k: v for k, v in sample_template_data.items() if k != "name"}
        )
        template2 = await template_service.create_template(
            user_id=test_user.id,
            name="Template 2",
            **{k: v for k, v in sample_template_data.items() if k != "name"}
        )

        # Act
        templates = await template_service.list_user_templates(
            user_id=test_user.id,
            skip=0,
            limit=10,
        )

        # Assert
        assert len(templates) >= 2
        template_ids = [t.id for t in templates]
        assert template1.id in template_ids
        assert template2.id in template_ids

    @pytest.mark.asyncio
    async def test_list_public_templates(
        self,
        template_service,
        test_user,
        sample_template_data,
        db_session,
    ):
        """Test listing public templates."""
        # Arrange - Create public and private templates
        public_template = await template_service.create_template(
            user_id=test_user.id,
            is_public=True,
            **{k: v for k, v in sample_template_data.items() if k != "is_public"}
        )
        private_template = await template_service.create_template(
            user_id=test_user.id,
            is_public=False,
            name="Private Template",
            **{k: v for k, v in sample_template_data.items() if k not in ["is_public", "name"]}
        )

        # Act
        public_templates = await template_service.list_public_templates(
            skip=0,
            limit=10,
        )

        # Assert
        public_template_ids = [t.id for t in public_templates]
        assert public_template.id in public_template_ids
        assert private_template.id not in public_template_ids

    @pytest.mark.asyncio
    async def test_search_templates_by_name(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test searching templates by name."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            name="Unique Security Template",
            **{k: v for k, v in sample_template_data.items() if k != "name"}
        )

        # Act
        results = await template_service.search_templates(
            user_id=test_user.id,
            search_term="Unique",
            skip=0,
            limit=10,
        )

        # Assert
        assert len(results) > 0
        assert any(t.id == template.id for t in results)

    @pytest.mark.asyncio
    async def test_search_templates_by_category(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test searching templates by category."""
        # Arrange
        security_template = await template_service.create_template(
            user_id=test_user.id,
            category=TemplateCategory.SECURITY,
            **{k: v for k, v in sample_template_data.items() if k != "category"}
        )
        dev_template = await template_service.create_template(
            user_id=test_user.id,
            name="Dev Template",
            category=TemplateCategory.DEVELOPMENT,
            **{k: v for k, v in sample_template_data.items() if k not in ["category", "name"]}
        )

        # Act
        security_results = await template_service.search_templates(
            user_id=test_user.id,
            category=TemplateCategory.SECURITY,
            skip=0,
            limit=10,
        )

        # Assert
        assert len(security_results) > 0
        assert any(t.id == security_template.id for t in security_results)
        assert all(t.category == TemplateCategory.SECURITY for t in security_results if t.category)

    @pytest.mark.asyncio
    async def test_search_templates_by_tags(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test searching templates by tags."""
        # Arrange
        template = await template_service.create_template(
            user_id=test_user.id,
            tags=["security", "compliance", "pci-dss"],
            **{k: v for k, v in sample_template_data.items() if k != "tags"}
        )

        # Act
        results = await template_service.search_templates(
            user_id=test_user.id,
            tags=["compliance"],
            skip=0,
            limit=10,
        )

        # Assert
        assert len(results) > 0
        assert any(t.id == template.id for t in results)

    @pytest.mark.asyncio
    async def test_get_most_used_templates(
        self,
        template_service,
        test_user,
        sample_template_data,
    ):
        """Test getting most frequently used templates."""
        # Arrange - Create templates and increment usage
        template1 = await template_service.create_template(
            user_id=test_user.id,
            name="Popular Template",
            **{k: v for k, v in sample_template_data.items() if k != "name"}
        )
        # Increment usage multiple times
        for _ in range(5):
            await template_service.increment_usage(template1.id, test_user.id)

        template2 = await template_service.create_template(
            user_id=test_user.id,
            name="Less Popular",
            **{k: v for k, v in sample_template_data.items() if k != "name"}
        )
        await template_service.increment_usage(template2.id, test_user.id)

        # Act
        most_used = await template_service.get_most_used_templates(
            user_id=test_user.id,
            limit=10,
        )

        # Assert
        assert len(most_used) >= 2
        # Most used should be first
        assert most_used[0].usage_count >= most_used[1].usage_count
