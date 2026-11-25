"""System domain ``litestar-queues`` background and scheduled tasks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar_queues import NonRetryableError, RetryBackoff, get_current_task_context, task
from sqlalchemy import delete, func, select

from app.db import models as m
from app.lib.schema import CamelizedBaseStruct

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from sqlalchemy import ColumnElement, FromClause
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import DeclarativeBase

__all__ = (
    "QueueTaskEventPayload",
    "cleanup_auth_tokens",
    "export_team_summary",
    "scheduler_canary",
)

logger = structlog.get_logger(__name__)

_TEAM_NOT_FOUND = "Team not found"


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


async def run_export_team_summary(
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    team_id: str,
    requested_by_id: str,
) -> dict[str, Any]:
    """Compute member and tag counts for a team.

    Returns:
        Structured summary payload for the requested team.

    Raises:
        NonRetryableError: If ``team_id`` is malformed or no such team exists.
    """
    try:
        requested_team_id = UUID(team_id)
    except ValueError as exc:
        raise NonRetryableError(_TEAM_NOT_FOUND) from exc

    context = get_current_task_context()
    if context is not None:
        await context.progress(current=1, total=3, message="Loading team record")

    async with alchemy_config.get_session() as db_session:
        team = await db_session.scalar(select(m.Team).where(m.Team.id == requested_team_id))
        if team is None:
            raise NonRetryableError(_TEAM_NOT_FOUND)
        member_count = await _count_rows(db_session, m.TeamMember, m.TeamMember.team_id == team.id)
        if context is not None:
            await context.progress(current=2, total=3, message="Counting team tags")
        tag_count = await _count_rows(db_session, m.team_tag, m.team_tag.c.team_id == team.id)
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
        entries_before = await _count_rows(db_session, m.AppStore, in_namespace)
    await SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace=namespace).delete_expired()
    async with alchemy_config.get_session() as db_session:
        entries_after = await _count_rows(db_session, m.AppStore, in_namespace)
    return max(0, entries_before - entries_after)


async def _count_rows(
    db_session: AsyncSession,
    source: FromClause | type[DeclarativeBase],
    criterion: ColumnElement[bool],
) -> int:
    return await db_session.scalar(select(func.count()).select_from(source).where(criterion)) or 0
