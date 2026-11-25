"""Personal API key lifecycle SecureController."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, ClassVar, cast

from litestar import Request, delete, get, post
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, SecurityPlugin, required
from litestar_security.context import CredentialRestrictions
from litestar_security.providers.api_key import APIKeyService, IssuedAPIKey

from app.db import models as m
from app.domain.accounts.schemas import APIKeyCreate, APIKeyIssued, APIKeyItem, PasswordConfirmation
from app.domain.accounts.security.api_keys import SQLAlchemyAPIKeyStore, build_api_key_service
from app.domain.accounts.security.reauth import confirm_authentication
from app.domain.accounts.services import APIKeyRecordService

_SECRET_PREFIX_LENGTH = 12
_ROTATION_OVERLAP = timedelta(hours=24)


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
        store, _ = self._api_key_components(request)
        return [APIKeyRecordService.to_item(api_key) for api_key in await store.list_for_user(current_user.id)]

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
        store, api_key_service = self._api_key_components(request)
        expires_at = (
            datetime.now(UTC) + timedelta(days=data.expires_in_days) if data.expires_in_days is not None else None
        )
        issued = await api_key_service.issue(
            subject_id=str(current_user.id),
            restrictions=CredentialRestrictions(scopes=frozenset(data.scopes)) if data.scopes else None,
            expires_at=expires_at,
        )
        return await self._describe_issued(store, issued, name=data.name, scopes=data.scopes, expires_at=expires_at)

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
        store, api_key_service = self._api_key_components(request)
        api_key = await store.get_for_user(current_user.id, key_id)
        if api_key is None:
            raise HTTPException(status_code=404, detail="API key not found.")
        if api_key.revoked_at is not None:
            raise HTTPException(status_code=409, detail="API key has already been revoked or rotated.")
        if api_key.expires_at is not None and api_key.expires_at <= datetime.now(UTC):
            raise HTTPException(status_code=409, detail="API key has expired and cannot be rotated.")
        state = await store.get(key_id)
        try:
            issued = await api_key_service.rotate(
                current_key_id=key_id,
                subject_id=str(current_user.id),
                restrictions=state.restrictions if state is not None else None,
                expires_at=api_key.expires_at,
                overlap=_ROTATION_OVERLAP,
            )
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return await self._describe_issued(
            store,
            issued,
            name=api_key.name,
            scopes=api_key.scopes or [],
            expires_at=api_key.expires_at,
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
        store, api_key_service = self._api_key_components(request)
        if await store.get_for_user(current_user.id, key_id) is None:
            raise HTTPException(status_code=404, detail="API key not found.")
        await api_key_service.revoke(key_id)

    @staticmethod
    def _api_key_components(request: Request[Any, Any, Any]) -> tuple[SQLAlchemyAPIKeyStore, APIKeyService]:
        api_key_config = cast("SecurityPlugin[m.User]", request.app.plugins.get(SecurityPlugin)).config.api_key
        if api_key_config is None or not isinstance(api_key_config.store, SQLAlchemyAPIKeyStore):
            raise HTTPException(status_code=503, detail="API key authentication is not configured.")
        store = api_key_config.store
        return store, build_api_key_service(store, api_key_config.pepper, prefix=api_key_config.prefix)

    @staticmethod
    async def _describe_issued(
        store: SQLAlchemyAPIKeyStore,
        issued: IssuedAPIKey,
        *,
        name: str,
        scopes: list[str],
        expires_at: datetime | None,
    ) -> APIKeyIssued:
        prefix = issued.value[:_SECRET_PREFIX_LENGTH]
        api_key = await store.update_metadata(issued.key_id, name=name, key_prefix=prefix)
        return APIKeyIssued(
            id=issued.key_id,
            name=name,
            prefix=prefix,
            secret=issued.value,
            scopes=list(scopes),
            created_at=api_key.created_at if api_key is not None else datetime.now(UTC),
            expires_at=expires_at,
        )
