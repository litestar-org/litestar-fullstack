"""Team database service with slug generation, tags, and ownership transfer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.extensions.litestar import repository, service
from sqlalchemy import select

from app.db import models as m
from app.domain.tags.services import TagService
from app.lib import constants

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from advanced_alchemy.filters import StatementFilter
    from advanced_alchemy.service import ModelDictT
    from sqlalchemy import ColumnElement


class TeamService(service.SQLAlchemyAsyncRepositoryService[m.Team]):
    """Handles CRUD operations, unique slugs, tag assignment, and ownership transfer for teams."""

    class Repo(repository.SQLAlchemyAsyncSlugRepository[m.Team]):
        """Team SQLAlchemy slug repository."""

        model_type = m.Team

    repository_type = Repo
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug, initial owner membership, and tags on team creation.

        Returns:
            Prepared ``Team`` model or payload for creation.
        """
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped, is_new_team=True)

    async def to_model_on_update(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug and resolve tag associations on team update.

        Returns:
            Prepared ``Team`` model or payload for update.
        """
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped)

    async def to_model_on_upsert(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        """Populate unique slug and resolve tag associations on team upsert.

        Returns:
            Prepared ``Team`` model or payload for upsert.
        """
        dumped = await self._populate_slug(service.schema_dump(data))
        return await self._populate_with_owner_and_tags(dumped)

    async def update(self, data: ModelDictT[m.Team], item_id: Any | None = None, **kwargs: Any) -> m.Team:
        """Update team details and optionally transfer ownership when ``owner_id`` is provided.

        Returns:
            The updated ``Team`` model instance.
        """
        new_owner_id: UUID | None = data.get("owner_id") if service.is_dict_with_field(data, "owner_id") else None
        if item_id is not None:
            await self._keep_slug_when_name_unchanged(data, item_id)
        if new_owner_id is None:
            return await super().update(data, item_id=item_id, **kwargs)

        commit_requested = bool(kwargs.pop("auto_commit", False))
        team = await super().update(data, item_id=item_id, auto_commit=False, **kwargs)
        await self._transfer_ownership(team, new_owner_id)
        if commit_requested:
            await self.repository.session.commit()
        return team

    async def list_visible_to(
        self,
        user: m.User,
        *filters: StatementFilter | ColumnElement[bool],
    ) -> tuple[Sequence[m.Team], int]:
        """List the teams ``user`` may see: every team for workspace superusers, otherwise only their own.

        Returns:
            The matching teams and their total count before pagination.
        """
        if self.can_view_all(user):
            return await self.get_many_and_count(*filters)
        own_team_ids = select(m.TeamMember.team_id).where(m.TeamMember.user_id == user.id).scalar_subquery()
        return await self.get_many_and_count(*filters, m.Team.id.in_(own_team_ids))

    @staticmethod
    def can_view_all(user: m.User) -> bool:
        """Return whether ``user`` may list all teams across the workspace."""
        return bool(
            user.is_superuser
            or any(assigned_role.role.name == constants.SUPERUSER_ACCESS_ROLE for assigned_role in user.roles),
        )

    async def _populate_slug(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        if service.is_dict_without_field(data, "slug") and service.is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(str(data["name"]))
        return data

    async def _populate_with_owner_and_tags(
        self,
        data: ModelDictT[m.Team],
        *,
        is_new_team: bool = False,
    ) -> ModelDictT[m.Team]:
        if not service.is_dict(data):
            return data

        owner_id: UUID | None = data.pop("owner_id", None)
        owner: m.User | None = data.pop("owner", None)
        tag_names: list[str] | None = data.pop("tags", None)
        if is_new_team and owner_id is None and owner is None:
            msg = "'owner_id' is required to create a team."
            raise RepositoryError(msg)
        team = await super().to_model(data)
        if is_new_team:
            owner_reference: dict[str, m.User | UUID | None] = {"user": owner} if owner else {"user_id": owner_id}
            team.members.append(m.TeamMember(**owner_reference, role=m.TeamRoles.ADMIN, is_owner=True))
        if tag_names is not None:
            tags_service = TagService(session=self.repository.session)
            team.tags = list(await tags_service.upsert_many([{"name": tag_name} for tag_name in tag_names]))
        return team

    async def _keep_slug_when_name_unchanged(self, data: ModelDictT[m.Team], item_id: Any) -> None:
        if service.is_dict_with_field(data, "name") and service.is_dict_without_field(data, "slug"):
            team = await self.get(item_id)
            if team.name == data["name"]:
                data["slug"] = team.slug

    async def _transfer_ownership(self, team: m.Team, new_owner_id: UUID) -> None:
        await self.repository.session.refresh(team, ["members"])
        if not any(member.user_id == new_owner_id for member in team.members):
            msg = "Target user is not a member of this team."
            raise RepositoryError(msg)
        for member in team.members:
            if member.user_id == new_owner_id:
                member.is_owner = True
                member.role = m.TeamRoles.ADMIN
            elif member.is_owner:
                member.is_owner = False
