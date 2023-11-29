"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar.dto import DTOData
from litestar.pagination import OffsetPagination
from litestar.security.jwt import OAuth2Login
from litestar.types import TypeEncodersMap

from app.domain.accounts.dtos import AccountLogin, AccountRegister, UserCreate, UserUpdate
from app.domain.accounts.models import User
from app.domain.analytics.dtos import NewUsersByWeek
from app.domain.tags.models import Tag
from app.domain.teams.models import Team

from . import accounts, analytics, openapi, plugins, security, system, tags, teams, urls, web

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from litestar.types import ControllerRouterHandler


routes: list[ControllerRouterHandler] = [
    accounts.controllers.AccessController,
    accounts.controllers.AccountController,
    teams.controllers.TeamController,
    # teams.controllers.TeamInvitationController,
    # teams.controllers.TeamMemberController,
    analytics.controllers.StatsController,
    tags.controllers.TagController,
    system.controllers.SystemController,
    web.controllers.WebController,
]

__all__ = [
    "system",
    "accounts",
    "teams",
    "web",
    "urls",
    "tags",
    "security",
    "routes",
    "openapi",
    "analytics",
    "plugins",
    "signature_namespace",
]

signature_namespace: Mapping[str, Any] = {
    "UUID": UUID,
    "User": User,
    "Team": Team,
    "UserCreate": UserCreate,
    "UserUpdate": UserUpdate,
    "AccountLogin": AccountLogin,
    "AccountRegister": AccountRegister,
    "NewUsersByWeek": NewUsersByWeek,
    "Tag": Tag,
    "OAuth2Login": OAuth2Login,
    "OffsetPagination": OffsetPagination,
    "UserService": accounts.services.UserService,
    "TeamService": teams.services.TeamService,
    "TagService": tags.services.TagService,
    "TeamInvitationService": teams.services.TeamInvitationService,
    "TeamMemberService": teams.services.TeamMemberService,
    "DTOData": DTOData,
    "TypeEncodersMap": TypeEncodersMap,
}
