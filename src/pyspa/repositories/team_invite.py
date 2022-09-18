from pyspa import models
from pyspa.repositories.base import BaseRepository


class TeamInvitationRepository(BaseRepository[models.TeamInvitation]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


team_invite = TeamInvitationRepository(model=models.TeamInvitation)
