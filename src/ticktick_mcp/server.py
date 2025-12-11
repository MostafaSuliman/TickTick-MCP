"""
TickTick MCP Server - Production-ready Model Context Protocol server.

This is the main entry point for the TickTick MCP server.
Provides comprehensive task management, habit tracking, focus timer,
and productivity analytics via both official v1 and unofficial v2 APIs.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .api.client import TickTickClient
from .services import (
    AuthService,
    TaskService,
    ProjectService,
    TagService,
    HabitService,
    FocusService,
    StatisticsService,
)
from .tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("ticktick-mcp")


def create_server(
    name: str = "ticktick-mcp",
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    access_token: Optional[str] = None,
) -> FastMCP:
    """
    Create and configure the TickTick MCP server.

    Args:
        name: Server name for MCP identification
        client_id: OAuth2 Client ID (optional, can be configured later)
        client_secret: OAuth2 Client Secret (optional)
        access_token: Pre-existing access token (optional)

    Returns:
        Configured FastMCP server instance
    """
    # Create FastMCP server with instructions
    mcp = FastMCP(
        name,
        instructions="""
TickTick MCP Server - Comprehensive task management, habit tracking, and productivity tools.

## Authentication

This server supports two authentication methods:

### 1. OAuth2 (v1 API - Official)
For basic task and project management:
1. Use `ticktick_configure_oauth` with your Client ID and Secret from the TickTick Developer Portal
2. Visit the authorization URL provided
3. Use `ticktick_authorize_oauth` with the code from the callback URL

### 2. Username/Password (v2 API - Extended)
For full features including tags, habits, focus timer, and statistics:
- Use `ticktick_login` with your TickTick username and password

## Available Features

### Tasks (v1 + v2)
- `ticktick_list_tasks` - List all tasks with filtering
- `ticktick_create_task` - Create new tasks
- `ticktick_update_task` - Update existing tasks
- `ticktick_complete_task` - Mark tasks complete
- `ticktick_delete_task` - Delete tasks
- `ticktick_move_task` - Move tasks between projects
- `ticktick_batch_create_tasks` - Create multiple tasks at once

### Projects (v1 + v2)
- `ticktick_list_projects` - List all projects/lists
- `ticktick_create_project` - Create new projects
- `ticktick_update_project` - Update projects
- `ticktick_delete_project` - Delete projects
- `ticktick_list_folders` - List project folders

### Tags (v2 only)
- `ticktick_list_tags` - List all tags
- `ticktick_create_tag` - Create new tags
- `ticktick_rename_tag` - Rename tags
- `ticktick_merge_tags` - Merge tags together

### Habits (v2 only)
- `ticktick_list_habits` - List all habits
- `ticktick_create_habit` - Create new habits
- `ticktick_checkin_habit` - Record habit check-ins
- `ticktick_get_today_habits` - Get today's habit status

### Focus/Pomodoro (v2 only)
- `ticktick_start_pomodoro` - Start a Pomodoro session
- `ticktick_start_stopwatch` - Start a stopwatch session
- `ticktick_stop_focus` - Stop current focus session
- `ticktick_get_today_focus` - Get today's focus statistics

### Statistics
- `ticktick_get_overview` - Get productivity overview
- `ticktick_get_productivity_score` - Calculate productivity score
- `ticktick_get_weekly_report` - Get weekly productivity report
- `ticktick_get_task_analytics` - Get task analytics

## Notes
- v2 features require username/password authentication
- OAuth2 provides access to official API endpoints only
- For full functionality, use both authentication methods
""",
    )

    # Initialize API client
    client = TickTickClient()

    # Apply pre-configured credentials if provided
    if client_id and client_secret:
        client.configure_oauth(client_id, client_secret)
        logger.info("OAuth credentials pre-configured from environment")

    if access_token:
        # This would require a method to set the token directly
        # For now, tokens must be obtained through the auth flow
        logger.info("Pre-existing access token provided (not implemented)")

    # Initialize services
    services = {
        "auth": AuthService(client),
        "task": TaskService(client),
        "project": ProjectService(client),
        "tag": TagService(client),
        "habit": HabitService(client),
        "focus": FocusService(client),
        "statistics": StatisticsService(client),
    }

    # Register all MCP tools
    register_all_tools(mcp, services)
    logger.info(f"Registered MCP tools for {len(services)} services")

    return mcp


def main():
    """Main entry point for the MCP server."""
    # Check for environment variables
    client_id = os.environ.get("TICKTICK_CLIENT_ID")
    client_secret = os.environ.get("TICKTICK_CLIENT_SECRET")
    access_token = os.environ.get("TICKTICK_ACCESS_TOKEN")

    # Log startup info
    logger.info("Starting TickTick MCP Server")
    if client_id:
        logger.info("OAuth Client ID found in environment")
    if access_token:
        logger.info("Access token found in environment")

    # Create and run server
    server = create_server(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
    )

    # Run the server
    server.run()


if __name__ == "__main__":
    main()
