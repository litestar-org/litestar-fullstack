"""Team Invitation SecureController with QueuedBackgroundTask email delivery."""

from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import Response, delete, get, post
from litestar.di import Provide
from litestar.params import Dependency
from litestar_queues import QueuedBackgroundTask
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, required

from app.db import models as m
from app.domain.accounts.jobs import send_team_invitation_email_task
from app.domain.accounts.security import requires_team_role
from app.domain.teams.deps import (
    TeamInvitationFilterSet,
    create_filter_dependencies,
    provide_team_invitations_service,
    provide_team_services,
    provide_teams_service,
)
from app.domain.teams.schemas import TeamInvitation, TeamInvitationCreate
from app.domain.teams.services import TeamInvitationService, TeamService, TeamServices
from app.lib.schema import Message
from app.lib.settings import get_settings


class TeamInvitationController(SecureController):
    """Manages team invitations with durable background email dispatch."""

    path = "/api/teams/{team_id:uuid}/invitations"
    tags = ["Teams"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    dependencies = {
        "team_invitations_service": Provide(provide_team_invitations_service),
        "teams_service": Provide(provide_teams_service),
        "team_services": Provide(provide_team_services),
    } | create_filter_dependencies(TeamInvitationFilterSet)

    @post(
        operation_id="CreateTeamInvitation",
        path="",
        guards=[requires_team_role("admin")],
    )
    async def create_team_invitation(
        self,
        current_user: CurrentUser[m.User],
        team_invitations_service: TeamInvitationService,
        teams_service: TeamService,
        team_id: UUID,
        data: TeamInvitationCreate,
    ) -> Response[TeamInvitation]:
        """Create a new team invitation and enqueue durable email delivery.

        Returns:
            HTTP 201 response containing the created invitation.
        """
        team = await teams_service.get(team_id)
        invitation = await team_invitations_service.invite(
            team,
            email=data.email,
            role=data.role,
            invited_by=current_user,
        )
        app_url = get_settings().app.URL.rstrip("/")
        invitation_url = f"{app_url}/teams/{team_id}/invitations/{invitation.id}/accept"
        return Response(
            content=team_invitations_service.to_schema(invitation, schema_type=TeamInvitation),
            status_code=201,
            background=QueuedBackgroundTask(
                send_team_invitation_email_task,
                invitee_email=invitation.email,
                inviter_name=current_user.name or current_user.email,
                team_name=team.name,
                invitation_url=invitation_url,
            ),
        )

    @get(
        operation_id="ListTeamInvitations",
        path="",
        guards=[requires_team_role("member")],
    )
    async def list_team_invitations(
        self,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[TeamInvitation]:
        """List invitations for a team.

        Returns:
            Paginated team invitations.
        """
        invitations, total = await team_invitations_service.get_many_and_count(
            *filters,
            m.TeamInvitation.team_id == team_id,
        )
        return team_invitations_service.to_schema(invitations, total, filters, schema_type=TeamInvitation)

    @delete(
        operation_id="DeleteTeamInvitation",
        path="/{invitation_id:uuid}",
        guards=[requires_team_role("admin")],
    )
    async def delete_team_invitation(
        self,
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> None:
        """Delete an invitation issued by this team."""
        invitation = await team_invitations_service.get_for_team(invitation_id, team_id)
        await team_invitations_service.delete(invitation.id, auto_commit=True)

    @post(operation_id="AcceptTeamInvitation", path="/{invitation_id:uuid}/accept")
    async def accept_team_invitation(
        self,
        current_user: CurrentUser[m.User],
        team_services: TeamServices,
        team_id: UUID,
        invitation_id: UUID,
    ) -> Message:
        """Accept a pending invitation addressed to the authenticated user, adding the membership in the same transaction.

        Returns:
            Confirmation message for the accepted invitation.
        """
        await team_services.accept_invitation(invitation_id, team_id=team_id, user=current_user)
        return Message(message="Team invitation accepted")

    @post(operation_id="RejectTeamInvitation", path="/{invitation_id:uuid}/reject")
    async def reject_team_invitation(
        self,
        current_user: CurrentUser[m.User],
        team_invitations_service: TeamInvitationService,
        team_id: UUID,
        invitation_id: UUID,
    ) -> Message:
        """Reject a pending invitation addressed to the authenticated user.

        Returns:
            Confirmation message for the rejected invitation.
        """
        await team_invitations_service.reject(invitation_id, team_id=team_id, user=current_user)
        return Message(message="Team invitation rejected")
