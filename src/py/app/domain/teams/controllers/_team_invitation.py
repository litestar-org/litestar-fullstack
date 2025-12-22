"""Team Invitation Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException

from app.domain.teams.dependencies import (
    provide_team_invitations_service,
    provide_team_members_service,
    provide_teams_service,
)
from app.domain.teams.schemas import TeamInvitation, TeamInvitationCreate
from app.lib.email import email_service
from app.lib.settings import get_settings
from app.schemas.base import Message

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import OffsetPagination

    from app.db import models as m
    from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService


class TeamInvitationController(Controller):
    """Team Invitations."""

    path = "/api/teams/{team_id:uuid}/invitations"
    tags = ["Teams"]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "team_invitations_service": Provide(provide_team_invitations_service),
        "team_members_service": Provide(provide_team_members_service),
    }

    @post(operation_id="CreateTeamInvitation", path="")
    async def create_team_invitation(
        self,
        current_user: m.User,
        team_invitations_service: TeamInvitationService,
        teams_service: TeamService,
        team_id: UUID,
        data: TeamInvitationCreate,
    ) -> TeamInvitation:
        """Create a team invitation.

        Args:
            current_user: The current user sending the invitation.
            data: The data to create the team invitation with.
            team_invitations_service: The team invitation service.
            teams_service: The teams service.
            team_id: The team id.

        Returns:
            The created team invitation.
        """
        team = await teams_service.get(team_id)
        if any(member.email == data.email for member in team.members):
            raise HTTPException(status_code=400, detail="User is already a member of this team")
        payload = data.to_dict()
        payload["team_id"] = team_id
        payload["invited_by_id"] = current_user.id
        payload["invited_by_email"] = current_user.email
        db_obj = await team_invitations_service.create(payload)
        settings = get_settings()
        invitation_url = f"{settings.app.URL}/teams/{team_id}/invitations/{db_obj.id}/accept"
        await email_service.send_team_invitation_email(
            invitee_email=db_obj.email,
            inviter_name=current_user.name or current_user.email,
            team_name=team.name,
            invitation_url=invitation_url,
        )
        return team_invitations_service.to_schema(db_obj, schema_type=TeamInvitation)

    @get(operation_id="ListTeamInvitations", path="")
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

    @delete(operation_id="DeleteTeamInvitation", path="/{invitation_id:uuid}")
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
        invitation = await team_invitations_service.get(invitation_id)
        if invitation.team_id != team_id:
            raise HTTPException(status_code=400, detail="Invitation does not belong to this team")
        await team_invitations_service.delete(item_id=invitation_id)

    @post(operation_id="AcceptTeamInvitation", path="/{invitation_id:uuid}/accept")
    async def accept_team_invitation(
        self,
        current_user: m.User,
        team_invitations_service: TeamInvitationService,
        team_members_service: TeamMemberService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> Message:
        """Accept a team invitation.

        Args:
            team_id: The ID of the team to accept the invitation for.
            invitation_id: The ID of the invitation to accept.
            team_invitations_service: The team invitation service.
            team_members_service: The team member service.
            current_user: The current user.

        Raises:
            HTTPException: If the user is not authorized to accept the invitation.

        Returns:
            A message indicating that the team invitation has been accepted.
        """
        db_obj = await team_invitations_service.get(item_id=invitation_id)
        if db_obj.team_id != team_id:
            raise HTTPException(status_code=400, detail="Invitation does not belong to this team")
        if db_obj.is_accepted:
            raise HTTPException(status_code=400, detail="Invitation has already been accepted")
        if db_obj.email != current_user.email:
            raise HTTPException(status_code=400, detail="You are not authorized to accept this invitation")
        existing_membership = await team_members_service.get_one_or_none(
            team_id=team_id,
            user_id=current_user.id,
        )
        if existing_membership is not None:
            raise HTTPException(status_code=400, detail="User is already a member of this team")
        await team_members_service.create(
            {
                "team_id": team_id,
                "user_id": current_user.id,
                "role": db_obj.role,
                "is_owner": False,
            }
        )
        await team_invitations_service.update(item_id=invitation_id, data={"is_accepted": True})
        return Message(message="Team invitation accepted")

    @post(operation_id="RejectTeamInvitation", path="/{invitation_id:uuid}/reject")
    async def reject_team_invitation(
        self,
        current_user: m.User,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> Message:
        """Reject a team invitation."""
        db_obj = await team_invitations_service.get(item_id=invitation_id)
        if db_obj.team_id != team_id:
            raise HTTPException(status_code=400, detail="Invitation does not belong to this team")
        if db_obj.email != current_user.email:
            raise HTTPException(status_code=400, detail="You are not authorized to reject this invitation")
        await team_invitations_service.delete(item_id=invitation_id)
        return Message(message="Team invitation rejected")
