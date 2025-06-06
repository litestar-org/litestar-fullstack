from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from litestar.exceptions import ClientException
from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID


class PasswordResetService(service.SQLAlchemyAsyncRepositoryService[m.PasswordResetToken]):
    """Handles database operations for password reset tokens."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.PasswordResetToken]):
        """PasswordResetToken SQLAlchemy Repository."""

        model_type = m.PasswordResetToken

    repository_type = Repo
    match_fields = ["token"]

    async def create_reset_token(
        self,
        user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> m.PasswordResetToken:
        """Create a new password reset token for a user.

        Args:
            user_id: The user's UUID
            ip_address: IP address of the request
            user_agent: User agent string of the request

        Returns:
            The created PasswordResetToken instance
        """
        # Invalidate any existing tokens for this user
        await self.invalidate_user_tokens(user_id)

        # Generate a secure random token
        token = secrets.token_urlsafe(32)

        # Create token with 1-hour expiration for security
        reset_token = m.PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=m.PasswordResetToken.create_expires_at(hours=1),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return await self.repository.add(reset_token)

    async def validate_reset_token(self, token: str) -> m.PasswordResetToken | None:
        """Validate a token without consuming it.

        Args:
            token: The reset token string

        Returns:
            The PasswordResetToken instance if valid, None otherwise

        Raises:
            ClientException: If token is invalid, expired, or already used
        """
        reset_token = await self.repository.get_one_or_none(token=token)

        if reset_token is None:
            raise ClientException(detail="Invalid reset token", status_code=400)

        if reset_token.is_expired:
            raise ClientException(detail="Reset token has expired", status_code=400)

        if reset_token.is_used:
            raise ClientException(detail="Reset token has already been used", status_code=400)

        return reset_token

    async def use_reset_token(self, token: str) -> m.PasswordResetToken:
        """Use a token to mark it as consumed.

        Args:
            token: The reset token string

        Returns:
            The PasswordResetToken instance

        Raises:
            ClientException: If token is invalid, expired, or already used
        """
        reset_token = await self.validate_reset_token(token)

        if reset_token is None:
            raise ClientException(detail="Invalid reset token", status_code=400)

        # Mark token as used
        reset_token.used_at = datetime.now(UTC)
        await self.repository.update(reset_token)

        return reset_token

    async def invalidate_user_tokens(self, user_id: UUID) -> None:
        """Invalidate all active tokens for a user.

        Args:
            user_id: The user's UUID
        """
        # Find all active tokens for this user
        tokens = await self.repository.list(
            m.PasswordResetToken.user_id == user_id,
            m.PasswordResetToken.used_at.is_(None)
        )

        # Mark them as used (invalidated)
        current_time = datetime.now(UTC)
        for token in tokens:
            if not token.is_used:
                token.used_at = current_time

        if tokens:
            await self.repository.update_many(tokens)

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from the database.

        Returns:
            Number of tokens removed
        """
        current_time = datetime.now(UTC)
        expired_tokens = await self.repository.list(
            m.PasswordResetToken.expires_at < current_time
        )

        if not expired_tokens:
            return 0

        await self.repository.delete_many(expired_tokens)
        return len(expired_tokens)

    async def check_rate_limit(self, user_id: UUID, hours: int = 1) -> bool:
        """Check if user has exceeded reset token creation rate limit.

        Args:
            user_id: The user's UUID
            hours: Hours to look back for rate limiting

        Returns:
            True if rate limit exceeded, False otherwise
        """
        cutoff_time = datetime.now(UTC).replace(hour=datetime.now(UTC).hour - hours)

        recent_tokens = await self.repository.list(
            m.PasswordResetToken.user_id == user_id,
            m.PasswordResetToken.created_at >= cutoff_time
        )

        # Allow maximum of 3 reset requests per hour
        return len(recent_tokens) >= 3
