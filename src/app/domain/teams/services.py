from __future__ import annotations

from typing import TYPE_CHECKING, Any

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, is_dict, is_msgspec_model, is_pydantic_model
from advanced_alchemy.utils.text import slugify
from uuid_utils.compat import uuid4

from app.config import constants
from app.db.models import Team, TeamInvitation, TeamMember, TeamRoles
from app.db.models.tag import Tag
from app.db.models.user import User  # noqa: TCH001

from .repositories import TeamInvitationRepository, TeamMemberRepository, TeamRepository

if TYPE_CHECKING:
    from collections.abc import Iterable
    from uuid import UUID

    from advanced_alchemy.repository._util import LoadSpec
    from advanced_alchemy.service import ModelDictT
    from sqlalchemy.orm import InstrumentedAttribute

__all__ = (
    "TeamInvitationService",
    "TeamMemberService",
    "TeamService",
)


class TeamService(SQLAlchemyAsyncRepositoryService[Team]):
    """Team Service."""

    repository_type = TeamRepository
    match_fields = ["name"]

    def __init__(self, **repo_kwargs: Any) -> None:
        self.repository: TeamRepository = self.repository_type(**repo_kwargs)
        self.model_type = self.repository.model_type

    async def create(
        self,
        data: ModelDictT[Team],
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
    ) -> Team:
        """Create a new team with an owner."""
        owner_id: UUID | None = None
        owner: User | None = None
        tags_added: list[str] = []
        if isinstance(data, dict):
            data["id"] = data.get("id", uuid4())
            owner = data.pop("owner", None)
            owner_id = data.pop("owner_id", None)
            if owner_id is None:
                msg = "'owner_id' is required to create a team."
                raise RepositoryError(msg)
            tags_added = data.pop("tags", [])
        data = await self.to_model(data, "create")
        if owner:
            data.members.append(TeamMember(user=owner, role=TeamRoles.ADMIN, is_owner=True))
        elif owner_id:
            data.members.append(TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))
        if tags_added:
            data.tags.extend(
                [
                    await Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                    for tag_text in tags_added
                ],
            )
        await super().create(
            data=data,
            auto_commit=auto_commit,
            auto_expunge=True,
            auto_refresh=False,
        )
        return data

    async def update(
        self,
        data: ModelDictT[Team],
        item_id: Any | None = None,
        *,
        id_attribute: str | InstrumentedAttribute[Any] | None = None,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
    ) -> Team:
        """Wrap repository update operation.

        Returns:
            Updated representation.
        """
        tags_updated: list[str] = []
        if isinstance(data, dict):
            tags_updated.extend(data.pop("tags", None) or [])
            data["id"] = item_id
            data = await self.to_model(data, "update")
            existing_tags = [tag.name for tag in data.tags]
            tags_to_remove = [tag for tag in data.tags if tag.name not in tags_updated]
            tags_to_add = [tag for tag in tags_updated if tag not in existing_tags]
            for tag_rm in tags_to_remove:
                data.tags.remove(tag_rm)
            data.tags.extend(
                [
                    await Tag.as_unique_async(self.repository.session, name=tag_text, slug=slugify(tag_text))
                    for tag_text in tags_to_add
                ],
            )
        return await super().update(
            data=data,
            item_id=item_id,
            attribute_names=attribute_names,
            id_attribute=id_attribute,
            load=load,
            execution_options=execution_options,
            with_for_update=with_for_update,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
        )

    @staticmethod
    def can_view_all(user: User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in user.roles
                if assigned_role.role.name in {constants.SUPERUSER_ACCESS_ROLE}
            ),
        )

    async def to_model(self, data: ModelDictT[Team], operation: str | None = None) -> Team:
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "create" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "update" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if is_dict(data) and "slug" not in data and operation == "create":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if is_dict(data) and "slug" not in data and "name" in data and operation == "update":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return await super().to_model(data, operation)


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository
