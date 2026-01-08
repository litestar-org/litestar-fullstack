"""Background job for refreshing OAuth tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import httpx
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.oauth2 import GetAccessTokenError
from structlog import get_logger

from app.db import models as m
from app.domain.accounts import deps as account_deps
from app.lib.deps import provide_services
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from saq.types import Context

logger = get_logger()
REFRESH_WINDOW_MINUTES = 10


def _get_oauth_clients() -> dict[str, GitHubOAuth2 | GoogleOAuth2]:
    settings = get_settings()
    clients: dict[str, GitHubOAuth2 | GoogleOAuth2] = {}
    if settings.app.google_oauth_enabled:
        clients["google"] = GoogleOAuth2(
            settings.app.GOOGLE_OAUTH2_CLIENT_ID,
            settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
        )
    if settings.app.github_oauth_enabled:
        clients["github"] = GitHubOAuth2(
            settings.app.GITHUB_OAUTH2_CLIENT_ID,
            settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
        )
    return clients


async def refresh_oauth_tokens(_: Context) -> dict[str, int]:
    """Refresh OAuth access tokens that are nearing expiration."""
    clients = _get_oauth_clients()
    if not clients:
        return {"processed": 0, "refreshed": 0, "skipped": 0, "failed": 0}

    now = datetime.now(UTC)
    cutoff = now + timedelta(minutes=REFRESH_WINDOW_MINUTES)
    processed = 0
    refreshed = 0
    skipped = 0
    failed = 0

    async with provide_services(account_deps.provide_user_oauth_service) as (oauth_service,):
        accounts = await oauth_service.list(
            m.UserOAuthAccount.refresh_token.is_not(None),
            m.UserOAuthAccount.token_expires_at.is_not(None),
            m.UserOAuthAccount.token_expires_at <= cutoff,
        )

        for account in accounts:
            processed += 1
            client = clients.get(account.oauth_name)
            if client is None or account.refresh_token is None:
                skipped += 1
                continue

            try:
                token_data = await client.refresh_token(account.refresh_token)
            except (GetAccessTokenError, httpx.HTTPError) as exc:
                failed += 1
                await logger.awarning("OAuth refresh failed", provider=account.oauth_name, error=str(exc))
                continue

            expires_at = token_data.get("expires_at")
            token_expires_at = datetime.fromtimestamp(expires_at, tz=UTC) if expires_at else None

            update_data: dict[str, object] = {
                "access_token": token_data["access_token"],
            }
            if token_data.get("refresh_token"):
                update_data["refresh_token"] = token_data["refresh_token"]
            if expires_at is not None:
                update_data["expires_at"] = expires_at
                update_data["token_expires_at"] = token_expires_at
            if token_data.get("scope") is not None:
                update_data["scope"] = token_data["scope"]

            await oauth_service.update(item_id=account.id, data=update_data, auto_commit=True)
            refreshed += 1

    result = {"processed": processed, "refreshed": refreshed, "skipped": skipped, "failed": failed}
    await logger.ainfo("OAuth refresh job complete", **result)
    return result


__all__ = ("refresh_oauth_tokens",)
