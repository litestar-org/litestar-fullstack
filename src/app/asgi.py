# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING

from starlite import Provide, Starlite

from app import domain
from app.domain.web.vite import template_config
from app.lib import plugins, static_files

if TYPE_CHECKING:
    from starlite import Request
    from starlite.contrib.jwt import Token

    from app.domain.accounts.models import User

__all__ = ["run_app"]


def run_app() -> Starlite:
    """Create ASGI application."""
    return Starlite(
        route_handlers=[*domain.routes],
        dependencies=dependencies,
        on_app_init=[plugins.saqlalchemy, domain.security.auth.on_app_init],
        static_files_config=static_files.config,
        template_config=template_config,
    )


async def _provide_user(request: Request[User, Token]) -> User:
    return request.user


dependencies = {"current_user": Provide(_provide_user)}
"""Adds current_user as optional injected dependency for all connections."""
