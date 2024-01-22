"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.accounts.controllers import AccessController, UserController
from app.domain.system.controllers import SystemController
from app.domain.tags.controllers import TagController
from app.domain.teams.controllers import TeamController
from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


routes: list[ControllerRouterHandler] = [
    AccessController,
    UserController,
    TeamController,
    #  TeamInvitationController,
    # TeamMemberController,
    TagController,
    SystemController,
    WebController,
]
