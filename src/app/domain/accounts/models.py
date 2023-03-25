from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import func as sql_func
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
    )
    name: Mapped[str | None]
    hashed_password: Mapped[str | None] = mapped_column(String(length=255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[datetime | None]
    joined_at: Mapped[datetime] = mapped_column(default=sql_func.now())
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
