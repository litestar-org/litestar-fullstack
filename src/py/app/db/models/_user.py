from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import EncryptedString
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.settings import get_settings

if TYPE_CHECKING:
    from app.db.models._email_verification_token import EmailVerificationToken
    from app.db.models._oauth_account import UserOAuthAccount
    from app.db.models._password_reset_token import PasswordResetToken
    from app.db.models._refresh_token import RefreshToken
    from app.db.models._team_member import TeamMember
    from app.db.models._user_role import UserRole


settings = get_settings()


class User(UUIDv7AuditBase):
    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}
    __pii_columns__ = {"name", "email", "username", "phone", "avatar_url", "totp_secret"}

    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    username: Mapped[str | None] = mapped_column(
        String(length=30), unique=True, index=True, nullable=True, default=None
    )
    phone: Mapped[str | None] = mapped_column(String(length=20), nullable=True, default=None)
    hashed_password: Mapped[str | None] = mapped_column(
        String(length=255),
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
    )
    avatar_url: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_at: Mapped[date] = mapped_column(nullable=True, default=None)
    joined_at: Mapped[date] = mapped_column(default=lambda: datetime.now(UTC).date())
    login_count: Mapped[int] = mapped_column(default=0)

    password_reset_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    failed_reset_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    reset_locked_until: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    totp_secret: Mapped[str | None] = mapped_column(
        EncryptedString(key=settings.app.SECRET_KEY),
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
    )
    """Encrypted TOTP secret for authenticator apps."""
    is_two_factor_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    """Whether two-factor authentication is enabled for this user."""
    two_factor_confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    """When MFA was confirmed/enabled."""
    backup_codes: Mapped[list[str | None] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        deferred=True,
        deferred_group="security_sensitive",
    )
    """Hashed backup codes for MFA recovery."""

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
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        uselist=True,
    )

    @hybrid_property
    def has_password(self) -> bool:
        return self.hashed_password is not None

    @hybrid_property
    def has_mfa(self) -> bool:
        return self.is_two_factor_enabled
