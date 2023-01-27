from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from pydantic import constr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib import dto, orm
from app.utils.text import check_email

if TYPE_CHECKING:
    from app.domain.accounts.models import User

__all__ = ["Team", "TeamInvitation", "TeamMember", "TeamRoles"]


class TeamRoles(str, Enum):
    """Team Roles."""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Team(orm.DatabaseModel):
    """Team."""

    __tablename__ = "team"  # type: ignore[assignment]
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(sa.String(length=500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    members: Mapped[list[TeamMember]] = relationship(
        back_populates="team", cascade="all, delete", lazy="noload", passive_deletes=True
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


class TeamMember(orm.DatabaseModel):
    """Team Membership."""

    __tablename__ = "team_member"  # type: ignore[assignment]
    __table_args__ = (sa.UniqueConstraint("user_id", "team_id"),)
    user_id: Mapped[UUID] = mapped_column(sa.ForeignKey("user_account.id", ondelete="cascade"), nullable=False)
    team_id: Mapped[UUID] = mapped_column(sa.ForeignKey("team.id", ondelete="cascade"), nullable=False)
    role: Mapped[TeamRoles] = mapped_column(sa.String(length=50), default=TeamRoles.MEMBER, nullable=False, index=True)
    is_owner: Mapped[bool] = mapped_column(default=False, nullable=False)

    # -----------
    # ORM Relationships
    # ------------
    user: Mapped[User] = relationship(
        back_populates="teams",
        foreign_keys="TeamMember.user_id",
        innerjoin=True,
        uselist=False,
        cascade="all, delete",
        lazy="noload",
    )
    team: Mapped[Team] = relationship(
        back_populates="members",
        foreign_keys="TeamMember.team_id",
        innerjoin=True,
        uselist=False,
        cascade="all, delete",
        lazy="noload",
    )


class TeamInvitation(orm.DatabaseModel):
    """Team Invite."""

    __tablename__ = "team_invitation"  # type: ignore[assignment]
    team_id: Mapped[UUID] = mapped_column(sa.ForeignKey("team.id", ondelete="cascade"), nullable=False)
    email: Mapped[str] = mapped_column(
        nullable=False, info=dto.field(validators=[check_email], pydantic_type=constr(to_lower=True))
    )
    role: Mapped[TeamRoles] = mapped_column(sa.String(length=50), default=TeamRoles.MEMBER, nullable=False)
    is_accepted: Mapped[bool] = mapped_column(default=False)
    invited_by_id: Mapped[UUID | None] = mapped_column(
        sa.ForeignKey("user_account.id", ondelete="set null"), nullable=True
    )
    invited_by_email: Mapped[str] = mapped_column(
        nullable=False, info=dto.field(validators=[check_email], pydantic_type=constr(to_lower=True))
    )
    # -----------
    # ORM Relationships
    # ------------
    team: Mapped[Team] = relationship(foreign_keys="TeamInvitation.team_id", cascade="all, delete", lazy="noload")
    invited_by: Mapped[User] = relationship(foreign_keys="TeamInvitation.invited_by_id", lazy="noload", uselist=False)
