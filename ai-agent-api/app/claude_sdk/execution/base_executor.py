"""Base executor abstract class for all execution strategies."""
from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

from app.domain.entities.session import Session
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.result_handler import ResultHandler
from app.claude_sdk.handlers.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """Abstract base class for all executors.

    This class defines the common interface and error handling logic
    that all executor implementations must follow.

    Executors implement different execution strategies:
    - InteractiveExecutor: Real-time chat with streaming
    - BackgroundExecutor: Automation tasks without streaming
    - ForkedExecutor: Session continuation from parent

    All executors share common functionality:
    - Session management
    - Client connection handling
    - Message processing
    - Error handling

    Example:
        >>> class MyExecutor(BaseExecutor):
        ...     async def execute(self, prompt: str) -> Any:
        ...         # Implementation
        ...         pass
    """

    def __init__(
        self,
        session: Session,
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
    ):
        """Initialize base executor with dependencies.

        Args:
            session: Domain Session entity
            client: Enhanced Claude SDK client
            message_handler: Handler for processing messages
            result_handler: Handler for processing results
            error_handler: Handler for error recovery
        """
        self.session = session
        self.client = client
        self.message_handler = message_handler
        self.result_handler = result_handler
        self.error_handler = error_handler

        logger.info(
            f"{self.__class__.__name__} initialized for session {session.id}",
            extra={"session_id": str(session.id), "executor_type": self.__class__.__name__},
        )

    @abstractmethod
    async def execute(self, prompt: str) -> Any:
        """Execute query with strategy-specific implementation.

        This method must be implemented by all executor subclasses.
        The return type varies based on execution strategy:
        - InteractiveExecutor: AsyncIterator[AgentMessage]
        - BackgroundExecutor: ExecutionResult
        - ForkedExecutor: AsyncIterator[AgentMessage]

        Args:
            prompt: User prompt to execute

        Returns:
            Strategy-specific result (varies by executor type)

        Raises:
            Exception: If execution fails
        """
        pass

    async def _handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Common error handling logic for all executors.

        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        logger.error(
            f"Error in {self.__class__.__name__}: {str(error)}",
            extra={
                "session_id": str(self.session.id),
                "executor_type": self.__class__.__name__,
                "error_type": type(error).__name__,
                "context": context,
            },
        )

        await self.error_handler.handle_sdk_error(
            error=error, session_id=self.session.id, context=context
        )
