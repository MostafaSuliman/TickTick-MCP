"""
TickTick API Client Layer - Dual API (v1/v2) Support.
"""

from .client import TickTickClient
from .endpoints import APIVersion, Endpoints
from .exceptions import (
    TickTickAPIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
)

__all__ = [
    "TickTickClient",
    "APIVersion",
    "Endpoints",
    "TickTickAPIError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]
