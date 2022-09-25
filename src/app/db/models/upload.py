from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import orm

from app.db.models.base import BaseModel, CreatedUpdatedAtMixin

if TYPE_CHECKING:
    from .team import Team


class Upload(BaseModel, CreatedUpdatedAtMixin):
    """Users"""

    __tablename__ = "upload"
    __table_args__ = {"comment": "Stores links to uploaded files"}

    file_name: orm.Mapped[str] = sa.Column(sa.String(length=255), index=True)
    uploaded_by: orm.Mapped[str] = sa.Column(sa.String(length=255), index=False)
    is_processed: orm.Mapped[bool] = sa.Column(sa.Boolean, nullable=False, default=False, index=True)
    team_id: orm.Mapped[UUID4] = sa.Column(sa.ForeignKey("team.id", ondelete="cascade"), nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    team: orm.Mapped["Team"] = orm.relationship(
        "Team",
        back_populates="uploads",
        lazy="noload",
        join_depth=1,
        innerjoin=True,
        viewonly=True,
    )
