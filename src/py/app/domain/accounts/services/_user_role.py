from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m


class UserRoleService(service.SQLAlchemyAsyncRepositoryService[m.UserRole]):
    """Handles database operations for user roles."""

    class Repo(repository.SQLAlchemyAsyncRepository[m.UserRole]):
        """User Role SQLAlchemy Repository."""

        model_type = m.UserRole

    repository_type = Repo
