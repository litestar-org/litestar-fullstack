"""Role Routes."""
from __future__ import annotations

from litestar import Controller
from litestar.di import Provide

from app.domain.accounts.dependencies import provide_roles_service
from app.domain.accounts.guards import requires_superuser
from app.domain.accounts.services import RoleService


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {
        "roles_service": Provide(provide_roles_service),
    }
    signature_namespace = {"RoleService": RoleService}
