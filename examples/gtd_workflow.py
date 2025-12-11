"""
GTD (Getting Things Done) Workflow Example

This example demonstrates how to implement a GTD-style workflow
using the TickTick MCP server.

Workflow:
1. Capture - Quick add tasks to inbox
2. Clarify - Process inbox items
3. Organize - Move tasks to appropriate projects
4. Review - Check today's tasks and overdue items
5. Engage - Work on tasks
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ticktick_mcp.api.client import TickTickClient
from ticktick_mcp.services import TaskService, ProjectService, SmartService
from ticktick_mcp.models.tasks import TaskCreate, TaskPriority


async def daily_review(client: TickTickClient):
    """Perform a daily review of tasks."""
    smart_service = SmartService(client)

    print("\n" + "=" * 60)
    print("DAILY REVIEW")
    print("=" * 60)

    # 1. Check overdue tasks
    print("\n--- OVERDUE TASKS ---")
    overdue = await smart_service.get_overdue_tasks()
    if overdue:
        print(f"You have {len(overdue)} overdue tasks:")
        for task in overdue[:5]:  # Show first 5
            print(f"  🔴 {task.title} (due: {task.due_date[:10] if task.due_date else 'N/A'})")
    else:
        print("  ✅ No overdue tasks!")

    # 2. Today's tasks
    print("\n--- TODAY'S TASKS ---")
    today = await smart_service.get_today_tasks()
    if today:
        print(f"You have {len(today)} tasks for today:")
        for task in today:
            priority = {0: "⚪", 1: "🔵", 3: "🟡", 5: "🔴"}.get(task.priority, "⚪")
            print(f"  {priority} {task.title}")
    else:
        print("  📭 No tasks scheduled for today")

    # 3. Tomorrow preview
    print("\n--- TOMORROW'S PREVIEW ---")
    tomorrow = await smart_service.get_tomorrow_tasks()
    print(f"Tomorrow: {len(tomorrow)} tasks scheduled")

    # 4. Productivity summary
    print("\n--- PRODUCTIVITY SUMMARY ---")
    summary = await smart_service.get_productivity_summary()
    print(f"  High priority tasks: {summary['high_priority_total']}")
    print(f"  Unscheduled tasks: {summary['unscheduled']['count']}")

    if summary['recommendations']:
        print("\n--- RECOMMENDATIONS ---")
        for rec in summary['recommendations']:
            print(f"  {rec}")


async def quick_capture(client: TickTickClient, items: list[str]):
    """Quickly capture items to inbox."""
    task_service = TaskService(client)

    print("\n--- QUICK CAPTURE ---")

    for item in items:
        task_data = TaskCreate(
            title=item,
            project_id=None,  # Goes to inbox
            priority=TaskPriority.NONE,
        )

        try:
            task = await task_service.create(task_data)
            print(f"  ✓ Captured: {task.title}")
        except Exception as e:
            print(f"  ✗ Failed to capture '{item}': {e}")


async def weekly_planning(client: TickTickClient):
    """Weekly planning session."""
    smart_service = SmartService(client)
    project_service = ProjectService(client)

    print("\n" + "=" * 60)
    print("WEEKLY PLANNING")
    print("=" * 60)

    # Get next 7 days
    print("\n--- NEXT 7 DAYS ---")
    week = await smart_service.get_next_7_days_tasks()

    total = 0
    for date_str, tasks in week.items():
        day_name = datetime.fromisoformat(date_str).strftime("%A")
        count = len(tasks)
        total += count
        status = "✓" if count < 5 else "⚠️" if count < 10 else "🔴"
        print(f"  {status} {day_name} ({date_str}): {count} tasks")

    print(f"\n  Total for week: {total} tasks")

    # Check unscheduled high priority
    print("\n--- NEEDS SCHEDULING ---")
    no_date = await smart_service.get_no_date_tasks()
    high_priority_unscheduled = [t for t in no_date if t.priority >= 5]

    if high_priority_unscheduled:
        print(f"  ⚠️ {len(high_priority_unscheduled)} high-priority tasks need dates:")
        for task in high_priority_unscheduled[:5]:
            print(f"    - {task.title}")
    else:
        print("  ✅ All high-priority tasks are scheduled")


async def main():
    client = TickTickClient()

    # Example: Daily review
    await daily_review(client)

    # Example: Quick capture (uncomment to test)
    # await quick_capture(client, [
    #     "Call dentist",
    #     "Review project proposal",
    #     "Buy groceries",
    # ])

    # Example: Weekly planning (uncomment to test)
    # await weekly_planning(client)


if __name__ == "__main__":
    asyncio.run(main())
