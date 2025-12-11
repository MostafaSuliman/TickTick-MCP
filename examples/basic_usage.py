"""
Basic Usage Example

This example shows how to use the TickTick MCP server programmatically.
For use with Claude Desktop, configure the server in claude_desktop_config.json instead.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ticktick_mcp.api.client import TickTickClient
from ticktick_mcp.services import TaskService, ProjectService


async def main():
    # Initialize client
    client = TickTickClient()

    # Configure OAuth (you need to obtain tokens first)
    # client.configure_oauth("your_client_id", "your_client_secret")

    # Initialize services
    task_service = TaskService(client)
    project_service = ProjectService(client)

    # List all projects
    print("=== Projects ===")
    projects = await project_service.list()
    for project in projects:
        print(f"- {project.name} ({project.id})")

    # List all incomplete tasks
    print("\n=== Tasks ===")
    tasks = await task_service.list(include_completed=False)
    for task in tasks:
        priority = {0: " ", 1: "!", 3: "!!", 5: "!!!"}.get(task.priority, "")
        print(f"- [{priority}] {task.title}")

    # Create a new task (example - uncomment to test)
    # from ticktick_mcp.models.tasks import TaskCreate, TaskPriority
    # new_task = TaskCreate(
    #     title="Test task from Python",
    #     content="Created via TickTick MCP",
    #     priority=TaskPriority.MEDIUM,
    # )
    # created = await task_service.create(new_task)
    # print(f"\nCreated task: {created.title} ({created.id})")


if __name__ == "__main__":
    asyncio.run(main())
