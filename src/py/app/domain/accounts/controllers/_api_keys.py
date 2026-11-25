"""Personal API key lifecycle SecureController."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, ClassVar, cast

from litestar import Request, delete, get, post
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, SecurityPlugin, required
from litestar_security.context import CredentialRestrictions
from litestar_security.providers.api_key import APIKeyService

from app.db import models as m
from app.domain.accounts.schemas import APIKeyCreate, APIKeyIssued, APIKeyItem, PasswordConfirmation
from app.domain.accounts.security.api_keys import SQLAlchemyAPIKeyStore, build_api_key_service
from app.domain.accounts.security.reauth import confirm_authentication


def _resolve_api_key_components(request: Request[Any, Any, Any]) -> tuple[SQLAlchemyAPIKeyStore, APIKeyService]:
    plugin = cast("SecurityPlugin[m.User]", request.app.plugins.get(SecurityPlugin))
    api_key_cfg = plugin.config.api_key
    if api_key_cfg is None or not isinstance(api_key_cfg.store, SQLAlchemyAPIKeyStore):
        raise HTTPException(status_code=503, detail="API key authentication is not configured.")
    store = api_key_cfg.store
    service = build_api_key_service(store, api_key_cfg.pepper, prefix=api_key_cfg.prefix)
    return store, service


class ApiKeyController(SecureController):
    """Session-authenticated controller for managing user-owned personal API keys."""

    path = "/api/me/api-keys"
    tags = ["API Keys"]
    auth: ClassVar[AuthenticationPolicy] = required("session")

    @get(operation_id="ListApiKeys", path="")
    async def list_api_keys(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
    ) -> list[APIKeyItem]:
        """List secret-free API key metadata owned by the authenticated user.

        Returns:
            List of API key metadata items owned by the authenticated user.
        """
        store, _ = _resolve_api_key_components(request)
        rows = await store.list_for_user(current_user.id)
        return [
            APIKeyItem(
                id=row.key_id,
                name=row.name,
                prefix=row.key_prefix,
                scopes=list(row.scopes or []),
                created_at=row.created_at,
                expires_at=row.expires_at,
                last_used_at=row.last_used_at,
                revoked_at=row.revoked_at,
            )
            for row in rows
        ]

    @post(operation_id="CreateApiKey", path="")
    async def create_api_key(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        data: APIKeyCreate,
    ) -> APIKeyIssued:
        """Mint a new reveal-once API key after a recent sign-in or password confirmation.

        Returns:
            Newly issued API key payload including the reveal-once secret.
        """
        await confirm_authentication(request, current_user, data.current_password)
        store, service = _resolve_api_key_components(request)
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=data.expires_in_days) if data.expires_in_days is not None else None
        restrictions = CredentialRestrictions(scopes=frozenset(data.scopes)) if data.scopes else None
        issued = await service.issue(
            subject_id=str(current_user.id),
            restrictions=restrictions,
            expires_at=expires_at,
        )
        prefix = issued.value[:12]
        row = await store.update_metadata(issued.key_id, name=data.name, key_prefix=prefix)
        created_at = row.created_at if row is not None else now
        return APIKeyIssued(
            id=issued.key_id,
            name=data.name,
            prefix=prefix,
            secret=issued.value,
            scopes=list(data.scopes),
            created_at=created_at,
            expires_at=expires_at,
        )

    @post(operation_id="RotateApiKey", path="/{key_id:str}/rotate")
    async def rotate_api_key(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        key_id: Annotated[str, Parameter(title="API Key ID", description="Opaque API key identifier to rotate.")],
        data: PasswordConfirmation | None = None,
    ) -> APIKeyIssued:
        """Rotate an owned API key with a 24-hour overlap after a recent sign-in or password confirmation.

        Returns:
            Replacement API key payload including the reveal-once secret.

        Raises:
            HTTPException: If the key is not found, already revoked/rotated, expired, or cannot be rotated.
        """
        await confirm_authentication(request, current_user, data.current_password if data else None)
        store, service = _resolve_api_key_components(request)
        existing = await store.get_for_user(current_user.id, key_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="API key not found.")
        if existing.revoked_at is not None:
            raise HTTPException(status_code=409, detail="API key has already been revoked or rotated.")
        now = datetime.now(UTC)
        expires_at = (
            existing.expires_at.replace(tzinfo=UTC)
            if existing.expires_at is not None and existing.expires_at.tzinfo is None
            else existing.expires_at
        )
        if expires_at is not None and expires_at <= now:
            raise HTTPException(status_code=409, detail="API key has expired and cannot be rotated.")
        state = await store.get(key_id)
        restrictions = state.restrictions if state is not None else None
        try:
            issued = await service.rotate(
                current_key_id=key_id,
                subject_id=str(current_user.id),
                restrictions=restrictions,
                expires_at=expires_at,
                overlap=timedelta(hours=24),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        prefix = issued.value[:12]
        row = await store.update_metadata(issued.key_id, name=existing.name, key_prefix=prefix)
        created_at = row.created_at if row is not None else datetime.now(UTC)
        return APIKeyIssued(
            id=issued.key_id,
            name=existing.name,
            prefix=prefix,
            secret=issued.value,
            scopes=list(existing.scopes or []),
            created_at=created_at,
            expires_at=expires_at,
        )

    @delete(operation_id="RevokeApiKey", path="/{key_id:str}")
    async def revoke_api_key(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        key_id: Annotated[str, Parameter(title="API Key ID", description="Opaque API key identifier to revoke.")],
        data: PasswordConfirmation | None = None,
    ) -> None:
        """Immediately revoke an owned API key after a recent sign-in or password confirmation.

        Raises:
            HTTPException: If the API key does not exist or is not owned by the authenticated user.
        """
        await confirm_authentication(request, current_user, data.current_password if data else None)
        store, service = _resolve_api_key_components(request)
        existing = await store.get_for_user(current_user.id, key_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="API key not found.")
        await service.revoke(key_id)
