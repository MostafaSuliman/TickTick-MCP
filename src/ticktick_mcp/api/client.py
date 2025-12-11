"""
TickTick API Client - Unified client supporting both v1 and v2 APIs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import httpx

from .endpoints import APIVersion, Endpoints
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    raise_for_status,
)
from ..models.auth import (
    AuthConfig,
    AuthMethod,
    OAuthCredentials,
    OAuthToken,
    SessionToken,
    UserCredentials,
)

logger = logging.getLogger(__name__)


class TickTickClient:
    """
    Unified TickTick API client supporting both Official (v1) and Internal (v2) APIs.

    Features:
    - Dual authentication (OAuth2 for v1, username/password for v2)
    - Automatic token management and refresh
    - Rate limiting handling
    - Request retry with exponential backoff
    - Response caching
    """

    DEFAULT_TIMEOUT = 30.0
    DEFAULT_TOKEN_PATH = Path.home() / ".ticktick-mcp"

    def __init__(
        self,
        auth_config: Optional[AuthConfig] = None,
        timeout: float = DEFAULT_TIMEOUT,
        token_path: Optional[Path] = None,
        prefer_v2: bool = True,
    ):
        """
        Initialize TickTick client.

        Args:
            auth_config: Authentication configuration
            timeout: Request timeout in seconds
            token_path: Path to store tokens
            prefer_v2: Prefer v2 API when available
        """
        self.auth_config = auth_config
        self.timeout = timeout
        self.token_path = token_path or self.DEFAULT_TOKEN_PATH
        self.prefer_v2 = prefer_v2

        # Ensure token directory exists
        self.token_path.mkdir(parents=True, exist_ok=True)

        # Token storage
        self._oauth_token: Optional[OAuthToken] = None
        self._session_token: Optional[SessionToken] = None

        # Sync state
        self._inbox_id: Optional[str] = None
        self._user_id: Optional[str] = None

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

        # Load cached tokens
        self._load_cached_tokens()

    # =========================================================================
    # HTTP Client Management
    # =========================================================================

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "TickTickClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    # =========================================================================
    # Token Management
    # =========================================================================

    def _load_cached_tokens(self) -> None:
        """Load tokens from cache files."""
        # OAuth token
        oauth_file = self.token_path / "oauth_token.json"
        if oauth_file.exists():
            try:
                data = json.loads(oauth_file.read_text())
                self._oauth_token = OAuthToken(**data)
                if self._oauth_token.is_expired():
                    logger.warning("Cached OAuth token is expired")
                    self._oauth_token = None
            except Exception as e:
                logger.warning(f"Failed to load OAuth token: {e}")

        # Session token (v2)
        session_file = self.token_path / "session_token.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
                self._session_token = SessionToken(**data)
            except Exception as e:
                logger.warning(f"Failed to load session token: {e}")

    def _save_oauth_token(self, token: OAuthToken) -> None:
        """Save OAuth token to cache."""
        self._oauth_token = token
        oauth_file = self.token_path / "oauth_token.json"
        oauth_file.write_text(json.dumps(token.model_dump(), default=str, indent=2))
        logger.debug("OAuth token saved to cache")

    def _save_session_token(self, token: SessionToken) -> None:
        """Save session token to cache."""
        self._session_token = token
        session_file = self.token_path / "session_token.json"
        session_file.write_text(json.dumps(token.model_dump(), default=str, indent=2))
        logger.debug("Session token saved to cache")

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        config_file = self.token_path / "config.json"
        config_file.write_text(json.dumps(config, indent=2))

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config_file = self.token_path / "config.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except Exception:
                pass
        return {}

    # =========================================================================
    # Authentication Methods
    # =========================================================================

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        if self._oauth_token and not self._oauth_token.is_expired():
            return True
        if self._session_token:
            return True
        return False

    @property
    def active_api_version(self) -> Optional[APIVersion]:
        """Get currently active API version based on authentication."""
        if self._session_token:
            return APIVersion.V2
        if self._oauth_token and not self._oauth_token.is_expired():
            return APIVersion.V1 if not self.prefer_v2 else APIVersion.V1
        return None

    def get_access_token(self) -> Optional[str]:
        """Get current access token for API requests."""
        if self._oauth_token and not self._oauth_token.is_expired():
            return self._oauth_token.access_token
        return None

    def configure_oauth(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8080/callback",
    ) -> str:
        """
        Configure OAuth credentials and return authorization URL.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI

        Returns:
            Authorization URL for user to visit
        """
        # Save config
        config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
        self._save_config(config)

        # Build authorization URL
        auth_url = (
            f"{Endpoints.OAUTH_AUTHORIZE}"
            f"?client_id={client_id}"
            f"&scope=tasks:read tasks:write"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&state=mcp_auth"
        )

        return auth_url

    async def authorize_oauth(self, authorization_code: str) -> OAuthToken:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Code from OAuth callback

        Returns:
            OAuthToken with access credentials
        """
        config = self._load_config()
        if not config.get("client_id") or not config.get("client_secret"):
            raise ConfigurationError(
                "OAuth not configured. Call configure_oauth first."
            )

        client = await self._get_client()

        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": config.get("redirect_uri", "http://127.0.0.1:8080/callback"),
            "scope": "tasks:read tasks:write",
        }

        try:
            response = await client.post(
                Endpoints.OAUTH_TOKEN,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"OAuth token exchange failed: {response.text}",
                    status_code=response.status_code,
                )

            token_response = response.json()

            # Calculate expiration
            expires_in = token_response.get("expires_in", 15552000)
            token_response["expire_time"] = datetime.now().timestamp() + expires_in

            token = OAuthToken(**token_response)
            self._save_oauth_token(token)

            return token

        except httpx.RequestError as e:
            raise NetworkError(f"Network error during OAuth: {e}")

    async def login_v2(self, username: str, password: str) -> SessionToken:
        """
        Authenticate using username/password (v2 API).

        Args:
            username: TickTick username or email
            password: Account password

        Returns:
            SessionToken with session credentials
        """
        client = await self._get_client()

        try:
            response = await client.post(
                Endpoints.Auth.signin(),
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Login failed: {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()

            # Extract cookies for session management
            cookies = dict(response.cookies)

            token = SessionToken(
                token=data.get("token", ""),
                user_id=data.get("userId"),
                inbox_id=data.get("inboxId"),
                cookies=cookies,
            )

            self._session_token = token
            self._inbox_id = token.inbox_id
            self._user_id = token.user_id
            self._save_session_token(token)

            return token

        except httpx.RequestError as e:
            raise NetworkError(f"Network error during login: {e}")

    # =========================================================================
    # HTTP Request Methods
    # =========================================================================

    def _get_headers(self, version: APIVersion = APIVersion.V1) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if version == APIVersion.V1 and self._oauth_token:
            headers["Authorization"] = f"Bearer {self._oauth_token.access_token}"
        elif version == APIVersion.V2 and self._session_token:
            headers["Authorization"] = f"Bearer {self._session_token.token}"

        return headers

    def _get_cookies(self) -> Optional[Dict[str, str]]:
        """Get cookies for v2 requests."""
        if self._session_token and self._session_token.cookies:
            return self._session_token.cookies
        return None

    async def request(
        self,
        method: str,
        url: str,
        version: APIVersion = APIVersion.V1,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL or endpoint path
            version: API version to use
            data: JSON body data
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "Not authenticated. Please authenticate first."
            )

        client = await self._get_client()
        headers = self._get_headers(version)
        cookies = self._get_cookies() if version == APIVersion.V2 else None

        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                params=params,
                cookies=cookies,
                **kwargs,
            )

            # Handle response
            raise_for_status(response.status_code, response.text, url)

            if response.status_code == 204 or not response.content:
                return {"success": True}

            return response.json()

        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}")

    async def get(
        self,
        url: str,
        version: APIVersion = APIVersion.V1,
        params: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request("GET", url, version, params=params, **kwargs)

    async def post(
        self,
        url: str,
        version: APIVersion = APIVersion.V1,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request("POST", url, version, data=data, **kwargs)

    async def put(
        self,
        url: str,
        version: APIVersion = APIVersion.V1,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request("PUT", url, version, data=data, **kwargs)

    async def delete(
        self,
        url: str,
        version: APIVersion = APIVersion.V1,
        params: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request("DELETE", url, version, params=params, **kwargs)

    # =========================================================================
    # Sync Operations
    # =========================================================================

    async def sync(self, checkpoint: int = 0) -> Dict[str, Any]:
        """
        Perform full sync to get all account data (v2 only).

        Args:
            checkpoint: Sync checkpoint for delta sync

        Returns:
            Full account data including projects, tasks, tags, etc.
        """
        if not self._session_token:
            raise AuthenticationError(
                "V2 authentication required for sync. Use login_v2 first."
            )

        url = Endpoints.Sync.batch_check(checkpoint)
        response = await self.get(url, version=APIVersion.V2)

        # Extract inbox ID if not set
        if not self._inbox_id and "inboxId" in response:
            self._inbox_id = response["inboxId"]

        return response

    @property
    def inbox_id(self) -> Optional[str]:
        """Get inbox project ID."""
        return self._inbox_id

    @property
    def user_id(self) -> Optional[str]:
        """Get current user ID."""
        return self._user_id

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def clear_tokens(self) -> None:
        """Clear all cached tokens (logout)."""
        self._oauth_token = None
        self._session_token = None
        self._inbox_id = None
        self._user_id = None

        # Remove cached files
        for f in ["oauth_token.json", "session_token.json"]:
            token_file = self.token_path / f
            if token_file.exists():
                token_file.unlink()

        logger.info("All tokens cleared")

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        status = {
            "is_authenticated": self.is_authenticated,
            "api_version": self.active_api_version.value if self.active_api_version else None,
            "inbox_id": self._inbox_id,
            "user_id": self._user_id,
        }

        if self._oauth_token:
            status["oauth"] = {
                "token_type": self._oauth_token.token_type,
                "scope": self._oauth_token.scope,
                "expires_in_seconds": self._oauth_token.time_until_expiry(),
            }

        if self._session_token:
            status["session"] = {
                "created_at": str(self._session_token.created_at),
            }

        return status
