"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.accounts.controllers import AccessController, UserController, UserRoleController
from app.domain.system.controllers import SystemController
from app.domain.tags.controllers import TagController
from app.domain.teams.controllers import TeamController, TeamMemberController
from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


route_handlers: list[ControllerRouterHandler] = [
    AccessController,
    UserController,
    TeamController,
    UserRoleController,
    #  TeamInvitationController,
    TeamMemberController,
    TagController,
    SystemController,
    WebController,
]
