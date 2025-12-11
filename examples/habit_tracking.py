"""
Habit Tracking Example

This example shows how to use the habit tracking features
of the TickTick MCP server.

Note: Habit features require v2 API authentication (username/password).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ticktick_mcp.api.client import TickTickClient
from ticktick_mcp.services import HabitService


async def main():
    client = TickTickClient()

    # Note: You need v2 authentication for habits
    # This is just a demonstration of the API structure

    habit_service = HabitService(client)

    print("=== Habit Tracking Demo ===")
    print("\nNote: Habits require v2 API authentication.")
    print("Use ticktick_login to authenticate first.\n")

    # Example: List habits (would work after v2 auth)
    try:
        habits = await habit_service.list()
        print(f"Found {len(habits)} habits")

        for habit in habits:
            print(f"\n📊 {habit.name}")
            print(f"   Goal: {habit.goal} times")
            print(f"   Frequency: {habit.frequency}")
            if hasattr(habit, 'current_streak'):
                print(f"   Current streak: {habit.current_streak} days")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use habits, authenticate with v2 API using ticktick_login.")

    # Example workflow with Claude:
    print("\n" + "=" * 50)
    print("Example Claude Prompts for Habit Tracking:")
    print("=" * 50)
    print("""
    1. "Show me all my habits"
       → ticktick_list_habits

    2. "Create a habit to drink 8 glasses of water daily"
       → ticktick_create_habit with name="Drink water", goal=8

    3. "Check in my exercise habit for today"
       → ticktick_checkin_habit with habit name

    4. "What's my habit progress for this week?"
       → ticktick_get_today_habits or ticktick_get_habit_stats
    """)


if __name__ == "__main__":
    asyncio.run(main())
