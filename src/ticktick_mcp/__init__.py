"""
TickTick MCP Server - Production-Ready Task Management Integration

A comprehensive MCP (Model Context Protocol) server providing full access to
TickTick's task management platform, supporting both Official API (v1) and
Internal API (v2) for maximum functionality.

Features:
- Task Management (CRUD, batch operations, subtasks)
- Project/List Management (folders, archiving)
- Tag Management (create, merge, rename)
- Habit Tracking (check-ins, streaks)
- Focus/Pomodoro Timer (WebSocket real-time)
- Statistics & Analytics

Authentication:
- OAuth2 (v1 API): Official API with limited features
- Username/Password (v2 API): Extended features including tags, habits, focus

Author: TickTick MCP Team
License: MIT
"""

__version__ = "2.0.0"
__author__ = "TickTick MCP Team"

from .server import create_server, main
from .config import TickTickConfig

__all__ = ["create_server", "main", "TickTickConfig", "__version__"]
