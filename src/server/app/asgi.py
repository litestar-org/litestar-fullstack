# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from starlite import Provide, Starlite

from app import domain
from app.lib import plugins

__all__ = ["run_app"]

dependencies = {"current_user": Provide(domain.dependencies.provide_user)}


def run_app() -> Starlite:
    """Create ASGI application."""
    return Starlite(
        route_handlers=[*domain.routes],
        dependencies=dependencies,
        on_app_init=[plugins.saqlalchemy, domain.security.auth.on_app_init],
    )
