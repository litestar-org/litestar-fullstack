from app import models
from app.repositories.base import BaseRepository


class TeamInvitationRepository(BaseRepository[models.TeamInvitation]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """

    model_type = models.TeamInvitation


team_invite = TeamInvitationRepository()
