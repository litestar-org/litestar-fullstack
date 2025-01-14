"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import IntegrityError
from litestar import Controller, post
from litestar.params import Parameter

from app.db import models as m
from app.domain.teams import urls
from app.domain.teams.schemas import Team, TeamMemberModify
from app.domain.teams.services import TeamMemberService, TeamService
from app.lib.deps import create_service_provider

if TYPE_CHECKING:
    from uuid import UUID

    from app.domain.accounts.services import UserService


class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    dependencies = {
        "teams_service": create_service_provider(TeamService, load=[m.Team.tags, m.Team.members]),
        "team_members_service": create_service_provider(
            TeamMemberService,
            load=[m.TeamMember.team, m.TeamMember.user],
        ),
    }

    @post(operation_id="AddMemberToTeam", path=urls.TEAM_ADD_MEMBER)
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(title="Team ID", description="The team to update."),
    ) -> Team:
        """Add a member to a team."""
        team_obj = await teams_service.get(team_id)
        user_obj = await users_service.get_one(email=data.user_name)
        is_member = any(membership.team.id == team_id for membership in user_obj.teams)
        if is_member:
            msg = "User is already a member of the team."
            raise IntegrityError(msg)
        team_obj.members.append(m.TeamMember(user_id=user_obj.id, role=m.TeamRoles.MEMBER))
        team_obj = await teams_service.update(item_id=team_id, data=team_obj)
        return teams_service.to_schema(schema_type=Team, data=team_obj)

    @post(operation_id="RemoveMemberFromTeam", path=urls.TEAM_REMOVE_MEMBER)
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(title="Team ID", description="The team to delete."),
    ) -> Team:
        """Revoke a members access to a team."""
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
        return teams_service.to_schema(schema_type=Team, data=team_obj)
