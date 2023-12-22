from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import SlugKey

if TYPE_CHECKING:
    from .team import Team


class Tag(UUIDAuditBase, SlugKey):
    """Tag."""

    __tablename__ = "tag"  # type: ignore[assignment]
    __table_args__ = {"comment": "Tags that can be applied to workspaces, databases, assessments, and collections."}
    name: Mapped[str] = mapped_column(index=False)
    description: Mapped[str | None] = mapped_column(String(length=255), index=False, nullable=True)

    # -----------
    # ORM Relationships
    # ------------
    teams: Mapped[list[Team]] = relationship(
        secondary=lambda: _team_tag(),
        back_populates="tags",
    )


def _team_tag() -> Table:
    from .team_tag import team_tag

    return team_tag
