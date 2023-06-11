from dataclasses import dataclass
from datetime import datetime

from litestar.dto.factory.stdlib.dataclass import DataclassDTO

from app.lib import dto


@dataclass
class NewUsersByWeek:
    week: datetime
    new_users: int


class NewUsersByWeekDTO(DataclassDTO[NewUsersByWeek]):
    """NewUsersByWeek."""

    config = dto.config()
