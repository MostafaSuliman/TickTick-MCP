"""
Project MCP tools - Project and folder management.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ListProjectsInput(BaseModel):
    """Input for listing projects."""
    include_archived: bool = Field(
        default=False,
        description="Include archived projects"
    )


class GetProjectInput(BaseModel):
    """Input for getting a specific project."""
    project_id: str = Field(..., description="Project ID")


class CreateProjectInput(BaseModel):
    """Input for creating a project."""
    name: str = Field(..., description="Project name", min_length=1, max_length=100)
    color: Optional[str] = Field(
        default=None,
        description="Project color (hex code, e.g., '#FF5733')"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Folder ID to place project in"
    )
    view_mode: Optional[str] = Field(
        default="list",
        description="View mode: list, kanban, timeline"
    )


class UpdateProjectInput(BaseModel):
    """Input for updating a project."""
    project_id: str = Field(..., description="Project ID to update")
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None)
    folder_id: Optional[str] = Field(default=None)
    view_mode: Optional[str] = Field(default=None)


class DeleteProjectInput(BaseModel):
    """Input for deleting a project."""
    project_id: str = Field(..., description="Project ID to delete")


class ArchiveProjectInput(BaseModel):
    """Input for archiving a project."""
    project_id: str = Field(..., description="Project ID to archive")


class ListFoldersInput(BaseModel):
    """Input for listing folders."""
    pass


class CreateFolderInput(BaseModel):
    """Input for creating a folder."""
    name: str = Field(..., description="Folder name", min_length=1, max_length=100)


class UpdateFolderInput(BaseModel):
    """Input for updating a folder."""
    folder_id: str = Field(..., description="Folder ID to update")
    name: str = Field(..., description="New folder name", max_length=100)


class DeleteFolderInput(BaseModel):
    """Input for deleting a folder."""
    folder_id: str = Field(..., description="Folder ID to delete")


def register_project_tools(mcp, project_service):
    """Register project management tools."""

    @mcp.tool(
        name="ticktick_list_projects",
        annotations={
            "title": "List TickTick Projects",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_projects(params: ListProjectsInput) -> str:
        """
        List all projects/lists.

        Returns project details including ID, name, color, and task count.
        """
        try:
            projects = await project_service.list(
                include_archived=params.include_archived
            )
            return project_service.format_project_list(projects)
        except Exception as e:
            return f"**Error**: Failed to list projects - {str(e)}"

    @mcp.tool(
        name="ticktick_get_project",
        annotations={
            "title": "Get TickTick Project",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def get_project(params: GetProjectInput) -> str:
        """
        Get details of a specific project including its tasks.
        """
        try:
            project = await project_service.get(params.project_id)
            return project_service.format_project(project)
        except Exception as e:
            return f"**Error**: Could not find project - {str(e)}"

    @mcp.tool(
        name="ticktick_create_project",
        annotations={
            "title": "Create TickTick Project",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_project(params: CreateProjectInput) -> str:
        """
        Create a new project/list.

        Projects can be organized in folders and have different view modes.
        """
        from ..models.projects import ProjectCreate

        project_data = ProjectCreate(
            name=params.name,
            color=params.color,
            folder_id=params.folder_id,
            view_mode=params.view_mode,
        )

        try:
            project = await project_service.create(project_data)
            return f"""## Project Created

{project_service.format_project(project)}
"""
        except Exception as e:
            return f"**Error**: Failed to create project - {str(e)}"

    @mcp.tool(
        name="ticktick_update_project",
        annotations={
            "title": "Update TickTick Project",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_project(params: UpdateProjectInput) -> str:
        """
        Update an existing project's properties.
        """
        from ..models.projects import ProjectUpdate

        update_data = ProjectUpdate(
            id=params.project_id,
            name=params.name,
            color=params.color,
            folder_id=params.folder_id,
            view_mode=params.view_mode,
        )

        try:
            project = await project_service.update(update_data)
            return f"""## Project Updated

{project_service.format_project(project)}
"""
        except Exception as e:
            return f"**Error**: Failed to update project - {str(e)}"

    @mcp.tool(
        name="ticktick_delete_project",
        annotations={
            "title": "Delete TickTick Project",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_project(params: DeleteProjectInput) -> str:
        """
        Delete a project and all its tasks.

        Warning: This action cannot be undone. All tasks in the project will be deleted.
        """
        try:
            await project_service.delete(params.project_id)
            return f"## Project Deleted\n\nProject `{params.project_id}` and all its tasks have been deleted."
        except Exception as e:
            return f"**Error**: Failed to delete project - {str(e)}"

    @mcp.tool(
        name="ticktick_archive_project",
        annotations={
            "title": "Archive TickTick Project",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def archive_project(params: ArchiveProjectInput) -> str:
        """
        Archive a project.

        Archived projects are hidden from the main view but can be restored.
        Requires v2 API authentication.
        """
        try:
            await project_service.archive(params.project_id)
            return f"## Project Archived\n\nProject `{params.project_id}` has been archived."
        except Exception as e:
            return f"**Error**: Failed to archive project - {str(e)}"

    @mcp.tool(
        name="ticktick_list_folders",
        annotations={
            "title": "List TickTick Folders",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def list_folders(params: ListFoldersInput) -> str:
        """
        List all project folders.

        Folders are used to organize projects.
        """
        try:
            folders = await project_service.list_folders()
            return project_service.format_folder_list(folders)
        except Exception as e:
            return f"**Error**: Failed to list folders - {str(e)}"

    @mcp.tool(
        name="ticktick_create_folder",
        annotations={
            "title": "Create Project Folder",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
        }
    )
    async def create_folder(params: CreateFolderInput) -> str:
        """
        Create a new project folder.

        Folders help organize projects into logical groups.
        """
        from ..models.projects import FolderCreate

        try:
            folder = await project_service.create_folder(
                FolderCreate(name=params.name)
            )
            return f"""## Folder Created

- **ID**: `{folder.id}`
- **Name**: {folder.name}
"""
        except Exception as e:
            return f"**Error**: Failed to create folder - {str(e)}"

    @mcp.tool(
        name="ticktick_update_folder",
        annotations={
            "title": "Update Project Folder",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
        }
    )
    async def update_folder(params: UpdateFolderInput) -> str:
        """
        Rename a project folder.
        """
        from ..models.projects import FolderUpdate

        try:
            folder = await project_service.update_folder(
                FolderUpdate(id=params.folder_id, name=params.name)
            )
            return f"""## Folder Updated

- **ID**: `{folder.id}`
- **Name**: {folder.name}
"""
        except Exception as e:
            return f"**Error**: Failed to update folder - {str(e)}"

    @mcp.tool(
        name="ticktick_delete_folder",
        annotations={
            "title": "Delete Project Folder",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
        }
    )
    async def delete_folder(params: DeleteFolderInput) -> str:
        """
        Delete a project folder.

        Projects in the folder will be moved to the root level.
        """
        try:
            await project_service.delete_folder(params.folder_id)
            return f"## Folder Deleted\n\nFolder `{params.folder_id}` has been deleted. Projects have been moved to root."
        except Exception as e:
            return f"**Error**: Failed to delete folder - {str(e)}"
