"""
Project and Folder models for TickTick API.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectKind(str, Enum):
    """Project type classification."""
    TASK = "TASK"
    NOTE = "NOTE"


class ProjectViewMode(str, Enum):
    """Project view modes."""
    LIST = "list"
    KANBAN = "kanban"
    TIMELINE = "timeline"


class ProjectPermission(str, Enum):
    """Project sharing permission levels."""
    READ = "read"
    WRITE = "write"
    COMMENT = "comment"


class Project(BaseModel):
    """Complete project/list model from TickTick API."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(..., description="Unique project ID")
    name: str = Field(..., description="Project name")

    # Appearance
    color: Optional[str] = Field(default=None, description="Project color (hex)")

    # Organization
    group_id: Optional[str] = Field(default=None, alias="groupId", description="Parent folder ID")
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    sort_type: Optional[str] = Field(default=None, alias="sortType")

    # Type and view
    kind: ProjectKind = Field(default=ProjectKind.TASK)
    view_mode: Optional[ProjectViewMode] = Field(default=None, alias="viewMode")
    is_owner: Optional[bool] = Field(default=None, alias="isOwner")

    # Status
    closed: Optional[bool] = Field(default=False, description="Whether project is archived")
    in_all: Optional[bool] = Field(default=True, alias="inAll")

    # Metadata
    etag: Optional[str] = Field(default=None)
    modified_time: Optional[str] = Field(default=None, alias="modifiedTime")

    # Sharing
    team_id: Optional[str] = Field(default=None, alias="teamId")
    permission: Optional[ProjectPermission] = Field(default=None)


class ProjectCreate(BaseModel):
    """Model for creating a new project/list."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    color: Optional[str] = Field(
        default=None,
        description="Project color (hex code like '#FF5733' or 'random')"
    )
    kind: ProjectKind = Field(default=ProjectKind.TASK, description="Project type")
    folder_id: Optional[str] = Field(
        default=None,
        description="Parent folder ID"
    )
    view_mode: Optional[ProjectViewMode] = Field(
        default=None,
        description="Default view mode"
    )


class ProjectUpdate(BaseModel):
    """Model for updating an existing project."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(..., description="Project ID to update")
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None)
    folder_id: Optional[str] = Field(default=None)
    view_mode: Optional[ProjectViewMode] = Field(default=None)
    sort_order: Optional[int] = Field(default=None)


class ProjectArchive(BaseModel):
    """Model for archiving/unarchiving a project."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    project_id: str = Field(..., description="Project ID")
    archive: bool = Field(default=True, description="True to archive, False to unarchive")


class Folder(BaseModel):
    """Project folder/group model."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(..., description="Unique folder ID")
    name: str = Field(..., description="Folder name")
    etag: Optional[str] = Field(default=None)
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    show_all: Optional[bool] = Field(default=None, alias="showAll")
    list_type: str = Field(default="group", alias="listType")


class FolderCreate(BaseModel):
    """Model for creating a new folder."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Folder name", min_length=1, max_length=100)


class FolderUpdate(BaseModel):
    """Model for updating a folder."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(..., description="Folder ID to update")
    name: Optional[str] = Field(default=None, max_length=100)
    sort_order: Optional[int] = Field(default=None)


class ProjectWithTasks(BaseModel):
    """Project data including its tasks."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    project: Project
    tasks: list = Field(default_factory=list, description="Tasks in this project")
    columns: Optional[list] = Field(default=None, description="Kanban columns if applicable")
