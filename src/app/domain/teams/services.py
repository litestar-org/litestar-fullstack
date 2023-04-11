from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import joinedload, noload, selectinload

from app.domain.teams.models import Team, TeamInvitation, TeamMember, TeamRoles
from app.lib.dependencies import FilterTypes
from app.lib.repository import SQLAlchemyRepository, SQLAlchemySlugRepository
from app.lib.service.sqlalchemy import SQLAlchemyRepositoryService

__all__ = [
    "TeamInvitationRepository",
    "TeamInvitationService",
    "TeamMemberRepository",
    "TeamMemberService",
    "TeamRepository",
    "TeamService",
]


class TeamRepository(SQLAlchemySlugRepository[Team]):
    """Team Repository."""

    model_type = Team

    async def get_user_teams(
        self,
        *filters: FilterTypes,
        user_id: UUID,
        **kwargs: Any,
    ) -> tuple[list[Team], int]:
        """Get all teams for a user."""
        statement = (
            select(self.model_type)
            .join(TeamMember, onclause=self.model_type.id == TeamMember.team_id, isouter=False)
            .where(TeamMember.user_id == user_id)
            .options(
                noload("*"),
                selectinload(Team.members).options(
                    joinedload(TeamMember.user, innerjoin=True).options(noload("*")),
                ),
            )
            .execution_options(populate_existing=True)
        )
        return await self.list_and_count(*filters, statement=statement)


class TeamService(SQLAlchemyRepositoryService[Team]):
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
    ) -> Team:
        """Create a new team with an owner."""
        owner_id: UUID | None = None
        if isinstance(data, dict):
            data["id"] = data.get("id", uuid4())
            owner_id = data.pop("owner_id", None)
            db_obj = await self.to_model(data, "create")
        if owner_id:
            db_obj.members.append(TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))
        return await super().create(db_obj)

    async def to_model(self, data: Team | dict[str, Any], operation: str | None = None) -> Team:
        if isinstance(data, dict) and "slug" not in data:
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return await super().to_model(data, operation)


class TeamMemberRepository(SQLAlchemyRepository[TeamMember]):
    """Team Member Repository."""

    model_type = TeamMember


class TeamMemberService(SQLAlchemyRepositoryService[TeamMember]):
    """Team Member Service."""

    repository_type = TeamMemberRepository


class TeamInvitationRepository(SQLAlchemyRepository[TeamInvitation]):
    """Team Invitation Repository."""

    model_type = TeamInvitation


class TeamInvitationService(SQLAlchemyRepositoryService[TeamInvitation]):
    """Team Invitation Service."""

    repository_type = TeamInvitationRepository
