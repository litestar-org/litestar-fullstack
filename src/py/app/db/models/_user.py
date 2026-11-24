from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import Bool, DateTimeUTC
from sqlalchemy import Integer, String, inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._oauth_account import UserOAuthAccount
    from app.db.models._security import APIKey, UserMFAFactor, UserPasskey, UserSession
    from app.db.models._team_member import TeamMember
    from app.db.models._user_role import UserRole


class User(UUIDv7AuditBase):
    """Application user account model."""

    __tablename__ = "user_account"
    __table_args__ = {"comment": "User accounts for application access"}
    __pii_columns__ = {"name", "email", "username", "phone", "avatar_url"}

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
    is_active: Mapped[bool] = mapped_column(Bool, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Bool, default=False, nullable=False)
    security_epoch: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    verified_at: Mapped[date | None] = mapped_column(nullable=True, default=None)
    joined_at: Mapped[date] = mapped_column(default=lambda: datetime.now(UTC).date())
    login_count: Mapped[int] = mapped_column(default=0)
    password_reset_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    failed_reset_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    reset_locked_until: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)

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
        cascade="all, delete-orphan",
        uselist=True,
    )
    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        uselist=True,
    )
    mfa_factors: Mapped[list[UserMFAFactor]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        uselist=True,
    )
    passkeys: Mapped[list[UserPasskey]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        uselist=True,
    )
    api_keys: Mapped[list[APIKey]] = relationship(
        back_populates="user",
        lazy="noload",
        cascade="all, delete-orphan",
        uselist=True,
    )

    @hybrid_property
    def has_password(self) -> bool:
        """Return whether the user has a password credential set."""
        return self.hashed_password is not None

    @property
    def has_mfa(self) -> bool:
        """Return whether an eager-loaded confirmed MFA factor exists without triggering lazy I/O."""
        if "mfa_factors" in inspect(self).unloaded:
            return False
        return any(factor.is_confirmed for factor in self.mfa_factors)

    @property
    def is_two_factor_enabled(self) -> bool:
        """Compatibility alias returning whether the user has confirmed MFA enabled."""
        return self.has_mfa
