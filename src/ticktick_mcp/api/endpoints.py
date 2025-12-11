"""
TickTick API endpoint definitions for both v1 (Official) and v2 (Internal).
"""

from enum import Enum
from typing import Optional


class APIVersion(str, Enum):
    """TickTick API versions."""
    V1 = "v1"  # Official Open API
    V2 = "v2"  # Internal/Unofficial API


class Endpoints:
    """
    Centralized endpoint definitions for TickTick APIs.

    API v1 (Official): https://api.ticktick.com/open/v1/
    API v2 (Internal): https://api.ticktick.com/api/v2/
    """

    # Base URLs
    BASE_V1 = "https://api.ticktick.com/open/v1"
    BASE_V2 = "https://api.ticktick.com/api/v2"

    # OAuth URLs
    OAUTH_AUTHORIZE = "https://ticktick.com/oauth/authorize"
    OAUTH_TOKEN = "https://ticktick.com/oauth/token"

    # WebSocket
    WEBSOCKET_URL = "wss://api.ticktick.com/ws"

    # =========================================================================
    # Authentication Endpoints
    # =========================================================================

    class Auth:
        """Authentication endpoints."""

        # v2 only - username/password login
        SIGNIN = "/user/signin"

        # v2 - user settings
        USER_SETTINGS = "/user/preferences/settings"

        @classmethod
        def signin(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.SIGNIN}"

        @classmethod
        def user_settings(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.USER_SETTINGS}"

    # =========================================================================
    # Sync Endpoints
    # =========================================================================

    class Sync:
        """Synchronization endpoints (v2)."""

        # Initial batch sync - returns all data
        BATCH_CHECK = "/batch/check/{checkpoint}"

        @classmethod
        def batch_check(cls, checkpoint: int = 0) -> str:
            return f"{Endpoints.BASE_V2}{cls.BATCH_CHECK.format(checkpoint=checkpoint)}"

    # =========================================================================
    # Task Endpoints
    # =========================================================================

    class Tasks:
        """Task management endpoints."""

        # v1 endpoints
        V1_TASK = "/task"
        V1_TASK_BY_ID = "/task/{task_id}"
        V1_PROJECT_TASK = "/project/{project_id}/task/{task_id}"
        V1_COMPLETE = "/project/{project_id}/task/{task_id}/complete"
        V1_BATCH = "/batch/task"

        # v2 endpoints
        V2_BATCH_TASK = "/batch/task"
        V2_BATCH_PARENT = "/batch/taskParent"
        V2_BATCH_PROJECT = "/batch/taskProject"
        V2_COMPLETED = "/project/all/completed"
        V2_PROJECT_COMPLETED = "/project/{project_id}/completed"

        # v1 methods
        @classmethod
        def create_v1(cls) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_TASK}"

        @classmethod
        def update_v1(cls, task_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_TASK_BY_ID.format(task_id=task_id)}"

        @classmethod
        def get_v1(cls, project_id: str, task_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT_TASK.format(project_id=project_id, task_id=task_id)}"

        @classmethod
        def complete_v1(cls, project_id: str, task_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_COMPLETE.format(project_id=project_id, task_id=task_id)}"

        @classmethod
        def delete_v1(cls, project_id: str, task_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT_TASK.format(project_id=project_id, task_id=task_id)}"

        @classmethod
        def batch_v1(cls) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_BATCH}"

        # v2 methods
        @classmethod
        def batch_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_TASK}"

        @classmethod
        def batch_parent_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_PARENT}"

        @classmethod
        def batch_move_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_PROJECT}"

        @classmethod
        def completed_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_COMPLETED}"

        @classmethod
        def project_completed_v2(cls, project_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_PROJECT_COMPLETED.format(project_id=project_id)}"

    # =========================================================================
    # Project Endpoints
    # =========================================================================

    class Projects:
        """Project/list management endpoints."""

        # v1 endpoints
        V1_PROJECT = "/project"
        V1_PROJECT_BY_ID = "/project/{project_id}"
        V1_PROJECT_DATA = "/project/{project_id}/data"

        # v2 endpoints
        V2_PROJECTS = "/projects"
        V2_BATCH_PROJECT = "/batch/project"
        V2_BATCH_FOLDER = "/batch/projectGroup"

        # v1 methods
        @classmethod
        def list_v1(cls) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT}"

        @classmethod
        def create_v1(cls) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT}"

        @classmethod
        def get_v1(cls, project_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT_BY_ID.format(project_id=project_id)}"

        @classmethod
        def delete_v1(cls, project_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT_BY_ID.format(project_id=project_id)}"

        @classmethod
        def data_v1(cls, project_id: str) -> str:
            return f"{Endpoints.BASE_V1}{cls.V1_PROJECT_DATA.format(project_id=project_id)}"

        # v2 methods
        @classmethod
        def list_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_PROJECTS}"

        @classmethod
        def batch_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_PROJECT}"

        @classmethod
        def batch_folder_v2(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_FOLDER}"

    # =========================================================================
    # Tag Endpoints (v2 only)
    # =========================================================================

    class Tags:
        """Tag management endpoints (v2 only)."""

        V2_BATCH_TAG = "/batch/tag"
        V2_TAG_RENAME = "/tag/rename"
        V2_TAG_MERGE = "/tag/merge"
        V2_TAG = "/tag"

        @classmethod
        def batch(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_TAG}"

        @classmethod
        def rename(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_TAG_RENAME}"

        @classmethod
        def merge(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_TAG_MERGE}"

        @classmethod
        def delete(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_TAG}"

    # =========================================================================
    # Habit Endpoints (v2 only)
    # =========================================================================

    class Habits:
        """Habit management endpoints (v2 only)."""

        V2_HABITS = "/habits"
        V2_HABIT = "/habit"
        V2_HABIT_BY_ID = "/habit/{habit_id}"
        V2_HABIT_CHECKIN = "/habit/{habit_id}/checkin"
        V2_HABIT_RECORDS = "/habit/{habit_id}/records"
        V2_BATCH_HABIT = "/batch/habit"

        @classmethod
        def list(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABITS}"

        @classmethod
        def create(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT}"

        @classmethod
        def get(cls, habit_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_BY_ID.format(habit_id=habit_id)}"

        @classmethod
        def update(cls, habit_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_BY_ID.format(habit_id=habit_id)}"

        @classmethod
        def delete(cls, habit_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_BY_ID.format(habit_id=habit_id)}"

        @classmethod
        def checkin(cls, habit_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_CHECKIN.format(habit_id=habit_id)}"

        @classmethod
        def records(cls, habit_id: str) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_RECORDS.format(habit_id=habit_id)}"

        @classmethod
        def batch(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_BATCH_HABIT}"

    # =========================================================================
    # Focus/Pomodoro Endpoints (v2 only)
    # =========================================================================

    class Focus:
        """Focus/Pomodoro endpoints (v2 only)."""

        V2_FOCUS = "/focus"
        V2_FOCUS_RECORDS = "/focus/records"
        V2_FOCUS_SAVE = "/focus/save"
        V2_POMO_STATUS = "/pomodoro/status"
        V2_POMO_SETTINGS = "/pomodoro/settings"

        @classmethod
        def records(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_FOCUS_RECORDS}"

        @classmethod
        def save(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_FOCUS_SAVE}"

        @classmethod
        def status(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_POMO_STATUS}"

        @classmethod
        def settings(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_POMO_SETTINGS}"

    # =========================================================================
    # Statistics Endpoints (v2 only)
    # =========================================================================

    class Statistics:
        """Statistics and analytics endpoints (v2 only)."""

        V2_GENERAL = "/statistics/general"
        V2_FOCUS_STATS = "/statistics/focus"
        V2_HABIT_STATS = "/statistics/habit"
        V2_TASK_STATS = "/statistics/task"

        @classmethod
        def general(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_GENERAL}"

        @classmethod
        def focus(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_FOCUS_STATS}"

        @classmethod
        def habit(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_HABIT_STATS}"

        @classmethod
        def task(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_TASK_STATS}"

    # =========================================================================
    # Calendar Endpoints
    # =========================================================================

    class Calendar:
        """Calendar integration endpoints."""

        V2_CALENDAR_EVENTS = "/calendar/events"
        V2_CALENDARS = "/calendars"

        @classmethod
        def events(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_CALENDAR_EVENTS}"

        @classmethod
        def calendars(cls) -> str:
            return f"{Endpoints.BASE_V2}{cls.V2_CALENDARS}"

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @classmethod
    def get_base_url(cls, version: APIVersion) -> str:
        """Get base URL for specified API version."""
        return cls.BASE_V1 if version == APIVersion.V1 else cls.BASE_V2

    @classmethod
    def build_url(cls, version: APIVersion, path: str) -> str:
        """Build full URL for given version and path."""
        base = cls.get_base_url(version)
        return f"{base}{path}"
