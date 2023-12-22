from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TCH003

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.team_roles import TeamRoles
from app.lib.db import orm

if TYPE_CHECKING:
    from .team import Team
    from .user import User


class TeamInvitation(orm.DatabaseModel, orm.AuditColumns):
    """Team Invite."""

    __tablename__ = "team_invitation"  # type: ignore[assignment]
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"))
    email: Mapped[str] = mapped_column(index=True)
    role: Mapped[TeamRoles] = mapped_column(String(length=50), default=TeamRoles.MEMBER)
    is_accepted: Mapped[bool] = mapped_column(default=False)
    invited_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="set null"))
    invited_by_email: Mapped[str]
    # -----------
    # ORM Relationships
    # ------------
    team: Mapped[Team] = relationship(foreign_keys="TeamInvitation.team_id", lazy="noload")
    invited_by: Mapped[User] = relationship(foreign_keys="TeamInvitation.invited_by_id", lazy="noload", uselist=False)
