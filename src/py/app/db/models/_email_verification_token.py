from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String, case, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._user import User


class EmailVerificationToken(UUIDv7AuditBase):
    """Email verification tokens for user account verification."""

    __tablename__ = "email_verification_token"
    __table_args__ = {"comment": "Email verification tokens for user account verification"}

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    user: Mapped[User] = relationship(lazy="selectin", back_populates="verification_tokens")

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(UTC) > self.expires_at

    @is_expired.expression
    def is_expired(cls) -> object:
        return case((cls.expires_at <= func.now(), True), else_=False)

    @hybrid_property
    def is_used(self) -> bool:
        """Check if the token has been used."""
        return self.used_at is not None

    @is_used.expression
    def is_used(cls) -> object:
        return case((cls.used_at.isnot(None), True), else_=False)

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    @is_valid.expression
    def is_valid(cls) -> object:
        return case(
            ((cls.expires_at > func.now()) & cls.used_at.is_(None), True),
            else_=False,
        )

    @classmethod
    def create_expires_at(cls, hours: int = 24) -> datetime:
        """Create an expiration datetime for the token.

        Returns:
            datetime: The expiration datetime set to the current time plus the specified hours.
        """
        return datetime.now(UTC) + timedelta(hours=hours)
