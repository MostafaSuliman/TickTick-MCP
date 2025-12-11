"""
Statistics Service - Productivity analytics and reporting (v2 API only).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..api.exceptions import ConfigurationError
from ..models.tasks import TaskStatus, TaskPriority
from .base_service import BaseService
from .task_service import TaskService
from .habit_service import HabitService
from .focus_service import FocusService

logger = logging.getLogger(__name__)


class StatisticsService(BaseService):
    """
    Service for productivity statistics and analytics.

    Aggregates data from tasks, habits, and focus sessions to provide
    comprehensive productivity insights.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)
        self._task_service = TaskService(client)
        self._habit_service = HabitService(client)
        self._focus_service = FocusService(client)

    def _require_v2(self) -> None:
        """Raise error if v2 is not available."""
        if not self.is_v2_available:
            raise ConfigurationError(
                "Statistics require v2 API authentication. "
                "Use login_v2(username, password) to authenticate."
            )

    # =========================================================================
    # Overview Statistics
    # =========================================================================

    async def get_overview(self) -> Dict[str, Any]:
        """
        Get overview statistics for the dashboard.

        Returns:
            Dict with overview statistics
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get all data in parallel
        tasks = await self._task_service.list(include_completed=False)
        habits_status = []
        focus_today = {}

        if self.is_v2_available:
            try:
                habits_status = await self._habit_service.get_today_status()
            except Exception as e:
                logger.warning(f"Could not get habit status: {e}")

            try:
                focus_today = await self._focus_service.get_today_stats()
            except Exception as e:
                logger.warning(f"Could not get focus stats: {e}")

        # Task statistics
        today_tasks = []
        overdue_tasks = []
        high_priority = []

        for task in tasks:
            if task.priority == TaskPriority.HIGH:
                high_priority.append(task)

            if task.due_date:
                try:
                    due = datetime.fromisoformat(
                        task.due_date.replace("Z", "+00:00")
                    ).date()
                    if due < datetime.now().date():
                        overdue_tasks.append(task)
                    elif due == datetime.now().date():
                        today_tasks.append(task)
                except Exception:
                    pass

        # Habit statistics
        habits_completed = sum(1 for h in habits_status if h.get("completed", False))
        habits_total = len(habits_status)

        return {
            "date": today,
            "tasks": {
                "total_pending": len(tasks),
                "due_today": len(today_tasks),
                "overdue": len(overdue_tasks),
                "high_priority": len(high_priority),
            },
            "habits": {
                "total_active": habits_total,
                "completed_today": habits_completed,
                "completion_rate": (habits_completed / habits_total * 100) if habits_total else 0,
            },
            "focus": focus_today,
        }

    async def get_daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed daily summary.

        Args:
            date_str: Date to summarize (YYYY-MM-DD, defaults to today)

        Returns:
            Dict with daily summary
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        summary = {
            "date": date_str,
            "tasks_completed": [],
            "tasks_created": [],
            "habits_completed": [],
            "focus_sessions": [],
            "total_focus_time": 0,
        }

        # Get completed tasks for the day
        if self.is_v2_available:
            try:
                completed = await self._task_service.get_completed(
                    from_date=date_str,
                    to_date=date_str,
                )
                summary["tasks_completed"] = [
                    {"id": t.id, "title": t.title, "project_id": t.project_id}
                    for t in completed
                ]
            except Exception as e:
                logger.warning(f"Could not get completed tasks: {e}")

            # Get focus sessions
            try:
                from ..models.focus import FocusFilter
                focus_records = await self._focus_service.get_records(
                    FocusFilter(from_date=date_str, to_date=date_str)
                )
                summary["focus_sessions"] = [
                    {
                        "duration_minutes": r.duration // 60,
                        "type": r.focus_type.value,
                        "task": r.task_title,
                    }
                    for r in focus_records
                ]
                summary["total_focus_time"] = sum(r.duration for r in focus_records) // 60
            except Exception as e:
                logger.warning(f"Could not get focus records: {e}")

        return summary

    async def get_weekly_report(self, week_offset: int = 0) -> Dict[str, Any]:
        """
        Get weekly productivity report.

        Args:
            week_offset: 0 for current week, -1 for last week, etc.

        Returns:
            Dict with weekly report
        """
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday() + (7 * abs(week_offset)))
        week_end = week_start + timedelta(days=6)

        report = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "daily_breakdown": {},
            "totals": {
                "tasks_completed": 0,
                "habits_completed": 0,
                "focus_time_minutes": 0,
                "pomodoros": 0,
            },
        }

        # Get data for each day
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.isoformat()

            day_data = {
                "tasks_completed": 0,
                "habits_completed": 0,
                "focus_time": 0,
            }

            if self.is_v2_available:
                try:
                    completed = await self._task_service.get_completed(
                        from_date=day_str,
                        to_date=day_str,
                    )
                    day_data["tasks_completed"] = len(completed)
                    report["totals"]["tasks_completed"] += len(completed)
                except Exception:
                    pass

                try:
                    from ..models.focus import FocusFilter
                    focus_records = await self._focus_service.get_records(
                        FocusFilter(from_date=day_str, to_date=day_str)
                    )
                    focus_time = sum(r.duration for r in focus_records) // 60
                    day_data["focus_time"] = focus_time
                    report["totals"]["focus_time_minutes"] += focus_time
                    report["totals"]["pomodoros"] += len([
                        r for r in focus_records
                        if r.focus_type.value == "pomo"
                    ])
                except Exception:
                    pass

            report["daily_breakdown"][day_str] = day_data

        return report

    # =========================================================================
    # Productivity Metrics
    # =========================================================================

    async def get_productivity_score(self) -> Dict[str, Any]:
        """
        Calculate productivity score based on various metrics.

        Returns:
            Dict with productivity score and breakdown
        """
        score_breakdown = {
            "task_completion": 0,
            "habit_consistency": 0,
            "focus_time": 0,
            "overdue_penalty": 0,
        }

        # Task completion score (0-30 points)
        tasks = await self._task_service.list(include_completed=False)
        overdue_count = sum(
            1 for t in tasks
            if t.due_date and datetime.fromisoformat(
                t.due_date.replace("Z", "+00:00")
            ).date() < datetime.now().date()
        )

        if self.is_v2_available:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                completed_today = await self._task_service.get_completed(
                    from_date=today,
                    to_date=today,
                )
                # Score based on tasks completed
                score_breakdown["task_completion"] = min(30, len(completed_today) * 5)
            except Exception:
                pass

            # Habit consistency score (0-30 points)
            try:
                habits_status = await self._habit_service.get_today_status()
                if habits_status:
                    completed = sum(1 for h in habits_status if h["completed"])
                    rate = completed / len(habits_status)
                    score_breakdown["habit_consistency"] = int(rate * 30)
            except Exception:
                pass

            # Focus time score (0-30 points)
            try:
                focus_stats = await self._focus_service.get_today_stats()
                pomo_count = focus_stats.get("pomo_count", 0)
                # Score based on pomodoros (target ~8)
                score_breakdown["focus_time"] = min(30, pomo_count * 4)
            except Exception:
                pass

        # Overdue penalty (-10 to 0)
        score_breakdown["overdue_penalty"] = -min(10, overdue_count * 2)

        total_score = sum(score_breakdown.values())

        # Determine grade
        if total_score >= 80:
            grade = "A"
        elif total_score >= 60:
            grade = "B"
        elif total_score >= 40:
            grade = "C"
        elif total_score >= 20:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": max(0, min(100, total_score)),
            "grade": grade,
            "breakdown": score_breakdown,
            "recommendations": self._get_recommendations(score_breakdown),
        }

    def _get_recommendations(self, breakdown: Dict[str, int]) -> List[str]:
        """Generate recommendations based on score breakdown."""
        recommendations = []

        if breakdown["task_completion"] < 15:
            recommendations.append("Try to complete more tasks today. Break large tasks into smaller ones.")

        if breakdown["habit_consistency"] < 15:
            recommendations.append("Focus on maintaining your habit streaks. Consistency is key!")

        if breakdown["focus_time"] < 15:
            recommendations.append("Use the Pomodoro timer to increase focused work time.")

        if breakdown["overdue_penalty"] < -5:
            recommendations.append("You have several overdue tasks. Consider rescheduling or completing them.")

        if not recommendations:
            recommendations.append("Great job! Keep up the excellent work!")

        return recommendations

    # =========================================================================
    # Task Analytics
    # =========================================================================

    async def get_task_analytics(self) -> Dict[str, Any]:
        """
        Get detailed task analytics.

        Returns:
            Dict with task analytics
        """
        tasks = await self._task_service.list(include_completed=False)

        # Priority distribution
        priority_dist = {
            "high": len([t for t in tasks if t.priority == TaskPriority.HIGH]),
            "medium": len([t for t in tasks if t.priority == TaskPriority.MEDIUM]),
            "low": len([t for t in tasks if t.priority == TaskPriority.LOW]),
            "none": len([t for t in tasks if t.priority == TaskPriority.NONE]),
        }

        # Due date analysis
        today = datetime.now().date()
        due_analysis = {
            "overdue": 0,
            "today": 0,
            "this_week": 0,
            "later": 0,
            "no_date": 0,
        }

        for task in tasks:
            if not task.due_date:
                due_analysis["no_date"] += 1
            else:
                try:
                    due = datetime.fromisoformat(
                        task.due_date.replace("Z", "+00:00")
                    ).date()
                    if due < today:
                        due_analysis["overdue"] += 1
                    elif due == today:
                        due_analysis["today"] += 1
                    elif due <= today + timedelta(days=7):
                        due_analysis["this_week"] += 1
                    else:
                        due_analysis["later"] += 1
                except Exception:
                    due_analysis["no_date"] += 1

        # Tag usage
        tag_counts: Dict[str, int] = {}
        for task in tasks:
            if task.tags:
                for tag in task.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_pending": len(tasks),
            "priority_distribution": priority_dist,
            "due_date_analysis": due_analysis,
            "top_tags": dict(top_tags),
        }

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_overview(self, overview: Dict[str, Any]) -> str:
        """Format overview as markdown."""
        lines = [
            f"##  Productivity Overview - {overview['date']}\n",
            "### Tasks",
            f"-  Pending: {overview['tasks']['total_pending']}",
            f"-  Due Today: {overview['tasks']['due_today']}",
            f"-  Overdue: {overview['tasks']['overdue']}",
            f"-  High Priority: {overview['tasks']['high_priority']}",
        ]

        if overview.get("habits"):
            habits = overview["habits"]
            lines.extend([
                "",
                "### Habits",
                f"-  Completed: {habits['completed_today']}/{habits['total_active']}",
                f"-  Rate: {habits['completion_rate']:.0f}%",
            ])

        if overview.get("focus"):
            focus = overview["focus"]
            lines.extend([
                "",
                "### Focus",
                f"-  Time: {focus.get('focus_time_minutes', 0)} minutes",
                f"-  Pomodoros: {focus.get('pomo_count', 0)}/{focus.get('target', 8)}",
            ])

        return "\n".join(lines)

    def format_productivity_score(self, score_data: Dict[str, Any]) -> str:
        """Format productivity score as markdown."""
        lines = [
            "##  Productivity Score\n",
            f"### Score: {score_data['score']}/100 (Grade: {score_data['grade']})\n",
            "### Breakdown",
        ]

        breakdown = score_data["breakdown"]
        lines.extend([
            f"- Task Completion: {breakdown['task_completion']}/30",
            f"- Habit Consistency: {breakdown['habit_consistency']}/30",
            f"- Focus Time: {breakdown['focus_time']}/30",
            f"- Overdue Penalty: {breakdown['overdue_penalty']}",
        ])

        lines.extend([
            "",
            "### Recommendations",
        ])
        for rec in score_data["recommendations"]:
            lines.append(f"- {rec}")

        return "\n".join(lines)

    def format_weekly_report(self, report: Dict[str, Any]) -> str:
        """Format weekly report as markdown."""
        lines = [
            f"##  Weekly Report",
            f"**{report['week_start']} to {report['week_end']}**\n",
            "### Totals",
            f"-  Tasks Completed: {report['totals']['tasks_completed']}",
            f"-  Focus Time: {report['totals']['focus_time_minutes']} minutes",
            f"-  Pomodoros: {report['totals']['pomodoros']}",
            "",
            "### Daily Breakdown",
        ]

        for day, data in report["daily_breakdown"].items():
            day_name = datetime.fromisoformat(day).strftime("%A")
            lines.append(
                f"- **{day_name}**: {data['tasks_completed']} tasks, "
                f"{data['focus_time']}m focus"
            )

        return "\n".join(lines)
