"""Team SecureController."""

from typing import Annotated, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, any_of, required
from sqlalchemy import select

from app.db import models as m
from app.domain.accounts.security import requires_team_role
from app.domain.teams.deps import TeamFilterSet, create_filter_dependencies, provide_teams_service
from app.domain.teams.schemas import Team, TeamCreate, TeamUpdate
from app.domain.teams.services import TeamService


class TeamController(SecureController):
    """Handles team CRUD with snapshot-based team role authorization."""

    path = "/api/teams"
    tags = ["Teams"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    dependencies = {
        "teams_service": Provide(provide_teams_service),
    } | create_filter_dependencies(TeamFilterSet)

    @get(
        operation_id="ListTeams",
        path="",
        opt={"auth": any_of("session", "api-key")},
        mcp_resource="teams_list",
    )
    async def list_teams(
        self,
        teams_service: TeamService,
        current_user: CurrentUser[m.User],
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams accessible to the authenticated account."""
        if not teams_service.can_view_all(current_user):
            results, total = await teams_service.get_many_and_count(
                *filters,
                m.Team.id.in_(
                    select(m.TeamMember.team_id).where(m.TeamMember.user_id == current_user.id).scalar_subquery()
                ),
            )
        else:
            results, total = await teams_service.get_many_and_count(*filters)
        return teams_service.to_schema(results, total, filters, schema_type=Team)

    @post(operation_id="CreateTeam", path="")
    async def create_team(
        self,
        teams_service: TeamService,
        current_user: CurrentUser[m.User],
        data: TeamCreate,
    ) -> Team:
        """Create a new team owned by the authenticated user."""
        obj = data.to_dict()
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj, auto_commit=True)
        return teams_service.to_schema(db_obj, schema_type=Team)

    @get(
        operation_id="GetTeam",
        path="/{team_id:uuid}",
        guards=[requires_team_role("member")],
        opt={"auth": any_of("session", "api-key")},
        mcp_resource="team_detail",
        mcp_resource_template="app://teams/{team_id}",
    )
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to retrieve.")],
    ) -> Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        return teams_service.to_schema(db_obj, schema_type=Team)

    @patch(
        operation_id="UpdateTeam",
        path="/{team_id:uuid}",
        guards=[requires_team_role("admin")],
    )
    async def update_team(
        self,
        data: TeamUpdate,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Update team attributes, tags, or ownership."""
        await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
            auto_commit=True,
        )
        fresh_obj = await teams_service.get_one(id=team_id)
        return teams_service.to_schema(fresh_obj, schema_type=Team)

    @delete(
        operation_id="DeleteTeam",
        path="/{team_id:uuid}",
        guards=[requires_team_role("owner")],
    )
    async def delete_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> None:
        """Delete a team."""
        _ = await teams_service.delete(team_id, auto_commit=True)
