"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter

from app.domain import urls
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.dependencies import provides_teams_service
from app.domain.teams.dtos import TeamCreate, TeamCreateDTO, TeamDTO, TeamUpdate, TeamUpdateDTO
from app.domain.teams.guards import requires_team_admin, requires_team_membership

if TYPE_CHECKING:
    from uuid import UUID

    from litestar.dto import DTOData
    from litestar.pagination import OffsetPagination

    from app.domain.accounts.models import User
    from app.domain.teams.models import Team
    from app.domain.teams.services import TeamService
    from app.lib.dependencies import FilterTypes

__all__ = ["TeamController"]


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provides_teams_service)}
    guards = [requires_active_user]
    return_dto = TeamDTO
    signature_namespace = {"TeamUpdate": TeamUpdate, "TeamCreate": TeamCreate}

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
    ) -> OffsetPagination[Team]:
        """List teams that your account can access.."""
        if current_user.is_superuser:
            results, total = await teams_service.list_and_count(*filters)
        else:
            results, total = await teams_service.get_user_teams(*filters, user_id=current_user.id)
        return teams_service.to_dto(results, total, *filters)

    @post(
        operation_id="CreateTeam",
        name="teams:create",
        summary="Create a new team.",
        path=urls.TEAM_CREATE,
        dto=TeamCreateDTO,
    )
    async def create_team(
        self,
        teams_service: TeamService,
        current_user: User,
        data: DTOData[TeamCreate],
    ) -> Team:
        """Create a new team."""
        obj = data.create_instance().__dict__
        obj.update({"owner_id": current_user.id})
        db_obj = await teams_service.create(obj)
        return teams_service.to_dto(db_obj)

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
    ) -> Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        return teams_service.to_dto(db_obj)

    @patch(
        operation_id="UpdateTeam",
        name="teams:update",
        guards=[requires_team_admin],
        path=urls.TEAM_UPDATE,
        dto=TeamUpdateDTO,
    )
    async def update_team(
        self,
        data: DTOData[TeamUpdate],
        teams_service: TeamService,
        team_id: UUID = Parameter(
            title="Team ID",
            description="The team to update.",
        ),
    ) -> Team:
        """Update a migration team."""
        db_obj = await teams_service.update(
            item_id=team_id,
            data=data.create_instance().__dict__,
        )
        return teams_service.to_dto(db_obj)

    @delete(
        operation_id="DeleteTeam",
        name="teams:delete",
        guards=[requires_team_admin],
        summary="Remove Team",
        path=urls.TEAM_DELETE,
        return_dto=None,
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
