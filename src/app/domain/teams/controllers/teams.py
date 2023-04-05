"""User Account Controllers."""
from __future__ import annotations

from starlite import Controller
from starlite.di import Provide

from app.domain.teams.dependencies import provides_teams_service

__all__ = ["TeamController", "provides_teams_service"]


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = {"teams_service": Provide(provides_teams_service)}
