"""Personal API key database service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import service
from litestar_security.context import CredentialRestrictions, ResourcePermission
from litestar_security.providers.api_key import APIKeyState
from sqlalchemy import or_, update

from app.db import models as m
from app.domain.accounts.schemas import APIKeyItem
from app.domain.accounts.services._statements import affected_rows

if TYPE_CHECKING:
    from datetime import datetime

    from advanced_alchemy.service import ModelDictT

_DEFAULT_NAME = "API Key"
_DISPLAY_PREFIX_LENGTH = 8


class APIKeyRecordService(service.SQLAlchemyAsyncRepositoryService[m.APIKey]):
    """Handles database operations for hashed personal API key records."""

    async def to_model_on_create(self, data: ModelDictT[m.APIKey]) -> ModelDictT[m.APIKey]:
        """Translate a digest-only ``APIKeyState`` into the API key it describes before creation.

        Returns:
            API key built from the state, or ``data`` unchanged when it is not an ``APIKeyState``.
        """
        return self._to_api_key(data) if isinstance(data, APIKeyState) else data

    def to_state(self, api_key: m.APIKey) -> APIKeyState:
        """Translate a stored API key into the digest-only state ``litestar-security`` verifies.

        Returns:
            State carrying the key's digest, restrictions, expiry, and revocation window.
        """
        return APIKeyState(
            key_id=api_key.key_id,
            subject_id=str(api_key.user_id),
            digest=bytes.fromhex(api_key.key_hash),
            restrictions=self._to_restrictions(api_key),
            expires_at=api_key.expires_at,
            revoked_at=api_key.revoked_at,
            overlap_until=api_key.overlap_until,
        )

    @staticmethod
    def to_item(api_key: m.APIKey) -> APIKeyItem:
        """Translate a stored API key into the secret-free ``APIKeyItem`` shown to its owner.

        Returns:
            The key's name, display prefix, scopes, and lifecycle timestamps.
        """
        return APIKeyItem(
            id=api_key.key_id,
            name=api_key.name,
            prefix=api_key.key_prefix,
            scopes=list(api_key.scopes or []),
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            revoked_at=api_key.revoked_at,
        )

    async def rotate(
        self,
        key_id: str,
        replacement: APIKeyState,
        *,
        overlap_until: datetime | None,
        now: datetime,
    ) -> bool:
        """Revoke a live key and add the replacement that inherits its name, inside the caller's transaction.

        The revoked key stays usable until ``overlap_until``, capped at its own expiry.

        Returns:
            ``True`` when this call rotated the key, ``False`` when it is missing or was already rotated or revoked.
        """
        api_key = await self.get_one_or_none(m.APIKey.key_id == key_id)
        if api_key is None:
            return False
        statement = (
            update(m.APIKey)
            .where(m.APIKey.id == api_key.id, m.APIKey.revoked_at.is_(None))
            .values(revoked_at=now, overlap_until=self._bound_overlap(overlap_until, api_key.expires_at, now))
        )
        if await affected_rows(self.repository.session, statement) != 1:
            return False
        await self.create(self._to_api_key(replacement, name=api_key.name, rotated_from_id=api_key.id))
        return True

    async def revoke(self, key_id: str, *, now: datetime) -> bool:
        """Stop a key from working at ``now``, ending any rotation overlap it still has.

        A key that already stopped working keeps the time it was revoked and the overlap it was given.

        Returns:
            ``True`` when a key matched ``key_id``, ``False`` when none exists.
        """
        api_key = await self.get_one_or_none(m.APIKey.key_id == key_id)
        if api_key is None:
            return False
        still_working = or_(m.APIKey.revoked_at.is_(None), m.APIKey.overlap_until > now)
        statement = (
            update(m.APIKey).where(m.APIKey.id == api_key.id, still_working).values(revoked_at=now, overlap_until=None)
        )
        await self.repository.session.execute(statement)
        return True

    async def record_usage(self, key_id: str, *, used_at: datetime) -> bool:
        """Stamp the last time a key authenticated a request.

        Returns:
            ``True`` when a key matched ``key_id``, ``False`` when none exists.
        """
        statement = update(m.APIKey).where(m.APIKey.key_id == key_id).values(last_used_at=used_at)
        return await affected_rows(self.repository.session, statement) == 1

    def _to_api_key(
        self,
        state: APIKeyState,
        *,
        name: str = _DEFAULT_NAME,
        rotated_from_id: UUID | None = None,
    ) -> m.APIKey:
        return m.APIKey(
            key_id=state.key_id,
            user_id=UUID(state.subject_id),
            name=name,
            key_prefix=state.key_id[:_DISPLAY_PREFIX_LENGTH],
            key_hash=state.digest.hex(),
            scopes=sorted(state.restrictions.scopes or ()),
            restrictions=self._to_stored_restrictions(state.restrictions),
            rotated_from_id=rotated_from_id,
            expires_at=state.expires_at,
            revoked_at=state.revoked_at,
            overlap_until=state.overlap_until,
        )

    @staticmethod
    def _to_stored_restrictions(restrictions: CredentialRestrictions) -> dict[str, Any]:
        return {
            "scopes": sorted(restrictions.scopes) if restrictions.scopes is not None else None,
            "roles": sorted(restrictions.roles) if restrictions.roles is not None else None,
            "capabilities": sorted(restrictions.capabilities) if restrictions.capabilities is not None else None,
            "tenant_ids": sorted(restrictions.tenant_ids) if restrictions.tenant_ids is not None else None,
            "resources": (
                [
                    {"resource": permission.resource, "scopes": sorted(permission.scopes)}
                    for permission in restrictions.resources
                ]
                if restrictions.resources is not None
                else None
            ),
        }

    @staticmethod
    def _to_restrictions(api_key: m.APIKey) -> CredentialRestrictions:
        stored = api_key.restrictions
        if not stored:
            return CredentialRestrictions()
        permissions = stored.get("resources")
        return CredentialRestrictions(
            scopes=frozenset(stored["scopes"]) if stored.get("scopes") is not None else None,
            roles=frozenset(stored["roles"]) if stored.get("roles") is not None else None,
            capabilities=frozenset(stored["capabilities"]) if stored.get("capabilities") is not None else None,
            tenant_ids=frozenset(stored["tenant_ids"]) if stored.get("tenant_ids") is not None else None,
            resources=(
                frozenset(
                    ResourcePermission(
                        resource=permission["resource"],
                        scopes=frozenset(permission.get("scopes") or ()),
                    )
                    for permission in permissions
                )
                if permissions is not None
                else None
            ),
        )

    @staticmethod
    def _bound_overlap(
        overlap_until: datetime | None,
        key_expires_at: datetime | None,
        now: datetime,
    ) -> datetime | None:
        if overlap_until is None:
            return None
        bounded_overlap = min(overlap_until, key_expires_at) if key_expires_at is not None else overlap_until
        return bounded_overlap if bounded_overlap >= now else None
