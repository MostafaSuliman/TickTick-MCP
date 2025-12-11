"""
Common models shared across all TickTick MCP components.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"
    COMPACT = "compact"


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(default=100, ge=1, le=500, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class DateRange(BaseModel):
    """Date range filter for queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    from_date: Optional[str] = Field(
        default=None,
        description="Start date in ISO format (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date in ISO format (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )


class BatchOperationType(str, Enum):
    """Types of batch operations."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


T = TypeVar("T")


class BatchOperation(BaseModel, Generic[T]):
    """Generic batch operation container."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    add: Optional[List[T]] = Field(default=None, description="Items to add")
    update: Optional[List[T]] = Field(default=None, description="Items to update")
    delete: Optional[List[str]] = Field(default=None, description="Item IDs to delete")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    model_config = ConfigDict(extra="allow")

    success: bool = Field(default=True)
    data: Optional[T] = Field(default=None)
    error: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)


class SortOrder(str, Enum):
    """Sort order for list queries."""
    ASC = "asc"
    DESC = "desc"


class TimeZoneInfo(BaseModel):
    """Timezone information."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    timezone: str = Field(
        default="UTC",
        description="IANA timezone identifier (e.g., 'America/New_York', 'Europe/London')"
    )


class Color(BaseModel):
    """Color specification for UI elements."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    hex_color: Optional[str] = Field(
        default=None,
        description="Hex color code (e.g., '#FF5733')",
        pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    preset: Optional[str] = Field(
        default=None,
        description="Preset color name or 'random'"
    )

    def to_api_value(self) -> Optional[str]:
        """Convert to API-compatible value."""
        if self.preset == "random":
            return "random"
        return self.hex_color or self.preset


class Etag(BaseModel):
    """Entity tag for optimistic concurrency control."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    value: str = Field(..., description="ETag value from server")


class SyncState(BaseModel):
    """Synchronization state tracking."""
    model_config = ConfigDict(extra="allow")

    last_sync: Optional[datetime] = Field(default=None)
    checkpoint: Optional[int] = Field(default=0)
    inbox_id: Optional[str] = Field(default=None)


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    model_config = ConfigDict(extra="forbid")

    remaining: int = Field(default=100)
    reset_at: Optional[datetime] = Field(default=None)
    limit: int = Field(default=100)
