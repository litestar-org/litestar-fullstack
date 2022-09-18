# Standard Library
from enum import Enum
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import UUID4, EmailStr
from sqlalchemy import orm

from pyspa.db import db_types as t
from pyspa.models.base import BaseModel, CreatedUpdatedAtMixin, ExpiresAtMixin

if TYPE_CHECKING:
    from .upload import Upload
    from .user import User


# # ----------------------------
# Roles
class TeamRoles(str, Enum):
    """Team Role valid values"""

    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Team(BaseModel, CreatedUpdatedAtMixin):
    """Contains collections of Databases.

    Allows for grouping and permissions to be applied to a set of databases.

    Users can create and invite users to a team.
    """

    __tablename__ = "team"
    name: orm.Mapped[str] = sa.Column(sa.String(length=255), nullable=False, index=True)
    description: orm.Mapped[str] = sa.Column(sa.String(length=500), nullable=True)
    is_active: orm.Mapped[bool] = sa.Column(sa.Boolean, default=True, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    members: orm.Mapped[list["TeamMember"]] = orm.relationship(
        "TeamMember",
        back_populates="team",
        lazy="subquery",
        load_on_pending=True,
        cascade="all, delete",
        active_history=True,
    )
    invitations: orm.Mapped[list["TeamInvitation"]] = orm.relationship(
        "TeamInvitation", back_populates="team", lazy="noload"
    )
    pending_invitations: orm.Mapped[list["TeamInvitation"]] = orm.relationship(
        "TeamInvitation",
        primaryjoin="and_(TeamInvitation.team_id==Team.id, TeamInvitation.is_accepted == False)",  # noqa: E501
        viewonly=True,
        lazy="noload",
    )
    uploads: orm.Mapped[list["Upload"]] = orm.relationship("Upload", back_populates="team", lazy="noload")


class TeamMember(BaseModel, CreatedUpdatedAtMixin):
    """Team Membership"""

    __tablename__ = "team_member"
    __table_args__ = (sa.UniqueConstraint("user_id", "team_id"),)
    user_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("user_account.id"), nullable=False)
    team_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("team.id"), nullable=False)
    role: orm.Mapped[TeamRoles] = sa.Column(sa.String(length=50), default=TeamRoles.MEMBER, nullable=False, index=True)
    is_owner: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    user: orm.Mapped["User"] = orm.relationship(
        "User", back_populates="teams", lazy="joined", foreign_keys="TeamMember.user_id", active_history=True
    )
    team: orm.Mapped["Team"] = orm.relationship(
        "Team", back_populates="members", lazy="joined", foreign_keys="TeamMember.team_id", active_history=True
    )


class TeamInvitation(BaseModel, CreatedUpdatedAtMixin, ExpiresAtMixin):
    """Team Invite"""

    __tablename__ = "team_invitation"
    team_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("team.id"), nullable=False)
    email: orm.Mapped[EmailStr] = sa.Column(t.EmailString, nullable=False)
    role: orm.Mapped[TeamRoles] = sa.Column(sa.String(length=50), default=TeamRoles.MEMBER, nullable=False)
    is_accepted: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False)
    invited_by_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("user_account.id"), nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    team: orm.Mapped["Team"] = orm.relationship("Team", foreign_keys="TeamInvitation.team_id")
    invited_by: orm.Mapped["User"] = orm.relationship("User", foreign_keys="TeamInvitation.invited_by_id")
