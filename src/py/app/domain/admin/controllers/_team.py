"""Admin Teams SecureController."""

from typing import Annotated, Any, ClassVar
from uuid import UUID

from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service.pagination import OffsetPagination
from litestar import Request, delete, get, patch
from litestar.di import Provide
from litestar.params import Dependency
from litestar_security import AuthenticationPolicy, CurrentUser, SecureController, required, requires_role

from app.db import models as m
from app.domain.admin.deps import provide_audit_log_service
from app.domain.admin.schemas import AdminTeamDetail, AdminTeamSummary, AdminTeamUpdate
from app.domain.admin.services import AuditLogService
from app.domain.teams.deps import TeamFilterSet, create_filter_dependencies, provide_teams_service
from app.domain.teams.services import TeamService
from app.lib.schema import Message


class AdminTeamsController(SecureController):
    """Superuser team administration endpoints."""

    path = "/api/admin/teams"
    tags = ["Admin"]
    auth: ClassVar[AuthenticationPolicy] = required("session")
    guards = [requires_role("superuser")]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "audit_service": Provide(provide_audit_log_service),
    } | create_filter_dependencies(TeamFilterSet)

    @get(operation_id="AdminListTeams", path="/")
    async def list_teams(
        self,
        teams_service: TeamService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AdminTeamSummary]:
        """List all teams with filtering and pagination.

        Returns:
            Paginated team summaries.
        """
        teams, total = await teams_service.get_many_and_count(*filters)
        return teams_service.to_schema(teams, total, filters, schema_type=AdminTeamSummary)

    @get(operation_id="AdminGetTeam", path="/{team_id:uuid}")
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: UUID,
    ) -> AdminTeamDetail:
        """Get detailed team information.

        Returns:
            Detailed team record.
        """
        team = await teams_service.get(team_id)
        return teams_service.to_schema(team, schema_type=AdminTeamDetail)

    @patch(operation_id="AdminUpdateTeam", path="/{team_id:uuid}")
    async def update_team(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        teams_service: TeamService,
        audit_service: AuditLogService,
        team_id: UUID,
        data: AdminTeamUpdate,
    ) -> AdminTeamDetail:
        """Update team attributes as an administrator.

        Returns:
            Updated team details.
        """
        changes = data.to_dict()
        changed_fields = list(changes)
        team = await teams_service.update(item_id=team_id, data=changes, auto_commit=True)
        await audit_service.log_admin_team_update(
            actor_id=current_user.id,
            actor_email=current_user.email,
            team_id=team_id,
            team_name=team.name,
            changes=changed_fields,
            request=request,
        )
        return teams_service.to_schema(team, schema_type=AdminTeamDetail)

    @delete(operation_id="AdminDeleteTeam", path="/{team_id:uuid}", status_code=200)
    async def delete_team(
        self,
        request: Request[Any, Any, Any],
        current_user: CurrentUser[m.User],
        teams_service: TeamService,
        audit_service: AuditLogService,
        team_id: UUID,
    ) -> Message:
        """Delete a team as an administrator.

        Returns:
            Confirmation message for the deleted team.
        """
        team = await teams_service.get(team_id)
        team_name = team.name
        await teams_service.delete(team.id, auto_commit=True)
        await audit_service.log_admin_team_delete(
            actor_id=current_user.id,
            actor_email=current_user.email,
            team_id=team_id,
            team_name=team_name,
            request=request,
        )
        return Message(message=f"Team {team_name} deleted successfully")
