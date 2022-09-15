from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import EmailStr
from sqlalchemy import orm

from pyspa.db import db_types as t
from pyspa.models.base import BaseModel, CreatedUpdatedAtMixin

if TYPE_CHECKING:
    from .team import TeamMember


class User(BaseModel, CreatedUpdatedAtMixin):
    """Users"""

    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}

    full_name: orm.Mapped[str] = sa.Column(sa.String(length=255), nullable=True)
    email: orm.Mapped[EmailStr] = sa.Column(t.EmailString, unique=True, index=True, nullable=False)
    hashed_password: orm.Mapped[str] = sa.Column(sa.String(length=255), nullable=True)
    is_active: orm.Mapped[bool] = sa.Column(sa.Boolean, default=True, nullable=False)
    is_superuser: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False, nullable=False)
    is_verified: orm.Mapped[bool] = sa.Column(sa.Boolean, default=False, nullable=False)
    # -----------
    # ORM Relationships
    # ------------
    teams: orm.Mapped[list["TeamMember"]] = orm.relationship(
        "TeamMember",
        back_populates="user",
        lazy="subquery",
        cascade="all, delete",
    )
