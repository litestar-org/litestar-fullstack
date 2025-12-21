"""Team Invitation Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException

from app.domain.teams.dependencies import provide_team_invitations_service
from app.domain.teams.schemas import TeamInvitation, TeamInvitationCreate
from app.schemas.base import Message

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import OffsetPagination

    from app.db import models as m
    from app.domain.teams.services import TeamInvitationService


class TeamInvitationController(Controller):
    """Team Invitations."""

    tags = ["Teams"]
    dependencies = {
        "team_invitations_service": Provide(provide_team_invitations_service),
    }

    @post(operation_id="CreateTeamInvitation", path="/{team_id:uuid}")
    async def create_team_invitation(
        self, team_invitations_service: TeamInvitationService, data: TeamInvitationCreate
    ) -> TeamInvitation:
        """Create a team invitation.

        Args:
            data: The data to create the team invitation with.
            team_invitations_service: The team invitation service.

        Returns:
            The created team invitation.
        """
        db_obj = await team_invitations_service.create(data)
        return team_invitations_service.to_schema(db_obj, schema_type=TeamInvitation)

    @get(operation_id="ListTeamInvitations", path="/{team_id:uuid}")
    async def list_team_invitations(
        self, team_invitations_service: TeamInvitationService, team_id: UUID
    ) -> OffsetPagination[TeamInvitation]:
        """List team invitations.

        Args:
            team_id: The ID of the team to list the invitations for.
            team_invitations_service: The team invitation service.

        Returns:
            The list of team invitations.
        """
        db_objs, total = await team_invitations_service.list_and_count(team_id=team_id)
        return team_invitations_service.to_schema(data=db_objs, total=total, schema_type=TeamInvitation)

    @delete(operation_id="DeleteTeamInvitation", path="/{team_id:uuid}/{invitation_id:uuid}")
    async def delete_team_invitation(
        self,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> None:
        """Delete a team invitation.

        Args:
            team_id: The ID of the team to delete the invitation for.
            invitation_id: The ID of the invitation to delete.
            team_invitations_service: The team invitation service.
        """
        await team_invitations_service.delete(item_id=invitation_id)

    @post(operation_id="AcceptTeamInvitation", path="/{team_id:uuid}/{invitation_id:uuid}")
    async def accept_team_invitation(
        self,
        current_user: m.User,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> Message:
        """Accept a team invitation.

        Args:
            team_id: The ID of the team to accept the invitation for.
            invitation_id: The ID of the invitation to accept.
            team_invitations_service: The team invitation service.
            current_user: The current user.

        Raises:
            HTTPException: If the user is not authorized to accept the invitation.

        Returns:
            A message indicating that the team invitation has been accepted.
        """
        db_obj = await team_invitations_service.get(item_id=invitation_id)
        if db_obj.email != current_user.email:
            raise HTTPException(status_code=400, detail="You are not authorized to accept this invitation")
        db_obj = await team_invitations_service.update(item_id=invitation_id, data={"accepted": True})
        return Message(message="Team invitation accepted")
