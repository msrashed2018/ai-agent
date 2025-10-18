"""Integration tests for Session Templates API."""

import pytest
import json
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.models.session_template import SessionTemplateModel
from app.models.user import UserModel, OrganizationModel


class TestSessionTemplatesAPIIntegration:
    """Integration tests for session templates API endpoints."""

    @pytest.fixture
    def sample_template_request(self):
        """Sample template creation request."""
        return {
            "name": "Security Audit Template",
            "description": "Template for security code audits",
            "category": "security",
            "system_prompt": "You are a security expert analyzing code",
            "working_directory": "/workspace/project",
            "allowed_tools": ["Read", "Grep", "Bash"],
            "sdk_options": {"model": "claude-sonnet-4-5", "max_turns": 10},
            "is_public": False,
            "is_organization_shared": False,
            "tags": ["security", "audit"],
            "template_metadata": {"severity": "high"},
        }

    @pytest.mark.asyncio
    async def test_create_template_success(
        self,
        async_client,
        test_user,
        auth_headers,
        sample_template_request,
    ):
        """Test successful template creation via API."""
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.post(
                "/api/v1/session-templates",
                json=sample_template_request,
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 201

            data = response.json()
            assert data["name"] == sample_template_request["name"]
            assert data["description"] == sample_template_request["description"]
            assert data["category"] == sample_template_request["category"]
            assert data["is_public"] == sample_template_request["is_public"]
            assert data["usage_count"] == 0
            assert "_links" in data
            assert "self" in data["_links"]

    @pytest.mark.asyncio
    async def test_create_public_template(
        self,
        async_client,
        test_user,
        auth_headers,
        sample_template_request,
    ):
        """Test creating a public template."""
        sample_template_request["is_public"] = True

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.post(
                "/api/v1/session-templates",
                json=sample_template_request,
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_get_template_success(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successfully retrieving a template."""
        # Arrange - Create template in database
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Template",
            description="Test description",
            category="development",
            system_prompt="Test prompt",
            allowed_tools=["Read", "Write"],
            sdk_options={"model": "claude-sonnet-4-5"},
            mcp_server_ids=[],
            is_public=False,
            is_organization_shared=False,
            version="1.0.0",
            tags=["test"],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.get(
                f"/api/v1/session-templates/{template.id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["id"] == str(template.id)
            assert data["name"] == template.name
            assert "_links" in data

    @pytest.mark.asyncio
    async def test_get_template_not_found(
        self,
        async_client,
        test_user,
        auth_headers,
    ):
        """Test getting non-existent template."""
        nonexistent_id = uuid4()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.get(
                f"/api/v1/session-templates/{nonexistent_id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_templates_my_scope(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test listing templates owned by user."""
        # Arrange - Create templates
        template1 = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="My Template 1",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        template2 = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="My Template 2",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template1)
        db_session.add(template2)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.get(
                "/api/v1/session-templates?scope=my",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "items" in data
            assert len(data["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_templates_public_scope(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test listing public templates."""
        # Arrange - Create public template
        public_template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Public Template",
            is_public=True,
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(public_template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.get(
                "/api/v1/session-templates?scope=public",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "items" in data
            # All templates should be public
            for item in data["items"]:
                assert item["is_public"] is True

    @pytest.mark.asyncio
    async def test_search_templates(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test searching templates."""
        # Arrange - Create template with unique name
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Unique Search Template",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=["searchable"],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.post(
                "/api/v1/session-templates/search",
                json={
                    "search_term": "Unique",
                    "page": 1,
                    "page_size": 10,
                },
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "items" in data
            # Should find our template
            template_ids = [item["id"] for item in data["items"]]
            assert str(template.id) in template_ids

    @pytest.mark.asyncio
    async def test_search_by_category(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test searching templates by category."""
        # Arrange
        security_template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Security Template",
            category="security",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(security_template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.post(
                "/api/v1/session-templates/search",
                json={
                    "category": "security",
                    "page": 1,
                    "page_size": 10,
                },
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "items" in data
            # All returned templates should be security category
            for item in data["items"]:
                if item.get("category"):
                    assert item["category"] == "security"

    @pytest.mark.asyncio
    async def test_get_most_used_templates(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test getting most used templates."""
        # Arrange - Create templates with different usage counts
        popular_template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Popular Template",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=100,
        )
        less_popular = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Less Popular",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=10,
        )
        db_session.add(popular_template)
        db_session.add(less_popular)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.get(
                "/api/v1/session-templates/popular/top?limit=10",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)
            # Should be sorted by usage count
            if len(data) >= 2:
                assert data[0]["usage_count"] >= data[1]["usage_count"]

    @pytest.mark.asyncio
    async def test_update_template_success(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successfully updating a template."""
        # Arrange
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Original Name",
            description="Original description",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.put(
                f"/api/v1/session-templates/{template.id}",
                json={
                    "name": "Updated Name",
                    "description": "Updated description",
                },
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_sharing_settings(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test updating template sharing settings."""
        # Arrange
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Template",
            is_public=False,
            is_organization_shared=False,
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.patch(
                f"/api/v1/session-templates/{template.id}/sharing",
                json={
                    "is_public": True,
                    "is_organization_shared": True,
                },
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["is_public"] is True
            assert data["is_organization_shared"] is True

    @pytest.mark.asyncio
    async def test_delete_template_success(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successfully deleting a template."""
        # Arrange
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Template to Delete",
            allowed_tools=[],
            sdk_options={},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.delete(
                f"/api/v1/session-templates/{template.id}",
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 204

            # Verify template is soft-deleted
            get_response = await async_client.get(
                f"/api/v1/session-templates/{template.id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_session_from_template(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test creating a session from a template."""
        # Arrange - Create template
        template = SessionTemplateModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Session Template",
            description="Template for sessions",
            system_prompt="You are an AI assistant",
            working_directory="/workspace",
            allowed_tools=["Read", "Write"],
            sdk_options={"model": "claude-sonnet-4-5"},
            mcp_server_ids=[],
            tags=[],
            template_metadata={},
            usage_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user

            # Act
            response = await async_client.post(
                "/api/v1/sessions",
                json={
                    "template_id": str(template.id),
                    "name": "Session from Template",
                },
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == 201

            data = response.json()
            assert data["name"] == "Session from Template"
            assert "metadata" in data
            # Should have template tracking in metadata
            if data.get("metadata"):
                assert "created_from_template_id" in data["metadata"]
