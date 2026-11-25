from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import SlugKey, UniqueMixin
from advanced_alchemy.utils.text import slugify
from sqlalchemy import ColumnElement, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models._team_tag import team_tag

if TYPE_CHECKING:
    from collections.abc import Hashable

    from app.db.models._team import Team


class Tag(UUIDv7AuditBase, SlugKey, UniqueMixin):
    """Tag."""

    __tablename__ = "tag"
    name: Mapped[str] = mapped_column(index=False)
    description: Mapped[str | None] = mapped_column(String(length=255), index=False, nullable=True)

    teams: Mapped[list[Team]] = relationship(secondary=lambda: team_tag, back_populates="tags", viewonly=True)

    @classmethod
    def unique_hash(cls, name: str, slug: str | None = None) -> Hashable:
        return slugify(name)

    @classmethod
    def unique_filter(
        cls,
        name: str,
        slug: str | None = None,
    ) -> ColumnElement[bool]:
        return cls.slug == slugify(name)
