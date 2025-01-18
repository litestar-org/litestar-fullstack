from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyAsyncSlugRepository,
)
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    is_schema_with_field,
)
from advanced_alchemy.utils.text import slugify
from uuid_utils.compat import uuid4

from app.config import constants
from app.db import models as m

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

__all__ = (
    "TeamInvitationService",
    "TeamMemberService",
    "TeamService",
)


class TeamService(SQLAlchemyAsyncRepositoryService[m.Team]):
    """Team Service."""

    class TeamRepository(SQLAlchemyAsyncSlugRepository[m.Team]):
        """Team Repository."""

        model_type = m.Team

    repository_type = TeamRepository
    match_fields = ["name"]

    @staticmethod
    def can_view_all(user: m.User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in user.roles
                if assigned_role.role.name in {constants.SUPERUSER_ACCESS_ROLE}
            ),
        )

    async def to_model(self, data: ModelDictT[m.Team], operation: str | None = None) -> m.Team:
        data = await self._populate_slug(data, operation)
        data = await self._populate_with_owner_and_tags(data, operation)
        return await super().to_model(data, operation)

    async def _populate_slug(self, data: ModelDictT[m.Team], operation: str | None) -> ModelDictT[m.Team]:
        if operation == "create" and is_schema_with_field(data, "slug") and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if operation == "create" and is_dict_without_field(data, "slug"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if operation == "update" and is_schema_with_field(data, "slug") and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if operation == "update" and is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def _populate_with_owner_and_tags(
        self,
        data: ModelDictT[m.Team],
        operation: str | None,
    ) -> ModelDictT[m.Team]:
        if operation == "create" and is_dict(data):
            owner_id: UUID | None = data.pop("owner_id", None)
            owner: m.User | None = data.pop("owner", None)
            tags_added: list[str] = data.pop("tags", [])
            data["id"] = data.get("id", uuid4())
            data = await super().to_model(data, operation)
            if tags_added:
                data.tags.extend(
                    [
                        await m.Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                        for tag_text in tags_added
                    ],
                )
            if owner:
                data.members.append(m.TeamMember(user=owner, role=m.TeamRoles.ADMIN, is_owner=True))
            elif owner_id:
                data.members.append(m.TeamMember(user_id=owner_id, role=m.TeamRoles.ADMIN, is_owner=True))

        if operation == "update" and is_dict(data):
            tags_updated = data.pop("tags", None)
            data = await super().to_model(data, operation)
            if tags_updated:
                existing_tags = [tag.name for tag in data.tags]
                tags_to_remove = [tag for tag in data.tags if tag.name not in tags_updated]
                tags_to_add = [tag for tag in tags_updated if tag not in existing_tags]
                for tag_rm in tags_to_remove:
                    data.tags.remove(tag_rm)
                data.tags.extend(
                    [
                        await m.Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                        for tag_text in tags_to_add
                    ],
                )
        return data


class TeamMemberService(SQLAlchemyAsyncRepositoryService[m.TeamMember]):
    """Team Member Service."""

    class TeamMemberRepository(SQLAlchemyAsyncRepository[m.TeamMember]):
        """Team Member Repository."""

        model_type = m.TeamMember

    repository_type = TeamMemberRepository


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[m.TeamInvitation]):
    """Team Invitation Service."""

    class TeamInvitationRepository(SQLAlchemyAsyncRepository[m.TeamInvitation]):
        """Team Invitation Repository."""

        model_type = m.TeamInvitation

    repository_type = TeamInvitationRepository
