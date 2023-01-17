from app.core.db import models
from app.core.db.repositories.base import BaseRepository


class TeamInvitationRepository(BaseRepository[models.TeamInvitation]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """

    model_type = models.TeamInvitation
