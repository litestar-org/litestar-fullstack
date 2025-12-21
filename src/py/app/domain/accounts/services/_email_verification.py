from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from litestar.exceptions import ClientException
from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID


class EmailVerificationTokenService(service.SQLAlchemyAsyncRepositoryService[m.EmailVerificationToken]):
    """Handles database operations for email verification tokens."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.EmailVerificationToken]):
        """EmailVerificationToken SQLAlchemy Repository."""

        model_type = m.EmailVerificationToken

    repository_type = Repo
    match_fields = ["token"]

    async def create_verification_token(self, user_id: UUID, email: str) -> m.EmailVerificationToken:
        """Create a new email verification token for a user.

        Args:
            user_id: The user's UUID
            email: The email address to verify

        Returns:
            The created EmailVerificationToken instance
        """
        # Invalidate any existing tokens for this user/email combination
        await self.invalidate_user_tokens(user_id, email)

        # Generate a secure random token
        token = secrets.token_urlsafe(32)

        # Create token with 24-hour expiration
        verification_token = m.EmailVerificationToken(
            user_id=user_id, token=token, email=email, expires_at=m.EmailVerificationToken.create_expires_at(hours=24)
        )

        obj = await self.create(verification_token)
        return self.to_schema(obj)

    async def verify_token(self, token: str) -> m.EmailVerificationToken:
        """Verify a token and mark it as used.

        Args:
            token: The verification token string

        Returns:
            The EmailVerificationToken instance if valid

        Raises:
            ClientException: If token is invalid, expired, or already used
        """
        verification_token = await self.repository.get_one_or_none(token=token)

        if verification_token is None:
            raise ClientException(detail="Invalid verification token", status_code=400)

        if verification_token.is_expired:
            raise ClientException(detail="Verification token has expired", status_code=400)

        if verification_token.is_used:
            raise ClientException(detail="Verification token has already been used", status_code=400)

        # Mark token as used
        verification_token.used_at = datetime.now(UTC)
        obj = await self.update(verification_token)

        return self.to_schema(obj)

    async def invalidate_user_tokens(self, user_id: UUID, email: str | None = None) -> None:
        """Invalidate all tokens for a user, optionally filtered by email.

        Args:
            user_id: The user's UUID
            email: Optional email to filter tokens
        """
        filters = [m.EmailVerificationToken.user_id == user_id]
        if email:
            filters.append(m.EmailVerificationToken.email == email)

        # Find all active tokens
        tokens = await self.repository.list(*filters)

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
        expired_tokens = await self.repository.list(m.EmailVerificationToken.expires_at < current_time)

        if expired_tokens:
            await self.repository.delete_many(expired_tokens)

        return len(expired_tokens)
