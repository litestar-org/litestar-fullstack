"""Background ``litestar-queues`` task for refreshing expiring OAuth access tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal

import httpx
import structlog
from litestar_queues import RetryBackoff, get_current_task_context, task
from litestar_security.providers.oauth import ProtectedOAuthSecret, ProviderTokenSet, SecretStr

from app.domain.accounts.security.oauth import (
    build_oauth_protector,
    deserialize_oauth_tokens,
    oauth_account_aad,
    serialize_oauth_tokens,
)
from app.domain.accounts.services import OAuthAccountService
from app.lib.settings import Settings, get_settings

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar_security.providers.oauth import OAuthTransactionProtector

    from app.db import models as m

__all__ = ("refresh_oauth_tokens", "run_refresh_oauth_tokens")

logger = structlog.get_logger(__name__)
REFRESH_WINDOW_MINUTES = 10

_RefreshOutcome = Literal["refreshed", "skipped", "failed"]

_TOKEN_ENDPOINTS: dict[str, str] = {
    "github": "https://github.com/login/oauth/access_token",
}


async def run_refresh_oauth_tokens(
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, int]:
    """Refresh AES-GCM-protected OAuth tokens nearing expiration using ``httpx.AsyncClient``.

    Returns:
        Summary counts mapping for ``processed``, ``refreshed``, ``skipped``, and ``failed`` accounts.
    """
    active_settings = settings or get_settings()
    counts = {"processed": 0, "refreshed": 0, "skipped": 0, "failed": 0}
    credentials = _configured_credentials(active_settings)
    if not credentials:
        return counts

    context = get_current_task_context()
    protector = build_oauth_protector(active_settings)
    now = datetime.now(UTC)
    async with (
        OAuthAccountService.new(config=alchemy_config) as oauth_accounts,
        httpx.AsyncClient(timeout=15.0, transport=transport) as client,
    ):
        expiring_accounts = await oauth_accounts.list_expiring(before=now + timedelta(minutes=REFRESH_WINDOW_MINUTES))
        for position, oauth_account in enumerate(expiring_accounts, start=1):
            counts["processed"] += 1
            if context is not None:
                await context.progress(
                    current=position,
                    total=len(expiring_accounts),
                    message=f"Refreshing {oauth_account.oauth_name} token",
                )
            outcome = await _refresh_account(
                oauth_accounts,
                oauth_account,
                client=client,
                protector=protector,
                credentials=credentials,
                now=now,
            )
            counts[outcome] += 1
        await oauth_accounts.repository.session.commit()

    if context is not None:
        await context.log("OAuth token refresh job completed")
    await logger.ainfo("OAuth refresh job complete", **counts)
    return counts


@task(
    "accounts.refresh_oauth_tokens",
    queue="maintenance",
    cron="*/15 * * * *",
    retries=3,
    retry_backoff=RetryBackoff(initial_delay=5.0, multiplier=2.0, max_delay=300.0),
    unique_by="task",
)
async def refresh_oauth_tokens() -> dict[str, int]:
    """Scheduled task refreshing OAuth access tokens nearing expiration.

    Returns:
        Summary counts mapping for ``processed``, ``refreshed``, ``skipped``, and ``failed`` accounts.
    """
    from app import config

    return await run_refresh_oauth_tokens(config.alchemy)


def _configured_credentials(settings: Settings) -> dict[str, tuple[str, str]]:
    credentials: dict[str, tuple[str, str]] = {}
    if settings.app.github_oauth_enabled:
        credentials["github"] = (settings.app.GITHUB_OAUTH2_CLIENT_ID, settings.app.GITHUB_OAUTH2_CLIENT_SECRET)
    return credentials


async def _refresh_account(
    oauth_accounts: OAuthAccountService,
    oauth_account: m.UserOAuthAccount,
    *,
    client: httpx.AsyncClient,
    protector: OAuthTransactionProtector,
    credentials: dict[str, tuple[str, str]],
    now: datetime,
) -> _RefreshOutcome:
    provider_credentials = credentials.get(oauth_account.oauth_name)
    token_endpoint = _TOKEN_ENDPOINTS.get(oauth_account.oauth_name)
    if (
        provider_credentials is None
        or token_endpoint is None
        or oauth_account.protected_tokens is None
        or oauth_account.key_version is None
    ):
        return "skipped"

    associated_data = oauth_account_aad(oauth_account.oauth_name, oauth_account.account_id)
    try:
        serialized_tokens = await protector.unprotect(
            ProtectedOAuthSecret(key_version=oauth_account.key_version, ciphertext=oauth_account.protected_tokens),
            associated_data=associated_data,
        )
        stored_tokens = deserialize_oauth_tokens(serialized_tokens)
        if stored_tokens.refresh_token is None or not stored_tokens.refresh_token.get_secret_value():
            return "skipped"

        client_id, client_secret = provider_credentials
        response = await client.post(
            token_endpoint,
            headers={"Accept": "application/json"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": stored_tokens.refresh_token.get_secret_value(),
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        tokens = _merge_refreshed_tokens(
            response.json(),
            stored_tokens,
            fallback_expires_at=oauth_account.token_expires_at or now + timedelta(hours=1),
            now=now,
        )
        if tokens is None:
            return "failed"
        replaced = await oauth_accounts.replace_tokens(
            oauth_account,
            expected_version=oauth_account.token_version,
            tokens=tokens,
            protected_tokens=await protector.protect(serialize_oauth_tokens(tokens), associated_data=associated_data),
        )
    except Exception as error:  # noqa: BLE001
        await logger.awarning(
            "OAuth token refresh failed",
            provider=oauth_account.oauth_name,
            error_type=type(error).__name__,
        )
        return "failed"
    else:
        return "refreshed" if replaced else "skipped"


def _merge_refreshed_tokens(
    token_response: dict[str, Any],
    stored_tokens: ProviderTokenSet,
    *,
    fallback_expires_at: datetime,
    now: datetime,
) -> ProviderTokenSet | None:
    access_token = token_response.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        return None
    expires_in = token_response.get("expires_in")
    expires_at = (
        now + timedelta(seconds=int(expires_in))
        if isinstance(expires_in, (int, float)) and expires_in > 0
        else fallback_expires_at
    )
    scope = token_response.get("scope")
    return ProviderTokenSet(
        access_token=SecretStr(access_token),
        token_type=stored_tokens.token_type,
        scopes=frozenset(scope.split()) if isinstance(scope, str) and scope.strip() else stored_tokens.scopes,
        refresh_token=_secret_or(token_response.get("refresh_token"), stored_tokens.refresh_token),
        id_token=_secret_or(token_response.get("id_token"), stored_tokens.id_token),
        expires_at=expires_at,
    )


def _secret_or(value: object, fallback: SecretStr | None) -> SecretStr | None:
    return SecretStr(value) if isinstance(value, str) and value else fallback
