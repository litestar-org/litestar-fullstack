"""Refresh token model for JWT rotation with reuse detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.user import User


class RefreshToken(UUIDv7AuditBase):
    """Refresh token storage for JWT rotation with reuse detection.

    Tokens are stored as SHA-256 hashes, never plaintext.
    Each token belongs to a 'family' for reuse detection - if a revoked
    token is presented, the entire family is revoked for security.
    """

    __tablename__ = "refresh_token"
    __table_args__ = {"comment": "JWT refresh tokens with rotation tracking"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hex digest is 64 characters
        nullable=False,
        unique=True,
        index=True,
    )
    family_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    """Token family for reuse detection - all tokens from same login share this ID."""

    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    """Optional device fingerprint (user agent, etc.)"""

    # ORM Relationships
    user: Mapped[User] = relationship(lazy="selectin", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if the token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

    @classmethod
    def create_expires_at(cls, days: int = 7) -> datetime:
        """Create an expiration datetime for the token.

        Args:
            days: Number of days until expiration (default: 7 days)

        Returns:
            Expiration datetime
        """
        return datetime.now(UTC) + timedelta(days=days)
