"""Unit tests for SDKIntegratedSessionService."""

import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.sdk_session_service import SDKIntegratedSessionService
from app.domain.entities.session import Session, SessionStatus
from app.domain.value_objects.message import Message, MessageType
from app.domain.exceptions import SessionNotActiveError, SessionNotFoundError


class TestSDKIntegratedSessionService:
    """Test cases for SDKIntegratedSessionService."""

    @pytest.fixture
    def sdk_session_service(
        self,
        db_session,
        mock_storage_manager,
        mock_audit_service,
        mock_claude_sdk_client,
        mock_mcp_config_builder,
        mock_permission_service,
        mock_event_broadcaster,
    ):
        """Create SDKIntegratedSessionService with mocked dependencies."""
        from app.repositories.session_repository import SessionRepository
        from app.repositories.message_repository import MessageRepository
        from app.repositories.tool_call_repository import ToolCallRepository
        from app.repositories.user_repository import UserRepository
        
        service = SDKIntegratedSessionService(
            db=db_session,
            session_repo=SessionRepository(db_session),
            message_repo=MessageRepository(db_session),
            tool_call_repo=ToolCallRepository(db_session),
            user_repo=UserRepository(db_session),
            storage_manager=mock_storage_manager,
            audit_service=mock_audit_service,
        )
        
        # Mock the SDK client manager
        service.sdk_client_manager = AsyncMock()
        service.sdk_client_manager.has_client.return_value = False
        service.sdk_client_manager.get_client.return_value = mock_claude_sdk_client
        service.sdk_client_manager.create_client.return_value = mock_claude_sdk_client
        
        # Mock permission service
        service.permission_service = mock_permission_service
        
        # Mock event broadcaster
        service.event_broadcaster = mock_event_broadcaster
        
        return service

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
        mock_claude_sdk_client,
        mock_sdk_message_stream,
    ):
        """Test successful message sending through SDK."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        message_content = "Hello, Claude!"
        
        # Set session to active status
        test_session_model.status = "active"
        await sdk_session_service.db.commit()
        
        # Mock SDK client responses
        mock_claude_sdk_client.query.return_value = None
        mock_claude_sdk_client.receive_response.return_value = mock_sdk_message_stream
        
        # Mock message processor
        mock_message = Message(
            id=uuid4(),
            session_id=uuid4(),
            sequence_number=1,
            message_type=MessageType.ASSISTANT,
            content={"text": "Hello back!"},
        )
        
        with patch('app.services.sdk_session_service.MessageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor
            mock_processor.process_message_stream.return_value = AsyncMock()
            mock_processor.process_message_stream.return_value.__aiter__.return_value = [mock_message]
            
            # Act
            result_message = await sdk_session_service.send_message(
                session_id=session_id,
                message_content=message_content,
            )
            
            # Assert
            assert result_message is not None
            mock_claude_sdk_client.query.assert_called_once_with(message_content)

    @pytest.mark.asyncio
    async def test_send_message_session_not_active(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
    ):
        """Test message sending fails for inactive session."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        message_content = "Hello!"
        
        # Set session to terminated status
        test_session_model.status = "terminated"
        await sdk_session_service.db.commit()
        
        # Act & Assert
        with pytest.raises(SessionNotActiveError):
            await sdk_session_service.send_message(
                session_id=session_id,
                message_content=message_content,
            )

    @pytest.mark.asyncio
    async def test_send_message_creates_sdk_client(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
        mock_claude_sdk_client,
    ):
        """Test that SDK client is created when not exists."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        message_content = "Hello!"
        
        # Set session to created status (will transition to active)
        test_session_model.status = "created"
        await sdk_session_service.db.commit()
        
        # Mock SDK client manager - no existing client
        sdk_session_service.sdk_client_manager.has_client.return_value = False
        
        # Mock message processor
        with patch('app.services.sdk_session_service.MessageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor
            mock_processor.process_message_stream.return_value = AsyncMock()
            mock_processor.process_message_stream.return_value.__aiter__.return_value = []
            
            # Mock _setup_sdk_client method
            with patch.object(sdk_session_service, '_setup_sdk_client', new_callable=AsyncMock) as mock_setup:
                # Act
                await sdk_session_service.send_message(
                    session_id=session_id,
                    message_content=message_content,
                )
                
                # Assert
                mock_setup.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.sdk_session_service.MCPConfigBuilder')
    @patch('app.repositories.mcp_server_repository.MCPServerRepository')
    async def test_setup_sdk_client_builds_mcp_config(
        self,
        mock_mcp_repo_class,
        mock_mcp_builder_class,
        sdk_session_service,
        test_session_model,
        test_user,
    ):
        """Test that _setup_sdk_client builds MCP configuration."""
        # Arrange
        session = sdk_session_service._model_to_entity(test_session_model)
        user_id = test_user.id
        
        mock_mcp_repo = AsyncMock()
        mock_mcp_repo_class.return_value = mock_mcp_repo
        
        mock_mcp_builder = AsyncMock()
        mock_mcp_builder_class.return_value = mock_mcp_builder
        mock_mcp_builder.build_session_mcp_config.return_value = {
            "kubernetes_readonly": {
                "command": "python",
                "args": ["-m", "kubemind.mcp.kubernetes"],
            },
            "database": {
                "type": "stdio",
                "command": "python",
                "args": ["-m", "kubemind.mcp.database"],
            },
        }
        
        # Act
        await sdk_session_service._setup_sdk_client(session, user_id)
        
        # Assert
        mock_mcp_builder.build_session_mcp_config.assert_called_once_with(
            user_id=user_id,
            include_sdk_tools=True,
        )
        
        # Verify SDK client manager was called
        sdk_session_service.sdk_client_manager.create_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_sdk_client_creates_permission_callback(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
        mock_permission_service,
    ):
        """Test that _setup_sdk_client creates permission callback."""
        # Arrange
        session = sdk_session_service._model_to_entity(test_session_model)
        user_id = test_user.id
        
        mock_callback = AsyncMock()
        mock_permission_service.create_permission_callback.return_value = mock_callback
        
        with patch('app.services.sdk_session_service.MCPConfigBuilder'):
            with patch('app.repositories.mcp_server_repository.MCPServerRepository'):
                # Act
                await sdk_session_service._setup_sdk_client(session, user_id)
                
                # Assert
                mock_permission_service.create_permission_callback.assert_called_once_with(
                    session_id=session.id,
                    user_id=user_id,
                )

    @pytest.mark.asyncio
    async def test_cleanup_session_client(
        self,
        sdk_session_service,
    ):
        """Test SDK client cleanup."""
        # Arrange
        session_id = uuid4()
        
        # Act
        await sdk_session_service.cleanup_session_client(session_id)
        
        # Assert
        sdk_session_service.sdk_client_manager.disconnect_client.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_terminate_session_cleans_up_client(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
    ):
        """Test that session termination cleans up SDK client."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        
        with patch.object(sdk_session_service, 'cleanup_session_client', new_callable=AsyncMock) as mock_cleanup:
            # Act
            await sdk_session_service.terminate_session(
                session_id=UUID(session_id),
                user_id=user_id,
            )
            
            # Assert
            mock_cleanup.assert_called_once_with(UUID(session_id))

    @pytest.mark.asyncio
    async def test_delete_session_cleans_up_client(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
    ):
        """Test that session deletion cleans up SDK client."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        
        with patch.object(sdk_session_service, 'cleanup_session_client', new_callable=AsyncMock) as mock_cleanup:
            # Act
            await sdk_session_service.delete_session(
                session_id=UUID(session_id),
                user_id=user_id,
            )
            
            # Assert
            mock_cleanup.assert_called_once_with(UUID(session_id))

    @pytest.mark.asyncio
    async def test_send_message_handles_sdk_error(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
        mock_claude_sdk_client,
    ):
        """Test error handling during message sending."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        message_content = "Hello!"
        
        test_session_model.status = "active"
        await sdk_session_service.db.commit()
        
        # Mock SDK client to raise exception
        mock_claude_sdk_client.query.side_effect = Exception("SDK Error")
        
        # Act & Assert
        with pytest.raises(Exception, match="SDK Error"):
            await sdk_session_service.send_message(
                session_id=session_id,
                message_content=message_content,
            )
        
        # Verify session status is updated to failed
        updated_session = await sdk_session_service.get_session(session_id, user_id)
        assert updated_session.status == SessionStatus.FAILED

    @pytest.mark.asyncio
    async def test_send_message_updates_session_status(
        self,
        sdk_session_service,
        test_session_model,
        test_user,
        mock_claude_sdk_client,
    ):
        """Test that session status is properly updated during message flow."""
        # Arrange
        session_id = str(test_session_model.id)
        user_id = test_user.id
        message_content = "Test message"
        
        # Start with created status
        test_session_model.status = "created"
        await sdk_session_service.db.commit()
        
        # Mock successful flow
        mock_claude_sdk_client.query.return_value = None
        mock_claude_sdk_client.receive_response.return_value = AsyncMock()
        
        with patch('app.services.sdk_session_service.MessageProcessor') as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor
            mock_processor.process_message_stream.return_value = AsyncMock()
            mock_processor.process_message_stream.return_value.__aiter__.return_value = []
            
            with patch.object(sdk_session_service, '_setup_sdk_client', new_callable=AsyncMock):
                # Act
                await sdk_session_service.send_message(
                    session_id=session_id,
                    message_content=message_content,
                )
        
        # Assert - Session should be active after successful processing
        updated_session = await sdk_session_service.get_session(session_id, user_id)
        assert updated_session.status == SessionStatus.ACTIVE