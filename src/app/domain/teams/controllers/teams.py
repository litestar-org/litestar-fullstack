"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from litestar import Controller, Request, delete, get, patch, post
from litestar.di import Provide
from litestar.plugins.flash import flash
from litestar_vite.inertia import InertiaRedirect
from sqlalchemy import select

from app.db.models import Team as TeamModel
from app.db.models import User as UserModel
from app.db.models.team_member import TeamMember as TeamMemberModel
from app.domain.accounts.guards import requires_active_user
from app.domain.teams.dependencies import provide_teams_service
from app.domain.teams.guards import requires_team_admin, requires_team_membership, requires_team_ownership
from app.domain.teams.schemas import Team, TeamCreate, TeamUpdate
from app.domain.teams.services import TeamService

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar.params import Dependency, Parameter

    from app.lib.dependencies import FilterTypes


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provide_teams_service)}
    guards = [requires_active_user]
    signature_namespace = {
        "TeamService": TeamService,
        "TeamUpdate": TeamUpdate,
        "TeamCreate": TeamCreate,
    }

    @get(
        component="team/list",
        name="teams.list",
        operation_id="ListTeams",
        path="/teams/",
    )
    async def list_teams(
        self,
        teams_service: TeamService,
        current_user: UserModel,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams that your account can access.."""
        if not teams_service.can_view_all(current_user):
            filters.append(
                TeamModel.id.in_(select(TeamMemberModel.team_id).where(TeamMemberModel.user_id == current_user.id)),  # type: ignore[arg-type]
            )
        results, total = await teams_service.list_and_count(*filters)
        return teams_service.to_schema(data=results, total=total, schema_type=Team, filters=filters)

    @post(
        name="teams.add",
        operation_id="CreateTeam",
        summary="Create a new team.",
        path="/teams/",
    )
    async def create_team(
        self,
        request: Request,
        teams_service: TeamService,
        current_user: UserModel,
        data: TeamCreate,
    ) -> InertiaRedirect:
        """Create a new team."""
        obj = data.to_dict()
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj)
        flash(request, f'Successfully created team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.show", team_id=db_obj.id))

    @get(
        component="team/show",
        name="teams.show",
        operation_id="GetTeam",
        guards=[requires_team_membership],
        path="/teams/{team_id:uuid}/",
    )
    async def get_team(
        self,
        request: Request,
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
        request.session.update({"currentTeam": {"teamId": db_obj.id, "teamName": db_obj.name}})
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @patch(
        component="team/edit",
        name="teams.edit",
        operation_id="UpdateTeam",
        guards=[requires_team_admin],
        path="/teams/{team_id:uuid}/",
    )
    async def update_team(
        self,
        request: Request,
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
        request.session.update({"currentTeam": {"teamId": db_obj.id, "teamName": db_obj.name}})
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @delete(
        name="teams.remove",
        operation_id="DeleteTeam",
        guards=[requires_team_ownership],
        path="/teams/{team_id:uuid}/",
        status_code=303,  # This is the correct inertia redirect code
    )
    async def delete_team(
        self,
        request: Request,
        teams_service: TeamService,
        team_id: Annotated[
            UUID,
            Parameter(title="Team ID", description="The team to delete."),
        ],
    ) -> InertiaRedirect:
        """Delete a team."""
        request.session.pop("currentTeam")
        db_obj = await teams_service.delete(team_id)
        flash(request, f'Removed team "{db_obj.name}".', category="info")
        return InertiaRedirect(request, request.url_for("teams.list"))
