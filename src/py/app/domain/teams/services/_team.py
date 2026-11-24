"""Team database service with slug generation, tags, and ownership transfer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.extensions.litestar import repository, service

from app.db import models as m
from app.domain.tags.services import TagService
from app.lib import constants

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT


class TeamService(service.SQLAlchemyAsyncRepositoryService[m.Team]):
    """Handles CRUD operations, unique slugs, tag assignment, and ownership transfer for teams."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Team]):
        """Team SQLAlchemy slug repository."""

        model_type = m.Team

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug, initial owner membership, and tags on team creation."""
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped, "create")

    async def to_model_on_update(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug and resolve tag associations on team update."""
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped, "update")

    async def to_model_on_upsert(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug and resolve tag associations on team upsert."""
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped, "upsert")

    async def _populate_slug(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(str(data["name"]))
        return data

    @staticmethod
    def can_view_all(user: m.User) -> bool:
        """Return whether ``user`` may list all teams across the workspace."""
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name == constants.SUPERUSER_ACCESS_ROLE
                for assigned_role in user.roles
            ),
        )

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
        model = await super().to_model(data)
        if operation == "create":
            owner_data: dict[str, Any] = {"user": owner} if owner else {"user_id": owner_id}
            model.members.append(m.TeamMember(**owner_data, role=m.TeamRoles.ADMIN, is_owner=True))
        if input_tags is not None:
            tag_service = TagService(session=self.repository.session)
            model.tags = list(await tag_service.upsert_many([{"name": tag_text} for tag_text in input_tags]))
        return model

    async def update(self, data: ModelDictT[m.Team], item_id: Any | None = None, **kwargs: Any) -> m.Team:
        """Update team details and optionally transfer ownership when ``owner_id`` is provided."""
        pending_owner_id: UUID | None = None
        if service.is_dict_with_field(data, "owner_id"):
            pending_owner_id = data.get("owner_id")
        if (
            item_id is not None
            and service.is_dict_with_field(data, "name")
            and service.is_dict_without_field(data, "slug")
        ):
            existing = await self.get(item_id)
            if existing.name == data["name"]:
                data["slug"] = existing.slug

        if pending_owner_id is None:
            return await super().update(data, item_id=item_id, **kwargs)

        requested_commit = bool(kwargs.pop("auto_commit", False))
        team = await super().update(data, item_id=item_id, auto_commit=False, **kwargs)
        await self._transfer_ownership(team, pending_owner_id)
        if requested_commit:
            await self.repository.session.commit()
        return team

    async def _transfer_ownership(self, team: m.Team, new_owner_id: UUID) -> None:
        await self.repository.session.refresh(team, ["members"])
        target = next((member for member in team.members if member.user_id == new_owner_id), None)
        if target is None:
            msg = "Target user is not a member of this team."
            raise RepositoryError(msg)
        for member in team.members:
            if member.user_id == new_owner_id:
                member.is_owner = True
                member.role = m.TeamRoles.ADMIN
            elif member.is_owner:
                member.is_owner = False
