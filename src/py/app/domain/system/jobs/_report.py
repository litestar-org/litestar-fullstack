"""Team summary report task."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar_queues import NonRetryableError, RetryBackoff, get_current_task_context, task
from sqlalchemy import select

from app.db import models as m
from app.domain.system.jobs._statements import count_rows

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

_TEAM_NOT_FOUND = "Team not found"


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
        member_count = await count_rows(db_session, m.TeamMember, m.TeamMember.team_id == team.id)
        if context is not None:
            await context.progress(current=2, total=3, message="Counting team tags")
        tag_count = await count_rows(db_session, m.team_tag, m.team_tag.c.team_id == team.id)
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
