"""Role database service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import IntegrityError
from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m
from app.domain.accounts.services._statements import is_constraint_violation
from app.lib import constants

if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT


class RoleService(service.SQLAlchemyAsyncRepositoryService[m.Role]):
    """Handles database operations for roles with automatic unique slug generation."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Role]):
        """Role SQLAlchemy slug repository."""

        model_type = m.Role

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Role]) -> ModelDictT[m.Role]:
        """Populate a unique slug from the role name when creating a new role.

        Returns:
            Prepared role payload with a unique slug populated when omitted.
        """
        data = service.schema_dump(data)
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def ensure_default_access_role(self) -> m.Role:
        """Load the default access role, creating it inside the caller's transaction when it is missing.

        Sign-ups racing on a database without the role all try to create it. The insert runs in a savepoint,
        so a caller that loses to the role's unique constraint keeps its transaction and uses the winner's role.

        Returns:
            The stored default access role.

        Raises:
            IntegrityError: If the database fails for a reason other than a violated constraint.
        """
        default_access_role = await self.get_one_or_none(name=constants.DEFAULT_ACCESS_ROLE)
        if default_access_role is not None:
            return default_access_role
        try:
            async with self.repository.session.begin_nested():
                return await self.create(
                    {"name": constants.DEFAULT_ACCESS_ROLE, "description": constants.DEFAULT_ACCESS_ROLE_DESCRIPTION}
                )
        except IntegrityError as error:
            if not is_constraint_violation(error):
                raise
        return await self.get_one(name=constants.DEFAULT_ACCESS_ROLE)
