from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.mixins import SlugKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user_role import UserRole


class Role(UUIDAuditBase, SlugKey):
    """Role."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    # -----------
    # ORM Relationships
    # ------------
    users: Mapped[list[UserRole]] = relationship(
        back_populates="role",
        cascade="all, delete",
        lazy="noload",
        viewonly=True,
    )
