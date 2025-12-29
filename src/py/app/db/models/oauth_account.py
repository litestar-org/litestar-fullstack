from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import EncryptedText
from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.lib.settings import get_settings
if TYPE_CHECKING:
    from app.db.models.user import User


settings = get_settings()


class UserOAuthAccount(UUIDv7AuditBase):
    """User Oauth Account"""

    __tablename__ = "user_account_oauth"
    __table_args__ = (
        Index("ix_oauth_provider_oauth_id", "oauth_name", "account_id"),
        Index("ix_oauth_user_provider", "user_id", "oauth_name"),
        {"comment": "Registered OAUTH2 Accounts for Users"},
    )
    __pii_columns__ = {"oauth_name", "account_email", "account_id", "access_token", "refresh_token"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="cascade"),
        nullable=False,
    )
    oauth_name: Mapped[str] = mapped_column(String(length=100), index=True, nullable=False)
    access_token: Mapped[str] = mapped_column(EncryptedText(key=settings.app.SECRET_KEY), nullable=False)
    expires_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(EncryptedText(key=settings.app.SECRET_KEY), nullable=True)
    account_id: Mapped[str] = mapped_column(String(length=320), index=True, nullable=False)
    account_email: Mapped[str] = mapped_column(String(length=320), nullable=False)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_user_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # -----------
    # ORM Relationships
    # ------------
    user_name: AssociationProxy[str] = association_proxy("user", "name")
    user_email: AssociationProxy[str] = association_proxy("user", "email")
    user: Mapped[User] = relationship(
        back_populates="oauth_accounts",
        viewonly=True,
        innerjoin=True,
        lazy="joined",
    )
