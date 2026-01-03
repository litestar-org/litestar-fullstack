"""Admin Teams Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from litestar import Controller, delete, get, patch
from litestar.di import Provide
from litestar.params import Dependency
from sqlalchemy.orm import joinedload, selectinload

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.deps import provide_audit_log_service
from app.domain.admin.schemas import AdminTeamDetail, AdminTeamSummary, AdminTeamUpdate
from app.domain.teams.services import TeamService
from app.lib.deps import create_service_dependencies
from app.lib.schema import Message

if TYPE_CHECKING:
    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar import Request
    from litestar.security.jwt import Token

    from app.domain.admin.services import AuditLogService


class AdminTeamsController(Controller):
    """Admin team management endpoints."""

    tags = ["Admin"]
    path = "/api/admin/teams"
    guards = [requires_superuser]
    dependencies = create_service_dependencies(
        TeamService,
        key="teams_service",
        load=[selectinload(m.Team.members).options(joinedload(m.TeamMember.user, innerjoin=True))],
        error_messages={"duplicate_key": "This team already exists.", "integrity": "Team operation failed."},
        filters={
            "id_filter": UUID,
            "search": "name",
            "pagination_type": "limit_offset",
            "pagination_size": 25,
            "created_at": True,
            "updated_at": True,
            "sort_field": "created_at",
            "sort_order": "desc",
        },
    ) | {
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="AdminListTeams", path="/")
    async def list_teams(
        self,
        request: Request[m.User, Token, Any],
        teams_service: TeamService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[AdminTeamSummary]:
        """List all teams with pagination.

        Args:
            request: Request with authenticated superuser
            teams_service: Team service
            filters: Filter and pagination parameters

        Returns:
            Paginated team list
        """
        results, total = await teams_service.list_and_count(*filters)
        items = [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "member_count": len(t.members) if t.members else 0,
                "is_active": t.is_active,
                "created_at": t.created_at,
            }
            for t in results
        ]
        return teams_service.to_schema(
            data=items,
            total=total,
            filters=filters,
            schema_type=AdminTeamSummary,
        )

    @get(operation_id="AdminGetTeam", path="/{team_id:uuid}")
    async def get_team(
        self,
        request: Request[m.User, Token, Any],
        teams_service: TeamService,
        team_id: UUID,
    ) -> AdminTeamDetail:
        """Get detailed team information.

        Args:
            request: Request with authenticated superuser
            teams_service: Team service
            team_id: ID of team to retrieve

        Returns:
            Detailed team information
        """
        team = await teams_service.get(team_id)

        return teams_service.to_schema(
            data={
                "id": team.id,
                "name": team.name,
                "slug": team.slug,
                "description": team.description,
                "is_active": team.is_active,
                "member_count": len(team.members) if team.members else 0,
                "owner_email": next(
                    (member.user.email for member in team.members if member.is_owner and member.user),
                    None,
                )
                if team.members
                else None,
                "created_at": team.created_at,
                "updated_at": team.updated_at,
            },
            schema_type=AdminTeamDetail,
        )

    @patch(operation_id="AdminUpdateTeam", path="/{team_id:uuid}")
    async def update_team(
        self,
        request: Request[m.User, Token, Any],
        teams_service: TeamService,
        audit_service: AuditLogService,
        team_id: UUID,
        data: AdminTeamUpdate,
    ) -> AdminTeamDetail:
        """Update team as admin.

        Args:
            request: Request with authenticated superuser
            teams_service: Team service
            audit_service: Audit log service
            team_id: ID of team to update
            data: Update payload

        Returns:
            Updated team details
        """
        import msgspec

        update_data: dict[str, Any] = {}
        for field in ("name", "description", "is_active"):
            value = getattr(data, field)
            if value is not msgspec.UNSET:
                update_data[field] = value

        team = await teams_service.update(item_id=team_id, data=update_data, auto_commit=True)

        await audit_service.log_admin_team_update(
            actor_id=request.user.id,
            actor_email=request.user.email,
            team_id=team_id,
            team_name=team.name,
            changes=list(update_data.keys()),
            request=request,
        )

        return teams_service.to_schema(
            data={
                "id": team.id,
                "name": team.name,
                "slug": team.slug,
                "description": team.description,
                "is_active": team.is_active,
                "member_count": len(team.members) if team.members else 0,
                "owner_email": next(
                    (member.user.email for member in team.members if member.is_owner and member.user),
                    None,
                )
                if team.members
                else None,
                "created_at": team.created_at,
                "updated_at": team.updated_at,
            },
            schema_type=AdminTeamDetail,
        )

    @delete(operation_id="AdminDeleteTeam", path="/{team_id:uuid}", status_code=200)
    async def delete_team(
        self,
        request: Request[m.User, Token, Any],
        teams_service: TeamService,
        audit_service: AuditLogService,
        team_id: UUID,
    ) -> Message:
        """Delete a team (admin only).

        Args:
            request: Request with authenticated superuser
            teams_service: Team service
            audit_service: Audit log service
            team_id: ID of team to delete

        Returns:
            Success message
        """
        team = await teams_service.get(team_id)
        team_name = team.name

        await teams_service.delete(team_id)

        await audit_service.log_admin_team_delete(
            actor_id=request.user.id,
            actor_email=request.user.email,
            team_id=team_id,
            team_name=team_name,
            request=request,
        )

        return Message(message=f"Team {team_name} deleted successfully")
