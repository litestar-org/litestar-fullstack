"""System domain ``litestar-queues`` background and scheduled tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, NoReturn
from uuid import UUID

import structlog
from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar_queues import NonRetryableError, RetryBackoff, get_current_task_context, task
from sqlalchemy import delete, func, select

from app.db import models as m
from app.lib.schema import CamelizedBaseStruct

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

__all__ = (
    "QueueTaskEventPayload",
    "cleanup_auth_tokens",
    "export_team_summary",
    "scheduler_canary",
)

logger = structlog.get_logger(__name__)


class QueueTaskEventPayload(CamelizedBaseStruct):
    """Typed AsyncAPI payload emitted on the ``queue_events`` channel."""

    task_id: str
    task_name: str
    queue: str
    status: str
    timestamp: datetime
    progress: int | None = None
    total: int | None = None
    message: str | None = None


async def run_cleanup_auth_tokens(alchemy_config: SQLAlchemyAsyncConfig) -> dict[str, int]:
    """Delete expired security tokens, challenges, sessions, and ``AppStore`` entries.

    Returns:
        Mapping of cleaned table or namespace labels to deleted row counts.
    """
    now = datetime.now(UTC)
    context = get_current_task_context()
    if context is not None:
        await context.log("Starting expired authentication and store cleanup")

    counts: dict[str, int] = {}
    async with alchemy_config.get_session() as session:
        tables: tuple[tuple[str, Any, Any], ...] = (
            ("purpose_tokens", m.PurposeToken, m.PurposeToken.expires_at <= now),
            ("mfa_challenges", m.MFALoginChallenge, m.MFALoginChallenge.expires_at <= now),
            ("passkey_challenges", m.PasskeyChallenge, m.PasskeyChallenge.expires_at <= now),
            ("oauth_transactions", m.OAuthTransaction, m.OAuthTransaction.expires_at <= now),
            ("step_up_grants", m.StepUpGrant, m.StepUpGrant.expires_at <= now),
            ("user_sessions", m.UserSession, m.UserSession.expires_at <= now),
        )
        for label, model_cls, predicate in tables:
            result = await session.execute(delete(model_cls).where(predicate))
            counts[label] = int(getattr(result, "rowcount", 0) or 0)
        await session.commit()

    rate_store = SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace="rate_limit")
    session_store = SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace="sessions")
    async with alchemy_config.get_session() as session:
        rate_before = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.AppStore).where(m.AppStore.namespace == "rate_limit")
                )
            )
            or 0
        )
        sess_before = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.AppStore).where(m.AppStore.namespace == "sessions")
                )
            )
            or 0
        )
    await rate_store.delete_expired()
    await session_store.delete_expired()
    async with alchemy_config.get_session() as session:
        rate_after = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.AppStore).where(m.AppStore.namespace == "rate_limit")
                )
            )
            or 0
        )
        sess_after = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.AppStore).where(m.AppStore.namespace == "sessions")
                )
            )
            or 0
        )
    counts["rate_limit_entries"] = max(0, rate_before - rate_after)
    counts["session_store_entries"] = max(0, sess_before - sess_after)

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


def _abort_non_retryable(message: str) -> NoReturn:
    raise NonRetryableError(message)


async def run_export_team_summary(
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    team_id: str,
    requested_by_id: str,
) -> dict[str, Any]:
    """Compute member and tag counts for a team, aborting non-retryably if missing.

    Returns:
        Structured summary payload for the requested team.
    """
    try:
        parsed_team_id = UUID(team_id)
    except ValueError:
        _abort_non_retryable("Team not found")

    context = get_current_task_context()
    if context is not None:
        await context.progress(current=1, total=3, message="Loading team record")

    async with alchemy_config.get_session() as session:
        team = await session.scalar(select(m.Team).where(m.Team.id == parsed_team_id))
        if team is None:
            _abort_non_retryable("Team not found")
        member_count = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.TeamMember).where(m.TeamMember.team_id == parsed_team_id)
                )
            )
            or 0
        )
        if context is not None:
            await context.progress(current=2, total=3, message="Counting team tags")
        tag_count = int(
            (
                await session.scalar(
                    select(func.count()).select_from(m.team_tag).where(m.team_tag.c.team_id == parsed_team_id)
                )
            )
            or 0
        )
        summary: dict[str, Any] = {
            "team_id": str(team.id),
            "team_name": team.name,
            "requested_by_id": requested_by_id,
            "member_count": member_count,
            "tag_count": tag_count,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    if context is not None:
        await context.progress(current=3, total=3, message="Team summary ready")
        await context.log("Team summary report generated")
    return summary


@task(
    "reports.export_team_summary",
    queue="reports",
    retries=3,
    retry_backoff=RetryBackoff(initial_delay=2.0, multiplier=2.0, max_delay=60.0),
    unique_by="arguments",
)
async def export_team_summary(team_id: str, requested_by_id: str) -> dict[str, Any]:
    """Generate a structured summary report for the specified team.

    Returns:
        Structured summary payload for the requested team.
    """
    from app import config

    return await run_export_team_summary(config.alchemy, team_id=team_id, requested_by_id=requested_by_id)
