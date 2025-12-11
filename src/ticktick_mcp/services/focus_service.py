"""
Focus/Pomodoro Service - Focus timer and productivity tracking (v2 API + WebSocket).
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..api.exceptions import ConfigurationError, WebSocketError
from ..models.focus import (
    FocusSession,
    FocusSessionCreate,
    FocusRecord,
    FocusStatus,
    FocusType,
    PomoSettings,
    FocusStats,
    FocusFilter,
    FocusWebSocketEvent,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class FocusService(BaseService[FocusSession]):
    """
    Service for Focus/Pomodoro timer operations.

    Note: Focus features are only available through the v2 API.
    Real-time timer updates require WebSocket connection.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)
        self._ws_connection = None
        self._event_handlers: List[Callable[[FocusWebSocketEvent], None]] = []
        self._current_session: Optional[FocusSession] = None

    def _require_v2(self) -> None:
        """Raise error if v2 is not available."""
        if not self.is_v2_available:
            raise ConfigurationError(
                "Focus operations require v2 API authentication. "
                "Use login_v2(username, password) to authenticate."
            )

    # =========================================================================
    # Focus Records (Completed Sessions)
    # =========================================================================

    async def get_records(
        self,
        filter_params: Optional[FocusFilter] = None,
    ) -> List[FocusRecord]:
        """
        Get focus session records.

        Args:
            filter_params: Optional filter parameters

        Returns:
            List of FocusRecord objects
        """
        self._require_v2()

        params = {}
        if filter_params:
            if filter_params.from_date:
                params["from"] = filter_params.from_date
            if filter_params.to_date:
                params["to"] = filter_params.to_date
            if filter_params.project_id:
                params["projectId"] = filter_params.project_id

        url = Endpoints.Focus.records()
        data = await self.client.get(url, version=APIVersion.V2, params=params)

        records = [FocusRecord(**r) for r in data] if isinstance(data, list) else []

        # Apply additional filters
        if filter_params:
            if filter_params.task_id:
                records = [r for r in records if r.task_id == filter_params.task_id]
            if filter_params.focus_type:
                records = [r for r in records if r.focus_type == filter_params.focus_type]
            if filter_params.min_duration:
                records = [r for r in records if r.duration >= filter_params.min_duration]

        return records

    async def save_record(
        self,
        duration: int,
        focus_type: FocusType = FocusType.POMODORO,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        note: Optional[str] = None,
        start_time: Optional[str] = None,
    ) -> FocusRecord:
        """
        Save a completed focus session record.

        Args:
            duration: Focus duration in seconds
            focus_type: Type of focus session
            task_id: Associated task ID
            project_id: Associated project ID
            note: Session note
            start_time: When session started (defaults to duration ago)

        Returns:
            Created FocusRecord
        """
        self._require_v2()

        now = datetime.now()
        if not start_time:
            start = now - timedelta(seconds=duration)
            start_time = start.isoformat()

        payload = {
            "duration": duration,
            "focusType": focus_type.value,
            "startTime": start_time,
            "endTime": now.isoformat(),
        }

        if task_id:
            payload["taskId"] = task_id
        if project_id:
            payload["projectId"] = project_id
        if note:
            payload["note"] = note

        url = Endpoints.Focus.save()
        data = await self.client.post(url, version=APIVersion.V2, data=payload)
        return FocusRecord(**data)

    async def delete_record(self, record_id: str) -> bool:
        """
        Delete a focus record.

        Args:
            record_id: Record ID to delete

        Returns:
            True if successful
        """
        self._require_v2()

        url = f"{Endpoints.BASE_V2}/focus/{record_id}"
        await self.client.delete(url, version=APIVersion.V2)
        return True

    # =========================================================================
    # Pomodoro Settings
    # =========================================================================

    async def get_settings(self) -> PomoSettings:
        """
        Get Pomodoro timer settings.

        Returns:
            PomoSettings object
        """
        self._require_v2()

        url = Endpoints.Focus.settings()
        data = await self.client.get(url, version=APIVersion.V2)
        return PomoSettings(**data)

    async def update_settings(self, settings: PomoSettings) -> PomoSettings:
        """
        Update Pomodoro timer settings.

        Args:
            settings: New settings

        Returns:
            Updated PomoSettings
        """
        self._require_v2()

        payload = settings.model_dump(by_alias=True, exclude_none=True)
        url = Endpoints.Focus.settings()
        data = await self.client.post(url, version=APIVersion.V2, data=payload)
        return PomoSettings(**data)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> FocusStats:
        """
        Get focus statistics.

        Args:
            from_date: Start date for stats
            to_date: End date for stats

        Returns:
            FocusStats object
        """
        self._require_v2()

        # Get records and calculate stats
        filter_params = FocusFilter(from_date=from_date, to_date=to_date)
        records = await self.get_records(filter_params)

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        # Initialize counters
        stats = {
            "today_focus_time": 0,
            "today_pomo_count": 0,
            "week_focus_time": 0,
            "week_pomo_count": 0,
            "month_focus_time": 0,
            "month_pomo_count": 0,
            "total_focus_time": 0,
            "total_pomo_count": 0,
        }

        project_times: Dict[str, int] = {}
        daily_times: Dict[int, int] = {h: 0 for h in range(24)}

        for record in records:
            try:
                record_date = datetime.fromisoformat(
                    record.start_time.replace("Z", "+00:00")
                ).date()
                record_hour = datetime.fromisoformat(
                    record.start_time.replace("Z", "+00:00")
                ).hour

                # Total
                stats["total_focus_time"] += record.duration
                if record.focus_type == FocusType.POMODORO:
                    stats["total_pomo_count"] += 1

                # Today
                if record_date == today:
                    stats["today_focus_time"] += record.duration
                    if record.focus_type == FocusType.POMODORO:
                        stats["today_pomo_count"] += 1

                # Week
                if record_date >= week_start:
                    stats["week_focus_time"] += record.duration
                    if record.focus_type == FocusType.POMODORO:
                        stats["week_pomo_count"] += 1

                # Month
                if record_date >= month_start:
                    stats["month_focus_time"] += record.duration
                    if record.focus_type == FocusType.POMODORO:
                        stats["month_pomo_count"] += 1

                # Project distribution
                if record.project_id:
                    project_times[record.project_id] = (
                        project_times.get(record.project_id, 0) + record.duration
                    )

                # Hourly distribution
                daily_times[record_hour] += record.duration

            except Exception as e:
                logger.warning(f"Error processing record: {e}")

        return FocusStats(
            **stats,
            daily_distribution=daily_times,
            project_distribution=project_times,
        )

    async def get_today_stats(self) -> Dict[str, Any]:
        """
        Get today's focus statistics.

        Returns:
            Dict with today's stats
        """
        today = datetime.now().strftime("%Y-%m-%d")
        stats = await self.get_stats(from_date=today, to_date=today)

        settings = await self.get_settings()
        target = settings.daily_pomo_target

        return {
            "focus_time_minutes": stats.today_focus_time // 60,
            "pomo_count": stats.today_pomo_count,
            "target": target,
            "progress_percent": min(100, (stats.today_pomo_count / target) * 100) if target else 0,
            "remaining": max(0, target - stats.today_pomo_count),
        }

    # =========================================================================
    # WebSocket Operations (Real-time Timer)
    # =========================================================================

    async def connect_websocket(self) -> None:
        """
        Connect to TickTick WebSocket for real-time timer updates.

        Note: This is an experimental feature based on reverse-engineered protocol.
        """
        self._require_v2()

        try:
            import websockets
        except ImportError:
            raise WebSocketError(
                "websockets library required for real-time features. "
                "Install with: pip install websockets"
            )

        ws_url = Endpoints.WEBSOCKET_URL
        logger.info(f"Connecting to WebSocket: {ws_url}")

        try:
            self._ws_connection = await websockets.connect(ws_url)
            logger.info("WebSocket connected")

            # Start listener task
            asyncio.create_task(self._ws_listener())

        except Exception as e:
            raise WebSocketError(f"Failed to connect WebSocket: {e}")

    async def disconnect_websocket(self) -> None:
        """Disconnect WebSocket connection."""
        if self._ws_connection:
            await self._ws_connection.close()
            self._ws_connection = None
            logger.info("WebSocket disconnected")

    async def _ws_listener(self) -> None:
        """Listen for WebSocket messages."""
        if not self._ws_connection:
            return

        try:
            async for message in self._ws_connection:
                try:
                    data = json.loads(message)
                    event = FocusWebSocketEvent(**data)

                    # Update current session state
                    self._handle_ws_event(event)

                    # Notify handlers
                    for handler in self._event_handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"Event handler error: {e}")

                except json.JSONDecodeError:
                    logger.warning(f"Invalid WebSocket message: {message}")

        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")
            self._ws_connection = None

    def _handle_ws_event(self, event: FocusWebSocketEvent) -> None:
        """Handle WebSocket event internally."""
        event_type = event.event.lower()

        if event_type == "start":
            self._current_session = FocusSession(
                status=FocusStatus.RUNNING,
                id=event.session_id,
            )
        elif event_type == "pause":
            if self._current_session:
                self._current_session.status = FocusStatus.PAUSED
        elif event_type == "continue":
            if self._current_session:
                self._current_session.status = FocusStatus.RUNNING
        elif event_type in ("startbreak", "endbreak"):
            if self._current_session:
                self._current_session.status = FocusStatus.BREAK
        elif event_type == "exit":
            self._current_session = None

    def add_event_handler(
        self,
        handler: Callable[[FocusWebSocketEvent], None],
    ) -> None:
        """
        Add a handler for WebSocket events.

        Args:
            handler: Callback function for events
        """
        self._event_handlers.append(handler)

    def remove_event_handler(
        self,
        handler: Callable[[FocusWebSocketEvent], None],
    ) -> None:
        """Remove an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    @property
    def current_session(self) -> Optional[FocusSession]:
        """Get current focus session (if any)."""
        return self._current_session

    @property
    def is_focus_active(self) -> bool:
        """Check if a focus session is currently active."""
        return self._current_session is not None and self._current_session.status in (
            FocusStatus.RUNNING,
            FocusStatus.PAUSED,
        )

    # =========================================================================
    # Manual Session Management (No WebSocket)
    # =========================================================================

    def start_local_session(
        self,
        duration: int = 1500,
        focus_type: FocusType = FocusType.POMODORO,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> FocusSession:
        """
        Start a local focus session (without WebSocket).

        The session state is tracked locally and can be saved when completed.

        Args:
            duration: Duration in seconds
            focus_type: Type of session
            task_id: Associated task
            project_id: Associated project

        Returns:
            FocusSession object
        """
        self._current_session = FocusSession(
            focus_type=focus_type,
            duration=duration,
            status=FocusStatus.RUNNING,
            task_id=task_id,
            project_id=project_id,
            start_time=datetime.now().isoformat(),
            elapsed=0,
            remaining=duration,
        )
        return self._current_session

    def pause_local_session(self) -> Optional[FocusSession]:
        """Pause the current local session."""
        if self._current_session:
            self._current_session.status = FocusStatus.PAUSED
            self._current_session.pause_count += 1
        return self._current_session

    def resume_local_session(self) -> Optional[FocusSession]:
        """Resume the current local session."""
        if self._current_session:
            self._current_session.status = FocusStatus.RUNNING
        return self._current_session

    async def complete_local_session(self) -> Optional[FocusRecord]:
        """
        Complete and save the current local session.

        Returns:
            FocusRecord if session was saved
        """
        if not self._current_session:
            return None

        session = self._current_session
        self._current_session = None

        # Save to TickTick
        return await self.save_record(
            duration=session.elapsed or session.duration,
            focus_type=session.focus_type,
            task_id=session.task_id,
            project_id=session.project_id,
            start_time=session.start_time,
        )

    def cancel_local_session(self) -> None:
        """Cancel the current local session without saving."""
        self._current_session = None

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_record(self, record: FocusRecord) -> str:
        """Format a single focus record as markdown."""
        duration_min = record.duration // 60
        lines = [
            f"- **{record.focus_type.value}** - {duration_min} minutes",
            f"  - Started: {record.start_time[:16]}",
        ]

        if record.task_title:
            lines.append(f"  - Task: {record.task_title}")
        if record.note:
            lines.append(f"  - Note: {record.note}")

        return "\n".join(lines)

    def format_record_list(
        self,
        records: List[FocusRecord],
        title: str = "Focus Sessions",
    ) -> str:
        """Format focus records as markdown."""
        if not records:
            return f"##  {title}\n\nNo focus sessions found."

        total_time = sum(r.duration for r in records)
        total_min = total_time // 60
        total_hours = total_min // 60
        remaining_min = total_min % 60

        lines = [
            f"##  {title} ({len(records)} sessions)\n",
            f"**Total Time**: {total_hours}h {remaining_min}m\n",
        ]

        # Group by date
        by_date: Dict[str, List[FocusRecord]] = {}
        for record in records:
            date_str = record.start_time[:10]
            if date_str not in by_date:
                by_date[date_str] = []
            by_date[date_str].append(record)

        for date_str in sorted(by_date.keys(), reverse=True):
            lines.append(f"\n### {date_str}\n")
            for record in by_date[date_str]:
                lines.append(self.format_record(record))

        return "\n".join(lines)

    def format_stats(self, stats: FocusStats) -> str:
        """Format focus statistics as markdown."""
        def fmt_time(seconds: int) -> str:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if hours:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"

        lines = [
            "##  Focus Statistics\n",
            "### Today",
            f"- Focus Time: {fmt_time(stats.today_focus_time)}",
            f"- Pomodoros: {stats.today_pomo_count}",
            "",
            "### This Week",
            f"- Focus Time: {fmt_time(stats.week_focus_time)}",
            f"- Pomodoros: {stats.week_pomo_count}",
            "",
            "### This Month",
            f"- Focus Time: {fmt_time(stats.month_focus_time)}",
            f"- Pomodoros: {stats.month_pomo_count}",
            "",
            "### All Time",
            f"- Focus Time: {fmt_time(stats.total_focus_time)}",
            f"- Pomodoros: {stats.total_pomo_count}",
        ]

        if stats.current_streak:
            lines.extend([
                "",
                "### Streaks",
                f"-  Current: {stats.current_streak} days",
                f"-  Best: {stats.best_streak} days",
            ])

        return "\n".join(lines)

    def format_settings(self, settings: PomoSettings) -> str:
        """Format Pomodoro settings as markdown."""
        lines = [
            "##  Pomodoro Settings\n",
            "### Duration",
            f"- Focus: {settings.pomo_duration} minutes",
            f"- Short Break: {settings.short_break} minutes",
            f"- Long Break: {settings.long_break} minutes",
            f"- Long Break After: {settings.long_break_interval} pomodoros",
            "",
            "### Behavior",
            f"- Auto-start Break: {'Yes' if settings.auto_start_break else 'No'}",
            f"- Auto-start Pomo: {'Yes' if settings.auto_start_pomo else 'No'}",
            f"- Max Pauses: {settings.max_pause_count}",
            "",
            "### Goals",
            f"- Daily Target: {settings.daily_pomo_target} pomodoros",
        ]

        return "\n".join(lines)
