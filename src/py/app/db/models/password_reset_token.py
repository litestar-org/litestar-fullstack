from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.user import User


class PasswordResetToken(UUIDv7AuditBase):
    """Password reset tokens for secure password recovery."""

    __tablename__ = "password_reset_token"
    __table_args__ = {"comment": "Password reset tokens for secure password recovery"}

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ORM Relationships
    user: Mapped[User] = relationship(lazy="selectin", back_populates="reset_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if the token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    @classmethod
    def create_expires_at(cls, hours: int = 1) -> datetime:
        """Create an expiration datetime for the token.

        Args:
            hours: Number of hours until expiration (default: 1 hour for security)
        """
        return datetime.now(UTC) + timedelta(hours=hours)
