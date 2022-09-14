from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy import orm

from pyspa.models.base import BaseModel, CreatedUpdatedAtMixin

if TYPE_CHECKING:
    from .workspace import Workspace


class Collection(BaseModel, CreatedUpdatedAtMixin):
    """Assessment Collection"""

    __tablename__ = "collection"
    __table_args__ = {"comment": "Stores the top level collection of files"}

    file_name: orm.Mapped[str] = sa.Column(sa.Unicode(length=255), index=True)  # type: ignore[no-untyped-call]
    uploaded_by: orm.Mapped[str] = sa.Column(sa.Unicode(length=255), index=False)  # type: ignore[no-untyped-call]
    is_processed: orm.Mapped[bool] = sa.Column(sa.Boolean, nullable=False, default=False, index=True)
    workspace_id: orm.Mapped[UUID4] = sa.Column(
        sa.ForeignKey("workspace.id", ondelete="cascade"),
        nullable=False,
    )
    # -----------
    # ORM Relationships
    # ------------
    workspace: orm.Mapped["Workspace"] = orm.relationship(
        "Workspace",
        back_populates="collections",
        innerjoin=True,
        viewonly=True,
    )


class Upload(BaseModel, CreatedUpdatedAtMixin):
    """Users"""

    __tablename__ = "upload"
    __table_args__ = {"comment": "Stores links to uploaded files"}

    file_name: orm.Mapped[str] = sa.Column(sa.String(length=255), index=True)
    uploaded_by: orm.Mapped[str] = sa.Column(sa.String(length=255), index=False)
    is_processed: orm.Mapped[bool] = sa.Column(sa.Boolean, nullable=False, default=False, index=True)
    workspace_id: orm.Mapped[UUID4] = sa.Column(
        sa.ForeignKey("workspace.id", ondelete="cascade"),
        nullable=False,
    )
    # -----------
    # ORM Relationships
    # ------------
    workspace: orm.Mapped["Workspace"] = orm.relationship(
        "Workspace",
        back_populates="uploads",
        innerjoin=True,
        viewonly=True,
    )
