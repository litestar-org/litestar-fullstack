from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.email_verification_token import EmailVerificationToken
    from app.db.models.oauth_account import UserOAuthAccount
    from app.db.models.password_reset_token import PasswordResetToken
    from app.db.models.team_member import TeamMember
    from app.db.models.user_role import UserRole


class User(UUIDAuditBase):
    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}
    __pii_columns__ = {"name", "email", "username", "phone", "avatar_url"}

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    username: Mapped[str | None] = mapped_column(
        String(length=30), unique=True, index=True, nullable=True, default=None
    )
    phone: Mapped[str | None] = mapped_column(String(length=20), nullable=True, default=None)
    hashed_password: Mapped[str | None] = mapped_column(String(length=255), nullable=True, default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_at: Mapped[date] = mapped_column(nullable=True, default=None)
    joined_at: Mapped[date] = mapped_column(default=datetime.now)
    login_count: Mapped[int] = mapped_column(default=0)

    # Password reset security fields
    password_reset_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    failed_reset_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    reset_locked_until: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    # -----------
    # ORM Relationships
    # ------------

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        lazy="selectin",
        uselist=True,
        cascade="all, delete",
    )
    teams: Mapped[list[TeamMember]] = relationship(
        back_populates="user",
        lazy="selectin",
        uselist=True,
        cascade="all, delete",
        viewonly=True,
    )
    oauth_accounts: Mapped[list[UserOAuthAccount]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete",
        uselist=True,
    )
    verification_tokens: Mapped[list[EmailVerificationToken]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete",
        uselist=True,
    )
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete",
        uselist=True,
    )

    @hybrid_property
    def has_password(self) -> bool:
        return self.hashed_password is not None
