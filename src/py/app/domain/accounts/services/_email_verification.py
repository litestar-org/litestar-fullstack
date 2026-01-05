from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from litestar.exceptions import ClientException
from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID


class EmailVerificationTokenService(service.SQLAlchemyAsyncRepositoryService[m.EmailVerificationToken]):
    """Handles database operations for email verification tokens."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.EmailVerificationToken]):
        """EmailVerificationToken SQLAlchemy Repository."""

        model_type = m.EmailVerificationToken

    repository_type = Repo
    match_fields = ["token_hash"]

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def to_model_on_create(
        self,
        data: service.ModelDictT[m.EmailVerificationToken],
    ) -> service.ModelDictT[m.EmailVerificationToken]:
        data = service.schema_dump(data)
        if service.is_dict_with_field(data, "token") and service.is_dict_without_field(data, "token_hash"):
            data["token_hash"] = self._hash_token(data.pop("token"))
        return data

    async def create_verification_token(
        self,
        user_id: UUID,
        email: str,
    ) -> tuple[m.EmailVerificationToken, str]:
        """Create a new email verification token for a user.

        Args:
            user_id: The user's UUID
            email: The email address to verify

        Returns:
            Tuple of (EmailVerificationToken, plain_token)
        """

        await self.invalidate_user_tokens(user_id, email)

        token = secrets.token_urlsafe(32)

        verification_token = {
            "user_id": user_id,
            "token": token,
            "email": email,
            "expires_at": m.EmailVerificationToken.create_expires_at(hours=24),
        }

        obj = await self.create(verification_token)
        return obj, token

    async def verify_token(self, token: str) -> m.EmailVerificationToken:
        """Verify a token and mark it as used.

        Args:
            token: The verification token string

        Returns:
            The EmailVerificationToken instance if valid

        Raises:
            ClientException: If token is invalid, expired, or already used
        """
        verification_token = await self.get_one_or_none(token_hash=self._hash_token(token))

        if verification_token is None:
            raise ClientException(detail="Invalid verification token", status_code=400)

        if verification_token.is_expired:
            raise ClientException(detail="Verification token has expired", status_code=400)

        if verification_token.is_used:
            raise ClientException(detail="Verification token has already been used", status_code=400)

        verification_token.used_at = datetime.now(UTC)
        return await self.update(verification_token)

    async def invalidate_user_tokens(self, user_id: UUID, email: str | None = None) -> None:
        """Invalidate all tokens for a user, optionally filtered by email.

        Args:
            user_id: The user's UUID
            email: Optional email to filter tokens
        """
        filters = [m.EmailVerificationToken.user_id == user_id]
        if email:
            filters.append(m.EmailVerificationToken.email == email)

        tokens = await self.list(*filters)

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
        expired_tokens = await self.list(m.EmailVerificationToken.expires_at < current_time)

        if expired_tokens:
            # Pass IDs explicitly to delete_many, not model objects
            token_ids = [token.id for token in expired_tokens]
            await self.delete_many(token_ids)

        return len(expired_tokens)
