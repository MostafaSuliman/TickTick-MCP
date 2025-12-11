"""
Authentication models for TickTick API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    OAUTH2 = "oauth2"
    USERNAME_PASSWORD = "username_password"


class OAuthCredentials(BaseModel):
    """OAuth2 application credentials."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    client_id: str = Field(
        ...,
        description="OAuth2 Client ID from TickTick Developer Portal",
        min_length=1
    )
    client_secret: SecretStr = Field(
        ...,
        description="OAuth2 Client Secret",
        min_length=1
    )
    redirect_uri: str = Field(
        default="http://127.0.0.1:8080/callback",
        description="OAuth2 redirect URI"
    )
    scope: str = Field(
        default="tasks:read tasks:write",
        description="OAuth2 scopes (space-separated)"
    )


class OAuthToken(BaseModel):
    """OAuth2 token response and storage."""
    model_config = ConfigDict(extra="allow")

    access_token: str = Field(..., description="Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(
        default=15552000,  # 180 days
        description="Token lifetime in seconds"
    )
    scope: Optional[str] = Field(default=None, description="Granted scopes")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token if provided")

    # Computed fields for token management
    expire_time: Optional[float] = Field(default=None, description="Unix timestamp when token expires")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expire_time is None:
            return False
        return datetime.now().timestamp() >= self.expire_time

    def time_until_expiry(self) -> Optional[int]:
        """Return seconds until token expires."""
        if self.expire_time is None:
            return None
        remaining = self.expire_time - datetime.now().timestamp()
        return max(0, int(remaining))


class UserCredentials(BaseModel):
    """Username/password credentials for API v2."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: str = Field(..., description="TickTick username or email", min_length=1)
    password: SecretStr = Field(..., description="TickTick password", min_length=1)


class SessionToken(BaseModel):
    """Session token from username/password auth (API v2)."""
    model_config = ConfigDict(extra="allow")

    token: str = Field(..., description="Session token")
    user_id: Optional[str] = Field(default=None)
    inbox_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    cookies: Optional[dict] = Field(default=None, description="Session cookies")


class AuthConfig(BaseModel):
    """Complete authentication configuration."""
    model_config = ConfigDict(extra="forbid")

    method: AuthMethod = Field(
        default=AuthMethod.OAUTH2,
        description="Authentication method to use"
    )
    oauth: Optional[OAuthCredentials] = Field(
        default=None,
        description="OAuth2 credentials (required for OAUTH2 method)"
    )
    user_credentials: Optional[UserCredentials] = Field(
        default=None,
        description="Username/password (required for USERNAME_PASSWORD method)"
    )

    # API version preference
    prefer_v2: bool = Field(
        default=True,
        description="Prefer API v2 when available for extended features"
    )

    # Token storage paths
    token_cache_path: Optional[str] = Field(
        default=None,
        description="Path to cache tokens (defaults to ~/.ticktick-mcp/)"
    )


class AuthorizationRequest(BaseModel):
    """OAuth authorization code exchange request."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    authorization_code: str = Field(
        ...,
        description="Authorization code from OAuth callback",
        min_length=1
    )
    state: Optional[str] = Field(
        default=None,
        description="State parameter for CSRF validation"
    )


class AuthStatus(BaseModel):
    """Current authentication status."""
    model_config = ConfigDict(extra="forbid")

    is_authenticated: bool = Field(default=False)
    method: Optional[AuthMethod] = Field(default=None)
    api_version: Optional[str] = Field(default=None, description="Active API version (v1 or v2)")
    user_id: Optional[str] = Field(default=None)
    inbox_id: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    scopes: Optional[list[str]] = Field(default=None)
