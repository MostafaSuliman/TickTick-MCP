"""
User Service - User profile and settings management.
"""

import logging
from typing import Any, Dict, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from .base_service import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService[Dict[str, Any]]):
    """
    Service for user profile and settings management.

    Provides:
    - User profile information
    - Settings retrieval and updates
    - Inbox ID retrieval
    - Time zone information
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)
        self._user_data: Optional[Dict[str, Any]] = None

    # =========================================================================
    # User Profile
    # =========================================================================

    async def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile information.

        Returns:
            User profile data
        """
        if not self.is_v2_available:
            return {
                "error": "User profile requires v2 API authentication",
                "hint": "Use ticktick_login to authenticate with username/password"
            }

        try:
            # Get user data from batch check
            url = Endpoints.Sync.batch_check(0)
            data = await self.client.get(url, version=APIVersion.V2)

            self._user_data = data

            # Extract user info
            return {
                "inbox_id": data.get("inboxId"),
                "user_id": self.client._user_id,
                "timezone": data.get("timezone"),
                "sync_status": "synced",
            }
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {"error": str(e)}

    async def get_inbox_id(self) -> Optional[str]:
        """
        Get the inbox project ID.

        The inbox has a special ID format that's needed for operations
        on inbox tasks.

        Returns:
            Inbox project ID or None
        """
        if self._user_data and "inboxId" in self._user_data:
            return self._user_data["inboxId"]

        profile = await self.get_profile()
        return profile.get("inbox_id")

    async def get_timezone(self) -> Optional[str]:
        """
        Get user's configured time zone.

        Returns:
            Time zone string (e.g., "America/Los_Angeles")
        """
        if self._user_data and "timezone" in self._user_data:
            return self._user_data["timezone"]

        profile = await self.get_profile()
        return profile.get("timezone")

    # =========================================================================
    # Settings
    # =========================================================================

    async def get_settings(self) -> Dict[str, Any]:
        """
        Get user settings.

        Returns:
            User settings dictionary
        """
        if not self.is_v2_available:
            return {
                "error": "Settings require v2 API authentication",
                "hint": "Use ticktick_login to authenticate with username/password"
            }

        try:
            url = Endpoints.Auth.user_settings()
            data = await self.client.get(url, version=APIVersion.V2)
            return data
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return {"error": str(e)}

    async def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user settings.

        Args:
            settings: Settings to update

        Returns:
            Updated settings
        """
        if not self.is_v2_available:
            return {
                "error": "Settings require v2 API authentication",
            }

        try:
            url = Endpoints.Auth.user_settings()
            data = await self.client.post(url, version=APIVersion.V2, data=settings)
            return data
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return {"error": str(e)}

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile as markdown."""
        if "error" in profile:
            return f"## ⚠️ Profile Error\n\n{profile['error']}\n\n*{profile.get('hint', '')}*"

        lines = [
            "## 👤 User Profile\n",
            f"- **Inbox ID**: `{profile.get('inbox_id', 'N/A')}`",
            f"- **User ID**: `{profile.get('user_id', 'N/A')}`",
            f"- **Time Zone**: {profile.get('timezone', 'N/A')}",
            f"- **Sync Status**: {profile.get('sync_status', 'unknown')}",
        ]

        return "\n".join(lines)

    def format_settings(self, settings: Dict[str, Any]) -> str:
        """Format settings as markdown."""
        if "error" in settings:
            return f"## ⚠️ Settings Error\n\n{settings['error']}"

        import json
        lines = [
            "## ⚙️ User Settings\n",
            "```json",
            json.dumps(settings, indent=2, default=str),
            "```",
        ]

        return "\n".join(lines)
