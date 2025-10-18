"""Custom exceptions for CLI."""


class CLIError(Exception):
    """Base exception for CLI errors."""
    pass


class APIError(CLIError):
    """API request error."""
    pass


class AuthenticationError(CLIError):
    """Authentication error."""
    pass


class NotFoundError(CLIError):
    """Resource not found error."""
    pass


class ValidationError(CLIError):
    """Validation error."""
    pass


class ConfigError(CLIError):
    """Configuration error."""
    pass
