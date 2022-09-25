from app.db import models
from app.db.repositories.base import BaseRepository


class TeamRepository(BaseRepository[models.Team]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """

    model_type = models.Team
