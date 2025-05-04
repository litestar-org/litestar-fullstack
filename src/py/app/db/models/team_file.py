from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import FileObject, StoredObject
from advanced_alchemy.utils.sync_tools import await_
from sqlalchemy import ForeignKey
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.team import Team
    from app.db.models.user import User


class TeamFile(UUIDAuditBase):
    """Team Files."""

    __tablename__ = "team_file"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    file: Mapped[FileObject] = mapped_column(StoredObject(backend="private"))
    uploaded_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="set null"))

    # -----------
    # ORM Relationships
    # ------------
    uploaded_by: Mapped[User | None] = relationship(
        foreign_keys="TeamFile.uploaded_by_id", uselist=False, viewonly=True
    )
    uploaded_by_name: AssociationProxy[str] = association_proxy("uploaded_by", "name")
    uploaded_by_email: AssociationProxy[str] = association_proxy("uploaded_by", "email")
    team: Mapped[Team] = relationship(
        back_populates="files", foreign_keys="TeamFile.team_id", innerjoin=True, uselist=False, viewonly=True
    )
    team_name: AssociationProxy[str] = association_proxy("team", "name")

    @hybrid_property
    def url(self) -> str:
        return await_(self.file.sign_async)()
