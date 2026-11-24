"""Background ``litestar-queues`` task for refreshing expiring OAuth access tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from litestar_queues import RetryBackoff, get_current_task_context, task
from litestar_security.providers.oauth import ProtectedOAuthSecret, ProviderTokenSet, SecretStr
from sqlalchemy import select

from app.db import models as m
from app.domain.accounts.security.oauth import (
    build_oauth_protector,
    deserialize_oauth_tokens,
    oauth_account_aad,
    serialize_oauth_tokens,
)
from app.lib.settings import Settings, get_settings

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar_security.providers.oauth import OAuthTransactionProtector

__all__ = ("refresh_oauth_tokens", "run_refresh_oauth_tokens")

logger = structlog.get_logger(__name__)
REFRESH_WINDOW_MINUTES = 10

_TOKEN_ENDPOINTS: dict[str, str] = {
    "google": "https://oauth2.googleapis.com/token",
    "github": "https://github.com/login/oauth/access_token",
}


def _configured_credentials(settings: Settings) -> dict[str, tuple[str, str]]:
    creds: dict[str, tuple[str, str]] = {}
    if settings.app.google_oauth_enabled:
        creds["google"] = (settings.app.GOOGLE_OAUTH2_CLIENT_ID, settings.app.GOOGLE_OAUTH2_CLIENT_SECRET)
    if settings.app.github_oauth_enabled:
        creds["github"] = (settings.app.GITHUB_OAUTH2_CLIENT_ID, settings.app.GITHUB_OAUTH2_CLIENT_SECRET)
    return creds


async def _refresh_single_account(
    row: m.UserOAuthAccount,
    *,
    client: httpx.AsyncClient,
    protector: OAuthTransactionProtector,
    credentials: dict[str, tuple[str, str]],
    now: datetime,
) -> str:
    provider_creds = credentials.get(row.oauth_name)
    endpoint = _TOKEN_ENDPOINTS.get(row.oauth_name)
    if provider_creds is None or endpoint is None or row.protected_tokens is None or row.key_version is None:
        return "skipped"

    aad = oauth_account_aad(row.oauth_name, row.account_id)
    try:
        raw_blob = await protector.unprotect(
            ProtectedOAuthSecret(key_version=row.key_version, ciphertext=row.protected_tokens),
            associated_data=aad,
        )
        stored = deserialize_oauth_tokens(raw_blob)
        if stored.refresh_token is None or not stored.refresh_token.get_secret_value():
            return "skipped"

        client_id, client_secret = provider_creds
        resp = await client.post(
            endpoint,
            headers={"Accept": "application/json"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": stored.refresh_token.get_secret_value(),
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
        new_access = payload.get("access_token")
        if not isinstance(new_access, str) or not new_access:
            return "failed"

        new_refresh_raw = payload.get("refresh_token")
        new_refresh = (
            SecretStr(new_refresh_raw)
            if isinstance(new_refresh_raw, str) and new_refresh_raw
            else stored.refresh_token
        )
        new_id_token_raw = payload.get("id_token")
        new_id_token = (
            SecretStr(new_id_token_raw)
            if isinstance(new_id_token_raw, str) and new_id_token_raw
            else stored.id_token
        )
        expires_in = payload.get("expires_in")
        new_expires_at = (
            now + timedelta(seconds=int(expires_in))
            if isinstance(expires_in, (int, float)) and expires_in > 0
            else (row.token_expires_at or now + timedelta(hours=1))
        )
        scopes_raw = payload.get("scope")
        scopes = (
            frozenset(scopes_raw.split())
            if isinstance(scopes_raw, str) and scopes_raw.strip()
            else stored.scopes
        )
        tokens = ProviderTokenSet(
            access_token=SecretStr(new_access),
            token_type=stored.token_type,
            scopes=scopes,
            refresh_token=new_refresh,
            id_token=new_id_token,
            expires_at=new_expires_at,
        )
        re_protected = await protector.protect(serialize_oauth_tokens(tokens), associated_data=aad)
        row.protected_tokens = re_protected.ciphertext
        row.key_version = re_protected.key_version
        row.token_version += 1
        row.token_expires_at = new_expires_at
        row.scopes = sorted(tokens.scopes)
    except Exception as exc:  # noqa: BLE001
        await logger.awarning(
            "OAuth token refresh failed",
            provider=row.oauth_name,
            error_type=type(exc).__name__,
        )
        return "failed"
    else:
        return "refreshed"


async def run_refresh_oauth_tokens(
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, int]:
    """Refresh AES-GCM-protected OAuth tokens nearing expiration using ``httpx.AsyncClient``."""
    active_settings = settings or get_settings()
    credentials = _configured_credentials(active_settings)
    if not credentials:
        return {"processed": 0, "refreshed": 0, "skipped": 0, "failed": 0}

    context = get_current_task_context()
    protector = build_oauth_protector(active_settings)
    now = datetime.now(UTC)
    cutoff = now + timedelta(minutes=REFRESH_WINDOW_MINUTES)
    counts = {"processed": 0, "refreshed": 0, "skipped": 0, "failed": 0}

    async with alchemy_config.get_session() as session:
        rows = (
            await session.scalars(
                select(m.UserOAuthAccount).where(
                    m.UserOAuthAccount.protected_tokens.is_not(None),
                    m.UserOAuthAccount.token_expires_at.is_not(None),
                    m.UserOAuthAccount.token_expires_at <= cutoff,
                )
            )
        ).all()

        total = len(rows)
        async with httpx.AsyncClient(timeout=15.0, transport=transport) as client:
            for idx, row in enumerate(rows, start=1):
                counts["processed"] += 1
                if context is not None:
                    await context.progress(
                        current=idx,
                        total=max(1, total),
                        message=f"Refreshing {row.oauth_name} token",
                    )
                outcome = await _refresh_single_account(
                    row,
                    client=client,
                    protector=protector,
                    credentials=credentials,
                    now=now,
                )
                counts[outcome] += 1
        await session.commit()

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
    """Scheduled task refreshing OAuth access tokens nearing expiration."""
    from app import config

    return await run_refresh_oauth_tokens(config.alchemy)
