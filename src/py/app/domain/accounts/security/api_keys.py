"""SQLAlchemy digest-only API key store, identity resolver, and ``APIKeyService`` factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from anyio import Lock
from litestar_security.authentication import InvalidCredentials, VerificationUnavailable
from litestar_security.context import CredentialRestrictions, Principal, ResourcePermission
from litestar_security.providers.api_key import (
    APIKeyClaims,
    APIKeyCodec,
    APIKeyConfig,
    APIKeyService,
    APIKeyState,
)
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload

from app.db import models as m

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

logger = structlog.get_logger(__name__)

__all__ = (
    "APIKeyIdentityResolver",
    "SQLAlchemyAPIKeyStore",
    "build_api_key_service",
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_uuid(raw: str) -> UUID | None:
    try:
        return UUID(raw)
    except ValueError:
        return None


def _serialize_restrictions(restrictions: CredentialRestrictions) -> dict[str, Any]:
    return {
        "scopes": sorted(restrictions.scopes) if restrictions.scopes is not None else None,
        "roles": sorted(restrictions.roles) if restrictions.roles is not None else None,
        "capabilities": sorted(restrictions.capabilities) if restrictions.capabilities is not None else None,
        "tenant_ids": sorted(restrictions.tenant_ids) if restrictions.tenant_ids is not None else None,
        "resources": (
            [
                {
                    "resource": perm.resource,
                    "scopes": sorted(perm.scopes),
                }
                for perm in restrictions.resources
            ]
            if restrictions.resources is not None
            else None
        ),
    }


def _deserialize_restrictions(raw: dict[str, Any] | None) -> CredentialRestrictions:
    if not raw:
        return CredentialRestrictions()
    raw_resources = raw.get("resources")
    resources = (
        frozenset(
            ResourcePermission(
                resource=item["resource"],
                scopes=frozenset(item.get("scopes") or ()),
            )
            for item in raw_resources
        )
        if raw_resources is not None
        else None
    )
    return CredentialRestrictions(
        scopes=frozenset(raw["scopes"]) if raw.get("scopes") is not None else None,
        roles=frozenset(raw["roles"]) if raw.get("roles") is not None else None,
        capabilities=frozenset(raw["capabilities"]) if raw.get("capabilities") is not None else None,
        tenant_ids=frozenset(raw["tenant_ids"]) if raw.get("tenant_ids") is not None else None,
        resources=resources,
    )


def _row_to_state(row: m.APIKey) -> APIKeyState:
    return APIKeyState(
        key_id=row.key_id,
        subject_id=str(row.user_id),
        digest=bytes.fromhex(row.key_hash),
        restrictions=_deserialize_restrictions(row.restrictions),
        expires_at=_ensure_utc(row.expires_at) if row.expires_at is not None else None,
        revoked_at=_ensure_utc(row.revoked_at) if row.revoked_at is not None else None,
        overlap_until=_ensure_utc(row.overlap_until) if row.overlap_until is not None else None,
    )


class SQLAlchemyAPIKeyStore:
    """SQLAlchemy ``APIKeyStore`` storing only peppered digests, prefixes, and rotation lineage."""

    __slots__ = ("_alchemy_config", "_lock")

    def __init__(self, alchemy_config: SQLAlchemyAsyncConfig) -> None:
        """Initialize the API key store."""
        self._alchemy_config = alchemy_config
        self._lock = Lock()

    async def get(self, key_id: str) -> APIKeyState | None:
        """Load one API key state record by opaque ``key_id``."""
        async with self._alchemy_config.get_session() as session:
            row = await session.scalar(select(m.APIKey).where(m.APIKey.key_id == key_id))
            return _row_to_state(row) if row is not None else None

    async def create(
        self,
        record: APIKeyState,
        *,
        name: str = "API Key",
        key_prefix: str | None = None,
    ) -> None:
        """Persist a new digest-only API key record."""
        uid = _parse_uuid(record.subject_id)
        if uid is None:
            msg = "API key subject_id must be a valid UUID"
            raise ValueError(msg)
        row = m.APIKey(
            key_id=record.key_id,
            user_id=uid,
            name=name,
            key_prefix=key_prefix or record.key_id[:8],
            key_hash=record.digest.hex(),
            scopes=sorted(record.restrictions.scopes) if record.restrictions.scopes is not None else [],
            restrictions=_serialize_restrictions(record.restrictions),
            expires_at=_ensure_utc(record.expires_at) if record.expires_at is not None else None,
            revoked_at=_ensure_utc(record.revoked_at) if record.revoked_at is not None else None,
            overlap_until=_ensure_utc(record.overlap_until) if record.overlap_until is not None else None,
        )
        async with self._lock, self._alchemy_config.get_session() as session:
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                msg = "API-key ID already exists"
                raise ValueError(msg) from exc

    async def rotate(
        self,
        *,
        current_key_id: str,
        replacement: APIKeyState,
        overlap_until: datetime | None,
        now: datetime,
    ) -> None:
        """Atomically mark the current key rotated with bounded overlap and persist its successor."""
        now_utc = _ensure_utc(now)
        uid = _parse_uuid(replacement.subject_id)
        if uid is None:
            msg = "Replacement API key subject_id must be a valid UUID"
            raise ValueError(msg)
        async with self._lock, self._alchemy_config.get_session() as session:
            current = await session.scalar(select(m.APIKey).where(m.APIKey.key_id == current_key_id))
            if current is None or current.revoked_at is not None:
                msg = "API-key rotation conflict"
                raise ValueError(msg)
            current_expires = _ensure_utc(current.expires_at) if current.expires_at is not None else None
            bounded_overlap = (
                min(_ensure_utc(overlap_until), current_expires)
                if overlap_until is not None and current_expires is not None
                else (_ensure_utc(overlap_until) if overlap_until is not None else None)
            )
            if bounded_overlap is not None and bounded_overlap < now_utc:
                bounded_overlap = None
            result = await session.execute(
                update(m.APIKey)
                .where(m.APIKey.id == current.id, m.APIKey.revoked_at.is_(None))
                .values(revoked_at=now_utc, overlap_until=bounded_overlap)
            )
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                await session.rollback()
                msg = "API-key rotation conflict"
                raise ValueError(msg)
            successor = m.APIKey(
                key_id=replacement.key_id,
                user_id=uid,
                name=current.name,
                key_prefix=replacement.key_id[:8],
                key_hash=replacement.digest.hex(),
                scopes=sorted(replacement.restrictions.scopes) if replacement.restrictions.scopes is not None else [],
                restrictions=_serialize_restrictions(replacement.restrictions),
                rotated_from_id=current.id,
                expires_at=_ensure_utc(replacement.expires_at) if replacement.expires_at is not None else None,
                revoked_at=_ensure_utc(replacement.revoked_at) if replacement.revoked_at is not None else None,
                overlap_until=_ensure_utc(replacement.overlap_until) if replacement.overlap_until is not None else None,
            )
            session.add(successor)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                msg = "API-key rotation conflict"
                raise ValueError(msg) from exc

    async def revoke(self, *, key_id: str, now: datetime) -> None:
        """Immediately revoke an existing API key and clear any grace overlap window."""
        now_utc = _ensure_utc(now)
        async with self._lock, self._alchemy_config.get_session() as session:
            result = await session.execute(
                update(m.APIKey).where(m.APIKey.key_id == key_id).values(revoked_at=now_utc, overlap_until=None)
            )
            await session.commit()
            if int(getattr(result, "rowcount", 0) or 0) != 1:
                msg = "API-key does not exist"
                raise ValueError(msg)

    async def list_for_user(self, user_id: UUID) -> list[m.APIKey]:
        """List all API key metadata rows owned by a user ordered newest first."""
        async with self._alchemy_config.get_session() as session:
            rows = (
                await session.scalars(
                    select(m.APIKey).where(m.APIKey.user_id == user_id).order_by(m.APIKey.created_at.desc())
                )
            ).all()
            return list(rows)

    async def get_for_user(self, user_id: UUID, key_id: str) -> m.APIKey | None:
        """Fetch one API key metadata row owned by ``user_id``."""
        async with self._alchemy_config.get_session() as session:
            return await session.scalar(select(m.APIKey).where(m.APIKey.user_id == user_id, m.APIKey.key_id == key_id))

    async def update_metadata(
        self,
        key_id: str,
        *,
        name: str,
        key_prefix: str,
    ) -> m.APIKey | None:
        """Update human-readable name and display prefix on an existing key."""
        async with self._lock, self._alchemy_config.get_session() as session:
            row = await session.scalar(select(m.APIKey).where(m.APIKey.key_id == key_id))
            if row is None:
                return None
            row.name = name
            row.key_prefix = key_prefix
            await session.commit()
            return row

    async def record(self, *, key_id: str, used_at: datetime) -> None:
        """Persist one coalesced API-key usage timestamp."""
        await self.record_usage({key_id: used_at})

    async def record_usage(self, updates: dict[str, datetime]) -> None:
        """Batch-update ``last_used_at`` timestamps for verified API keys."""
        if not updates:
            return
        async with self._lock, self._alchemy_config.get_session() as session:
            for key_id, used_at in updates.items():
                await session.execute(
                    update(m.APIKey).where(m.APIKey.key_id == key_id).values(last_used_at=_ensure_utc(used_at))
                )
            await session.commit()


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
        """Load the active user for the key's ``subject_id`` or fail closed on storage errors."""
        uid = _parse_uuid(claims.subject_id)
        if uid is None:
            return InvalidCredentials()
        try:
            async with self._alchemy_config.get_session() as session:
                stmt = (
                    select(m.User)
                    .where(m.User.id == uid)
                    .options(
                        selectinload(m.User.roles).options(joinedload(m.UserRole.role, innerjoin=True)),
                        selectinload(m.User.teams).options(joinedload(m.TeamMember.team, innerjoin=True)),
                        selectinload(m.User.mfa_factors),
                    )
                )
                user = await session.scalar(stmt)
        except SQLAlchemyError:
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
    """Construct an ``APIKeyService`` backed by ``SQLAlchemyAPIKeyStore``."""
    return APIKeyService(
        config=APIKeyConfig(store=store, pepper=pepper, prefix=prefix),
        codec=APIKeyCodec(pepper=pepper, prefix=prefix),
        clock=lambda: datetime.now(UTC),
    )
