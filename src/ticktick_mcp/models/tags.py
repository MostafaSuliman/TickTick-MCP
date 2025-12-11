"""
Tag models for TickTick API (v2 only).
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Tag(BaseModel):
    """Tag model from TickTick API."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(..., description="Tag name (unique identifier)")
    label: Optional[str] = Field(default=None, description="Display label")
    color: Optional[str] = Field(default=None, description="Tag color (hex)")
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    sort_type: Optional[str] = Field(default=None, alias="sortType")
    etag: Optional[str] = Field(default=None)
    parent: Optional[str] = Field(default=None, description="Parent tag name for nested tags")


class TagCreate(BaseModel):
    """Model for creating a new tag."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ...,
        description="Tag name (will be used as identifier)",
        min_length=1,
        max_length=50
    )
    label: Optional[str] = Field(
        default=None,
        description="Display label (defaults to name)",
        max_length=50
    )
    color: Optional[str] = Field(
        default=None,
        description="Tag color in hex format (e.g., '#FF5733')"
    )
    parent: Optional[str] = Field(
        default=None,
        description="Parent tag name for creating nested tags"
    )


class TagUpdate(BaseModel):
    """Model for updating an existing tag."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Current tag name (identifier)")
    label: Optional[str] = Field(default=None, description="New display label")
    color: Optional[str] = Field(default=None, description="New color")
    sort_order: Optional[int] = Field(default=None)
    parent: Optional[str] = Field(default=None, description="New parent tag")


class TagRename(BaseModel):
    """Model for renaming a tag."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Current tag name")
    new_name: str = Field(..., description="New tag name", min_length=1, max_length=50)


class TagMerge(BaseModel):
    """Model for merging multiple tags into one."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_tags: list[str] = Field(
        ...,
        description="Tags to merge (will be deleted)",
        min_length=1
    )
    target_tag: str = Field(
        ...,
        description="Target tag (will receive all tasks from source tags)"
    )


class TagDelete(BaseModel):
    """Model for deleting a tag."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Tag name to delete")


class TagFilter(BaseModel):
    """Filter for listing/searching tags."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    search: Optional[str] = Field(default=None, description="Search in tag names")
    parent: Optional[str] = Field(default=None, description="Filter by parent tag")
    include_nested: bool = Field(default=True, description="Include nested tags")
