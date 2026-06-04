class AvanikoError(Exception):
    """Base exception for all Avaniko errors."""

class AuthError(AvanikoError):
    """Invalid or expired API key."""

class RateLimitError(AvanikoError):
    """Too many requests."""

class APIError(AvanikoError):
    """Server-side error."""

class ModelNotFoundError(AvanikoError):
    """Requested model does not exist."""
