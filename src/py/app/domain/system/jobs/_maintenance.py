"""Scheduled maintenance tasks: expired credential cleanup and the scheduler heartbeat."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar_queues import RetryBackoff, get_current_task_context, task
from sqlalchemy import delete

from app.db import models as m
from app.domain.system.jobs._statements import count_rows

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

logger = structlog.get_logger(__name__)


async def run_cleanup_auth_tokens(alchemy_config: SQLAlchemyAsyncConfig) -> dict[str, int]:
    """Delete expired security tokens, challenges, sessions, and ``AppStore`` entries.

    Returns:
        Mapping of cleaned table or namespace labels to deleted row counts.
    """
    context = get_current_task_context()
    if context is not None:
        await context.log("Starting expired authentication and store cleanup")

    counts = await _delete_expired_rows(alchemy_config, now=datetime.now(UTC))
    counts["rate_limit_entries"] = await _delete_expired_store_entries(alchemy_config, namespace="rate_limit")
    counts["session_store_entries"] = await _delete_expired_store_entries(alchemy_config, namespace="sessions")

    if context is not None:
        await context.progress(current=1, total=1, message="Authentication cleanup completed")
        await context.log("Authentication cleanup completed", level="info")
    await logger.ainfo("Token cleanup complete", **counts)
    return counts


@task(
    "system.cleanup_auth_tokens",
    queue="maintenance",
    cron="0 * * * *",
    retries=3,
    retry_backoff=RetryBackoff(initial_delay=5.0, multiplier=2.0, max_delay=300.0),
    unique_by="task",
)
async def cleanup_auth_tokens() -> dict[str, int]:
    """Hourly maintenance task pruning expired auth tokens, challenges, sessions, and rate-limit records.

    Returns:
        Mapping of cleaned table or namespace labels to deleted row counts.
    """
    from app import config

    return await run_cleanup_auth_tokens(config.alchemy)


@task(
    "system.scheduler_canary",
    queue="maintenance",
    cron="*/5 * * * *",
    unique_by="task",
)
async def scheduler_canary() -> dict[str, str]:
    """Periodic scheduler heartbeat confirming beat execution.

    Returns:
        Heartbeat payload with ``status`` and ISO-8601 ``timestamp``.
    """
    now = datetime.now(UTC).isoformat()
    context = get_current_task_context()
    if context is not None:
        await context.log("Scheduler canary heartbeat executed")
    return {"status": "ok", "timestamp": now}


async def _delete_expired_rows(alchemy_config: SQLAlchemyAsyncConfig, *, now: datetime) -> dict[str, int]:
    deletions = {
        "purpose_tokens": delete(m.PurposeToken).where(m.PurposeToken.expires_at <= now),
        "mfa_challenges": delete(m.MFALoginChallenge).where(m.MFALoginChallenge.expires_at <= now),
        "passkey_challenges": delete(m.PasskeyChallenge).where(m.PasskeyChallenge.expires_at <= now),
        "oauth_transactions": delete(m.OAuthTransaction).where(m.OAuthTransaction.expires_at <= now),
        "step_up_grants": delete(m.StepUpGrant).where(m.StepUpGrant.expires_at <= now),
        "user_sessions": delete(m.UserSession).where(m.UserSession.expires_at <= now),
    }
    counts: dict[str, int] = {}
    async with alchemy_config.get_session() as db_session:
        for label, deletion in deletions.items():
            cursor = await db_session.execute(deletion)
            counts[label] = int(getattr(cursor, "rowcount", 0) or 0)
        await db_session.commit()
    return counts


async def _delete_expired_store_entries(alchemy_config: SQLAlchemyAsyncConfig, *, namespace: str) -> int:
    in_namespace = m.AppStore.namespace == namespace
    async with alchemy_config.get_session() as db_session:
        entries_before = await count_rows(db_session, m.AppStore, in_namespace)
    await SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace=namespace).delete_expired()
    async with alchemy_config.get_session() as db_session:
        entries_after = await count_rows(db_session, m.AppStore, in_namespace)
    return max(0, entries_before - entries_after)
