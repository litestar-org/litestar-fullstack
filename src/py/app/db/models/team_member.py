from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

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

    __tablename__ = "team_member"
    __table_args__ = (UniqueConstraint("user_id", "team_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="cascade"), nullable=False)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"), nullable=False)
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
        back_populates="teams",
        foreign_keys="TeamMember.user_id",
        innerjoin=True,
        uselist=False,
        lazy="joined",
    )
    name: AssociationProxy[str] = association_proxy("user", "name")
    email: AssociationProxy[str] = association_proxy("user", "email")
    team: Mapped[Team] = relationship(
        back_populates="members",
        foreign_keys="TeamMember.team_id",
        innerjoin=True,
        uselist=False,
        lazy="joined",
    )
    team_name: AssociationProxy[str] = association_proxy("team", "name")
