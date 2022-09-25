from sqlalchemy import orm

from app import schemas
from app.db import models, repositories
from app.services.base import BaseRepositoryService, BaseRepositoryServiceException


class TeamInvitationServiceException(BaseRepositoryServiceException):
    """_summary_"""


class TeamInvitationNotFoundException(TeamInvitationServiceException):
    """Team Invite was not found"""


class TeamInvitationExpired(TeamInvitationServiceException):
    """Team Invite expired"""


class TeamInvitationEmailMismatchException(TeamInvitationServiceException):
    """User email does not match invite email"""


class TeamInvitationService(
    BaseRepositoryService[
        models.TeamInvitation,
        repositories.TeamInvitationRepository,
        schemas.TeamInvitationCreate,
        schemas.TeamInvitationUpdate,
    ]
):
    """Handles basic lookup operations for an Invitation"""

    model_type = models.TeamInvitation
    repository_type = repositories.TeamInvitationRepository


team_invite = TeamInvitationService(default_options=[orm.noload("*")])
