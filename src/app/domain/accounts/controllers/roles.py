"""Role Routes."""

from __future__ import annotations

from uuid import UUID

from litestar import Controller

from app.domain.accounts.guards import requires_superuser
from app.lib.deps import create_filter_dependencies


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""

    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {
        "filters": create_filter_dependencies(
            {
                "id_filter": UUID,
                "created_at": True,
                "updated_at": True,
                "pagination_size": 5,
                "sort_field": "name",
                "search_fields": ["name", "slug"],
            },
        ),
    }
