from datetime import date
from typing import Annotated

import sqlalchemy as sa
from pydantic import EmailStr
from sqlalchemy.orm import Mapped, mapped_column

from app.lib import dto
from app.lib.db import orm

__all__ = ["User"]


class User(orm.DatabaseModel):
    """User Model."""

    __tablename__ = "user_account"  # type: ignore[assignment]
    __table_args__ = {"comment": "User accounts for application access"}
    email: Mapped[EmailStr] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(length=255), nullable=True, info={"dto": dto.Mark.PRIVATE})
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, info={"dto": dto.Mark.READ_ONLY})
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False, info={"dto": dto.Mark.READ_ONLY})
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False, info={"dto": dto.Mark.READ_ONLY})
    verified_at: Mapped[date] = mapped_column(nullable=True, info={"dto": dto.Mark.READ_ONLY})
    joined_at: Mapped[date] = mapped_column(default=date.today, info={"dto": dto.Mark.READ_ONLY})


UserReadDTO = dto.FromMapped[Annotated[User, "read"]]
UserWriteDTO = dto.FromMapped[Annotated[User, "write"]]
