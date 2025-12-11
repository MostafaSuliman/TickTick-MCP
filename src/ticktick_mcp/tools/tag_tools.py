"""
Tag MCP tools - Tag management (v2 API only).
"""

from typing import Optional
from pydantic import BaseModel, Field


class ListTagsInput(BaseModel):
    """Input for listing tags."""
    pass


class CreateTagInput(BaseModel):
    """Input for creating a tag."""
    name: str = Field(..., description="Tag name", min_length=1, max_length=50)
    color: Optional[str] = Field(
        default=None,
        description="Tag color (hex code, e.g., '#FF5733')"
    )
    parent_name: Optional[str] = Field(
        default=None,
        description="Parent tag name for nested tags"
    )


class UpdateTagInput(BaseModel):
    """Input for updating a tag."""
    name: str = Field(..., description="Current tag name")
    new_name: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None)


class RenameTagInput(BaseModel):
    """Input for renaming a tag."""
    old_name: str = Field(..., description="Current tag name")
    new_name: str = Field(..., description="New tag name", max_length=50)


class MergeTagsInput(BaseModel):
    """Input for merging tags."""
    source_tag: str = Field(..., description="Tag to merge from (will be deleted)")
    target_tag: str = Field(..., description="Tag to merge into (will remain)")


class DeleteTagInput(BaseModel):
    """Input for deleting a tag."""
    name: str = Field(..., description="Tag name to delete")


class GetTagTasksInput(BaseModel):
    """Input for getting tasks with a specific tag."""
    tag_name: str = Field(..., description="Tag name")
    include_completed: bool = Field(default=False)


def register_tag_tools(mcp, tag_service):
    """Register tag management tools (v2 API only)."""

    @mcp.tool(
        name="ticktick_list_tags",
        annotations={
            "title": "List TickTick Tags",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_tags(params: ListTagsInput) -> str:
        """
        List all tags in your TickTick account.

        Requires v2 API authentication (username/password login).
        Tags can be nested (have parent-child relationships).
        """
        try:
            tags = await tag_service.list()
            return tag_service.format_tag_list(tags)
        except Exception as e:
            return f"**Error**: Failed to list tags - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_create_tag",
        annotations={
            "title": "Create TickTick Tag",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_tag(params: CreateTagInput) -> str:
        """
        Create a new tag.

        Tags can be nested by specifying a parent tag name.
        Requires v2 API authentication.
        """
        from ..models.tags import TagCreate

        tag_data = TagCreate(
            name=params.name,
            color=params.color,
            parent_name=params.parent_name,
        )

        try:
            tag = await tag_service.create(tag_data)
            return f"""## Tag Created

- **Name**: {tag.name}
- **Color**: {tag.color or 'default'}
- **Parent**: {tag.parent or 'none'}
"""
        except Exception as e:
            return f"**Error**: Failed to create tag - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_update_tag",
        annotations={
            "title": "Update TickTick Tag",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_tag(params: UpdateTagInput) -> str:
        """
        Update a tag's properties (color, etc.).

        Requires v2 API authentication.
        """
        from ..models.tags import TagUpdate

        update_data = TagUpdate(
            name=params.name,
            new_name=params.new_name,
            color=params.color,
        )

        try:
            tag = await tag_service.update(update_data)
            return f"""## Tag Updated

- **Name**: {tag.name}
- **Color**: {tag.color or 'default'}
"""
        except Exception as e:
            return f"**Error**: Failed to update tag - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_rename_tag",
        annotations={
            "title": "Rename TickTick Tag",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def rename_tag(params: RenameTagInput) -> str:
        """
        Rename a tag.

        All tasks with the old tag will be updated to use the new name.
        Requires v2 API authentication.
        """
        try:
            await tag_service.rename(params.old_name, params.new_name)
            return f"""## Tag Renamed

- **Old Name**: {params.old_name}
- **New Name**: {params.new_name}

All tasks have been updated.
"""
        except Exception as e:
            return f"**Error**: Failed to rename tag - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_merge_tags",
        annotations={
            "title": "Merge TickTick Tags",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def merge_tags(params: MergeTagsInput) -> str:
        """
        Merge one tag into another.

        The source tag will be deleted, and all tasks will be moved to the target tag.
        Requires v2 API authentication.
        """
        try:
            await tag_service.merge(params.source_tag, params.target_tag)
            return f"""## Tags Merged

- **Merged**: `{params.source_tag}` → `{params.target_tag}`
- The source tag has been deleted
- All tasks now use the target tag
"""
        except Exception as e:
            return f"**Error**: Failed to merge tags - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_delete_tag",
        annotations={
            "title": "Delete TickTick Tag",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_tag(params: DeleteTagInput) -> str:
        """
        Delete a tag.

        The tag will be removed from all tasks.
        Requires v2 API authentication.
        """
        try:
            await tag_service.delete(params.name)
            return f"## Tag Deleted\n\nTag `{params.name}` has been deleted and removed from all tasks."
        except Exception as e:
            return f"**Error**: Failed to delete tag - {str(e)}\n\n_Note: This feature requires v2 API authentication._"

    @mcp.tool(
        name="ticktick_get_tag_tasks",
        annotations={
            "title": "Get Tasks by Tag",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_tag_tasks(params: GetTagTasksInput) -> str:
        """
        Get all tasks that have a specific tag.

        Requires v2 API authentication.
        """
        try:
            tasks = await tag_service.get_tasks_by_tag(params.tag_name)
            if not tasks:
                return f"## Tasks with tag `{params.tag_name}`\n\nNo tasks found."

            lines = [f"## Tasks with tag `{params.tag_name}` ({len(tasks)} total)\n"]
            for task in tasks:
                status = "✅" if task.status == 2 else "⬜"
                lines.append(f"- {status} **{task.title}** (`{task.id}`)")
                if task.due_date:
                    lines.append(f"  - Due: {task.due_date}")

            return "\n".join(lines)
        except Exception as e:
            return f"**Error**: Failed to get tasks - {str(e)}\n\n_Note: This feature requires v2 API authentication._"
