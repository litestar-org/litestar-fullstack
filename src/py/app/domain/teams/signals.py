"""Team domain signals/events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar.events import listener

from app.domain.teams import deps
from app.lib.deps import provide_services

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


@listener("team_created")
async def team_created_event_handler(team_id: UUID) -> None:
    """Executes when a new team is created.

    Args:
        team_id: The primary key of the team that was created.
    """
    await logger.ainfo("Running post team creation flow.")
    async with provide_services(deps.provide_teams_service) as (service,):
        obj = await service.get_one_or_none(id=team_id)
        if obj is None:
            await logger.aerror("Could not locate the specified team", id=team_id)
        else:
            await logger.ainfo("Found team", **obj.to_dict())


__all__ = ("team_created_event_handler",)
