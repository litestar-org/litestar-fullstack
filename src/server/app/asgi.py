# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from starlite import Starlite

from app import domain
from app.lib import plugins

__all__ = ["run_app"]


def run_app() -> Starlite:
    """Create ASGI application."""
    return Starlite(route_handlers=[*domain.routes], on_app_init=[plugins.saqlalchemy])
