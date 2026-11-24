from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import ForeignKey, Index, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models._user import User


class UserOAuthAccount(UUIDv7AuditBase):
    """Linked external OAuth provider account with AES-GCM protected token envelope."""

    __tablename__ = "user_account_oauth"
    __table_args__ = (
        UniqueConstraint("oauth_name", "account_id", name="uq_user_account_oauth_provider_account"),
        Index("ix_oauth_user_provider", "user_id", "oauth_name"),
        {"comment": "Registered OAuth2 accounts for users"},
    )
    __pii_columns__ = {"oauth_name", "account_email", "account_id"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        nullable=False,
    )
    oauth_name: Mapped[str] = mapped_column(String(length=100), index=True, nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(length=500), nullable=True, default=None)
    account_id: Mapped[str] = mapped_column(String(length=320), index=True, nullable=False)
    account_email: Mapped[str] = mapped_column(String(length=320), nullable=False)
    protected_tokens: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, default=None)
    key_version: Mapped[str | None] = mapped_column(String(length=64), nullable=True, default=None)
    token_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True, default=None)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)
    provider_user_data: Mapped[dict[str, Any] | None] = mapped_column(JsonB, nullable=True, default=None)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(timezone=True), nullable=True, default=None)

    user_name: AssociationProxy[str] = association_proxy("user", "name")
    user_email: AssociationProxy[str] = association_proxy("user", "email")
    user: Mapped[User] = relationship(back_populates="oauth_accounts", viewonly=True, innerjoin=True, lazy="joined")
