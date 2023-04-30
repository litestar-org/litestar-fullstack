from __future__ import annotations

from datetime import datetime  # noqa: TCH003

from app.lib.schema import CamelizedBaseModel

__all__ = ["NewUsersByWeek"]


class NewUsersByWeek(CamelizedBaseModel):
    """User properties to use for a response."""

    week: datetime
    new_users: int
