"""
Authentication Service - Wrapper for authentication operations.
"""

import logging
from typing import Any, Dict, Optional

from ..api.client import TickTickClient
from ..models.auth import AuthStatus, OAuthToken, SessionToken
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """
    Service for authentication operations.

    Provides a clean interface for OAuth2 and username/password authentication.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)

    # =========================================================================
    # OAuth2 Authentication (v1 API)
    # =========================================================================

    def configure_oauth(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8080/callback",
    ) -> str:
        """
        Configure OAuth2 credentials and get authorization URL.

        Args:
            client_id: OAuth2 Client ID from TickTick Developer Portal
            client_secret: OAuth2 Client Secret
            redirect_uri: Redirect URI configured in TickTick app

        Returns:
            Authorization URL for user to visit
        """
        return self.client.configure_oauth(client_id, client_secret, redirect_uri)

    async def authorize_oauth(self, authorization_code: str) -> OAuthToken:
        """
        Complete OAuth2 authorization with the authorization code.

        Args:
            authorization_code: Code from OAuth callback URL

        Returns:
            OAuthToken with access credentials
        """
        return await self.client.authorize_oauth(authorization_code)

    # =========================================================================
    # Username/Password Authentication (v2 API)
    # =========================================================================

    async def login(self, username: str, password: str) -> SessionToken:
        """
        Authenticate using username/password for v2 API access.

        This enables access to extended features like tags, habits, and focus timer.

        Args:
            username: TickTick username or email
            password: Account password

        Returns:
            SessionToken with session credentials
        """
        return await self.client.login_v2(username, password)

    # =========================================================================
    # Status and Management
    # =========================================================================

    def get_status(self) -> AuthStatus:
        """
        Get current authentication status.

        Returns:
            AuthStatus object with current auth state
        """
        status_dict = self.client.get_auth_status()

        expires_at = None
        if status_dict.get("oauth", {}).get("expires_in_seconds"):
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(
                seconds=status_dict["oauth"]["expires_in_seconds"]
            )

        scopes = None
        if status_dict.get("oauth", {}).get("scope"):
            scopes = status_dict["oauth"]["scope"].split()

        return AuthStatus(
            is_authenticated=status_dict["is_authenticated"],
            api_version=status_dict.get("api_version"),
            user_id=status_dict.get("user_id"),
            inbox_id=status_dict.get("inbox_id"),
            expires_at=expires_at,
            scopes=scopes,
        )

    def logout(self) -> None:
        """
        Clear all authentication tokens (logout).
        """
        self.client.clear_tokens()

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.client.is_authenticated

    @property
    def has_v2_access(self) -> bool:
        """Check if v2 API is available (extended features)."""
        return self.client._session_token is not None

    @property
    def inbox_id(self) -> Optional[str]:
        """Get inbox project ID."""
        return self.client.inbox_id

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_status(self) -> str:
        """Format authentication status as markdown."""
        status = self.get_status()
        lines = ["##  TickTick Authentication Status\n"]

        if status.is_authenticated:
            lines.append(" **Status**: Authenticated")
            lines.append(f"- **API Version**: {status.api_version or 'v1'}")

            if status.user_id:
                lines.append(f"- **User ID**: `{status.user_id}`")
            if status.inbox_id:
                lines.append(f"- **Inbox ID**: `{status.inbox_id}`")
            if status.expires_at:
                lines.append(f"- **Expires**: {status.expires_at.strftime('%Y-%m-%d %H:%M')}")
            if status.scopes:
                lines.append(f"- **Scopes**: {', '.join(status.scopes)}")

            if self.has_v2_access:
                lines.append("\n **Extended Features**: Available (tags, habits, focus)")
            else:
                lines.append("\n **Extended Features**: Not available")
                lines.append("  _Use login(username, password) to enable_")
        else:
            lines.append(" **Status**: Not Authenticated")
            lines.append("\n**To authenticate:**")
            lines.append("1. OAuth2 (v1): `configure_oauth` then `authorize_oauth`")
            lines.append("2. Login (v2): `login(username, password)`")

        return "\n".join(lines)

    def format_oauth_instructions(self, auth_url: str, redirect_uri: str) -> str:
        """Format OAuth setup instructions."""
        return f"""##  TickTick OAuth Configuration Saved!

**Next Steps:**

1. **Visit this URL to authorize the app:**

   {auth_url}

2. **After authorizing**, you'll be redirected to:
   `{redirect_uri}?code=AUTHORIZATION_CODE&state=mcp_auth`

3. **Copy the `code` parameter** from the URL and use:
   `authorize_oauth(code="YOUR_CODE")`

**Note**: The redirect URL doesn't need to be a live server.
You just need to copy the `code` parameter from the URL bar.
"""
