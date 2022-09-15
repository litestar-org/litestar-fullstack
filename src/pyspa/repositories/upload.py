from pyspa import models
from pyspa.repositories.base import BaseRepository


class UploadRepository(BaseRepository[models.Upload]):
    """_summary_

    Args:
        BaseRepository (_type_): _description_
    """


upload = UploadRepository(model=models.Upload)
