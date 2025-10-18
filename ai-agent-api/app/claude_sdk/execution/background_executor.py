"""Background executor for automation tasks without streaming."""
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from uuid import UUID

from claude_agent_sdk import AssistantMessage, ResultMessage

from app.domain.entities.session import Session
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.core.config import ClientMetrics
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.result_handler import ResultHandler
from app.claude_sdk.handlers.error_handler import ErrorHandler
from app.claude_sdk.execution.base_executor import BaseExecutor
from app.claude_sdk.retry.retry_manager import RetryManager

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Background execution result with metrics.

    Attributes:
        session_id: Session identifier
        success: Whether execution succeeded
        data: Optional result data
        error_message: Error message if failed
        metrics: Client metrics from execution
    """

    session_id: UUID
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metrics: ClientMetrics


class BackgroundExecutor(BaseExecutor):
    """Execute background automation tasks without streaming.

    This executor is optimized for automation and batch processing:
    - No real-time streaming (better performance)
    - Built-in retry logic for reliability
    - Returns final result with metrics
    - Suitable for scheduled tasks and APIs

    Reference: POC script 08_production_ready.py for production patterns
    """

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        retry_manager: RetryManager,
    ):
        """Initialize background executor with retry support.

        Args:
            session: Domain Session entity
            client: Enhanced Claude SDK client
            message_handler: Handler for processing messages
            result_handler: Handler for processing results
            error_handler: Handler for error recovery
            retry_manager: Retry manager for failure recovery
        """
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.retry_manager = retry_manager

    async def execute(self, prompt: str) -> ExecutionResult:
        """Execute task and return final result (no streaming).

        Args:
            prompt: User prompt

        Returns:
            ExecutionResult: Execution outcome with metrics
        """
        logger.info(
            f"BackgroundExecutor executing query (no streaming)",
            extra={"session_id": str(self.session.id)},
        )

        try:
            # Disable partial messages for background execution
            self.client.config.include_partial_messages = False

            # Execute with retry logic
            await self.retry_manager.execute_with_retry(self._execute_query, prompt)

            # Get final metrics
            metrics = await self.client.get_metrics()

            return ExecutionResult(
                session_id=self.session.id,
                success=True,
                data={"status": "completed"},
                error_message=None,
                metrics=metrics,
            )

        except Exception as e:
            await self._handle_error(e, {"prompt": prompt})

            return ExecutionResult(
                session_id=self.session.id,
                success=False,
                data=None,
                error_message=str(e),
                metrics=await self.client.get_metrics(),
            )

    async def _execute_query(self, prompt: str) -> None:
        """Execute query without streaming (internal method).

        Args:
            prompt: User prompt
        """
        await self.client.query(prompt)

        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                await self.message_handler.handle_assistant_message(message, self.session.id)
            elif isinstance(message, ResultMessage):
                await self.result_handler.handle_result_message(message, self.session.id)
                break
