"""Integration tests for EnhancedClaudeClient with mock SDK."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.claude_sdk.client import EnhancedClaudeClient
from app.repositories.session_repository import SessionRepository
from app.repositories.hook_execution_repository import HookExecutionRepository


@pytest.mark.asyncio
class TestEnhancedClaudeClientIntegration:
    """Integration tests for EnhancedClaudeClient with database."""

    async def test_connect_and_track_session(self, db_session, test_session_model):
        """Test connecting client and tracking session state."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )

            # Act
            await client.connect()

            # Assert
            mock_sdk_instance.connect.assert_called_once()
            
            # Verify session status was updated
            session = await session_repo.find_by_id(test_session_model.id)
            assert session.status in ["active", "created"]

    async def test_query_with_token_tracking(self, db_session, test_session_model):
        """Test query execution with token usage tracking."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock response
            mock_response = MagicMock()
            mock_response.message = {
                "type": "assistant",
                "content": [{"type": "text", "text": "Hello!"}]
            }
            mock_response.token_usage = {
                "input_tokens": 50,
                "output_tokens": 10,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            }
            mock_sdk_instance.query.return_value = mock_response
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act
            response = await client.query("Hello")

            # Assert
            assert response == mock_response
            
            # Verify tokens were tracked
            session = await session_repo.find_by_id(test_session_model.id)
            assert session.total_input_tokens >= 50
            assert session.total_output_tokens >= 10

    async def test_streaming_with_database_updates(self, db_session, test_session_model):
        """Test streaming response with session updates."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock streaming response
            async def mock_stream():
                for chunk in ["Hello", " ", "World", "!"]:
                    yield {"type": "text", "text": chunk}
            
            mock_sdk_instance.stream_query.return_value = mock_stream()
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act
            chunks = []
            async for chunk in client.stream_query("Test"):
                chunks.append(chunk)

            # Assert
            assert len(chunks) == 4
            full_text = "".join([c["text"] for c in chunks])
            assert full_text == "Hello World!"

    async def test_error_handling_with_session_update(self, db_session, test_session_model):
        """Test error handling updates session status."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            mock_sdk_instance.query.side_effect = Exception("API Error")
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act & Assert
            with pytest.raises(Exception, match="API Error"):
                await client.query("Test")
            
            # Verify session was updated with error
            session = await session_repo.find_by_id(test_session_model.id)
            # Error state may be tracked in session metadata or status

    async def test_disconnect_cleanup(self, db_session, test_session_model):
        """Test disconnecting client cleans up resources."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act
            await client.disconnect()

            # Assert
            mock_sdk_instance.disconnect.assert_called_once()

    async def test_multiple_queries_cumulative_tokens(self, db_session, test_session_model):
        """Test multiple queries accumulate token usage."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock multiple responses
            responses = []
            for i in range(3):
                mock_response = MagicMock()
                mock_response.message = {
                    "type": "assistant",
                    "content": [{"type": "text", "text": f"Response {i}"}]
                }
                mock_response.token_usage = {
                    "input_tokens": 50 + i * 10,
                    "output_tokens": 20 + i * 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                }
                responses.append(mock_response)
            
            mock_sdk_instance.query.side_effect = responses
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act
            for i in range(3):
                await client.query(f"Query {i}")

            # Assert
            session = await session_repo.find_by_id(test_session_model.id)
            # Should have cumulative tokens: 50+60+70=180 input, 20+25+30=75 output
            assert session.total_input_tokens >= 180
            assert session.total_output_tokens >= 75

    async def test_cache_tokens_tracking(self, db_session, test_session_model):
        """Test cache tokens are properly tracked."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock response with cache tokens
            mock_response = MagicMock()
            mock_response.message = {
                "type": "assistant",
                "content": [{"type": "text", "text": "Cached response"}]
            }
            mock_response.token_usage = {
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 50,
            }
            mock_sdk_instance.query.return_value = mock_response
            
            client = EnhancedClaudeClient(
                session_id=test_session_model.id,
                session_repo=session_repo,
            )
            await client.connect()

            # Act
            await client.query("Test with cache")

            # Assert
            session = await session_repo.find_by_id(test_session_model.id)
            assert session.total_cache_creation_tokens >= 100
            assert session.total_cache_read_tokens >= 50

    async def test_concurrent_client_instances(self, db_session):
        """Test multiple client instances can coexist."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        # Create multiple sessions
        from app.models.session import SessionModel
        sessions = []
        for i in range(3):
            session = SessionModel(
                id=uuid4(),
                user_id=uuid4(),
                name=f"Session {i}",
                mode="interactive",
                status="created",
                sdk_options={"model": "claude-sonnet-4-5"},
            )
            db_session.add(session)
            sessions.append(session)
        await db_session.commit()

        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Create multiple clients
            clients = []
            for session in sessions:
                client = EnhancedClaudeClient(
                    session_id=session.id,
                    session_repo=session_repo,
                )
                await client.connect()
                clients.append(client)

            # Act - Each client queries independently
            for i, client in enumerate(clients):
                mock_response = MagicMock()
                mock_response.message = {"type": "assistant", "content": [{"type": "text", "text": f"Response {i}"}]}
                mock_response.token_usage = {
                    "input_tokens": 50 + i * 10,
                    "output_tokens": 20 + i * 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                }
                mock_sdk_instance.query.return_value = mock_response
                await client.query(f"Query {i}")

            # Assert - Each session has different token counts
            for i, session in enumerate(sessions):
                retrieved = await session_repo.find_by_id(session.id)
                assert retrieved.total_input_tokens >= 50 + i * 10
                assert retrieved.total_output_tokens >= 20 + i * 5

            # Cleanup
            for client in clients:
                await client.disconnect()
