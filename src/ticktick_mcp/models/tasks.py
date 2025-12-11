"""
Task models for TickTick API.
"""

from datetime import datetime
from enum import IntEnum, Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskPriority(IntEnum):
    """Task priority levels in TickTick."""
    NONE = 0
    LOW = 1
    MEDIUM = 3
    HIGH = 5

    @classmethod
    def from_string(cls, value: str) -> "TaskPriority":
        """Convert string to priority."""
        mapping = {
            "none": cls.NONE,
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
        }
        return mapping.get(value.lower(), cls.NONE)

    def to_emoji(self) -> str:
        """Convert priority to emoji representation."""
        mapping = {
            self.NONE: "",
            self.LOW: "",
            self.MEDIUM: "",
            self.HIGH: "",
        }
        return mapping.get(self, "")


class TaskStatus(IntEnum):
    """Task status values."""
    INCOMPLETE = 0
    COMPLETE = 2

    def to_emoji(self) -> str:
        """Convert status to emoji."""
        return "" if self == self.COMPLETE else ""


class TaskKind(str, Enum):
    """Task type classification."""
    TASK = "TASK"
    NOTE = "NOTE"
    CHECKLIST = "CHECKLIST"


class ReminderType(str, Enum):
    """Reminder trigger types."""
    TRIGGER = "TRIGGER"  # Relative to due date
    ABSOLUTE = "ABSOLUTE"  # Specific time


class Reminder(BaseModel):
    """Task reminder configuration."""
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = Field(default=None)
    trigger: Optional[str] = Field(
        default=None,
        description="Reminder trigger (e.g., 'TRIGGER:P0DT9H0M0S' for 9 hours before)"
    )


class ChecklistItem(BaseModel):
    """Subtask/checklist item within a task."""
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = Field(default=None)
    title: str = Field(..., description="Checklist item title", min_length=1)
    status: TaskStatus = Field(default=TaskStatus.INCOMPLETE)
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    start_date: Optional[str] = Field(default=None, alias="startDate")
    is_all_day: Optional[bool] = Field(default=None, alias="isAllDay")
    time_zone: Optional[str] = Field(default=None, alias="timeZone")
    completed_time: Optional[str] = Field(default=None, alias="completedTime")


class RepeatConfig(BaseModel):
    """Recurring task configuration."""
    model_config = ConfigDict(extra="allow")

    # RRULE format string (RFC 5545)
    rrule: Optional[str] = Field(
        default=None,
        description="iCal RRULE string (e.g., 'RRULE:FREQ=DAILY;INTERVAL=1')"
    )
    # Simplified repeat patterns
    frequency: Optional[str] = Field(
        default=None,
        description="Simple frequency: daily, weekly, monthly, yearly"
    )
    interval: int = Field(default=1, ge=1, description="Repeat interval")
    end_date: Optional[str] = Field(default=None, description="When repetition ends")
    count: Optional[int] = Field(default=None, description="Number of occurrences")


class Task(BaseModel):
    """Complete task model from TickTick API."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Core identifiers
    id: str = Field(..., description="Unique task ID")
    project_id: str = Field(..., alias="projectId", description="Parent project/list ID")

    # Content
    title: str = Field(..., description="Task title")
    content: Optional[str] = Field(default=None, description="Task description/notes")
    desc: Optional[str] = Field(default=None, description="Additional description")

    # Status
    status: TaskStatus = Field(default=TaskStatus.INCOMPLETE)
    priority: TaskPriority = Field(default=TaskPriority.NONE)

    # Dates
    start_date: Optional[str] = Field(default=None, alias="startDate")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    completed_time: Optional[str] = Field(default=None, alias="completedTime")
    created_time: Optional[str] = Field(default=None, alias="createdTime")
    modified_time: Optional[str] = Field(default=None, alias="modifiedTime")

    # Time settings
    is_all_day: bool = Field(default=True, alias="isAllDay")
    time_zone: Optional[str] = Field(default=None, alias="timeZone")

    # Organization
    tags: Optional[list[str]] = Field(default=None)
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")

    # Subtasks/checklist
    items: Optional[list[ChecklistItem]] = Field(default=None, description="Checklist items")

    # Reminders
    reminders: Optional[list[Reminder]] = Field(default=None)

    # Recurrence
    repeat_flag: Optional[str] = Field(default=None, alias="repeatFlag")
    repeat_from: Optional[int] = Field(default=None, alias="repeatFrom")
    repeat_first_date: Optional[str] = Field(default=None, alias="repeatFirstDate")

    # Hierarchy
    parent_id: Optional[str] = Field(default=None, alias="parentId")
    child_ids: Optional[list[str]] = Field(default=None, alias="childIds")

    # Metadata
    etag: Optional[str] = Field(default=None)
    kind: Optional[TaskKind] = Field(default=None)

    # Pomodoro tracking
    focus_summaries: Optional[list[dict]] = Field(default=None, alias="focusSummaries")
    pomo_done: Optional[int] = Field(default=None, alias="pomoDone")
    pomo_estimated: Optional[int] = Field(default=None, alias="pomoEstimated")

    # Progress (for tasks with subtasks)
    progress: Optional[int] = Field(default=None, ge=0, le=100)


class TaskCreate(BaseModel):
    """Model for creating a new task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", populate_by_name=True)

    title: str = Field(..., description="Task title", min_length=1, max_length=500)
    content: Optional[str] = Field(default=None, description="Task description", max_length=5000)
    project_id: Optional[str] = Field(
        default=None,
        alias="projectId",
        description="Project/list ID (empty for inbox)"
    )

    # Dates
    start_date: Optional[str] = Field(
        default=None,
        alias="startDate",
        description="Start date in ISO format"
    )
    due_date: Optional[str] = Field(
        default=None,
        alias="dueDate",
        description="Due date in ISO format"
    )
    is_all_day: bool = Field(default=True, alias="isAllDay")
    time_zone: Optional[str] = Field(default=None, alias="timeZone")

    # Priority and tags
    priority: TaskPriority = Field(default=TaskPriority.NONE)
    tags: Optional[list[str]] = Field(default=None, max_length=20)

    # Checklist items
    items: Optional[list[ChecklistItem]] = Field(default=None)

    # Reminders
    reminders: Optional[list[Reminder]] = Field(default=None)

    # Recurrence
    repeat_flag: Optional[str] = Field(default=None, alias="repeatFlag")

    # Parent task (for subtasks)
    parent_id: Optional[str] = Field(default=None, alias="parentId")

    # Pomodoro estimation
    pomo_estimated: Optional[int] = Field(default=None, alias="pomoEstimated", ge=0)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tag names."""
        if v is None:
            return v
        # Tags cannot contain certain special characters without escaping
        for tag in v:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 character limit")
        return v


class TaskUpdate(BaseModel):
    """Model for updating an existing task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", populate_by_name=True)

    # Required identifiers
    id: str = Field(..., description="Task ID to update")
    project_id: str = Field(..., alias="projectId", description="Project ID containing the task")

    # Updatable fields (all optional)
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = Field(default=None, max_length=5000)
    start_date: Optional[str] = Field(default=None, alias="startDate")
    due_date: Optional[str] = Field(default=None, alias="dueDate")
    is_all_day: Optional[bool] = Field(default=None, alias="isAllDay")
    time_zone: Optional[str] = Field(default=None, alias="timeZone")
    priority: Optional[TaskPriority] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    items: Optional[list[ChecklistItem]] = Field(default=None)
    reminders: Optional[list[Reminder]] = Field(default=None)
    repeat_flag: Optional[str] = Field(default=None, alias="repeatFlag")
    pomo_estimated: Optional[int] = Field(default=None, alias="pomoEstimated", ge=0)
    progress: Optional[int] = Field(default=None, ge=0, le=100)


class TaskMove(BaseModel):
    """Model for moving a task between projects."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task_id: str = Field(..., description="Task ID to move")
    from_project_id: str = Field(..., description="Source project ID")
    to_project_id: str = Field(..., description="Destination project ID")


class TaskComplete(BaseModel):
    """Model for completing a task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task_id: str = Field(..., description="Task ID to complete")
    project_id: str = Field(..., description="Project ID containing the task")


class TaskDelete(BaseModel):
    """Model for deleting a task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task_id: str = Field(..., description="Task ID to delete")
    project_id: str = Field(..., description="Project ID containing the task")


class TaskFilter(BaseModel):
    """Filter parameters for listing tasks."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    project_id: Optional[str] = Field(default=None, description="Filter by project")
    status: Optional[TaskStatus] = Field(default=None, description="Filter by status")
    priority: Optional[TaskPriority] = Field(default=None, description="Filter by priority")
    tags: Optional[list[str]] = Field(default=None, description="Filter by tags")
    due_before: Optional[str] = Field(default=None, description="Due before date (ISO)")
    due_after: Optional[str] = Field(default=None, description="Due after date (ISO)")
    search_query: Optional[str] = Field(default=None, description="Search in title/content")
    include_completed: bool = Field(default=False, description="Include completed tasks")
