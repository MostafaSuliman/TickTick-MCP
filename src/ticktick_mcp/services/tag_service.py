"""
Tag Service - Tag management operations (v2 API only).
"""

import logging
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..api.exceptions import ConfigurationError
from ..models.tags import (
    Tag,
    TagCreate,
    TagUpdate,
    TagRename,
    TagMerge,
    TagFilter,
)
from .base_service import CRUDService

logger = logging.getLogger(__name__)


class TagService(CRUDService[Tag]):
    """
    Service for tag management operations.

    Note: Tags are only available through the v2 API.
    The official v1 API does not support tag operations.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)

    def _require_v2(self) -> None:
        """Raise error if v2 is not available."""
        if not self.is_v2_available:
            raise ConfigurationError(
                "Tag operations require v2 API authentication. "
                "Use login_v2(username, password) to authenticate."
            )

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    async def list(self, filter_params: Optional[TagFilter] = None) -> List[Tag]:
        """
        List all tags.

        Args:
            filter_params: Optional filter parameters

        Returns:
            List of Tag objects
        """
        self._require_v2()

        # Tags come from sync data
        sync_data = await self.client.sync()
        tags_data = sync_data.get("tags", [])
        tags = [Tag(**t) for t in tags_data]

        # Apply filters
        if filter_params:
            if filter_params.search:
                query = filter_params.search.lower()
                tags = [t for t in tags if query in t.name.lower()]
            if filter_params.parent:
                tags = [t for t in tags if t.parent == filter_params.parent]

        return tags

    async def get(self, tag_name: str) -> Optional[Tag]:
        """
        Get a specific tag by name.

        Args:
            tag_name: Tag name (identifier)

        Returns:
            Tag object or None
        """
        self._require_v2()

        tags = await self.list()
        for tag in tags:
            if tag.name == tag_name:
                return tag
        return None

    async def create(self, tag_data: TagCreate) -> Tag:
        """
        Create a new tag.

        Args:
            tag_data: Tag creation data

        Returns:
            Created Tag object
        """
        self._require_v2()

        payload = {
            "name": tag_data.name,
        }

        if tag_data.label:
            payload["label"] = tag_data.label
        if tag_data.color:
            payload["color"] = tag_data.color
        if tag_data.parent:
            payload["parent"] = tag_data.parent

        url = Endpoints.Tags.batch()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"add": [payload]}
        )

        # Return the created tag
        created = data.get("add", [])
        if created:
            return Tag(**created[0])

        # Fetch and return
        return await self.get(tag_data.name)

    async def update(self, tag_data: TagUpdate) -> Tag:
        """
        Update an existing tag.

        Args:
            tag_data: Tag update data

        Returns:
            Updated Tag object
        """
        self._require_v2()

        # Get existing tag
        existing = await self.get(tag_data.name)
        if not existing:
            raise Exception(f"Tag '{tag_data.name}' not found")

        payload = {"name": tag_data.name}
        if tag_data.label:
            payload["label"] = tag_data.label
        if tag_data.color:
            payload["color"] = tag_data.color
        if tag_data.sort_order is not None:
            payload["sortOrder"] = tag_data.sort_order
        if tag_data.parent is not None:
            payload["parent"] = tag_data.parent

        url = Endpoints.Tags.batch()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"update": [payload]}
        )

        updated = data.get("update", [])
        if updated:
            return Tag(**updated[0])
        return await self.get(tag_data.name)

    async def delete(self, tag_name: str) -> bool:
        """
        Delete a tag.

        Note: This removes the tag but does not delete tasks with this tag.

        Args:
            tag_name: Tag to delete

        Returns:
            True if successful
        """
        self._require_v2()

        url = Endpoints.Tags.delete()
        await self.client.delete(
            url,
            version=APIVersion.V2,
            params={"name": tag_name}
        )
        return True

    # =========================================================================
    # Extended Operations
    # =========================================================================

    async def rename(self, current_name: str, new_name: str) -> Tag:
        """
        Rename a tag.

        This updates all tasks with this tag to use the new name.

        Args:
            current_name: Current tag name
            new_name: New tag name

        Returns:
            Renamed Tag object
        """
        self._require_v2()

        url = Endpoints.Tags.rename()
        await self.client.put(
            url,
            version=APIVersion.V2,
            data={"name": current_name, "newName": new_name}
        )

        return await self.get(new_name)

    async def merge(self, source_tags: List[str], target_tag: str) -> Tag:
        """
        Merge multiple tags into one.

        All tasks from source tags will be assigned to target tag.
        Source tags will be deleted.

        Args:
            source_tags: Tags to merge (will be deleted)
            target_tag: Tag to merge into

        Returns:
            Target Tag object
        """
        self._require_v2()

        # Ensure target exists
        target = await self.get(target_tag)
        if not target:
            # Create target tag
            target = await self.create(TagCreate(name=target_tag))

        url = Endpoints.Tags.merge()
        await self.client.put(
            url,
            version=APIVersion.V2,
            data={
                "sourceTags": source_tags,
                "targetTag": target_tag,
            }
        )

        return await self.get(target_tag)

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_create(self, tags: List[TagCreate]) -> List[Tag]:
        """
        Create multiple tags.

        Args:
            tags: List of tags to create

        Returns:
            List of created tags
        """
        self._require_v2()

        payloads = []
        for tag in tags:
            payload = {"name": tag.name}
            if tag.label:
                payload["label"] = tag.label
            if tag.color:
                payload["color"] = tag.color
            if tag.parent:
                payload["parent"] = tag.parent
            payloads.append(payload)

        url = Endpoints.Tags.batch()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"add": payloads}
        )

        return [Tag(**t) for t in data.get("add", [])]

    async def batch_update(self, tags: List[TagUpdate]) -> List[Tag]:
        """
        Update multiple tags.

        Args:
            tags: List of tag updates

        Returns:
            List of updated tags
        """
        self._require_v2()

        payloads = []
        for tag in tags:
            payload = {"name": tag.name}
            if tag.label:
                payload["label"] = tag.label
            if tag.color:
                payload["color"] = tag.color
            if tag.sort_order is not None:
                payload["sortOrder"] = tag.sort_order
            payloads.append(payload)

        url = Endpoints.Tags.batch()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"update": payloads}
        )

        return [Tag(**t) for t in data.get("update", [])]

    async def batch_delete(self, tag_names: List[str]) -> bool:
        """
        Delete multiple tags.

        Args:
            tag_names: List of tag names to delete

        Returns:
            True if successful
        """
        self._require_v2()

        # Sequential deletion (API limitation)
        for name in tag_names:
            await self.delete(name)
        return True

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_tasks_by_tag(self, tag_name: str) -> List[Any]:
        """
        Get all tasks with a specific tag.

        Args:
            tag_name: Tag to filter by

        Returns:
            List of tasks with this tag
        """
        self._require_v2()

        from .task_service import TaskService
        task_service = TaskService(self.client)

        all_tasks = await task_service.list(include_completed=False)
        return [t for t in all_tasks if t.tags and tag_name in t.tags]

    async def get_nested_tags(self, parent_name: Optional[str] = None) -> List[Tag]:
        """
        Get tags organized by parent relationship.

        Args:
            parent_name: Filter by parent (None for root tags)

        Returns:
            List of tags with matching parent
        """
        tags = await self.list()
        return [t for t in tags if t.parent == parent_name]

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_tag(self, tag: Tag) -> str:
        """Format a single tag as markdown."""
        lines = [f"- **{tag.name}**"]

        if tag.label and tag.label != tag.name:
            lines[0] += f" ({tag.label})"
        if tag.color:
            lines.append(f"  - Color: {tag.color}")
        if tag.parent:
            lines.append(f"  - Parent: {tag.parent}")

        return "\n".join(lines)

    def format_tag_list(self, tags: List[Tag], title: str = "Tags") -> str:
        """Format tag list as markdown."""
        if not tags:
            return f"##  {title}\n\nNo tags found."

        lines = [f"##  {title} ({len(tags)} total)\n"]

        # Organize by parent
        root_tags = [t for t in tags if not t.parent]
        nested = {t.name: [] for t in root_tags}

        for tag in tags:
            if tag.parent and tag.parent in nested:
                nested[tag.parent].append(tag)

        for tag in root_tags:
            lines.append(self.format_tag(tag))
            for child in nested.get(tag.name, []):
                lines.append("  " + self.format_tag(child))

        return "\n".join(lines)
