"""
Smart Service - AI-powered task scheduling and smart task views.

Provides intelligent task filtering, scheduling suggestions, and productivity insights.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..models.tasks import Task, TaskStatus, TaskPriority
from .base_service import BaseService
from .task_service import TaskService
from .project_service import ProjectService

logger = logging.getLogger(__name__)


class SmartService(BaseService[Task]):
    """
    Service for smart task views and AI-assisted scheduling.

    Provides:
    - Today's tasks
    - Tomorrow's tasks
    - Overdue tasks
    - Next 7 days view
    - Search functionality
    - Day scheduling suggestions
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)
        self.task_service = TaskService(client)
        self.project_service = ProjectService(client)

    # =========================================================================
    # Smart Views
    # =========================================================================

    async def get_today_tasks(self) -> List[Task]:
        """
        Get all tasks due today.

        Returns:
            List of tasks due today
        """
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

        all_tasks = await self.task_service.list(include_completed=False)

        today_tasks = []
        for task in all_tasks:
            if task.due_date:
                try:
                    due = self._parse_date(task.due_date)
                    if today_start <= due <= today_end:
                        today_tasks.append(task)
                except ValueError:
                    continue
            elif task.start_date:
                try:
                    start = self._parse_date(task.start_date)
                    if today_start <= start <= today_end:
                        today_tasks.append(task)
                except ValueError:
                    continue

        # Sort by priority (high to low) then by due time
        return sorted(
            today_tasks,
            key=lambda t: (-t.priority, t.due_date or t.start_date or "")
        )

    async def get_tomorrow_tasks(self) -> List[Task]:
        """
        Get all tasks due tomorrow.

        Returns:
            List of tasks due tomorrow
        """
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
        tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time()).replace(tzinfo=timezone.utc)

        all_tasks = await self.task_service.list(include_completed=False)

        tomorrow_tasks = []
        for task in all_tasks:
            if task.due_date:
                try:
                    due = self._parse_date(task.due_date)
                    if tomorrow_start <= due <= tomorrow_end:
                        tomorrow_tasks.append(task)
                except ValueError:
                    continue

        return sorted(
            tomorrow_tasks,
            key=lambda t: (-t.priority, t.due_date or "")
        )

    async def get_overdue_tasks(self) -> List[Task]:
        """
        Get all overdue tasks (past due date, not completed).

        Returns:
            List of overdue tasks
        """
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)

        all_tasks = await self.task_service.list(include_completed=False)

        overdue_tasks = []
        for task in all_tasks:
            if task.due_date:
                try:
                    due = self._parse_date(task.due_date)
                    if due < today_start:
                        overdue_tasks.append(task)
                except ValueError:
                    continue

        # Sort by due date (oldest first) then priority
        return sorted(
            overdue_tasks,
            key=lambda t: (t.due_date or "", -t.priority)
        )

    async def get_next_7_days_tasks(self) -> Dict[str, List[Task]]:
        """
        Get tasks for the next 7 days, grouped by date.

        Returns:
            Dict mapping date strings to task lists
        """
        now = datetime.now(timezone.utc)
        start_date = now.date()
        end_date = start_date + timedelta(days=7)

        all_tasks = await self.task_service.list(include_completed=False)

        # Group tasks by date
        tasks_by_date: Dict[str, List[Task]] = {}
        for i in range(7):
            date_str = (start_date + timedelta(days=i)).isoformat()
            tasks_by_date[date_str] = []

        for task in all_tasks:
            if task.due_date:
                try:
                    due = self._parse_date(task.due_date)
                    due_date = due.date()
                    if start_date <= due_date <= end_date:
                        date_str = due_date.isoformat()
                        if date_str in tasks_by_date:
                            tasks_by_date[date_str].append(task)
                except ValueError:
                    continue

        # Sort tasks within each day by priority
        for date_str in tasks_by_date:
            tasks_by_date[date_str] = sorted(
                tasks_by_date[date_str],
                key=lambda t: (-t.priority, t.due_date or "")
            )

        return tasks_by_date

    async def search_tasks(
        self,
        query: str,
        project_id: Optional[str] = None,
        include_completed: bool = False,
    ) -> List[Task]:
        """
        Search tasks by keyword in title and content.

        Args:
            query: Search query string
            project_id: Optional project filter
            include_completed: Include completed tasks

        Returns:
            List of matching tasks
        """
        all_tasks = await self.task_service.list(
            project_id=project_id,
            include_completed=include_completed
        )

        query_lower = query.lower()
        matching_tasks = []

        for task in all_tasks:
            title_match = query_lower in task.title.lower()
            content_match = task.content and query_lower in task.content.lower()
            tag_match = task.tags and any(query_lower in tag.lower() for tag in task.tags)

            if title_match or content_match or tag_match:
                matching_tasks.append(task)

        # Sort by relevance (title match first) then priority
        def relevance_score(t: Task) -> int:
            score = 0
            if query_lower in t.title.lower():
                score += 10
            if t.content and query_lower in t.content.lower():
                score += 5
            if t.tags and any(query_lower in tag.lower() for tag in t.tags):
                score += 3
            score += t.priority
            return score

        return sorted(matching_tasks, key=lambda t: -relevance_score(t))

    async def get_no_date_tasks(self) -> List[Task]:
        """
        Get tasks without any due date or start date.

        Returns:
            List of unscheduled tasks
        """
        all_tasks = await self.task_service.list(include_completed=False)

        no_date_tasks = [
            task for task in all_tasks
            if not task.due_date and not task.start_date
        ]

        return sorted(no_date_tasks, key=lambda t: (-t.priority, t.title))

    async def get_high_priority_tasks(self) -> List[Task]:
        """
        Get all high priority (priority=5) tasks.

        Returns:
            List of high priority tasks
        """
        all_tasks = await self.task_service.list(include_completed=False)

        high_priority = [
            task for task in all_tasks
            if task.priority == TaskPriority.HIGH.value
        ]

        return sorted(high_priority, key=lambda t: (t.due_date or "9999", t.title))

    # =========================================================================
    # Scheduling Suggestions
    # =========================================================================

    async def schedule_day(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AI-suggested schedule for a day.

        Args:
            date: Date to schedule (defaults to today)

        Returns:
            Suggested schedule with time blocks and task assignments
        """
        if date:
            target_date = datetime.fromisoformat(date).date()
        else:
            target_date = datetime.now(timezone.utc).date()

        # Get tasks for the target date
        target_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        target_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        all_tasks = await self.task_service.list(include_completed=False)

        # Get overdue tasks (high priority for scheduling)
        overdue = await self.get_overdue_tasks()

        # Filter tasks for target date
        day_tasks = []
        for task in all_tasks:
            if task.due_date:
                try:
                    due = self._parse_date(task.due_date)
                    if target_start <= due <= target_end:
                        day_tasks.append(task)
                except ValueError:
                    continue

        # Combine overdue with day tasks
        tasks_to_schedule = overdue[:5] + day_tasks  # Top 5 overdue

        # Create time blocks (simplified scheduling)
        schedule = {
            "date": target_date.isoformat(),
            "summary": {
                "total_tasks": len(tasks_to_schedule),
                "overdue_tasks": len(overdue),
                "high_priority": len([t for t in tasks_to_schedule if t.priority >= 5]),
            },
            "morning": {
                "time": "09:00-12:00",
                "focus": "High priority and deep work",
                "tasks": [],
            },
            "afternoon": {
                "time": "13:00-17:00",
                "focus": "Meetings and collaborative work",
                "tasks": [],
            },
            "evening": {
                "time": "17:00-19:00",
                "focus": "Wrap-up and planning",
                "tasks": [],
            },
        }

        # Distribute tasks by priority
        sorted_tasks = sorted(tasks_to_schedule, key=lambda t: -t.priority)

        for i, task in enumerate(sorted_tasks):
            task_info = {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "project_id": task.project_id,
                "is_overdue": task in overdue,
            }

            # High priority goes to morning, others distributed
            if task.priority >= 5 or task in overdue:
                schedule["morning"]["tasks"].append(task_info)
            elif i % 2 == 0:
                schedule["afternoon"]["tasks"].append(task_info)
            else:
                schedule["evening"]["tasks"].append(task_info)

        return schedule

    async def get_productivity_summary(self) -> Dict[str, Any]:
        """
        Get a productivity summary with actionable insights.

        Returns:
            Productivity summary with recommendations
        """
        today_tasks = await self.get_today_tasks()
        overdue_tasks = await self.get_overdue_tasks()
        no_date_tasks = await self.get_no_date_tasks()
        high_priority = await self.get_high_priority_tasks()

        # Calculate summary
        summary = {
            "today": {
                "count": len(today_tasks),
                "high_priority_count": len([t for t in today_tasks if t.priority >= 5]),
            },
            "overdue": {
                "count": len(overdue_tasks),
                "oldest_days": 0,
            },
            "unscheduled": {
                "count": len(no_date_tasks),
                "high_priority_count": len([t for t in no_date_tasks if t.priority >= 5]),
            },
            "high_priority_total": len(high_priority),
            "recommendations": [],
        }

        # Calculate oldest overdue
        if overdue_tasks:
            oldest = overdue_tasks[0]
            if oldest.due_date:
                oldest_due = self._parse_date(oldest.due_date)
                summary["overdue"]["oldest_days"] = (datetime.now(timezone.utc) - oldest_due).days

        # Generate recommendations
        if overdue_tasks:
            summary["recommendations"].append(
                f"🔴 You have {len(overdue_tasks)} overdue tasks. Consider completing or rescheduling them."
            )

        if len([t for t in no_date_tasks if t.priority >= 5]) > 0:
            summary["recommendations"].append(
                "⚠️ Some high-priority tasks don't have due dates. Schedule them to stay on track."
            )

        if len(today_tasks) > 10:
            summary["recommendations"].append(
                "📋 You have many tasks today. Focus on the top 3 priorities first."
            )

        if len(today_tasks) == 0:
            summary["recommendations"].append(
                "✨ No tasks due today! Great time to tackle overdue items or plan ahead."
            )

        return summary

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        # Handle various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]

        # Clean up timezone format
        date_str = date_str.replace("+0000", "+00:00").replace("Z", "+00:00")

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_smart_view(
        self,
        tasks: List[Task],
        title: str = "Tasks",
        show_project: bool = True,
    ) -> str:
        """Format a smart view as markdown."""
        if not tasks:
            return f"## 📋 {title}\n\nNo tasks found."

        lines = [f"## 📋 {title} ({len(tasks)} tasks)\n"]

        for task in tasks:
            priority_emoji = {0: "⚪", 1: "🔵", 3: "🟡", 5: "🔴"}.get(task.priority, "⚪")

            line = f"- {priority_emoji} **{task.title}**"

            if task.due_date:
                line += f" 📅 {task.due_date[:10]}"

            if show_project and task.project_id:
                line += f" 📁 `{task.project_id}`"

            if task.tags:
                tags = ", ".join([f"`{t}`" for t in task.tags[:3]])
                line += f" 🏷️ {tags}"

            lines.append(line)
            lines.append(f"  - ID: `{task.id}`")

        return "\n".join(lines)

    def format_schedule(self, schedule: Dict[str, Any]) -> str:
        """Format schedule as markdown."""
        lines = [
            f"## 📅 Schedule for {schedule['date']}\n",
            f"### Summary",
            f"- Total tasks: {schedule['summary']['total_tasks']}",
            f"- Overdue: {schedule['summary']['overdue_tasks']}",
            f"- High priority: {schedule['summary']['high_priority']}",
            "",
        ]

        for period in ["morning", "afternoon", "evening"]:
            block = schedule[period]
            emoji = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}[period]

            lines.append(f"### {emoji} {period.title()} ({block['time']})")
            lines.append(f"*{block['focus']}*\n")

            if block["tasks"]:
                for task in block["tasks"]:
                    overdue_marker = "🔴 " if task.get("is_overdue") else ""
                    priority_emoji = {0: "⚪", 1: "🔵", 3: "🟡", 5: "🔴"}.get(
                        task.get("priority", 0), "⚪"
                    )
                    lines.append(f"- {overdue_marker}{priority_emoji} {task['title']}")
            else:
                lines.append("- *(No tasks scheduled)*")

            lines.append("")

        return "\n".join(lines)

    def format_productivity_summary(self, summary: Dict[str, Any]) -> str:
        """Format productivity summary as markdown."""
        lines = [
            "## 📊 Productivity Summary\n",
            "### Today's Focus",
            f"- Tasks due today: **{summary['today']['count']}**",
            f"- High priority today: **{summary['today']['high_priority_count']}**",
            "",
            "### Attention Needed",
            f"- Overdue tasks: **{summary['overdue']['count']}**",
        ]

        if summary["overdue"]["oldest_days"] > 0:
            lines.append(f"- Oldest overdue: **{summary['overdue']['oldest_days']} days ago**")

        lines.extend([
            "",
            "### Planning",
            f"- Unscheduled tasks: **{summary['unscheduled']['count']}**",
            f"- Unscheduled high priority: **{summary['unscheduled']['high_priority_count']}**",
            "",
        ])

        if summary["recommendations"]:
            lines.append("### 💡 Recommendations\n")
            for rec in summary["recommendations"]:
                lines.append(f"- {rec}")

        return "\n".join(lines)
