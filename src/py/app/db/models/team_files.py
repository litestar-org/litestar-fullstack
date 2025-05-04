from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import FileObject, StoredObject
from sqlalchemy import ForeignKey
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.team import Team
    from app.db.models.user import User


class TeamFiles(UUIDAuditBase):
    """Team Files."""

    __tablename__ = "team_files"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.id", ondelete="cascade"), nullable=False)
    file: Mapped[FileObject] = mapped_column(StoredObject(backend="private"))
    uploaded_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("user_account.id", ondelete="set null"))

    # -----------
    # ORM Relationships
    # ------------
    uploaded_by: Mapped[User] = relationship(foreign_keys="TeamFiles.uploaded_by_id", uselist=False)
    uploaded_by_name: AssociationProxy[str] = association_proxy("uploaded_by", "name")
    uploaded_by_email: AssociationProxy[str] = association_proxy("uploaded_by", "email")
    team: Mapped[Team] = relationship(
        back_populates="files", foreign_keys="TeamFiles.team_id", innerjoin=True, uselist=False
    )
    team_name: AssociationProxy[str] = association_proxy("team", "name")
