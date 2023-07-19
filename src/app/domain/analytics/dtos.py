from dataclasses import dataclass
from datetime import datetime

from litestar.dto import DataclassDTO

from app.lib import dto

__all__ = ["NewUsersByWeek", "NewUsersByWeekDTO"]


@dataclass
class NewUsersByWeek:
    week: datetime
    new_users: int


class NewUsersByWeekDTO(DataclassDTO[NewUsersByWeek]):
    """NewUsersByWeek."""

    config = dto.config()
