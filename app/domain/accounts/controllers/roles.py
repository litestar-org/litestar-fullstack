"""Role Routes."""

from __future__ import annotations

from litestar import Controller

from app.domain.accounts.guards import requires_superuser


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [requires_superuser]
