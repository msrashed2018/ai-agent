"""Forked executor for session continuation from parent session."""
from typing import AsyncIterator, Optional
from uuid import UUID

from claude_agent_sdk import AssistantMessage, ResultMessage

from app.domain.entities.session import Session
from app.domain.value_objects.message import Message as DomainMessage
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.handlers.message_handler import MessageHandler
from app.claude_sdk.handlers.result_handler import ResultHandler
from app.claude_sdk.handlers.error_handler import ErrorHandler
from app.claude_sdk.execution.base_executor import BaseExecutor
from app.repositories.message_repository import MessageRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class ForkedExecutor(BaseExecutor):
    """Execute forked session with restored context from parent.

    This executor enables session forking:
    - Restores conversation history from parent session
    - Continues conversation from specific point
    - Useful for exploring alternative paths
    - Maintains parent-child relationship

    Note: Full context restoration depends on SDK support (Phase 3 feature)
    """

    def __init__(
        self,
        session: Session,
        parent_session_id: UUID,
        fork_at_message: Optional[int],
        client: EnhancedClaudeClient,
        message_handler: MessageHandler,
        result_handler: ResultHandler,
        error_handler: ErrorHandler,
        message_repo: MessageRepository,
    ):
        """Initialize forked executor with parent context.

        Args:
            session: Domain Session entity (forked session)
            parent_session_id: Parent session to fork from
            fork_at_message: Optional message index to fork from
            client: Enhanced Claude SDK client
            message_handler: Handler for processing messages
            result_handler: Handler for processing results
            error_handler: Handler for error recovery
            message_repo: Repository for retrieving parent messages
        """
        super().__init__(session, client, message_handler, result_handler, error_handler)
        self.parent_session_id = parent_session_id
        self.fork_at_message = fork_at_message
        self.message_repo = message_repo

    async def execute(self, prompt: str) -> AsyncIterator[DomainMessage]:
        """Execute in forked session with restored context.

        Args:
            prompt: User prompt

        Yields:
            DomainMessage: Agent messages

        Raises:
            Exception: If execution fails
        """
        logger.info(
            "Forked executor starting execution with context restoration",
            extra={
                "session_id": str(self.session.id),
                "user_id": str(self.session.user_id),
                "parent_session_id": str(self.parent_session_id),
                "fork_at_message": self.fork_at_message,
                "prompt_length": len(prompt)
            }
        )

        try:
            # Restore context from parent session
            await self._restore_context()

            # Continue conversation (same as interactive executor)
            await self.client.query(prompt)

            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    domain_message = await self.message_handler.handle_assistant_message(
                        message, self.session.id
                    )
                    yield domain_message

                elif isinstance(message, ResultMessage):
                    await self.result_handler.handle_result_message(message, self.session.id)
                    break

        except Exception as e:
            await self._handle_error(e, {"prompt": prompt, "parent_session_id": str(self.parent_session_id)})
            raise

    async def _restore_context(self) -> None:
        """Restore conversation history from parent session.

        This method retrieves parent messages and prepares context
        for the forked session. Full implementation depends on SDK
        support for session continuation (planned for Phase 3).
        """
        # Retrieve parent session messages
        parent_messages = await self.message_repo.get_by_session(
            self.parent_session_id, limit=self.fork_at_message
        )

        logger.info(
            f"Retrieved {len(parent_messages)} messages from parent session",
            extra={"parent_session_id": str(self.parent_session_id)},
        )

        # TODO: Implement context restoration with SDK
        # This requires SDK support for conversation continuation
        # For now, we log the intent
        logger.warning("Full context restoration not yet implemented (Phase 3 feature)")
