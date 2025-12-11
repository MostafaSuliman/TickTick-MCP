"""
User MCP tools - User profile and settings management.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GetProfileInput(BaseModel):
    """Input for getting user profile."""
    pass


class GetInboxIdInput(BaseModel):
    """Input for getting inbox ID."""
    pass


class GetTimezoneInput(BaseModel):
    """Input for getting timezone."""
    pass


class GetSettingsInput(BaseModel):
    """Input for getting user settings."""
    pass


class UpdateSettingsInput(BaseModel):
    """Input for updating settings."""
    settings: Dict[str, Any] = Field(..., description="Settings to update")


def register_user_tools(mcp, user_service):
    """Register user profile and settings tools."""

    @mcp.tool(
        name="ticktick_get_profile",
        annotations={
            "title": "Get User Profile",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_profile(params: GetProfileInput) -> str:
        """
        Get user profile information.

        Includes inbox ID, user ID, and timezone.
        Requires v2 API authentication.
        """
        try:
            profile = await user_service.get_profile()
            return user_service.format_profile(profile)
        except Exception as e:
            return f"**Error**: Failed to get profile - {str(e)}"

    @mcp.tool(
        name="ticktick_get_inbox_id",
        annotations={
            "title": "Get Inbox ID",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_inbox_id(params: GetInboxIdInput) -> str:
        """
        Get the inbox project ID.

        The inbox has a special ID needed for creating tasks in the inbox.
        Requires v2 API authentication.
        """
        try:
            inbox_id = await user_service.get_inbox_id()
            if inbox_id:
                return f"""## 📥 Inbox ID

Your inbox project ID is: `{inbox_id}`

Use this ID when creating tasks in your inbox.
"""
            else:
                return "## ⚠️ Could Not Get Inbox ID\n\nMake sure you're authenticated with v2 API (username/password login)."
        except Exception as e:
            return f"**Error**: Failed to get inbox ID - {str(e)}"

    @mcp.tool(
        name="ticktick_get_timezone",
        annotations={
            "title": "Get User Timezone",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_timezone(params: GetTimezoneInput) -> str:
        """
        Get user's configured time zone.

        Useful for scheduling tasks in the correct timezone.
        """
        try:
            tz = await user_service.get_timezone()
            if tz:
                return f"## 🌍 Time Zone\n\nYour configured timezone is: **{tz}**"
            else:
                return "## ⚠️ Could Not Get Timezone\n\nMake sure you're authenticated."
        except Exception as e:
            return f"**Error**: Failed to get timezone - {str(e)}"

    @mcp.tool(
        name="ticktick_get_settings",
        annotations={
            "title": "Get User Settings",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_settings(params: GetSettingsInput) -> str:
        """
        Get user settings from TickTick.

        Requires v2 API authentication.
        """
        try:
            settings = await user_service.get_settings()
            return user_service.format_settings(settings)
        except Exception as e:
            return f"**Error**: Failed to get settings - {str(e)}"

    @mcp.tool(
        name="ticktick_update_settings",
        annotations={
            "title": "Update User Settings",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_settings(params: UpdateSettingsInput) -> str:
        """
        Update user settings in TickTick.

        Requires v2 API authentication.
        """
        try:
            result = await user_service.update_settings(params.settings)
            if "error" in result:
                return f"**Error**: {result['error']}"
            return f"## ✅ Settings Updated\n\nSettings have been updated successfully."
        except Exception as e:
            return f"**Error**: Failed to update settings - {str(e)}"
