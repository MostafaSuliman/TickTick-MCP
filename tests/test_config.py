"""
Tests for TickTick MCP configuration management.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path

from ticktick_mcp.config import TickTickConfig, OAuthConfig, ServerConfig, APIConfig


class TestTickTickConfig:
    """Tests for configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TickTickConfig()

        assert config.oauth.client_id is None
        assert config.oauth.redirect_uri == "http://127.0.0.1:8080/callback"
        assert config.server.name == "ticktick-mcp"
        assert config.server.log_level == "INFO"
        assert config.api.timeout == 30

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("TICKTICK_CLIENT_ID", "env_client_id")
        monkeypatch.setenv("TICKTICK_CLIENT_SECRET", "env_client_secret")
        monkeypatch.setenv("TICKTICK_LOG_LEVEL", "DEBUG")

        config = TickTickConfig.from_env()

        assert config.oauth.client_id == "env_client_id"
        assert config.oauth.client_secret == "env_client_secret"
        assert config.server.log_level == "DEBUG"

    def test_from_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "oauth": {
                "client_id": "file_client_id",
                "client_secret": "file_secret",
                "redirect_uri": "http://custom.redirect/callback",
            },
            "server": {
                "name": "custom-mcp",
                "log_level": "WARNING",
                "cache_enabled": False,
            },
            "api": {
                "timeout": 60,
                "retry_count": 5,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = TickTickConfig.from_file(temp_path)

            assert config.oauth.client_id == "file_client_id"
            assert config.oauth.redirect_uri == "http://custom.redirect/callback"
            assert config.server.name == "custom-mcp"
            assert config.server.cache_enabled is False
            assert config.api.timeout == 60
        finally:
            os.unlink(temp_path)

    def test_from_file_not_found(self):
        """Test loading from non-existent file returns defaults."""
        config = TickTickConfig.from_file("/nonexistent/path.json")

        # Should return default config without errors
        assert config.oauth.client_id is None
        assert config.server.name == "ticktick-mcp"

    def test_load_env_priority(self, monkeypatch):
        """Test that environment variables override file config."""
        config_data = {
            "oauth": {
                "client_id": "file_client_id",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        # Set environment variable to override
        monkeypatch.setenv("TICKTICK_CLIENT_ID", "env_override_id")

        try:
            config = TickTickConfig.load(temp_path)

            # Environment should override file
            assert config.oauth.client_id == "env_override_id"
        finally:
            os.unlink(temp_path)

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = TickTickConfig()
        config.oauth.client_id = "test_id"
        config.oauth.client_secret = "secret123"

        data = config.to_dict()

        assert data["oauth"]["client_id"] == "test_id"
        # Secret should be masked
        assert data["oauth"]["client_secret"] == "***"

    def test_save(self):
        """Test saving configuration to file."""
        config = TickTickConfig()
        config.oauth.client_id = "save_test_id"
        config.server.log_level = "DEBUG"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config.save(str(config_path))

            # Verify file was created
            assert config_path.exists()

            # Load and verify contents
            with open(config_path) as f:
                data = json.load(f)

            assert data["oauth"]["client_id"] == "save_test_id"
            assert data["server"]["log_level"] == "DEBUG"
            # Secret should not be saved
            assert data["oauth"]["client_secret"] is None


class TestOAuthConfig:
    """Tests for OAuth configuration."""

    def test_defaults(self):
        """Test OAuth default values."""
        config = OAuthConfig()

        assert config.client_id is None
        assert config.client_secret is None
        assert config.redirect_uri == "http://127.0.0.1:8080/callback"
        assert config.scope == "tasks:read tasks:write"


class TestServerConfig:
    """Tests for server configuration."""

    def test_defaults(self):
        """Test server default values."""
        config = ServerConfig()

        assert config.name == "ticktick-mcp"
        assert config.log_level == "INFO"
        assert config.cache_enabled is True
        assert config.cache_ttl == 300


class TestAPIConfig:
    """Tests for API configuration."""

    def test_defaults(self):
        """Test API default values."""
        config = APIConfig()

        assert config.v1_base_url == "https://api.ticktick.com/open/v1"
        assert config.v2_base_url == "https://api.ticktick.com/api/v2"
        assert config.timeout == 30
        assert config.retry_count == 3
