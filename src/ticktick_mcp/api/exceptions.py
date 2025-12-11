"""
Custom exceptions for TickTick API operations.
"""

from typing import Any, Optional


class TickTickAPIError(Exception):
    """Base exception for TickTick API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
        endpoint: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.endpoint = endpoint
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.endpoint:
            parts.append(f"at {self.endpoint}")
        return " ".join(parts)


class AuthenticationError(TickTickAPIError):
    """Raised when authentication fails or token is invalid/expired."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: Optional[int] = 401,
        **kwargs,
    ):
        super().__init__(message, status_code, **kwargs)


class AuthorizationError(TickTickAPIError):
    """Raised when user lacks permission for an operation."""

    def __init__(
        self,
        message: str = "Not authorized for this operation",
        status_code: Optional[int] = 403,
        **kwargs,
    ):
        super().__init__(message, status_code, **kwargs)


class RateLimitError(TickTickAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before making more requests.",
        status_code: Optional[int] = 429,
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code, **kwargs)


class NotFoundError(TickTickAPIError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status_code: Optional[int] = 404,
        **kwargs,
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_type and resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, status_code, **kwargs)


class ValidationError(TickTickAPIError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Request validation failed",
        field: Optional[str] = None,
        status_code: Optional[int] = 400,
        **kwargs,
    ):
        self.field = field
        if field:
            message = f"Validation error on field '{field}': {message}"
        super().__init__(message, status_code, **kwargs)


class ServerError(TickTickAPIError):
    """Raised when TickTick server returns an internal error."""

    def __init__(
        self,
        message: str = "TickTick server error",
        status_code: Optional[int] = 500,
        **kwargs,
    ):
        super().__init__(message, status_code, **kwargs)


class NetworkError(TickTickAPIError):
    """Raised when network communication fails."""

    def __init__(
        self,
        message: str = "Network error communicating with TickTick",
        **kwargs,
    ):
        super().__init__(message, **kwargs)


class ConfigurationError(TickTickAPIError):
    """Raised when client configuration is invalid."""

    def __init__(
        self,
        message: str = "Invalid client configuration",
        **kwargs,
    ):
        super().__init__(message, **kwargs)


class WebSocketError(TickTickAPIError):
    """Raised when WebSocket connection fails."""

    def __init__(
        self,
        message: str = "WebSocket connection error",
        **kwargs,
    ):
        super().__init__(message, **kwargs)


class SyncError(TickTickAPIError):
    """Raised when data synchronization fails."""

    def __init__(
        self,
        message: str = "Synchronization error",
        **kwargs,
    ):
        super().__init__(message, **kwargs)


def raise_for_status(status_code: int, response_body: Any, endpoint: str) -> None:
    """Raise appropriate exception based on HTTP status code."""
    if status_code < 400:
        return

    # Extract error message from response
    error_message = "Unknown error"
    if isinstance(response_body, dict):
        error_message = response_body.get("error", response_body.get("message", str(response_body)))
    elif isinstance(response_body, str):
        error_message = response_body

    if status_code == 400:
        raise ValidationError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    elif status_code == 401:
        raise AuthenticationError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    elif status_code == 403:
        raise AuthorizationError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    elif status_code == 404:
        raise NotFoundError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    elif status_code == 429:
        raise RateLimitError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    elif status_code >= 500:
        raise ServerError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
    else:
        raise TickTickAPIError(error_message, status_code=status_code, response_body=response_body, endpoint=endpoint)
