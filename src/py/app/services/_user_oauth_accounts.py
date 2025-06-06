from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import select

from app.db import models as m

if TYPE_CHECKING:
    from httpx_oauth.oauth2 import OAuth2Token


class UserOAuthAccountService(SQLAlchemyAsyncRepositoryService[m.UserOauthAccount]):
    """Handles database operations for user OAuth external authorization."""

    class Repo(SQLAlchemyAsyncRepository[m.UserOauthAccount]):
        """User SQLAlchemy Repository."""

        model_type = m.UserOauthAccount

    repository_type = Repo

    async def create_or_update_oauth_account(
        self,
        user_id: UUID,
        provider: str,
        oauth_data: dict[str, Any],
        token_data: OAuth2Token,
    ) -> m.UserOauthAccount:
        """Create or update OAuth account with token data."""
        # Check if OAuth account already exists
        existing = await self.get_one_or_none(
            user_id=user_id,
            oauth_name=provider,
        )

        account_data = {
            "user_id": user_id,
            "oauth_name": provider,
            "account_id": oauth_data.get("id", oauth_data.get("sub", "")),
            "account_email": oauth_data.get("email", ""),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": token_data.get("expires_at"),
            "token_expires_at": (
                datetime.fromtimestamp(token_data["expires_at"], tz=UTC) if token_data.get("expires_at") else None
            ),
            "scope": token_data.get("scope"),
            "provider_user_data": oauth_data,
            "last_login_at": datetime.now(UTC),
        }

        if existing:
            # Update existing account
            return await self.update(item_id=existing.id, data=account_data)

        # Create new account
        return await self.create(data=account_data)

    async def find_user_by_oauth_account(
        self,
        provider: str,
        oauth_id: str,
    ) -> m.User | None:
        """Find user by OAuth provider and ID."""
        statement = (
            select(m.User)
            .join(m.UserOauthAccount)
            .where(
                m.UserOauthAccount.oauth_name == provider,
                m.UserOauthAccount.account_id == oauth_id,
            )
        )
        result = await self.repository.session.execute(statement)
        return result.scalar_one_or_none()

    async def link_oauth_account(
        self,
        user_id: UUID,
        provider: str,
        oauth_data: dict[str, Any],
        token_data: OAuth2Token,
    ) -> m.UserOauthAccount:
        """Link OAuth account to existing user."""
        # Check if OAuth account is already linked to another user
        existing_user = await self.find_user_by_oauth_account(
            provider=provider,
            oauth_id=oauth_data.get("id", oauth_data.get("sub", "")),
        )

        if existing_user and existing_user.id != user_id:
            msg = "This OAuth account is already linked to another user"
            raise ValueError(msg)

        return await self.create_or_update_oauth_account(
            user_id=user_id,
            provider=provider,
            oauth_data=oauth_data,
            token_data=token_data,
        )

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
            await self.delete(item_id=oauth_account.id)
            return True

        return False

    async def get_user_oauth_accounts(self, user_id: UUID) -> list[m.UserOauthAccount]:
        """Get all OAuth accounts for a user."""
        result = await self.list(user_id=user_id)
        return list(result)
