"""
Habit Service - Habit tracking operations (v2 API only).
"""

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..api.exceptions import ConfigurationError
from ..models.habits import (
    Habit,
    HabitCreate,
    HabitUpdate,
    HabitCheckIn,
    HabitRecord,
    HabitStats,
    HabitStatus,
    HabitFilter,
)
from .base_service import CRUDService

logger = logging.getLogger(__name__)


class HabitService(CRUDService[Habit]):
    """
    Service for habit tracking operations.

    Note: Habits are only available through the v2 API.
    The official v1 API does not support habit operations.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)

    def _require_v2(self) -> None:
        """Raise error if v2 is not available."""
        if not self.is_v2_available:
            raise ConfigurationError(
                "Habit operations require v2 API authentication. "
                "Use login_v2(username, password) to authenticate."
            )

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    async def list(self, filter_params: Optional[HabitFilter] = None) -> List[Habit]:
        """
        List all habits.

        Args:
            filter_params: Optional filter parameters

        Returns:
            List of Habit objects
        """
        self._require_v2()

        url = Endpoints.Habits.list()
        data = await self.client.get(url, version=APIVersion.V2)

        habits = [Habit(**h) for h in data] if isinstance(data, list) else []

        # Apply filters
        if filter_params:
            if filter_params.status:
                habits = [h for h in habits if h.status == filter_params.status]
            if filter_params.frequency:
                habits = [h for h in habits if h.frequency == filter_params.frequency]
            if filter_params.section_id:
                habits = [h for h in habits if h.section_id == filter_params.section_id]
            if filter_params.search:
                query = filter_params.search.lower()
                habits = [h for h in habits if query in h.name.lower()]

        return habits

    async def get(self, habit_id: str) -> Habit:
        """
        Get a specific habit by ID.

        Args:
            habit_id: Habit identifier

        Returns:
            Habit object
        """
        self._require_v2()

        url = Endpoints.Habits.get(habit_id)
        data = await self.client.get(url, version=APIVersion.V2)
        return Habit(**data)

    async def create(self, habit_data: HabitCreate) -> Habit:
        """
        Create a new habit.

        Args:
            habit_data: Habit creation data

        Returns:
            Created Habit object
        """
        self._require_v2()

        payload = {
            "name": habit_data.name,
            "goal": habit_data.goal,
            "goalType": habit_data.goal_type.value,
            "frequency": habit_data.frequency.value,
        }

        if habit_data.unit:
            payload["unit"] = habit_data.unit
        if habit_data.repeat_days:
            payload["repeatDays"] = habit_data.repeat_days
        if habit_data.reminder_time:
            payload["reminderTime"] = habit_data.reminder_time
        if habit_data.section_id:
            payload["sectionId"] = habit_data.section_id
        if habit_data.color:
            payload["color"] = habit_data.color
        if habit_data.icon:
            payload["icon"] = habit_data.icon

        url = Endpoints.Habits.create()
        data = await self.client.post(url, version=APIVersion.V2, data=payload)
        return Habit(**data)

    async def update(self, habit_data: HabitUpdate) -> Habit:
        """
        Update an existing habit.

        Args:
            habit_data: Habit update data

        Returns:
            Updated Habit object
        """
        self._require_v2()

        payload = {"id": habit_data.id}

        if habit_data.name:
            payload["name"] = habit_data.name
        if habit_data.goal:
            payload["goal"] = habit_data.goal
        if habit_data.goal_type:
            payload["goalType"] = habit_data.goal_type.value
        if habit_data.unit:
            payload["unit"] = habit_data.unit
        if habit_data.frequency:
            payload["frequency"] = habit_data.frequency.value
        if habit_data.repeat_days:
            payload["repeatDays"] = habit_data.repeat_days
        if habit_data.reminder_time:
            payload["reminderTime"] = habit_data.reminder_time
        if habit_data.section_id:
            payload["sectionId"] = habit_data.section_id
        if habit_data.color:
            payload["color"] = habit_data.color
        if habit_data.icon:
            payload["icon"] = habit_data.icon
        if habit_data.status:
            payload["status"] = habit_data.status.value

        url = Endpoints.Habits.update(habit_data.id)
        data = await self.client.post(url, version=APIVersion.V2, data=payload)
        return Habit(**data)

    async def delete(self, habit_id: str) -> bool:
        """
        Delete a habit.

        Args:
            habit_id: Habit to delete

        Returns:
            True if successful
        """
        self._require_v2()

        url = Endpoints.Habits.delete(habit_id)
        await self.client.delete(url, version=APIVersion.V2)
        return True

    # =========================================================================
    # Check-in Operations
    # =========================================================================

    async def checkin(self, checkin_data: HabitCheckIn) -> HabitRecord:
        """
        Record a habit check-in.

        Args:
            checkin_data: Check-in data

        Returns:
            HabitRecord object
        """
        self._require_v2()

        payload = {
            "habitId": checkin_data.habit_id,
            "value": checkin_data.value or 1,
        }

        if checkin_data.date:
            payload["date"] = checkin_data.date
        else:
            payload["date"] = datetime.now().strftime("%Y-%m-%d")

        if checkin_data.note:
            payload["note"] = checkin_data.note

        url = Endpoints.Habits.checkin(checkin_data.habit_id)
        data = await self.client.post(url, version=APIVersion.V2, data=payload)
        return HabitRecord(**data)

    async def undo_checkin(self, habit_id: str, date_str: str) -> bool:
        """
        Undo a habit check-in for a specific date.

        Args:
            habit_id: Habit ID
            date_str: Date of check-in to undo (YYYY-MM-DD)

        Returns:
            True if successful
        """
        self._require_v2()

        payload = {
            "habitId": habit_id,
            "date": date_str,
            "value": 0,  # Reset to 0
        }

        url = Endpoints.Habits.checkin(habit_id)
        await self.client.post(url, version=APIVersion.V2, data=payload)
        return True

    async def get_records(
        self,
        habit_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HabitRecord]:
        """
        Get check-in records for a habit.

        Args:
            habit_id: Habit ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of HabitRecord objects
        """
        self._require_v2()

        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        url = Endpoints.Habits.records(habit_id)
        data = await self.client.get(url, version=APIVersion.V2, params=params)

        return [HabitRecord(**r) for r in data] if isinstance(data, list) else []

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_stats(self, habit_id: str) -> HabitStats:
        """
        Get statistics for a habit.

        Args:
            habit_id: Habit ID

        Returns:
            HabitStats object
        """
        self._require_v2()

        habit = await self.get(habit_id)

        return HabitStats(
            habit_id=habit_id,
            current_streak=habit.current_streak or 0,
            best_streak=habit.best_streak or 0,
            total_check_ins=habit.total_check_ins or 0,
        )

    async def get_today_status(self) -> List[Dict[str, Any]]:
        """
        Get today's status for all habits.

        Returns:
            List of habits with today's completion status
        """
        self._require_v2()

        habits = await self.list(HabitFilter(status=HabitStatus.ACTIVE))
        today = datetime.now().strftime("%Y-%m-%d")

        results = []
        for habit in habits:
            records = await self.get_records(habit.id, from_date=today, to_date=today)
            completed = any(r.value >= habit.goal for r in records)
            current_value = sum(r.value for r in records)

            results.append({
                "habit": habit,
                "completed": completed,
                "current_value": current_value,
                "goal": habit.goal,
                "remaining": max(0, habit.goal - current_value),
            })

        return results

    # =========================================================================
    # Extended Operations
    # =========================================================================

    async def pause(self, habit_id: str) -> Habit:
        """
        Pause a habit.

        Args:
            habit_id: Habit to pause

        Returns:
            Updated Habit
        """
        return await self.update(HabitUpdate(id=habit_id, status=HabitStatus.PAUSED))

    async def resume(self, habit_id: str) -> Habit:
        """
        Resume a paused habit.

        Args:
            habit_id: Habit to resume

        Returns:
            Updated Habit
        """
        return await self.update(HabitUpdate(id=habit_id, status=HabitStatus.ACTIVE))

    async def archive(self, habit_id: str) -> Habit:
        """
        Archive a habit.

        Args:
            habit_id: Habit to archive

        Returns:
            Updated Habit
        """
        return await self.update(HabitUpdate(id=habit_id, status=HabitStatus.ARCHIVED))

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_checkin(self, checkins: List[HabitCheckIn]) -> List[HabitRecord]:
        """
        Record multiple check-ins.

        Args:
            checkins: List of check-in data

        Returns:
            List of HabitRecord objects
        """
        results = []
        for checkin in checkins:
            result = await self.checkin(checkin)
            results.append(result)
        return results

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_habit(self, habit: Habit, include_stats: bool = True) -> str:
        """Format a single habit as markdown."""
        status_emoji = {
            HabitStatus.ACTIVE: "",
            HabitStatus.PAUSED: "",
            HabitStatus.ARCHIVED: "",
        }

        lines = [
            f"### {habit.name}",
            f"- **ID**: `{habit.id}`",
            f"- **Status**: {status_emoji.get(habit.status, '')} {habit.status.value}",
            f"- **Goal**: {habit.goal} {habit.unit or 'times'}/{habit.frequency.value}",
        ]

        if habit.goal_type:
            lines.append(f"- **Type**: {habit.goal_type.value}")
        if habit.section_id:
            lines.append(f"- **Time**: {habit.section_id}")
        if habit.reminder_time:
            lines.append(f"- **Reminder**: {habit.reminder_time}")

        if include_stats:
            lines.append(f"- **Current Streak**: {habit.current_streak or 0} days")
            lines.append(f"- **Best Streak**: {habit.best_streak or 0} days")
            lines.append(f"- **Total Check-ins**: {habit.total_check_ins or 0}")

        return "\n".join(lines)

    def format_habit_list(self, habits: List[Habit], title: str = "Habits") -> str:
        """Format habit list as markdown."""
        if not habits:
            return f"##  {title}\n\nNo habits found."

        lines = [f"##  {title} ({len(habits)} total)\n"]

        # Group by status
        active = [h for h in habits if h.status == HabitStatus.ACTIVE]
        paused = [h for h in habits if h.status == HabitStatus.PAUSED]
        archived = [h for h in habits if h.status == HabitStatus.ARCHIVED]

        if active:
            lines.append("\n### Active Habits\n")
            for habit in active:
                lines.append(self.format_habit(habit))
                lines.append("")

        if paused:
            lines.append("\n### Paused Habits\n")
            for habit in paused:
                lines.append(self.format_habit(habit, include_stats=False))
                lines.append("")

        if archived:
            lines.append("\n### Archived Habits\n")
            for habit in archived:
                lines.append(self.format_habit(habit, include_stats=False))
                lines.append("")

        return "\n".join(lines)

    def format_today_status(self, status_list: List[Dict[str, Any]]) -> str:
        """Format today's habit status as markdown."""
        if not status_list:
            return "##  Today's Habits\n\nNo active habits found."

        lines = ["##  Today's Habit Progress\n"]

        completed_count = sum(1 for s in status_list if s["completed"])
        total = len(status_list)

        lines.append(f"**Progress**: {completed_count}/{total} habits completed\n")

        for item in status_list:
            habit = item["habit"]
            check = "" if item["completed"] else ""
            progress = f"{item['current_value']}/{item['goal']}"

            lines.append(f"- {check} **{habit.name}** - {progress}")
            if not item["completed"] and item["remaining"] > 0:
                lines.append(f"  _{item['remaining']} more to go_")

        return "\n".join(lines)
