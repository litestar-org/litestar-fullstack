"""Team Member SecureController."""

from typing import Annotated, ClassVar
from uuid import UUID

from litestar import delete, patch, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.status_codes import HTTP_202_ACCEPTED
from litestar_security import AuthenticationPolicy, SecureController, required

from app.domain.accounts.deps import provide_users_service
from app.domain.accounts.security import requires_team_role
from app.domain.accounts.services import UserService
from app.domain.teams.deps import provide_team_members_service, provide_teams_service
from app.domain.teams.schemas import Team, TeamMember, TeamMemberModify, TeamMemberUpdate
from app.domain.teams.services import TeamMemberService, TeamService


class TeamMemberController(SecureController):
    """Manages team membership additions, removals, and role updates for team admins."""

    path = "/api/teams/{team_id:uuid}/members"
    tags = ["Team Members"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_team_role("admin")]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "team_members_service": Provide(provide_team_members_service),
        "users_service": Provide(provide_users_service),
    }

    @post(operation_id="AddMemberToTeam", path="")
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Add an existing user to the team.

        Returns:
            The updated team with its members.
        """
        user = await users_service.get_one(email=data.user_name)
        await team_members_service.add_member(team_id, user.id)
        team = await teams_service.get(team_id)
        return teams_service.to_schema(team, schema_type=Team)

    @delete(operation_id="RemoveMemberFromTeam", path="", status_code=HTTP_202_ACCEPTED)
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Revoke a member's access to a team while protecting the sole team owner.

        Returns:
            The updated team after removing the member.
        """
        user = await users_service.get_one(email=data.user_name)
        await team_members_service.remove_member(team_id, user.id)
        team = await teams_service.get(team_id)
        return teams_service.to_schema(team, schema_type=Team)

    @patch(operation_id="UpdateTeamMember", path="/{user_id:uuid}")
    async def update_team_member(
        self,
        team_members_service: TeamMemberService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to update.")],
        data: TeamMemberUpdate,
    ) -> TeamMember:
        """Update a team member's role.

        Returns:
            The updated team membership.
        """
        membership = await team_members_service.change_role(team_id, user_id, data.role)
        return team_members_service.to_schema(membership, schema_type=TeamMember)
