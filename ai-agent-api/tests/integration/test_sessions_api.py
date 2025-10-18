"""Integration tests for Sessions API."""

import pytest
import json
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.models.session import SessionModel
from app.models.user import UserModel, OrganizationModel


class TestSessionsAPIIntegration:
    """Integration tests for sessions API endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self,
        async_client,
        test_user,
        auth_headers,
    ):
        """Test successful session creation via API."""
        # Arrange
        request_data = {
            "name": "Integration Test Session",
            "description": "Test session for integration testing",
            "sdk_options": {
                "model": "claude-sonnet-4-5",
                "max_turns": 15,
                "permission_mode": "default",
            },
            "allowed_tools": ["Bash", "Write", "Read"],
        }
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.post(
                "/api/v1/sessions",
                json=request_data,
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 201
            
            data = response.json()
            assert data["name"] == request_data["name"]
            assert data["description"] == request_data["description"]
            assert data["status"] == "created"
            assert data["mode"] == "interactive"
            assert "_links" in data
            assert "self" in data["_links"]

    @pytest.mark.asyncio
    async def test_get_session_success(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
    ):
        """Test successful session retrieval via API."""
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                f"/api/v1/sessions/{test_session_model.id}",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == str(test_session_model.id)
            assert data["name"] == test_session_model.name
            assert "_links" in data

    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self,
        async_client,
        test_user,
        auth_headers,
    ):
        """Test session retrieval with non-existent ID."""
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                f"/api/v1/sessions/{uuid4()}",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_session_forbidden_different_user(
        self,
        async_client,
        test_session_model,
        auth_headers,
        db_session,
    ):
        """Test session retrieval forbidden for different user."""
        # Arrange - Create different user
        other_user = UserModel(
            id=uuid4(),
            organization_id=uuid4(),
            email="other@example.com",
            username="otheruser",
            role="user",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = other_user
            
            # Act
            response = await async_client.get(
                f"/api/v1/sessions/{test_session_model.id}",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 403
            assert "not authorized" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_sessions_success(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successful session listing via API."""
        # Arrange - Create multiple sessions
        sessions = []
        for i in range(3):
            session = SessionModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Session {i}",
                mode="interactive",
                status="created",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/session-{i}",
            )
            db_session.add(session)
            sessions.append(session)
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                "/api/v1/sessions",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 200
            
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 3
            assert "pagination" in data
            
            # Check HATEOAS links
            for item in data["items"]:
                assert "_links" in item
                assert "self" in item["_links"]

    @pytest.mark.asyncio
    async def test_list_sessions_with_filters(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test session listing with status filter."""
        # Arrange - Create sessions with different statuses
        active_session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Active Session",
            mode="interactive",
            status="active",
            sdk_options={"model": "claude-sonnet-4-5"},
            working_directory_path="/tmp/active",
        )
        paused_session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Paused Session",
            mode="interactive",
            status="paused",
            sdk_options={"model": "claude-sonnet-4-5"},
            working_directory_path="/tmp/paused",
        )
        db_session.add_all([active_session, paused_session])
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                "/api/v1/sessions?status=active",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successful message sending via API."""
        # Arrange
        test_session_model.status = "active"
        await db_session.commit()
        
        request_data = {
            "message": "Hello, Claude! What can you help me with?",
            "fork": False,
        }
        
        # Mock the SDK session service
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock send_message to return a message
            mock_message = AsyncMock()
            mock_message.id = uuid4()
            mock_service.send_message.return_value = mock_message
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.post(
                    f"/api/v1/sessions/{test_session_model.id}/query",
                    json=request_data,
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 200
                
                data = response.json()
                assert "message_id" in data
                assert data["status"] == test_session_model.status
                assert "_links" in data
                
                # Verify service was called
                mock_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_session_success(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successful session pausing via API."""
        # Arrange
        test_session_model.status = "active"
        await db_session.commit()
        
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock pause_session
            paused_session = AsyncMock()
            paused_session.id = test_session_model.id
            paused_session.status = "paused"
            mock_service.pause_session.return_value = paused_session
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.post(
                    f"/api/v1/sessions/{test_session_model.id}/pause",
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "paused"
                assert "_links" in data
                assert "resume" in data["_links"]

    @pytest.mark.asyncio
    async def test_resume_session_success(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test successful session resuming via API."""
        # Arrange
        test_session_model.status = "paused"
        await db_session.commit()
        
        request_data = {
            "fork": False,
        }
        
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock resume_session
            resumed_session = AsyncMock()
            resumed_session.id = test_session_model.id
            resumed_session.status = "active"
            mock_service.resume_session.return_value = resumed_session
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.post(
                    f"/api/v1/sessions/{test_session_model.id}/resume",
                    json=request_data,
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "active"
                assert "_links" in data

    @pytest.mark.asyncio
    async def test_terminate_session_success(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
    ):
        """Test successful session termination via API."""
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock terminate_session
            mock_service.terminate_session.return_value = None
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.delete(
                    f"/api/v1/sessions/{test_session_model.id}",
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 204
                
                # Verify service was called
                mock_service.terminate_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_session_messages(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test listing messages in a session."""
        # Arrange - Create some messages
        from app.models.message import MessageModel
        
        messages = []
        for i in range(3):
            message = MessageModel(
                id=uuid4(),
                session_id=test_session_model.id,
                sequence_number=i + 1,
                message_type="user" if i % 2 == 0 else "assistant",
                content={"text": f"Message {i}"},
            )
            db_session.add(message)
            messages.append(message)
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                f"/api/v1/sessions/{test_session_model.id}/messages",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 3
            
            # Messages should be in reverse chronological order
            for i, message_data in enumerate(data):
                assert "id" in message_data
                assert "message_type" in message_data
                assert "content" in message_data

    @pytest.mark.asyncio
    async def test_list_session_tool_calls(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test listing tool calls in a session."""
        # Arrange - Create some tool calls
        from app.models.tool_call import ToolCallModel
        
        tool_calls = []
        for i in range(2):
            tool_call = ToolCallModel(
                id=uuid4(),
                session_id=test_session_model.id,
                message_id=uuid4(),
                tool_name=f"test_tool_{i}",
                tool_use_id=f"tool_use_{i}",
                tool_input={"param": f"value_{i}"},
                status="success",
            )
            db_session.add(tool_call)
            tool_calls.append(tool_call)
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Act
            response = await async_client.get(
                f"/api/v1/sessions/{test_session_model.id}/tool-calls",
                headers=auth_headers,
            )
            
            # Assert
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 2
            
            for tool_call_data in data:
                assert "id" in tool_call_data
                assert "tool_name" in tool_call_data
                assert "tool_input" in tool_call_data
                assert "status" in tool_call_data

    @pytest.mark.asyncio
    async def test_unauthorized_access(
        self,
        async_client,
        test_session_model,
    ):
        """Test API access without authentication."""
        # Act
        response = await async_client.get(
            f"/api/v1/sessions/{test_session_model.id}",
        )
        
        # Assert
        assert response.status_code == 401 or response.status_code == 403

    @pytest.mark.asyncio
    async def test_session_fork_via_api(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test session forking via query API."""
        # Arrange
        test_session_model.status = "active"
        await db_session.commit()
        
        request_data = {
            "message": "Fork this session",
            "fork": True,
        }
        
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock fork_session
            forked_session = AsyncMock()
            forked_session.id = uuid4()
            forked_session.parent_session_id = test_session_model.id
            forked_session.is_fork = True
            forked_session.status = "active"
            mock_service.fork_session.return_value = forked_session
            
            # Mock send_message
            mock_message = AsyncMock()
            mock_message.id = uuid4()
            mock_service.send_message.return_value = mock_message
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.post(
                    f"/api/v1/sessions/{test_session_model.id}/query",
                    json=request_data,
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 200
                
                data = response.json()
                assert data["is_fork"] is True
                assert data["parent_session_id"] == str(test_session_model.id)
                
                # Verify fork_session was called
                mock_service.fork_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_handling(
        self,
        async_client,
        test_session_model,
        test_user,
        auth_headers,
    ):
        """Test API error handling and response format."""
        # Arrange - Mock service to raise exception
        with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_session.side_effect = Exception("Database error")
            
            with patch('app.api.dependencies.get_current_active_user') as mock_auth:
                mock_auth.return_value = test_user
                
                # Act
                response = await async_client.get(
                    f"/api/v1/sessions/{test_session_model.id}",
                    headers=auth_headers,
                )
                
                # Assert
                assert response.status_code == 500
                
                data = response.json()
                assert "error" in data
                assert "code" in data["error"]
                assert "message" in data["error"]
                assert "request_id" in data["error"]
                assert "timestamp" in data["error"]