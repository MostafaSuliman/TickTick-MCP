"""
Focus/Pomodoro models for TickTick API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FocusStatus(str, Enum):
    """Focus session status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    BREAK = "break"
    COMPLETED = "completed"


class FocusType(str, Enum):
    """Focus session types."""
    POMODORO = "pomo"  # Timed with breaks
    STOPWATCH = "stopwatch"  # Count up
    COUNTDOWN = "countdown"  # Custom duration countdown


class BreakType(str, Enum):
    """Break types between focus sessions."""
    SHORT = "short"
    LONG = "long"


class FocusSession(BaseModel):
    """Focus/Pomodoro session model."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: Optional[str] = Field(default=None, description="Session ID")

    # Session type and timing
    focus_type: FocusType = Field(default=FocusType.POMODORO, alias="focusType")
    duration: int = Field(default=1500, description="Duration in seconds (default 25 min)")

    # Status
    status: FocusStatus = Field(default=FocusStatus.IDLE)
    elapsed: int = Field(default=0, description="Elapsed time in seconds")
    remaining: int = Field(default=0, description="Remaining time in seconds")
    pause_count: int = Field(default=0, alias="pauseCount")

    # Associated task
    task_id: Optional[str] = Field(default=None, alias="taskId")
    project_id: Optional[str] = Field(default=None, alias="projectId")

    # Timestamps
    start_time: Optional[str] = Field(default=None, alias="startTime")
    end_time: Optional[str] = Field(default=None, alias="endTime")
    created_time: Optional[str] = Field(default=None, alias="createdTime")

    # Notes
    note: Optional[str] = Field(default=None)


class FocusSessionCreate(BaseModel):
    """Model for starting a new focus session."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    focus_type: FocusType = Field(default=FocusType.POMODORO)
    duration: Optional[int] = Field(
        default=None,
        ge=60,
        le=14400,  # Max 4 hours
        description="Duration in seconds (default from settings)"
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Task to focus on (optional)"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID if task_id is provided"
    )
    note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Session note"
    )


class FocusRecord(BaseModel):
    """Completed focus session record."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(..., description="Record ID")
    duration: int = Field(..., description="Actual focus time in seconds")
    focus_type: FocusType = Field(alias="focusType")

    # Associated task
    task_id: Optional[str] = Field(default=None, alias="taskId")
    task_title: Optional[str] = Field(default=None, alias="taskTitle")
    project_id: Optional[str] = Field(default=None, alias="projectId")

    # Timestamps
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")

    # Notes
    note: Optional[str] = Field(default=None)


class PomoSettings(BaseModel):
    """Pomodoro timer settings."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Duration settings (in minutes)
    pomo_duration: int = Field(default=25, alias="pomoDuration", ge=1, le=240)
    short_break: int = Field(default=5, alias="shortBreak", ge=1, le=60)
    long_break: int = Field(default=15, alias="longBreak", ge=1, le=120)
    long_break_interval: int = Field(
        default=4,
        alias="longBreakInterval",
        ge=1,
        le=10,
        description="Number of pomos before long break"
    )

    # Behavior settings
    auto_start_break: bool = Field(default=True, alias="autoStartBreak")
    auto_start_pomo: bool = Field(default=False, alias="autoStartPomo")
    max_pause_count: int = Field(default=3, alias="maxPauseCount", ge=1, le=10)

    # Sound settings
    sound_enabled: bool = Field(default=True, alias="soundEnabled")
    sound_type: Optional[str] = Field(default=None, alias="soundType")

    # Target settings
    daily_pomo_target: int = Field(default=8, alias="dailyPomoTarget", ge=1, le=50)


class FocusStats(BaseModel):
    """Focus/Pomodoro statistics."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Today's stats
    today_focus_time: int = Field(default=0, alias="todayFocusTime", description="Seconds")
    today_pomo_count: int = Field(default=0, alias="todayPomoCount")

    # Weekly stats
    week_focus_time: int = Field(default=0, alias="weekFocusTime")
    week_pomo_count: int = Field(default=0, alias="weekPomoCount")

    # Monthly stats
    month_focus_time: int = Field(default=0, alias="monthFocusTime")
    month_pomo_count: int = Field(default=0, alias="monthPomoCount")

    # All-time stats
    total_focus_time: int = Field(default=0, alias="totalFocusTime")
    total_pomo_count: int = Field(default=0, alias="totalPomoCount")

    # Streaks
    current_streak: int = Field(default=0, alias="currentStreak")
    best_streak: int = Field(default=0, alias="bestStreak")

    # Distribution
    daily_distribution: Optional[dict] = Field(
        default=None,
        alias="dailyDistribution",
        description="Focus time by hour of day"
    )
    project_distribution: Optional[dict] = Field(
        default=None,
        alias="projectDistribution",
        description="Focus time by project"
    )


class FocusFilter(BaseModel):
    """Filter for focus records."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    from_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    to_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    task_id: Optional[str] = Field(default=None)
    project_id: Optional[str] = Field(default=None)
    focus_type: Optional[FocusType] = Field(default=None)
    min_duration: Optional[int] = Field(default=None, description="Minimum duration in seconds")


# WebSocket event models
class FocusWebSocketEvent(BaseModel):
    """WebSocket event for focus timer."""
    model_config = ConfigDict(extra="allow")

    event: str = Field(..., description="Event type: start, pause, continue, startBreak, endBreak, exit")
    session_id: Optional[str] = Field(default=None, alias="sessionId")
    timestamp: Optional[str] = Field(default=None)
    data: Optional[dict] = Field(default=None)
