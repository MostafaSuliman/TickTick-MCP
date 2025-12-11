"""
Task Cache - Local cache system for task discovery.

Solves TickTick API limitation where you can't list all tasks without knowing project IDs.
Maintains a local cache of task IDs, titles, and project mappings.
"""

import json
import logging
import csv
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry for a task."""

    def __init__(
        self,
        task_id: str,
        project_id: str,
        title: str,
        priority: int = 0,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.task_id = task_id
        self.project_id = project_id
        self.title = title
        self.priority = priority
        self.tags = tags or []
        self.due_date = due_date
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "title": self.title,
            "priority": self.priority,
            "tags": self.tags,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_task(cls, task: Any) -> "CacheEntry":
        """Create from Task object."""
        return cls(
            task_id=task.id,
            project_id=task.project_id or "",
            title=task.title,
            priority=task.priority,
            tags=task.tags or [],
            due_date=task.due_date,
        )


class TaskCache:
    """
    Local cache for TickTick tasks.

    Provides:
    - Task ID to project ID mapping (for API calls)
    - Quick task lookup by title
    - Tag-based filtering
    - CSV import/export
    - Automatic cache persistence
    """

    DEFAULT_PATH = Path.home() / ".ticktick-mcp" / "cache.json"

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize task cache.

        Args:
            cache_path: Path to cache file (defaults to ~/.ticktick-mcp/cache.json)
        """
        self.cache_path = cache_path or self.DEFAULT_PATH
        self._entries: Dict[str, CacheEntry] = {}
        self._last_refresh: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r") as f:
                    data = json.load(f)
                    self._entries = {
                        k: CacheEntry.from_dict(v)
                        for k, v in data.get("entries", {}).items()
                    }
                    self._last_refresh = data.get("last_refresh")
                logger.info(f"Loaded {len(self._entries)} cached tasks")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self._entries = {}

    def _save(self) -> None:
        """Save cache to disk."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": {k: v.to_dict() for k, v in self._entries.items()},
                "last_refresh": self._last_refresh,
                "version": "1.0",
            }
            with open(self.cache_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self._entries)} tasks to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    # =========================================================================
    # Core Operations
    # =========================================================================

    def register(
        self,
        task_id: str,
        project_id: str,
        title: str,
        priority: int = 0,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
    ) -> CacheEntry:
        """
        Register a task in the cache.

        Args:
            task_id: Task ID
            project_id: Project ID containing the task
            title: Task title
            priority: Task priority (0-5)
            tags: Task tags
            due_date: Due date

        Returns:
            Created/updated cache entry
        """
        entry = CacheEntry(
            task_id=task_id,
            project_id=project_id,
            title=title,
            priority=priority,
            tags=tags,
            due_date=due_date,
        )

        if task_id in self._entries:
            entry.created_at = self._entries[task_id].created_at
            entry.updated_at = datetime.now(timezone.utc).isoformat()

        self._entries[task_id] = entry
        self._save()
        return entry

    def register_task(self, task: Any) -> CacheEntry:
        """
        Register a Task object in the cache.

        Args:
            task: Task object with id, project_id, title, etc.

        Returns:
            Created cache entry
        """
        return self.register(
            task_id=task.id,
            project_id=task.project_id or "",
            title=task.title,
            priority=task.priority,
            tags=task.tags,
            due_date=task.due_date,
        )

    def unregister(self, task_id: str) -> bool:
        """
        Remove a task from the cache.

        Args:
            task_id: Task ID to remove

        Returns:
            True if removed, False if not found
        """
        if task_id in self._entries:
            del self._entries[task_id]
            self._save()
            return True
        return False

    def get(self, task_id: str) -> Optional[CacheEntry]:
        """
        Get cache entry by task ID.

        Args:
            task_id: Task ID

        Returns:
            Cache entry or None
        """
        return self._entries.get(task_id)

    def get_project_id(self, task_id: str) -> Optional[str]:
        """
        Get project ID for a task (primary use case).

        Args:
            task_id: Task ID

        Returns:
            Project ID or None if not cached
        """
        entry = self._entries.get(task_id)
        return entry.project_id if entry else None

    def search(self, query: str) -> List[CacheEntry]:
        """
        Search cached tasks by title.

        Args:
            query: Search query

        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        return [
            entry for entry in self._entries.values()
            if query_lower in entry.title.lower()
        ]

    def get_by_project(self, project_id: str) -> List[CacheEntry]:
        """
        Get all cached tasks for a project.

        Args:
            project_id: Project ID

        Returns:
            List of cached entries for the project
        """
        return [
            entry for entry in self._entries.values()
            if entry.project_id == project_id
        ]

    def get_by_tag(self, tag: str) -> List[CacheEntry]:
        """
        Get cached tasks with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of matching entries
        """
        tag_lower = tag.lower()
        return [
            entry for entry in self._entries.values()
            if any(t.lower() == tag_lower for t in entry.tags)
        ]

    def list_all(self) -> List[CacheEntry]:
        """
        List all cached entries.

        Returns:
            List of all cache entries
        """
        return list(self._entries.values())

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def bulk_register(self, tasks: List[Any]) -> int:
        """
        Register multiple tasks at once.

        Args:
            tasks: List of Task objects

        Returns:
            Number of tasks registered
        """
        for task in tasks:
            entry = CacheEntry.from_task(task)
            self._entries[task.id] = entry

        self._last_refresh = datetime.now(timezone.utc).isoformat()
        self._save()
        return len(tasks)

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._entries)
        self._entries.clear()
        self._save()
        return count

    # =========================================================================
    # Import/Export
    # =========================================================================

    def export_csv(self) -> str:
        """
        Export cache to CSV format.

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["task_id", "project_id", "title", "priority", "tags", "due_date"])

        # Data
        for entry in self._entries.values():
            writer.writerow([
                entry.task_id,
                entry.project_id,
                entry.title,
                entry.priority,
                ";".join(entry.tags),
                entry.due_date or "",
            ])

        return output.getvalue()

    def import_csv(self, csv_data: str) -> int:
        """
        Import tasks from CSV format.

        Expected columns: task_id, project_id, title, priority, tags, due_date

        Args:
            csv_data: CSV string

        Returns:
            Number of entries imported
        """
        reader = csv.DictReader(io.StringIO(csv_data))
        count = 0

        for row in reader:
            tags = row.get("tags", "").split(";") if row.get("tags") else []
            tags = [t.strip() for t in tags if t.strip()]

            self.register(
                task_id=row["task_id"],
                project_id=row["project_id"],
                title=row["title"],
                priority=int(row.get("priority", 0)),
                tags=tags,
                due_date=row.get("due_date") or None,
            )
            count += 1

        return count

    # =========================================================================
    # Statistics
    # =========================================================================

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        by_project: Dict[str, int] = {}
        by_priority: Dict[int, int] = {0: 0, 1: 0, 3: 0, 5: 0}
        tags_used: Dict[str, int] = {}

        for entry in self._entries.values():
            # Count by project
            pid = entry.project_id or "inbox"
            by_project[pid] = by_project.get(pid, 0) + 1

            # Count by priority
            by_priority[entry.priority] = by_priority.get(entry.priority, 0) + 1

            # Count tags
            for tag in entry.tags:
                tags_used[tag] = tags_used.get(tag, 0) + 1

        return {
            "total_entries": len(self._entries),
            "last_refresh": self._last_refresh,
            "cache_path": str(self.cache_path),
            "by_project": by_project,
            "by_priority": by_priority,
            "top_tags": dict(sorted(tags_used.items(), key=lambda x: -x[1])[:10]),
        }

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_entries(self, entries: List[CacheEntry], title: str = "Cached Tasks") -> str:
        """Format entries as markdown."""
        if not entries:
            return f"## {title}\n\nNo entries found."

        lines = [f"## {title} ({len(entries)} entries)\n"]

        for entry in entries:
            priority_emoji = {0: "⚪", 1: "🔵", 3: "🟡", 5: "🔴"}.get(entry.priority, "⚪")
            lines.append(f"- {priority_emoji} **{entry.title}**")
            lines.append(f"  - Task ID: `{entry.task_id}`")
            lines.append(f"  - Project ID: `{entry.project_id}`")
            if entry.due_date:
                lines.append(f"  - Due: {entry.due_date[:10]}")
            if entry.tags:
                lines.append(f"  - Tags: {', '.join(entry.tags)}")

        return "\n".join(lines)

    def format_stats(self, stats: Dict[str, Any]) -> str:
        """Format statistics as markdown."""
        lines = [
            "## 📊 Cache Statistics\n",
            f"- **Total cached tasks**: {stats['total_entries']}",
            f"- **Last refresh**: {stats['last_refresh'] or 'Never'}",
            f"- **Cache file**: `{stats['cache_path']}`",
            "",
            "### By Project",
        ]

        for pid, count in stats["by_project"].items():
            lines.append(f"- `{pid}`: {count} tasks")

        lines.extend([
            "",
            "### By Priority",
            f"- 🔴 High (5): {stats['by_priority'].get(5, 0)}",
            f"- 🟡 Medium (3): {stats['by_priority'].get(3, 0)}",
            f"- 🔵 Low (1): {stats['by_priority'].get(1, 0)}",
            f"- ⚪ None (0): {stats['by_priority'].get(0, 0)}",
        ])

        if stats["top_tags"]:
            lines.extend(["", "### Top Tags"])
            for tag, count in stats["top_tags"].items():
                lines.append(f"- `{tag}`: {count} tasks")

        return "\n".join(lines)
