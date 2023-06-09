from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.db.orm import TimestampedDatabaseModel

if TYPE_CHECKING:
    from app.domain.teams.models import Team

__all__ = ["Tag"]


class Tag(TimestampedDatabaseModel):
    """Tag."""

    __tablename__ = "tag"  # type: ignore[assignment]
    __table_args__ = {"comment": "Tags that can be applied to various objects"}
    name: Mapped[str] = mapped_column(index=False)
    description: Mapped[str | None] = mapped_column(sa.String(length=255), index=False, nullable=True)

    # -----------
    # ORM Relationships
    # ------------
    teams: Mapped[list[Team]] = relationship(
        secondary=lambda: _team_tag(),
        back_populates="tags",
        lazy="selectin",
    )


def _team_tag() -> sa.Table:
    # prevent circular imports
    from app.domain.teams.models import team_tag

    return team_tag
