from pyspa import models
from pyspa.repositories.base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


user = UserRepository(model=models.User)
