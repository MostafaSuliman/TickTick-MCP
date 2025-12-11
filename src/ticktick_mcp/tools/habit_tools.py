"""
Habit MCP tools - Habit tracking and management (v2 API only).
"""

from typing import Optional
from pydantic import BaseModel, Field


class ListHabitsInput(BaseModel):
    """Input for listing habits."""
    pass


class GetHabitInput(BaseModel):
    """Input for getting a specific habit."""
    habit_id: str = Field(..., description="Habit ID")


class CreateHabitInput(BaseModel):
    """Input for creating a habit."""
    name: str = Field(..., description="Habit name", min_length=1, max_length=100)
    goal: int = Field(
        default=1,
        description="Daily goal count",
        ge=1,
        le=100
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., 'times', 'minutes', 'pages')"
    )
    frequency: Optional[str] = Field(
        default="daily",
        description="Frequency: daily, weekly, specific_days"
    )
    reminder_time: Optional[str] = Field(
        default=None,
        description="Reminder time (HH:MM format)"
    )
    color: Optional[str] = Field(
        default=None,
        description="Habit color (hex code)"
    )
    icon: Optional[str] = Field(
        default=None,
        description="Habit icon identifier"
    )


class UpdateHabitInput(BaseModel):
    """Input for updating a habit."""
    habit_id: str = Field(..., description="Habit ID to update")
    name: Optional[str] = Field(default=None, max_length=100)
    goal: Optional[int] = Field(default=None, ge=1, le=100)
    unit: Optional[str] = Field(default=None)
    frequency: Optional[str] = Field(default=None)
    reminder_time: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)


class DeleteHabitInput(BaseModel):
    """Input for deleting a habit."""
    habit_id: str = Field(..., description="Habit ID to delete")


class CheckinHabitInput(BaseModel):
    """Input for habit check-in."""
    habit_id: str = Field(..., description="Habit ID")
    value: int = Field(
        default=1,
        description="Check-in value/count",
        ge=1
    )
    date: Optional[str] = Field(
        default=None,
        description="Check-in date (YYYY-MM-DD, defaults to today)"
    )


class GetHabitStatsInput(BaseModel):
    """Input for getting habit statistics."""
    habit_id: str = Field(..., description="Habit ID")
    from_date: Optional[str] = Field(
        default=None,
        description="Start date (YYYY-MM-DD)"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM-DD)"
    )


class GetTodayStatusInput(BaseModel):
    """Input for getting today's habit status."""
    pass


def register_habit_tools(mcp, habit_service):
    """Register habit tracking tools (v2 API only)."""

    @mcp.tool(
        name="ticktick_list_habits",
        annotations={
            "title": "List TickTick Habits",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_habits(params: ListHabitsInput) -> str:
        """
        List all habits.

        Requires v2 API authentication (username/password login).
        """
        try:
            habits = await habit_service.list()
            return habit_service.format_habit_list(habits)
        except Exception as e:
            return f"**Error**: Failed to list habits - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_habit",
        annotations={
            "title": "Get TickTick Habit",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_habit(params: GetHabitInput) -> str:
        """
        Get details of a specific habit including its statistics.

        Requires v2 API authentication.
        """
        try:
            habit = await habit_service.get(params.habit_id)
            return habit_service.format_habit(habit)
        except Exception as e:
            return f"**Error**: Could not find habit - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_create_habit",
        annotations={
            "title": "Create TickTick Habit",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_habit(params: CreateHabitInput) -> str:
        """
        Create a new habit to track.

        Set daily goals, reminders, and custom icons/colors.
        Requires v2 API authentication.
        """
        from ..models.habits import HabitCreate

        habit_data = HabitCreate(
            name=params.name,
            goal=params.goal,
            unit=params.unit,
            frequency=params.frequency,
            reminder_time=params.reminder_time,
            color=params.color,
            icon=params.icon,
        )

        try:
            habit = await habit_service.create(habit_data)
            return f"""## Habit Created

{habit_service.format_habit(habit)}
"""
        except Exception as e:
            return f"**Error**: Failed to create habit - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_update_habit",
        annotations={
            "title": "Update TickTick Habit",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_habit(params: UpdateHabitInput) -> str:
        """
        Update an existing habit's properties.

        Requires v2 API authentication.
        """
        from ..models.habits import HabitUpdate

        update_data = HabitUpdate(
            id=params.habit_id,
            name=params.name,
            goal=params.goal,
            unit=params.unit,
            frequency=params.frequency,
            reminder_time=params.reminder_time,
            color=params.color,
        )

        try:
            habit = await habit_service.update(update_data)
            return f"""## Habit Updated

{habit_service.format_habit(habit)}
"""
        except Exception as e:
            return f"**Error**: Failed to update habit - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_delete_habit",
        annotations={
            "title": "Delete TickTick Habit",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_habit(params: DeleteHabitInput) -> str:
        """
        Delete a habit.

        Warning: This will delete all check-in history for this habit.
        Requires v2 API authentication.
        """
        try:
            await habit_service.delete(params.habit_id)
            return f"## Habit Deleted\n\nHabit `{params.habit_id}` and all its history have been deleted."
        except Exception as e:
            return f"**Error**: Failed to delete habit - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_checkin_habit",
        annotations={
            "title": "Check-in Habit",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def checkin_habit(params: CheckinHabitInput) -> str:
        """
        Record a habit check-in.

        Track your daily progress toward habit goals.
        Requires v2 API authentication.
        """
        from ..models.habits import HabitCheckIn

        checkin_data = HabitCheckIn(
            habit_id=params.habit_id,
            value=params.value,
            date=params.date,
        )

        try:
            record = await habit_service.checkin(checkin_data)
            completed = record.status == 2
            return f"""## Habit Check-in Recorded

- **Habit ID**: `{params.habit_id}`
- **Value**: {params.value}
- **Date**: {params.date or 'today'}
- **Status**: {'Goal completed!' if completed else 'Progress recorded'}
"""
        except Exception as e:
            return f"**Error**: Failed to check-in - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_habit_stats",
        annotations={
            "title": "Get Habit Statistics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_habit_stats(params: GetHabitStatsInput) -> str:
        """
        Get statistics for a specific habit.

        Includes completion rate, streaks, and historical data.
        Requires v2 API authentication.
        """
        try:
            stats = await habit_service.get_stats(params.habit_id)

            lines = [
                f"## Habit Statistics\n",
                f"- **Habit ID**: `{stats.habit_id}`",
                f"- **Current Streak**: {stats.current_streak} days",
                f"- **Best Streak**: {stats.best_streak} days",
                f"- **Total Check-ins**: {stats.total_check_ins}",
            ]
            if stats.completion_rate is not None:
                lines.append(f"- **Completion Rate**: {stats.completion_rate:.1f}%")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get habit stats - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_today_habits",
        annotations={
            "title": "Get Today's Habit Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_today_status(params: GetTodayStatusInput) -> str:
        """
        Get today's status for all habits.

        Shows which habits are completed and which need attention.
        Requires v2 API authentication.
        """
        try:
            status = await habit_service.get_today_status()
            if not status:
                return "## Today's Habits\n\nNo habits found or v2 API not authenticated."

            lines = ["## Today's Habit Status\n"]

            completed = [h for h in status if h.get("completed")]
            pending = [h for h in status if not h.get("completed")]

            if completed:
                lines.append(f"### Completed ({len(completed)})\n")
                for h in completed:
                    habit = h.get('habit')
                    current = h.get('current_value', 0)
                    goal = h.get('goal', 1)
                    unit = habit.unit if habit else 'times'
                    name = habit.name if habit else 'Unknown'
                    lines.append(f"- ✅ **{name}**: {current}/{goal} {unit or 'times'}")

            if pending:
                lines.append(f"\n### Pending ({len(pending)})\n")
                for h in pending:
                    habit = h.get('habit')
                    current = h.get('current_value', 0)
                    goal = h.get('goal', 1)
                    unit = habit.unit if habit else 'times'
                    name = habit.name if habit else 'Unknown'
                    lines.append(f"- ⬜ **{name}**: {current}/{goal} {unit or 'times'}")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get today's status - {str(e)}\n\n_Note: This feature requires v2 API authentication._"
