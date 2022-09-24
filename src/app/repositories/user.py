from app import models
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    model_type = models.User
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


user = UserRepository()
