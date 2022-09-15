from sqlalchemy import orm

from pyspa import models, repositories, schemas
from pyspa.services.base import DataAccessService, DataAccessServiceException


class TeamInvitationServiceException(DataAccessServiceException):
    """_summary_"""


class TeamInvitationNotFoundException(TeamInvitationServiceException):
    """Team Invite was not found"""


class TeamInvitationExpired(TeamInvitationServiceException):
    """Team Invite expired"""


class TeamInvitationEmailMismatchException(TeamInvitationServiceException):
    """User email does not match invite email"""


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
    model=models.TeamInvitation, repository=repositories.TeamInvitationRepository, default_options=[orm.noload("*")]
)
