"""
Task MCP tools - CRUD, completion, and batch operations.
"""

from typing import Optional
from pydantic import BaseModel, Field

from ..models.tasks import TaskPriority, ChecklistItem


class ListTasksInput(BaseModel):
    """Input for listing tasks."""
    project_id: Optional[str] = Field(
        default=None,
        description="Filter by project ID (None for all projects)"
    )
    include_completed: bool = Field(
        default=False,
        description="Include completed tasks"
    )
    priority: Optional[str] = Field(
        default=None,
        description="Filter by priority: none, low, medium, high"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Filter by tags"
    )
    search_query: Optional[str] = Field(
        default=None,
        description="Search in task titles and content"
    )


class GetTaskInput(BaseModel):
    """Input for getting a specific task."""
    task_id: str = Field(..., description="Task ID")
    project_id: str = Field(..., description="Project ID containing the task")


class CreateTaskInput(BaseModel):
    """Input for creating a task."""
    title: str = Field(..., description="Task title", min_length=1, max_length=500)
    content: Optional[str] = Field(default=None, description="Task description/notes")
    project_id: Optional[str] = Field(
        default=None,
        description="Project/list ID (empty for inbox)"
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Due date in ISO format (e.g., 2024-12-31T23:59:00+0000)"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in ISO format"
    )
    priority: Optional[str] = Field(
        default="none",
        description="Priority: none, low, medium, high"
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Tags to add to the task"
    )
    is_all_day: bool = Field(default=True, description="Is all-day task")
    time_zone: Optional[str] = Field(default=None, description="Time zone")
    repeat_flag: Optional[str] = Field(
        default=None,
        description="Recurrence rule (RRULE format, e.g., 'RRULE:FREQ=DAILY;INTERVAL=1')"
    )
    pomo_estimated: Optional[int] = Field(
        default=None,
        description="Estimated pomodoro sessions",
        ge=0
    )


class UpdateTaskInput(BaseModel):
    """Input for updating a task."""
    task_id: str = Field(..., description="Task ID to update")
    project_id: str = Field(..., description="Project ID containing the task")
    title: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = Field(default=None)
    due_date: Optional[str] = Field(default=None)
    start_date: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    is_all_day: Optional[bool] = Field(default=None)
    pomo_estimated: Optional[int] = Field(default=None, ge=0)


class CompleteTaskInput(BaseModel):
    """Input for completing a task."""
    task_id: str = Field(..., description="Task ID to complete")
    project_id: str = Field(..., description="Project ID containing the task")


class UncompleteTaskInput(BaseModel):
    """Input for reopening a completed task."""
    task_id: str = Field(..., description="Task ID to uncomplete")
    project_id: str = Field(..., description="Project ID containing the task")


class DeleteTaskInput(BaseModel):
    """Input for deleting a task."""
    task_id: str = Field(..., description="Task ID to delete")
    project_id: str = Field(..., description="Project ID containing the task")


class MoveTaskInput(BaseModel):
    """Input for moving a task between projects."""
    task_id: str = Field(..., description="Task ID to move")
    from_project_id: str = Field(..., description="Source project ID")
    to_project_id: str = Field(..., description="Destination project ID")


class CreateSubtaskInput(BaseModel):
    """Input for creating a subtask."""
    parent_task_id: str = Field(..., description="Parent task ID")
    project_id: str = Field(..., description="Project ID")
    title: str = Field(..., description="Subtask title")
    content: Optional[str] = Field(default=None)
    due_date: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default="none")


class GetCompletedTasksInput(BaseModel):
    """Input for getting completed tasks (v2 only)."""
    from_date: Optional[str] = Field(
        default=None,
        description="Start date (YYYY-MM-DD)"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM-DD)"
    )
    project_id: Optional[str] = Field(default=None)
    limit: int = Field(default=50, ge=1, le=100)


class BatchCreateTasksInput(BaseModel):
    """Input for batch task creation."""
    tasks: list[CreateTaskInput] = Field(
        ...,
        description="List of tasks to create",
        min_length=1,
        max_length=50
    )


class BatchDeleteTasksInput(BaseModel):
    """Input for batch task deletion."""
    tasks: list[dict] = Field(
        ...,
        description="List of {task_id, project_id} to delete",
        min_length=1,
        max_length=50
    )


def register_task_tools(mcp, task_service):
    """Register task management tools."""

    @mcp.tool(
        name="ticktick_list_tasks",
        annotations={
            "title": "List TickTick Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_tasks(params: ListTasksInput) -> str:
        """
        List tasks with optional filtering.

        Supports filtering by project, priority, tags, and search query.
        """
        filters = {}
        if params.priority:
            filters["priority"] = TaskPriority.from_string(params.priority)
        if params.tags:
            filters["tags"] = params.tags
        if params.search_query:
            filters["search_query"] = params.search_query

        tasks = await task_service.list(
            project_id=params.project_id,
            include_completed=params.include_completed,
            **filters
        )
        return task_service.format_task_list(tasks)

    @mcp.tool(
        name="ticktick_get_task",
        annotations={
            "title": "Get TickTick Task",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_task(params: GetTaskInput) -> str:
        """
        Get a specific task by ID.

        Requires both task ID and project ID.
        """
        try:
            task = await task_service.get(params.task_id, params.project_id)
            return task_service.format_task(task)
        except Exception as e:
            return f"**Error**: Could not find task - {str(e)}"

    @mcp.tool(
        name="ticktick_create_task",
        annotations={
            "title": "Create TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_task(params: CreateTaskInput) -> str:
        """
        Create a new task in TickTick.

        Can set title, description, due date, priority, tags, and more.
        If project_id is not provided, task goes to inbox.
        """
        from ..models.tasks import TaskCreate

        task_data = TaskCreate(
            title=params.title,
            content=params.content,
            project_id=params.project_id,
            due_date=params.due_date,
            start_date=params.start_date,
            priority=TaskPriority.from_string(params.priority or "none"),
            tags=params.tags,
            is_all_day=params.is_all_day,
            time_zone=params.time_zone,
            repeat_flag=params.repeat_flag,
            pomo_estimated=params.pomo_estimated,
        )

        try:
            task = await task_service.create(task_data)
            return f"""## Task Created

{task_service.format_task(task)}
"""
        except Exception as e:
            return f"**Error**: Failed to create task - {str(e)}"

    @mcp.tool(
        name="ticktick_update_task",
        annotations={
            "title": "Update TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_task(params: UpdateTaskInput) -> str:
        """
        Update an existing task.

        Only provided fields will be updated.
        """
        from ..models.tasks import TaskUpdate

        update_data = TaskUpdate(
            id=params.task_id,
            project_id=params.project_id,
            title=params.title,
            content=params.content,
            due_date=params.due_date,
            start_date=params.start_date,
            priority=TaskPriority.from_string(params.priority) if params.priority else None,
            tags=params.tags,
            is_all_day=params.is_all_day,
            pomo_estimated=params.pomo_estimated,
        )

        try:
            task = await task_service.update(update_data)
            return f"""## Task Updated

{task_service.format_task(task)}
"""
        except Exception as e:
            return f"**Error**: Failed to update task - {str(e)}"

    @mcp.tool(
        name="ticktick_complete_task",
        annotations={
            "title": "Complete TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def complete_task(params: CompleteTaskInput) -> str:
        """
        Mark a task as complete.
        """
        try:
            await task_service.complete(params.task_id, params.project_id)
            return f"## Task Completed\n\nTask `{params.task_id}` has been marked as complete."
        except Exception as e:
            return f"**Error**: Failed to complete task - {str(e)}"

    @mcp.tool(
        name="ticktick_uncomplete_task",
        annotations={
            "title": "Uncomplete TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def uncomplete_task(params: UncompleteTaskInput) -> str:
        """
        Reopen a completed task (mark as incomplete).
        """
        try:
            task = await task_service.uncomplete(params.task_id, params.project_id)
            return f"""## Task Reopened

{task_service.format_task(task)}
"""
        except Exception as e:
            return f"**Error**: Failed to uncomplete task - {str(e)}"

    @mcp.tool(
        name="ticktick_delete_task",
        annotations={
            "title": "Delete TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_task(params: DeleteTaskInput) -> str:
        """
        Delete a task permanently.

        Warning: This action cannot be undone.
        """
        try:
            await task_service.delete(params.task_id, params.project_id)
            return f"## Task Deleted\n\nTask `{params.task_id}` has been permanently deleted."
        except Exception as e:
            return f"**Error**: Failed to delete task - {str(e)}"

    @mcp.tool(
        name="ticktick_move_task",
        annotations={
            "title": "Move TickTick Task",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def move_task(params: MoveTaskInput) -> str:
        """
        Move a task to a different project/list.
        """
        try:
            task = await task_service.move(
                params.task_id,
                params.from_project_id,
                params.to_project_id
            )
            return f"""## Task Moved

Task moved to project `{params.to_project_id}`.

{task_service.format_task(task)}
"""
        except Exception as e:
            return f"**Error**: Failed to move task - {str(e)}"

    @mcp.tool(
        name="ticktick_create_subtask",
        annotations={
            "title": "Create Subtask",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_subtask(params: CreateSubtaskInput) -> str:
        """
        Create a subtask under a parent task.

        Note: Requires v2 API for full hierarchy support.
        """
        from ..models.tasks import TaskCreate

        task_data = TaskCreate(
            title=params.title,
            content=params.content,
            project_id=params.project_id,
            due_date=params.due_date,
            priority=TaskPriority.from_string(params.priority or "none"),
        )

        try:
            subtask = await task_service.create_subtask(
                params.parent_task_id,
                params.project_id,
                task_data
            )
            return f"""## Subtask Created

Parent: `{params.parent_task_id}`

{task_service.format_task(subtask)}
"""
        except Exception as e:
            return f"**Error**: Failed to create subtask - {str(e)}"

    @mcp.tool(
        name="ticktick_get_completed_tasks",
        annotations={
            "title": "Get Completed Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_completed_tasks(params: GetCompletedTasksInput) -> str:
        """
        Get completed tasks within a date range.

        Requires v2 API authentication (username/password login).
        """
        try:
            tasks = await task_service.get_completed(
                from_date=params.from_date,
                to_date=params.to_date,
                project_id=params.project_id,
                limit=params.limit
            )
            if not tasks:
                return "## Completed Tasks\n\nNo completed tasks found for the specified criteria.\n\n_Note: This feature requires v2 API authentication._"
            return task_service.format_task_list(tasks, title="Completed Tasks")
        except Exception as e:
            return f"**Error**: Failed to get completed tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_batch_create_tasks",
        annotations={
            "title": "Batch Create Tasks",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def batch_create_tasks(params: BatchCreateTasksInput) -> str:
        """
        Create multiple tasks in a single request.

        More efficient than creating tasks one by one.
        """
        from ..models.tasks import TaskCreate

        task_creates = []
        for t in params.tasks:
            task_creates.append(TaskCreate(
                title=t.title,
                content=t.content,
                project_id=t.project_id,
                due_date=t.due_date,
                start_date=t.start_date,
                priority=TaskPriority.from_string(t.priority or "none"),
                tags=t.tags,
                is_all_day=t.is_all_day,
                time_zone=t.time_zone,
            ))

        try:
            tasks = await task_service.batch_create(task_creates)
            return f"""## Batch Task Creation

Successfully created {len(tasks)} tasks.

{task_service.format_task_list(tasks, title="Created Tasks")}
"""
        except Exception as e:
            return f"**Error**: Batch creation failed - {str(e)}"

    @mcp.tool(
        name="ticktick_batch_delete_tasks",
        annotations={
            "title": "Batch Delete Tasks",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def batch_delete_tasks(params: BatchDeleteTasksInput) -> str:
        """
        Delete multiple tasks in a single request.

        Warning: This action cannot be undone.
        """
        try:
            await task_service.batch_delete(params.tasks)
            return f"## Batch Deletion Complete\n\nSuccessfully deleted {len(params.tasks)} tasks."
        except Exception as e:
            return f"**Error**: Batch deletion failed - {str(e)}"
