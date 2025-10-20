"""Error handler for centralized error handling and recovery logic."""
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from claude_agent_sdk import CLIConnectionError, ClaudeSDKError

from app.repositories.session_repository import SessionRepository
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """Centralized error handling and recovery logic.

    This handler:
    - Determines if errors are retryable
    - Updates session state on errors
    - Logs errors to audit trail
    - Provides error classification and context

    Example:
        >>> handler = ErrorHandler(db, session_repo, audit_service)
        >>> await handler.handle_sdk_error(error, session_id, context)
        >>> is_retryable = handler.is_retryable(error)
    """

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        audit_service: AuditService,
    ):
        """Initialize error handler with repositories and services.

        Args:
            db: Async database session
            session_repo: Repository for session updates
            audit_service: Service for audit logging
        """
        self.db = db
        self.session_repo = session_repo
        self.audit_service = audit_service

    async def handle_sdk_error(
        self, error: Exception, session_id: UUID, context: Dict[str, Any]
    ) -> None:
        """Handle SDK errors and update session state.

        Args:
            error: Exception that occurred
            session_id: Session identifier
            context: Additional context about the error
        """
        error_type = type(error).__name__
        error_message = str(error)

        logger.error(
            f"Handling SDK error: {error_type} - {error_message}",
            extra={
                "session_id": str(session_id),
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
            },
        )

        # Update session status to failed
        from app.models.session import SessionModel
        from sqlalchemy import update

        update_stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                status="failed",
                error_message=error_message,
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(update_stmt)
        await self.db.flush()

        logger.info(
            f"Updated session status to failed",
            extra={"session_id": str(session_id)},
        )

        # Log error to audit trail
        await self.log_error(error, session_id, context)

    def is_retryable(self, error: Exception) -> bool:
        """Determine if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is transient and should be retried, False otherwise
        """
        error_type = type(error).__name__
        
        logger.debug(
            "Evaluating error retryability",
            extra={
                "error_type": error_type,
                "error_message": str(error)
            }
        )
        
        retryable = False
        
        # Connection errors are retryable (transient network issues)
        if isinstance(error, CLIConnectionError):
            retryable = True

        # Other SDK errors are not retryable (permanent failures)
        elif isinstance(error, ClaudeSDKError):
            retryable = False

        # Unknown errors are not retryable by default
        else:
            retryable = False
        
        logger.debug(
            "Error retryability determined",
            extra={
                "error_type": error_type,
                "retryable": retryable
            }
        )
        
        return retryable

    async def log_error(
        self, error: Exception, session_id: UUID, context: Dict[str, Any]
    ) -> None:
        """Log error to audit trail.

        Args:
            error: Exception that occurred
            session_id: Session identifier
            context: Additional error context
        """
        error_type = type(error).__name__
        error_message = str(error)

        logger.info(
            f"Logging error to audit trail: {error_type}",
            extra={"session_id": str(session_id)},
        )

        # Log to audit service
        await self.audit_service.log_event(
            event_type="sdk_error",
            event_category="system",
            session_id=session_id,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "is_retryable": self.is_retryable(error),
                "context": context,
            },
        )

        logger.info(
            f"Error logged to audit trail",
            extra={"session_id": str(session_id), "error_type": error_type},
        )

    def classify_error(self, error: Exception) -> Dict[str, Any]:
        """Classify error with details for reporting.

        Args:
            error: Exception to classify

        Returns:
            Dictionary with error classification details
        """
        error_type = type(error).__name__
        
        logger.debug(
            "Classifying error",
            extra={
                "error_type": error_type,
                "error_message": str(error)
            }
        )

        classification = {
            "type": error_type,
            "message": str(error),
            "is_retryable": self.is_retryable(error),
            "category": "unknown",
            "severity": "error",
        }

        if isinstance(error, CLIConnectionError):
            classification["category"] = "connection"
            classification["severity"] = "warning"
        elif isinstance(error, ClaudeSDKError):
            classification["category"] = "sdk"
            classification["severity"] = "error"
        
        logger.debug(
            "Error classification complete",
            extra={
                "error_type": error_type,
                "category": classification["category"],
                "severity": classification["severity"],
                "is_retryable": classification["is_retryable"]
            }
        )

        return classification
