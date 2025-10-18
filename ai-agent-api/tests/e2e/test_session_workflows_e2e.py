"""End-to-end tests for complete session workflows."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.session_service import SessionService
from app.repositories.session_repository import SessionRepository
from app.repositories.hook_execution_repository import HookExecutionRepository
from app.repositories.permission_decision_repository import PermissionDecisionRepository
from app.claude_sdk.hooks.hook_manager import HookManager
from app.claude_sdk.permissions.permission_manager import PermissionManager
from app.claude_sdk.permissions.policy_engine import PolicyEngine


@pytest.mark.asyncio
@pytest.mark.e2e
class TestSessionWorkflowE2E:
    """End-to-end tests for complete session workflows."""

    async def test_interactive_session_with_fork_workflow(self, db_session, test_user):
        """Test complete workflow: create interactive session, execute queries, fork, continue."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        decision_repo = PermissionDecisionRepository(db_session)
        
        service = SessionService(
            session_repo=session_repo,
            hook_execution_repo=hook_repo,
            permission_decision_repo=decision_repo,
        )

        with patch('app.claude_sdk.client.ClaudeAgentSDK') as mock_sdk:
            mock_sdk_instance = AsyncMock()
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock query responses
            mock_response = MagicMock()
            mock_response.message = {
                "type": "assistant",
                "content": [{"type": "text", "text": "Response"}]
            }
            mock_response.token_usage = {
                "input_tokens": 50,
                "output_tokens": 30,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            }
            mock_sdk_instance.query.return_value = mock_response

            # Step 1: Create session
            session = await service.create_session(
                user_id=test_user.id,
                name="E2E Interactive Session",
                mode="interactive",
                sdk_options={
                    "model": "claude-sonnet-4-5",
                    "max_turns": 10,
                    "hooks_enabled": True,
                },
            )
            assert session.id is not None
            assert session.status == "created"

            # Step 2: Start session and execute queries
            from app.claude_sdk.client import EnhancedClaudeClient
            with patch('app.claude_sdk.client.ClaudeAgentSDK', return_value=mock_sdk_instance):
                client = EnhancedClaudeClient(
                    session_id=session.id,
                    session_repo=session_repo,
                )
                await client.connect()
                
                # Execute multiple queries
                for i in range(3):
                    await client.query(f"Query {i}")
                
                await client.disconnect()

            # Verify session state
            updated_session = await session_repo.find_by_id(session.id)
            assert updated_session.total_input_tokens >= 150  # 3 * 50
            assert updated_session.total_output_tokens >= 90   # 3 * 30

            # Step 3: Fork session at this point
            forked_session = await service.fork_session_advanced(
                session_id=session.id,
                user_id=test_user.id,
                new_name="Forked Interactive Session",
            )
            assert forked_session.id != session.id
            assert forked_session.parent_session_id == session.id
            assert forked_session.total_input_tokens == updated_session.total_input_tokens

            # Step 4: Continue with forked session
            with patch('app.claude_sdk.client.ClaudeAgentSDK', return_value=mock_sdk_instance):
                forked_client = EnhancedClaudeClient(
                    session_id=forked_session.id,
                    session_repo=session_repo,
                )
                await forked_client.connect()
                await forked_client.query("Continue in forked session")
                await forked_client.disconnect()

            # Step 5: Verify both sessions exist independently
            original = await session_repo.find_by_id(session.id)
            forked = await session_repo.find_by_id(forked_session.id)
            
            assert original is not None
            assert forked is not None
            assert forked.total_input_tokens > original.total_input_tokens  # Forked has more queries

    async def test_background_task_with_archive_workflow(self, db_session, test_user):
        """Test complete workflow: create background session, execute, archive, retrieve."""
        # Arrange
        session_repo = SessionRepository(db_session)
        
        with patch('app.services.session_service.StorageArchiver') as mock_archiver:
            mock_archiver_instance = AsyncMock()
            mock_archiver.return_value = mock_archiver_instance
            mock_archiver_instance.archive_working_directory.return_value = {
                "archive_id": str(uuid4()),
                "s3_key": "archives/test/background.tar.gz",
                "local_path": "/tmp/archives/background.tar.gz",
                "manifest": {
                    "files": ["output.txt", "results.json"],
                    "total_size_bytes": 2048,
                    "file_count": 2,
                },
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            service = SessionService(session_repo=session_repo)

            # Step 1: Create background session
            session = await service.create_session(
                user_id=test_user.id,
                name="E2E Background Task",
                mode="background",
                sdk_options={
                    "model": "claude-sonnet-4-5",
                    "task_description": "Process data and generate report",
                },
            )
            assert session.mode == "background"

            # Step 2: Simulate task execution
            session.status = "active"
            session.query_count = 5
            session.total_input_tokens = 300
            session.total_output_tokens = 200
            await session_repo.update(session)

            # Step 3: Complete task
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            await session_repo.update(session)

            # Step 4: Archive results
            archive_result = await service.archive_session_to_storage(
                session_id=session.id,
                working_directory="/tmp/test-workdir",
            )
            
            assert "archive_id" in archive_result
            assert archive_result["status"] == "completed"
            assert archive_result["manifest"]["file_count"] == 2

            # Step 5: Retrieve archive info
            retrieved_archive = await service.retrieve_archive(session.id)
            assert retrieved_archive is not None
            assert "s3_key" in retrieved_archive

    async def test_monitoring_and_cost_tracking_workflow(self, db_session, test_user):
        """Test workflow with metrics collection and cost tracking."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        
        from app.claude_sdk.monitoring.metrics_collector import MetricsCollector
        from app.claude_sdk.monitoring.cost_tracker import CostTracker
        
        with patch('app.claude_sdk.monitoring.cost_tracker.UserRepository') as mock_user_repo, \
             patch('app.claude_sdk.monitoring.cost_tracker.settings') as mock_settings:
            
            mock_settings.MONTHLY_BUDGET_USD = 1000.0
            mock_user_repo_instance = AsyncMock()
            mock_user_repo.return_value = mock_user_repo_instance
            
            service = SessionService(
                session_repo=session_repo,
                hook_execution_repo=hook_repo,
            )

            # Step 1: Create session with monitoring enabled
            session = await service.create_session(
                user_id=test_user.id,
                name="Monitored Session",
                mode="interactive",
                sdk_options={
                    "model": "claude-sonnet-4-5",
                    "monitoring_enabled": True,
                },
            )

            # Step 2: Initialize monitoring components
            metrics_collector = MetricsCollector(session_repo=session_repo)
            cost_tracker = CostTracker(db_session=db_session)

            # Step 3: Simulate queries with token usage
            for i in range(10):
                await metrics_collector.record_query_duration(
                    session_id=session.id,
                    duration_seconds=1.5 + i * 0.1,
                )
                
                await metrics_collector.record_token_usage(
                    session_id=session.id,
                    input_tokens=100 + i * 10,
                    output_tokens=50 + i * 5,
                )
                
                # Track costs
                await cost_tracker.track_cost(
                    session_id=session.id,
                    user_id=test_user.id,
                    input_tokens=100 + i * 10,
                    output_tokens=50 + i * 5,
                    model="claude-sonnet-4-5",
                )

            # Step 4: Get metrics summary
            metrics = await service.get_session_metrics_summary(session.id)
            assert metrics["query_count"] >= 10
            assert metrics["total_input_tokens"] >= 1000
            assert metrics["total_output_tokens"] >= 500

            # Step 5: Check budget status
            budget_status = await cost_tracker.check_budget_status(test_user.id)
            assert budget_status["status"] in ["under_limit", "at_limit", "over_limit"]
            assert budget_status["monthly_budget"] == 1000.0

    async def test_permission_enforcement_workflow(self, db_session, test_user):
        """Test complete workflow with permission checks and logging."""
        # Arrange
        session_repo = SessionRepository(db_session)
        decision_repo = PermissionDecisionRepository(db_session)
        
        from app.claude_sdk.permissions.policies.file_access_policy import FileAccessPolicy
        from app.claude_sdk.permissions.policies.command_policy import CommandPolicy
        
        service = SessionService(
            session_repo=session_repo,
            permission_decision_repo=decision_repo,
        )

        # Step 1: Create session with strict permissions
        session = await service.create_session(
            user_id=test_user.id,
            name="Restricted Session",
            mode="interactive",
            sdk_options={
                "model": "claude-sonnet-4-5",
                "permission_mode": "strict",
            },
        )

        # Step 2: Setup permission manager
        policy_engine = PolicyEngine()
        
        file_policy = FileAccessPolicy(
            allowed_read_paths=["/tmp"],
            allowed_write_paths=["/tmp"],
        )
        command_policy = CommandPolicy()
        
        policy_engine.register_policy(file_policy)
        policy_engine.register_policy(command_policy)
        
        permission_manager = PermissionManager(
            session_id=session.id,
            user_id=test_user.id,
            policy_engine=policy_engine,
            decision_repo=decision_repo,
        )

        # Step 3: Attempt various operations
        operations = [
            {"tool_name": "Read", "tool_input": {"path": "/tmp/allowed.txt"}},  # Allowed
            {"tool_name": "Write", "tool_input": {"path": "/etc/passwd"}},      # Denied
            {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},         # Allowed
            {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}},       # Denied
        ]
        
        results = []
        for op in operations:
            result = await permission_manager.can_use_tool(op)
            results.append(result)

        # Step 4: Verify results
        assert results[0].allowed is True   # Read /tmp allowed
        assert results[1].allowed is False  # Write /etc denied
        assert results[2].allowed is True   # ls allowed
        assert results[3].allowed is False  # rm -rf denied

        # Step 5: Get permission history
        history = await service.get_session_permissions_history(session.id)
        assert len(history) == 4
        
        denied_ops = [h for h in history if h["decision"] == "deny"]
        assert len(denied_ops) == 2

        # Step 6: Get statistics
        stats = await decision_repo.get_decision_statistics(session.id)
        assert stats["total_decisions"] == 4
        assert stats["allowed_count"] == 2
        assert stats["denied_count"] == 2

    async def test_hooks_execution_workflow(self, db_session, test_user):
        """Test complete workflow with hook execution and logging."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        
        from app.claude_sdk.hooks.implementations.audit_hook import AuditHook
        from app.claude_sdk.hooks.implementations.metrics_hook import MetricsHook
        
        service = SessionService(
            session_repo=session_repo,
            hook_execution_repo=hook_repo,
        )

        with patch('app.claude_sdk.hooks.implementations.audit_hook.AuditService') as mock_audit:
            mock_audit_instance = AsyncMock()
            mock_audit.return_value = mock_audit_instance

            # Step 1: Create session with hooks
            session = await service.create_session(
                user_id=test_user.id,
                name="Hooked Session",
                mode="interactive",
                sdk_options={
                    "model": "claude-sonnet-4-5",
                    "hooks_enabled": True,
                    "enabled_hooks": ["audit", "metrics"],
                },
            )

            # Step 2: Setup hook manager
            hook_manager = HookManager(
                session_id=session.id,
                hook_execution_repo=hook_repo,
            )
            
            # Register hooks
            from app.claude_sdk.monitoring.metrics_collector import MetricsCollector
            metrics_collector = MetricsCollector(session_repo=session_repo)
            
            audit_hook = AuditHook(audit_service=mock_audit_instance, priority=100)
            metrics_hook = MetricsHook(metrics_collector=metrics_collector, priority=90)
            
            hook_manager.register_hook(audit_hook)
            hook_manager.register_hook(metrics_hook)

            # Step 3: Execute tool uses with hooks
            from app.claude_sdk.hooks.base_hook import HookType
            
            for i in range(5):
                pre_context = {
                    "tool_name": "Bash",
                    "tool_input": {"command": f"echo {i}"},
                    "session_id": session.id,
                }
                await hook_manager.execute_hooks(HookType.PRE_TOOL_USE, pre_context)
                
                post_context = {
                    "tool_name": "Bash",
                    "tool_input": {"command": f"echo {i}"},
                    "tool_output": {"stdout": str(i)},
                    "session_id": session.id,
                }
                await hook_manager.execute_hooks(HookType.POST_TOOL_USE, post_context)

            # Step 4: Verify hook executions logged
            executions = await hook_repo.find_by_session_id(session.id)
            assert len(executions) == 10  # 2 hooks * 5 tool uses

            # Step 5: Get hook statistics
            stats = await hook_repo.get_execution_statistics(session.id)
            assert stats["total_executions"] == 10
            assert stats["avg_execution_time_ms"] > 0

            # Step 6: Get hooks history through service
            hooks_history = await service.get_session_hooks_history(session.id)
            assert len(hooks_history) == 10
            
            audit_count = sum(1 for h in hooks_history if h["hook_name"] == "audit_hook")
            metrics_count = sum(1 for h in hooks_history if h["hook_name"] == "metrics_hook")
            assert audit_count == 5
            assert metrics_count == 5

    async def test_complete_lifecycle_with_all_features(self, db_session, test_user):
        """Test complete session lifecycle with hooks, permissions, monitoring, fork, and archive."""
        # Arrange
        session_repo = SessionRepository(db_session)
        hook_repo = HookExecutionRepository(db_session)
        decision_repo = PermissionDecisionRepository(db_session)
        
        with patch('app.services.session_service.StorageArchiver') as mock_archiver, \
             patch('app.claude_sdk.hooks.implementations.audit_hook.AuditService') as mock_audit:
            
            mock_archiver_instance = AsyncMock()
            mock_archiver.return_value = mock_archiver_instance
            mock_archiver_instance.archive_working_directory.return_value = {
                "archive_id": str(uuid4()),
                "s3_key": "archives/complete/lifecycle.tar.gz",
                "manifest": {"files": []},
            }
            
            mock_audit_instance = AsyncMock()
            mock_audit.return_value = mock_audit_instance
            
            service = SessionService(
                session_repo=session_repo,
                hook_execution_repo=hook_repo,
                permission_decision_repo=decision_repo,
            )

            # Step 1: Create fully-featured session
            session = await service.create_session(
                user_id=test_user.id,
                name="Complete Lifecycle Session",
                mode="interactive",
                sdk_options={
                    "model": "claude-sonnet-4-5",
                    "hooks_enabled": True,
                    "permission_mode": "strict",
                    "monitoring_enabled": True,
                },
            )

            # Step 2: Execute work with all features active
            # (Hooks would be registered, permissions checked, metrics collected)
            session.query_count = 10
            session.total_input_tokens = 500
            session.total_output_tokens = 300
            await session_repo.update(session)

            # Step 3: Fork session
            forked = await service.fork_session_advanced(
                session_id=session.id,
                user_id=test_user.id,
                new_name="Forked Complete Session",
            )
            assert forked.id != session.id

            # Step 4: Archive original session
            archive_result = await service.archive_session_to_storage(
                session_id=session.id,
                working_directory="/tmp/workdir",
            )
            assert "archive_id" in archive_result

            # Step 5: Get comprehensive metrics
            metrics = await service.get_session_metrics_summary(session.id)
            assert metrics["query_count"] == 10
            assert metrics["total_input_tokens"] == 500

            # Step 6: Verify forked session is independent and active
            forked_retrieved = await session_repo.find_by_id(forked.id)
            assert forked_retrieved is not None
            assert forked_retrieved.status != "archived"

            # Final verification: Both sessions exist with correct states
            original = await session_repo.find_by_id(session.id)
            assert original is not None
