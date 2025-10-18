"""Domain layer exceptions."""


class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class ValidationError(DomainException):
    """Raised when domain validation fails."""
    pass


class InvalidStateTransitionError(DomainException):
    """Raised when invalid state transition is attempted."""
    pass


class SessionNotFoundError(DomainException):
    """Raised when session is not found."""
    pass


class SessionNotActiveError(DomainException):
    """Raised when operation requires active session."""
    pass


class SessionCannotResumeError(DomainException):
    """Raised when session cannot be resumed."""
    pass


class TaskNotFoundError(DomainException):
    """Raised when task is not found."""
    pass


class ReportNotFoundError(DomainException):
    """Raised when report is not found."""
    pass


class TemplateNotFoundError(DomainException):
    """Raised when template is not found."""
    pass


class UserNotFoundError(DomainException):
    """Raised when user is not found."""
    pass


class PermissionDeniedError(DomainException):
    """Raised when user lacks permission for operation."""
    pass


class QuotaExceededError(DomainException):
    """Raised when user quota is exceeded."""
    pass


class ResourceNotFoundError(DomainException):
    """Raised when a generic resource is not found."""
    pass


class InvalidOperationError(DomainException):
    """Raised when operation is invalid in current context."""
    pass


class ConcurrencyError(DomainException):
    """Raised when concurrent modification conflict occurs."""
    pass
