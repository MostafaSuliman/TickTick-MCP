"""
Calendar Service - Calendar event management and integration.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from .base_service import BaseService

logger = logging.getLogger(__name__)


class CalendarEvent:
    """Represents a calendar event."""

    def __init__(
        self,
        id: str,
        title: str,
        start_date: str,
        end_date: Optional[str] = None,
        is_all_day: bool = False,
        calendar_id: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.is_all_day = is_all_day
        self.calendar_id = calendar_id
        self.description = description
        self.location = location
        self.extra = kwargs


class CalendarService(BaseService[CalendarEvent]):
    """
    Service for calendar event management.

    Provides:
    - Calendar event listing
    - Event retrieval by date range
    - Calendar sync status
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)

    # =========================================================================
    # Calendar Events
    # =========================================================================

    async def get_events(
        self,
        start_date: str,
        end_date: str,
    ) -> List[CalendarEvent]:
        """
        Get calendar events within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of calendar events
        """
        if not self.is_v2_available:
            logger.warning("Calendar API requires v2 authentication")
            return []

        try:
            url = Endpoints.Calendar.events()
            params = {
                "startDate": start_date,
                "endDate": end_date,
            }
            data = await self.client.get(url, version=APIVersion.V2, params=params)

            events = []
            for item in data if isinstance(data, list) else []:
                events.append(CalendarEvent(
                    id=item.get("id", ""),
                    title=item.get("title", "Untitled"),
                    start_date=item.get("startDate", ""),
                    end_date=item.get("endDate"),
                    is_all_day=item.get("isAllDay", False),
                    calendar_id=item.get("calendarId"),
                    description=item.get("content"),
                    location=item.get("location"),
                ))
            return events
        except Exception as e:
            logger.error(f"Failed to get calendar events: {e}")
            return []

    async def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get list of connected calendars.

        Returns:
            List of calendar configurations
        """
        if not self.is_v2_available:
            return []

        try:
            url = Endpoints.Calendar.calendars()
            data = await self.client.get(url, version=APIVersion.V2)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to get calendars: {e}")
            return []

    async def get_today_events(self) -> List[CalendarEvent]:
        """
        Get calendar events for today.

        Returns:
            List of today's events
        """
        today = datetime.now(timezone.utc).date().isoformat()
        return await self.get_events(today, today)

    async def get_week_events(self) -> List[CalendarEvent]:
        """
        Get calendar events for the current week.

        Returns:
            List of this week's events
        """
        today = datetime.now(timezone.utc).date()
        week_end = today + timedelta(days=7)
        return await self.get_events(today.isoformat(), week_end.isoformat())

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_events(
        self,
        events: List[CalendarEvent],
        title: str = "Calendar Events"
    ) -> str:
        """Format events as markdown."""
        if not events:
            return f"## 📅 {title}\n\nNo events found."

        lines = [f"## 📅 {title} ({len(events)} events)\n"]

        for event in events:
            time_info = "All day" if event.is_all_day else event.start_date
            lines.append(f"### {event.title}")
            lines.append(f"- **Time**: {time_info}")
            if event.end_date and not event.is_all_day:
                lines.append(f"- **End**: {event.end_date}")
            if event.location:
                lines.append(f"- **Location**: {event.location}")
            if event.description:
                lines.append(f"- **Description**: {event.description}")
            lines.append(f"- **ID**: `{event.id}`")
            lines.append("")

        return "\n".join(lines)

    def format_calendars(self, calendars: List[Dict[str, Any]]) -> str:
        """Format calendar list as markdown."""
        if not calendars:
            return "## 📆 Calendars\n\nNo calendars connected."

        lines = ["## 📆 Connected Calendars\n"]

        for cal in calendars:
            name = cal.get("name", "Unnamed")
            cal_id = cal.get("id", "")
            enabled = "✅" if cal.get("enabled", True) else "❌"
            lines.append(f"- {enabled} **{name}** (`{cal_id}`)")

        return "\n".join(lines)
