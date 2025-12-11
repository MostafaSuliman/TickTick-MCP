"""
Cache MCP tools - Local task cache management for task discovery.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class RegisterTaskInput(BaseModel):
    """Input for registering a task in cache."""
    task_id: str = Field(..., description="Task ID to register")
    project_id: str = Field(..., description="Project ID containing the task")
    title: str = Field(..., description="Task title")
    priority: int = Field(default=0, description="Priority (0=none, 1=low, 3=medium, 5=high)")
    tags: Optional[List[str]] = Field(default=None, description="Task tags")
    due_date: Optional[str] = Field(default=None, description="Due date (ISO format)")


class UnregisterTaskInput(BaseModel):
    """Input for removing a task from cache."""
    task_id: str = Field(..., description="Task ID to remove")


class GetCachedTaskInput(BaseModel):
    """Input for getting a cached task."""
    task_id: str = Field(..., description="Task ID to look up")


class SearchCacheInput(BaseModel):
    """Input for searching cached tasks."""
    query: str = Field(..., description="Search query (searches title)")


class GetByProjectInput(BaseModel):
    """Input for getting cached tasks by project."""
    project_id: str = Field(..., description="Project ID to filter by")


class GetByTagInput(BaseModel):
    """Input for getting cached tasks by tag."""
    tag: str = Field(..., description="Tag to filter by")


class ListCachedInput(BaseModel):
    """Input for listing all cached tasks."""
    pass


class ClearCacheInput(BaseModel):
    """Input for clearing the cache."""
    pass


class ExportCacheInput(BaseModel):
    """Input for exporting cache to CSV."""
    pass


class ImportCacheInput(BaseModel):
    """Input for importing tasks from CSV."""
    csv_data: str = Field(
        ...,
        description="CSV data with columns: task_id, project_id, title, priority, tags, due_date"
    )


class CacheStatsInput(BaseModel):
    """Input for getting cache statistics."""
    pass


class RefreshCacheInput(BaseModel):
    """Input for refreshing cache from API."""
    pass


def register_cache_tools(mcp, cache, task_service):
    """Register cache management tools."""

    @mcp.tool(
        name="ticktick_cache_register",
        annotations={
            "title": "Register Task in Cache",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_register(params: RegisterTaskInput) -> str:
        """
        Register a task ID and project ID mapping in the local cache.

        This is useful for tracking tasks you've created or discovered,
        so you can later operate on them without needing to know the project ID.
        """
        try:
            entry = cache.register(
                task_id=params.task_id,
                project_id=params.project_id,
                title=params.title,
                priority=params.priority,
                tags=params.tags,
                due_date=params.due_date,
            )
            return f"""## Task Registered in Cache

- **Task ID**: `{entry.task_id}`
- **Project ID**: `{entry.project_id}`
- **Title**: {entry.title}
- **Priority**: {entry.priority}
"""
        except Exception as e:
            return f"**Error**: Failed to register task - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_unregister",
        annotations={
            "title": "Remove Task from Cache",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_unregister(params: UnregisterTaskInput) -> str:
        """
        Remove a task from the local cache.

        This doesn't delete the task from TickTick, only from local cache.
        """
        try:
            removed = cache.unregister(params.task_id)
            if removed:
                return f"## Task Removed from Cache\n\nTask `{params.task_id}` has been removed from cache."
            else:
                return f"## Not Found\n\nTask `{params.task_id}` was not in the cache."
        except Exception as e:
            return f"**Error**: Failed to unregister task - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_get",
        annotations={
            "title": "Get Cached Task Info",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_get(params: GetCachedTaskInput) -> str:
        """
        Get cached information for a task, including its project ID.

        Useful for finding the project ID needed to operate on a task.
        """
        try:
            entry = cache.get(params.task_id)
            if entry:
                return cache.format_entries([entry], "Cached Task")
            else:
                return f"## Not Found\n\nTask `{params.task_id}` is not in the cache."
        except Exception as e:
            return f"**Error**: Failed to get cached task - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_search",
        annotations={
            "title": "Search Cached Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_search(params: SearchCacheInput) -> str:
        """
        Search cached tasks by title.

        Faster than API search as it uses local cache.
        """
        try:
            entries = cache.search(params.query)
            return cache.format_entries(entries, f"Search Results for '{params.query}'")
        except Exception as e:
            return f"**Error**: Search failed - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_by_project",
        annotations={
            "title": "Get Cached Tasks by Project",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_by_project(params: GetByProjectInput) -> str:
        """
        Get all cached tasks for a specific project.
        """
        try:
            entries = cache.get_by_project(params.project_id)
            return cache.format_entries(entries, f"Cached Tasks in Project `{params.project_id}`")
        except Exception as e:
            return f"**Error**: Failed to get tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_by_tag",
        annotations={
            "title": "Get Cached Tasks by Tag",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_by_tag(params: GetByTagInput) -> str:
        """
        Get cached tasks with a specific tag.
        """
        try:
            entries = cache.get_by_tag(params.tag)
            return cache.format_entries(entries, f"Cached Tasks with Tag `{params.tag}`")
        except Exception as e:
            return f"**Error**: Failed to get tasks - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_list",
        annotations={
            "title": "List All Cached Tasks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_list(params: ListCachedInput) -> str:
        """
        List all tasks in the local cache.
        """
        try:
            entries = cache.list_all()
            return cache.format_entries(entries, "All Cached Tasks")
        except Exception as e:
            return f"**Error**: Failed to list cache - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_clear",
        annotations={
            "title": "Clear Task Cache",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def cache_clear(params: ClearCacheInput) -> str:
        """
        Clear all entries from the local cache.

        This doesn't affect TickTick tasks, only the local cache.
        """
        try:
            count = cache.clear()
            return f"## Cache Cleared\n\nRemoved {count} entries from cache."
        except Exception as e:
            return f"**Error**: Failed to clear cache - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_export",
        annotations={
            "title": "Export Cache to CSV",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_export(params: ExportCacheInput) -> str:
        """
        Export the task cache to CSV format.

        Useful for backup or migration.
        """
        try:
            csv_data = cache.export_csv()
            return f"""## Cache Export

```csv
{csv_data}
```
"""
        except Exception as e:
            return f"**Error**: Export failed - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_import",
        annotations={
            "title": "Import Tasks to Cache",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def cache_import(params: ImportCacheInput) -> str:
        """
        Import tasks from CSV data into the cache.

        Expected columns: task_id, project_id, title, priority, tags, due_date
        """
        try:
            count = cache.import_csv(params.csv_data)
            return f"## Import Complete\n\nImported {count} tasks into cache."
        except Exception as e:
            return f"**Error**: Import failed - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_stats",
        annotations={
            "title": "Get Cache Statistics",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def cache_stats(params: CacheStatsInput) -> str:
        """
        Get statistics about the local cache.

        Shows task counts by project, priority, and tags.
        """
        try:
            stats = cache.stats()
            return cache.format_stats(stats)
        except Exception as e:
            return f"**Error**: Failed to get stats - {str(e)}"

    @mcp.tool(
        name="ticktick_cache_refresh",
        annotations={
            "title": "Refresh Cache from API",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def cache_refresh(params: RefreshCacheInput) -> str:
        """
        Refresh the local cache by fetching all tasks from the API.

        This will update the cache with current data from TickTick.
        """
        try:
            # Get all tasks
            tasks = await task_service.list(include_completed=False)

            # Update cache
            count = cache.bulk_register(tasks)

            return f"""## Cache Refreshed

- **Tasks cached**: {count}
- **Last refresh**: Now

The cache now contains current data from your TickTick account.
"""
        except Exception as e:
            return f"**Error**: Refresh failed - {str(e)}"
