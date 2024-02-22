"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import IntegrityError
from litestar import Controller, post
from litestar.di import Provide
from litestar.params import Parameter

from app.db.models import TeamMember, TeamRoles
from app.domain.accounts.dependencies import provide_users_service
from app.domain.accounts.services import UserService
from app.domain.teams import urls
from app.domain.teams.dependencies import provide_team_members_service, provide_teams_service
from app.domain.teams.schemas import Team, TeamMemberModify
from app.domain.teams.services import TeamMemberService, TeamService

if TYPE_CHECKING:
    from uuid_utils import UUID


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "team_members_service": Provide(provide_team_members_service),
        "users_service": Provide(provide_users_service),
    }
    signature_namespace = {
        "TeamService": TeamService,
        "UserService": UserService,
        "TeamMemberService": TeamMemberService,
    }

    @post(
        operation_id="AddMemberToTeam",
        name="teams:add-member",
        path=urls.TEAM_ADD_MEMBER,
    )
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to update.",
        ),
    ) -> Team:
        """Add a member to a team."""
        team_obj = await teams_service.get(team_id)
        user_obj = await users_service.get_one(email=data.user_name)
        is_member = any(membership.team.id == team_id for membership in user_obj.teams)
        if is_member:
            msg = "User is already a member of the team."
            raise IntegrityError(msg)
        team_obj.members.append(TeamMember(user_id=user_obj.id, role=TeamRoles.MEMBER))
        team_obj = await teams_service.update(item_id=team_id, data=team_obj)
        return teams_service.to_schema(Team, team_obj)

    @post(
        operation_id="RemoveMemberFromTeam",
        name="teams:remove-member",
        summary="Remove Team Member",
        description="Removes a member from a team",
        path=urls.TEAM_REMOVE_MEMBER,
    )
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to delete.",
        ),
    ) -> Team:
        """Delete a new migration team."""
        user_obj = await users_service.get_one(email=data.user_name)
        removed_member = False
        for membership in user_obj.teams:
            if membership.user_id == user_obj.id:
                removed_member = True
                _ = await team_members_service.delete(membership.id)
        if not removed_member:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(Team, team_obj)
