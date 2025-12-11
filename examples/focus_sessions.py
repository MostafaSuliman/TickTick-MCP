"""
Focus/Pomodoro Sessions Example

This example demonstrates the focus timer and Pomodoro features
of the TickTick MCP server.

Note: Focus features require v2 API authentication (username/password).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ticktick_mcp.api.client import TickTickClient
from ticktick_mcp.services import FocusService, TaskService


async def main():
    client = TickTickClient()

    focus_service = FocusService(client)
    task_service = TaskService(client)

    print("=== Focus Timer Demo ===")
    print("\nNote: Focus features require v2 API authentication.")
    print("Use ticktick_login to authenticate first.\n")

    # Example: Get today's focus statistics
    try:
        stats = await focus_service.get_today_stats()
        print("Today's Focus Statistics:")
        print(f"  Total focus time: {stats.get('total_minutes', 0)} minutes")
        print(f"  Sessions completed: {stats.get('session_count', 0)}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use focus features, authenticate with v2 API.")

    # Example workflow with Claude:
    print("\n" + "=" * 50)
    print("Example Claude Prompts for Focus Sessions:")
    print("=" * 50)
    print("""
    1. "Start a 25-minute Pomodoro session"
       → ticktick_start_pomodoro

    2. "Start a focus session on my 'Write documentation' task"
       → ticktick_start_pomodoro with task_id

    3. "Stop my current focus session"
       → ticktick_stop_focus

    4. "How much have I focused today?"
       → ticktick_get_today_focus

    5. "Show my focus history for this week"
       → ticktick_get_focus_records with date range

    6. "What are my Pomodoro settings?"
       → ticktick_get_focus_settings
    """)

    # Pomodoro technique explanation
    print("\n" + "=" * 50)
    print("Pomodoro Technique Tips:")
    print("=" * 50)
    print("""
    The Pomodoro Technique uses 25-minute focused work sessions
    followed by short breaks:

    1. Choose a task
    2. Set timer for 25 minutes (one "pomodoro")
    3. Work on the task until timer rings
    4. Take a 5-minute break
    5. After 4 pomodoros, take a longer 15-30 minute break

    With TickTick MCP:
    - Start a pomodoro: "Start a 25-minute focus session"
    - Link to task: "Focus on [task name]"
    - Track progress: "Show my focus stats for today"
    """)


if __name__ == "__main__":
    asyncio.run(main())
