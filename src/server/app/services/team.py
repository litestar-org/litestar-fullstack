from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import orm, select

from app import schemas
from app.core.db import models, repositories
from app.services.base import BaseRepositoryService, BaseRepositoryServiceException

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.db.repositories.base import LimitOffset


class TeamServiceException(BaseRepositoryServiceException):
    """_summary_"""


class TeamService(
    BaseRepositoryService[models.Team, repositories.TeamRepository, schemas.TeamCreate, schemas.TeamUpdate]
):
    """Handles basic lookup operations for a team"""

    model_type = models.Team
    repository_type = repositories.TeamRepository

    async def create(self, db_session: "AsyncSession", obj_in: schemas.TeamCreate) -> models.Team:
        obj_data = obj_in.dict(
            exclude_unset=True, by_alias=False, exclude_none=True, exclude=["owner_id"]  # type: ignore[arg-type]
        )
        obj_data["slug"] = self.repository.get_available_slug(db_session, obj_in.name)
        team = self.model(**obj_data)
        team.members.append(models.TeamMember(user_id=obj_in.owner_id, role=models.TeamRoles.ADMIN, is_owner=True))
        team = await self.repository.create(db_session, team)
        return team

    async def get_teams_for_user(
        self,
        db_session: "AsyncSession",
        user_id: "UUID4",
        limit_offset: Optional["LimitOffset"] = None,
        options: Optional[list[Any]] = None,
    ) -> list[models.Team] | tuple[list[models.Team], int]:
        """Get all workspaces for a user"""
        options = options if options else self.default_options
        statement = (
            select(self.model)
            .join(models.TeamMember, onclause=self.model.id == models.TeamMember.team_id, isouter=False)
            .where(models.TeamMember.user_id == user_id)
            .options(*options)
        )
        return await self.repository.select(db_session, statement, limit_offset)

    @staticmethod
    def is_owner(team: models.Team, user_id: int) -> bool:
        """Returns true if the user is the owner of the workspace"""
        return any(member.user_id == user_id and member.is_owner for member in team.members)


team = TeamService(
    default_options=[
        orm.noload("*"),
        orm.subqueryload(models.Team.members).options(
            orm.joinedload(models.TeamMember.user, innerjoin=True).options(
                orm.noload("*"),
            ),
        ),
    ],
)
