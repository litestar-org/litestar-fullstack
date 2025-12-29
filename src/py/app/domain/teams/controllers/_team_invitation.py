"""Team Invitation Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Dependency
from sqlalchemy.orm import selectinload

from app.db import models as m
from app.domain.teams.dependencies import provide_team_members_service, provide_teams_service
from app.domain.teams.schemas import TeamInvitation, TeamInvitationCreate
from app.domain.teams.services import TeamInvitationService
from app.lib.deps import create_service_dependencies
from app.lib.email import email_service
from app.lib.settings import AppSettings
from app.schemas.base import Message

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service import OffsetPagination

    from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService


class TeamInvitationController(Controller):
    """Team Invitations."""

    path = "/api/teams/{team_id:uuid}/invitations"
    tags = ["Teams"]
    dependencies = create_service_dependencies(
        TeamInvitationService,
        key="team_invitations_service",
        load=[selectinload(m.TeamInvitation.team)],
        error_messages={
            "duplicate_key": "Invitation already exists.",
            "integrity": "Team invitation operation failed.",
        },
        filters={
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "teams_service": Provide(provide_teams_service),
        "team_members_service": Provide(provide_team_members_service),
    }

    @post(operation_id="CreateTeamInvitation", path="")
    async def create_team_invitation(
        self,
        current_user: m.User,
        team_invitations_service: TeamInvitationService,
        teams_service: TeamService,
        settings: AppSettings,
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

        Raises:
            HTTPException: If the invitee is already a team member

        Returns:
            The created team invitation.
        """
        team = await teams_service.get(team_id)
        if any(member.email == data.email for member in team.members):
            raise HTTPException(status_code=400, detail="User is already a member of this team")
        payload = data.to_dict()
        payload["team_id"] = team_id
        payload["invited_by"] = current_user
        db_obj = await team_invitations_service.create(payload)
        await email_service.send_team_invitation_email(
            invitee_email=db_obj.email,
            inviter_name=current_user.name or current_user.email,
            team_name=team.name,
            invitation_url=f"{settings.app.URL}/teams/{team_id}/invitations/{db_obj.id}/accept",
        )
        return team_invitations_service.to_schema(db_obj, schema_type=TeamInvitation)

    @get(operation_id="ListTeamInvitations", path="")
    async def list_team_invitations(
        self,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[TeamInvitation]:
        """List team invitations.

        Args:
            team_id: The ID of the team to list the invitations for.
            team_invitations_service: The team invitation service.

        Returns:
            The list of team invitations.
        """
        db_objs, total = await team_invitations_service.list_and_count(*filters, m.TeamInvitation.team_id == team_id)
        return team_invitations_service.to_schema(
            data=db_objs,
            total=total,
            filters=filters,
            schema_type=TeamInvitation,
        )

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

        Raises:
            HTTPException: If the invitation does not belong to the team
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
            HTTPException: If the invitation is invalid or the user cannot accept it

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
        await team_members_service.create({
            "team_id": team_id,
            "user_id": current_user.id,
            "role": db_obj.role,
            "is_owner": False,
        })
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
        """Reject a team invitation.

        Raises:
            HTTPException: If the invitation is invalid or the user cannot reject it
        """
        db_obj = await team_invitations_service.get(item_id=invitation_id)
        if db_obj.team_id != team_id:
            raise HTTPException(status_code=400, detail="Invitation does not belong to this team")
        if db_obj.email != current_user.email:
            raise HTTPException(status_code=400, detail="You are not authorized to reject this invitation")
        await team_invitations_service.delete(item_id=invitation_id)
        return Message(message="Team invitation rejected")
