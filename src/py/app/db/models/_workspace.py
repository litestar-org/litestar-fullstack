from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import SlugKey
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._team import Team
    from app.db.models._user import User


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Workspace(UUIDv7AuditBase, SlugKey):
    """Workspaces for organizing tasks."""
    
    __tablename__ = "workspace"
    __pii_columns__ = {"name", "description"}
    
    name: Mapped[str] = mapped_column(String(length=100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=500), nullable=True)
    
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"))
    team: Mapped[Team] = relationship(lazy="selectin")
    
    tasks: Mapped[list[Task]] = relationship(
        back_populates="workspace", 
        cascade="all, delete",
        passive_deletes=True,
    )


class Task(UUIDv7AuditBase):
    """Tasks within a workspace."""
    
    __tablename__ = "task"
    __pii_columns__ = {"title", "description"}
    
    title: Mapped[str] = mapped_column(String(length=100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.TODO)
    priority: Mapped[TaskPriority] = mapped_column(default=TaskPriority.MEDIUM)
    
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspace.id", ondelete="CASCADE"))
    workspace: Mapped[Workspace] = relationship(back_populates="tasks")
    
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="SET NULL"), nullable=True)
    assignee: Mapped[User | None] = relationship(lazy="joined")
