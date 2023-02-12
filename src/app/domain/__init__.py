"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import accounts, examples, security, teams, urls, web

if TYPE_CHECKING:
    from starlite.types import ControllerRouterHandler

routes: list[ControllerRouterHandler] = [examples.controllers.example_handler, accounts.controllers.AccessController]

__all__ = ["accounts", "examples", "teams", "web", "urls", "security", "routes"]
