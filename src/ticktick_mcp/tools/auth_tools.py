"""
Authentication MCP tools.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ConfigureOAuthInput(BaseModel):
    """Input for OAuth configuration."""
    client_id: str = Field(..., description="OAuth Client ID from TickTick Developer Portal")
    client_secret: str = Field(..., description="OAuth Client Secret")
    redirect_uri: str = Field(
        default="http://127.0.0.1:8080/callback",
        description="OAuth redirect URI"
    )


class AuthorizeOAuthInput(BaseModel):
    """Input for OAuth authorization."""
    authorization_code: str = Field(
        ...,
        description="Authorization code from callback URL"
    )


class LoginInput(BaseModel):
    """Input for username/password login."""
    username: str = Field(..., description="TickTick username or email")
    password: str = Field(..., description="Account password")


def register_auth_tools(mcp, auth_service):
    """Register authentication tools."""

    @mcp.tool(
        name="ticktick_configure_oauth",
        annotations={
            "title": "Configure TickTick OAuth",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def configure_oauth(params: ConfigureOAuthInput) -> str:
        """
        Configure OAuth2 credentials for TickTick API v1.

        This is the first step for OAuth authentication. After configuration,
        you'll receive an authorization URL to visit.

        Args:
            params: OAuth credentials

        Returns:
            Authorization URL and instructions
        """
        auth_url = auth_service.configure_oauth(
            params.client_id,
            params.client_secret,
            params.redirect_uri
        )
        return auth_service.format_oauth_instructions(auth_url, params.redirect_uri)

    @mcp.tool(
        name="ticktick_authorize_oauth",
        annotations={
            "title": "Complete TickTick OAuth",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def authorize_oauth(params: AuthorizeOAuthInput) -> str:
        """
        Complete OAuth2 authorization with the code from callback URL.

        Use this after visiting the authorization URL and being redirected.

        Args:
            params: Authorization code

        Returns:
            Success message with token details
        """
        try:
            token = await auth_service.authorize_oauth(params.authorization_code)
            return f"""##  Authorization Successful!

**Token Details:**
- **Type**: {token.token_type}
- **Scope**: {token.scope}
- **Expires In**: {token.time_until_expiry() // 86400} days

You can now use all TickTick v1 API tools:
- `ticktick_list_tasks` - View tasks
- `ticktick_create_task` - Create tasks
- `ticktick_list_projects` - View projects

For extended features (tags, habits, focus), use `ticktick_login`.
"""
        except Exception as e:
            return f" **Authorization Failed**: {str(e)}"

    @mcp.tool(
        name="ticktick_login",
        annotations={
            "title": "TickTick Login (v2 API)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def login(params: LoginInput) -> str:
        """
        Login with username/password for v2 API access.

        This enables extended features like tags, habits, and focus timer.

        Args:
            params: Login credentials

        Returns:
            Success message
        """
        try:
            token = await auth_service.login(params.username, params.password)
            return f"""##  Login Successful!

**Extended Features Now Available:**
-  Tags Management
-  Habit Tracking
-  Focus/Pomodoro Timer
-  Productivity Statistics
-  Completed Tasks History
-  Batch Operations

**Inbox ID**: `{token.inbox_id}`
"""
        except Exception as e:
            return f" **Login Failed**: {str(e)}"

    @mcp.tool(
        name="ticktick_auth_status",
        annotations={
            "title": "Check Authentication Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def check_auth_status() -> str:
        """
        Check current authentication status.

        Returns:
            Authentication status details
        """
        return auth_service.format_status()

    @mcp.tool(
        name="ticktick_logout",
        annotations={
            "title": "TickTick Logout",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def logout() -> str:
        """
        Clear all authentication tokens (logout).

        Returns:
            Confirmation message
        """
        auth_service.logout()
        return "##  Logged Out\n\nAll tokens have been cleared."
