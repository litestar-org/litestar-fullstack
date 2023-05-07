from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TCH003

import sqlalchemy as sa
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.db import orm

if TYPE_CHECKING:
    from app.domain.accounts.models import User

__all__ = ["Team", "TeamInvitation", "TeamMember", "TeamRoles"]


class TeamRoles(str, Enum):
    """Team Roles."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Team(orm.DatabaseModel, orm.AuditColumns, orm.SlugKey):
    """Team."""

    __tablename__ = "team"  # type: ignore[assignment]
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(sa.String(length=500))
    is_active: Mapped[bool] = mapped_column(default=True)
    # -----------
    # ORM Relationships
    # ------------
    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team",
        cascade="all, delete",
        lazy="noload",
        passive_deletes=True,
    )
    invitations: Mapped[list[TeamInvitation]] = relationship(
        back_populates="team",
        cascade="all, delete",
        lazy="noload",
    )
    pending_invitations: Mapped[list[TeamInvitation]] = relationship(
        primaryjoin="and_(TeamInvitation.team_id==Team.id, TeamInvitation.is_accepted == False)",
        viewonly=True,
        lazy="noload",
    )


class TeamMember(orm.DatabaseModel, orm.AuditColumns):
    """Team Membership."""

    __tablename__ = "team_member"  # type: ignore[assignment]
    __table_args__ = (sa.UniqueConstraint("user_id", "team_id"),)
    user_id: Mapped[UUID] = mapped_column(sa.ForeignKey("user_account.id", ondelete="cascade"))
    team_id: Mapped[UUID] = mapped_column(sa.ForeignKey("team.id", ondelete="cascade"))
    role: Mapped[TeamRoles] = mapped_column(sa.String(length=50), default=TeamRoles.MEMBER, index=True)
    is_owner: Mapped[bool] = mapped_column(default=False)
    user_name: AssociationProxy[str] = association_proxy("user", "name")
    user_email: AssociationProxy[str] = association_proxy("user", "email")
    team_name: AssociationProxy[str] = association_proxy("team", "name")
    # -----------
    # ORM Relationships
    # ------------
    user: Mapped[User] = relationship(
        back_populates="teams",
        foreign_keys="TeamMember.user_id",
        innerjoin=True,
        uselist=False,
        lazy="noload",
    )
    team: Mapped[Team] = relationship(
        back_populates="members",
        foreign_keys="TeamMember.team_id",
        innerjoin=True,
        uselist=False,
        lazy="noload",
    )


class TeamInvitation(orm.DatabaseModel, orm.AuditColumns):
    """Team Invite."""

    __tablename__ = "team_invitation"  # type: ignore[assignment]
    team_id: Mapped[UUID] = mapped_column(sa.ForeignKey("team.id", ondelete="cascade"))
    email: Mapped[str] = mapped_column(index=True)
    role: Mapped[TeamRoles] = mapped_column(sa.String(length=50), default=TeamRoles.MEMBER)
    is_accepted: Mapped[bool] = mapped_column(default=False)
    invited_by_id: Mapped[UUID | None] = mapped_column(sa.ForeignKey("user_account.id", ondelete="set null"))
    invited_by_email: Mapped[str]
    # -----------
    # ORM Relationships
    # ------------
    team: Mapped[Team] = relationship(foreign_keys="TeamInvitation.team_id", lazy="noload")
    invited_by: Mapped[User] = relationship(foreign_keys="TeamInvitation.invited_by_id", lazy="noload", uselist=False)
