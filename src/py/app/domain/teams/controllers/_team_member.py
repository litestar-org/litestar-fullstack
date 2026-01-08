"""Team Member Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from advanced_alchemy.exceptions import IntegrityError
from litestar import Controller, delete, patch, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.status_codes import HTTP_202_ACCEPTED

from app.db import models as m
from app.domain.accounts.deps import provide_users_service
from app.domain.teams.deps import provide_team_members_service, provide_teams_service
from app.domain.teams.schemas import Team, TeamMember, TeamMemberModify, TeamMemberUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.accounts.services import UserService
    from app.domain.teams.services import TeamMemberService, TeamService


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "team_members_service": Provide(provide_team_members_service),
        "users_service": Provide(provide_users_service),
    }

    @post(operation_id="AddMemberToTeam", path="/api/teams/{team_id:uuid}/members")
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Add a member to a team.

        Args:
            teams_service: Team Service
            team_members_service: Team Member Service
            users_service: User Service
            data: Team Member Modify
            team_id: Team ID

        Raises:
            IntegrityError: If the user is already a member of the team.

        Returns:
            Team
        """
        user_obj = await users_service.get_one(email=data.user_name)
        existing_membership = await team_members_service.get_one_or_none(team_id=team_id, user_id=user_obj.id)
        if existing_membership is not None:
            msg = "User is already a member of the team."
            raise IntegrityError(msg)
        await team_members_service.create(
            {
                "team_id": team_id,
                "user_id": user_obj.id,
                "role": m.TeamRoles.MEMBER,
                "is_owner": False,
            }
        )
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(team_obj, schema_type=Team)

    @delete(
        operation_id="RemoveMemberFromTeam", path="/api/teams/{team_id:uuid}/members", status_code=HTTP_202_ACCEPTED
    )
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> Team:
        """Revoke a member's access to a team.

        Args:
            teams_service: Team Service
            team_members_service: Team Member Service
            users_service: User Service
            data: Team Member Modify
            team_id: Team ID

        Raises:
            IntegrityError: If the user is not a member of the team.

        Returns:
            Team
        """
        user_obj = await users_service.get_one(email=data.user_name)
        membership = await team_members_service.get_one_or_none(team_id=team_id, user_id=user_obj.id)
        if membership is None:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        _ = await team_members_service.delete(membership.id)
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(team_obj, schema_type=Team)

    @patch(operation_id="UpdateTeamMember", path="/api/teams/{team_id:uuid}/members/{user_id:uuid}")
    async def update_team_member(
        self,
        team_members_service: TeamMemberService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to update.")],
        data: TeamMemberUpdate,
    ) -> TeamMember:
        """Update a team member's role.

        Raises:
            IntegrityError: If the user is not a member of the team.
        """
        membership = await team_members_service.get_one_or_none(team_id=team_id, user_id=user_id)
        if membership is None:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        updated = await team_members_service.update(item_id=membership.id, data={"role": data.role})
        return team_members_service.to_schema(updated, schema_type=TeamMember)
