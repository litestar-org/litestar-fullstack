# Standard Library
from enum import Enum
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import UUID4, EmailStr
from sqlalchemy import orm

from pyspa.db import db_types as t
from pyspa.models.base import BaseModel, CreatedUpdatedAtMixin, ExpiresAtMixin

if TYPE_CHECKING:
    from .collection import Collection, Upload
    from .organization import Organization
    from .user import User


# # ----------------------------
# Roles
class WorkspaceRoleTypes(str, Enum):
    """Workspace Role valid values"""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Workspace(BaseModel, CreatedUpdatedAtMixin):
    """Contains collections of Databases.

    Allows for grouping and permissions to be applied to a set of databases.

    Users can create and invite users to a workspace.
    """

    __tablename__ = "workspace"
    name: orm.Mapped[str] = sa.Column(sa.Unicode(255), nullable=False, index=True)  # type: ignore[no-untyped-call]
    description: orm.Mapped[str] = sa.Column(sa.Unicode(500))  # type: ignore[no-untyped-call]
    organization_id: orm.Mapped[UUID4] = sa.Column(
        sa.ForeignKey("organization.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: orm.Mapped[bool] = sa.Column(sa.Boolean, default=True, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    members: orm.Mapped[list["WorkspaceMember"]] = orm.relationship(
        "WorkspaceMember",
        back_populates="workspace",
        lazy="subquery",
        load_on_pending=True,
        cascade="all, delete",
        active_history=True,
    )
    invitations: orm.Mapped[list["WorkspaceInvitation"]] = orm.relationship(
        "WorkspaceInvitation",
        back_populates="workspace",
        lazy="noload",
    )
    pending_invitations: orm.Mapped[list["WorkspaceInvitation"]] = orm.relationship(
        "WorkspaceInvitation",
        primaryjoin="and_(WorkspaceInvitation.workspace_id==Workspace.id, WorkspaceInvitation.is_accepted == False)",  # noqa: E501
        viewonly=True,
        lazy="noload",
    )
    organization: orm.Mapped["Organization"] = orm.relationship(
        "Organization",
        uselist=False,
        back_populates="workspaces",
        lazy="noload",
    )
    collections: orm.Mapped[list["Collection"]] = orm.relationship(
        "Collection",
        back_populates="workspace",
        lazy="subquery",
    )
    uploads: orm.Mapped[list["Upload"]] = orm.relationship(
        "Upload",
        back_populates="workspace",
        lazy="noload",
    )


class WorkspaceMember(BaseModel, CreatedUpdatedAtMixin):
    """Workspace Membership"""

    __tablename__ = "workspace_member"
    __table_args__ = (sa.UniqueConstraint("user_id", "workspace_id"),)
    user_id: orm.Mapped[UUID4] = sa.Column(
        sa.ForeignKey("user_account.id"),
        nullable=False,
    )
    workspace_id: orm.Mapped[UUID4] = sa.Column(
        sa.ForeignKey("workspace.id"),
        nullable=False,
    )
    role: orm.Mapped[WorkspaceRoleTypes] = sa.Column(
        sa.String(length=50),
        default=WorkspaceRoleTypes.MEMBER,
        nullable=False,
        index=True,
    )
    is_owner: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    user: orm.Mapped["User"] = orm.relationship(
        "User",
        back_populates="workspaces",
        lazy="joined",
        foreign_keys="WorkspaceMember.user_id",
        active_history=True,
    )
    workspace: orm.Mapped["Workspace"] = orm.relationship(
        "Workspace",
        back_populates="members",
        lazy="joined",
        foreign_keys="WorkspaceMember.workspace_id",
        active_history=True,
    )


class WorkspaceInvitation(BaseModel, CreatedUpdatedAtMixin, ExpiresAtMixin):
    """Workspace Invite"""

    __tablename__ = "workspace_invitation"
    workspace_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("workspace.id"), nullable=False)
    email: orm.Mapped[EmailStr] = sa.Column(t.EmailString, nullable=False)
    role: orm.Mapped[WorkspaceRoleTypes] = sa.Column(
        sa.String(length=50), default=WorkspaceRoleTypes.MEMBER, nullable=False
    )
    is_accepted: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False)
    invited_by_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("user_account.id"), nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    workspace: orm.Mapped["Workspace"] = orm.relationship("Workspace", foreign_keys="WorkspaceInvitation.workspace_id")
    invited_by: orm.Mapped["User"] = orm.relationship("User", foreign_keys="WorkspaceInvitation.invited_by_id")
