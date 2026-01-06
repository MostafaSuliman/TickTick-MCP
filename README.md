<div align="center">

[![TickTick](https://ticktick.com/favicon.ico)](https://ticktick.com)

# TickTick MCP Server 🎯

**[TickTick.com](https://ticktick.com)** | Manage Your Tasks with AI

</div>

A comprehensive MCP (Model Context Protocol) server for managing your TickTick tasks directly from Claude or any MCP-compatible AI assistant.

## Features ✨

- **Task Management**: Create, update, complete, and delete tasks
- **Project Management**: Create and manage projects/lists
- **Smart Scheduling**: Generate daily schedules based on task priorities and due dates
- **OAuth2 Authentication**: Secure authentication with TickTick's official API
- **Rich Formatting**: Beautiful markdown output for easy reading

## Prerequisites

- Python 3.10 or higher
- A TickTick account
- A TickTick Developer App (we'll create this below)

## Installation

### Step 1: Clone/Copy the Server

```bash
# Create directory
mkdir -p ~/ticktick-mcp
cd ~/ticktick-mcp

# Copy the files (ticktick_mcp.py and pyproject.toml)
```

### Step 2: Install Dependencies

```bash
# Using pip
pip install mcp httpx pydantic

# Or using the project
cd ~/ticktick-mcp
pip install -e .
```

### Step 3: Register a TickTick Developer App

1. Go to [TickTick Developer Portal](https://developer.ticktick.com/manage)
2. Log in with your TickTick account
3. Click **"+ App Name"** to create a new app
4. Enter a name (e.g., "Claude MCP Integration")
5. **Important**: Set the OAuth Redirect URL to: `http://127.0.0.1:8080/callback`
6. Click Save
7. Note down your **Client ID** and **Client Secret**

## Configuration

### For Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "python",
      "args": ["/path/to/ticktick-mcp/ticktick_mcp.py"],
      "env": {}
    }
  }
}
```

**Using uv (recommended)**:
```json
{
  "mcpServers": {
    "ticktick": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ticktick-mcp", "python", "ticktick_mcp.py"]
    }
  }
}
```

### For Other MCP Clients

Run the server directly:
```bash
python ticktick_mcp.py
```

## First-Time Setup (OAuth Authentication)

Once the MCP server is connected, use these tools in order:

### 1. Configure Credentials

Tell Claude:
> "Configure TickTick with my credentials: Client ID is `YOUR_CLIENT_ID` and Client Secret is `YOUR_CLIENT_SECRET`"

This will:
- Save your credentials securely
- Generate an authorization URL for you to visit

### 2. Authorize the App

1. Claude will provide an authorization URL
2. Open the URL in your browser
3. Log in to TickTick and click "Allow"
4. You'll be redirected to a URL like:
   `http://127.0.0.1:8080/callback?code=ABCD1234&state=mcp_auth`
5. Copy the **code** parameter (`ABCD1234` in this example)

### 3. Complete Authorization

Tell Claude:
> "Complete TickTick authorization with code: ABCD1234"

You're now authenticated! The token is cached for ~6 months.

## Available Tools

### Authentication
| Tool | Description |
|------|-------------|
| `ticktick_configure` | Configure API credentials |
| `ticktick_authorize` | Complete OAuth flow |
| `ticktick_check_auth` | Check authentication status |

### Tasks
| Tool | Description |
|------|-------------|
| `ticktick_list_tasks` | List all incomplete tasks |
| `ticktick_get_task` | Get details of a specific task |
| `ticktick_create_task` | Create a new task |
| `ticktick_update_task` | Update an existing task |
| `ticktick_complete_task` | Mark a task as complete |
| `ticktick_delete_task` | Delete a task |

### Projects
| Tool | Description |
|------|-------------|
| `ticktick_list_projects` | List all projects/lists |
| `ticktick_create_project` | Create a new project |
| `ticktick_delete_project` | Delete a project |

### Scheduling
| Tool | Description |
|------|-------------|
| `ticktick_schedule_time` | Generate a daily schedule |
| `ticktick_get_today` | Quick view of today's tasks |

## Usage Examples

### List Your Tasks
> "Show me all my TickTick tasks"

### Create a Task
> "Create a TickTick task: Review Q4 report, due tomorrow, high priority"

### Schedule Your Day
> "Help me plan my day based on my TickTick tasks"

### Create a Project
> "Create a new TickTick project called 'Side Business Ideas'"

### Complete a Task
> "Mark task ID abc123 in project xyz as complete"

## Task Priority Levels

| Priority | Value | Emoji |
|----------|-------|-------|
| None | 0 | ⚪ |
| Low | 1 | 🟢 |
| Medium | 3 | 🟡 |
| High | 5 | 🔴 |

## File Locations

The server stores configuration and tokens in your home directory:

- **Configuration**: `~/.ticktick-mcp-config.json`
- **OAuth Token**: `~/.ticktick-mcp-token.json`

To reset authentication, delete these files.

## Troubleshooting

### "Not authenticated" Error
Run `ticktick_check_auth` to verify your authentication status, then re-run the OAuth flow if needed.

### "Token expired" Error
Delete `~/.ticktick-mcp-token.json` and re-authenticate.

### "Rate limit exceeded" Error
Wait a minute before making more requests. TickTick has API rate limits.

### "Resource not found" Error
Double-check the task ID and project ID. Use `ticktick_list_tasks` to see valid IDs.

## API Reference

This server uses TickTick's official Open API:
- [TickTick Developer Portal](https://developer.ticktick.com)
- [API Documentation](https://developer.ticktick.com/api#/openapi)

## Contributing

Feel free to extend this server! Some ideas:
- Add support for habits
- Add Pomodoro timer integration
- Add calendar view
- Add recurring task support
- Add tag management tools

## License

MIT License - feel free to use and modify!

---

Built with ❤️ for productivity enthusiasts using Claude and TickTick.
