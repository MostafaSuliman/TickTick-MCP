"""
TickTick MCP Models - Pydantic models for type-safe API interactions.
"""

from .tasks import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskPriority,
    TaskStatus,
    ChecklistItem,
    Reminder,
    RepeatConfig,
)
from .projects import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectKind,
    ProjectViewMode,
    Folder,
    FolderCreate,
)
from .tags import Tag, TagCreate, TagUpdate, TagMerge
from .habits import Habit, HabitCreate, HabitCheckIn, HabitFrequency
from .focus import (
    FocusSession,
    FocusSessionCreate,
    FocusStatus,
    PomoSettings,
)
from .auth import (
    OAuthCredentials,
    OAuthToken,
    UserCredentials,
    AuthConfig,
)
from .common import (
    ResponseFormat,
    PaginationParams,
    DateRange,
    BatchOperation,
    APIResponse,
)

__all__ = [
    # Tasks
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskPriority",
    "TaskStatus",
    "ChecklistItem",
    "Reminder",
    "RepeatConfig",
    # Projects
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectKind",
    "ProjectViewMode",
    "Folder",
    "FolderCreate",
    # Tags
    "Tag",
    "TagCreate",
    "TagUpdate",
    "TagMerge",
    # Habits
    "Habit",
    "HabitCreate",
    "HabitCheckIn",
    "HabitFrequency",
    # Focus
    "FocusSession",
    "FocusSessionCreate",
    "FocusStatus",
    "PomoSettings",
    # Auth
    "OAuthCredentials",
    "OAuthToken",
    "UserCredentials",
    "AuthConfig",
    # Common
    "ResponseFormat",
    "PaginationParams",
    "DateRange",
    "BatchOperation",
    "APIResponse",
]
