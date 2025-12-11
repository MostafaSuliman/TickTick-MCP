"""
Tests for TickTick MCP data models.
"""

import pytest
from pydantic import ValidationError

from ticktick_mcp.models.tasks import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskPriority,
    TaskStatus,
    ChecklistItem,
)
from ticktick_mcp.models.projects import Project, ProjectCreate
from ticktick_mcp.models.auth import OAuthToken, SessionToken


class TestTaskModels:
    """Tests for task-related models."""

    def test_task_from_api_response(self, sample_task):
        """Test creating a Task from API response."""
        task = Task(**sample_task)

        assert task.id == "task123"
        assert task.project_id == "project456"
        assert task.title == "Test Task"
        assert task.status == TaskStatus.INCOMPLETE
        assert task.priority == TaskPriority.MEDIUM
        assert task.tags == ["work", "important"]

    def test_task_create_minimal(self):
        """Test creating a task with minimal data."""
        task = TaskCreate(title="Simple Task")

        assert task.title == "Simple Task"
        assert task.project_id is None
        assert task.priority == TaskPriority.NONE

    def test_task_create_full(self):
        """Test creating a task with all fields."""
        task = TaskCreate(
            title="Full Task",
            content="Description here",
            project_id="proj123",
            due_date="2024-12-31T23:59:59+0000",
            priority=TaskPriority.HIGH,
            tags=["urgent"],
        )

        assert task.title == "Full Task"
        assert task.content == "Description here"
        assert task.project_id == "proj123"
        assert task.priority == TaskPriority.HIGH

    def test_task_create_validation_empty_title(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValidationError):
            TaskCreate(title="")

    def test_task_create_tag_validation(self):
        """Test tag length validation."""
        with pytest.raises(ValidationError):
            TaskCreate(
                title="Task",
                tags=["a" * 51]  # Tag exceeds 50 char limit
            )

    def test_task_priority_from_string(self):
        """Test priority conversion from string."""
        assert TaskPriority.from_string("high") == TaskPriority.HIGH
        assert TaskPriority.from_string("medium") == TaskPriority.MEDIUM
        assert TaskPriority.from_string("low") == TaskPriority.LOW
        assert TaskPriority.from_string("none") == TaskPriority.NONE
        assert TaskPriority.from_string("invalid") == TaskPriority.NONE

    def test_task_status_to_emoji(self):
        """Test status emoji conversion."""
        assert TaskStatus.COMPLETE.to_emoji() == ""
        assert TaskStatus.INCOMPLETE.to_emoji() == ""

    def test_checklist_item(self):
        """Test checklist item model."""
        item = ChecklistItem(title="Subtask 1")

        assert item.title == "Subtask 1"
        assert item.status == TaskStatus.INCOMPLETE


class TestProjectModels:
    """Tests for project-related models."""

    def test_project_from_api_response(self, sample_project):
        """Test creating a Project from API response."""
        project = Project(**sample_project)

        assert project.id == "project456"
        assert project.name == "Test Project"
        assert project.color == "#FF5733"

    def test_project_create_minimal(self):
        """Test creating a project with minimal data."""
        project = ProjectCreate(name="My Project")

        assert project.name == "My Project"
        assert project.color is None


class TestAuthModels:
    """Tests for authentication models."""

    def test_oauth_token(self):
        """Test OAuth token model."""
        token = OAuthToken(
            access_token="test_access_token",
            token_type="Bearer",
            expires_in=86400,
            scope="tasks:read tasks:write",
        )

        assert token.access_token == "test_access_token"
        assert token.token_type == "Bearer"
        assert token.scope == "tasks:read tasks:write"

    def test_oauth_token_time_until_expiry(self):
        """Test token expiry calculation."""
        token = OAuthToken(
            access_token="test",
            token_type="Bearer",
            expires_in=3600,
            scope="tasks:read",
        )

        # Should be approximately 3600 seconds
        assert 3590 <= token.time_until_expiry() <= 3600

    def test_session_token(self):
        """Test session token model."""
        token = SessionToken(
            token="session_token_value",
            user_id="user123",
            inbox_id="inbox456",
        )

        assert token.token == "session_token_value"
        assert token.user_id == "user123"
        assert token.inbox_id == "inbox456"
