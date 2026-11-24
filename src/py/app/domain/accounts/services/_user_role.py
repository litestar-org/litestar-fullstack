"""User-role assignment database service."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import service

from app.db import models as m


class UserRoleService(service.SQLAlchemyAsyncRepositoryService[m.UserRole]):
    """Handles database operations for user role assignments using an inferred repository."""
