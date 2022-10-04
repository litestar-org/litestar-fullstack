from app.core.db import models
from app.core.db.repositories.base import BaseRepository


class UploadRepository(BaseRepository[models.Upload]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """

    model_type = models.Upload
