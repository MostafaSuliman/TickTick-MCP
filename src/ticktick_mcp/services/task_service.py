"""
Task Service - Comprehensive task management operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..api.exceptions import NotFoundError
from ..models.tasks import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskPriority,
    TaskStatus,
    TaskFilter,
)
from .base_service import CRUDService

logger = logging.getLogger(__name__)


class TaskService(CRUDService[Task]):
    """
    Service for task management operations.

    Supports both v1 and v2 APIs with automatic version selection.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)
        self._tasks_by_project: Dict[str, List[Task]] = {}

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    async def list(
        self,
        project_id: Optional[str] = None,
        include_completed: bool = False,
        **filters,
    ) -> List[Task]:
        """
        List tasks with optional filtering.

        Args:
            project_id: Filter by specific project (None for all)
            include_completed: Include completed tasks
            **filters: Additional filter parameters

        Returns:
            List of Task objects
        """
        tasks = []

        if project_id:
            # Get tasks for specific project
            tasks = await self._get_project_tasks(project_id)
        else:
            # Get all tasks from all projects
            from .project_service import ProjectService
            project_service = ProjectService(self.client)
            projects = await project_service.list()

            for project in projects:
                try:
                    project_tasks = await self._get_project_tasks(project.id)
                    tasks.extend(project_tasks)
                except Exception as e:
                    logger.warning(f"Failed to get tasks for project {project.id}: {e}")

        # Apply filters
        if not include_completed:
            tasks = [t for t in tasks if t.status != TaskStatus.COMPLETE]

        # Apply additional filters
        task_filter = TaskFilter(**filters) if filters else None
        if task_filter:
            tasks = self._apply_filters(tasks, task_filter)

        return tasks

    async def _get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a specific project."""
        try:
            url = Endpoints.Projects.data_v1(project_id)
            data = await self.client.get(url, version=APIVersion.V1)
            raw_tasks = data.get("tasks", [])
            return [Task(**t) for t in raw_tasks]
        except Exception as e:
            logger.error(f"Error fetching tasks for project {project_id}: {e}")
            return []

    async def get(self, task_id: str, project_id: str) -> Task:
        """
        Get a specific task by ID.

        Args:
            task_id: Task identifier
            project_id: Project containing the task

        Returns:
            Task object

        Raises:
            NotFoundError: If task not found
        """
        url = Endpoints.Tasks.get_v1(project_id, task_id)
        data = await self.client.get(url, version=APIVersion.V1)
        return Task(**data)

    async def create(self, task_data: TaskCreate) -> Task:
        """
        Create a new task.

        Args:
            task_data: Task creation data

        Returns:
            Created Task object
        """
        payload = self._build_task_payload(task_data)

        url = Endpoints.Tasks.create_v1()
        data = await self.client.post(url, version=APIVersion.V1, data=payload)

        return Task(**data)

    async def update(self, task_data: TaskUpdate) -> Task:
        """
        Update an existing task.

        Args:
            task_data: Task update data including task_id and project_id

        Returns:
            Updated Task object
        """
        # First get the existing task
        existing = await self.get(task_data.id, task_data.project_id)

        # Merge updates
        update_payload = existing.model_dump(by_alias=True, exclude_none=True)
        update_data = task_data.model_dump(by_alias=True, exclude_none=True)
        update_payload.update(update_data)

        url = Endpoints.Tasks.update_v1(task_data.id)
        data = await self.client.post(url, version=APIVersion.V1, data=update_payload)

        return Task(**data)

    async def delete(self, task_id: str, project_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task to delete
            project_id: Project containing the task

        Returns:
            True if successful
        """
        # Try v2 batch delete first (more reliable)
        if self.is_v2_available:
            try:
                url = Endpoints.Tasks.batch_v2()
                payload = {
                    "delete": [{"taskId": task_id, "projectId": project_id}]
                }
                await self.client.post(url, version=APIVersion.V2, data=payload)
                return True
            except Exception as e:
                logger.warning(f"V2 delete failed, trying v1: {e}")

        # Fallback to v1
        url = Endpoints.Tasks.delete_v1(project_id, task_id)
        await self.client.delete(url, version=APIVersion.V1)
        return True

    # =========================================================================
    # Extended Operations
    # =========================================================================

    async def complete(self, task_id: str, project_id: str) -> bool:
        """
        Mark a task as complete.

        Args:
            task_id: Task to complete
            project_id: Project containing the task

        Returns:
            True if successful
        """
        url = Endpoints.Tasks.complete_v1(project_id, task_id)
        await self.client.post(url, version=APIVersion.V1, data={})
        return True

    async def uncomplete(self, task_id: str, project_id: str) -> Task:
        """
        Mark a task as incomplete (reopen).

        Args:
            task_id: Task to uncomplete
            project_id: Project containing the task

        Returns:
            Updated Task
        """
        task = await self.get(task_id, project_id)
        update = TaskUpdate(
            id=task_id,
            project_id=project_id,
        )
        # Set status back to incomplete
        payload = task.model_dump(by_alias=True)
        payload["status"] = TaskStatus.INCOMPLETE.value

        url = Endpoints.Tasks.update_v1(task_id)
        data = await self.client.post(url, version=APIVersion.V1, data=payload)
        return Task(**data)

    async def move(
        self,
        task_id: str,
        from_project_id: str,
        to_project_id: str,
    ) -> Task:
        """
        Move a task to a different project.

        Args:
            task_id: Task to move
            from_project_id: Source project
            to_project_id: Destination project

        Returns:
            Moved Task
        """
        if not self.is_v2_available:
            # V1 workaround: delete and recreate
            task = await self.get(task_id, from_project_id)
            await self.delete(task_id, from_project_id)

            create_data = TaskCreate(
                title=task.title,
                content=task.content,
                project_id=to_project_id,
                priority=task.priority,
                tags=task.tags,
                due_date=task.due_date,
                start_date=task.start_date,
            )
            return await self.create(create_data)

        # V2 batch move
        url = Endpoints.Tasks.batch_move_v2()
        payload = [{
            "fromProjectId": from_project_id,
            "taskId": task_id,
            "toProjectId": to_project_id,
        }]
        await self.client.post(url, version=APIVersion.V2, data=payload)
        return await self.get(task_id, to_project_id)

    async def create_subtask(
        self,
        parent_task_id: str,
        project_id: str,
        task_data: TaskCreate,
    ) -> Task:
        """
        Create a subtask under a parent task.

        Args:
            parent_task_id: Parent task ID
            project_id: Project ID
            task_data: Subtask data

        Returns:
            Created subtask
        """
        # First create the task
        task_data.project_id = project_id
        subtask = await self.create(task_data)

        if self.is_v2_available:
            # Set parent relationship via v2 API
            url = Endpoints.Tasks.batch_parent_v2()
            payload = [{
                "parentId": parent_task_id,
                "projectId": project_id,
                "taskId": subtask.id,
            }]
            await self.client.post(url, version=APIVersion.V2, data=payload)

        return await self.get(subtask.id, project_id)

    async def get_completed(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
        """
        Get completed tasks within a date range (v2 only).

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            project_id: Filter by project
            limit: Maximum results

        Returns:
            List of completed tasks
        """
        if not self.is_v2_available:
            logger.warning("Completed tasks endpoint requires v2 API")
            return []

        params = {"limit": min(limit, 100)}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        if project_id:
            url = Endpoints.Tasks.project_completed_v2(project_id)
        else:
            url = Endpoints.Tasks.completed_v2()

        data = await self.client.get(url, version=APIVersion.V2, params=params)
        return [Task(**t) for t in data] if isinstance(data, list) else []

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_create(self, tasks: List[TaskCreate]) -> List[Task]:
        """
        Create multiple tasks in one request.

        Args:
            tasks: List of tasks to create

        Returns:
            List of created tasks
        """
        payloads = [self._build_task_payload(t) for t in tasks]

        url = Endpoints.Tasks.batch_v1()
        data = await self.client.post(
            url,
            version=APIVersion.V1,
            data={"add": payloads}
        )

        return [Task(**t) for t in data.get("add", [])]

    async def batch_update(self, tasks: List[TaskUpdate]) -> List[Task]:
        """
        Update multiple tasks in one request (v2 only).

        Args:
            tasks: List of task updates

        Returns:
            List of updated tasks
        """
        if not self.is_v2_available:
            # Fallback to sequential updates
            results = []
            for task in tasks:
                results.append(await self.update(task))
            return results

        payloads = []
        for task in tasks:
            existing = await self.get(task.id, task.project_id)
            payload = existing.model_dump(by_alias=True, exclude_none=True)
            payload.update(task.model_dump(by_alias=True, exclude_none=True))
            payloads.append(payload)

        url = Endpoints.Tasks.batch_v2()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"update": payloads}
        )

        return [Task(**t) for t in data.get("update", [])]

    async def batch_delete(
        self,
        tasks: List[Dict[str, str]],
    ) -> bool:
        """
        Delete multiple tasks in one request.

        Args:
            tasks: List of {"task_id": ..., "project_id": ...} dicts

        Returns:
            True if successful
        """
        if self.is_v2_available:
            url = Endpoints.Tasks.batch_v2()
            payload = {
                "delete": [
                    {"taskId": t["task_id"], "projectId": t["project_id"]}
                    for t in tasks
                ]
            }
            await self.client.post(url, version=APIVersion.V2, data=payload)
        else:
            # Sequential deletion for v1
            for task in tasks:
                await self.delete(task["task_id"], task["project_id"])

        return True

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_task_payload(self, task_data: TaskCreate) -> Dict[str, Any]:
        """Build API payload from TaskCreate model."""
        payload = {
            "title": task_data.title,
        }

        if task_data.content:
            payload["content"] = task_data.content
        if task_data.project_id:
            payload["projectId"] = task_data.project_id
        if task_data.start_date:
            payload["startDate"] = task_data.start_date
            payload["isAllDay"] = task_data.is_all_day
        if task_data.due_date:
            payload["dueDate"] = task_data.due_date
            payload["isAllDay"] = task_data.is_all_day
        if task_data.priority:
            payload["priority"] = task_data.priority.value
        if task_data.tags:
            payload["tags"] = task_data.tags
        if task_data.time_zone:
            payload["timeZone"] = task_data.time_zone
        if task_data.items:
            payload["items"] = [
                item.model_dump(by_alias=True, exclude_none=True)
                for item in task_data.items
            ]
        if task_data.reminders:
            payload["reminders"] = [
                r.model_dump(exclude_none=True)
                for r in task_data.reminders
            ]
        if task_data.repeat_flag:
            payload["repeatFlag"] = task_data.repeat_flag
        if task_data.pomo_estimated:
            payload["pomoEstimated"] = task_data.pomo_estimated

        return payload

    def _apply_filters(self, tasks: List[Task], filters: TaskFilter) -> List[Task]:
        """Apply filters to task list."""
        result = tasks

        if filters.priority is not None:
            result = [t for t in result if t.priority == filters.priority]

        if filters.tags:
            result = [
                t for t in result
                if t.tags and any(tag in t.tags for tag in filters.tags)
            ]

        if filters.due_before:
            due_before = datetime.fromisoformat(filters.due_before)
            result = [
                t for t in result
                if t.due_date and datetime.fromisoformat(t.due_date.replace("Z", "+00:00")) <= due_before
            ]

        if filters.due_after:
            due_after = datetime.fromisoformat(filters.due_after)
            result = [
                t for t in result
                if t.due_date and datetime.fromisoformat(t.due_date.replace("Z", "+00:00")) >= due_after
            ]

        if filters.search_query:
            query = filters.search_query.lower()
            result = [
                t for t in result
                if query in t.title.lower() or (t.content and query in t.content.lower())
            ]

        return result

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_task(self, task: Task) -> str:
        """Format a single task as markdown."""
        priority_map = {0: "", 1: " Low", 3: " Medium", 5: " High"}
        priority = priority_map.get(task.priority, "")
        status = "" if task.status == TaskStatus.COMPLETE else ""

        lines = [
            f"### {task.title}",
            f"- **ID**: `{task.id}`",
            f"- **Status**: {status} {'Complete' if task.status == TaskStatus.COMPLETE else 'Incomplete'}",
            f"- **Priority**: {priority}",
        ]

        if task.project_id:
            lines.append(f"- **Project ID**: `{task.project_id}`")
        if task.content:
            lines.append(f"- **Description**: {task.content}")
        if task.due_date:
            lines.append(f"- **Due Date**: {task.due_date}")
        if task.start_date:
            lines.append(f"- **Start Date**: {task.start_date}")
        if task.tags:
            tags = ", ".join([f"`{t}`" for t in task.tags])
            lines.append(f"- **Tags**: {tags}")
        if task.items:
            lines.append("- **Checklist**:")
            for item in task.items:
                check = "" if item.status == TaskStatus.COMPLETE else ""
                lines.append(f"  - {check} {item.title}")

        return "\n".join(lines)

    def format_task_list(self, tasks: List[Task], title: str = "Tasks") -> str:
        """Format a list of tasks as markdown."""
        if not tasks:
            return f"##  {title}\n\nNo tasks found."

        lines = [f"##  {title} ({len(tasks)} total)\n"]

        # Group by project
        by_project: Dict[str, List[Task]] = {}
        for task in tasks:
            pid = task.project_id or "inbox"
            if pid not in by_project:
                by_project[pid] = []
            by_project[pid].append(task)

        for project_id, project_tasks in by_project.items():
            lines.append(f"\n### Project: `{project_id}`\n")
            # Sort by priority
            sorted_tasks = sorted(project_tasks, key=lambda t: t.priority, reverse=True)
            for task in sorted_tasks:
                lines.append(self.format_task(task))
                lines.append("")

        return "\n".join(lines)
