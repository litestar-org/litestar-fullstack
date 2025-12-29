from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.utils.text import slugify
from litestar.plugins.sqlalchemy import repository, service

from app.db import models as m
from app.lib import constants

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT


class TeamService(service.SQLAlchemyAsyncRepositoryService[m.Team]):
    """Team Service."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Team]):
        """Team Repository."""

        model_type = m.Team

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = service.schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner_and_tags(data, "create")

    async def to_model_on_update(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = service.schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner_and_tags(data, "update")

    async def to_model_on_upsert(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = service.schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner_and_tags(data, "upsert")

    @staticmethod
    def can_view_all(user: m.User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in user.roles
                if assigned_role.role.name == constants.SUPERUSER_ACCESS_ROLE
            ),
        )

    async def _populate_slug(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def _populate_with_owner_and_tags(
        self,
        data: ModelDictT[m.Team],
        operation: str | None,
    ) -> ModelDictT[m.Team]:
        if not service.is_dict(data):
            return data

        owner_id: UUID | None = data.pop("owner_id", None)
        owner: m.User | None = data.pop("owner", None)
        input_tags: list[str] | None = data.pop("tags", None)

        if operation == "create" and owner_id is None and owner is None:
            msg = "'owner_id' is required to create a team."
            raise RepositoryError(msg)

        data = await super().to_model(data)

        if operation == "create" and (owner or owner_id):
            owner_data: dict[str, Any] = {"user": owner} if owner else {"user_id": owner_id}
            data.members.append(m.TeamMember(**owner_data, role=m.TeamRoles.ADMIN, is_owner=True))

        if input_tags is not None:
            existing_tags = [tag.name for tag in data.tags]
            tags_to_remove = [tag for tag in data.tags if tag.name not in input_tags]
            tags_to_add = [tag for tag in input_tags if tag not in existing_tags]
            for tag_rm in tags_to_remove:
                data.tags.remove(tag_rm)
            data.tags.extend(
                [
                    await m.Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                    for tag_text in tags_to_add
                ],
            )

        if operation != "create" and (owner or owner_id):
            for member in data.members:
                if member.user_id == owner.id if owner is not None else owner_id and not member.is_owner:
                    member.is_owner = True
                    member.role = m.TeamRoles.ADMIN
                    break
            else:
                owner_data = {"user": owner} if owner else {"user_id": owner_id}
                data.members.append(m.TeamMember(**owner_data, role=m.TeamRoles.ADMIN, is_owner=True))

        return data
