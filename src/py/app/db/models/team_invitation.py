from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.team_roles import TeamRoles

if TYPE_CHECKING:
    from app.db.models.team import Team
    from app.db.models.user import User


class TeamInvitation(UUIDv7AuditBase):
    """Team Invite."""

    __tablename__ = "team_invitation"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"))
    email: Mapped[str] = mapped_column(index=True)
    role: Mapped[TeamRoles] = mapped_column(String(length=50), default=TeamRoles.MEMBER)
    is_accepted: Mapped[bool] = mapped_column(default=False)
    invited_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="set null"))
    invited_by_email: Mapped[str]
    # -----------
    # ORM Relationships
    # ------------
    team: Mapped[Team] = relationship(foreign_keys="TeamInvitation.team_id", innerjoin=True, viewonly=True)
    invited_by: Mapped[User | None] = relationship(
        foreign_keys="TeamInvitation.invited_by_id", uselist=False, viewonly=True
    )
