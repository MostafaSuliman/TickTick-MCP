# TickTick MCP Server

[![PyPI version](https://badge.fury.io/py/ticktick-mcp.svg)](https://pypi.org/project/ticktick-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/MostafaSuliman/TickTick-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/MostafaSuliman/TickTick-MCP/actions)

A comprehensive MCP (Model Context Protocol) server for TickTick with **80+ tools** covering task management, habits, focus timer, and more. Manage your TickTick directly from Claude or any MCP-compatible AI assistant.

## Features

- **Task Management**: Create, update, complete, delete, search, and batch operations
- **Project Management**: Full CRUD with views (list, kanban, timeline)
- **Subtask Support**: Complete checklist item management
- **Tag Management**: Create, organize, and filter by tags
- **Habit Tracking**: Create habits, check-ins, streaks, and statistics
- **Focus/Pomodoro**: Start sessions, track time, view statistics
- **Calendar Integration**: View and sync calendar events
- **Smart Features**: Today/overdue tasks, AI scheduling suggestions
- **Cache System**: Local task discovery (solves API limitations)
- **OAuth2**: Secure authentication with auto-refresh

## Quick Start

### Installation

```bash
# Using pip (recommended)
pip install ticktick-mcp

# Using pipx (isolated environment)
pipx install ticktick-mcp

# From source
git clone https://github.com/MostafaSuliman/TickTick-MCP.git
cd TickTick-MCP
pip install -e .
```

### Setup

1. **Register a TickTick App**
   - Go to [TickTick Developer Portal](https://developer.ticktick.com/manage)
   - Create a new app
   - Set redirect URL to: `http://127.0.0.1:8080/callback`
   - Note your Client ID and Client Secret

2. **Authenticate**
   ```bash
   python scripts/get_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   ```
   Follow the browser prompts to authorize.

3. **Configure Claude Desktop**

   Add to `claude_desktop_config.json`:

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "ticktick": {
         "command": "ticktick-mcp",
         "env": {
           "TICKTICK_CLIENT_ID": "your_client_id",
           "TICKTICK_CLIENT_SECRET": "your_client_secret"
         }
       }
     }
   }
   ```

## Available Tools (80+)

### Authentication
| Tool | Description |
|------|-------------|
| `ticktick_configure_oauth` | Configure OAuth credentials |
| `ticktick_authorize_oauth` | Complete OAuth flow |
| `ticktick_login` | Login with username/password (v2 API) |
| `ticktick_auth_status` | Check authentication status |
| `ticktick_logout` | Clear all tokens |

### Task Management
| Tool | Description |
|------|-------------|
| `ticktick_list_tasks` | List tasks with filtering |
| `ticktick_get_task` | Get task details |
| `ticktick_create_task` | Create a new task |
| `ticktick_update_task` | Update task properties |
| `ticktick_complete_task` | Mark task as complete |
| `ticktick_uncomplete_task` | Reopen a completed task |
| `ticktick_delete_task` | Delete a task |
| `ticktick_move_task` | Move task between projects |
| `ticktick_create_subtask` | Create subtask |
| `ticktick_batch_create_tasks` | Create multiple tasks |
| `ticktick_batch_delete_tasks` | Delete multiple tasks |
| `ticktick_get_completed_tasks` | Get completed tasks |

### Smart Views
| Tool | Description |
|------|-------------|
| `ticktick_get_today` | Today's tasks sorted by priority |
| `ticktick_get_tomorrow` | Tomorrow's tasks |
| `ticktick_get_overdue` | Overdue tasks |
| `ticktick_get_next_7_days` | Weekly task view |
| `ticktick_search_tasks` | Full-text search |
| `ticktick_get_unscheduled` | Tasks without dates |
| `ticktick_get_high_priority` | High priority filter |
| `ticktick_schedule_day` | AI scheduling suggestions |
| `ticktick_productivity_summary` | Productivity insights |

### Project Management
| Tool | Description |
|------|-------------|
| `ticktick_list_projects` | List all projects |
| `ticktick_get_project` | Get project details |
| `ticktick_create_project` | Create new project |
| `ticktick_update_project` | Update project settings |
| `ticktick_delete_project` | Delete a project |
| `ticktick_archive_project` | Archive/unarchive project |
| `ticktick_list_folders` | List project folders |
| `ticktick_create_folder` | Create new folder |

### Tag Management (v2)
| Tool | Description |
|------|-------------|
| `ticktick_list_tags` | List all tags |
| `ticktick_get_tag_tasks` | Get tasks with specific tag |
| `ticktick_create_tag` | Create new tag |
| `ticktick_rename_tag` | Rename tag |
| `ticktick_merge_tags` | Merge tags |
| `ticktick_delete_tag` | Delete tag |

### Habit Tracking (v2)
| Tool | Description |
|------|-------------|
| `ticktick_list_habits` | List all habits |
| `ticktick_get_habit` | Get habit details |
| `ticktick_create_habit` | Create new habit |
| `ticktick_update_habit` | Update habit |
| `ticktick_delete_habit` | Delete habit |
| `ticktick_checkin_habit` | Record check-in |
| `ticktick_get_today_habits` | Today's habit status |
| `ticktick_get_habit_stats` | Habit statistics |

### Focus/Pomodoro (v2)
| Tool | Description |
|------|-------------|
| `ticktick_start_pomodoro` | Start 25min Pomodoro session |
| `ticktick_start_stopwatch` | Start stopwatch session |
| `ticktick_stop_focus` | Stop current session |
| `ticktick_get_today_focus` | Today's focus statistics |
| `ticktick_get_focus_records` | Focus session history |
| `ticktick_get_focus_settings` | Pomodoro settings |

### Calendar (v2)
| Tool | Description |
|------|-------------|
| `ticktick_calendar_today` | Today's events |
| `ticktick_calendar_week` | This week's events |
| `ticktick_calendar_events` | Custom date range |
| `ticktick_calendars_list` | List connected calendars |

### Statistics
| Tool | Description |
|------|-------------|
| `ticktick_get_overview` | Productivity overview |
| `ticktick_get_productivity_score` | Score calculation |
| `ticktick_get_weekly_report` | Weekly report |
| `ticktick_get_task_analytics` | Task analytics |

### Cache System
| Tool | Description |
|------|-------------|
| `ticktick_cache_refresh` | Sync all tasks to cache |
| `ticktick_cache_search` | Fast local search |
| `ticktick_cache_get` | Get task project mapping |
| `ticktick_cache_stats` | Cache statistics |
| `ticktick_cache_export` | Export to CSV |
| `ticktick_cache_import` | Import from CSV |

### User/Settings
| Tool | Description |
|------|-------------|
| `ticktick_get_profile` | User profile info |
| `ticktick_get_inbox_id` | Get inbox project ID |
| `ticktick_get_timezone` | User timezone |
| `ticktick_get_settings` | User settings |

## Usage Examples

### Create a Task with Subtasks
```
"Create a task 'Plan vacation' with subtasks: 'Book flights', 'Reserve hotel', 'Plan activities'"
```

### GTD Workflow
```
"Show me all tasks due today and overdue tasks, then help me prioritize them"
```

### Focus Session
```
"Start a 25-minute focus session on my 'Write documentation' task"
```

### Habit Check-in
```
"Check in my 'Exercise' and 'Reading' habits for today"
```

### Daily Review
```
"Give me a productivity summary and suggest a schedule for today"
```

## Authentication Methods

### Option 1: OAuth2 (v1 API - Official)
Basic task and project management:
```
1. ticktick_configure_oauth with Client ID/Secret
2. Visit authorization URL
3. ticktick_authorize_oauth with callback code
```

### Option 2: Username/Password (v2 API - Extended)
Full features including habits, focus, tags:
```
ticktick_login with your TickTick credentials
```

## Configuration

### Environment Variables
```bash
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
TICKTICK_ACCESS_TOKEN=your_access_token  # Optional
```

### File Locations
- Token storage: `~/.ticktick-mcp/oauth_token.json`
- Session tokens: `~/.ticktick-mcp/session_token.json`
- Cache storage: `~/.ticktick-mcp/cache.json`

## Docker

```bash
# Build
docker build -t ticktick-mcp .

# Run
docker run -e TICKTICK_CLIENT_ID=xxx -e TICKTICK_CLIENT_SECRET=xxx ticktick-mcp

# With docker-compose
docker-compose up
```

## Task Priority Levels

| Priority | Value | Emoji |
|----------|-------|-------|
| None | 0 | ⚪ |
| Low | 1 | 🔵 |
| Medium | 3 | 🟡 |
| High | 5 | 🔴 |

## Troubleshooting

### "Not authenticated" Error
Run `ticktick_auth_status` to check status, then re-authenticate.

### "Token expired" Error
Delete `~/.ticktick-mcp/oauth_token.json` and re-authenticate, or use `ticktick_refresh_token`.

### "Rate limit exceeded" Error
Wait a minute. TickTick has API rate limits.

### v2 Features Not Working
Ensure you've logged in with username/password using `ticktick_login`.

### Cache Out of Date
Run `ticktick_cache_refresh` to sync with the API.

## API Reference

- [TickTick Developer Portal](https://developer.ticktick.com)
- [API Documentation](https://developer.ticktick.com/api#/openapi)

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

## Acknowledgments

- [TickTick](https://ticktick.com) for the API
- [Model Context Protocol](https://github.com/modelcontextprotocol) specification

---

Built with ❤️ for productivity enthusiasts using Claude and TickTick.
