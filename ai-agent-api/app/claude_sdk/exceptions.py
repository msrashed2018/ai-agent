"""Claude SDK exceptions."""


class SDKError(Exception):
    """Base exception for Claude SDK errors."""

    pass


class ClientAlreadyExistsError(SDKError):
    """Raised when attempting to create a client that already exists."""

    pass


class ClientNotFoundError(SDKError):
    """Raised when client is not found in the manager."""

    pass


class SDKConnectionError(SDKError):
    """Raised when SDK connection fails."""

    pass


class SDKRuntimeError(SDKError):
    """Raised when SDK runtime error occurs."""

    pass


class PermissionDeniedError(SDKError):
    """Raised when tool permission is denied."""

    pass
