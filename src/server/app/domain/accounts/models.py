from __future__ import annotations

from datetime import date

import sqlalchemy as sa
from pydantic import constr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.teams.models import TeamMember
from app.lib import dto
from app.lib.db import orm
from app.utils.text import check_email

__all__ = ["User"]


class User(orm.DatabaseModel):
    """User Model."""

    __tablename__ = "user_account"  # type: ignore[assignment]
    __table_args__ = {"comment": "User accounts for application access"}
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        info=dto.field(validators=[check_email], pydantic_type=constr(to_lower=True)),
    )
    name: Mapped[str] = mapped_column(nullable=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(length=255), nullable=True, info=dto.field("private"))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, info=dto.field("read-only"))
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False, info=dto.field("read-only"))
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False, info=dto.field("read-only"))
    verified_at: Mapped[date] = mapped_column(nullable=True, info=dto.field("read-only"))
    joined_at: Mapped[date] = mapped_column(default=date.today, info=dto.field("read-only"))
    # -----------
    # ORM Relationships
    # ------------
    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="user",
        lazy="noload",
        uselist=True,
        cascade="all, delete",
        viewonly=True,
        info=dto.field("read-only"),
    )
