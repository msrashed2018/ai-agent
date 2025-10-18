"""Session manager for Claude SDK session lifecycle management."""
import logging
from typing import Dict, Optional, Any
from uuid import UUID
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.session import Session, SessionMode, SessionStatus
from app.claude_sdk.core.client import EnhancedClaudeClient
from app.claude_sdk.core.config import ClientConfig
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.working_directory_archive_repository import WorkingDirectoryArchiveRepository
from app.claude_sdk.persistence.storage_archiver import StorageArchiver

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages Claude SDK sessions throughout their lifecycle.

    This class manages the lifecycle of Claude SDK client sessions:
    - Creates new sessions with appropriate configuration
    - Maintains registry of active clients
    - Resumes paused sessions
    - Forks sessions from parent sessions
    - Archives sessions when completed
    - Provides centralized access to active clients

    Example:
        >>> manager = SessionManager(db)
        >>> client = await manager.create_session(
        ...     session_id=session_id,
        ...     mode=SessionMode.INTERACTIVE,
        ...     config=session.sdk_options
        ... )
        >>> # Use client...
        >>> await manager.archive_session(session_id)
    """

    def __init__(
        self,
        db: AsyncSession,
        storage_archiver: Optional[StorageArchiver] = None
    ):
        """Initialize session manager with database session.

        Args:
            db: Async database session for repository operations
            storage_archiver: Optional storage archiver for working directory archival
        """
        self.db = db
        self.active_clients: Dict[UUID, EnhancedClaudeClient] = {}
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)

        # Initialize StorageArchiver if not provided
        if storage_archiver is None:
            archive_repo = WorkingDirectoryArchiveRepository(db)
            self.storage_archiver = StorageArchiver(db, archive_repo)
        else:
            self.storage_archiver = storage_archiver

        logger.info("SessionManager initialized")

    async def create_session(
        self, session_id: UUID, mode: SessionMode, session: Session
    ) -> EnhancedClaudeClient:
        """Create new Claude SDK session.

        Args:
            session_id: Unique session identifier
            mode: Session mode (interactive, background, forked)
            session: Domain Session entity with configuration

        Returns:
            EnhancedClaudeClient: Connected client ready for use

        Raises:
            ValueError: If session already exists in active clients
        """
        if session_id in self.active_clients:
            logger.warning(f"Session {session_id} already exists in active clients")
            raise ValueError(f"Session {session_id} is already active")

        logger.info(
            f"Creating new session: {session_id} (mode={mode.value})",
            extra={"session_id": str(session_id), "mode": mode.value},
        )

        # Build client configuration
        config = ClientConfig(
            session_id=session_id,
            model=session.sdk_options.get("model", "claude-sonnet-4-5"),
            permission_mode=session.permission_mode or "default",
            max_turns=session.sdk_options.get("max_turns", 10),
            max_retries=session.max_retries or 3,
            retry_delay=session.retry_delay or 2.0,
            timeout_seconds=session.timeout_seconds or 120,
            include_partial_messages=session.include_partial_messages or False,
            working_directory=Path(session.working_directory_path),
            allowed_tools=session.sdk_options.get("allowed_tools"),
        )

        # Create enhanced client
        client = EnhancedClaudeClient(config)

        # Connect to SDK
        await client.connect()

        # Register in active clients
        self.active_clients[session_id] = client

        logger.info(
            f"Session created successfully: {session_id}",
            extra={"session_id": str(session_id), "active_sessions": len(self.active_clients)},
        )

        return client

    async def resume_session(
        self, session_id: UUID, session: Session, restore_context: bool = True
    ) -> EnhancedClaudeClient:
        """Resume paused or archived session.

        Args:
            session_id: Session to resume
            session: Domain Session entity
            restore_context: Whether to restore conversation history

        Returns:
            EnhancedClaudeClient: Reconnected client

        Raises:
            ValueError: If session cannot be resumed
        """
        logger.info(
            f"Resuming session: {session_id} (restore_context={restore_context})",
            extra={"session_id": str(session_id)},
        )

        # Check if already active
        if session_id in self.active_clients:
            logger.info(f"Session {session_id} already active")
            return self.active_clients[session_id]

        # Validate session can be resumed
        if session.status not in [SessionStatus.PAUSED, SessionStatus.WAITING]:
            raise ValueError(
                f"Session {session_id} cannot be resumed (status={session.status.value})"
            )

        # Create new client (same as create_session)
        client = await self.create_session(session_id, session.mode, session)

        # TODO: Restore context if requested
        # This depends on SDK support for session continuation
        # For now, we'll just create a fresh session
        if restore_context:
            logger.warning("Context restoration not yet implemented")

        return client

    async def fork_session(
        self,
        parent_session_id: UUID,
        fork_session_id: UUID,
        fork_session: Session,
        fork_at_message: Optional[int] = None,
    ) -> EnhancedClaudeClient:
        """Fork session from specific point in history.

        Args:
            parent_session_id: Parent session to fork from
            fork_session_id: New forked session ID
            fork_session: Domain Session entity for forked session
            fork_at_message: Optional message index to fork from

        Returns:
            EnhancedClaudeClient: New client with parent context

        Raises:
            ValueError: If parent session not found or cannot be forked
        """
        logger.info(
            f"Forking session: parent={parent_session_id}, fork={fork_session_id}, at_message={fork_at_message}",
            extra={"parent_session_id": str(parent_session_id), "fork_session_id": str(fork_session_id)},
        )

        # Retrieve parent session messages
        parent_messages = await self.message_repo.get_by_session(
            parent_session_id, limit=fork_at_message
        )

        logger.info(
            f"Retrieved {len(parent_messages)} messages from parent session",
            extra={"parent_session_id": str(parent_session_id)},
        )

        # Create new client for forked session
        client = await self.create_session(fork_session_id, SessionMode.FORKED, fork_session)

        # TODO: Restore parent context
        # This requires SDK support for conversation continuation
        # For now, we log the intent and create a fresh session
        logger.warning(
            f"Context restoration from parent not yet implemented ({len(parent_messages)} messages)"
        )

        return client

    async def archive_session(
        self,
        session_id: UUID,
        archive_to_storage: bool = True,
        storage_backend: str = "s3",
        compression: str = "tar.gz"
    ) -> Dict[str, Any]:
        """Archive session and cleanup resources.

        Args:
            session_id: Session to archive
            archive_to_storage: Whether to upload working directory to S3/storage
            storage_backend: Storage backend to use (s3, filesystem)
            compression: Compression type (tar.gz, zip)

        Returns:
            ArchiveResult: Archive metadata and status

        Raises:
            ValueError: If session not found or already archived
        """
        logger.info(
            f"Archiving session: {session_id} (archive_to_storage={archive_to_storage}, backend={storage_backend})",
            extra={"session_id": str(session_id)},
        )

        # Get session from database
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Disconnect client if active
        if session_id in self.active_clients:
            client = self.active_clients[session_id]
            metrics = await client.disconnect()

            # Remove from active clients
            del self.active_clients[session_id]

            logger.info(
                f"Session disconnected: {session_id}",
                extra={"session_id": str(session_id), "metrics": metrics.to_dict()},
            )

        # Archive working directory to storage
        storage_path = None
        archive_metadata = None

        if archive_to_storage and session.working_directory_path:
            try:
                logger.info(
                    f"Archiving working directory for session {session_id}",
                    extra={"session_id": str(session_id), "backend": storage_backend}
                )

                archive_metadata = await self.storage_archiver.archive_working_directory(
                    session_id=session_id,
                    working_directory=Path(session.working_directory_path),
                    storage_backend=storage_backend,
                    compression_type=compression
                )

                storage_path = archive_metadata.archive_path

                # Update session with archive_id
                await self.session_repo.update(
                    session_id,
                    archive_id=archive_metadata.id
                )
                await self.db.commit()

                logger.info(
                    f"Working directory archived: {storage_path}",
                    extra={"session_id": str(session_id), "archive_id": str(archive_metadata.id)}
                )

            except Exception as e:
                logger.error(
                    f"Failed to archive working directory for session {session_id}: {str(e)}",
                    extra={"session_id": str(session_id)},
                    exc_info=True
                )
                # Don't fail the entire archive operation if storage upload fails
                # The session metadata is still saved

        logger.info(
            f"Session archived successfully: {session_id}",
            extra={"session_id": str(session_id), "storage_path": storage_path},
        )

        return {
            "session_id": session_id,
            "archived": True,
            "storage_path": storage_path,
            "archive_metadata": archive_metadata.to_dict() if archive_metadata else None,
        }

    async def get_client(self, session_id: UUID) -> Optional[EnhancedClaudeClient]:
        """Get active client for session.

        Args:
            session_id: Session identifier

        Returns:
            EnhancedClaudeClient if active, None otherwise
        """
        return self.active_clients.get(session_id)

    async def disconnect_all(self) -> None:
        """Disconnect all active clients.

        Used for graceful shutdown or cleanup operations.
        """
        logger.info(f"Disconnecting all active sessions ({len(self.active_clients)})")

        for session_id, client in list(self.active_clients.items()):
            try:
                await client.disconnect()
                logger.info(f"Disconnected session: {session_id}")
            except Exception as e:
                logger.error(
                    f"Error disconnecting session {session_id}: {str(e)}",
                    extra={"session_id": str(session_id)},
                )

        self.active_clients.clear()
        logger.info("All sessions disconnected")

    def get_active_session_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.active_clients)

    def get_active_session_ids(self) -> list[UUID]:
        """Get list of active session IDs.

        Returns:
            List of active session UUIDs
        """
        return list(self.active_clients.keys())
