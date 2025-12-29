"""Refresh token service with rotation and reuse detection."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from litestar.exceptions import NotAuthorizedException
from litestar.plugins.sqlalchemy import repository, service

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
        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)

        # Use provided family_id or create new one for fresh login
        if family_id is None:
            family_id = uuid4()

        refresh_token = m.RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=m.RefreshToken.create_expires_at(days=expiration_days),
            device_info=device_info,
        )

        created = cast("m.RefreshToken", await self.repository.add(refresh_token))
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
        refresh_token = cast(
            "m.RefreshToken | None",
            await self.repository.get_one_or_none(token_hash=token_hash),
        )

        if refresh_token is None:
            raise NotAuthorizedException(detail="Invalid refresh token")

        if refresh_token.is_expired:
            raise NotAuthorizedException(detail="Refresh token has expired")

        if refresh_token.is_revoked:
            # SECURITY: Token reuse detected - revoke entire family
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

        Raises:
            NotAuthorizedException: If token is invalid, expired, or revoked
        """
        # Validate the current token
        old_token = await self.validate_refresh_token(raw_token)

        # Revoke the old token
        old_token.revoked_at = datetime.now(UTC)
        await self.repository.update(old_token)

        # Create a new token in the same family
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
        tokens = await self.repository.list(
            m.RefreshToken.family_id == family_id,
            m.RefreshToken.revoked_at.is_(None),
        )

        if not tokens:
            return 0

        current_time = datetime.now(UTC)
        for token in tokens:
            token.revoked_at = current_time

        await self.repository.update_many(tokens)
        return len(tokens)

    async def revoke_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user.

        Used for password changes, security events, or explicit logout from all devices.

        Args:
            user_id: The user's UUID

        Returns:
            Number of tokens revoked
        """
        tokens = await self.repository.list(
            m.RefreshToken.user_id == user_id,
            m.RefreshToken.revoked_at.is_(None),
        )

        if not tokens:
            return 0

        current_time = datetime.now(UTC)
        for token in tokens:
            token.revoked_at = current_time

        await self.repository.update_many(tokens)
        return len(tokens)

    async def get_active_sessions(self, user_id: UUID) -> list[m.RefreshToken]:
        """Get all active refresh tokens for a user.

        Useful for showing active sessions in account settings.

        Args:
            user_id: The user's UUID

        Returns:
            List of active RefreshToken instances
        """
        results = await self.repository.list(
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

        # Get expired tokens and tokens revoked more than 24 hours ago
        expired_tokens = await self.repository.list(
            (m.RefreshToken.expires_at < current_time)
            | ((m.RefreshToken.revoked_at.is_not(None)) & (m.RefreshToken.revoked_at < current_time))
        )

        if not expired_tokens:
            return 0

        await self.repository.delete_many(expired_tokens)
        return len(expired_tokens)
