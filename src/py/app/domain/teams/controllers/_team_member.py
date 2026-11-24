"""Team Member SecureController."""

from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError
from litestar import delete, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import HTTP_202_ACCEPTED
from litestar_security import AuthenticationPolicy, SecureController, required

from app.db import models as m
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
        """Add an existing user to the team."""
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
            },
            auto_commit=True,
        )
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(team_obj, schema_type=Team)

    @delete(operation_id="RemoveMemberFromTeam", path="", status_code=HTTP_202_ACCEPTED)
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Revoke a member's access to a team while protecting the sole team owner."""
        user_obj = await users_service.get_one(email=data.user_name)
        membership = await team_members_service.get_one_or_none(team_id=team_id, user_id=user_obj.id)
        if membership is None:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        if membership.is_owner:
            owner_count = await team_members_service.count(
                m.TeamMember.team_id == team_id,
                m.TeamMember.is_owner.is_(True),
            )
            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the sole team owner without transferring ownership",
                )
        await team_members_service.delete(membership.id, auto_commit=True)
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(team_obj, schema_type=Team)

    @patch(operation_id="UpdateTeamMember", path="/{user_id:uuid}")
    async def update_team_member(
        self,
        team_members_service: TeamMemberService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
        user_id: Annotated[UUID, Parameter(title="User ID", description="The user to update.")],
        data: TeamMemberUpdate,
    ) -> TeamMember:
        """Update a team member's role."""
        membership = await team_members_service.get_one_or_none(team_id=team_id, user_id=user_id)
        if membership is None:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        if membership.is_owner and data.role != m.TeamRoles.ADMIN:
            raise HTTPException(status_code=400, detail="Cannot demote a team owner from ADMIN role")
        updated = await team_members_service.update(
            item_id=membership.id,
            data={"role": data.role},
            auto_commit=True,
        )
        return team_members_service.to_schema(updated, schema_type=TeamMember)
