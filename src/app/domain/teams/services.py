from collections.abc import Iterable
from typing import Any
from uuid import UUID

from advanced_alchemy import RepositoryError
from sqlalchemy.orm import InstrumentedAttribute
from uuid_utils.compat import uuid4

from app.db.models import Team, TeamInvitation, TeamMember, TeamRoles
from app.db.models.tag import Tag
from app.db.models.user import User  # noqa: TCH001
from app.lib.dependencies import FilterTypes
from app.lib.service import SQLAlchemyAsyncRepositoryService
from app.utils import slugify

from .repositories import TeamInvitationRepository, TeamMemberRepository, TeamRepository

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

    async def get_user_teams(
        self,
        *filters: FilterTypes,
        user_id: UUID,
        **kwargs: Any,
    ) -> tuple[list[Team], int]:
        """Get all teams for a user."""
        return await self.repository.get_user_teams(*filters, user_id=user_id, **kwargs)

    async def create(
        self,
        data: Team | dict[str, Any],
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
                msg = "'owner_id' is required to create a workspace."
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
        _ = await super().create(
            data=data,
            auto_commit=auto_commit,
            auto_expunge=True,
            auto_refresh=False,
        )
        return data

    async def update(
        self,
        data: Team | dict[str, Any],
        item_id: Any | None = None,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
        auto_refresh: bool | None = None,
        id_attribute: str | InstrumentedAttribute | None = None,
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
            item_id=item_id,
            data=data,
            attribute_names=attribute_names,
            with_for_update=with_for_update,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
            id_attribute=id_attribute,
        )

    async def to_model(self, data: Team | dict[str, Any], operation: str | None = None) -> Team:
        if isinstance(data, dict) and "slug" not in data and operation == "create":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if isinstance(data, dict) and "slug" not in data and "name" in data and operation == "update":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return await super().to_model(data, operation)


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository
