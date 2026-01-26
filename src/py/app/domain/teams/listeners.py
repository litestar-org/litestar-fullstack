"""Team domain signals/events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar.events import listener

from app.domain.accounts.deps import provide_users_service
from app.domain.teams import deps
from app.lib.deps import provide_services

if TYPE_CHECKING:
    from uuid import UUID

    from app.lib.email import AppEmailService


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


@listener("team_invitation_created")
async def team_invitation_created_event_handler(invitation_id: UUID, mailer: AppEmailService) -> None:
    """Executes when a new team invitation is created.

    Args:
        invitation_id: The team invitation ID.
        mailer: The application email service.
    """
    await logger.ainfo("Running post team invitation creation flow.")
    async with provide_services(
        deps.provide_team_invitations_service, deps.provide_teams_service, provide_users_service
    ) as (
        team_invitations_service,
        teams_service,
        users_service,
    ):
        invitation = await team_invitations_service.get_one_or_none(id=invitation_id)
        if invitation is None:
            await logger.aerror("Could not locate the specified team invitation", id=invitation_id)
            return

        inviter = await users_service.get_one_or_none(id=invitation.invited_by_id)
        if inviter is None:
            await logger.aerror("Could not locate the inviter", id=invitation.invited_by_id)
            return

        team = await teams_service.get_one_or_none(id=invitation.team_id)
        if team is None:
            await logger.aerror("Could not locate the team", id=invitation.team_id)
            return

        await mailer.send_team_invitation_email(
            invitee_email=invitation.email,
            inviter_name=inviter.name or inviter.email,
            team_name=team.name,
            invitation_url=f"{mailer.base_url}/teams/{team.id}/invitations/{invitation.id}",
        )

        await logger.ainfo("Sent team invitation email", invitation_id=invitation.id)


__all__ = (
    "team_created_event_handler",
    "team_invitation_created_event_handler",
)
