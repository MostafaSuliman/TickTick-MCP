"""
Statistics MCP tools - Productivity analytics and reporting.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GetOverviewInput(BaseModel):
    """Input for getting productivity overview."""
    pass


class GetDailySummaryInput(BaseModel):
    """Input for daily summary."""
    date: Optional[str] = Field(
        default=None,
        description="Date to summarize (YYYY-MM-DD, defaults to today)"
    )


class GetWeeklyReportInput(BaseModel):
    """Input for weekly report."""
    week_offset: int = Field(
        default=0,
        description="Week offset: 0 for current week, -1 for last week, etc."
    )


class GetProductivityScoreInput(BaseModel):
    """Input for productivity score."""
    pass


class GetTaskAnalyticsInput(BaseModel):
    """Input for task analytics."""
    pass


def register_statistics_tools(mcp, statistics_service):
    """Register statistics and analytics tools."""

    @mcp.tool(
        name="ticktick_get_overview",
        annotations={
            "title": "Get Productivity Overview",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_overview(params: GetOverviewInput) -> str:
        """
        Get today's productivity overview.

        Includes task status, habit progress, and focus statistics.
        Extended features require v2 API authentication.
        """
        try:
            overview = await statistics_service.get_overview()
            return statistics_service.format_overview(overview)
        except Exception as e:
            return f"**Error**: Failed to get overview - {str(e)}"

    @mcp.tool(
        name="ticktick_get_daily_summary",
        annotations={
            "title": "Get Daily Summary",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_daily_summary(params: GetDailySummaryInput) -> str:
        """
        Get detailed summary for a specific day.

        Shows tasks completed, habits done, and focus time.
        Requires v2 API for complete data.
        """
        try:
            summary = await statistics_service.get_daily_summary(params.date)

            lines = [f"## Daily Summary - {summary['date']}\n"]

            # Tasks completed
            tasks_done = summary.get("tasks_completed", [])
            lines.append(f"### Tasks Completed: {len(tasks_done)}")
            if tasks_done:
                for task in tasks_done[:10]:  # Show max 10
                    lines.append(f"- ✅ {task['title']}")
                if len(tasks_done) > 10:
                    lines.append(f"- ... and {len(tasks_done) - 10} more")
            lines.append("")

            # Focus time
            focus_time = summary.get("total_focus_time", 0)
            sessions = summary.get("focus_sessions", [])
            lines.append(f"### Focus Time: {focus_time} minutes")
            if sessions:
                lines.append(f"- Sessions: {len(sessions)}")
                for session in sessions[:5]:
                    lines.append(f"  - {session['duration_minutes']}m ({session['type']})")
            lines.append("")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get daily summary - {str(e)}\n\n_Note: Full summary requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_weekly_report",
        annotations={
            "title": "Get Weekly Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_weekly_report(params: GetWeeklyReportInput) -> str:
        """
        Get weekly productivity report.

        Includes daily breakdown, totals, and trends.
        Requires v2 API for complete data.
        """
        try:
            report = await statistics_service.get_weekly_report(params.week_offset)
            return statistics_service.format_weekly_report(report)
        except Exception as e:
            return f"**Error**: Failed to get weekly report - {str(e)}\n\n_Note: Full report requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_productivity_score",
        annotations={
            "title": "Get Productivity Score",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_productivity_score(params: GetProductivityScoreInput) -> str:
        """
        Calculate your productivity score.

        Score is based on task completion, habit consistency, and focus time.
        Includes personalized recommendations.
        Extended metrics require v2 API authentication.
        """
        try:
            score_data = await statistics_service.get_productivity_score()
            return statistics_service.format_productivity_score(score_data)
        except Exception as e:
            return f"**Error**: Failed to calculate productivity score - {str(e)}"

    @mcp.tool(
        name="ticktick_get_task_analytics",
        annotations={
            "title": "Get Task Analytics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_task_analytics(params: GetTaskAnalyticsInput) -> str:
        """
        Get detailed task analytics.

        Shows priority distribution, due date analysis, and tag usage.
        """
        try:
            analytics = await statistics_service.get_task_analytics()

            lines = ["## Task Analytics\n"]

            # Total pending
            lines.append(f"### Total Pending Tasks: {analytics['total_pending']}\n")

            # Priority distribution
            lines.append("### Priority Distribution")
            priority = analytics["priority_distribution"]
            lines.append(f"- 🔴 High: {priority['high']}")
            lines.append(f"- 🟡 Medium: {priority['medium']}")
            lines.append(f"- 🔵 Low: {priority['low']}")
            lines.append(f"- ⚪ None: {priority['none']}")
            lines.append("")

            # Due date analysis
            lines.append("### Due Date Analysis")
            due = analytics["due_date_analysis"]
            lines.append(f"- ⚠️ Overdue: {due['overdue']}")
            lines.append(f"- 📅 Today: {due['today']}")
            lines.append(f"- 📆 This Week: {due['this_week']}")
            lines.append(f"- 🗓️ Later: {due['later']}")
            lines.append(f"- ❓ No Date: {due['no_date']}")
            lines.append("")

            # Top tags
            if analytics.get("top_tags"):
                lines.append("### Top Tags")
                for tag, count in analytics["top_tags"].items():
                    lines.append(f"- `{tag}`: {count} tasks")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get task analytics - {str(e)}"
