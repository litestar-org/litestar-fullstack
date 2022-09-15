from typing import TYPE_CHECKING

from sqlalchemy import orm

from pyspa import models, repositories, schemas
from pyspa.services.base import DataAccessService, DataAccessServiceException

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
# team


class TeamServiceException(DataAccessServiceException):
    """_summary_"""


class TeamService(DataAccessService[models.Team, repositories.TeamRepository, schemas.TeamCreate, schemas.TeamUpdate]):
    """Handles basic lookup operations for a team"""

    async def create(self, db: "AsyncSession", *, obj_in: schemas.TeamCreate) -> models.Workspace:
        obj_data = obj_in.dict(exclude_unset=True, by_alias=False, exclude_none=True, exclude=["owner_id"])
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
# team invite


class TeamInvitationServiceException(DataAccessServiceException):
    """_summary_"""


class TeamInvitationService(
    DataAccessService[
        models.TeamInvitation,
        repositories.TeamInvitationRepository,
        schemas.TeamInvitationCreate,
        schemas.TeamInvitationUpdate,
    ]
):
    """Handles basic lookup operations for an Invitation"""


team_invite = TeamInvitationService(
    model=models.TeamInvitation, repository=repositories.TeamInvitationRepository, default_options=[]
)
