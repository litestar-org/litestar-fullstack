from app.core.db import models
from app.core.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    model_type = models.User
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """
