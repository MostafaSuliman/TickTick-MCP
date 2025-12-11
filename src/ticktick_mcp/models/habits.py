"""
Habit models for TickTick API (v2 only).
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HabitFrequency(str, Enum):
    """Habit frequency types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class HabitGoalType(str, Enum):
    """Habit goal measurement types."""
    COUNT = "count"  # e.g., 8 glasses of water
    DURATION = "duration"  # e.g., 30 minutes meditation
    BOOLEAN = "boolean"  # Simple check/uncheck


class HabitStatus(str, Enum):
    """Habit status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Habit(BaseModel):
    """Habit model from TickTick API."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(..., description="Unique habit ID")
    name: str = Field(..., description="Habit name")

    # Goal configuration
    goal: Optional[int] = Field(default=1, description="Target value per period")
    goal_type: Optional[HabitGoalType] = Field(
        default=HabitGoalType.BOOLEAN,
        alias="goalType"
    )
    unit: Optional[str] = Field(default=None, description="Unit for count/duration goals")

    # Frequency
    frequency: HabitFrequency = Field(default=HabitFrequency.DAILY)
    repeat_days: Optional[list[int]] = Field(
        default=None,
        alias="repeatDays",
        description="Days of week (0=Mon, 6=Sun) for weekly habits"
    )

    # Timing
    reminder_time: Optional[str] = Field(default=None, alias="reminderTime")
    section_id: Optional[str] = Field(
        default=None,
        alias="sectionId",
        description="Time section (morning, afternoon, evening)"
    )

    # Status
    status: HabitStatus = Field(default=HabitStatus.ACTIVE)

    # Appearance
    color: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)

    # Stats
    current_streak: Optional[int] = Field(default=0, alias="currentStreak")
    best_streak: Optional[int] = Field(default=0, alias="bestStreak")
    total_check_ins: Optional[int] = Field(default=0, alias="totalCheckIns")

    # Metadata
    created_time: Optional[str] = Field(default=None, alias="createdTime")
    modified_time: Optional[str] = Field(default=None, alias="modifiedTime")
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    etag: Optional[str] = Field(default=None)


class HabitCreate(BaseModel):
    """Model for creating a new habit."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., description="Habit name", min_length=1, max_length=100)

    # Goal
    goal: int = Field(default=1, ge=1, description="Target value per period")
    goal_type: HabitGoalType = Field(default=HabitGoalType.BOOLEAN)
    unit: Optional[str] = Field(
        default=None,
        description="Unit for tracking (e.g., 'glasses', 'minutes')"
    )

    # Frequency
    frequency: HabitFrequency = Field(default=HabitFrequency.DAILY)
    repeat_days: Optional[list[int]] = Field(
        default=None,
        description="Days of week for weekly habits (0=Mon, 6=Sun)"
    )

    # Timing
    reminder_time: Optional[str] = Field(
        default=None,
        description="Reminder time in HH:MM format"
    )
    section_id: Optional[str] = Field(
        default=None,
        description="Time section: 'morning', 'afternoon', 'evening', 'anytime'"
    )

    # Appearance
    color: Optional[str] = Field(default=None, description="Hex color code")
    icon: Optional[str] = Field(default=None, description="Icon identifier")


class HabitUpdate(BaseModel):
    """Model for updating a habit."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(..., description="Habit ID to update")
    name: Optional[str] = Field(default=None, max_length=100)
    goal: Optional[int] = Field(default=None, ge=1)
    goal_type: Optional[HabitGoalType] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    frequency: Optional[HabitFrequency] = Field(default=None)
    repeat_days: Optional[list[int]] = Field(default=None)
    reminder_time: Optional[str] = Field(default=None)
    section_id: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)
    status: Optional[HabitStatus] = Field(default=None)


class HabitCheckIn(BaseModel):
    """Model for recording a habit check-in."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    habit_id: str = Field(..., description="Habit ID to check in")
    date: Optional[str] = Field(
        default=None,
        description="Check-in date (ISO format, defaults to today)"
    )
    value: Optional[int] = Field(
        default=1,
        ge=0,
        description="Check-in value (1 for boolean, count for count-based)"
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional note for this check-in",
        max_length=500
    )


class HabitRecord(BaseModel):
    """Individual habit check-in record."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    habit_id: str = Field(..., alias="habitId")
    date: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    value: int = Field(default=1)
    status: int = Field(default=0, description="0=incomplete, 2=complete")
    note: Optional[str] = Field(default=None)
    created_time: Optional[str] = Field(default=None, alias="createdTime")


class HabitStats(BaseModel):
    """Habit statistics and analytics."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    habit_id: str = Field(..., alias="habitId")
    current_streak: int = Field(default=0, alias="currentStreak")
    best_streak: int = Field(default=0, alias="bestStreak")
    total_check_ins: int = Field(default=0, alias="totalCheckIns")
    completion_rate: Optional[float] = Field(
        default=None,
        alias="completionRate",
        description="Percentage of days completed"
    )
    monthly_stats: Optional[dict] = Field(
        default=None,
        alias="monthlyStats",
        description="Check-ins per month"
    )


class HabitFilter(BaseModel):
    """Filter for listing habits."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: Optional[HabitStatus] = Field(default=None)
    frequency: Optional[HabitFrequency] = Field(default=None)
    section_id: Optional[str] = Field(default=None)
    search: Optional[str] = Field(default=None, description="Search in habit names")
