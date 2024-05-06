from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import SlugKey, UUIDAuditBase
from advanced_alchemy.mixins import UniqueMixin
from sqlalchemy import (
    ColumnElement,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.utils import slugify

if TYPE_CHECKING:
    from collections.abc import Hashable

    from .team import Team


class Tag(UUIDAuditBase, SlugKey, UniqueMixin):
    """Tag."""

    __tablename__ = "tag"
    name: Mapped[str] = mapped_column(index=False)
    description: Mapped[str | None] = mapped_column(String(length=255), index=False, nullable=True)

    # -----------
    # ORM Relationships
    # ------------
    teams: Mapped[list[Team]] = relationship(
        secondary=lambda: _team_tag(),
        back_populates="tags",
    )

    @classmethod
    def unique_hash(cls, name: str, slug: str | None = None) -> Hashable:  # noqa: ARG003
        return slugify(name)

    @classmethod
    def unique_filter(
        cls,
        name: str,
        slug: str | None = None,  # noqa: ARG003
    ) -> ColumnElement[bool]:
        return cls.slug == slugify(name)


def _team_tag() -> Table:
    from .team_tag import team_tag

    return team_tag
