"""User Account Controllers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.params import Dependency, Parameter
from msgspec.structs import asdict

from app.config import constants
from app.domain import urls
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.dependencies import provide_teams_service
from app.domain.teams.dtos import Team, TeamCreate, TeamUpdate
from app.domain.teams.guards import requires_team_admin, requires_team_membership
from app.domain.teams.services import TeamService

if TYPE_CHECKING:
    from litestar.pagination import OffsetPagination
    from uuid_utils import UUID

    from app.db.models import User
    from app.lib.dependencies import FilterTypes


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provide_teams_service)}
    guards = [requires_active_user]
    signature_namespace = {
        "Dependency": Dependency,
        "Parameter": Parameter,
        "TeamService": TeamService,
        "TeamUpdate": TeamUpdate,
        "TeamCreate": TeamCreate,
        "Team": Team,
    }

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
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams that your account can access.."""
        show_all = bool(
            current_user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in current_user.roles
                if assigned_role.role.name in {constants.SUPERUSER_ACCESS_ROLE}
            ),
        )
        if show_all:
            results, total = await teams_service.list_and_count(*filters)
        else:
            results, total = await teams_service.get_user_teams(*filters, user_id=current_user.id)
        return teams_service.to_schema(Team, results, total, *filters)

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
        data: TeamCreate,
    ) -> Team:
        """Create a new team."""
        obj = asdict(data)
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj)
        return teams_service.to_schema(Team, db_obj)

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
        team_id: Annotated[
            UUID,
            Parameter(
                title="Team ID",
                description="The team to retrieve.",
            ),
        ],
    ) -> Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        return teams_service.to_schema(Team, db_obj)

    @patch(
        operation_id="UpdateTeam",
        name="teams:update",
        guards=[requires_team_admin],
        path=urls.TEAM_UPDATE,
    )
    async def update_team(
        self,
        data: TeamUpdate,
        teams_service: TeamService,
        team_id: Annotated[
            UUID,
            Parameter(
                title="Team ID",
                description="The team to update.",
            ),
        ],
    ) -> Team:
        """Update a migration team."""
        db_obj = await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
        )
        return teams_service.to_schema(Team, db_obj)

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
        team_id: Annotated[
            UUID,
            Parameter(
                title="Team ID",
                description="The team to delete.",
            ),
        ],
    ) -> None:
        """Delete a team."""
        _ = await teams_service.delete(team_id)
