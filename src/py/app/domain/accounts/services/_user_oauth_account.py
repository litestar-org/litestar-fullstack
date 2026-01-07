from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID

    from httpx_oauth.oauth2 import OAuth2Token


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[m.UserOAuthAccount]):
    """Handles database operations for user OAuth external authorization."""

    class Repo(SQLAlchemyAsyncRepository[m.UserOAuthAccount]):
        """User SQLAlchemy Repository."""

        model_type = m.UserOAuthAccount

    repository_type = Repo

    async def can_unlink_oauth(self, user: m.User) -> tuple[bool, str]:
        """Check if user can safely unlink an OAuth provider.

        Args:
            user: The user attempting to unlink.

        Returns:
            Tuple of (can_unlink, reason_if_not).
        """
        if user.hashed_password is not None:
            return True, ""

        oauth_count = await self.count(user_id=user.id)
        if oauth_count <= 1:
            return False, "Cannot unlink your only login method. Please set a password first."
        return True, ""

    async def create_or_update_oauth_account(
        self,
        user_id: UUID,
        provider: str,
        oauth_data: dict[str, Any],
        token_data: OAuth2Token,
    ) -> m.UserOAuthAccount:
        """Create or update OAuth account with token data."""
        account_id = oauth_data.get("id", oauth_data.get("sub", ""))
        account_email = oauth_data.get("email", "")
        return await self.link_or_update_oauth(
            user_id=user_id,
            provider=provider,
            account_id=account_id,
            account_email=account_email,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=token_data.get("expires_at"),
            scopes=token_data.get("scope"),
            provider_user_data=oauth_data,
            last_login_at=datetime.now(UTC),
        )

    async def link_or_update_oauth(
        self,
        user_id: UUID,
        provider: str,
        account_id: str,
        account_email: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: int | None = None,
        scopes: list[str] | str | None = None,
        provider_user_data: dict[str, Any] | None = None,
        last_login_at: datetime | None = None,
    ) -> m.UserOAuthAccount:
        """Link a new OAuth account or update existing one."""
        scope_value = " ".join(scopes) if isinstance(scopes, list) else scopes
        token_expires_at = datetime.fromtimestamp(expires_at, tz=UTC) if expires_at else None
        account_data: dict[str, Any] = {
            "user_id": user_id,
            "oauth_name": provider,
            "account_id": account_id,
            "account_email": account_email,
            "access_token": access_token,
        }
        if refresh_token is not None:
            account_data["refresh_token"] = refresh_token
        if expires_at is not None:
            account_data["expires_at"] = expires_at
            account_data["token_expires_at"] = token_expires_at
        if scope_value is not None:
            account_data["scope"] = scope_value
        if provider_user_data is not None:
            account_data["provider_user_data"] = provider_user_data
        if last_login_at is not None:
            account_data["last_login_at"] = last_login_at
        existing = await self.get_one_or_none(user_id=user_id, oauth_name=provider)
        if existing:
            return await self.update(item_id=existing.id, data=account_data, auto_commit=True)
        return await self.create(data=account_data, auto_commit=True)

    async def unlink_oauth_account(
        self,
        user_id: UUID,
        provider: str,
    ) -> bool:
        """Unlink OAuth account from user."""
        oauth_account = await self.get_one_or_none(
            user_id=user_id,
            oauth_name=provider,
        )

        if oauth_account:
            await self.delete(item_id=oauth_account.id, auto_commit=True)
            return True

        return False

    async def get_by_provider_account_id(
        self,
        provider: str,
        account_id: str,
    ) -> m.UserOAuthAccount | None:
        """Get an OAuth account by provider and account ID."""
        return await self.get_one_or_none(oauth_name=provider, account_id=account_id)
