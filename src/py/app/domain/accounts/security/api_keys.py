"""Digest-only API key store, identity resolver, and ``APIKeyService`` factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from advanced_alchemy.exceptions import IntegrityError, RepositoryError
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.context import Principal
from litestar_security.providers.api_key import (
    APIKeyClaims,
    APIKeyCodec,
    APIKeyConfig,
    APIKeyService,
    APIKeyState,
)
from sqlalchemy.exc import SQLAlchemyError

from app.db import models as m
from app.domain.accounts.services import APIKeyRecordService, UserService, is_constraint_violation

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

logger = structlog.get_logger(__name__)

_DUPLICATE_KEY = "API-key ID already exists"
_ROTATION_CONFLICT = "API-key rotation conflict"
_UNKNOWN_KEY = "API-key does not exist"

__all__ = (
    "APIKeyIdentityResolver",
    "SQLAlchemyAPIKeyStore",
    "build_api_key_service",
)


class SQLAlchemyAPIKeyStore:
    """``APIKeyStore`` on Advanced Alchemy services storing only peppered digests, prefixes, and rotation lineage."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the API key store."""
        self._alchemy_config = alchemy_config

    async def get(self, key_id: str) -> APIKeyState | None:
        """Load one API key state record by opaque ``key_id``.

        Returns:
            Matching key state, or ``None`` if not found.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            api_key = await api_keys.get_one_or_none(m.APIKey.key_id == key_id)
            return api_keys.to_state(api_key) if api_key is not None else None

    async def create(self, record: APIKeyState) -> None:
        """Persist a new digest-only API key record.

        Raises:
            ValueError: If ``subject_id`` is not a valid UUID or ``key_id`` already exists.
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            try:
                await api_keys.create(record, auto_commit=True)
            except IntegrityError as error:
                if not is_constraint_violation(error):
                    raise
                raise ValueError(_DUPLICATE_KEY) from error

    async def rotate(
        self,
        *,
        current_key_id: str,
        replacement: APIKeyState,
        overlap_until: datetime | None,
        now: datetime,
    ) -> None:
        """Atomically mark the current key rotated with bounded overlap and persist its successor.

        Raises:
            ValueError: If ``replacement.subject_id`` is invalid or rotation conflicts with current state.
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            try:
                rotated = await api_keys.rotate(current_key_id, replacement, overlap_until=overlap_until, now=now)
                await api_keys.repository.session.commit()
            except IntegrityError as error:
                if not is_constraint_violation(error):
                    raise
                raise ValueError(_ROTATION_CONFLICT) from error
        if not rotated:
            raise ValueError(_ROTATION_CONFLICT)

    async def revoke(self, *, key_id: str, now: datetime) -> None:
        """Immediately revoke an existing API key and clear any grace overlap window.

        Raises:
            ValueError: If no API key matches ``key_id``.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            revoked = await api_keys.revoke(key_id, now=now)
            await api_keys.repository.session.commit()
        if not revoked:
            raise ValueError(_UNKNOWN_KEY)

    async def list_for_user(self, user_id: UUID) -> list[m.APIKey]:
        """List all API keys owned by a user ordered newest first.

        Returns:
            API keys belonging to ``user_id``.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            return list(await api_keys.list(m.APIKey.user_id == user_id, order_by=m.APIKey.created_at.desc()))

    async def get_for_user(self, user_id: UUID, key_id: str) -> m.APIKey | None:
        """Fetch one API key owned by ``user_id``.

        Returns:
            Matching API key, or ``None`` if not found.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            return await api_keys.get_one_or_none(m.APIKey.user_id == user_id, m.APIKey.key_id == key_id)

    async def update_metadata(
        self,
        key_id: str,
        *,
        name: str,
        key_prefix: str,
    ) -> m.APIKey | None:
        """Update human-readable name and display prefix on an existing key.

        Returns:
            Updated API key, or ``None`` if ``key_id`` does not exist.
        """
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            api_key = await api_keys.get_one_or_none(m.APIKey.key_id == key_id)
            if api_key is None:
                return None
            api_key.name = name
            api_key.key_prefix = key_prefix
            return await api_keys.update(api_key, auto_commit=True)

    async def record(self, *, key_id: str, used_at: datetime) -> None:
        """Persist one coalesced API-key usage timestamp."""
        await self.record_usage({key_id: used_at})

    async def record_usage(self, updates: dict[str, datetime]) -> None:
        """Batch-update ``last_used_at`` timestamps for verified API keys."""
        if not updates:
            return
        async with APIKeyRecordService.new(config=self._alchemy_config) as api_keys:
            for key_id, used_at in updates.items():
                await api_keys.record_usage(key_id, used_at=used_at)
            await api_keys.repository.session.commit()


class APIKeyIdentityResolver:
    """Resolves verified ``APIKeyClaims`` to an eager-loaded ``Principal[m.User]``."""

    __slots__ = ("_alchemy_config",)

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the API key identity resolver."""
        self._alchemy_config = alchemy_config

    async def resolve(
        self,
        claims: APIKeyClaims | APIKeyState,
    ) -> Principal[m.User] | InvalidCredentials | VerificationUnavailable:
        """Load the active user for the key's ``subject_id`` or fail closed on storage errors.

        Returns:
            Resolved user principal, ``InvalidCredentials`` if missing/inactive, or ``VerificationUnavailable``.
        """
        user_id = UserService.to_user_id(claims.subject_id)
        if user_id is None:
            return InvalidCredentials()
        try:
            async with UserService.new(config=self._alchemy_config) as users:
                user = await users.find_for_authorization(m.User.id == user_id)
        except (RepositoryError, SQLAlchemyError):
            logger.warning("Database error during API key identity resolution", key_id=claims.key_id)
            return VerificationUnavailable()
        if user is None or not user.is_active:
            return InvalidCredentials()
        return Principal(
            id=str(user.id),
            display_name=user.name or user.email,
            user=user,
        )


def build_api_key_service(
    store: SQLAlchemyAPIKeyStore,
    pepper: bytes,
    *,
    prefix: str = "lsk",
) -> APIKeyService:
    """Construct an ``APIKeyService`` backed by ``SQLAlchemyAPIKeyStore``.

    Returns:
        Configured ``APIKeyService`` instance.
    """
    return APIKeyService(
        config=APIKeyConfig(store=store, pepper=pepper, prefix=prefix),
        codec=APIKeyCodec(pepper=pepper, prefix=prefix),
        clock=lambda: datetime.now(UTC),
    )
