"""Team domain Advanced Alchemy service and filter providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import (
    FilterConfig,
    create_filter_dependencies,
    create_service_provider,
)
from advanced_alchemy.filters import FilterSet
from sqlalchemy.orm import joinedload, selectinload

from app.db import models as m
from app.domain.teams.services import (
    ALREADY_A_MEMBER,
    TeamInvitationService,
    TeamMemberService,
    TeamService,
    TeamServices,
)

if TYPE_CHECKING:
    from collections.abc import Collection

TEAM_LOAD_OPTIONS = [
    selectinload(m.Team.tags),
    selectinload(m.Team.members).options(joinedload(m.TeamMember.user, innerjoin=True)),
]


class TeamFilterSet(FilterSet[m.Team]):
    """Typed filter set for querying teams."""

    model_type: ClassVar[type[m.Team]] = m.Team
    search_fields: ClassVar[Collection[str]] = ("name",)
    sort_fields: ClassVar[Collection[str]] = ("name", "slug", "created_at", "updated_at")
    config: ClassVar[FilterConfig] = {
        "id_filter": UUID,
        "pagination_type": "limit_offset",
        "pagination_size": 20,
        "created_at": True,
        "updated_at": True,
        "sort_field": "name",
        "sort_order": "asc",
    }


class TeamInvitationFilterSet(FilterSet[m.TeamInvitation]):
    """Typed filter set for querying team invitations."""

    model_type: ClassVar[type[m.TeamInvitation]] = m.TeamInvitation
    search_fields: ClassVar[Collection[str]] = ("email",)
    sort_fields: ClassVar[Collection[str]] = ("created_at", "updated_at", "email")
    config: ClassVar[FilterConfig] = {
        "pagination_type": "limit_offset",
        "pagination_size": 20,
        "created_at": True,
        "updated_at": True,
        "sort_field": "created_at",
        "sort_order": "desc",
    }


provide_teams_service = create_service_provider(
    TeamService,
    load=TEAM_LOAD_OPTIONS,
    error_messages={"duplicate_key": "This team already exists.", "integrity": "Team operation failed."},
)

provide_team_invitations_service = create_service_provider(
    TeamInvitationService,
    load=[selectinload(m.TeamInvitation.team)],
    error_messages={"duplicate_key": "Invitation already exists.", "integrity": "Team invitation operation failed."},
)

provide_team_members_service = create_service_provider(
    TeamMemberService,
    load=[
        selectinload(m.TeamMember.team),
        selectinload(m.TeamMember.user),
    ],
    error_messages={"duplicate_key": ALREADY_A_MEMBER, "integrity": "Team member operation failed."},
)

provide_team_services = create_service_provider(TeamServices)

__all__ = (
    "TEAM_LOAD_OPTIONS",
    "TeamFilterSet",
    "TeamInvitationFilterSet",
    "create_filter_dependencies",
    "provide_team_invitations_service",
    "provide_team_members_service",
    "provide_team_services",
    "provide_teams_service",
)
