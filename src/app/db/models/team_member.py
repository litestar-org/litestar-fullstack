from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TCH003

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .team_roles import TeamRoles

if TYPE_CHECKING:
    from .team import Team
    from .user import User


class TeamMember(UUIDAuditBase):
    """Team Membership."""

    __tablename__ = "workspace_member"  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint("user_id", "workspace_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="cascade"), nullable=False)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspace.id", ondelete="cascade"), nullable=False)
    role: Mapped[TeamRoles] = mapped_column(
        String(length=50),
        default=TeamRoles.MEMBER,
        nullable=False,
        index=True,
    )
    is_owner: Mapped[bool] = mapped_column(default=False, nullable=False)

    # -----------
    # ORM Relationships
    # ------------
    user: Mapped[User] = relationship(
        back_populates="workspaces",
        foreign_keys="WorkspaceMember.user_id",
        innerjoin=True,
        uselist=False,
    )
    name: AssociationProxy[str] = association_proxy("user", "name")
    email: AssociationProxy[str] = association_proxy("user", "email")
    workspace: Mapped[Team] = relationship(
        back_populates="members",
        foreign_keys="WorkspaceMember.workspace_id",
        innerjoin=True,
        uselist=False,
    )
    workspace_name: AssociationProxy[str] = association_proxy("workspace", "name")
