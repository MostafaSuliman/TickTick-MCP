#!/usr/bin/env python3
"""
TickTick MCP Server - A comprehensive MCP server for TickTick task management.

This server provides tools for managing tasks, projects (lists), and time scheduling
through TickTick's API.

Author: Claude (built for Mostafa)
"""

import os
import json
import httpx
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Configuration and Constants
# ============================================================================

TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"
TICKTICK_AUTH_URL = "https://ticktick.com/oauth/authorize"
TICKTICK_TOKEN_URL = "https://ticktick.com/oauth/token"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8080/callback"
TOKEN_CACHE_FILE = Path.home() / ".ticktick-mcp-token.json"
CONFIG_FILE = Path.home() / ".ticktick-mcp-config.json"

# Initialize MCP Server
mcp = FastMCP("ticktick_mcp")


# ============================================================================
# Enums and Models
# ============================================================================

class TaskPriority(int, Enum):
    """Task priority levels in TickTick."""
    NONE = 0
    LOW = 1
    MEDIUM = 3
    HIGH = 5


class TaskStatus(int, Enum):
    """Task status values."""
    INCOMPLETE = 0
    COMPLETE = 2


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Pydantic Input Models
# ============================================================================

class ConfigureInput(BaseModel):
    """Input model for configuring TickTick credentials."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    client_id: str = Field(..., description="Your TickTick app Client ID from https://developer.ticktick.com/manage", min_length=1)
    client_secret: str = Field(..., description="Your TickTick app Client Secret", min_length=1)
    redirect_uri: str = Field(default=DEFAULT_REDIRECT_URI, description="OAuth redirect URI (default: http://127.0.0.1:8080/callback)")


class AuthorizeInput(BaseModel):
    """Input model for completing OAuth authorization."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    authorization_code: str = Field(..., description="The authorization code from the callback URL (the 'code' parameter)", min_length=1)


class ListTasksInput(BaseModel):
    """Input model for listing tasks."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    project_id: Optional[str] = Field(default=None, description="Filter by project/list ID. Use 'inbox' for inbox tasks.")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'")


class GetTaskInput(BaseModel):
    """Input model for getting a specific task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    task_id: str = Field(..., description="The task ID to retrieve", min_length=1)
    project_id: str = Field(..., description="The project/list ID containing the task", min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class CreateTaskInput(BaseModel):
    """Input model for creating a new task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    title: str = Field(..., description="Task title", min_length=1, max_length=500)
    content: Optional[str] = Field(default=None, description="Task description/content", max_length=5000)
    project_id: Optional[str] = Field(default=None, description="Project/list ID. Leave empty for inbox.")
    start_date: Optional[str] = Field(default=None, description="Start date in ISO format (e.g., '2025-01-15' or '2025-01-15T14:30:00+00:00')")
    due_date: Optional[str] = Field(default=None, description="Due date in ISO format")
    priority: TaskPriority = Field(default=TaskPriority.NONE, description="Priority: 0=None, 1=Low, 3=Medium, 5=High")
    tags: Optional[List[str]] = Field(default=None, description="List of tag names to apply", max_length=10)
    all_day: bool = Field(default=True, description="Whether this is an all-day task")
    time_zone: Optional[str] = Field(default=None, description="Time zone (e.g., 'Africa/Cairo')")


class UpdateTaskInput(BaseModel):
    """Input model for updating a task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    task_id: str = Field(..., description="The task ID to update", min_length=1)
    project_id: str = Field(..., description="The project/list ID containing the task", min_length=1)
    title: Optional[str] = Field(default=None, description="New task title", max_length=500)
    content: Optional[str] = Field(default=None, description="New task description", max_length=5000)
    start_date: Optional[str] = Field(default=None, description="New start date in ISO format")
    due_date: Optional[str] = Field(default=None, description="New due date in ISO format")
    priority: Optional[TaskPriority] = Field(default=None, description="New priority level")
    tags: Optional[List[str]] = Field(default=None, description="New list of tags")


class CompleteTaskInput(BaseModel):
    """Input model for completing a task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    task_id: str = Field(..., description="The task ID to complete", min_length=1)
    project_id: str = Field(..., description="The project/list ID containing the task", min_length=1)


class DeleteTaskInput(BaseModel):
    """Input model for deleting a task."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    task_id: str = Field(..., description="The task ID to delete", min_length=1)
    project_id: str = Field(..., description="The project/list ID containing the task", min_length=1)


class ListProjectsInput(BaseModel):
    """Input model for listing projects/lists."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class CreateProjectInput(BaseModel):
    """Input model for creating a project/list."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    name: str = Field(..., description="Project/list name", min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, description="Color in hex format (e.g., '#FF0000')")
    folder_id: Optional[str] = Field(default=None, description="Parent folder ID")


class DeleteProjectInput(BaseModel):
    """Input model for deleting a project."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    project_id: str = Field(..., description="The project/list ID to delete", min_length=1)


class ScheduleTimeInput(BaseModel):
    """Input model for scheduling/planning time."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    date: Optional[str] = Field(default=None, description="Date to plan for in ISO format (defaults to today)")
    include_completed: bool = Field(default=False, description="Include completed tasks in analysis")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


class GetCompletedTasksInput(BaseModel):
    """Input model for getting completed tasks."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    from_date: Optional[str] = Field(default=None, description="Start date for completed tasks range (ISO format)")
    to_date: Optional[str] = Field(default=None, description="End date for completed tasks range (ISO format)")
    project_id: Optional[str] = Field(default=None, description="Filter by project ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")


# ============================================================================
# Helper Functions
# ============================================================================

def load_config() -> Dict[str, str]:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_config(config: Dict[str, str]) -> None:
    """Save configuration to file."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_token() -> Optional[Dict[str, Any]]:
    """Load cached access token."""
    if TOKEN_CACHE_FILE.exists():
        try:
            token_data = json.loads(TOKEN_CACHE_FILE.read_text())
            # Check if token is expired
            if 'expire_time' in token_data:
                if datetime.now().timestamp() < token_data['expire_time']:
                    return token_data
        except Exception:
            pass
    return None


def save_token(token_data: Dict[str, Any]) -> None:
    """Save access token to cache."""
    TOKEN_CACHE_FILE.write_text(json.dumps(token_data, indent=2))


def get_access_token() -> Optional[str]:
    """Get valid access token or None if not authenticated."""
    token_data = load_token()
    if token_data:
        return token_data.get('access_token')
    return None


async def api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make an authenticated API request to TickTick."""
    access_token = get_access_token()
    if not access_token:
        raise Exception("Not authenticated. Please run ticktick_configure and ticktick_authorize first.")
    
    url = f"{TICKTICK_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code == 401:
            raise Exception("Access token expired or invalid. Please re-authenticate using ticktick_authorize.")
        elif response.status_code == 404:
            raise Exception("Resource not found. Please check the task/project ID.")
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded. Please wait before making more requests.")
        
        response.raise_for_status()
        
        if response.status_code == 204 or not response.content:
            return {"success": True}
        
        return response.json()


def format_task_markdown(task: Dict) -> str:
    """Format a task as markdown."""
    priority_map = {0: "None", 1: "🟢 Low", 3: "🟡 Medium", 5: "🔴 High"}
    priority = priority_map.get(task.get('priority', 0), "None")
    status = "✅ Complete" if task.get('status', 0) == 2 else "⬜ Incomplete"
    
    lines = [
        f"### {task.get('title', 'Untitled')}",
        f"- **ID**: `{task.get('id', 'N/A')}`",
        f"- **Status**: {status}",
        f"- **Priority**: {priority}",
    ]
    
    if task.get('projectId'):
        lines.append(f"- **Project ID**: `{task.get('projectId')}`")
    
    if task.get('content'):
        lines.append(f"- **Description**: {task.get('content')}")
    
    if task.get('dueDate'):
        lines.append(f"- **Due Date**: {task.get('dueDate')}")
    
    if task.get('startDate'):
        lines.append(f"- **Start Date**: {task.get('startDate')}")
    
    if task.get('tags'):
        tags = ', '.join([f"`{t}`" for t in task.get('tags', [])])
        lines.append(f"- **Tags**: {tags}")
    
    if task.get('items'):  # Subtasks/checklist items
        lines.append("- **Checklist**:")
        for item in task.get('items', []):
            check = "✅" if item.get('status', 0) == 2 else "⬜"
            lines.append(f"  - {check} {item.get('title', '')}")
    
    return '\n'.join(lines)


def format_project_markdown(project: Dict) -> str:
    """Format a project as markdown."""
    lines = [
        f"### {project.get('name', 'Untitled')}",
        f"- **ID**: `{project.get('id', 'N/A')}`",
    ]
    
    if project.get('color'):
        lines.append(f"- **Color**: {project.get('color')}")
    
    if project.get('groupId'):
        lines.append(f"- **Folder ID**: `{project.get('groupId')}`")
    
    if project.get('viewMode'):
        lines.append(f"- **View Mode**: {project.get('viewMode')}")
    
    return '\n'.join(lines)


# ============================================================================
# MCP Tools - Authentication
# ============================================================================

@mcp.tool(
    name="ticktick_configure",
    annotations={
        "title": "Configure TickTick Credentials",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ticktick_configure(params: ConfigureInput) -> str:
    """Configure TickTick API credentials and initiate OAuth flow.
    
    Step 1: Register an app at https://developer.ticktick.com/manage
    Step 2: Use this tool to configure your credentials
    Step 3: Visit the authorization URL provided
    Step 4: Use ticktick_authorize with the code from the callback URL
    
    Args:
        params (ConfigureInput): Contains client_id, client_secret, and redirect_uri
    
    Returns:
        str: Instructions for completing OAuth authorization
    """
    config = {
        "client_id": params.client_id,
        "client_secret": params.client_secret,
        "redirect_uri": params.redirect_uri
    }
    save_config(config)
    
    # Generate authorization URL
    auth_url = (
        f"{TICKTICK_AUTH_URL}"
        f"?client_id={params.client_id}"
        f"&scope=tasks:read tasks:write"
        f"&response_type=code"
        f"&redirect_uri={params.redirect_uri}"
        f"&state=mcp_auth"
    )
    
    return f"""## TickTick Configuration Saved! ✅

**Next Steps:**

1. **Visit this URL to authorize the app:**
   
   {auth_url}

2. **After authorizing**, you'll be redirected to:
   `{params.redirect_uri}?code=AUTHORIZATION_CODE&state=mcp_auth`

3. **Copy the `code` parameter** from the URL and use it with:
   `ticktick_authorize` tool with the authorization_code

**Note**: The redirect URL doesn't need to be a live server. You just need to copy the `code` parameter from the URL bar after redirecting.

---

*Configuration saved to: `{CONFIG_FILE}`*
"""


@mcp.tool(
    name="ticktick_authorize",
    annotations={
        "title": "Complete TickTick Authorization",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def ticktick_authorize(params: AuthorizeInput) -> str:
    """Complete OAuth authorization with the authorization code.
    
    Use this after visiting the authorization URL and getting the code.
    
    Args:
        params (AuthorizeInput): Contains the authorization code from callback URL
    
    Returns:
        str: Success message or error details
    """
    config = load_config()
    if not config.get('client_id') or not config.get('client_secret'):
        return "❌ **Error**: Please run `ticktick_configure` first to set up your credentials."
    
    # Exchange authorization code for access token
    token_data = {
        "client_id": config['client_id'],
        "client_secret": config['client_secret'],
        "code": params.authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": config.get('redirect_uri', DEFAULT_REDIRECT_URI),
        "scope": "tasks:read tasks:write"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TICKTICK_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_response = response.json()
        
        # Calculate expiration time
        expires_in = token_response.get('expires_in', 15552000)  # Default 180 days
        token_response['expire_time'] = datetime.now().timestamp() + expires_in
        token_response['readable_expire_time'] = (
            datetime.now() + timedelta(seconds=expires_in)
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        save_token(token_response)
        
        return f"""## ✅ Authorization Successful!

**Token Details:**
- **Token Type**: {token_response.get('token_type', 'bearer')}
- **Scope**: {token_response.get('scope', 'tasks:read tasks:write')}
- **Expires**: {token_response['readable_expire_time']}

You can now use all TickTick tools:
- `ticktick_list_tasks` - View your tasks
- `ticktick_create_task` - Create new tasks
- `ticktick_complete_task` - Mark tasks as complete
- `ticktick_list_projects` - View your projects/lists
- `ticktick_schedule_time` - Get a schedule for your day

---

*Token cached to: `{TOKEN_CACHE_FILE}`*
"""
    except httpx.HTTPStatusError as e:
        return f"❌ **Authorization Failed**: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"


@mcp.tool(
    name="ticktick_check_auth",
    annotations={
        "title": "Check TickTick Authentication Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ticktick_check_auth() -> str:
    """Check if TickTick is authenticated and token is valid.
    
    Returns:
        str: Authentication status information
    """
    config = load_config()
    token_data = load_token()
    
    status_lines = ["## TickTick Authentication Status\n"]
    
    if config.get('client_id'):
        status_lines.append(f"✅ **Configuration**: Found (Client ID: `{config['client_id'][:8]}...`)")
    else:
        status_lines.append("❌ **Configuration**: Not configured. Run `ticktick_configure` first.")
    
    if token_data:
        expire_time = token_data.get('readable_expire_time', 'Unknown')
        status_lines.append(f"✅ **Token**: Valid (Expires: {expire_time})")
        status_lines.append(f"   - Scope: {token_data.get('scope', 'Unknown')}")
    else:
        status_lines.append("❌ **Token**: Not found or expired. Run `ticktick_authorize`.")
    
    return '\n'.join(status_lines)


# ============================================================================
# MCP Tools - Tasks
# ============================================================================

@mcp.tool(
    name="ticktick_list_tasks",
    annotations={
        "title": "List TickTick Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_list_tasks(params: ListTasksInput) -> str:
    """List all incomplete tasks from TickTick.
    
    Args:
        params (ListTasksInput): Filter options and response format
    
    Returns:
        str: List of tasks in markdown or JSON format
    """
    try:
        # Get all tasks (TickTick API doesn't have direct filter by project in list endpoint)
        # We need to get project data first, then filter
        if params.project_id:
            # Get specific project's tasks
            data = await api_request("GET", f"/project/{params.project_id}/data")
            tasks = data.get('tasks', [])
        else:
            # Get all projects and aggregate tasks
            projects = await api_request("GET", "/project")
            all_tasks = []
            for project in projects:
                try:
                    data = await api_request("GET", f"/project/{project['id']}/data")
                    all_tasks.extend(data.get('tasks', []))
                except Exception:
                    continue
            tasks = all_tasks
        
        # Filter to incomplete tasks only
        tasks = [t for t in tasks if t.get('status', 0) != 2]
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"tasks": tasks, "count": len(tasks)}, indent=2)
        
        if not tasks:
            return "## 📋 No incomplete tasks found.\n\nYou're all caught up! 🎉"
        
        lines = [f"## 📋 Tasks ({len(tasks)} incomplete)\n"]
        
        # Group by project
        tasks_by_project: Dict[str, List] = {}
        for task in tasks:
            proj_id = task.get('projectId', 'inbox')
            if proj_id not in tasks_by_project:
                tasks_by_project[proj_id] = []
            tasks_by_project[proj_id].append(task)
        
        for proj_id, proj_tasks in tasks_by_project.items():
            lines.append(f"\n### Project: `{proj_id}`\n")
            for task in sorted(proj_tasks, key=lambda x: x.get('priority', 0), reverse=True):
                lines.append(format_task_markdown(task))
                lines.append("")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"❌ **Error listing tasks**: {str(e)}"


@mcp.tool(
    name="ticktick_get_task",
    annotations={
        "title": "Get Specific Task",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_get_task(params: GetTaskInput) -> str:
    """Get details of a specific task.
    
    Args:
        params (GetTaskInput): Task ID and project ID to fetch
    
    Returns:
        str: Task details in markdown or JSON format
    """
    try:
        task = await api_request("GET", f"/project/{params.project_id}/task/{params.task_id}")
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(task, indent=2)
        
        return format_task_markdown(task)
        
    except Exception as e:
        return f"❌ **Error getting task**: {str(e)}"


@mcp.tool(
    name="ticktick_create_task",
    annotations={
        "title": "Create TickTick Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def ticktick_create_task(params: CreateTaskInput) -> str:
    """Create a new task in TickTick.
    
    Args:
        params (CreateTaskInput): Task details including title, dates, priority, etc.
    
    Returns:
        str: Created task details
    """
    try:
        task_data: Dict[str, Any] = {
            "title": params.title
        }
        
        if params.content:
            task_data["content"] = params.content
        
        if params.project_id:
            task_data["projectId"] = params.project_id
        
        if params.start_date:
            task_data["startDate"] = params.start_date
            task_data["isAllDay"] = params.all_day
        
        if params.due_date:
            task_data["dueDate"] = params.due_date
            task_data["isAllDay"] = params.all_day
        
        if params.priority:
            task_data["priority"] = params.priority.value
        
        if params.tags:
            task_data["tags"] = params.tags
        
        if params.time_zone:
            task_data["timeZone"] = params.time_zone
        
        task = await api_request("POST", "/task", data=task_data)
        
        return f"""## ✅ Task Created Successfully!

{format_task_markdown(task)}

---

**Task ID**: `{task.get('id')}`
**Project ID**: `{task.get('projectId', 'inbox')}`

Use these IDs to update or complete the task.
"""
        
    except Exception as e:
        return f"❌ **Error creating task**: {str(e)}"


@mcp.tool(
    name="ticktick_update_task",
    annotations={
        "title": "Update TickTick Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_update_task(params: UpdateTaskInput) -> str:
    """Update an existing task in TickTick.
    
    Args:
        params (UpdateTaskInput): Task ID and fields to update
    
    Returns:
        str: Updated task details
    """
    try:
        # First get the existing task
        existing_task = await api_request("GET", f"/project/{params.project_id}/task/{params.task_id}")
        
        # Merge updates
        if params.title:
            existing_task["title"] = params.title
        if params.content is not None:
            existing_task["content"] = params.content
        if params.start_date:
            existing_task["startDate"] = params.start_date
        if params.due_date:
            existing_task["dueDate"] = params.due_date
        if params.priority is not None:
            existing_task["priority"] = params.priority.value
        if params.tags is not None:
            existing_task["tags"] = params.tags
        
        # Update the task
        task = await api_request("POST", f"/task/{params.task_id}", data=existing_task)
        
        return f"""## ✅ Task Updated Successfully!

{format_task_markdown(task)}
"""
        
    except Exception as e:
        return f"❌ **Error updating task**: {str(e)}"


@mcp.tool(
    name="ticktick_complete_task",
    annotations={
        "title": "Complete TickTick Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_complete_task(params: CompleteTaskInput) -> str:
    """Mark a task as complete in TickTick.
    
    Args:
        params (CompleteTaskInput): Task ID and project ID
    
    Returns:
        str: Confirmation message
    """
    try:
        await api_request("POST", f"/project/{params.project_id}/task/{params.task_id}/complete")
        
        return f"""## ✅ Task Completed!

**Task ID**: `{params.task_id}`
**Project ID**: `{params.project_id}`

Great job! 🎉
"""
        
    except Exception as e:
        return f"❌ **Error completing task**: {str(e)}"


@mcp.tool(
    name="ticktick_delete_task",
    annotations={
        "title": "Delete TickTick Task",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_delete_task(params: DeleteTaskInput) -> str:
    """Delete a task from TickTick.
    
    Args:
        params (DeleteTaskInput): Task ID and project ID
    
    Returns:
        str: Confirmation message
    """
    try:
        await api_request("DELETE", f"/project/{params.project_id}/task/{params.task_id}")
        
        return f"""## 🗑️ Task Deleted

**Task ID**: `{params.task_id}`
**Project ID**: `{params.project_id}`

The task has been permanently deleted.
"""
        
    except Exception as e:
        return f"❌ **Error deleting task**: {str(e)}"


# ============================================================================
# MCP Tools - Projects/Lists
# ============================================================================

@mcp.tool(
    name="ticktick_list_projects",
    annotations={
        "title": "List TickTick Projects/Lists",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_list_projects(params: ListProjectsInput) -> str:
    """List all projects/lists in TickTick.
    
    Args:
        params (ListProjectsInput): Response format option
    
    Returns:
        str: List of projects in markdown or JSON format
    """
    try:
        projects = await api_request("GET", "/project")
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"projects": projects, "count": len(projects)}, indent=2)
        
        if not projects:
            return "## 📂 No projects found.\n\nCreate your first project with `ticktick_create_project`!"
        
        lines = [f"## 📂 Projects/Lists ({len(projects)} total)\n"]
        
        for project in projects:
            lines.append(format_project_markdown(project))
            lines.append("")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"❌ **Error listing projects**: {str(e)}"


@mcp.tool(
    name="ticktick_create_project",
    annotations={
        "title": "Create TickTick Project/List",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def ticktick_create_project(params: CreateProjectInput) -> str:
    """Create a new project/list in TickTick.
    
    Args:
        params (CreateProjectInput): Project name and optional settings
    
    Returns:
        str: Created project details
    """
    try:
        project_data: Dict[str, Any] = {
            "name": params.name
        }
        
        if params.color:
            project_data["color"] = params.color
        
        if params.folder_id:
            project_data["groupId"] = params.folder_id
        
        project = await api_request("POST", "/project", data=project_data)
        
        return f"""## ✅ Project Created Successfully!

{format_project_markdown(project)}

---

Use the Project ID `{project.get('id')}` when creating tasks.
"""
        
    except Exception as e:
        return f"❌ **Error creating project**: {str(e)}"


@mcp.tool(
    name="ticktick_delete_project",
    annotations={
        "title": "Delete TickTick Project/List",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_delete_project(params: DeleteProjectInput) -> str:
    """Delete a project/list from TickTick.
    
    ⚠️ WARNING: This will delete all tasks in the project!
    
    Args:
        params (DeleteProjectInput): Project ID to delete
    
    Returns:
        str: Confirmation message
    """
    try:
        await api_request("DELETE", f"/project/{params.project_id}")
        
        return f"""## 🗑️ Project Deleted

**Project ID**: `{params.project_id}`

The project and all its tasks have been permanently deleted.
"""
        
    except Exception as e:
        return f"❌ **Error deleting project**: {str(e)}"


# ============================================================================
# MCP Tools - Time Management / Scheduling
# ============================================================================

@mcp.tool(
    name="ticktick_schedule_time",
    annotations={
        "title": "Generate Daily Schedule",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_schedule_time(params: ScheduleTimeInput) -> str:
    """Analyze tasks and generate a suggested daily schedule.
    
    This tool fetches your tasks and organizes them into a time-based schedule,
    prioritizing by due date and priority level.
    
    Args:
        params (ScheduleTimeInput): Date to plan and format options
    
    Returns:
        str: Suggested schedule with time blocks
    """
    try:
        target_date = params.date or datetime.now().strftime('%Y-%m-%d')
        
        # Fetch all projects and their tasks
        projects = await api_request("GET", "/project")
        all_tasks = []
        project_names: Dict[str, str] = {}
        
        for project in projects:
            project_names[project['id']] = project.get('name', 'Unknown')
            try:
                data = await api_request("GET", f"/project/{project['id']}/data")
                for task in data.get('tasks', []):
                    task['_project_name'] = project.get('name', 'Unknown')
                    all_tasks.append(task)
            except Exception:
                continue
        
        # Filter tasks
        if not params.include_completed:
            all_tasks = [t for t in all_tasks if t.get('status', 0) != 2]
        
        # Categorize tasks
        today = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        overdue = []
        due_today = []
        upcoming = []
        no_date = []
        
        for task in all_tasks:
            due_str = task.get('dueDate') or task.get('startDate')
            if due_str:
                try:
                    # Parse the date (handle various formats)
                    due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00')).date()
                    if due_date < today:
                        overdue.append(task)
                    elif due_date == today:
                        due_today.append(task)
                    else:
                        upcoming.append(task)
                except Exception:
                    no_date.append(task)
            else:
                no_date.append(task)
        
        # Sort by priority (high to low)
        def sort_key(t):
            return -t.get('priority', 0)
        
        overdue.sort(key=sort_key)
        due_today.sort(key=sort_key)
        upcoming.sort(key=sort_key)
        no_date.sort(key=sort_key)
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "date": target_date,
                "overdue": overdue,
                "due_today": due_today,
                "upcoming": upcoming[:5],  # Next 5 upcoming
                "no_date": no_date[:10]  # First 10 without dates
            }, indent=2)
        
        # Generate markdown schedule
        lines = [
            f"## 📅 Schedule for {target_date}",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            ""
        ]
        
        # Summary
        total_today = len(overdue) + len(due_today)
        lines.extend([
            "### 📊 Summary",
            f"- **Overdue**: {len(overdue)} tasks",
            f"- **Due Today**: {len(due_today)} tasks",
            f"- **Upcoming**: {len(upcoming)} tasks",
            f"- **Unscheduled**: {len(no_date)} tasks",
            ""
        ])
        
        # Priority Focus Section
        lines.append("---")
        lines.append("### 🎯 Priority Focus (Do First)")
        lines.append("")
        
        if overdue:
            lines.append("#### 🔴 OVERDUE - Handle Immediately")
            for task in overdue[:5]:
                priority_emoji = "🔴" if task.get('priority', 0) >= 5 else "🟡" if task.get('priority', 0) >= 3 else "⚪"
                lines.append(f"- {priority_emoji} **{task.get('title')}** (`{task.get('_project_name')}`)")
                if task.get('dueDate'):
                    lines.append(f"  - Due: {task.get('dueDate')[:10]}")
            lines.append("")
        
        if due_today:
            lines.append("#### 📌 Due Today")
            for task in due_today:
                priority_emoji = "🔴" if task.get('priority', 0) >= 5 else "🟡" if task.get('priority', 0) >= 3 else "⚪"
                lines.append(f"- {priority_emoji} **{task.get('title')}** (`{task.get('_project_name')}`)")
            lines.append("")
        
        # Suggested Time Blocks
        lines.append("---")
        lines.append("### ⏰ Suggested Time Blocks")
        lines.append("")
        
        high_priority = [t for t in (overdue + due_today + no_date) if t.get('priority', 0) >= 5]
        medium_priority = [t for t in (overdue + due_today + no_date) if t.get('priority', 0) == 3]
        low_priority = [t for t in (overdue + due_today + no_date) if t.get('priority', 0) <= 1]
        
        lines.append("**Morning Focus (9:00 - 12:00)** - High Priority Tasks")
        if high_priority:
            for task in high_priority[:3]:
                lines.append(f"- [ ] {task.get('title')}")
        else:
            lines.append("- No high priority tasks!")
        lines.append("")
        
        lines.append("**Afternoon Work (13:00 - 17:00)** - Medium Priority Tasks")
        if medium_priority:
            for task in medium_priority[:4]:
                lines.append(f"- [ ] {task.get('title')}")
        else:
            lines.append("- No medium priority tasks!")
        lines.append("")
        
        lines.append("**End of Day (17:00 - 18:00)** - Quick Wins / Low Priority")
        if low_priority:
            for task in low_priority[:3]:
                lines.append(f"- [ ] {task.get('title')}")
        else:
            lines.append("- No low priority tasks!")
        lines.append("")
        
        # Upcoming Preview
        if upcoming:
            lines.append("---")
            lines.append("### 📆 Coming Up")
            lines.append("")
            for task in upcoming[:5]:
                due = task.get('dueDate', task.get('startDate', ''))[:10] if task.get('dueDate') or task.get('startDate') else 'No date'
                lines.append(f"- **{due}**: {task.get('title')} (`{task.get('_project_name')}`)")
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"❌ **Error generating schedule**: {str(e)}"


@mcp.tool(
    name="ticktick_get_today",
    annotations={
        "title": "Get Today's Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def ticktick_get_today() -> str:
    """Get all tasks due today or overdue.
    
    Quick view of what needs attention today.
    
    Returns:
        str: Today's tasks organized by priority
    """
    try:
        # Use schedule_time with today's date
        return await ticktick_schedule_time(ScheduleTimeInput(
            date=datetime.now().strftime('%Y-%m-%d'),
            include_completed=False,
            response_format=ResponseFormat.MARKDOWN
        ))
        
    except Exception as e:
        return f"❌ **Error getting today's tasks**: {str(e)}"


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
