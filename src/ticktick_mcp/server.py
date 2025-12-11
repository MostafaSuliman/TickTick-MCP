"""
TickTick MCP Server - Production-ready Model Context Protocol server.

This is the main entry point for the TickTick MCP server.
Provides comprehensive task management, habit tracking, focus timer,
and productivity analytics via both official v1 and unofficial v2 APIs.

Features 80+ tools covering:
- Task management (CRUD, batch, subtasks)
- Project management (folders, views)
- Tag management
- Habit tracking
- Focus/Pomodoro timer
- Statistics and analytics
- Smart views (today, tomorrow, overdue)
- Calendar integration
- Local cache system
"""

import asyncio
import logging
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .api.client import TickTickClient
from .cache import TaskCache
from .services import (
    AuthService,
    TaskService,
    ProjectService,
    TagService,
    HabitService,
    FocusService,
    StatisticsService,
    SmartService,
    UserService,
    CalendarService,
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

## 🚀 Quick Start

1. **Authenticate**: Use `ticktick_configure_oauth` + `ticktick_authorize_oauth` for basic features,
   or `ticktick_login` for full v2 API access.
2. **List Projects**: `ticktick_list_projects` to see your lists
3. **Create Tasks**: `ticktick_create_task` with title and optional due date
4. **View Today**: `ticktick_get_today` for today's tasks

## 🔐 Authentication

### Option 1: OAuth2 (v1 API - Official)
For basic task and project management:
1. Use `ticktick_configure_oauth` with Client ID/Secret from TickTick Developer Portal
2. Visit the authorization URL provided
3. Use `ticktick_authorize_oauth` with the callback code

### Option 2: Username/Password (v2 API - Extended)
For full features including habits, focus, tags, and statistics:
- Use `ticktick_login` with your TickTick credentials

## 📋 Tasks (80+ Tools Available)

### Core Task Operations
- `ticktick_list_tasks` - List tasks with filtering
- `ticktick_create_task` - Create new tasks
- `ticktick_update_task` - Update existing tasks
- `ticktick_complete_task` / `ticktick_uncomplete_task` - Toggle completion
- `ticktick_delete_task` - Delete tasks
- `ticktick_move_task` - Move between projects
- `ticktick_batch_create_tasks` / `ticktick_batch_delete_tasks` - Batch operations

### Smart Views (AI-Enhanced)
- `ticktick_get_today` - Today's tasks sorted by priority
- `ticktick_get_tomorrow` - Tomorrow's tasks
- `ticktick_get_overdue` - Overdue tasks
- `ticktick_get_next_7_days` - Weekly view
- `ticktick_search_tasks` - Full-text search
- `ticktick_get_unscheduled` - Tasks without dates
- `ticktick_get_high_priority` - Priority filter
- `ticktick_schedule_day` - AI scheduling suggestions
- `ticktick_productivity_summary` - Productivity insights

## 📁 Projects
- `ticktick_list_projects` - List all projects
- `ticktick_create_project` - Create new project
- `ticktick_update_project` / `ticktick_delete_project`
- `ticktick_archive_project` - Archive/unarchive
- `ticktick_list_folders` - Folder management

## 🏷️ Tags (v2)
- `ticktick_list_tags` - List all tags
- `ticktick_create_tag` - Create tag
- `ticktick_rename_tag` / `ticktick_merge_tags`

## 🎯 Habits (v2)
- `ticktick_list_habits` - List habits
- `ticktick_create_habit` - Create habit
- `ticktick_checkin_habit` - Record check-in
- `ticktick_get_today_habits` - Today's status
- `ticktick_get_habit_stats` - Statistics

## 🍅 Focus/Pomodoro (v2)
- `ticktick_start_pomodoro` - Start 25min session
- `ticktick_start_stopwatch` - Start stopwatch
- `ticktick_stop_focus` - Stop current session
- `ticktick_get_today_focus` - Today's focus stats

## 📅 Calendar (v2)
- `ticktick_calendar_today` - Today's events
- `ticktick_calendar_week` - This week's events
- `ticktick_calendar_events` - Custom date range

## 📊 Statistics
- `ticktick_get_overview` - Productivity overview
- `ticktick_get_productivity_score` - Score calculation
- `ticktick_get_weekly_report` - Weekly report
- `ticktick_get_task_analytics` - Task analytics

## 💾 Cache System
- `ticktick_cache_refresh` - Sync all tasks to cache
- `ticktick_cache_search` - Fast local search
- `ticktick_cache_get` - Get task project mapping
- `ticktick_cache_stats` - Cache statistics

## 👤 User
- `ticktick_get_profile` - User profile
- `ticktick_get_inbox_id` - Get inbox ID
- `ticktick_get_timezone` - User timezone

## ⚠️ Notes
- v2 features require username/password authentication
- OAuth2 provides basic task/project functionality
- Use cache system for faster task lookups
""",
    )

    # Initialize API client
    client = TickTickClient()

    # Initialize task cache
    cache = TaskCache()
    logger.info(f"Task cache initialized with {len(cache.list_all())} entries")

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
        "smart": SmartService(client),
        "user": UserService(client),
        "calendar": CalendarService(client),
    }

    # Register all MCP tools
    register_all_tools(mcp, services, cache)
    logger.info(f"Registered MCP tools for {len(services)} services + cache")

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
