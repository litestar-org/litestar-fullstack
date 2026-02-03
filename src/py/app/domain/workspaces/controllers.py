from __future__ import annotations

from typing import Annotated, TYPE_CHECKING
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.workspaces.schemas import (
    Task,
    TaskCreate,
    TaskUpdate,
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
)
from app.domain.workspaces.services import TaskService, WorkspaceService
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination


class WorkspaceController(Controller):
    path = "/api/workspaces"
    tags = ["Workspaces"]
    dependencies = create_service_dependencies(
        WorkspaceService,
        key="workspace_service",
        load=[selectinload(m.Workspace.tasks).selectinload(m.Task.assignee)],
        filters={
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(operation_id="ListWorkspaces")
    async def list_workspaces(
        self,
        workspace_service: WorkspaceService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Workspace]:
        results, total = await workspace_service.list_and_count(*filters)
        return workspace_service.to_schema(results, total, filters, schema_type=Workspace)

    @post(operation_id="CreateWorkspace")
    async def create_workspace(
        self,
        workspace_service: WorkspaceService,
        data: WorkspaceCreate,
    ) -> Workspace:
        db_obj = await workspace_service.create(data.to_dict())
        return workspace_service.to_schema(db_obj, schema_type=Workspace)

    @get(path="/{workspace_id:uuid}", operation_id="GetWorkspace")
    async def get_workspace(
        self,
        workspace_service: WorkspaceService,
        workspace_id: Annotated[UUID, Parameter(title="Workspace ID", description="The workspace to retrieve.")],
    ) -> Workspace:
        db_obj = await workspace_service.get(workspace_id)
        return workspace_service.to_schema(db_obj, schema_type=Workspace)

    @patch(path="/{workspace_id:uuid}", operation_id="UpdateWorkspace")
    async def update_workspace(
        self,
        workspace_service: WorkspaceService,
        workspace_id: Annotated[UUID, Parameter(title="Workspace ID", description="The workspace to retrieve.")],
        data: WorkspaceUpdate,
    ) -> Workspace:
        db_obj = await workspace_service.update(item_id=workspace_id, data=data.to_dict())
        return workspace_service.to_schema(db_obj, schema_type=Workspace)

    @delete(path="/{workspace_id:uuid}", operation_id="DeleteWorkspace")
    async def delete_workspace(
        self,
        workspace_service: WorkspaceService,
        workspace_id: Annotated[UUID, Parameter(title="Workspace ID", description="The workspace to retrieve.")],
    ) -> None:
        await workspace_service.delete(workspace_id)


class TaskController(Controller):
    path = "/api/tasks"
    tags = ["Tasks"]
    dependencies = create_service_dependencies(
        TaskService,
        key="task_service",
        load=[selectinload(m.Task.assignee)],
        filters={
            "id_filter": UUID,
            "pagination_type": "limit_offset",
            "pagination_size": 20,
        },
    )

    @post(operation_id="CreateTask")
    async def create_task(
        self,
        task_service: TaskService,
        data: TaskCreate,
    ) -> Task:
        db_obj = await task_service.create(data.to_dict())
        return task_service.to_schema(db_obj, schema_type=Task)

    @patch(path="/{task_id:uuid}", operation_id="UpdateTask")
    async def update_task(
        self,
        task_service: TaskService,
        task_id: Annotated[UUID, Parameter(title="Task ID", description="The task to update.")],
        data: TaskUpdate,
    ) -> Task:
        db_obj = await task_service.update(item_id=task_id, data=data.to_dict())
        return task_service.to_schema(db_obj, schema_type=Task)

    @delete(path="/{task_id:uuid}", operation_id="DeleteTask")
    async def delete_task(
        self,
        task_service: TaskService,
        task_id: Annotated[UUID, Parameter(title="Task ID", description="The task to delete.")],
    ) -> None:
        await task_service.delete(task_id)
