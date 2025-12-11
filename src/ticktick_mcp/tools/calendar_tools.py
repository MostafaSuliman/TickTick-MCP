"""
Calendar MCP tools - Calendar event management.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GetEventsInput(BaseModel):
    """Input for getting calendar events."""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")


class GetTodayEventsInput(BaseModel):
    """Input for getting today's events."""
    pass


class GetWeekEventsInput(BaseModel):
    """Input for getting this week's events."""
    pass


class GetCalendarsInput(BaseModel):
    """Input for listing connected calendars."""
    pass


def register_calendar_tools(mcp, calendar_service):
    """Register calendar management tools."""

    @mcp.tool(
        name="ticktick_calendar_events",
        annotations={
            "title": "Get Calendar Events",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_events(params: GetEventsInput) -> str:
        """
        Get calendar events within a date range.

        Requires v2 API authentication.
        """
        try:
            events = await calendar_service.get_events(
                start_date=params.start_date,
                end_date=params.end_date,
            )
            return calendar_service.format_events(
                events,
                f"Events ({params.start_date} to {params.end_date})"
            )
        except Exception as e:
            return f"**Error**: Failed to get events - {str(e)}"

    @mcp.tool(
        name="ticktick_calendar_today",
        annotations={
            "title": "Get Today's Calendar Events",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_today_events(params: GetTodayEventsInput) -> str:
        """
        Get calendar events for today.

        Requires v2 API authentication.
        """
        try:
            events = await calendar_service.get_today_events()
            return calendar_service.format_events(events, "Today's Events")
        except Exception as e:
            return f"**Error**: Failed to get today's events - {str(e)}"

    @mcp.tool(
        name="ticktick_calendar_week",
        annotations={
            "title": "Get This Week's Calendar Events",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_week_events(params: GetWeekEventsInput) -> str:
        """
        Get calendar events for the current week.

        Requires v2 API authentication.
        """
        try:
            events = await calendar_service.get_week_events()
            return calendar_service.format_events(events, "This Week's Events")
        except Exception as e:
            return f"**Error**: Failed to get week's events - {str(e)}"

    @mcp.tool(
        name="ticktick_calendars_list",
        annotations={
            "title": "List Connected Calendars",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_calendars(params: GetCalendarsInput) -> str:
        """
        List all connected calendars.

        Requires v2 API authentication.
        """
        try:
            calendars = await calendar_service.get_calendars()
            return calendar_service.format_calendars(calendars)
        except Exception as e:
            return f"**Error**: Failed to list calendars - {str(e)}"
