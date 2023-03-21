from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.db import orm

if TYPE_CHECKING:
    from app.domain.teams.models import TeamMember


__all__ = ["User"]


class User(orm.DatabaseModel):
    """User Model."""

    __tablename__ = "user_account"  # type: ignore[assignment]
    __table_args__ = {"comment": "User accounts for application access"}
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(sa.String(length=255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_at: Mapped[date | None] = mapped_column(nullable=True)
    joined_at: Mapped[date] = mapped_column(default=date.today)
    # -----------
    # ORM Relationships
    # ------------
    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="user",
        lazy="noload",
        uselist=True,
        cascade="all, delete",
        viewonly=True,
    )
