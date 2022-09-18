from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import orm, select

from pyspa import models, repositories, schemas
from pyspa.services.base import DataAccessService, DataAccessServiceException

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.ext.asyncio import AsyncSession


class TeamServiceException(DataAccessServiceException):
    """_summary_"""


class TeamService(DataAccessService[models.Team, repositories.TeamRepository, schemas.TeamCreate, schemas.TeamUpdate]):
    """Handles basic lookup operations for a team"""

    async def create(self, db: "AsyncSession", obj_in: schemas.TeamCreate) -> models.Team:
        obj_data = obj_in.dict(
            exclude_unset=True, by_alias=False, exclude_none=True, exclude=["owner_id"]  # type: ignore[arg-type]
        )
        team = self.model(**obj_data)
        team.members.append(models.TeamMember(user_id=obj_in.owner_id, role=models.TeamRoless.ADMIN, is_owner=True))
        return await self.repository.create(db, team)

    async def get_teams_for_user(
        self, db: "AsyncSession", user_id: "UUID4", options: Optional[List[Any]] = None
    ) -> List[schemas.Team]:
        """Get all workspaces for a user"""
        options = options if options else self.default_options
        statement = (
            select(self.model)
            .join(models.TeamMember, onclause=self.model.id == models.TeamMember.team_id, isouter=False)
            .where(models.TeamMember.user_id == user_id)
            .options(*options)
        )
        return await self.repository.list(db, statement)

    @staticmethod
    def is_owner(team: models.Team, user_id: int) -> bool:
        """Returns true if the user is the owner of the workspace"""
        return any(member.user_id == user_id and member.is_owner for member in team.members)


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
