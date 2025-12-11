"""
TickTick MCP Tools - MCP tool definitions for all services.
"""

from .auth_tools import register_auth_tools
from .task_tools import register_task_tools
from .project_tools import register_project_tools
from .tag_tools import register_tag_tools
from .habit_tools import register_habit_tools
from .focus_tools import register_focus_tools
from .statistics_tools import register_statistics_tools
from .smart_tools import register_smart_tools
from .user_tools import register_user_tools
from .calendar_tools import register_calendar_tools
from .cache_tools import register_cache_tools


def register_all_tools(mcp, services, cache=None):
    """Register all MCP tools with the server."""
    register_auth_tools(mcp, services["auth"])
    register_task_tools(mcp, services["task"])
    register_project_tools(mcp, services["project"])
    register_tag_tools(mcp, services["tag"])
    register_habit_tools(mcp, services["habit"])
    register_focus_tools(mcp, services["focus"])
    register_statistics_tools(mcp, services["statistics"])
    register_smart_tools(mcp, services["smart"])
    register_user_tools(mcp, services["user"])
    register_calendar_tools(mcp, services["calendar"])

    # Register cache tools if cache is provided
    if cache:
        register_cache_tools(mcp, cache, services["task"])


__all__ = [
    "register_all_tools",
    "register_auth_tools",
    "register_task_tools",
    "register_project_tools",
    "register_tag_tools",
    "register_habit_tools",
    "register_focus_tools",
    "register_statistics_tools",
    "register_smart_tools",
    "register_user_tools",
    "register_calendar_tools",
    "register_cache_tools",
]
