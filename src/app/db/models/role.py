from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import SlugKey

if TYPE_CHECKING:
    from .user_role import UserRole


class Role(UUIDAuditBase, SlugKey):
    """Role."""

    __tablename__ = "role"  # type: ignore[assignment]
    __table_args__ = {"comment": "Access roles for the application"}

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    # -----------
    # ORM Relationships
    # ------------
    users: Mapped[list[UserRole]] = relationship(
        back_populates="role",
        cascade="all, delete",
        viewonly=True,
    )
