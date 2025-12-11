"""
Configuration management for TickTick MCP server.

Supports loading configuration from:
- Environment variables
- Configuration files (JSON/YAML)
- Default values
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthConfig:
    """OAuth2 configuration."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str = "http://127.0.0.1:8080/callback"
    scope: str = "tasks:read tasks:write"


@dataclass
class ServerConfig:
    """MCP server configuration."""
    name: str = "ticktick-mcp"
    log_level: str = "INFO"
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds


@dataclass
class APIConfig:
    """API client configuration."""
    v1_base_url: str = "https://api.ticktick.com/open/v1"
    v2_base_url: str = "https://api.ticktick.com/api/v2"
    timeout: int = 30  # seconds
    retry_count: int = 3
    retry_delay: float = 1.0  # seconds


@dataclass
class TickTickConfig:
    """Complete configuration for TickTick MCP server."""
    oauth: OAuthConfig = field(default_factory=OAuthConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    api: APIConfig = field(default_factory=APIConfig)

    @classmethod
    def from_env(cls) -> "TickTickConfig":
        """Load configuration from environment variables."""
        config = cls()

        # OAuth config
        config.oauth.client_id = os.environ.get("TICKTICK_CLIENT_ID")
        config.oauth.client_secret = os.environ.get("TICKTICK_CLIENT_SECRET")
        config.oauth.redirect_uri = os.environ.get(
            "TICKTICK_REDIRECT_URI",
            config.oauth.redirect_uri
        )

        # Server config
        config.server.name = os.environ.get(
            "TICKTICK_MCP_NAME",
            config.server.name
        )
        config.server.log_level = os.environ.get(
            "TICKTICK_LOG_LEVEL",
            config.server.log_level
        )

        # API config
        config.api.timeout = int(os.environ.get(
            "TICKTICK_API_TIMEOUT",
            str(config.api.timeout)
        ))

        return config

    @classmethod
    def from_file(cls, path: str) -> "TickTickConfig":
        """Load configuration from JSON file."""
        config_path = Path(path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {path}")
            return cls()

        with open(config_path) as f:
            data = json.load(f)

        config = cls()

        # OAuth
        if "oauth" in data:
            oauth = data["oauth"]
            config.oauth.client_id = oauth.get("client_id")
            config.oauth.client_secret = oauth.get("client_secret")
            config.oauth.redirect_uri = oauth.get(
                "redirect_uri",
                config.oauth.redirect_uri
            )

        # Server
        if "server" in data:
            server = data["server"]
            config.server.name = server.get("name", config.server.name)
            config.server.log_level = server.get("log_level", config.server.log_level)
            config.server.cache_enabled = server.get(
                "cache_enabled",
                config.server.cache_enabled
            )
            config.server.cache_ttl = server.get(
                "cache_ttl",
                config.server.cache_ttl
            )

        # API
        if "api" in data:
            api = data["api"]
            config.api.timeout = api.get("timeout", config.api.timeout)
            config.api.retry_count = api.get("retry_count", config.api.retry_count)

        return config

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "TickTickConfig":
        """
        Load configuration with priority:
        1. Environment variables (highest)
        2. Config file
        3. Default values (lowest)
        """
        # Start with defaults
        config = cls()

        # Load from file if provided
        if config_path:
            file_config = cls.from_file(config_path)
            # Merge file config (only non-None values)
            if file_config.oauth.client_id:
                config.oauth.client_id = file_config.oauth.client_id
            if file_config.oauth.client_secret:
                config.oauth.client_secret = file_config.oauth.client_secret
            config.oauth.redirect_uri = file_config.oauth.redirect_uri
            config.server = file_config.server
            config.api = file_config.api
        else:
            # Try default config paths
            default_paths = [
                Path.home() / ".config" / "ticktick-mcp" / "config.json",
                Path.home() / ".ticktick-mcp.json",
                Path.cwd() / "ticktick-config.json",
            ]
            for default_path in default_paths:
                if default_path.exists():
                    logger.info(f"Loading config from: {default_path}")
                    file_config = cls.from_file(str(default_path))
                    if file_config.oauth.client_id:
                        config.oauth.client_id = file_config.oauth.client_id
                    if file_config.oauth.client_secret:
                        config.oauth.client_secret = file_config.oauth.client_secret
                    break

        # Override with environment variables
        env_config = cls.from_env()
        if env_config.oauth.client_id:
            config.oauth.client_id = env_config.oauth.client_id
        if env_config.oauth.client_secret:
            config.oauth.client_secret = env_config.oauth.client_secret
        if os.environ.get("TICKTICK_REDIRECT_URI"):
            config.oauth.redirect_uri = env_config.oauth.redirect_uri
        if os.environ.get("TICKTICK_LOG_LEVEL"):
            config.server.log_level = env_config.server.log_level
        if os.environ.get("TICKTICK_API_TIMEOUT"):
            config.api.timeout = env_config.api.timeout

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "oauth": {
                "client_id": self.oauth.client_id,
                "client_secret": "***" if self.oauth.client_secret else None,
                "redirect_uri": self.oauth.redirect_uri,
            },
            "server": {
                "name": self.server.name,
                "log_level": self.server.log_level,
                "cache_enabled": self.server.cache_enabled,
                "cache_ttl": self.server.cache_ttl,
            },
            "api": {
                "v1_base_url": self.api.v1_base_url,
                "v2_base_url": self.api.v2_base_url,
                "timeout": self.api.timeout,
                "retry_count": self.api.retry_count,
            },
        }

    def save(self, path: str) -> None:
        """Save configuration to JSON file (excluding secrets)."""
        config_data = self.to_dict()
        # Remove sensitive data
        config_data["oauth"]["client_secret"] = None

        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Configuration saved to: {path}")
