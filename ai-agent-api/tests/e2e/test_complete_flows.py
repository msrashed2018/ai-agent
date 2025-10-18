"""End-to-End tests for complete AI-Agent-API service flows."""

import pytest
import json
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.session import SessionModel
from app.models.user import UserModel, OrganizationModel
from app.models.mcp_server import MCPServerModel


class TestCompleteFlows:
    """End-to-end tests for complete service flows."""

    @pytest.mark.asyncio
    async def test_complete_session_message_flow(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test complete flow: Create session → Send message → Receive response."""
        
        # Step 1: Create session
        create_request = {
            "name": "E2E Test Session",
            "description": "End-to-end test session",
            "sdk_options": {
                "model": "claude-sonnet-4-5",
                "max_turns": 10,
                "permission_mode": "default",
            },
            "allowed_tools": ["Bash", "Write"],
        }
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Mock session service for creation
            with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                # Mock created session
                created_session = AsyncMock()
                created_session.id = uuid4()
                created_session.name = create_request["name"]
                created_session.status = "created"
                created_session.mode = "interactive"
                created_session.user_id = test_user.id
                mock_service.create_session.return_value = created_session
                
                # Create session
                response = await async_client.post(
                    "/api/v1/sessions",
                    json=create_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 201
                session_data = response.json()
                session_id = session_data["id"]
                
                # Step 2: Send message to session
                message_request = {
                    "message": "List files in the current directory using ls command",
                    "fork": False,
                }
                
                # Mock message response
                mock_message = AsyncMock()
                mock_message.id = uuid4()
                mock_service.send_message.return_value = mock_message
                
                # Update session status to active for message sending
                created_session.status = "active"
                
                response = await async_client.post(
                    f"/api/v1/sessions/{session_id}/query",
                    json=message_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 200
                message_data = response.json()
                
                # Verify message was processed
                assert "message_id" in message_data
                assert message_data["status"] == "active"
                
                # Verify service calls
                mock_service.create_session.assert_called_once()
                mock_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_server_integration_flow(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test MCP server configuration and usage flow."""
        
        # Step 1: Create MCP server
        mcp_create_request = {
            "name": "test_filesystem",
            "description": "Test filesystem MCP server",
            "config_type": "stdio",
            "config": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
            },
            "is_enabled": True,
        }
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Create MCP server
            response = await async_client.post(
                "/api/v1/mcp-servers",
                json=mcp_create_request,
                headers=auth_headers,
            )
            
            assert response.status_code == 201
            mcp_server_data = response.json()
            
            # Step 2: Create session (should include MCP server)
            session_request = {
                "name": "MCP Integration Session",
                "sdk_options": {
                    "model": "claude-sonnet-4-5",
                    "max_turns": 5,
                },
            }
            
            with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                # Mock session creation with MCP config
                mock_session = AsyncMock()
                mock_session.id = uuid4()
                mock_session.sdk_options.mcp_servers = {
                    "test_filesystem": {
                        "command": "npx",
                        "args": ["@modelcontextprotocol/server-filesystem", "/tmp"],
                    },
                    "kubernetes_readonly": {
                        "tools": [{"name": "list_pods", "function": MagicMock()}],
                    },
                }
                mock_service.create_session.return_value = mock_session
                
                response = await async_client.post(
                    "/api/v1/sessions",
                    json=session_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 201
                
                # Step 3: Send message using MCP tool
                message_request = {
                    "message": "List files in /tmp directory using the filesystem server",
                }
                
                mock_message = AsyncMock()
                mock_message.id = uuid4()
                mock_service.send_message.return_value = mock_message
                
                session_id = response.json()["id"]
                response = await async_client.post(
                    f"/api/v1/sessions/{session_id}/query",
                    json=message_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_task_execution_flow(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test complete task creation and execution flow."""
        
        # Step 1: Create task
        task_request = {
            "name": "System Health Check",
            "description": "Check system health and resources",
            "prompt_template": "Check the system status for {environment} environment and report CPU, memory usage",
            "allowed_tools": ["Bash", "mcp__monitoring__get_system_metrics"],
            "sdk_options": {
                "model": "claude-sonnet-4-5",
                "max_turns": 3,
            },
            "generate_report": True,
            "report_format": "html",
        }
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Mock task service
            with patch('app.api.v1.tasks.TaskService') as mock_task_service_class:
                mock_task_service = AsyncMock()
                mock_task_service_class.return_value = mock_task_service
                
                # Mock created task
                mock_task = AsyncMock()
                mock_task.id = uuid4()
                mock_task.name = task_request["name"]
                mock_task.user_id = test_user.id
                mock_task_service.create_task.return_value = mock_task
                
                # Create task
                response = await async_client.post(
                    "/api/v1/tasks",
                    json=task_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 201
                task_data = response.json()
                task_id = task_data["id"]
                
                # Step 2: Execute task
                execute_request = {
                    "variables": {
                        "environment": "production",
                    },
                }
                
                # Mock task execution
                mock_execution = AsyncMock()
                mock_execution.id = uuid4()
                mock_execution.task_id = uuid4()
                mock_execution.status = "completed"
                mock_execution.session_id = uuid4()
                mock_execution.report_id = uuid4()
                mock_task_service.execute_task.return_value = mock_execution
                
                response = await async_client.post(
                    f"/api/v1/tasks/{task_id}/execute",
                    json=execute_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 200
                execution_data = response.json()
                
                # Verify execution
                assert execution_data["status"] == "completed"
                assert "session_id" in execution_data
                assert "report_id" in execution_data
                
                # Verify service calls
                mock_task_service.create_task.assert_called_once()
                mock_task_service.execute_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_streaming_flow(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test WebSocket streaming for real-time session updates."""
        
        # Step 1: Create session
        session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="WebSocket Test Session",
            mode="interactive",
            status="active",
            sdk_options={"model": "claude-sonnet-4-5"},
            working_directory_path="/tmp/ws-test",
        )
        db_session.add(session)
        await db_session.commit()
        
        # Step 2: Test WebSocket connection
        # Note: This is a simplified test - real WebSocket testing would require
        # additional setup with pytest-asyncio and websockets library
        
        with patch('app.api.dependencies.get_websocket_user') as mock_ws_auth:
            mock_ws_auth.return_value = test_user
            
            # Mock WebSocket connection
            mock_websocket = AsyncMock()
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_json = AsyncMock()
            mock_websocket.receive_text = AsyncMock(
                return_value=json.dumps({
                    "type": "query",
                    "message": "Hello from WebSocket!"
                })
            )
            
            # Mock SDK session service
            with patch('app.api.v1.websocket.SDKIntegratedSessionService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                
                mock_message = AsyncMock()
                mock_message.id = uuid4()
                mock_service.send_message.return_value = mock_message
                
                # Test WebSocket endpoint logic (simplified)
                # In a real test, we would establish actual WebSocket connection
                # and verify message flow
                
                # Verify session exists and is accessible
                response = await async_client.get(
                    f"/api/v1/sessions/{session.id}",
                    headers=auth_headers,
                )
                
                assert response.status_code == 200

    @pytest.mark.asyncio 
    async def test_permission_and_security_flow(
        self,
        async_client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test permission checking and security throughout the flow."""
        
        # Step 1: Create session
        session = SessionModel(
            id=uuid4(),
            user_id=test_user.id,
            name="Security Test Session",
            mode="interactive",
            status="active",
            sdk_options={"model": "claude-sonnet-4-5"},
            working_directory_path="/tmp/security-test",
        )
        db_session.add(session)
        await db_session.commit()
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Step 2: Test access to own session (should succeed)
            response = await async_client.get(
                f"/api/v1/sessions/{session.id}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            
            # Step 3: Test access to other user's session (should fail)
            other_user = UserModel(
                id=uuid4(),
                organization_id=uuid4(),
                email="other@example.com",
                username="otheruser",
                role="user",
                is_active=True,
            )
            db_session.add(other_user)
            
            other_session = SessionModel(
                id=uuid4(),
                user_id=other_user.id,
                name="Other User Session",
                mode="interactive",
                status="active",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path="/tmp/other-test",
            )
            db_session.add(other_session)
            await db_session.commit()
            
            response = await async_client.get(
                f"/api/v1/sessions/{other_session.id}",
                headers=auth_headers,
            )
            assert response.status_code == 403
            
            # Step 4: Test admin access (admin can access any session)
            admin_user = UserModel(
                id=uuid4(),
                organization_id=test_user.organization_id,
                email="admin@example.com",
                username="admin",
                role="admin",
                is_active=True,
            )
            db_session.add(admin_user)
            await db_session.commit()
            
            mock_auth.return_value = admin_user
            
            response = await async_client.get(
                f"/api/v1/sessions/{other_session.id}",
                headers=auth_headers,
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_flow(
        self,
        async_client,
        test_user,
        auth_headers,
    ):
        """Test error handling and recovery throughout the system."""
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Step 1: Test validation errors
            invalid_session_request = {
                "name": "",  # Invalid empty name
                "sdk_options": {
                    "model": "invalid-model",  # Invalid model
                },
            }
            
            response = await async_client.post(
                "/api/v1/sessions",
                json=invalid_session_request,
                headers=auth_headers,
            )
            
            assert response.status_code == 422
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"]["code"] == "VALIDATION_ERROR"
            
            # Step 2: Test resource not found
            response = await async_client.get(
                f"/api/v1/sessions/{uuid4()}",
                headers=auth_headers,
            )
            
            assert response.status_code == 404
            
            # Step 3: Test service errors
            with patch('app.api.v1.sessions.SDKIntegratedSessionService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.create_session.side_effect = Exception("Database connection failed")
                
                valid_session_request = {
                    "name": "Test Session",
                    "sdk_options": {"model": "claude-sonnet-4-5"},
                }
                
                response = await async_client.post(
                    "/api/v1/sessions",
                    json=valid_session_request,
                    headers=auth_headers,
                )
                
                assert response.status_code == 500
                error_data = response.json()
                assert "error" in error_data
                assert "request_id" in error_data["error"]
                assert "timestamp" in error_data["error"]

    @pytest.mark.asyncio
    async def test_claude_desktop_config_integration_flow(
        self,
        async_client,
        test_user,
        auth_headers,
    ):
        """Test Claude Desktop configuration import/export flow."""
        
        # Step 1: Import Claude Desktop config
        claude_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-filesystem", "/Users/test"],
                },
                "github": {
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"
                    }
                }
            }
        }
        
        with patch('app.api.dependencies.get_current_active_user') as mock_auth:
            mock_auth.return_value = test_user
            
            # Mock MCP config manager
            with patch('app.api.v1.mcp_import_export.MCPConfigManager') as mock_manager_class:
                mock_manager = AsyncMock()
                mock_manager_class.return_value = mock_manager
                
                mock_manager.import_claude_desktop_config.return_value = {
                    "imported": 2,
                    "skipped": 0,
                    "errors": [],
                }
                
                # Import config
                response = await async_client.post(
                    "/api/v1/mcp-servers/import",
                    json={
                        "config": claude_config,
                        "override_existing": True,
                    },
                    headers=auth_headers,
                )
                
                assert response.status_code == 200
                import_data = response.json()
                assert import_data["imported"] == 2
                assert import_data["skipped"] == 0
                
                # Step 2: Export config
                mock_manager.export_claude_desktop_config.return_value = claude_config
                
                response = await async_client.get(
                    "/api/v1/mcp-servers/export",
                    headers=auth_headers,
                )
                
                assert response.status_code == 200
                export_data = response.json()
                assert "mcpServers" in export_data
                assert len(export_data["mcpServers"]) == 2
                
                # Step 3: Get server templates
                mock_manager.get_server_templates.return_value = [
                    {
                        "name": "kubernetes",
                        "description": "Kubernetes MCP server",
                        "config_type": "stdio",
                        "config": {
                            "command": "kubectl-mcp-server",
                        },
                    }
                ]
                
                response = await async_client.get(
                    "/api/v1/mcp-servers/templates",
                    headers=auth_headers,
                )
                
                assert response.status_code == 200
                templates_data = response.json()
                assert len(templates_data) == 1
                assert templates_data[0]["name"] == "kubernetes"