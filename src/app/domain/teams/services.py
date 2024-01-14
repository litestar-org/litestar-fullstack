from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID, uuid4

from advanced_alchemy import RepositoryError
from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import InstrumentedAttribute, joinedload, load_only, noload, selectinload

from app.db.models import Team, TeamInvitation, TeamMember, TeamRoles, User
from app.domain.tags.dependencies import provide_tags_service
from app.lib.dependencies import FilterTypes
from app.lib.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository
from app.lib.service import SQLAlchemyAsyncRepositoryService
from app.utils import slugify

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = (
    "TeamInvitationRepository",
    "TeamInvitationService",
    "TeamMemberRepository",
    "TeamMemberService",
    "TeamRepository",
    "TeamService",
)


class TeamRepository(SQLAlchemyAsyncSlugRepository[Team]):
    """Team Repository."""

    model_type = Team

    async def get_user_teams(
        self,
        *filters: FilterTypes | ColumnElement[bool],
        user_id: UUID,
        auto_expunge: bool | None = None,
        force_basic_query_mode: bool | None = None,
        **kwargs: Any,
    ) -> tuple[list[Team], int]:
        """Get paginated list and total count of teams that a user can access."""

        return await self.list_and_count(
            *filters,
            statement=select(Team)
            .join(TeamMember, onclause=Team.id == TeamMember.team_id, isouter=False)
            .where(TeamMember.user_id == user_id)
            .options(
                noload("*"),
                selectinload(Team.members).options(
                    joinedload(TeamMember.user, innerjoin=True).options(
                        load_only(User.name, User.email),
                    ),
                ),
            )
            .execution_options(populate_existing=True),
            auto_expunge=auto_expunge,
            force_basic_query_mode=force_basic_query_mode,
            **kwargs,
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
        tags_added: list[str] = []
        if isinstance(data, dict):
            data["id"] = data.get("id", uuid4())
            owner_id = data.pop("owner_id", None)
            if owner_id is None:
                msg = "'owner_id' is required to create a workspace."
                raise RepositoryError(msg)
            tags_added = data.pop("tags", [])
            db_obj = await self.to_model(data, "create")
        if owner_id:
            db_obj.members.append(TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))
        if tags_added:
            tags_service = await anext(provide_tags_service(db_session=cast("AsyncSession", self.repository.session)))
            for tag_text in tags_added:
                tag, _ = await tags_service.get_or_upsert(
                    match_fields=["slug"],
                    upsert=False,
                    name=tag_text,
                    slug=slugify(tag_text),
                )
                db_obj.tags.append(tag)
        return await super().create(
            data=data,
            auto_commit=auto_commit,
            auto_expunge=auto_expunge,
            auto_refresh=auto_refresh,
        )

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
            data = await super().update(
                item_id=item_id,
                data=data,
                attribute_names=attribute_names,
                with_for_update=with_for_update,
                auto_commit=auto_commit,
                auto_expunge=auto_expunge,
                auto_refresh=auto_refresh,
                id_attribute=id_attribute,
            )
            tags_service = await anext(provide_tags_service(db_session=cast("AsyncSession", self.repository.session)))
            existing_tags = [tag.name for tag in data.tags]
            tags_to_remove = [tag for tag in data.tags if tag.name not in tags_updated]
            tags_to_add = [tag for tag in tags_updated if tag not in existing_tags]
            for tag_rm in tags_to_remove:
                data.tags.remove(tag_rm)
            for tag_text in tags_to_add:
                tag, _ = await tags_service.get_or_upsert(name=tag_text)
                data.tags.append(tag)
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


class TeamMemberRepository(SQLAlchemyAsyncRepository[TeamMember]):
    """Team Member Repository."""

    model_type = TeamMember


class TeamMemberService(SQLAlchemyAsyncRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationRepository(SQLAlchemyAsyncRepository[TeamInvitation]):
    """Team Invitation Repository."""

    model_type = TeamInvitation


class TeamInvitationService(SQLAlchemyAsyncRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository
