"""Refresh token service with rotation and reuse detection."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import NotAuthorizedException

from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID


class RefreshTokenService(service.SQLAlchemyAsyncRepositoryService[m.RefreshToken]):
    """Handles database operations for refresh tokens with rotation and reuse detection.

    Tokens are stored as SHA-256 hashes, never plaintext.
    Each token belongs to a 'family' for reuse detection - if a revoked
    token is presented, the entire family is revoked for security.
    """

    class Repo(repository.SQLAlchemyAsyncRepository[m.RefreshToken]):
        """RefreshToken SQLAlchemy Repository."""

        model_type = m.RefreshToken

    repository_type = Repo
    match_fields = ["token_hash"]

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token using SHA-256.

        Args:
            token: The raw token string

        Returns:
            SHA-256 hex digest of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_refresh_token(
        self,
        user_id: UUID,
        family_id: UUID | None = None,
        device_info: str | None = None,
        expiration_days: int = 7,
    ) -> tuple[str, m.RefreshToken]:
        """Create a new refresh token for a user.

        Args:
            user_id: The user's UUID
            family_id: Optional family ID for token rotation (creates new if None)
            device_info: Optional device fingerprint (user agent, etc.)
            expiration_days: Number of days until token expires

        Returns:
            Tuple of (raw_token, RefreshToken instance)
            The raw_token should be sent to the client, the model is stored in DB.
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)

        if family_id is None:
            family_id = uuid4()

        created = await self.create(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "family_id": family_id,
                "expires_at": m.RefreshToken.create_expires_at(days=expiration_days),
                "device_info": device_info,
            }
        )
        return raw_token, created

    async def validate_refresh_token(self, raw_token: str) -> m.RefreshToken:
        """Validate a refresh token without consuming it.

        Args:
            raw_token: The raw token string from the client

        Returns:
            The RefreshToken instance if valid.

        Raises:
            NotAuthorizedException: If token is invalid, expired, or revoked
        """
        token_hash = self.hash_token(raw_token)
        refresh_token = await self.get_one_or_none(token_hash=token_hash)

        if refresh_token is None:
            raise NotAuthorizedException(detail="Invalid refresh token")

        if refresh_token.is_expired:
            raise NotAuthorizedException(detail="Refresh token has expired")

        if refresh_token.is_revoked:
            await self.revoke_token_family(refresh_token.family_id)
            raise NotAuthorizedException(detail="Refresh token has been revoked")

        return refresh_token

    async def rotate_refresh_token(
        self,
        raw_token: str,
        device_info: str | None = None,
    ) -> tuple[str, m.RefreshToken]:
        """Rotate a refresh token, creating a new one and revoking the old.

        This implements refresh token rotation with reuse detection.
        If a revoked token is presented, the entire family is revoked.

        Args:
            raw_token: The raw token string from the client
            device_info: Optional device fingerprint

        Returns:
            Tuple of (new_raw_token, new_RefreshToken)
        """
        old_token = await self.validate_refresh_token(raw_token)

        await self.update(
            item_id=old_token.id,
            data={"revoked_at": datetime.now(UTC)},
            auto_commit=True,
        )

        return await self.create_refresh_token(
            user_id=old_token.user_id,
            family_id=old_token.family_id,
            device_info=device_info or old_token.device_info,
        )

    async def revoke_token_family(self, family_id: UUID) -> int:
        """Revoke all tokens in a family.

        Used for logout and security purposes (reuse detection).

        Args:
            family_id: The family ID to revoke

        Returns:
            Number of tokens revoked
        """
        tokens = await self.list(
            m.RefreshToken.family_id == family_id,
            m.RefreshToken.revoked_at.is_(None),
        )

        if not tokens:
            return 0

        current_time = datetime.now(UTC)
        for token in tokens:
            token.revoked_at = current_time

        await self.update_many(tokens)
        return len(tokens)

    async def revoke_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user.

        Used for password changes, security events, or explicit logout from all devices.

        Args:
            user_id: The user's UUID

        Returns:
            Number of tokens revoked
        """
        tokens = await self.list(
            m.RefreshToken.user_id == user_id,
            m.RefreshToken.revoked_at.is_(None),
        )

        if not tokens:
            return 0

        current_time = datetime.now(UTC)
        for token in tokens:
            token.revoked_at = current_time

        await self.update_many(tokens)
        return len(tokens)

    async def get_active_sessions(self, user_id: UUID) -> list[m.RefreshToken]:
        """Get all active refresh tokens for a user.

        Useful for showing active sessions in account settings.

        Args:
            user_id: The user's UUID

        Returns:
            List of active RefreshToken instances
        """
        results = await self.list(
            m.RefreshToken.user_id == user_id,
            m.RefreshToken.revoked_at.is_(None),
            m.RefreshToken.expires_at > datetime.now(UTC),
        )
        return list(results)

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired and old revoked tokens from the database.

        This should be run periodically as a background job.

        Returns:
            Number of tokens removed
        """
        current_time = datetime.now(UTC)

        expired_tokens = await self.list(
            (m.RefreshToken.expires_at < current_time)
            | ((m.RefreshToken.revoked_at.is_not(None)) & (m.RefreshToken.revoked_at < current_time))
        )

        if not expired_tokens:
            return 0

        # delete_many expects a list of IDs, not model instances
        token_ids = [token.id for token in expired_tokens]
        await self.delete_many(token_ids)
        return len(expired_tokens)
