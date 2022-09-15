from pyspa import models
from pyspa.repositories.base import BaseRepository


class TeamRepository(BaseRepository[models.Team]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


class TeamInvitationRepository(BaseRepository[models.TeamInvitation]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


team = TeamRepository(model=models.Team)
team_invite = TeamInvitationRepository(model=models.TeamInvitation)
