"""Role Routes."""

from __future__ import annotations

from litestar import Controller

from app.server import security


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [security.requires_superuser]
