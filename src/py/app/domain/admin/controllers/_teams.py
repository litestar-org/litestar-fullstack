"""Admin Teams Controller."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar import Controller, delete, get, patch
from litestar.di import Provide

from app.db import models as m
from app.domain.accounts.guards import requires_superuser
from app.domain.admin.dependencies import provide_audit_log_service
from app.domain.admin.schemas import AdminTeamDetail, AdminTeamList, AdminTeamSummary, AdminTeamUpdate
from app.domain.teams.dependencies import provide_teams_service

if TYPE_CHECKING:
    from uuid import UUID

    from litestar import Request
    from litestar.security.jwt import Token

    from app.domain.admin.services import AuditLogService
    from app.domain.teams.services import TeamService


class AdminTeamsController(Controller):
    """Admin team management endpoints."""

    tags = ["Admin"]
    path = "/api/admin/teams"
    guards = [requires_superuser]
    dependencies = {
        "teams_service": Provide(provide_teams_service),
        "audit_service": Provide(provide_audit_log_service),
    }

    @get(operation_id="AdminListTeams", path="/")
    async def list_teams(
        self,
        request: Request[m.User, Token, Any],
        teams_service: TeamService,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminTeamList:
        """List all teams with pagination.

        Args:
            request: Request with authenticated superuser
            teams_service: Team service
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated team list
        """
        all_teams = await teams_service.list()
        total = len(all_teams)

        # Manual pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_teams = all_teams[start:end]

        items = [
            AdminTeamSummary(
                id=t.id,
                name=t.name,
                slug=t.slug,
                member_count=len(t.members) if t.members else 0,
                is_active=True,  # Add is_active to Team model if needed
                created_at=t.created_at,
            )
            for t in paginated_teams
        ]

        return AdminTeamList(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
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

        # Find owner email
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
            is_active=True,  # Add is_active to Team model if needed
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

        # Build update dict from non-UNSET values
        update_data: dict[str, Any] = {}
        for field in ("name", "description", "is_active"):
            value = getattr(data, field)
            if value is not msgspec.UNSET:
                update_data[field] = value

        team = await teams_service.update(item_id=team_id, data=m.Team(**update_data), auto_commit=True)

        # Log the action
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

        # Find owner email
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
            is_active=True,
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
    ) -> dict[str, str]:
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

        # Log the action
        await audit_service.log_action(
            action="admin.team.delete",
            actor_id=request.user.id,
            actor_email=request.user.email,
            target_type="team",
            target_id=str(team_id),
            target_label=team_name,
            request=request,
        )

        return {"message": f"Team {team_name} deleted successfully"}
