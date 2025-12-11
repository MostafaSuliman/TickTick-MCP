"""
Project Service - Project and folder management operations.
"""

import logging
from typing import Any, Dict, List, Optional

from ..api.client import TickTickClient
from ..api.endpoints import APIVersion, Endpoints
from ..models.projects import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectKind,
    Folder,
    FolderCreate,
    FolderUpdate,
)
from .base_service import CRUDService

logger = logging.getLogger(__name__)


class ProjectService(CRUDService[Project]):
    """
    Service for project/list and folder management.

    Projects are the main organizational unit in TickTick (also called "lists").
    Folders allow grouping projects together.
    """

    def __init__(self, client: TickTickClient):
        super().__init__(client)

    # =========================================================================
    # Project CRUD Operations
    # =========================================================================

    async def list(self, include_archived: bool = False) -> List[Project]:
        """
        List all projects.

        Args:
            include_archived: Include archived projects

        Returns:
            List of Project objects
        """
        url = Endpoints.Projects.list_v1()
        data = await self.client.get(url, version=APIVersion.V1)

        projects = [Project(**p) for p in data] if isinstance(data, list) else []

        if not include_archived:
            projects = [p for p in projects if not p.closed]

        return projects

    async def get(self, project_id: str) -> Project:
        """
        Get a specific project by ID.

        Args:
            project_id: Project identifier

        Returns:
            Project object
        """
        # V1 doesn't have direct project get, need to list and filter
        projects = await self.list(include_archived=True)
        for project in projects:
            if project.id == project_id:
                return project

        raise Exception(f"Project '{project_id}' not found")

    async def create(self, project_data: ProjectCreate) -> Project:
        """
        Create a new project.

        Args:
            project_data: Project creation data

        Returns:
            Created Project object
        """
        payload = {
            "name": project_data.name,
        }

        if project_data.color:
            payload["color"] = project_data.color
        if project_data.kind:
            payload["kind"] = project_data.kind.value
        if project_data.folder_id:
            payload["groupId"] = project_data.folder_id
        if project_data.view_mode:
            payload["viewMode"] = project_data.view_mode.value

        url = Endpoints.Projects.create_v1()
        data = await self.client.post(url, version=APIVersion.V1, data=payload)

        return Project(**data)

    async def update(self, project_data: ProjectUpdate) -> Project:
        """
        Update an existing project (v2 only for full update).

        Args:
            project_data: Project update data

        Returns:
            Updated Project object
        """
        if not self.is_v2_available:
            logger.warning("Full project update requires v2 API")
            # Limited v1 update - just create new and delete old
            existing = await self.get(project_data.id)

            # Create with new settings
            create_data = ProjectCreate(
                name=project_data.name or existing.name,
                color=project_data.color or existing.color,
                folder_id=project_data.folder_id or existing.group_id,
            )
            new_project = await self.create(create_data)

            # Note: This doesn't preserve tasks - full update needs v2
            return new_project

        # V2 batch update
        payload = {"id": project_data.id}
        if project_data.name:
            payload["name"] = project_data.name
        if project_data.color:
            payload["color"] = project_data.color
        if project_data.folder_id:
            payload["groupId"] = project_data.folder_id
        if project_data.view_mode:
            payload["viewMode"] = project_data.view_mode.value
        if project_data.sort_order is not None:
            payload["sortOrder"] = project_data.sort_order

        url = Endpoints.Projects.batch_v2()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"update": [payload]}
        )

        updated = data.get("update", [])
        if updated:
            return Project(**updated[0])
        return await self.get(project_data.id)

    async def delete(self, project_id: str) -> bool:
        """
        Delete a project.

        Warning: This will delete all tasks in the project!

        Args:
            project_id: Project to delete

        Returns:
            True if successful
        """
        url = Endpoints.Projects.delete_v1(project_id)
        await self.client.delete(url, version=APIVersion.V1)
        return True

    # =========================================================================
    # Extended Project Operations
    # =========================================================================

    async def archive(self, project_id: str) -> bool:
        """
        Archive a project (v2 only).

        Args:
            project_id: Project to archive

        Returns:
            True if successful
        """
        if not self.is_v2_available:
            logger.warning("Archive requires v2 API")
            return False

        url = Endpoints.Projects.batch_v2()
        payload = {"update": [{"id": project_id, "closed": True}]}
        await self.client.post(url, version=APIVersion.V2, data=payload)
        return True

    async def unarchive(self, project_id: str) -> bool:
        """
        Unarchive a project (v2 only).

        Args:
            project_id: Project to unarchive

        Returns:
            True if successful
        """
        if not self.is_v2_available:
            logger.warning("Unarchive requires v2 API")
            return False

        url = Endpoints.Projects.batch_v2()
        payload = {"update": [{"id": project_id, "closed": False}]}
        await self.client.post(url, version=APIVersion.V2, data=payload)
        return True

    async def get_with_tasks(self, project_id: str) -> Dict[str, Any]:
        """
        Get project data including all its tasks.

        Args:
            project_id: Project identifier

        Returns:
            Dict with project info and tasks
        """
        url = Endpoints.Projects.data_v1(project_id)
        data = await self.client.get(url, version=APIVersion.V1)
        return data

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_create(self, projects: List[ProjectCreate]) -> List[Project]:
        """
        Create multiple projects (v2 only).

        Args:
            projects: List of projects to create

        Returns:
            List of created projects
        """
        if not self.is_v2_available:
            # Fallback to sequential
            results = []
            for project in projects:
                results.append(await self.create(project))
            return results

        payloads = []
        for p in projects:
            payload = {"name": p.name}
            if p.color:
                payload["color"] = p.color
            if p.kind:
                payload["kind"] = p.kind.value
            if p.folder_id:
                payload["groupId"] = p.folder_id
            payloads.append(payload)

        url = Endpoints.Projects.batch_v2()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"add": payloads}
        )

        return [Project(**p) for p in data.get("add", [])]

    async def batch_delete(self, project_ids: List[str]) -> bool:
        """
        Delete multiple projects (v2 only).

        Args:
            project_ids: List of project IDs to delete

        Returns:
            True if successful
        """
        if not self.is_v2_available:
            for pid in project_ids:
                await self.delete(pid)
            return True

        url = Endpoints.Projects.batch_v2()
        await self.client.post(
            url,
            version=APIVersion.V2,
            data={"delete": project_ids}
        )
        return True

    async def batch_archive(self, project_ids: List[str]) -> bool:
        """
        Archive multiple projects (v2 only).

        Args:
            project_ids: List of project IDs to archive

        Returns:
            True if successful
        """
        if not self.is_v2_available:
            return False

        url = Endpoints.Projects.batch_v2()
        payloads = [{"id": pid, "closed": True} for pid in project_ids]
        await self.client.post(url, version=APIVersion.V2, data={"update": payloads})
        return True

    # =========================================================================
    # Folder Operations (v2 only)
    # =========================================================================

    async def list_folders(self) -> List[Folder]:
        """
        List all folders (v2 only).

        Returns:
            List of Folder objects
        """
        if not self.is_v2_available:
            logger.warning("Folders require v2 API")
            return []

        # Folders come from sync data
        sync_data = await self.client.sync()
        folders_data = sync_data.get("projectGroups", [])
        return [Folder(**f) for f in folders_data]

    async def create_folder(self, folder_data: FolderCreate) -> Folder:
        """
        Create a new folder (v2 only).

        Args:
            folder_data: Folder creation data

        Returns:
            Created Folder object
        """
        if not self.is_v2_available:
            raise Exception("Folders require v2 API authentication")

        payload = {
            "name": folder_data.name,
            "listType": "group",
        }

        url = Endpoints.Projects.batch_folder_v2()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"add": [payload]}
        )

        folders = data.get("add", [])
        if folders:
            return Folder(**folders[0])
        raise Exception("Folder creation failed")

    async def update_folder(self, folder_data: FolderUpdate) -> Folder:
        """
        Update a folder (v2 only).

        Args:
            folder_data: Folder update data

        Returns:
            Updated Folder object
        """
        if not self.is_v2_available:
            raise Exception("Folders require v2 API authentication")

        payload = {"id": folder_data.id}
        if folder_data.name:
            payload["name"] = folder_data.name
        if folder_data.sort_order is not None:
            payload["sortOrder"] = folder_data.sort_order

        url = Endpoints.Projects.batch_folder_v2()
        data = await self.client.post(
            url,
            version=APIVersion.V2,
            data={"update": [payload]}
        )

        folders = data.get("update", [])
        if folders:
            return Folder(**folders[0])

        # Return current folder
        all_folders = await self.list_folders()
        for f in all_folders:
            if f.id == folder_data.id:
                return f
        raise Exception("Folder not found")

    async def delete_folder(self, folder_id: str) -> bool:
        """
        Delete a folder (v2 only).

        Note: Projects in the folder will be moved to root.

        Args:
            folder_id: Folder to delete

        Returns:
            True if successful
        """
        if not self.is_v2_available:
            raise Exception("Folders require v2 API authentication")

        url = Endpoints.Projects.batch_folder_v2()
        await self.client.post(
            url,
            version=APIVersion.V2,
            data={"delete": [folder_id]}
        )
        return True

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_project(self, project: Project) -> str:
        """Format a single project as markdown."""
        lines = [
            f"### {project.name}",
            f"- **ID**: `{project.id}`",
        ]

        if project.color:
            lines.append(f"- **Color**: {project.color}")
        if project.group_id:
            lines.append(f"- **Folder ID**: `{project.group_id}`")
        if project.kind:
            lines.append(f"- **Type**: {project.kind.value}")
        if project.view_mode:
            lines.append(f"- **View Mode**: {project.view_mode.value}")
        if project.closed:
            lines.append("- **Status**: Archived")

        return "\n".join(lines)

    def format_project_list(
        self,
        projects: List[Project],
        folders: Optional[List[Folder]] = None,
        title: str = "Projects",
    ) -> str:
        """Format projects with folder grouping as markdown."""
        if not projects:
            return f"##  {title}\n\nNo projects found."

        lines = [f"##  {title} ({len(projects)} total)\n"]

        # Build folder lookup
        folder_map = {}
        if folders:
            for f in folders:
                folder_map[f.id] = f.name

        # Group by folder
        by_folder: Dict[Optional[str], List[Project]] = {}
        for project in projects:
            folder_id = project.group_id
            if folder_id not in by_folder:
                by_folder[folder_id] = []
            by_folder[folder_id].append(project)

        # Root projects first
        if None in by_folder:
            lines.append("\n### Root Projects\n")
            for project in by_folder[None]:
                lines.append(self.format_project(project))
                lines.append("")

        # Then by folder
        for folder_id, folder_projects in by_folder.items():
            if folder_id is None:
                continue
            folder_name = folder_map.get(folder_id, folder_id)
            lines.append(f"\n###  {folder_name}\n")
            for project in folder_projects:
                lines.append(self.format_project(project))
                lines.append("")

        return "\n".join(lines)

    def format_folder(self, folder: Folder) -> str:
        """Format a folder as markdown."""
        return f"- ** {folder.name}** (ID: `{folder.id}`)"

    def format_folder_list(self, folders: List[Folder]) -> str:
        """Format folder list as markdown."""
        if not folders:
            return "##  Folders\n\nNo folders found."

        lines = [f"##  Folders ({len(folders)} total)\n"]
        for folder in folders:
            lines.append(self.format_folder(folder))

        return "\n".join(lines)
