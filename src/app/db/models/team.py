from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .team_tag import team_tag

if TYPE_CHECKING:
    from .tag import Tag
    from .team_invitation import TeamInvitation
    from .team_member import TeamMember


class Team(UUIDAuditBase):
    """A group of users with common permissions.
    Users can create and invite users to a workspace.
    """

    __tablename__ = "workspace"  # type: ignore[assignment]
    __pii_columns__ = {"name", "description"}
    __table_args__ = {"comment": "Links a user to a specific role."}
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    members: Mapped[list[TeamMember]] = relationship(
        back_populates="workspace",
        cascade="all, delete",
        passive_deletes=True,
    )
    invitations: Mapped[list[TeamInvitation]] = relationship(
        back_populates="team",
        cascade="all, delete",
    )
    pending_invitations: Mapped[list[TeamInvitation]] = relationship(
        primaryjoin="and_(TeamInvitation.team_id==Team.id, TeamInvitation.is_accepted == False)",
        viewonly=True,
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=lambda: team_tag,
        back_populates="teams",
        cascade="all, delete",
        passive_deletes=True,
    )
