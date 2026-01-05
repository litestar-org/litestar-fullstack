from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from litestar.exceptions import ClientException
from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID


class PasswordResetService(service.SQLAlchemyAsyncRepositoryService[m.PasswordResetToken]):
    """Handles database operations for password reset tokens."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.PasswordResetToken]):
        """PasswordResetToken SQLAlchemy Repository."""

        model_type = m.PasswordResetToken

    repository_type = Repo
    match_fields = ["token_hash"]

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def to_model_on_create(
        self,
        data: service.ModelDictT[m.PasswordResetToken],
    ) -> service.ModelDictT[m.PasswordResetToken]:
        data = service.schema_dump(data)
        if service.is_dict_with_field(data, "token") and service.is_dict_without_field(data, "token_hash"):
            data["token_hash"] = self._hash_token(data.pop("token"))
        return data

    async def create_reset_token(
        self, user_id: UUID, ip_address: str | None = None, user_agent: str | None = None
    ) -> tuple[m.PasswordResetToken, str]:
        """Create a new password reset token for a user.

        Args:
            user_id: The user's UUID
            ip_address: IP address of the request
            user_agent: User agent string of the request

        Returns:
            Tuple of (PasswordResetToken, plain_token)
        """
        await self.invalidate_user_tokens(user_id)

        token = secrets.token_urlsafe(32)

        created = await self.create(
            {
                "user_id": user_id,
                "token": token,
                "expires_at": m.PasswordResetToken.create_expires_at(hours=1),
                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )
        return created, token

    async def validate_reset_token(self, token: str) -> m.PasswordResetToken:
        """Validate a token without consuming it.

        Args:
            token: The reset token string

        Returns:
            The PasswordResetToken instance if valid.

        Raises:
            ClientException: If token is invalid, expired, or already used
        """
        reset_token = await self.get_one_or_none(token_hash=self._hash_token(token))

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
        """
        reset_token = await self.validate_reset_token(token)
        reset_token.used_at = datetime.now(UTC)
        await self.update(reset_token)

        return reset_token

    async def invalidate_user_tokens(self, user_id: UUID) -> None:
        """Invalidate all active tokens for a user.

        Args:
            user_id: The user's UUID
        """

        tokens = await self.list(m.PasswordResetToken.user_id == user_id, m.PasswordResetToken.used_at.is_(None))

        current_time = datetime.now(UTC)
        for token in tokens:
            if not token.is_used:
                token.used_at = current_time

        if tokens:
            await self.update_many(tokens)

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from the database.

        Returns:
            Number of tokens removed
        """
        current_time = datetime.now(UTC)
        expired_tokens = await self.list(m.PasswordResetToken.expires_at < current_time)

        if not expired_tokens:
            return 0

        # Pass IDs explicitly to delete_many, not model objects
        token_ids = [token.id for token in expired_tokens]
        await self.delete_many(token_ids)
        return len(expired_tokens)

    async def check_rate_limit(self, user_id: UUID, hours: float = 1) -> bool:
        """Check if user has exceeded reset token creation rate limit.

        Args:
            user_id: The user's UUID
            hours: Hours to look back for rate limiting

        Returns:
            True if rate limit exceeded, False otherwise
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        recent_tokens = await self.list(
            m.PasswordResetToken.user_id == user_id, m.PasswordResetToken.created_at >= cutoff_time
        )

        max_reset_requests_per_hour = 3
        return len(recent_tokens) >= max_reset_requests_per_hour
