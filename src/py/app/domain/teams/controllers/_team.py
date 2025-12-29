"""Team Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from sqlalchemy import select

from app.db import models as m
from app.domain.teams.schemas import Team, TeamCreate, TeamUpdate
from app.domain.teams.services import TeamService
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = create_service_dependencies(
        TeamService,
        key="teams_service",
        load=[m.Team.tags, m.Team.members],
        filters={
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(component="team/list", operation_id="ListTeams", path="/api/teams")
    async def list_teams(
        self,
        teams_service: TeamService,
        current_user: m.User,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams that your account can access.

        Args:
            teams_service: Team Service
            current_user: Current User
            filters: Filters

        Returns:
            OffsetPagination[Team]
        """
        if not teams_service.can_view_all(current_user):
            results, total = await teams_service.list_and_count(
                *filters,
                m.Team.id.in_(
                    select(m.TeamMember.team_id)
                    .where(m.TeamMember.user_id == current_user.id)
                    .scalar_subquery()
                ),
            )
        else:
            results, total = await teams_service.list_and_count(*filters)
        return teams_service.to_schema(results, total, filters, schema_type=Team)

    @post(operation_id="CreateTeam", path="/api/teams")
    async def create_team(self, teams_service: TeamService, current_user: m.User, data: TeamCreate) -> Team:
        """Create a new team.

        Args:
            teams_service: Team Service
            current_user: Current User
            data: Team Create

        Returns:
            Team
        """
        obj = data.to_dict()
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj)
        return teams_service.to_schema(db_obj, schema_type=Team)

    @get(operation_id="GetTeam", path="/api/teams/{team_id:uuid}")
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to retrieve.")],
    ) -> Team:
        """Get details about a team.

        Args:
            teams_service: Team Service
            team_id: Team ID

        Returns:
            Team
        """
        db_obj = await teams_service.get(team_id)
        return teams_service.to_schema(db_obj, schema_type=Team)

    @patch(operation_id="UpdateTeam", path="/api/teams/{team_id:uuid}")
    async def update_team(
        self,
        data: TeamUpdate,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Update a team.

        Args:
            data: Team Update
            teams_service: Team Service
            team_id: Team ID

        Returns:
            Team
        """
        await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
        )

        fresh_obj = await teams_service.get_one(id=team_id)
        return teams_service.to_schema(fresh_obj, schema_type=Team)

    @delete(operation_id="DeleteTeam", path="/api/teams/{team_id:uuid}")
    async def delete_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> None:
        """Delete a team.

        Args:
            teams_service: Team Service
            team_id: Team ID
        """
        _ = await teams_service.delete(team_id)
