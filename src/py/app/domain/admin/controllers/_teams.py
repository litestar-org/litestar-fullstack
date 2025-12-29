"""Admin Teams Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar import Controller, delete, get, patch
from litestar.di import Provide
from litestar.params import Dependency
from sqlalchemy.orm import joinedload, selectinload

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_log_service
from app.domain.admin.schemas import AdminTeamDetail, AdminTeamSummary, AdminTeamUpdate
from app.domain.teams.services import TeamService
from app.schemas.base import Message
from app.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from litestar import Request
    from litestar.security.jwt import Token

    from advanced_alchemy.filters import FilterTypes
    from advanced_alchemy.service.pagination import OffsetPagination

    from app.domain.admin.services import AuditLogService
    from app.domain.teams.services import TeamService


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

        owner_email = None
        if team.members:
            for member in team.members:
                if member.is_owner:
                    owner_email = member.user.email if member.user else None
                    break

        return AdminTeamDetail(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            is_active=team.is_active,
            member_count=len(team.members) if team.members else 0,
            owner_email=owner_email,
            created_at=team.created_at,
            updated_at=team.updated_at,
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

        team = await teams_service.update(item_id=team_id, data=m.Team(**update_data), auto_commit=True)

        await audit_service.log_action(
            action="admin.team.update",
            actor_id=request.user.id,
            actor_email=request.user.email,
            target_type="team",
            target_id=str(team_id),
            target_label=team.name,
            details={"changes": list(update_data.keys())},
            request=request,
        )

        owner_email = None
        if team.members:
            for member in team.members:
                if member.is_owner:
                    owner_email = member.user.email if member.user else None
                    break

        return AdminTeamDetail(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            is_active=team.is_active,
            member_count=len(team.members) if team.members else 0,
            owner_email=owner_email,
            created_at=team.created_at,
            updated_at=team.updated_at,
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

        await audit_service.log_action(
            action="admin.team.delete",
            actor_id=request.user.id,
            actor_email=request.user.email,
            target_type="team",
            target_id=str(team_id),
            target_label=team_name,
            request=request,
        )

        return Message(message=f"Team {team_name} deleted successfully")
