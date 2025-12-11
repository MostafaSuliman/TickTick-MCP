"""
Smart MCP tools - Intelligent task views and scheduling suggestions.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GetTodayInput(BaseModel):
    """Input for getting today's tasks."""
    pass


class GetTomorrowInput(BaseModel):
    """Input for getting tomorrow's tasks."""
    pass


class GetOverdueInput(BaseModel):
    """Input for getting overdue tasks."""
    pass


class GetNext7DaysInput(BaseModel):
    """Input for getting next 7 days tasks."""
    pass


class SearchTasksInput(BaseModel):
    """Input for searching tasks."""
    query: str = Field(..., description="Search query (searches title, content, tags)")
    project_id: Optional[str] = Field(default=None, description="Filter by project")
    include_completed: bool = Field(default=False, description="Include completed tasks")


class GetNoDateTasksInput(BaseModel):
    """Input for getting unscheduled tasks."""
    pass


class GetHighPriorityInput(BaseModel):
    """Input for getting high priority tasks."""
    pass


class ScheduleDayInput(BaseModel):
    """Input for scheduling a day."""
    date: Optional[str] = Field(
        default=None,
        description="Date to schedule (YYYY-MM-DD, defaults to today)"
    )


class GetProductivitySummaryInput(BaseModel):
    """Input for getting productivity summary."""
    pass


def register_smart_tools(mcp, smart_service):
    """Register smart/intelligent task tools."""

    @mcp.tool(
        name="ticktick_get_today",
        annotations={
            "title": "Get Today's Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_today(params: GetTodayInput) -> str:
        """
        Get all tasks due today.

        Returns tasks sorted by priority, perfect for daily planning.
        """
        try:
            tasks = await smart_service.get_today_tasks()
            return smart_service.format_smart_view(tasks, "Today's Tasks 📅")
        except Exception as e:
            return f"**Error**: Failed to get today's tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_get_tomorrow",
        annotations={
            "title": "Get Tomorrow's Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_tomorrow(params: GetTomorrowInput) -> str:
        """
        Get all tasks due tomorrow.

        Helps with planning ahead.
        """
        try:
            tasks = await smart_service.get_tomorrow_tasks()
            return smart_service.format_smart_view(tasks, "Tomorrow's Tasks 📆")
        except Exception as e:
            return f"**Error**: Failed to get tomorrow's tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_get_overdue",
        annotations={
            "title": "Get Overdue Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_overdue(params: GetOverdueInput) -> str:
        """
        Get all overdue tasks (past due date, not completed).

        Important for task management and catching up.
        """
        try:
            tasks = await smart_service.get_overdue_tasks()
            if not tasks:
                return "## ✅ No Overdue Tasks\n\nCongratulations! You're all caught up!"
            return smart_service.format_smart_view(tasks, "⚠️ Overdue Tasks")
        except Exception as e:
            return f"**Error**: Failed to get overdue tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_get_next_7_days",
        annotations={
            "title": "Get Next 7 Days Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_next_7_days(params: GetNext7DaysInput) -> str:
        """
        Get tasks for the next 7 days, grouped by date.

        Perfect for weekly planning.
        """
        try:
            tasks_by_date = await smart_service.get_next_7_days_tasks()

            lines = ["## 📅 Next 7 Days\n"]

            for date_str, tasks in tasks_by_date.items():
                lines.append(f"### {date_str}")
                if tasks:
                    for task in tasks:
                        priority_emoji = {0: "⚪", 1: "🔵", 3: "🟡", 5: "🔴"}.get(task.priority, "⚪")
                        lines.append(f"- {priority_emoji} {task.title} (`{task.id}`)")
                else:
                    lines.append("- *(No tasks)*")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get next 7 days - {str(e)}"

    @mcp.tool(
        name="ticktick_search_tasks",
        annotations={
            "title": "Search Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def search_tasks(params: SearchTasksInput) -> str:
        """
        Search tasks by keyword in title, content, and tags.

        Results are ranked by relevance and priority.
        """
        try:
            tasks = await smart_service.search_tasks(
                query=params.query,
                project_id=params.project_id,
                include_completed=params.include_completed,
            )
            return smart_service.format_smart_view(
                tasks, f"🔍 Search Results for '{params.query}'"
            )
        except Exception as e:
            return f"**Error**: Search failed - {str(e)}"

    @mcp.tool(
        name="ticktick_get_unscheduled",
        annotations={
            "title": "Get Unscheduled Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_unscheduled(params: GetNoDateTasksInput) -> str:
        """
        Get tasks without any due date or start date.

        Useful for planning and scheduling unorganized tasks.
        """
        try:
            tasks = await smart_service.get_no_date_tasks()
            return smart_service.format_smart_view(tasks, "📭 Unscheduled Tasks")
        except Exception as e:
            return f"**Error**: Failed to get unscheduled tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_get_high_priority",
        annotations={
            "title": "Get High Priority Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_high_priority(params: GetHighPriorityInput) -> str:
        """
        Get all high priority (priority=5) tasks.

        Focus on what matters most.
        """
        try:
            tasks = await smart_service.get_high_priority_tasks()
            return smart_service.format_smart_view(tasks, "🔴 High Priority Tasks")
        except Exception as e:
            return f"**Error**: Failed to get high priority tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_schedule_day",
        annotations={
            "title": "AI Schedule Day",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def schedule_day(params: ScheduleDayInput) -> str:
        """
        Get AI-suggested schedule for a day.

        Organizes tasks into morning, afternoon, and evening blocks
        based on priority and workload.
        """
        try:
            schedule = await smart_service.schedule_day(params.date)
            return smart_service.format_schedule(schedule)
        except Exception as e:
            return f"**Error**: Failed to generate schedule - {str(e)}"

    @mcp.tool(
        name="ticktick_productivity_summary",
        annotations={
            "title": "Get Productivity Summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def productivity_summary(params: GetProductivitySummaryInput) -> str:
        """
        Get a productivity summary with actionable insights.

        Includes task counts, overdue status, and AI recommendations.
        """
        try:
            summary = await smart_service.get_productivity_summary()
            return smart_service.format_productivity_summary(summary)
        except Exception as e:
            return f"**Error**: Failed to get productivity summary - {str(e)}"
