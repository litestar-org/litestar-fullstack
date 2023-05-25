"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.domain import urls
from app.domain.accounts.guards import requires_active_user
from app.domain.teams import schemas
from app.domain.teams.dependencies import provides_teams_service
from app.domain.teams.guards import requires_team_admin, requires_team_membership

if TYPE_CHECKING:
    from uuid import UUID

    from litestar.pagination import OffsetPagination

    from app.domain.accounts.models import User
    from app.domain.teams.services import TeamService
    from app.lib.dependencies import FilterTypes

__all__ = ["TeamController"]


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provides_teams_service)}
    guards = [requires_active_user]

    @get(
        operation_id="ListTeams",
        name="teams:list",
        summary="List Teams",
        path=urls.TEAM_LIST,
    )
    async def list_teams(
        self,
        teams_service: TeamService,
        current_user: User,
        filters: list[FilterTypes] = Dependency(skip_validation=True),
    ) -> OffsetPagination[schemas.Team]:
        """List teams that your account can access.."""
        if current_user.is_superuser:
            results, total = await teams_service.list_and_count(*filters)
        else:
            results, total = await teams_service.get_user_teams(*filters, user_id=current_user.id)
        return teams_service.to_dto(schemas.Team, results, total, *filters)

    @post(
        operation_id="CreateTeam",
        name="teams:create",
        summary="Create a new team.",
        path=urls.TEAM_CREATE,
    )
    async def create_team(
        self,
        teams_service: TeamService,
        current_user: User,
        data: schemas.TeamCreate,
    ) -> schemas.Team:
        """Create a new team."""
        obj = data.dict(exclude_unset=True, by_alias=False, exclude_none=True)
        obj.update({"owner_id": current_user.id})
        db_obj = await teams_service.create(obj)
        return teams_service.to_dto(schemas.Team, db_obj)

    @get(
        operation_id="GetTeam",
        name="teams:get",
        guards=[requires_team_membership],
        summary="Retrieve the details of a team.",
        path=urls.TEAM_DETAIL,
    )
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to retrieve.",
        ),
    ) -> schemas.Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        return teams_service.to_dto(schemas.Team, db_obj)

    @patch(
        operation_id="UpdateTeam",
        name="teams:update",
        guards=[requires_team_admin],
        path=urls.TEAM_UPDATE,
    )
    async def update_team(
        self,
        data: schemas.TeamUpdate,
        teams_service: TeamService,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to update.",
        ),
    ) -> schemas.Team:
        """Update a migration team."""
        db_obj = await teams_service.update(
            team_id,
            data.dict(exclude_unset=True, by_alias=False, exclude_none=True),
        )
        return teams_service.to_dto(schemas.Team, db_obj)

    @delete(
        operation_id="DeleteTeam",
        name="teams:delete",
        guards=[requires_team_admin],
        summary="Remove Team",
        path=urls.TEAM_DELETE,
    )
    async def delete_team(
        self,
        teams_service: TeamService,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to delete.",
        ),
    ) -> None:
        """Delete a team."""
        _ = await teams_service.delete(team_id)
