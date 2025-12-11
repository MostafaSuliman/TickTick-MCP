"""
Base service class for TickTick operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion

T = TypeVar("T")
logger = logging.getLogger(__name__)


class BaseService(ABC, Generic[T]):
    """
    Abstract base class for all TickTick services.

    Provides common functionality for API interactions, caching, and response formatting.
    """

    def __init__(self, client: TickTickClient):
        """
        Initialize service with API client.

        Args:
            client: Configured TickTickClient instance
        """
        self.client = client
        self._cache: Dict[str, Any] = {}

    @property
    def is_v2_available(self) -> bool:
        """Check if v2 API is available."""
        return self.client._session_token is not None

    @property
    def preferred_version(self) -> APIVersion:
        """Get preferred API version."""
        if self.is_v2_available and self.client.prefer_v2:
            return APIVersion.V2
        return APIVersion.V1

    def clear_cache(self) -> None:
        """Clear service cache."""
        self._cache.clear()

    def _cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        return ":".join(str(a) for a in args)

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)

    def _set_cached(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value

    def _format_response(
        self,
        data: Any,
        format_type: str = "markdown",
        title: Optional[str] = None,
    ) -> str:
        """
        Format response data for output.

        Args:
            data: Data to format
            format_type: Output format (markdown, json, compact)
            title: Optional title for the output

        Returns:
            Formatted string
        """
        import json

        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type == "compact":
            return json.dumps(data, separators=(",", ":"), default=str)
        else:
            # Default markdown formatting - subclasses should override
            if title:
                return f"## {title}\n\n```json\n{json.dumps(data, indent=2, default=str)}\n```"
            return f"```json\n{json.dumps(data, indent=2, default=str)}\n```"

    def _handle_error(self, error: Exception, operation: str) -> str:
        """
        Format error message.

        Args:
            error: Exception that occurred
            operation: Description of the operation that failed

        Returns:
            Formatted error message
        """
        logger.error(f"Error during {operation}: {error}")
        return f" **Error {operation}**: {str(error)}"


class CRUDService(BaseService[T]):
    """
    Extended base class for services with standard CRUD operations.
    """

    @abstractmethod
    async def list(self, **filters) -> List[T]:
        """List all items with optional filtering."""
        pass

    @abstractmethod
    async def get(self, item_id: str) -> Optional[T]:
        """Get a single item by ID."""
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new item."""
        pass

    @abstractmethod
    async def update(self, item_id: str, data: Dict[str, Any]) -> T:
        """Update an existing item."""
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item."""
        pass
