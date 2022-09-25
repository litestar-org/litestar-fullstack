from app.db import models
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    model_type = models.User
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """
