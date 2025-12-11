"""
Pytest configuration and fixtures for TickTick MCP tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_client():
    """Create a mock TickTick API client."""
    client = MagicMock()
    client.is_authenticated = False
    client._oauth_token = None
    client._session_token = None
    client.inbox_id = None

    # Mock async methods
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()

    return client


@pytest.fixture
def authenticated_client(mock_client):
    """Create an authenticated mock client."""
    mock_client.is_authenticated = True
    mock_client._oauth_token = MagicMock()
    mock_client._oauth_token.access_token = "test_token"
    return mock_client


@pytest.fixture
def v2_authenticated_client(authenticated_client):
    """Create a v2 authenticated mock client."""
    authenticated_client._session_token = MagicMock()
    authenticated_client._session_token.token = "v2_session_token"
    authenticated_client.inbox_id = "inbox123"
    return authenticated_client


@pytest.fixture
def sample_task():
    """Sample task data."""
    return {
        "id": "task123",
        "projectId": "project456",
        "title": "Test Task",
        "content": "Task description",
        "status": 0,
        "priority": 3,
        "tags": ["work", "important"],
        "dueDate": "2024-12-31T23:59:59+0000",
        "createdTime": "2024-01-01T00:00:00+0000",
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": "project456",
        "name": "Test Project",
        "color": "#FF5733",
        "sortOrder": 0,
        "closed": False,
        "viewMode": "list",
    }


@pytest.fixture
def sample_tag():
    """Sample tag data."""
    return {
        "name": "work",
        "color": "#0066FF",
        "sortOrder": 0,
        "parent": None,
    }


@pytest.fixture
def sample_habit():
    """Sample habit data."""
    return {
        "id": "habit789",
        "name": "Exercise",
        "goal": 1,
        "unit": "times",
        "color": "#00FF00",
        "status": 1,
        "targetDays": "1234567",
    }


@pytest.fixture
def sample_focus_record():
    """Sample focus record data."""
    return {
        "id": "focus001",
        "focusType": "pomo",
        "duration": 1500,  # 25 minutes in seconds
        "startTime": "2024-01-01T10:00:00+0000",
        "endTime": "2024-01-01T10:25:00+0000",
        "taskId": "task123",
        "taskTitle": "Test Task",
    }
