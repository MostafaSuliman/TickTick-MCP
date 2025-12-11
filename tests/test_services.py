"""
Tests for TickTick MCP services.
"""

import pytest
from unittest.mock import AsyncMock, patch

from ticktick_mcp.services.task_service import TaskService
from ticktick_mcp.services.project_service import ProjectService
from ticktick_mcp.services.auth_service import AuthService
from ticktick_mcp.models.tasks import Task, TaskCreate, TaskPriority


class TestTaskService:
    """Tests for TaskService."""

    @pytest.fixture
    def task_service(self, mock_client):
        """Create a TaskService instance."""
        return TaskService(mock_client)

    @pytest.mark.asyncio
    async def test_get_task(self, task_service, mock_client, sample_task):
        """Test getting a single task."""
        mock_client.get.return_value = sample_task

        task = await task_service.get("task123", "project456")

        assert isinstance(task, Task)
        assert task.id == "task123"
        assert task.title == "Test Task"
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task(self, task_service, mock_client, sample_task):
        """Test creating a task."""
        mock_client.post.return_value = sample_task

        task_data = TaskCreate(
            title="Test Task",
            project_id="project456",
            priority=TaskPriority.MEDIUM,
        )

        task = await task_service.create(task_data)

        assert isinstance(task, Task)
        assert task.title == "Test Task"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_task(self, task_service, mock_client):
        """Test completing a task."""
        mock_client.post.return_value = {}

        result = await task_service.complete("task123", "project456")

        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, mock_client):
        """Test deleting a task."""
        mock_client.delete.return_value = None

        result = await task_service.delete("task123", "project456")

        assert result is True

    def test_format_task(self, task_service, sample_task):
        """Test task formatting."""
        task = Task(**sample_task)
        formatted = task_service.format_task(task)

        assert "Test Task" in formatted
        assert "task123" in formatted
        assert "Medium" in formatted


class TestProjectService:
    """Tests for ProjectService."""

    @pytest.fixture
    def project_service(self, mock_client):
        """Create a ProjectService instance."""
        return ProjectService(mock_client)

    @pytest.mark.asyncio
    async def test_list_projects(self, project_service, mock_client, sample_project):
        """Test listing projects."""
        mock_client.get.return_value = [sample_project]

        projects = await project_service.list()

        assert len(projects) == 1
        assert projects[0].name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project(self, project_service, mock_client, sample_project):
        """Test getting a single project."""
        # Mock project list for lookup
        mock_client.get.return_value = [sample_project]

        project = await project_service.get("project456")

        assert project.id == "project456"
        assert project.name == "Test Project"


class TestAuthService:
    """Tests for AuthService."""

    @pytest.fixture
    def auth_service(self, mock_client):
        """Create an AuthService instance."""
        return AuthService(mock_client)

    def test_configure_oauth(self, auth_service, mock_client):
        """Test OAuth configuration."""
        mock_client.configure_oauth.return_value = "https://auth.url"

        url = auth_service.configure_oauth(
            "client_id",
            "client_secret",
            "http://localhost:8080/callback"
        )

        assert url == "https://auth.url"
        mock_client.configure_oauth.assert_called_once()

    @pytest.mark.asyncio
    async def test_authorize_oauth(self, auth_service, mock_client):
        """Test OAuth authorization."""
        from ticktick_mcp.models.auth import OAuthToken

        mock_token = OAuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=86400,
            scope="tasks:read tasks:write",
        )
        mock_client.authorize_oauth.return_value = mock_token

        token = await auth_service.authorize_oauth("auth_code_123")

        assert token.access_token == "test_token"
        mock_client.authorize_oauth.assert_called_once_with("auth_code_123")

    def test_is_authenticated(self, auth_service, mock_client):
        """Test authentication status check."""
        mock_client.is_authenticated = True

        assert auth_service.is_authenticated is True

    def test_format_status_not_authenticated(self, auth_service, mock_client):
        """Test status formatting when not authenticated."""
        mock_client.get_auth_status.return_value = {
            "is_authenticated": False,
        }

        status = auth_service.format_status()

        assert "Not Authenticated" in status

    def test_logout(self, auth_service, mock_client):
        """Test logout."""
        auth_service.logout()

        mock_client.clear_tokens.assert_called_once()
