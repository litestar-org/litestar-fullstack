from typing import TYPE_CHECKING

from sqlalchemy import orm

from pyspa import models, repositories, schemas
from pyspa.services.base import DataAccessService, DataAccessServiceException

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TeamServiceException(DataAccessServiceException):
    """_summary_"""


class TeamService(DataAccessService[models.Team, repositories.TeamRepository, schemas.TeamCreate, schemas.TeamUpdate]):
    """Handles basic lookup operations for a team"""

    async def create(self, db: "AsyncSession", obj_in: schemas.TeamCreate) -> models.Team:
        obj_data = obj_in.dict(
            exclude_unset=True, by_alias=False, exclude_none=True, exclude=["owner_id"]  # typing: ignore[arg-type]
        )
        team = self.model(**obj_data)
        team.members.append(models.TeamMember(user_id=obj_in.owner_id, role=models.TeamRoleTypes.ADMIN, is_owner=True))
        return await self.repository.create(db, team)


team = TeamService(
    model=models.Team,
    repository=repositories.TeamRepository,
    default_options=[
        orm.noload("*"),
        orm.subqueryload(models.Team.members).options(
            orm.joinedload(models.TeamMember.user, innerjoin=True).options(
                orm.noload("*"),
            ),
        ),
    ],
)
