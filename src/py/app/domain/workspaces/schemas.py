from uuid import UUID
from datetime import datetime

import msgspec
from app.lib.schema import CamelizedBaseStruct
from app.db.models._workspace import TaskStatus, TaskPriority
from app.domain.accounts.schemas import User


class Task(CamelizedBaseStruct):
    id: UUID
    title: str
    status: TaskStatus
    priority: TaskPriority
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    assignee_id: UUID | None = None
    assignee: User | None = None


class TaskCreate(CamelizedBaseStruct):
    title: str
    workspace_id: UUID
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: UUID | None = None


class TaskUpdate(CamelizedBaseStruct, omit_defaults=True):
    title: str | msgspec.UnsetType | None = msgspec.UNSET
    description: str | msgspec.UnsetType | None = msgspec.UNSET
    status: TaskStatus | msgspec.UnsetType | None = msgspec.UNSET
    priority: TaskPriority | msgspec.UnsetType | None = msgspec.UNSET
    assignee_id: UUID | msgspec.UnsetType | None = msgspec.UNSET


class Workspace(CamelizedBaseStruct):
    id: UUID
    name: str
    slug: str
    team_id: UUID
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    tasks: list[Task] = []


class WorkspaceCreate(CamelizedBaseStruct):
    name: str
    team_id: UUID
    description: str | None = None


class WorkspaceUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | msgspec.UnsetType | None = msgspec.UNSET
    description: str | msgspec.UnsetType | None = msgspec.UNSET
