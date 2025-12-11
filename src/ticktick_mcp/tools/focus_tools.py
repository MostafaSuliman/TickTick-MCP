"""
Focus/Pomodoro MCP tools - Focus timer and productivity tracking (v2 API only).
"""

from typing import Optional
from pydantic import BaseModel, Field


class StartPomodoroInput(BaseModel):
    """Input for starting a Pomodoro session."""
    duration_minutes: int = Field(
        default=25,
        description="Focus duration in minutes",
        ge=1,
        le=240
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Link to a task (optional)"
    )
    task_title: Optional[str] = Field(
        default=None,
        description="Task title to display (if no task_id)"
    )


class StartStopwatchInput(BaseModel):
    """Input for starting a stopwatch session."""
    task_id: Optional[str] = Field(
        default=None,
        description="Link to a task (optional)"
    )
    task_title: Optional[str] = Field(
        default=None,
        description="Task title to display (if no task_id)"
    )


class StopFocusInput(BaseModel):
    """Input for stopping a focus session."""
    save: bool = Field(
        default=True,
        description="Save the focus record"
    )


class GetFocusRecordsInput(BaseModel):
    """Input for getting focus records."""
    from_date: Optional[str] = Field(
        default=None,
        description="Start date (YYYY-MM-DD)"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM-DD)"
    )
    focus_type: Optional[str] = Field(
        default=None,
        description="Filter by type: pomo (pomodoro) or stopwatch"
    )


class GetTodayFocusInput(BaseModel):
    """Input for getting today's focus stats."""
    pass


class GetFocusSettingsInput(BaseModel):
    """Input for getting focus settings."""
    pass


class UpdateFocusSettingsInput(BaseModel):
    """Input for updating focus settings."""
    pomo_duration: Optional[int] = Field(
        default=None,
        description="Pomodoro duration in minutes",
        ge=1,
        le=240
    )
    short_break: Optional[int] = Field(
        default=None,
        description="Short break duration in minutes",
        ge=1,
        le=60
    )
    long_break: Optional[int] = Field(
        default=None,
        description="Long break duration in minutes",
        ge=1,
        le=120
    )
    long_break_interval: Optional[int] = Field(
        default=None,
        description="Pomodoros before long break",
        ge=1,
        le=10
    )
    daily_pomo_target: Optional[int] = Field(
        default=None,
        description="Daily pomodoro goal",
        ge=1,
        le=50
    )
    auto_start_break: Optional[bool] = Field(
        default=None,
        description="Auto-start break after work"
    )
    auto_start_pomo: Optional[bool] = Field(
        default=None,
        description="Auto-start work after break"
    )


class DeleteFocusRecordInput(BaseModel):
    """Input for deleting a focus record."""
    record_id: str = Field(..., description="Focus record ID to delete")


def register_focus_tools(mcp, focus_service):
    """Register focus/pomodoro tools (v2 API only)."""

    @mcp.tool(
        name="ticktick_start_pomodoro",
        annotations={
            "title": "Start Pomodoro Timer",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def start_pomodoro(params: StartPomodoroInput) -> str:
        """
        Start a Pomodoro focus session.

        The classic Pomodoro technique with customizable duration.
        Can be linked to a specific task.
        Requires v2 API authentication.
        """
        from ..models.focus import FocusType

        try:
            duration_seconds = params.duration_minutes * 60
            session = focus_service.start_local_session(
                duration=duration_seconds,
                focus_type=FocusType.POMODORO,
                task_id=params.task_id,
            )
            return f"""## Pomodoro Started

- **Duration**: {params.duration_minutes} minutes
- **Task**: {params.task_title or params.task_id or 'No task linked'}
- **Status**: Focus session in progress

Stay focused! Use `ticktick_stop_focus` to end the session.
"""
        except Exception as e:
            return f"**Error**: Failed to start pomodoro - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_start_stopwatch",
        annotations={
            "title": "Start Stopwatch Timer",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def start_stopwatch(params: StartStopwatchInput) -> str:
        """
        Start a stopwatch focus session.

        Open-ended focus tracking without a fixed duration.
        Requires v2 API authentication.
        """
        from ..models.focus import FocusType

        try:
            session = focus_service.start_local_session(
                duration=0,  # Stopwatch has no preset duration
                focus_type=FocusType.STOPWATCH,
                task_id=params.task_id,
            )
            return f"""## Stopwatch Started

- **Task**: {params.task_title or params.task_id or 'No task linked'}
- **Status**: Stopwatch running

Time is being tracked. Use `ticktick_stop_focus` to end the session.
"""
        except Exception as e:
            return f"**Error**: Failed to start stopwatch - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_stop_focus",
        annotations={
            "title": "Stop Focus Session",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def stop_focus(params: StopFocusInput) -> str:
        """
        Stop the current focus session.

        Optionally save or discard the focus record.
        Requires v2 API authentication.
        """
        try:
            if params.save:
                record = await focus_service.complete_local_session()
                if record:
                    duration = record.duration // 60
                    return f"""## Focus Session Ended

- **Duration**: {duration} minutes
- **Saved**: Yes
- **Type**: {record.focus_type.value}

Great work! Focus record has been saved.
"""
                else:
                    return "## No Active Session\n\nNo focus session was running."
            else:
                focus_service.cancel_local_session()
                return "## Focus Session Discarded\n\nThe focus session was ended without saving."
        except Exception as e:
            return f"**Error**: Failed to stop focus - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_focus_records",
        annotations={
            "title": "Get Focus Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_focus_records(params: GetFocusRecordsInput) -> str:
        """
        Get focus session history.

        Filter by date range and focus type (pomodoro/stopwatch).
        Requires v2 API authentication.
        """
        from ..models.focus import FocusFilter, FocusType

        filter_data = FocusFilter(
            from_date=params.from_date,
            to_date=params.to_date,
            focus_type=FocusType(params.focus_type) if params.focus_type else None,
        )

        try:
            records = await focus_service.get_records(filter_data)
            return focus_service.format_record_list(records)
        except Exception as e:
            return f"**Error**: Failed to get focus records - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_today_focus",
        annotations={
            "title": "Get Today's Focus Stats",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_today_focus(params: GetTodayFocusInput) -> str:
        """
        Get today's focus time statistics.

        Shows total focus time, pomodoro count, and progress toward daily goal.
        Requires v2 API authentication.
        """
        try:
            stats = await focus_service.get_today_stats()
            lines = [
                "## Today's Focus Stats\n",
                f"- **Focus Time**: {stats.get('focus_time_minutes', 0)} minutes",
                f"- **Pomodoros**: {stats.get('pomo_count', 0)}/{stats.get('target', 8)}",
                f"- **Progress**: {stats.get('progress_percent', 0):.0f}%",
                f"- **Remaining**: {stats.get('remaining', 0)} pomodoros to reach goal",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get today's stats - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_focus_settings",
        annotations={
            "title": "Get Focus Settings",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_focus_settings(params: GetFocusSettingsInput) -> str:
        """
        Get current Pomodoro/focus settings.

        Shows work duration, break times, and daily goals.
        Requires v2 API authentication.
        """
        try:
            settings = await focus_service.get_settings()
            return focus_service.format_settings(settings)
        except Exception as e:
            return f"**Error**: Failed to get settings - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_update_focus_settings",
        annotations={
            "title": "Update Focus Settings",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_focus_settings(params: UpdateFocusSettingsInput) -> str:
        """
        Update Pomodoro/focus settings.

        Customize work duration, breaks, and automation preferences.
        Requires v2 API authentication.
        """
        from ..models.focus import PomoSettings

        settings_data = PomoSettings(
            pomo_duration=params.pomo_duration,
            short_break=params.short_break,
            long_break=params.long_break,
            long_break_interval=params.long_break_interval,
            daily_pomo_target=params.daily_pomo_target,
            auto_start_break=params.auto_start_break,
            auto_start_pomo=params.auto_start_pomo,
        )

        try:
            settings = await focus_service.update_settings(settings_data)
            return f"""## Focus Settings Updated

{focus_service.format_settings(settings)}
"""
        except Exception as e:
            return f"**Error**: Failed to update settings - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_delete_focus_record",
        annotations={
            "title": "Delete Focus Record",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_focus_record(params: DeleteFocusRecordInput) -> str:
        """
        Delete a focus record.

        Warning: This cannot be undone.
        Requires v2 API authentication.
        """
        try:
            await focus_service.delete_record(params.record_id)
            return f"## Focus Record Deleted\n\nRecord `{params.record_id}` has been deleted."
        except Exception as e:
            return f"**Error**: Failed to delete record - {str(e)}\n\n_Note: This feature requires v2 API authentication._"
